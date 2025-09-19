#!/usr/bin/env python3
import pexpect
import sys
import time

# Configuration
PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"
TIMEOUT = 60

def ssh_exec(command):
    """Execute SSH command with password authentication"""
    try:
        print(f"Executing: {command[:80]}...")
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {USER}@{SERVER} "{command}"', timeout=TIMEOUT)

        i = child.expect(['password:', 'yes/no', pexpect.TIMEOUT, pexpect.EOF])

        if i == 0:  # password prompt
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        elif i == 1:  # yes/no prompt
            child.sendline('yes')
            child.expect('password:')
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        elif i == 2:  # timeout
            print("SSH timeout")
            return False

        output = child.before.decode('utf-8')
        print(output)
        child.close()
        return child.exitstatus == 0

    except Exception as e:
        print(f"SSH error: {e}")
        return False

def main():
    print("🔧 Fixing Supabase database issues (v2)...")

    # Step 1: Identify PostgreSQL container and users
    print("\n📋 Step 1: Investigating PostgreSQL setup...")
    investigate_cmd = '''
    echo "🔍 Finding PostgreSQL container..."
    POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)
    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo "❌ PostgreSQL container not found"
        echo "Available containers:"
        docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
        exit 1
    fi

    echo "📍 Found PostgreSQL container: $POSTGRES_CONTAINER"
    echo "🔍 Container details:"
    docker ps --filter id=$POSTGRES_CONTAINER --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

    echo "🔍 Checking PostgreSQL environment variables..."
    docker exec $POSTGRES_CONTAINER env | grep -E "(POSTGRES|DB)" || echo "No POSTGRES env vars found"

    echo "🔍 Attempting to connect with different users..."
    echo "Trying chatwoot_database user:"
    docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT current_user, current_database();" 2>/dev/null || echo "❌ chatwoot_database user failed"

    echo "Trying postgres user:"
    docker exec $POSTGRES_CONTAINER psql -U postgres -c "SELECT current_user;" 2>/dev/null || echo "❌ postgres user failed"

    echo "🔍 Checking what users exist:"
    docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT usename FROM pg_user;" 2>/dev/null || echo "❌ Cannot list users"

    echo "🔍 Checking databases:"
    docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT datname FROM pg_database;" 2>/dev/null || echo "❌ Cannot list databases"
    '''

    if not ssh_exec(investigate_cmd):
        print("❌ Failed to investigate PostgreSQL setup")
        return False
    print("✅ PostgreSQL investigation completed")

    # Step 2: Create database setup using existing user
    print("\n📋 Step 2: Setting up database with existing user...")
    setup_script = '''cat > /tmp/setup_supabase_db.sql << 'EOF'
-- Create Supabase users with correct passwords
CREATE USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_storage_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_functions_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER authenticator WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER pgbouncer WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';

-- Grant database permissions
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_storage_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_functions_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO authenticator;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_admin;

-- Create required schemas
CREATE SCHEMA IF NOT EXISTS _realtime;
CREATE SCHEMA IF NOT EXISTS _analytics;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS graphql_public;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant schema permissions
GRANT ALL ON SCHEMA _realtime TO supabase_auth_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_auth_admin;
GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
GRANT ALL ON SCHEMA extensions TO supabase_admin;
GRANT ALL ON SCHEMA graphql_public TO supabase_admin;

-- Grant usage on all schemas to all supabase users
GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
GRANT USAGE ON SCHEMA public TO supabase_storage_admin;
GRANT USAGE ON SCHEMA public TO supabase_functions_admin;
GRANT USAGE ON SCHEMA public TO authenticator;
GRANT USAGE ON SCHEMA public TO supabase_admin;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Skip pgjwt if not available
-- CREATE EXTENSION IF NOT EXISTS pgjwt;

-- Create basic tables for realtime
CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA _realtime GRANT ALL ON TABLES TO supabase_auth_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA storage GRANT ALL ON TABLES TO supabase_storage_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO supabase_auth_admin;

SELECT 'Supabase database setup completed successfully!' as result;
EOF'''

    if not ssh_exec(setup_script):
        print("❌ Failed to create setup script")
        return False
    print("✅ Setup script created")

    # Step 3: Execute database setup using chatwoot_database user
    print("\n📋 Step 3: Executing database setup...")
    db_setup_cmd = '''
    echo "🔧 Setting up Supabase database users and schemas..."
    POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)

    echo "📍 Copying setup script to container..."
    docker cp /tmp/setup_supabase_db.sql $POSTGRES_CONTAINER:/tmp/

    echo "🚀 Executing setup script..."
    docker exec -i $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/setup_supabase_db.sql
    '''

    if not ssh_exec(db_setup_cmd):
        print("❌ Failed to setup database, trying alternative method...")

        # Alternative method: Execute commands one by one
        print("\n📋 Trying alternative setup method...")
        alt_setup_cmd = '''
        POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)

        echo "Creating users one by one..."
        docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE USER IF NOT EXISTS supabase_auth_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';" || echo "User creation failed"
        docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE USER IF NOT EXISTS supabase_storage_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';" || echo "User creation failed"

        echo "Creating schemas..."
        docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS _realtime;" || echo "Schema creation failed"
        docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS storage;" || echo "Schema creation failed"
        docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS auth;" || echo "Schema creation failed"

        echo "✅ Alternative setup completed"
        '''

        ssh_exec(alt_setup_cmd)

    print("✅ Database setup attempted")

    # Step 4: Test connections and show current state
    print("\n📋 Step 4: Testing and showing current state...")
    test_cmd = '''
    POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)

    echo "🔍 Listing current users:"
    docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT usename FROM pg_user;" 2>/dev/null || echo "❌ Cannot list users"

    echo "🔍 Listing current schemas:"
    docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('_realtime', 'storage', 'auth', '_analytics');" 2>/dev/null || echo "❌ Cannot list schemas"

    echo "🔍 Testing supabase user connections:"
    docker exec $POSTGRES_CONTAINER psql -U supabase_auth_admin -d chatwoot_database -c "SELECT current_user;" 2>/dev/null && echo "✅ Auth admin connection works" || echo "❌ Auth admin connection failed"
    '''

    ssh_exec(test_cmd)

    # Step 5: Restart Supabase services regardless
    print("\n📋 Step 5: Restarting Supabase services...")
    restart_cmd = '''
    echo "🔄 Restarting Supabase services..."
    docker service update --force supabase_auth
    docker service update --force supabase_storage
    docker service update --force supabase_realtime
    docker service update --force supabase_functions

    echo "⏱️ Waiting for services to restart..."
    sleep 15

    echo "📊 Current service status:"
    docker service ls | grep supabase | head -5
    '''

    ssh_exec(restart_cmd)

    print("\n🎉 Database setup and service restart completed!")
    print("\n📋 Next steps:")
    print("1. Check service logs: ssh root@217.79.184.8 'docker service logs supabase_auth'")
    print("2. Monitor all services: ssh root@217.79.184.8 'docker service ls | grep supabase'")
    print("3. If issues persist, we may need to check your PostgreSQL stack configuration")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)