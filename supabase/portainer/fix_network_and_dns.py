#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 FIXING Kong network and DNS issues...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. First, let's restart the entire stack to ensure proper network registration
    print("\n🔄 Restarting entire Supabase stack for network reset...")
    stdin, stdout, stderr = ssh.exec_command("docker stack rm supabase")
    print("Stack removed, waiting 15 seconds...")
    time.sleep(15)

    # 2. Redeploy the stack
    print("\n🚀 Redeploying Supabase stack...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker stack deploy -c supabase.yml supabase")
    output = stdout.read().decode()
    print(f"Deployment result: {output}")

    # 3. Wait for services to start
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(30)

    # 4. Check network registration
    print("\n🌐 Checking network registration after redeploy...")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}} {{.IPv4Address}}{{\"\\n\"}}{{end}}' 2>/dev/null | grep supabase")
    network_info = stdout.read().decode()
    print(f"Services in app_network:\n{network_info}")

    # 5. Check service status
    print("\n📊 Service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # 6. Wait for Kong to be fully ready
    print("\n⏳ Waiting for Kong to be ready...")
    time.sleep(20)

    # 7. Test Kong DNS resolution now
    print("\n🔍 Testing Kong DNS resolution after redeploy...")
    services_to_test = ['meta', 'storage', 'imgproxy']  # Test working services first

    for service in services_to_test:
        stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) nslookup {service} 2>&1")
        output = stdout.read().decode()
        print(f"{service}: {output.strip()}")

    # 8. Test Kong -> Meta connectivity specifically (meta should be working)
    print("\n🧪 Testing Kong -> Meta connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) wget -qO- http://meta:8080/health 2>/dev/null || echo 'Meta health check failed'")
    meta_health = stdout.read().decode().strip()
    print(f"Meta health: {meta_health}")

    # 9. Check if Studio is running and accessible
    print("\n🎨 Checking Studio status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_studio")
    studio_status = stdout.read().decode()
    print(f"Studio status: {studio_status}")

    # 10. Force restart Studio specifically to ensure it registers
    print("\n🔄 Force restarting Studio...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force supabase_studio")
    time.sleep(15)

    # 11. Test Studio DNS after restart
    print("\n🔍 Testing Studio DNS after restart...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) nslookup studio 2>&1")
    studio_dns = stdout.read().decode()
    print(f"Studio DNS: {studio_dns}")

    # 12. If Studio still not resolving, check its network connectivity
    print("\n🌐 Checking Studio network connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}} {{.IPv4Address}}{{\"\\n\"}}{{end}}' | grep studio")
    studio_network = stdout.read().decode()
    print(f"Studio in network: {studio_network}")

    # 13. Alternative: Test using IP if DNS fails
    if "studio" in network_info or studio_network:
        print("\n🧪 Testing Studio by IP...")
        # Extract Studio IP from network info
        stdin, stdout, stderr = ssh.exec_command("docker inspect $(docker ps -f name=supabase_studio -q) --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null")
        studio_ip = stdout.read().decode().strip()
        if studio_ip:
            print(f"Studio IP: {studio_ip}")
            stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) wget -qO- http://{studio_ip}:3000/ 2>/dev/null | head -5 || echo 'Studio IP test failed'")
            studio_ip_test = stdout.read().decode()
            print(f"Studio IP test: {studio_ip_test}")

    # 14. Final external test
    print("\n🌐 Final external access test...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/' 2>&1")
    final_test = stdout.read().decode()
    print(f"Final access test: {final_test}")

    # 15. Test specific Studio path
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/project/default' 2>&1")
    studio_path_test = stdout.read().decode()
    print(f"Studio path test: {studio_path_test}")

    ssh.close()
    print("\n✅ Network and DNS fix completed!")

if __name__ == "__main__":
    main()