#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚀 Deploying Supabase with Traefik integration...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Upload the corrected supabase.yml
    print("📤 Uploading corrected supabase.yml with Traefik integration...")
    sftp = ssh.open_sftp()
    sftp.put("supabase.yml", "/opt/supabase/supabase.yml")
    sftp.close()

    # Redeploy the stack
    print("🔄 Redeploying Supabase stack for Traefik integration...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker stack deploy -c supabase.yml supabase")
    output = stdout.read().decode()
    error = stderr.read().decode()
    print(output)
    if error:
        print(f"Deployment errors: {error}")

    # Wait for services to update
    print("⏳ Waiting for services to update...")
    time.sleep(20)

    # Check Kong service status
    print("🔍 Checking Kong service status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_kong --no-trunc")
    output = stdout.read().decode()
    print(output)

    # Check if Kong is accessible internally (should not have external ports now)
    print("🧪 Testing Kong internal access...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/")
    status_code = stdout.read().decode().strip()
    print(f"Kong internal status: {status_code}")

    # Test external access through Traefik
    print("🌐 Testing external access through Traefik...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/")
    ext_status = stdout.read().decode().strip()
    print(f"External HTTPS status: {ext_status}")

    # Check service status
    print("📊 Final service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # Test if we can reach studio via Traefik
    print("🎨 Testing Studio access through Traefik...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/")
    studio_status = stdout.read().decode().strip()
    print(f"Studio access status: {studio_status}")

    ssh.close()
    print("\n✅ Traefik integration deployment completed!")

if __name__ == "__main__":
    main()