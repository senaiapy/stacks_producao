#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 DEBUGGING Kong configuration issue...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Check what's actually in Kong configuration file
    print("\n📋 Checking Kong configuration file (first 100 lines)...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cat /home/kong/kong.yml | head -100")
    kong_config = stdout.read().decode()
    print(kong_config)

    # 2. Check what services are defined and their URLs
    print("\n🔍 Looking for service definitions...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) grep -A5 -B5 'url:' /home/kong/kong.yml")
    service_urls = stdout.read().decode()
    print("Service URLs found:")
    print(service_urls)

    # 3. Check if AUTH and REST services are actually running
    print("\n📊 Checking AUTH and REST service status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_auth supabase_rest --no-trunc")
    auth_rest_status = stdout.read().decode()
    print(auth_rest_status)

    # 4. Test if Kong can reach studio directly by IP
    print("\n🧪 Testing Kong -> Studio direct connection...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) wget -qO- --timeout=5 http://10.0.2.109:3000/ 2>&1 | head -3")
    direct_test = stdout.read().decode()
    print(f"Direct Studio test: {direct_test}")

    # 5. Check which services Kong is trying to route to
    print("\n🔍 Checking Kong routing configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) grep -A10 -B10 'routes:' /home/kong/kong.yml | head -50")
    routes_config = stdout.read().decode()
    print("Routes configuration:")
    print(routes_config)

    # 6. Check if there's an error in Kong admin API
    print("\n🔧 Checking Kong admin API...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) curl -s http://localhost:8001/status 2>/dev/null || echo 'Kong admin API not accessible'")
    kong_admin = stdout.read().decode()
    print(f"Kong admin status: {kong_admin}")

    # 7. Check Kong error logs
    print("\n📋 Checking Kong error logs...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) ls -la /usr/local/kong/logs/ 2>/dev/null || echo 'Kong logs directory not found'")
    logs_dir = stdout.read().decode()
    print(f"Kong logs directory: {logs_dir}")

    # 8. Check Kong process status
    print("\n🔍 Checking Kong process status...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) ps aux | grep kong")
    kong_processes = stdout.read().decode()
    print(f"Kong processes: {kong_processes}")

    ssh.close()
    print("\n✅ Kong configuration debug completed!")

if __name__ == "__main__":
    main()