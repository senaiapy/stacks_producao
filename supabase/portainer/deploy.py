#!/usr/bin/env python3

import paramiko
import os
import sys
import time

# Server configuration
SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def print_status(message):
    print(f"[INFO] {message}")

def print_error(message):
    print(f"[ERROR] {message}")

def execute_remote_command(ssh, command):
    """Execute a command on the remote server"""
    print_status(f"Executing: {command}")
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if output:
            print(output)
        if error:
            print(f"Error: {error}")

        return stdout.channel.recv_exit_status() == 0
    except Exception as e:
        print_error(f"Command failed: {e}")
        return False

def upload_file(sftp, local_path, remote_path):
    """Upload a file to the remote server"""
    print_status(f"Uploading: {local_path} → {remote_path}")
    try:
        if os.path.isfile(local_path):
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            # Create remote directory
            try:
                sftp.mkdir(remote_path)
            except:
                pass
            # Upload directory contents
            for item in os.listdir(local_path):
                local_item = os.path.join(local_path, item)
                remote_item = f"{remote_path}/{item}"
                if os.path.isfile(local_item):
                    sftp.put(local_item, remote_item)
                elif os.path.isdir(local_item):
                    upload_file(sftp, local_item, remote_item)
        return True
    except Exception as e:
        print_error(f"Upload failed: {e}")
        return False

def main():
    try:
        # Check if paramiko is available
        import paramiko
    except ImportError:
        print_error("paramiko is not installed. Installing...")
        os.system("pip3 install paramiko")
        import paramiko

    print("🚀 Starting Supabase deployment...")

    # Create SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print_status("✅ SSH connection established")
    except Exception as e:
        print_error(f"SSH connection failed: {e}")
        return False

    # Create SFTP connection for file transfers
    sftp = ssh.open_sftp()

    # Step 1: Verify Docker Swarm
    print_status("📋 Step 1: Verifying Docker Swarm...")
    if not execute_remote_command(ssh, "docker node ls"):
        print_error("Docker Swarm verification failed")
        return False

    # Step 2: Create directories
    print_status("📂 Step 2: Creating directories...")
    commands = [
        "mkdir -p /opt/supabase",
        "mkdir -p /mnt/data/supabase/{api,storage,db,functions,logs}",
        "mkdir -p /mnt/data/supabase/db/{data,init}"
    ]

    for cmd in commands:
        execute_remote_command(ssh, cmd)

    # Step 3: Upload files
    print_status("📤 Step 3: Uploading files...")

    # Upload main files
    upload_file(sftp, "supabase.yml", "/opt/supabase/supabase.yml")
    upload_file(sftp, "SUPABASE-MANUAL.md", "/opt/supabase/SUPABASE-MANUAL.md")

    # Upload volumes directory
    try:
        sftp.mkdir("/opt/supabase/volumes")
    except:
        pass
    upload_file(sftp, "volumes", "/opt/supabase/volumes")

    # Step 4: Setup configuration files
    print_status("🔧 Step 4: Setting up configuration files...")
    config_commands = [
        "cp /opt/supabase/volumes/api/kong.yml /mnt/data/supabase/api/ 2>/dev/null || true",
        "cp /opt/supabase/volumes/logs/vector.yml /mnt/data/supabase/logs/ 2>/dev/null || true",
        "cp /opt/supabase/volumes/db/*.sql /mnt/data/supabase/db/ 2>/dev/null || true",
        "cp -r /opt/supabase/volumes/db/init/* /mnt/data/supabase/db/init/ 2>/dev/null || true",
        "chown -R 999:999 /mnt/data/supabase/db",
        "chmod 700 /mnt/data/supabase/db/data"
    ]

    for cmd in config_commands:
        execute_remote_command(ssh, cmd)

    # Step 5: Create Docker networks
    print_status("🌐 Step 5: Creating Docker networks...")
    network_commands = [
        "docker network create --driver=overlay traefik_public || echo 'Network exists'",
        "docker network create --driver=overlay app_network || echo 'Network exists'",
        "docker network ls | grep overlay"
    ]

    for cmd in network_commands:
        execute_remote_command(ssh, cmd)

    # Step 6: Deploy Supabase stack
    print_status("🗄️ Step 6: Deploying Supabase stack...")
    execute_remote_command(ssh, "cd /opt/supabase && docker stack deploy -c supabase.yml supabase")

    # Step 7: Wait and verify
    print_status("⏳ Step 7: Waiting for services to start...")
    time.sleep(30)

    print_status("📊 Step 8: Checking service status...")
    execute_remote_command(ssh, "docker service ls")

    # Close connections
    sftp.close()
    ssh.close()

    print("\n" + "="*50)
    print_status("✅ Deployment completed!")
    print("\n🌍 Access URLs:")
    print("  - Supabase Studio: https://supabase.senaia-bank.in")
    print("  - API Endpoint: https://supabase.senaia-bank.in/rest/v1/")
    print("\n👤 Default Credentials:")
    print("  - Username: supabase")
    print("  - Password: Ma1x1x0x_testing")

    return True

if __name__ == "__main__":
    main()