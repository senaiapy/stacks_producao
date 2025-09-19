#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 FIXING remaining Supabase services: Auth, REST, Realtime, Analytics...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. First check current service status
    print("\n📊 Current service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    current_status = stdout.read().decode()
    print(current_status)

    # 2. Check logs for failing services to understand issues
    print("\n📋 Checking service logs for errors...")

    failing_services = ['auth', 'rest', 'realtime', 'analytics']
    service_issues = {}

    for service in failing_services:
        print(f"\n🔍 Checking {service} logs...")
        stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 5 supabase_{service} 2>/dev/null")
        logs = stdout.read().decode()
        if logs.strip():
            print(f"{service} logs:")
            print(logs)
            service_issues[service] = logs

    # 3. Check database connectivity for auth services
    print("\n🗄️ Testing database connectivity for services...")

    # Test connection as authenticator user
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_db -q) psql -U authenticator -d supabase_db -c 'SELECT current_user, current_database();' 2>/dev/null || echo 'Authenticator DB connection failed'")
    auth_db_test = stdout.read().decode()
    print(f"Auth DB test: {auth_db_test}")

    # 4. Fix Analytics service by ensuring logflare database setup
    print("\n📊 Fixing Analytics service database setup...")

    analytics_setup_sql = """
    -- Connect to the correct database
    \\c supabase_db;

    -- Create missing tables for logflare/analytics
    CREATE TABLE IF NOT EXISTS public.sources (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        name text NOT NULL,
        token text UNIQUE NOT NULL,
        public_token text UNIQUE,
        favorite boolean DEFAULT false,
        bigquery_table_ttl integer,
        api_quota integer,
        webhook_notification_url text,
        slack_hook_url text,
        bq_table_partition_type text,
        custom_event_message_keys text[],
        log_events_updated_at timestamptz DEFAULT now(),
        notifications_every integer,
        lock_schema boolean DEFAULT false,
        validate_schema boolean DEFAULT false,
        drop_lql_filters boolean DEFAULT false,
        drop_lql_string text,
        v2_pipeline boolean DEFAULT false,
        suggested_keys text[],
        user_id uuid,
        notifications jsonb,
        inserted_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS public.system_metrics (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        all_logs_logged bigint DEFAULT 0,
        node text NOT NULL,
        inserted_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now()
    );

    -- Grant permissions
    GRANT ALL ON public.sources TO authenticator;
    GRANT ALL ON public.system_metrics TO authenticator;

    -- Insert initial data
    INSERT INTO public.system_metrics (all_logs_logged, node)
    VALUES (0, 'supabase-analytics')
    ON CONFLICT DO NOTHING;
    """

    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -f- <<< \"{analytics_setup_sql}\"")
    analytics_result = stdout.read().decode()
    print(f"Analytics DB setup: {analytics_result}")

    # 5. Update Supabase configuration with correct database settings
    print("\n🔧 Updating Supabase service configurations...")

    # Read current supabase.yml and fix database connections
    stdin, stdout, stderr = ssh.exec_command("cat /opt/supabase/supabase.yml | head -200")
    current_config = stdout.read().decode()

    # Check if services are pointing to the right database
    if 'POSTGRES_DB=supabase_database' in current_config:
        print("📝 Updating database name from supabase_database to supabase_db...")
        stdin, stdout, stderr = ssh.exec_command("sed -i 's/supabase_database/supabase_db/g' /opt/supabase/supabase.yml")

    # 6. Restart services in correct order
    print("\n🔄 Restarting services in dependency order...")

    restart_order = ['analytics', 'auth', 'rest', 'realtime']

    for service in restart_order:
        print(f"Restarting {service}...")
        stdin, stdout, stderr = ssh.exec_command(f"docker service update --force supabase_{service}")
        time.sleep(10)  # Wait between restarts

        # Check if service started successfully
        stdin, stdout, stderr = ssh.exec_command(f"docker service ps supabase_{service} --filter desired-state=running --no-trunc")
        service_status = stdout.read().decode()
        if 'Running' in service_status:
            print(f"✅ {service} started successfully")
        else:
            print(f"⚠️ {service} still having issues")

    # 7. Wait for all services to stabilize
    print("\n⏳ Waiting for services to stabilize...")
    time.sleep(30)

    # 8. Get current service IPs for Kong configuration
    print("\n🌐 Getting service IP addresses for Kong routing...")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}},{{.IPv4Address}}{{\"\\n\"}}{{end}}' | grep supabase")
    network_info = stdout.read().decode()

    service_ips = {}
    for line in network_info.strip().split('\n'):
        if line:
            parts = line.split(',')
            if len(parts) == 2:
                container_name = parts[0]
                ip = parts[1].split('/')[0]

                if 'supabase_auth' in container_name:
                    service_ips['auth'] = ip
                elif 'supabase_rest' in container_name:
                    service_ips['rest'] = ip
                elif 'supabase_realtime' in container_name:
                    service_ips['realtime'] = ip
                elif 'supabase_analytics' in container_name:
                    service_ips['analytics'] = ip
                elif 'supabase_studio' in container_name:
                    service_ips['studio'] = ip
                elif 'supabase_meta' in container_name:
                    service_ips['meta'] = ip
                elif 'supabase_storage' in container_name:
                    service_ips['storage'] = ip

    print("Available service IPs:")
    for service, ip in service_ips.items():
        print(f"  {service}: {ip}")

    # 9. Create comprehensive Kong configuration with all services
    print("\n🔧 Creating comprehensive Kong configuration...")

    kong_config = f"""_format_version: '2.1'
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
### API Routes
###
services:"""

    # Add Studio service
    if 'studio' in service_ips:
        kong_config += f"""
  ## Studio Dashboard
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

    # Add Auth service
    if 'auth' in service_ips:
        kong_config += f"""
  ## Auth Service
  - name: auth-v1
    url: http://{service_ips['auth']}:9999
    routes:
      - name: auth-v1-all
        paths:
          - /auth/v1
        strip_path: true
    plugins:
      - name: cors"""

    # Add REST service
    if 'rest' in service_ips:
        kong_config += f"""
  ## REST API
  - name: rest-v1
    url: http://{service_ips['rest']}:3000
    routes:
      - name: rest-v1-all
        paths:
          - /rest/v1
        strip_path: true
    plugins:
      - name: cors
      - name: key-auth"""

    # Add Realtime service
    if 'realtime' in service_ips:
        kong_config += f"""
  ## Realtime
  - name: realtime-v1
    url: http://{service_ips['realtime']}:4000
    routes:
      - name: realtime-v1-all
        paths:
          - /realtime/v1
        strip_path: true
    plugins:
      - name: cors
      - name: key-auth"""

    # Add Meta service
    if 'meta' in service_ips:
        kong_config += f"""
  ## Meta
  - name: meta
    url: http://{service_ips['meta']}:8080
    routes:
      - name: meta-all
        paths:
          - /pg
        strip_path: true
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # Add Storage service
    if 'storage' in service_ips:
        kong_config += f"""
  ## Storage
  - name: storage-v1
    url: http://{service_ips['storage']}:5000
    routes:
      - name: storage-v1-all
        paths:
          - /storage/v1
        strip_path: true
    plugins:
      - name: cors
      - name: key-auth"""

    # 10. Upload new Kong configuration
    print("\n📤 Uploading comprehensive Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) cat > /home/kong/kong.yml << 'EOF'\n{kong_config}\nEOF")

    # 11. Reload Kong
    print("\n🔄 Reloading Kong with new configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_result = stdout.read().decode()
    print(f"Kong reload: {reload_result}")

    # 12. Test Kong health
    print("\n🧪 Testing Kong health...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health")
    health_result = stdout.read().decode()
    print(f"Kong health: {health_result}")

    # 13. Check final service status
    print("\n📊 Final service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    final_status = stdout.read().decode()
    print(final_status)

    # 14. Test API endpoints
    print("\n🧪 Testing API endpoints...")

    endpoints_to_test = [
        ('Studio', '/'),
        ('Auth', '/auth/v1/health'),
        ('REST', '/rest/v1/'),
        ('Meta', '/pg/health'),
        ('Storage', '/storage/v1/'),
    ]

    for name, endpoint in endpoints_to_test:
        stdin, stdout, stderr = ssh.exec_command(f"curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{{http_code}}' 'https://supabase.senaia.in{endpoint}' 2>/dev/null")
        status_code = stdout.read().decode().strip()
        print(f"{name:10} ({endpoint:15}): {status_code}")

    ssh.close()
    print("\n✅ Remaining services fix completed!")

if __name__ == "__main__":
    main()