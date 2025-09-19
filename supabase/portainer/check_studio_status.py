#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🎨 Checking Studio service detailed status...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Check Studio service detailed status
    print("📊 Studio service detailed status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_studio --no-trunc")
    output = stdout.read().decode()
    print(output)

    # Check Studio container status
    print("\n🔍 Studio container status:")
    stdin, stdout, stderr = ssh.exec_command("docker ps -f name=supabase_studio")
    output = stdout.read().decode()
    print(output)

    # Get latest Studio logs
    print("\n📋 Latest Studio logs:")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 10 supabase_studio")
    output = stdout.read().decode()
    print(output)

    # Check if Studio is responding internally
    print("\n🧪 Testing Studio internal connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_studio -q) curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null || echo 'Studio internal test failed'")
    output = stdout.read().decode()
    print(f"Studio internal status: {output}")

    # Check Kong -> Studio connectivity
    print("\n🔗 Testing Kong -> Studio connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) nslookup studio 2>/dev/null || echo 'Kong->Studio DNS failed'")
    output = stdout.read().decode()
    print(f"Kong->Studio DNS: {output}")

    # Test Auth service too
    print("\n🔐 Checking Auth service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 supabase_auth")
    output = stdout.read().decode()
    print(output)

    # Check current service status
    print("\n📊 Current service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    ssh.close()
    print("\n✅ Studio check completed!")

if __name__ == "__main__":
    main()