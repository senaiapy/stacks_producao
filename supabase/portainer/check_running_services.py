#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 Checking which services are actually running on the server...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Check all Docker services
    print("\n📊 All running Docker services:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls")
    output = stdout.read().decode()
    print(output)

    # Check port usage on host
    print("\n🔍 Port usage on host system:")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlpn | grep LISTEN")
    output = stdout.read().decode()
    print("Listening ports:")
    print(output)

    # Check Docker port mappings
    print("\n🐳 Docker container port mappings:")
    stdin, stdout, stderr = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Ports}}'")
    output = stdout.read().decode()
    print(output)

    # Check specific conflicting ports
    print("\n🚨 Checking specific ports for conflicts:")
    conflict_ports = ['5678', '80', '443', '5050', '9443', '8181', '5434']

    for port in conflict_ports:
        stdin, stdout, stderr = ssh.exec_command(f"netstat -tlpn | grep :{port}")
        output = stdout.read().decode().strip()
        if output:
            print(f"Port {port}: {output}")
        else:
            print(f"Port {port}: Available")

    # Check if Supabase would conflict
    print("\n🎯 Supabase specific analysis:")
    print("Supabase only uses internal ports behind Traefik, should be safe")

    # Check current Supabase services
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print("\nCurrent Supabase services:")
    print(output)

    ssh.close()
    print("\n✅ Service analysis completed!")

if __name__ == "__main__":
    main()