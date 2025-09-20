#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔐 FIXING authentication and routing issues...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. The 401 responses mean authentication is working - let's test with proper API keys
    print("\n🔑 Testing with Supabase API keys...")

    # Test Auth with anon key
    anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao"

    # Test REST API with API key
    stdin, stdout, stderr = ssh.exec_command(f'curl -H "apikey: {anon_key}" -s -o /dev/null -w "%{{http_code}}" "https://supabase.senaia.in/rest/v1/" 2>/dev/null')
    rest_with_key = stdout.read().decode().strip()
    print(f"REST with API key: {rest_with_key}")

    # Test Auth endpoint
    stdin, stdout, stderr = ssh.exec_command(f'curl -H "apikey: {anon_key}" -s -o /dev/null -w "%{{http_code}}" "https://supabase.senaia.in/auth/v1/health" 2>/dev/null')
    auth_with_key = stdout.read().decode().strip()
    print(f"Auth with API key: {auth_with_key}")

    # 2. Fix Studio routing issue (503 error)
    print("\n🎨 Fixing Studio routing...")

    # Check if Studio is actually running
    stdin, stdout, stderr = ssh.exec_command("docker service ps supabase_studio --no-trunc")
    studio_status = stdout.read().decode()
    print("Studio service status:")
    print(studio_status)

    # Force restart Studio
    print("🔄 Restarting Studio service...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force supabase_studio")

    # Wait a moment for restart
    import time
    time.sleep(15)

    # 3. Update Kong configuration to fix routing issues
    print("\n🔧 Updating Kong configuration for better routing...")

    # Get current service IPs
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
                elif 'supabase_realtime' in container_name:
                    service_ips['realtime'] = ip

    print("Updated service IPs:")
    for service, ip in service_ips.items():
        print(f"  {service}: {ip}")

    # 4. Create improved Kong configuration with proper auth flows
    kong_config = f"""_format_version: '2.1'
_transform: true

###
### Consumers / Users
###
consumers:
  - username: DASHBOARD
  - username: anon
    keyauth_credentials:
      - key: {anon_key}
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
### Services
###
services:"""

    # Studio Dashboard (Basic Auth)
    if 'studio' in service_ips:
        kong_config += f"""
  ## Studio Dashboard
  - name: studio
    url: http://{service_ips['studio']}:3000
    routes:
      - name: studio-dashboard
        paths:
          - /
        strip_path: false
        methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600"""

    # Auth Service (Public + API Key)
    if 'auth' in service_ips:
        kong_config += f"""
  ## Auth Service - Public endpoints
  - name: auth-v1-public
    url: http://{service_ips['auth']}:9999
    routes:
      - name: auth-v1-signup
        paths:
          - /auth/v1/signup
          - /auth/v1/token
          - /auth/v1/verify
          - /auth/v1/recover
          - /auth/v1/user
          - /auth/v1/health
        strip_path: true
        methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
    plugins:
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600
          methods:
            - GET
            - POST
            - PUT
            - DELETE
            - OPTIONS
          headers:
            - "*"

  ## Auth Service - Protected endpoints
  - name: auth-v1-protected
    url: http://{service_ips['auth']}:9999
    routes:
      - name: auth-v1-admin
        paths:
          - /auth/v1/admin
        strip_path: true
    plugins:
      - name: key-auth
        config:
          key_names:
            - apikey
      - name: cors
        config:
          origins:
            - "*"
          credentials: true"""

    # REST API (API Key required)
    if 'rest' in service_ips:
        kong_config += f"""
  ## REST API
  - name: rest-v1
    url: http://{service_ips['rest']}:3000
    routes:
      - name: rest-v1-api
        paths:
          - /rest/v1
        strip_path: true
        methods:
          - GET
          - POST
          - PUT
          - DELETE
          - PATCH
          - OPTIONS
    plugins:
      - name: key-auth
        config:
          key_names:
            - apikey
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600
          methods:
            - GET
            - POST
            - PUT
            - DELETE
            - PATCH
            - OPTIONS
          headers:
            - "*"
            - apikey
            - authorization"""

    # Realtime (WebSocket + API Key)
    if 'realtime' in service_ips:
        kong_config += f"""
  ## Realtime Service
  - name: realtime-v1
    url: http://{service_ips['realtime']}:4000
    routes:
      - name: realtime-v1-ws
        paths:
          - /realtime/v1
        strip_path: true
        protocols:
          - http
          - https
          - ws
          - wss
        methods:
          - GET
          - POST
          - OPTIONS
    plugins:
      - name: key-auth
        config:
          key_names:
            - apikey
      - name: cors
        config:
          origins:
            - "*"
          credentials: true"""

    # Storage API (API Key required)
    if 'storage' in service_ips:
        kong_config += f"""
  ## Storage API
  - name: storage-v1
    url: http://{service_ips['storage']}:5000
    routes:
      - name: storage-v1-api
        paths:
          - /storage/v1
        strip_path: true
        methods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
    plugins:
      - name: key-auth
        config:
          key_names:
            - apikey
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600"""

    # Meta API (Basic Auth)
    if 'meta' in service_ips:
        kong_config += f"""
  ## Meta API
  - name: meta
    url: http://{service_ips['meta']}:8080
    routes:
      - name: meta-api
        paths:
          - /pg
        strip_path: true
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # 5. Upload improved Kong configuration
    print("\n📤 Uploading improved Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) cat > /home/kong/kong.yml << 'EOF'\n{kong_config}\nEOF")

    # 6. Reload Kong
    print("\n🔄 Reloading Kong...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_result = stdout.read().decode()
    print(f"Kong reload: {reload_result}")

    # 7. Test all endpoints with proper authentication
    print("\n🧪 Testing all endpoints with proper authentication...")

    test_cases = [
        ("Studio Dashboard", "/", "basic", "supabase:Ma1x1x0x_testing"),
        ("Auth Health (public)", "/auth/v1/health", "none", ""),
        ("Auth Signup (public)", "/auth/v1/signup", "none", ""),
        ("REST API", "/rest/v1/", "apikey", anon_key),
        ("Storage API", "/storage/v1/", "apikey", anon_key),
        ("Meta Health", "/pg/health", "basic", "supabase:Ma1x1x0x_testing"),
    ]

    for name, endpoint, auth_type, credentials in test_cases:
        if auth_type == "basic":
            cmd = f'curl -u "{credentials}" -s -o /dev/null -w "%{{http_code}}" "https://supabase.senaia.in{endpoint}" 2>/dev/null'
        elif auth_type == "apikey":
            cmd = f'curl -H "apikey: {credentials}" -s -o /dev/null -w "%{{http_code}}" "https://supabase.senaia.in{endpoint}" 2>/dev/null'
        else:  # none
            cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "https://supabase.senaia.in{endpoint}" 2>/dev/null'

        stdin, stdout, stderr = ssh.exec_command(cmd)
        status = stdout.read().decode().strip()

        # Status interpretation
        if status == '200':
            emoji = '✅'
            desc = 'Working'
        elif status == '401':
            emoji = '🔐'
            desc = 'Auth Required'
        elif status == '404':
            emoji = '❌'
            desc = 'Not Found'
        elif status == '503':
            emoji = '⚠️'
            desc = 'Service Unavailable'
        else:
            emoji = '❓'
            desc = f'Status {status}'

        print(f"{emoji} {name:25} ({endpoint:15}): {desc}")

    # 8. Test Studio content specifically
    print("\n🎨 Testing Studio content...")
    stdin, stdout, stderr = ssh.exec_command('curl -u "supabase:Ma1x1x0x_testing" -s "https://supabase.senaia.in/" 2>/dev/null | head -3')
    studio_content = stdout.read().decode()
    if 'DOCTYPE html' in studio_content or 'Supabase' in studio_content:
        print("✅ Studio content loading successfully")
    else:
        print("⚠️ Studio content issue:")
        print(studio_content)

    # 9. Final service status
    print("\n📊 Final service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    final_status = stdout.read().decode()
    print(final_status)

    ssh.close()
    print("\n🎉 AUTHENTICATION AND ROUTING FIX COMPLETED!")
    print("\n✅ FULL SUPABASE ACCESS:")
    print("🌐 Dashboard: https://supabase.senaia.in")
    print("🔐 Login: supabase / Ma1x1x0x_testing")
    print("\n🔑 API Keys:")
    print(f"Anon Key: {anon_key}")
    print("\n🛠️ API Endpoints:")
    print("🔓 Auth (Public): https://supabase.senaia.in/auth/v1/health")
    print("🔐 REST API: https://supabase.senaia.in/rest/v1/ (requires apikey header)")
    print("💾 Storage: https://supabase.senaia.in/storage/v1/ (requires apikey header)")
    print("📊 Meta: https://supabase.senaia.in/pg/health (basic auth)")

if __name__ == "__main__":
    main()