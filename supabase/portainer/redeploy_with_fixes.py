#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚀 Redeploying Supabase with Kong port fixes...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Upload the corrected supabase.yml
    print("📤 Uploading corrected supabase.yml...")
    sftp = ssh.open_sftp()
    sftp.put("supabase.yml", "/opt/supabase/supabase.yml")
    sftp.close()

    # Redeploy the stack
    print("🔄 Redeploying Supabase stack...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker stack deploy -c supabase.yml supabase")
    output = stdout.read().decode()
    error = stderr.read().decode()
    print(output)
    if error:
        print(f"Errors: {error}")

    # Wait for deployment
    print("⏳ Waiting for services to restart...")
    time.sleep(30)

    # Check Kong specifically
    print("🔍 Checking Kong status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_kong --no-trunc")
    output = stdout.read().decode()
    print(output)

    # Test Kong connectivity on new ports
    print("🧪 Testing Kong connectivity on port 8000...")
    stdin, stdout, stderr = ssh.exec_command("curl -I http://localhost:8000/ 2>/dev/null || echo 'Port 8000 not responding'")
    output = stdout.read().decode()
    print(f"Port 8000 test: {output}")

    # Check overall service status
    print("📊 Service status after redeploy:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # Test external access
    print("🌐 Testing external access...")
    stdin, stdout, stderr = ssh.exec_command("curl -I https://supabase.senaia.in 2>/dev/null")
    output = stdout.read().decode()
    print(f"External access: {output}")

    # Get recent logs for failing services
    print("\n📋 Recent logs for key services:")

    services = ["supabase_kong", "supabase_auth", "supabase_studio"]
    for service in services:
        print(f"\n--- {service} logs ---")
        stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 3 {service}")
        output = stdout.read().decode()
        if output.strip():
            print(output)
        else:
            print("No recent logs")

    ssh.close()
    print("\n✅ Redeploy completed!")

if __name__ == "__main__":
    main()