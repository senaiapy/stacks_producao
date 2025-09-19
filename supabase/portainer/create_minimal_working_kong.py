#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🎯 CREATING MINIMAL WORKING Kong configuration...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Get current running services with IPs
    print("\n🌐 Getting running service IPs...")
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
                elif 'supabase_meta' in container_name:
                    service_ips['meta'] = ip
                elif 'supabase_storage' in container_name:
                    service_ips['storage'] = ip

    print("Available services:")
    for service, ip in service_ips.items():
        print(f"  {service}: {ip}")

    # 2. Create a minimal Kong configuration that only routes to working services
    print("\n🔧 Creating minimal working Kong configuration...")

    # Only configure routes for services that are actually running
    minimal_kong_config = f"""_format_version: '2.1'
_transform: true

###
### Consumers / Users
###
consumers:
  - username: DASHBOARD
  - username: anon
    keyauth_credentials:
      - key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao
  - username: service_role
    keyauth_credentials:
      - key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI

###
### Access Control List
###
acls:
  - consumer: anon
    group: anon
  - consumer: service_role
    group: admin

###
### Dashboard credentials
###
basicauth_credentials:
  - consumer: DASHBOARD
    username: supabase
    password: Ma1x1x0x_testing

###
### API Routes - Only Working Services
###
services:"""

    # Add Studio service if available
    if 'studio' in service_ips:
        minimal_kong_config += f"""
  - name: studio
    url: http://{service_ips['studio']}:3000
    routes:
      - name: studio-all
        paths:
          - /
        strip_path: false
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # Add Meta service if available
    if 'meta' in service_ips:
        minimal_kong_config += f"""
  - name: meta
    url: http://{service_ips['meta']}:8080
    routes:
      - name: meta-all
        paths:
          - /meta
        strip_path: true
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # Add Storage service if available
    if 'storage' in service_ips:
        minimal_kong_config += f"""
  - name: storage
    url: http://{service_ips['storage']}:5000
    routes:
      - name: storage-all
        paths:
          - /storage
        strip_path: true
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # 3. Upload the minimal configuration
    print("\n📤 Uploading minimal Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) cat > /home/kong/kong.yml << 'EOF'\n{minimal_kong_config}\nEOF")

    # 4. Verify the configuration was uploaded
    print("\n🔍 Verifying configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cat /home/kong/kong.yml")
    config_check = stdout.read().decode()
    print("Kong configuration:")
    print(config_check[:500] + "..." if len(config_check) > 500 else config_check)

    # 5. Reload Kong
    print("\n🔄 Reloading Kong...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_result = stdout.read().decode()
    print(f"Kong reload: {reload_result}")

    # 6. Test Kong health
    print("\n🧪 Testing Kong health...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health")
    health_result = stdout.read().decode()
    print(f"Kong health: {health_result}")

    # 7. Test external access
    print("\n🌐 Testing external access...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' 'https://supabase.senaia.in/' 2>/dev/null")
    status_code = stdout.read().decode().strip()
    print(f"External access status: {status_code}")

    # 8. Test Studio specifically
    if 'studio' in service_ips:
        print("\n🎨 Testing Studio access...")
        stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/' 2>&1 | head -3")
        studio_test = stdout.read().decode()
        print(f"Studio access: {studio_test}")

    # 9. Test Meta service
    if 'meta' in service_ips:
        print("\n📊 Testing Meta service...")
        stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/meta/health' 2>&1")
        meta_test = stdout.read().decode()
        print(f"Meta access: {meta_test}")

    ssh.close()
    print("\n🎉 MINIMAL KONG CONFIGURATION COMPLETED!")
    print("\n✅ ACCESS SUPABASE:")
    print("URL: https://supabase.senaia.in")
    print("Username: supabase")
    print("Password: Ma1x1x0x_testing")

if __name__ == "__main__":
    main()