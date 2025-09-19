#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 Diagnosing name resolution errors...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Check DNS resolution
    print("\n🌐 Testing DNS resolution...")
    stdin, stdout, stderr = ssh.exec_command("nslookup supabase.senaia.in")
    output = stdout.read().decode()
    error = stderr.read().decode()
    print("DNS lookup result:")
    print(output)
    if error:
        print(f"DNS errors: {error}")

    # 2. Test external connectivity
    print("\n🌍 Testing external connectivity...")
    stdin, stdout, stderr = ssh.exec_command("curl -I https://supabase.senaia.in 2>&1")
    output = stdout.read().decode()
    print("External access test:")
    print(output)

    # 3. Check Kong service logs
    print("\n📋 Checking Kong service logs...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 10 supabase_kong")
    output = stdout.read().decode()
    print("Kong logs:")
    print(output)

    # 4. Check Kong container status
    print("\n🔍 Checking Kong container status...")
    stdin, stdout, stderr = ssh.exec_command("docker ps -f name=supabase_kong")
    output = stdout.read().decode()
    print("Kong containers:")
    print(output)

    # 5. Test Kong internal connectivity
    print("\n🧪 Testing Kong internal connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) wget -qO- http://localhost:8000/ 2>&1 || echo 'Kong internal test failed'")
    output = stdout.read().decode()
    print("Kong internal test:")
    print(output)

    # 6. Check if Studio service is running
    print("\n🎨 Checking Studio service...")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_studio --no-trunc")
    output = stdout.read().decode()
    print("Studio service status:")
    print(output)

    # 7. Test internal service discovery
    print("\n🔗 Testing internal service discovery...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) nslookup studio 2>&1 || echo 'Service discovery test failed'")
    output = stdout.read().decode()
    print("Service discovery test:")
    print(output)

    # 8. Check network connectivity
    print("\n🌐 Checking Docker networks...")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{\"\\n\"}}{{end}}'")
    output = stdout.read().decode()
    print("App network containers:")
    print(output)

    # 9. Check Traefik logs
    print("\n🚦 Checking Traefik logs...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 traefik_traefik")
    output = stdout.read().decode()
    print("Traefik logs:")
    print(output)

    ssh.close()
    print("\n✅ Diagnosis completed!")

if __name__ == "__main__":
    main()