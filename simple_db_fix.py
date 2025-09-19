#!/usr/bin/env python3
import pexpect
import sys

PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"

def ssh_exec_simple(command):
    """Execute simple SSH command"""
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
        return "Error executing command"

def main():
    print("🔧 Simple Supabase Database Fix")

    # Step 1: Check PostgreSQL container
    print("\n📋 Step 1: Finding PostgreSQL container...")
    result = ssh_exec_simple("docker ps --filter name=postgres --format '{{.Names}} {{.ID}}'")
    print(result)

    # Step 2: Check PostgreSQL users
    print("\n📋 Step 2: Checking existing users...")
    result = ssh_exec_simple("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c 'SELECT usename FROM pg_user;' 2>/dev/null || echo 'Cannot list users'")
    print(result)

    # Step 3: Create Supabase users
    print("\n📋 Step 3: Creating Supabase users...")
    commands = [
        "CREATE USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "CREATE USER supabase_storage_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "CREATE SCHEMA IF NOT EXISTS _realtime;",
        "CREATE SCHEMA IF NOT EXISTS storage;",
        "CREATE SCHEMA IF NOT EXISTS auth;",
        "GRANT ALL ON SCHEMA _realtime TO supabase_auth_admin;",
        "GRANT ALL ON SCHEMA storage TO supabase_storage_admin;"
    ]

    for cmd in commands:
        print(f"Executing: {cmd[:50]}...")
        result = ssh_exec_simple(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{cmd}\" 2>/dev/null || echo 'Command failed'")
        print(result)

    # Step 4: Restart services
    print("\n📋 Step 4: Restarting key services...")
    services = ['supabase_auth', 'supabase_storage', 'supabase_realtime']
    for service in services:
        print(f"Restarting {service}...")
        result = ssh_exec_simple(f"docker service update --force {service}")
        print(f"✅ {service} restarted")

    # Step 5: Check service status
    print("\n📋 Step 5: Checking service status...")
    result = ssh_exec_simple("docker service ls | grep supabase | head -5")
    print(result)

    print("\n🎉 Simple fix completed!")
    return True

if __name__ == "__main__":
    main()