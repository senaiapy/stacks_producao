#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("📊 Final Supabase status check...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Quick status check
    print("\n📊 Service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # Test Kong connectivity
    print("\n🔍 Kong connectivity test:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/")
    status_code = stdout.read().decode().strip()
    print(f"Kong status code: {status_code}")

    # Test external access
    print("\n🌐 External access test:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/")
    ext_status = stdout.read().decode().strip()
    print(f"External status code: {ext_status}")

    # Check if studio is responding
    print("\n🎨 Studio service check:")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 3 supabase_studio")
    studio_logs = stdout.read().decode()
    print(f"Studio logs: {studio_logs}")

    ssh.close()
    print("\n✅ Status check completed!")

if __name__ == "__main__":
    main()