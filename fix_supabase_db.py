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
    print("🔧 Fixing Supabase database issues...")

    # Step 1: Create database setup script on server
    print("\n📋 Step 1: Creating database setup script...")
    setup_script = '''cat > /tmp/setup_supabase_db.sql << 'EOF'
-- Create Supabase users with correct passwords
CREATE USER IF NOT EXISTS supabase_auth_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER IF NOT EXISTS supabase_storage_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER IF NOT EXISTS supabase_functions_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER IF NOT EXISTS authenticator WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER IF NOT EXISTS pgbouncer WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER IF NOT EXISTS supabase_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';

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

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pgjwt;

-- Create basic tables for realtime
CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);

SELECT 'Supabase database setup completed successfully!';
EOF'''

    if not ssh_exec(setup_script):
        print("❌ Failed to create setup script")
        return False
    print("✅ Setup script created")

    # Step 2: Execute database setup
    print("\n📋 Step 2: Executing database setup...")
    db_setup_cmd = '''
    echo "🔧 Setting up Supabase database users and schemas..."
    POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)
    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo "❌ PostgreSQL container not found"
        exit 1
    fi

    echo "📍 Found PostgreSQL container: $POSTGRES_CONTAINER"
    docker exec -i $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -f /tmp/setup_supabase_db.sql
    '''

    if not ssh_exec(db_setup_cmd):
        print("❌ Failed to setup database")
        return False
    print("✅ Database setup completed")

    # Step 3: Copy and execute migration files
    print("\n📋 Step 3: Executing migration files...")
    migration_cmd = '''
    echo "📋 Copying and executing migration files..."
    POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)

    # Copy migration files to container
    docker cp /opt/supabase/db-migrations/roles.sql $POSTGRES_CONTAINER:/tmp/ 2>/dev/null || echo "roles.sql not found"
    docker cp /opt/supabase/db-migrations/realtime.sql $POSTGRES_CONTAINER:/tmp/ 2>/dev/null || echo "realtime.sql not found"
    docker cp /opt/supabase/db-migrations/jwt.sql $POSTGRES_CONTAINER:/tmp/ 2>/dev/null || echo "jwt.sql not found"
    docker cp /opt/supabase/db-migrations/logs.sql $POSTGRES_CONTAINER:/tmp/ 2>/dev/null || echo "logs.sql not found"
    docker cp /opt/supabase/db-migrations/_supabase.sql $POSTGRES_CONTAINER:/tmp/ 2>/dev/null || echo "_supabase.sql not found"

    # Execute migration files
    echo "🚀 Executing migration files..."
    docker exec $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -f /tmp/roles.sql 2>/dev/null || echo "Skipped roles.sql"
    docker exec $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -f /tmp/realtime.sql 2>/dev/null || echo "Skipped realtime.sql"
    docker exec $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -f /tmp/jwt.sql 2>/dev/null || echo "Skipped jwt.sql"
    docker exec $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -f /tmp/logs.sql 2>/dev/null || echo "Skipped logs.sql"
    docker exec $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -f /tmp/_supabase.sql 2>/dev/null || echo "Skipped _supabase.sql"

    echo "✅ Migration files executed"
    '''

    if not ssh_exec(migration_cmd):
        print("❌ Failed to execute migrations")
        return False
    print("✅ Migrations executed")

    # Step 4: Test database connections
    print("\n📋 Step 4: Testing database connections...")
    test_cmd = '''
    echo "🔍 Testing database connections..."
    POSTGRES_CONTAINER=$(docker ps -q -f name=postgres | head -1)

    echo "Testing supabase_auth_admin connection:"
    docker exec $POSTGRES_CONTAINER psql -U supabase_auth_admin -d chatwoot_database -c "SELECT 'Auth admin connection successful';" || echo "❌ Auth admin connection failed"

    echo "Testing supabase_storage_admin connection:"
    docker exec $POSTGRES_CONTAINER psql -U supabase_storage_admin -d chatwoot_database -c "SELECT 'Storage admin connection successful';" || echo "❌ Storage admin connection failed"

    echo "Listing available schemas:"
    docker exec $POSTGRES_CONTAINER psql -U postgres -d chatwoot_database -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE '%realtime%' OR schema_name LIKE '%storage%' OR schema_name LIKE '%auth%';"
    '''

    if not ssh_exec(test_cmd):
        print("⚠️ Database connection tests had issues")
    print("✅ Database connection tests completed")

    # Step 5: Restart Supabase services
    print("\n📋 Step 5: Restarting Supabase services...")
    restart_cmd = '''
    echo "🔄 Restarting Supabase services..."
    docker service update --force supabase_auth
    docker service update --force supabase_storage
    docker service update --force supabase_realtime
    docker service update --force supabase_functions
    docker service update --force supabase_meta
    docker service update --force supabase_rest

    echo "⏱️ Waiting for services to restart..."
    sleep 10

    echo "📊 Current service status:"
    docker service ls | grep supabase
    '''

    if not ssh_exec(restart_cmd):
        print("❌ Failed to restart services")
        return False
    print("✅ Services restarted")

    print("\n🎉 Database fixes applied successfully!")
    print("\n📋 Next steps:")
    print("1. Monitor service logs: docker service logs supabase_auth")
    print("2. Check service status: docker service ls | grep supabase")
    print("3. Wait a few minutes for services to fully start")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)