#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 Checking Traefik status and port conflicts...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Check if Traefik is running
    print("🔍 Checking Traefik services...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=traefik")
    output = stdout.read().decode()
    print(output)

    # Check port usage
    print("🔍 Checking port usage...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlpn | grep -E ':80|:443|:8000|:8443'")
    output = stdout.read().decode()
    print("Port usage:")
    print(output)

    # Check Docker networks
    print("🔍 Checking Docker networks...")
    stdin, stdout, stderr = ssh.exec_command("docker network ls | grep -E 'traefik|app_network'")
    output = stdout.read().decode()
    print("Networks:")
    print(output)

    ssh.close()
    print("✅ Check completed!")

if __name__ == "__main__":
    main()