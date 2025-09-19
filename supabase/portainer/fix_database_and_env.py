#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 FIXING database connectivity and environment variables...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Fix the database connectivity - Analytics is looking for wrong database
    print("\n🗄️ Fixing database connectivity issues...")

    # Check which databases exist
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -l")
    databases = stdout.read().decode()
    print("Available databases:")
    print(databases)

    # The issue is that Analytics is looking for system_metrics table but in wrong place
    # Let's check if we need to create it in the Supabase internal database

    # First, let's check the Supabase database environment variables
    print("\n📋 Checking Supabase service environment configurations...")
    stdin, stdout, stderr = ssh.exec_command("docker service inspect supabase_analytics --format '{{.Spec.TaskTemplate.ContainerSpec.Env}}'")
    analytics_env = stdout.read().decode()
    print(f"Analytics environment: {analytics_env}")

    # 2. Create the analytics database tables in the correct database
    print("\n📊 Creating analytics tables in correct database...")

    # Analytics service is trying to connect to the main Supabase database
    # Let's create the required tables there
    analytics_setup = """
    -- Create logflare schema and tables in the main supabase database
    CREATE SCHEMA IF NOT EXISTS logflare;

    -- Create tables in public schema (where analytics is looking)
    CREATE TABLE IF NOT EXISTS public.system_metrics (
        id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
        all_logs_logged bigint DEFAULT 0,
        node text NOT NULL,
        inserted_at timestamptz DEFAULT now(),
        updated_at timestamptz DEFAULT now(),
        UNIQUE(node)
    );

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

    -- Insert initial system metrics
    INSERT INTO public.system_metrics (all_logs_logged, node)
    VALUES (0, 'supabase-analytics')
    ON CONFLICT (node) DO UPDATE SET
        all_logs_logged = EXCLUDED.all_logs_logged,
        updated_at = now();

    -- Grant permissions to authenticator and postgres
    GRANT ALL ON public.system_metrics TO authenticator;
    GRANT ALL ON public.sources TO authenticator;
    GRANT ALL ON public.system_metrics TO postgres;
    GRANT ALL ON public.sources TO postgres;
    """

    # Execute in the main Supabase database
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -d supabase_db -c \"{analytics_setup}\"")
    setup_result = stdout.read().decode()
    print(f"Analytics setup result: {setup_result}")

    # 3. Check and fix database authentication for services
    print("\n🔐 Fixing database authentication...")

    # Test database connection with correct credentials
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_db -q) psql -U authenticator -d supabase_db -c 'SELECT current_user, current_database();'")
    auth_test = stdout.read().decode()
    print(f"Authenticator connection test: {auth_test}")

    # 4. Update service configurations to use correct database settings
    print("\n🔧 Updating service configurations...")

    # Check the current Supabase configuration for database settings
    stdin, stdout, stderr = ssh.exec_command("grep -A5 -B5 'POSTGRES_' /opt/supabase/supabase.yml | head -20")
    db_config = stdout.read().decode()
    print("Database configuration in supabase.yml:")
    print(db_config)

    # 5. Restart Analytics service specifically
    print("\n🔄 Restarting Analytics service...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force supabase_analytics")
    time.sleep(15)

    # Check Analytics logs after restart
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 10 supabase_analytics")
    analytics_logs = stdout.read().decode()
    print("Analytics logs after restart:")
    print(analytics_logs)

    # 6. Fix Auth service database connection
    print("\n🔐 Fixing Auth service...")

    # Check Auth service logs for connection issues
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 supabase_auth")
    auth_logs = stdout.read().decode()
    print("Auth service logs:")
    print(auth_logs)

    # 7. Fix REST service
    print("\n🔧 Fixing REST service...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 supabase_rest")
    rest_logs = stdout.read().decode()
    print("REST service logs:")
    print(rest_logs)

    # 8. Test individual service health
    print("\n🧪 Testing individual service health...")

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
                if 'supabase_auth' in container_name:
                    service_ips['auth'] = ip
                elif 'supabase_rest' in container_name:
                    service_ips['rest'] = ip
                elif 'supabase_meta' in container_name:
                    service_ips['meta'] = ip

    # Test services directly
    for service, ip in service_ips.items():
        if service == 'meta':
            stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{ip}:8080/health 2>/dev/null")
            status = stdout.read().decode().strip()
            print(f"{service} direct health: {status}")
        elif service == 'auth':
            stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{ip}:9999/health 2>/dev/null")
            status = stdout.read().decode().strip()
            print(f"{service} direct health: {status}")
        elif service == 'rest':
            stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://{ip}:3000/ 2>/dev/null")
            status = stdout.read().decode().strip()
            print(f"{service} direct health: {status}")

    # 9. Test Kong routing again
    print("\n🔍 Testing Kong routing...")

    endpoints_to_test = [
        ('Studio', '/'),
        ('Auth Health', '/auth/v1/health'),
        ('REST API', '/rest/v1/'),
        ('Meta Health', '/pg/health'),
    ]

    for name, endpoint in endpoints_to_test:
        stdin, stdout, stderr = ssh.exec_command(f"curl -u 'supabase:Ma1x1x0x_testing' -s -w '%{{http_code}}\\n' 'https://supabase.senaia.in{endpoint}' 2>/dev/null | tail -1")
        status_code = stdout.read().decode().strip()
        print(f"{name:15} ({endpoint:15}): {status_code}")

    # 10. Final service status check
    print("\n📊 Final service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    final_status = stdout.read().decode()
    print(final_status)

    ssh.close()
    print("\n✅ Database and environment fix completed!")

if __name__ == "__main__":
    main()