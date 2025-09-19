#!/usr/bin/env python3
import pexpect
import sys
import time

# Configuration
PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"
TIMEOUT = 30

def ssh_exec(command):
    """Execute SSH command with password authentication"""
    try:
        print(f"Executing: {command[:50]}...")
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

        print(child.before.decode('utf-8'))
        child.close()
        return child.exitstatus == 0

    except Exception as e:
        print(f"SSH error: {e}")
        return False

def scp_exec(local_file, remote_path):
    """Execute SCP command with password authentication"""
    try:
        print(f"Transferring: {local_file} -> {remote_path}")
        child = pexpect.spawn(f'scp -o StrictHostKeyChecking=no {local_file} {USER}@{SERVER}:{remote_path}', timeout=TIMEOUT)

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
            print("SCP timeout")
            return False

        child.close()
        return child.exitstatus == 0

    except Exception as e:
        print(f"SCP error: {e}")
        return False

def main():
    print("🚀 Starting Supabase deployment to 217.79.184.8...")

    # Step 1: Test connection
    print("\n📋 Step 1: Testing SSH connection...")
    if not ssh_exec("echo 'SSH connection successful'"):
        print("❌ SSH connection failed")
        return False
    print("✅ SSH connection successful")

    # Step 2: Create directory structure
    print("\n📋 Step 2: Creating directory structure...")
    cmd = """
    sudo mkdir -p /opt/supabase/{config,db-migrations,reference,scripts} && \
    sudo mkdir -p /opt/supabase/db-migrations/init && \
    sudo chown -R $(whoami):$(whoami) /opt/supabase && \
    sudo chmod -R 755 /opt/supabase && \
    echo 'Directories created successfully'
    """
    if not ssh_exec(cmd):
        print("❌ Failed to create directories")
        return False
    print("✅ Directories created")

    # Step 3: Transfer Kong configuration
    print("\n📋 Step 3: Transferring Kong configuration...")
    if not scp_exec("supabase/docker/volumes/api/kong.yml", "/opt/supabase/config/"):
        print("❌ Failed to transfer Kong config")
        return False
    print("✅ Kong config transferred")

    # Step 4: Transfer Vector configuration
    print("\n📋 Step 4: Transferring Vector configuration...")
    if not scp_exec("supabase/docker/volumes/logs/vector.yml", "/opt/supabase/config/"):
        print("❌ Failed to transfer Vector config")
        return False
    print("✅ Vector config transferred")

    # Step 5: Transfer Pooler configuration
    print("\n📋 Step 5: Transferring Pooler configuration...")
    if not scp_exec("supabase/docker/volumes/pooler/pooler.exs", "/opt/supabase/config/"):
        print("❌ Failed to transfer Pooler config")
        return False
    print("✅ Pooler config transferred")

    # Step 6: Transfer supabase.yml
    print("\n📋 Step 6: Transferring supabase.yml...")
    if not scp_exec("supabase.yml", "/opt/supabase/"):
        print("❌ Failed to transfer supabase.yml")
        return False
    print("✅ supabase.yml transferred")

    # Step 7: Transfer database migration files
    print("\n📋 Step 7: Transferring database migration files...")
    migration_files = [
        "supabase/docker/volumes/db/roles.sql",
        "supabase/docker/volumes/db/realtime.sql",
        "supabase/docker/volumes/db/jwt.sql",
        "supabase/docker/volumes/db/logs.sql",
        "supabase/docker/volumes/db/pooler.sql",
        "supabase/docker/volumes/db/_supabase.sql"
    ]

    for file in migration_files:
        try:
            scp_exec(file, "/opt/supabase/db-migrations/")
        except:
            print(f"⚠️ Optional file {file} not found, skipping...")
    print("✅ Migration files transferred")

    # Step 8: Verify files
    print("\n📋 Step 8: Verifying file transfer...")
    ssh_exec("ls -la /opt/supabase/config/ && echo '--- Migration files ---' && ls -la /opt/supabase/db-migrations/")

    # Step 9: Initialize Docker Swarm
    print("\n📋 Step 9: Initializing Docker Swarm...")
    swarm_cmd = """
    docker swarm init 2>/dev/null || echo 'Swarm already initialized' && \
    docker network create --driver=overlay app_network 2>/dev/null || echo 'app_network exists' && \
    docker network create --driver=overlay traefik_public 2>/dev/null || echo 'traefik_public exists'
    """
    ssh_exec(swarm_cmd)
    print("✅ Docker Swarm initialized")

    # Step 10: Create Docker configs
    print("\n📋 Step 10: Creating Docker configs...")
    config_cmd = """
    cd /opt/supabase && \
    docker config rm supabase_kong_config 2>/dev/null || true && \
    docker config rm supabase_vector_config 2>/dev/null || true && \
    docker config rm supabase_pooler_config 2>/dev/null || true && \
    docker config create supabase_kong_config config/kong.yml && \
    docker config create supabase_vector_config config/vector.yml && \
    docker config create supabase_pooler_config config/pooler.exs && \
    echo 'Docker configs created:' && \
    docker config ls | grep supabase
    """
    if not ssh_exec(config_cmd):
        print("❌ Failed to create Docker configs")
        return False
    print("✅ Docker configs created")

    # Step 11: Deploy Supabase stack
    print("\n📋 Step 11: Deploying Supabase stack...")
    deploy_cmd = """
    cd /opt/supabase && \
    docker stack deploy -c supabase.yml supabase && \
    echo 'Supabase stack deployed successfully!'
    """
    if not ssh_exec(deploy_cmd):
        print("❌ Failed to deploy Supabase stack")
        return False
    print("✅ Supabase stack deployed")

    # Step 12: Verify deployment
    print("\n📋 Step 12: Verifying deployment...")
    ssh_exec("docker service ls | grep supabase")

    print("\n🎉 Deployment completed successfully!")
    print("\n🌐 Services will be available at:")
    print("   - Supabase API: https://supabase.senaia.in")
    print("   - Supabase Studio: https://studio.senaia.in")
    print("   - Connection Pooler: https://pooler.senaia.in")

    print("\n📈 Monitor deployment with:")
    print("   docker service ls | grep supabase")
    print("   docker service logs -f supabase_vector")
    print("   docker service logs -f supabase_analytics")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)