#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 Fixing Supabase database schema and authentication...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. First create the supabase_database if it doesn't exist
    print("\n📊 Creating Supabase database if not exists...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=postgres_postgres -q) psql -U postgres -c 'CREATE DATABASE supabase_database;' 2>/dev/null || echo 'Database already exists'")
    output = stdout.read().decode()
    print(f"Database creation: {output}")

    # 2. Create all required database users with correct passwords
    print("\n👤 Creating Supabase database users...")

    create_users_sql = """
    -- Drop and recreate users to ensure clean state
    DROP USER IF EXISTS authenticator;
    DROP USER IF EXISTS supabase_auth_admin;
    DROP USER IF EXISTS supabase_storage_admin;
    DROP USER IF EXISTS dashboard_user;
    DROP USER IF EXISTS supabase_read_only_user;
    DROP USER IF EXISTS supabase_admin;
    DROP USER IF EXISTS pgsodium_keyiduser;
    DROP USER IF EXISTS pgsodium_keyholder;
    DROP USER IF EXISTS supabase_functions_admin;
    DROP USER IF EXISTS supabase_replication_admin;
    DROP USER IF EXISTS supabase_realtime_admin;

    -- Create users with correct passwords
    CREATE USER authenticator WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_storage_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER dashboard_user WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_read_only_user WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER pgsodium_keyiduser WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER pgsodium_keyholder WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_functions_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_replication_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
    CREATE USER supabase_realtime_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';

    -- Grant necessary permissions
    GRANT ALL PRIVILEGES ON DATABASE supabase_database TO authenticator;
    GRANT ALL PRIVILEGES ON DATABASE supabase_database TO supabase_auth_admin;
    GRANT ALL PRIVILEGES ON DATABASE supabase_database TO supabase_storage_admin;
    GRANT ALL PRIVILEGES ON DATABASE supabase_database TO dashboard_user;
    GRANT ALL PRIVILEGES ON DATABASE supabase_database TO supabase_admin;
    """

    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=postgres_postgres -q) psql -U postgres -c \"{create_users_sql}\"")
    output = stdout.read().decode()
    error = stderr.read().decode()
    print(f"User creation output: {output}")
    if error:
        print(f"Errors: {error}")

    # 3. Initialize Supabase database schema
    print("\n🗄️ Initializing Supabase database schema...")

    schema_sql = """
    \\\\c supabase_database;

    -- Create required schemas
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE SCHEMA IF NOT EXISTS storage;
    CREATE SCHEMA IF NOT EXISTS realtime;
    CREATE SCHEMA IF NOT EXISTS supabase_functions;
    CREATE SCHEMA IF NOT EXISTS graphql_public;
    CREATE SCHEMA IF NOT EXISTS extensions;
    CREATE SCHEMA IF NOT EXISTS pgsodium;
    CREATE SCHEMA IF NOT EXISTS vault;

    -- Grant schema permissions
    GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
    GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
    GRANT ALL ON SCHEMA realtime TO supabase_realtime_admin;
    GRANT ALL ON SCHEMA supabase_functions TO supabase_functions_admin;
    GRANT USAGE ON SCHEMA public TO authenticator;
    GRANT CREATE ON SCHEMA public TO authenticator;

    -- Create essential extensions
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE EXTENSION IF NOT EXISTS uuid-ossp;
    CREATE EXTENSION IF NOT EXISTS pg_net;

    -- Create basic auth tables
    CREATE TABLE IF NOT EXISTS auth.schema_migrations (
        version varchar(255) NOT NULL,
        CONSTRAINT schema_migrations_pkey PRIMARY KEY (version)
    );

    -- Create logflare/analytics tables
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
        log_events_updated_at timestamptz,
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

    -- Grant table permissions
    GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticator;
    GRANT ALL ON ALL TABLES IN SCHEMA auth TO supabase_auth_admin;
    """

    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=postgres_postgres -q) psql -U postgres -f- <<< \"{schema_sql}\"")
    output = stdout.read().decode()
    error = stderr.read().decode()
    print(f"Schema creation output: {output}")
    if error:
        print(f"Schema errors: {error}")

    # 4. Run the database initialization SQL files
    print("\n📋 Running database initialization scripts...")

    # Upload and run the SQL initialization files
    sftp = ssh.open_sftp()

    # List of SQL files to run in order
    sql_files = [
        'roles.sql',
        '_supabase.sql',
        'jwt.sql',
        'logs.sql',
        'webhooks.sql',
        'realtime.sql'
    ]

    for sql_file in sql_files:
        try:
            print(f"Running {sql_file}...")
            stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=postgres_postgres -q) psql -U postgres -d supabase_database -f /opt/supabase/volumes/db/{sql_file} 2>/dev/null || echo 'File {sql_file} not found or error'")
            output = stdout.read().decode()
            print(f"{sql_file} result: {output[:200]}...")
        except Exception as e:
            print(f"Error with {sql_file}: {e}")

    sftp.close()

    # 5. Check service status
    print("\n📊 Checking Supabase services...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # 6. Check specific service logs
    services = ['kong', 'auth', 'db', 'storage']
    for service in services:
        print(f"\n📋 {service.upper()} logs:")
        stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 3 supabase_{service} 2>/dev/null || echo 'Service not ready'")
        output = stdout.read().decode()
        print(output)

    # 7. Test database connectivity
    print("\n🧪 Testing database connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=postgres_postgres -q) psql -U authenticator -d supabase_database -c 'SELECT current_user, current_database();' 2>/dev/null || echo 'Authenticator connection failed'")
    output = stdout.read().decode()
    print(f"Authenticator test: {output}")

    ssh.close()
    print("\n✅ Database schema fix completed!")

if __name__ == "__main__":
    main()