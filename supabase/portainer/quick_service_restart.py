#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚀 QUICK SERVICE RESTART for all Supabase services...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Re-enable Analytics
    print("\n📊 Re-enabling Analytics...")
    stdin, stdout, stderr = ssh.exec_command("docker service scale supabase_analytics=1")

    # 2. Restart services quickly
    services = ['auth', 'rest', 'realtime']

    for service in services:
        print(f"🔄 Restarting {service}...")
        stdin, stdout, stderr = ssh.exec_command(f"docker service update --force supabase_{service}")

    # 3. Check service status
    print("\n📊 Service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    status = stdout.read().decode()
    print(status)

    # 4. Get service IPs
    print("\n🌐 Getting service IPs...")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}},{{.IPv4Address}}{{\"\\n\"}}{{end}}' | grep supabase")
    network_info = stdout.read().decode()

    service_ips = {}
    for line in network_info.strip().split('\n'):
        if line:
            parts = line.split(',')
            if len(parts) == 2:
                container_name = parts[0]
                ip = parts[1].split('/')[0]

                if 'supabase_studio' in container_name:
                    service_ips['studio'] = ip
                elif 'supabase_auth' in container_name:
                    service_ips['auth'] = ip
                elif 'supabase_rest' in container_name:
                    service_ips['rest'] = ip
                elif 'supabase_meta' in container_name:
                    service_ips['meta'] = ip
                elif 'supabase_storage' in container_name:
                    service_ips['storage'] = ip

    print("Service IPs:")
    for service, ip in service_ips.items():
        print(f"  {service}: {ip}")

    # 5. Create working Kong configuration
    kong_config = f"""_format_version: '2.1'
_transform: true

consumers:
  - username: DASHBOARD
  - username: anon
    keyauth_credentials:
      - key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao

basicauth_credentials:
  - consumer: DASHBOARD
    username: supabase
    password: Ma1x1x0x_testing

services:"""

    # Add services with their IPs
    if 'studio' in service_ips:
        kong_config += f"""
  - name: studio
    url: http://{service_ips['studio']}:3000
    routes:
      - name: studio-root
        paths: ["/"]
        strip_path: false
    plugins:
      - name: basic-auth"""

    if 'auth' in service_ips:
        kong_config += f"""
  - name: auth-v1
    url: http://{service_ips['auth']}:9999
    routes:
      - name: auth-v1-all
        paths: ["/auth/v1"]
        strip_path: true
    plugins:
      - name: cors"""

    if 'rest' in service_ips:
        kong_config += f"""
  - name: rest-v1
    url: http://{service_ips['rest']}:3000
    routes:
      - name: rest-v1-all
        paths: ["/rest/v1"]
        strip_path: true
    plugins:
      - name: cors
      - name: key-auth"""

    if 'meta' in service_ips:
        kong_config += f"""
  - name: meta
    url: http://{service_ips['meta']}:8080
    routes:
      - name: meta-all
        paths: ["/pg"]
        strip_path: true
    plugins:
      - name: basic-auth"""

    if 'storage' in service_ips:
        kong_config += f"""
  - name: storage-v1
    url: http://{service_ips['storage']}:5000
    routes:
      - name: storage-v1-all
        paths: ["/storage/v1"]
        strip_path: true
    plugins:
      - name: cors
      - name: key-auth"""

    # 6. Upload Kong config
    print("\n📤 Uploading Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) cat > /home/kong/kong.yml << 'EOF'\n{kong_config}\nEOF")

    # 7. Reload Kong
    print("\n🔄 Reloading Kong...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")

    # 8. Test endpoints
    print("\n🧪 Testing endpoints...")

    endpoints = [
        ('Studio', '/', 'basic'),
        ('Auth', '/auth/v1/health', 'none'),
        ('REST', '/rest/v1/', 'none'),
        ('Meta', '/pg/health', 'basic'),
        ('Storage', '/storage/v1/', 'none'),
    ]

    for name, endpoint, auth_type in endpoints:
        if auth_type == 'basic':
            cmd = f"curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{{http_code}}' 'https://supabase.senaia.in{endpoint}' 2>/dev/null"
        else:
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' 'https://supabase.senaia.in{endpoint}' 2>/dev/null"

        stdin, stdout, stderr = ssh.exec_command(cmd)
        status = stdout.read().decode().strip()

        # Status interpretation
        if status == '200':
            emoji = '✅'
        elif status == '401':
            emoji = '🔐'  # Auth required
        elif status == '404':
            emoji = '❌'
        else:
            emoji = '⚠️'

        print(f"{emoji} {name:8} {endpoint:15}: {status}")

    ssh.close()
    print("\n✅ Quick service restart completed!")
    print("\n🌐 Access: https://supabase.senaia.in")
    print("🔐 Login: supabase / Ma1x1x0x_testing")

if __name__ == "__main__":
    main()