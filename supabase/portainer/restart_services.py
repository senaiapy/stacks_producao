#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔄 Restarting Supabase services in correct order...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Check current status
    print("📊 Current service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # Restart services in dependency order
    services_order = [
        "supabase_studio",
        "supabase_auth",
        "supabase_rest",
        "supabase_realtime"
    ]

    for service in services_order:
        print(f"\n🔄 Restarting {service}...")
        stdin, stdout, stderr = ssh.exec_command(f"docker service update --force {service}")

        # Wait and check status
        time.sleep(15)
        stdin, stdout, stderr = ssh.exec_command(f"docker service ps {service} --format 'table {{.Name}}{{\"\\t\"}}{{.CurrentState}}'")
        status = stdout.read().decode()
        print(f"{service} status: {status}")

    # Final status check
    print("\n📊 Final service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # Test Kong backend connectivity
    print("\n🧪 Testing Kong backend connectivity...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -I http://localhost:8000/ 2>/dev/null")
    output = stdout.read().decode()
    print(f"Kong backend test: {output}")

    # Test external HTTPS access
    print("\n🌐 Testing external HTTPS access...")
    stdin, stdout, stderr = ssh.exec_command("curl -I https://supabase.senaia.in 2>/dev/null")
    output = stdout.read().decode()
    print(f"External HTTPS: {output}")

    ssh.close()
    print("\n✅ Service restart completed!")

if __name__ == "__main__":
    main()