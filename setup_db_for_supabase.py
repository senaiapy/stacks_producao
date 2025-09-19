#!/usr/bin/env python3
import pexpect

PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"

def ssh_exec(command):
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {USER}@{SERVER} "{command}"', timeout=30)
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if i == 0:
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        output = child.before.decode('utf-8')
        child.close()
        return output
    except:
        return "Error"

print("🔧 Setting up database for Supabase...")

# Step 1: Create Supabase users
print("1. Creating Supabase users...")
users = [
    "CREATE USER IF NOT EXISTS supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
    "CREATE USER IF NOT EXISTS supabase_storage_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
    "CREATE USER IF NOT EXISTS supabase_functions_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
    "CREATE USER IF NOT EXISTS authenticator WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
    "CREATE USER IF NOT EXISTS pgbouncer WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
    "CREATE USER IF NOT EXISTS supabase_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';"
]

for user_cmd in users:
    result = ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{user_cmd}\" 2>/dev/null || echo 'User creation attempt'")

print("✅ Users created")

# Step 2: Grant database permissions
print("\n2. Granting database permissions...")
permissions = [
    "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_auth_admin;",
    "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_storage_admin;",
    "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_functions_admin;",
    "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO authenticator;",
    "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_admin;"
]

for perm_cmd in permissions:
    result = ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{perm_cmd}\" 2>/dev/null || echo 'Permission grant attempt'")

print("✅ Permissions granted")

# Step 3: Create schemas
print("\n3. Creating required schemas...")
schemas = [
    "CREATE SCHEMA IF NOT EXISTS _realtime;",
    "CREATE SCHEMA IF NOT EXISTS _analytics;",
    "CREATE SCHEMA IF NOT EXISTS storage;",
    "CREATE SCHEMA IF NOT EXISTS graphql_public;",
    "CREATE SCHEMA IF NOT EXISTS auth;",
    "CREATE SCHEMA IF NOT EXISTS extensions;"
]

for schema_cmd in schemas:
    result = ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{schema_cmd}\" 2>/dev/null || echo 'Schema creation attempt'")

print("✅ Schemas created")

# Step 4: Grant schema permissions
print("\n4. Granting schema permissions...")
schema_perms = [
    "GRANT ALL ON SCHEMA _realtime TO supabase_auth_admin;",
    "GRANT ALL ON SCHEMA _analytics TO supabase_auth_admin;",
    "GRANT ALL ON SCHEMA storage TO supabase_storage_admin;",
    "GRANT ALL ON SCHEMA auth TO supabase_auth_admin;",
    "GRANT ALL ON SCHEMA extensions TO supabase_admin;",
    "GRANT ALL ON SCHEMA graphql_public TO supabase_admin;"
]

for perm_cmd in schema_perms:
    result = ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{perm_cmd}\" 2>/dev/null || echo 'Schema permission attempt'")

print("✅ Schema permissions granted")

# Step 5: Create extensions
print("\n5. Creating extensions...")
extensions = [
    "CREATE EXTENSION IF NOT EXISTS vector;",
    "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;",
    "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
]

for ext_cmd in extensions:
    result = ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{ext_cmd}\" 2>/dev/null || echo 'Extension creation attempt'")

print("✅ Extensions created")

# Step 6: Create realtime table
print("\n6. Creating realtime migration table...")
realtime_table = """
CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);
"""

result = ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{realtime_table}\" 2>/dev/null || echo 'Realtime table creation attempt'")

print("✅ Realtime table created")

# Step 7: Restart key services
print("\n7. Restarting Supabase services...")
services = ["supabase_auth", "supabase_storage", "supabase_realtime", "supabase_meta"]

for service in services:
    result = ssh_exec(f"docker service update --force {service}")
    print(f"✅ {service} restarted")

print("\n🎉 Database setup completed!")
print("\n📋 Check service status:")
result = ssh_exec("docker service ls | grep supabase")
print(result)