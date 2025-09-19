#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 Fixing Traefik labels and service discovery...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Upload the corrected supabase.yml with fixed Traefik labels
    print("📤 Uploading corrected supabase.yml with fixed Traefik labels...")
    sftp = ssh.open_sftp()
    sftp.put("supabase.yml", "/opt/supabase/supabase.yml")
    sftp.close()

    # Redeploy just Kong service to fix Traefik labels
    print("🔄 Updating Kong service with corrected Traefik labels...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker service update --force supabase_kong")
    print("Kong service updated")

    # Wait for Kong to restart
    print("⏳ Waiting for Kong to restart...")
    time.sleep(15)

    # Force restart Studio service to ensure it starts
    print("🎨 Restarting Studio service...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force supabase_studio")
    print("Studio service restarted")

    # Wait for Studio to start
    print("⏳ Waiting for Studio to start...")
    time.sleep(15)

    # Check service status
    print("📊 Checking service status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # Test Kong health
    print("🧪 Testing Kong health...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 3 supabase_kong")
    output = stdout.read().decode()
    print("Recent Kong logs:")
    print(output)

    # Test Studio health
    print("🎨 Testing Studio health...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 3 supabase_studio")
    output = stdout.read().decode()
    print("Recent Studio logs:")
    print(output)

    # Test external access again
    print("🌐 Testing external access...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/")
    status_code = stdout.read().decode().strip()
    print(f"External access status: {status_code}")

    # Test with credentials
    print("🔐 Testing with credentials...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/")
    cred_status = stdout.read().decode().strip()
    print(f"Authenticated access status: {cred_status}")

    ssh.close()
    print("\n✅ Service discovery fix completed!")

if __name__ == "__main__":
    main()