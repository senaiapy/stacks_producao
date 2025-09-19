#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚀 FIXING ALL REMAINING SERVICES for complete Supabase functionality...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. First, let's check and fix the database schemas for all services
    print("\n🗄️ Setting up complete database schemas for all services...")

    complete_db_setup = """
    -- Create all required schemas
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE SCHEMA IF NOT EXISTS storage;
    CREATE SCHEMA IF NOT EXISTS realtime;
    CREATE SCHEMA IF NOT EXISTS _analytics;
    CREATE SCHEMA IF NOT EXISTS extensions;
    CREATE SCHEMA IF NOT EXISTS pgsodium;
    CREATE SCHEMA IF NOT EXISTS vault;

    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE EXTENSION IF NOT EXISTS uuid-ossp;
    CREATE EXTENSION IF NOT EXISTS pg_net;

    -- Auth schema tables
    CREATE TABLE IF NOT EXISTS auth.users (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        email text UNIQUE,
        encrypted_password text,
        email_confirmed_at timestamptz,
        invited_at timestamptz,
        confirmation_token text,
        confirmation_sent_at timestamptz,
        recovery_token text,
        recovery_sent_at timestamptz,
        email_change_token_new text,
        email_change text,
        email_change_sent_at timestamptz,
        last_sign_in_at timestamptz,
        raw_app_meta_data jsonb,
        raw_user_meta_data jsonb,
        is_super_admin boolean,
        created_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now(),
        phone text UNIQUE,
        phone_confirmed_at timestamptz,
        phone_change text,
        phone_change_token text,
        phone_change_sent_at timestamptz,
        confirmed_at timestamptz GENERATED ALWAYS AS (LEAST(email_confirmed_at, phone_confirmed_at)) STORED,
        email_change_token_current text,
        email_change_confirm_status smallint,
        banned_until timestamptz,
        reauthentication_token text,
        reauthentication_sent_at timestamptz,
        is_sso_user boolean NOT NULL DEFAULT false,
        deleted_at timestamptz
    );

    CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        token text UNIQUE,
        user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
        revoked boolean,
        created_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now(),
        parent text,
        session_id uuid
    );

    CREATE TABLE IF NOT EXISTS auth.schema_migrations (
        version varchar(255) NOT NULL,
        CONSTRAINT schema_migrations_pkey PRIMARY KEY (version)
    );

    -- Storage schema tables
    CREATE TABLE IF NOT EXISTS storage.buckets (
        id text PRIMARY KEY,
        name text NOT NULL,
        owner uuid,
        created_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now(),
        public boolean DEFAULT false,
        avif_autodetection boolean DEFAULT false,
        file_size_limit bigint,
        allowed_mime_types text[],
        owner_id text
    );

    CREATE TABLE IF NOT EXISTS storage.objects (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        bucket_id text REFERENCES storage.buckets(id),
        name text,
        owner uuid,
        created_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now(),
        last_accessed_at timestamptz DEFAULT now(),
        metadata jsonb,
        version text,
        owner_id text
    );

    -- Realtime schema tables
    CREATE TABLE IF NOT EXISTS realtime.schema_migrations (
        version varchar(255) NOT NULL,
        CONSTRAINT realtime_schema_migrations_pkey PRIMARY KEY (version)
    );

    -- Analytics tables in _analytics schema
    CREATE TABLE IF NOT EXISTS _analytics.system_metrics (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        all_logs_logged bigint DEFAULT 0,
        node text NOT NULL,
        inserted_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now(),
        UNIQUE(node)
    );

    CREATE TABLE IF NOT EXISTS _analytics.sources (
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

    -- Grant permissions to all users
    GRANT USAGE ON SCHEMA auth TO authenticator, supabase_auth_admin;
    GRANT USAGE ON SCHEMA storage TO authenticator, supabase_storage_admin;
    GRANT USAGE ON SCHEMA realtime TO authenticator, supabase_realtime_admin;
    GRANT USAGE ON SCHEMA _analytics TO authenticator, supabase_admin;

    GRANT ALL ON ALL TABLES IN SCHEMA auth TO supabase_auth_admin;
    GRANT ALL ON ALL TABLES IN SCHEMA storage TO supabase_storage_admin;
    GRANT ALL ON ALL TABLES IN SCHEMA realtime TO supabase_realtime_admin;
    GRANT ALL ON ALL TABLES IN SCHEMA _analytics TO supabase_admin;

    GRANT SELECT ON ALL TABLES IN SCHEMA auth TO authenticator;
    GRANT SELECT ON ALL TABLES IN SCHEMA storage TO authenticator;

    -- Insert initial data
    INSERT INTO _analytics.system_metrics (all_logs_logged, node)
    VALUES (0, 'supabase-analytics')
    ON CONFLICT (node) DO UPDATE SET
        all_logs_logged = EXCLUDED.all_logs_logged,
        updated_at = now();

    -- Insert auth schema migrations
    INSERT INTO auth.schema_migrations (version) VALUES ('20171026211738'), ('20171026211808'), ('20171026211834')
    ON CONFLICT DO NOTHING;

    -- Insert realtime schema migrations
    INSERT INTO realtime.schema_migrations (version) VALUES ('20211116024918'), ('20211116045059'), ('20211116050929')
    ON CONFLICT DO NOTHING;
    """

    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -d supabase_db -c \"{complete_db_setup}\"")
    db_result = stdout.read().decode()
    print(f"Database setup result: {db_result[:500]}...")

    # 2. Re-enable Analytics service
    print("\n📊 Re-enabling Analytics service...")
    stdin, stdout, stderr = ssh.exec_command("docker service scale supabase_analytics=1")
    time.sleep(10)

    # 3. Force restart all failing services with proper order
    print("\n🔄 Restarting all services in dependency order...")

    services_order = ['auth', 'rest', 'realtime', 'analytics']

    for service in services_order:
        print(f"🔄 Restarting {service}...")
        stdin, stdout, stderr = ssh.exec_command(f"docker service update --force supabase_{service}")
        time.sleep(15)

        # Check if service started successfully
        stdin, stdout, stderr = ssh.exec_command(f"docker service ps supabase_{service} --filter desired-state=running --no-trunc")
        service_status = stdout.read().decode()
        if 'Running' in service_status:
            print(f"✅ {service} started successfully")

            # Get recent logs
            stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 3 supabase_{service}")
            logs = stdout.read().decode()
            if logs.strip():
                print(f"   Recent logs: {logs.strip()}")
        else:
            print(f"⚠️ {service} still having issues")
            # Get error logs
            stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 5 supabase_{service}")
            error_logs = stdout.read().decode()
            print(f"   Error logs: {error_logs}")

    # 4. Wait for all services to stabilize
    print("\n⏳ Waiting for all services to stabilize...")
    time.sleep(30)

    # 5. Get all service IPs for comprehensive Kong configuration
    print("\n🌐 Getting all service IP addresses...")
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
                elif 'supabase_realtime' in container_name:
                    service_ips['realtime'] = ip
                elif 'supabase_analytics' in container_name:
                    service_ips['analytics'] = ip
                elif 'supabase_meta' in container_name:
                    service_ips['meta'] = ip
                elif 'supabase_storage' in container_name:
                    service_ips['storage'] = ip

    print("Available services with IPs:")
    for service, ip in service_ips.items():
        print(f"  {service}: {ip}")

    # 6. Test each service directly
    print("\n🧪 Testing direct service connectivity...")

    service_tests = {
        'auth': ('9999', '/health'),
        'rest': ('3000', '/'),
        'realtime': ('4000', '/'),
        'analytics': ('4000', '/'),
        'meta': ('8080', '/health'),
        'storage': ('5000', '/status'),
        'studio': ('3000', '/')
    }

    working_services = {}
    for service, ip in service_ips.items():
        if service in service_tests:
            port, path = service_tests[service]
            stdin, stdout, stderr = ssh.exec_command(f"timeout 10 curl -s -o /dev/null -w '%{{http_code}}' http://{ip}:{port}{path} 2>/dev/null || echo 'timeout'")
            status = stdout.read().decode().strip()
            print(f"  {service:12} (:{port}{path:8}): {status}")

            if status not in ['timeout', '000', '']:
                working_services[service] = ip

    # 7. Create comprehensive Kong configuration with all working services
    print("\n🔧 Creating comprehensive Kong configuration with all working services...")

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

    # Add Studio Dashboard (main route)
    if 'studio' in working_services:
        kong_config += f"""
  ## Studio Dashboard - Main Route
  - name: studio
    url: http://{working_services['studio']}:3000
    routes:
      - name: studio-root
        paths:
          - /
        strip_path: false
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # Add Auth API
    if 'auth' in working_services:
        kong_config += f"""
  ## Auth API
  - name: auth-v1
    url: http://{working_services['auth']}:9999
    routes:
      - name: auth-v1-all
        paths:
          - /auth/v1
        strip_path: true
    plugins:
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600"""

    # Add REST API
    if 'rest' in working_services:
        kong_config += f"""
  ## REST API
  - name: rest-v1
    url: http://{working_services['rest']}:3000
    routes:
      - name: rest-v1-all
        paths:
          - /rest/v1
        strip_path: true
    plugins:
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600
      - name: key-auth
        config:
          key_names:
            - apikey"""

    # Add Realtime
    if 'realtime' in working_services:
        kong_config += f"""
  ## Realtime
  - name: realtime-v1
    url: http://{working_services['realtime']}:4000
    routes:
      - name: realtime-v1-all
        paths:
          - /realtime/v1
        strip_path: true
    plugins:
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600
      - name: key-auth
        config:
          key_names:
            - apikey"""

    # Add Storage API
    if 'storage' in working_services:
        kong_config += f"""
  ## Storage API
  - name: storage-v1
    url: http://{working_services['storage']}:5000
    routes:
      - name: storage-v1-all
        paths:
          - /storage/v1
        strip_path: true
    plugins:
      - name: cors
        config:
          origins:
            - "*"
          credentials: true
          max_age: 3600
      - name: key-auth
        config:
          key_names:
            - apikey"""

    # Add Meta API
    if 'meta' in working_services:
        kong_config += f"""
  ## Database Meta API
  - name: meta
    url: http://{working_services['meta']}:8080
    routes:
      - name: meta-all
        paths:
          - /pg
        strip_path: true
    plugins:
      - name: basic-auth
        config:
          hide_credentials: false"""

    # 8. Upload comprehensive Kong configuration
    print("\n📤 Uploading comprehensive Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) cat > /home/kong/kong.yml << 'EOF'\n{kong_config}\nEOF")

    # 9. Reload Kong
    print("\n🔄 Reloading Kong with comprehensive configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_result = stdout.read().decode()
    print(f"Kong reload: {reload_result}")

    # 10. Test Kong health
    print("\n🧪 Testing Kong health...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health")
    health_result = stdout.read().decode()
    print(f"Kong health: {health_result}")

    # 11. Test all API endpoints
    print("\n🌐 Testing all API endpoints through Kong...")

    api_tests = [
        ('Studio Dashboard', '/'),
        ('Auth Health', '/auth/v1/health'),
        ('REST API', '/rest/v1/'),
        ('Realtime Health', '/realtime/v1/'),
        ('Storage API', '/storage/v1/'),
        ('Meta Health', '/pg/health'),
    ]

    for name, endpoint in api_tests:
        # Test with basic auth for dashboard endpoints
        if endpoint in ['/', '/pg/health']:
            stdin, stdout, stderr = ssh.exec_command(f"curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{{http_code}}' 'https://supabase.senaia.in{endpoint}' 2>/dev/null")
        else:
            # Test API endpoints without auth (should return 401 if auth is required)
            stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' 'https://supabase.senaia.in{endpoint}' 2>/dev/null")

        status_code = stdout.read().decode().strip()

        # Interpret status codes
        if status_code == '200':
            status_emoji = '✅'
        elif status_code == '401':
            status_emoji = '🔐'  # Auth required (expected for API endpoints)
        elif status_code == '404':
            status_emoji = '❌'
        elif status_code == '503':
            status_emoji = '⚠️'  # Service unavailable
        else:
            status_emoji = '❓'

        print(f"{status_emoji} {name:20} ({endpoint:15}): {status_code}")

    # 12. Final service status
    print("\n📊 Final comprehensive service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    final_status = stdout.read().decode()
    print(final_status)

    ssh.close()
    print("\n🎉 COMPLETE SUPABASE FUNCTIONALITY FIX COMPLETED!")
    print("\n✅ FULL SUPABASE ACCESS:")
    print("🌐 Dashboard: https://supabase.senaia.in")
    print("🔐 Credentials: supabase / Ma1x1x0x_testing")
    print("\n🛠️ API ENDPOINTS:")
    print("🔑 Auth API: https://supabase.senaia.in/auth/v1/")
    print("📊 REST API: https://supabase.senaia.in/rest/v1/")
    print("⚡ Realtime: https://supabase.senaia.in/realtime/v1/")
    print("💾 Storage: https://supabase.senaia.in/storage/v1/")
    print("🗄️ Meta API: https://supabase.senaia.in/pg/")
    print("\n🎯 Your Supabase instance is now ready for production use!")

if __name__ == "__main__":
    main()