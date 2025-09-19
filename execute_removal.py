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
    print("🗑️ Removing Supabase Stack from Server")

    # Step 1: Remove Docker stack
    print("\n📋 Step 1: Removing Supabase Docker stack...")
    result = ssh_exec_simple("docker stack rm supabase")
    print(result)

    # Wait for services to be removed
    print("\n⏱️ Waiting for services to be removed...")
    result = ssh_exec_simple("sleep 30")

    # Step 2: Remove Docker configs
    print("\n📋 Step 2: Removing Docker configs...")
    configs = [
        "supabase_kong_config",
        "supabase_vector_config",
        "supabase_pooler_config"
    ]

    for config in configs:
        print(f"Removing config: {config}")
        result = ssh_exec_simple(f"docker config rm {config} 2>/dev/null || echo 'Config {config} not found'")
        print(result)

    # Step 3: Remove Docker volumes
    print("\n📋 Step 3: Removing Docker volumes...")
    volumes = [
        "supabase_storage",
        "supabase_functions",
        "supabase_vector_config"
    ]

    for volume in volumes:
        print(f"Removing volume: {volume}")
        result = ssh_exec_simple(f"docker volume rm {volume} 2>/dev/null || echo 'Volume {volume} not found'")
        print(result)

    # Step 4: Remove server files
    print("\n📋 Step 4: Removing server files...")
    result = ssh_exec_simple("rm -rf /opt/supabase")
    print("✅ /opt/supabase directory removed")

    # Step 5: Clean up database
    print("\n📋 Step 5: Cleaning up database...")

    cleanup_commands = [
        "DROP SCHEMA IF EXISTS _realtime CASCADE;",
        "DROP SCHEMA IF EXISTS storage CASCADE;",
        "DROP SCHEMA IF EXISTS auth CASCADE;",
        "DROP SCHEMA IF EXISTS _analytics CASCADE;",
        "DROP SCHEMA IF EXISTS graphql_public CASCADE;",
        "DROP SCHEMA IF EXISTS extensions CASCADE;",
        "DROP USER IF EXISTS supabase_auth_admin;",
        "DROP USER IF EXISTS supabase_storage_admin;",
        "DROP USER IF EXISTS supabase_functions_admin;",
        "DROP USER IF EXISTS authenticator;",
        "DROP USER IF EXISTS pgbouncer;",
        "DROP USER IF EXISTS supabase_admin;"
    ]

    for cmd in cleanup_commands:
        print(f"Executing: {cmd[:50]}...")
        result = ssh_exec_simple(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{cmd}\" 2>/dev/null || echo 'Command skipped'")

    # Step 6: Verify removal
    print("\n📋 Step 6: Verifying removal...")

    print("Checking for remaining services:")
    result = ssh_exec_simple("docker service ls | grep supabase || echo 'No Supabase services found'")
    print(result)

    print("Checking for remaining configs:")
    result = ssh_exec_simple("docker config ls | grep supabase || echo 'No Supabase configs found'")
    print(result)

    print("Checking for remaining volumes:")
    result = ssh_exec_simple("docker volume ls | grep supabase || echo 'No Supabase volumes found'")
    print(result)

    print("\n🎉 Supabase stack removal completed!")
    print("\n📋 Summary:")
    print("✅ Docker stack removed")
    print("✅ Docker configs removed")
    print("✅ Docker volumes removed")
    print("✅ Server files removed")
    print("✅ Database users and schemas removed")

    print("\n📝 Note:")
    print("- Your PostgreSQL and other stacks remain untouched")
    print("- Traefik routes for Supabase domains will no longer work")
    print("- You can redeploy Supabase anytime using: python3 deploy_ssh.py")

    return True

if __name__ == "__main__":
    main()