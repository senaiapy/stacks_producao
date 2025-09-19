#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 DIAGNOSING Kong DNS resolution failure...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Check Kong container network connectivity
    print("\n🔍 Testing Kong DNS resolution...")

    services_to_test = ['studio', 'auth', 'rest', 'realtime', 'meta', 'storage']

    for service in services_to_test:
        stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) nslookup {service} 2>&1")
        output = stdout.read().decode()
        print(f"{service}: {output.strip()}")

    # 2. Check what networks Kong is connected to
    print("\n🌐 Checking Kong network connections...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cat /etc/resolv.conf")
    output = stdout.read().decode()
    print(f"Kong DNS config:\n{output}")

    # 3. Check service status of target services
    print("\n📊 Checking target service status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # 4. Check Kong configuration
    print("\n🔧 Checking Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cat /home/kong/kong.yml 2>/dev/null | head -50")
    output = stdout.read().decode()
    print("Kong config (first 50 lines):")
    print(output)

    # 5. Check if Studio service is actually running
    print("\n🎨 Checking Studio service specifically...")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_studio --no-trunc")
    output = stdout.read().decode()
    print("Studio service status:")
    print(output)

    # 6. Test internal connectivity from Kong to a working service
    print("\n🧪 Testing Kong connectivity to working services...")

    # Test meta (which should be working)
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) curl -s -o /dev/null -w '%{http_code}' http://meta:8080 2>/dev/null || echo 'Meta connection failed'")
    meta_status = stdout.read().decode().strip()
    print(f"Kong -> Meta: {meta_status}")

    # Test storage (which should be working)
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) curl -s -o /dev/null -w '%{http_code}' http://storage:5000/status 2>/dev/null || echo 'Storage connection failed'")
    storage_status = stdout.read().decode().strip()
    print(f"Kong -> Storage: {storage_status}")

    # 7. Force restart Kong to refresh DNS cache
    print("\n🔄 Force restarting Kong to refresh DNS cache...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force supabase_kong")
    print("Kong restart initiated")
    time.sleep(15)

    # 8. Test DNS resolution again after restart
    print("\n🔍 Testing DNS resolution after Kong restart...")
    for service in ['studio', 'meta', 'storage']:
        stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) nslookup {service} 2>&1")
        output = stdout.read().decode()
        print(f"{service} (after restart): {output.strip()}")

    # 9. Check if Studio is actually responding internally
    print("\n🎨 Testing Studio internal response...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_studio -q) curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null || echo 'Studio not responding internally'")
    studio_internal = stdout.read().decode().strip()
    print(f"Studio internal response: {studio_internal}")

    # 10. Check Docker overlay network
    print("\n🌐 Checking Docker overlay network...")
    stdin, stdout, stderr = ssh.exec_command("docker network ls | grep supabase")
    networks = stdout.read().decode()
    print(f"Supabase networks: {networks}")

    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}} {{.IPv4Address}}{{\"\\n\"}}{{end}}' 2>/dev/null | grep supabase")
    network_info = stdout.read().decode()
    print(f"Services in app_network: {network_info}")

    # 11. Final test of external access
    print("\n🌐 Final external access test...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/' 2>&1")
    final_test = stdout.read().decode()
    print(f"Final test result: {final_test}")

    ssh.close()
    print("\n✅ Kong DNS diagnosis completed!")

if __name__ == "__main__":
    main()