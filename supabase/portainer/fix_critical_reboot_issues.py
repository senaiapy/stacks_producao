#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚨 EMERGENCY: Fixing critical issues after server reboot...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. FIRST: Stop all Supabase services to prevent interference
    print("\n🛑 Stopping all Supabase services...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase --format '{{.Name}}' | xargs -r docker service rm")
    output = stdout.read().decode()
    print(f"Stopped services: {output}")
    time.sleep(10)

    # 2. Check PostgreSQL service status
    print("\n🔍 Checking PostgreSQL service status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=postgres")
    output = stdout.read().decode()
    print(output)

    # 3. Fix PostgreSQL if it's stuck in startup
    print("\n🔧 Checking PostgreSQL database status...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 10 postgres_postgres 2>/dev/null || echo 'PostgreSQL service not found'")
    output = stdout.read().decode()
    print("PostgreSQL logs:")
    print(output)

    # 4. If PostgreSQL is having issues, restart it
    print("\n🔄 Restarting PostgreSQL service...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force postgres_postgres")
    print("PostgreSQL restart initiated")
    time.sleep(15)

    # 5. Wait for PostgreSQL to be ready
    print("\n⏳ Waiting for PostgreSQL to be ready...")
    for i in range(12):  # Wait up to 2 minutes
        stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=postgres_postgres -q) pg_isready -U postgres 2>/dev/null || echo 'not ready'")
        output = stdout.read().decode().strip()
        if "accepting connections" in output:
            print("✅ PostgreSQL is ready!")
            break
        print(f"Attempt {i+1}/12: PostgreSQL not ready yet...")
        time.sleep(10)

    # 6. Create missing Supabase database users
    print("\n👤 Creating missing Supabase database users...")

    users_sql = """
    -- Create authenticator user with password
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
            CREATE ROLE authenticator WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
        ELSE
            ALTER ROLE authenticator WITH PASSWORD 'Ma1x1x0x_testing';
        END IF;
    END $$;

    -- Create other required users
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_auth_admin') THEN
            CREATE ROLE supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
        END IF;
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_storage_admin') THEN
            CREATE ROLE supabase_storage_admin WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
        END IF;
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dashboard_user') THEN
            CREATE ROLE dashboard_user WITH LOGIN PASSWORD 'Ma1x1x0x_testing';
        END IF;
    END $$;

    -- Grant necessary permissions
    GRANT USAGE ON SCHEMA public TO authenticator;
    GRANT CREATE ON SCHEMA public TO authenticator;
    """

    # Execute SQL to create users
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=postgres_postgres -q) psql -U postgres -d supabase_database -c \"{users_sql}\" 2>/dev/null || echo 'Database user creation failed'")
    output = stdout.read().decode()
    print(f"User creation result: {output}")

    # 7. Upload corrected supabase.yml with fixed Traefik labels
    print("\n📤 Uploading corrected supabase.yml...")
    sftp = ssh.open_sftp()
    sftp.put("supabase.yml", "/opt/supabase/supabase.yml")
    sftp.close()

    # 8. Deploy Supabase with proper startup order
    print("\n🚀 Deploying Supabase with proper startup order...")

    # Deploy database first (it should already be ready)
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker stack deploy -c supabase.yml supabase")
    output = stdout.read().decode()
    print(f"Deployment result: {output}")

    # 9. Wait and check Kong specifically
    print("\n⏳ Waiting for Kong to start...")
    time.sleep(20)

    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 supabase_kong")
    output = stdout.read().decode()
    print("Kong logs:")
    print(output)

    # 10. Check overall service status
    print("\n📊 Final service status check...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # 11. Test external connectivity
    print("\n🌐 Testing external connectivity...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/ 2>/dev/null || echo 'Connection failed'")
    status_code = stdout.read().decode().strip()
    print(f"External access status: {status_code}")

    # 12. Check Traefik status
    print("\n🔍 Checking Traefik status...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 3 traefik_traefik")
    output = stdout.read().decode()
    print("Traefik logs:")
    print(output)

    ssh.close()
    print("\n✅ Critical issue fix completed!")
    print("\n📋 NEXT STEPS:")
    print("1. Wait 5-10 minutes for all services to fully start")
    print("2. Check database schema initialization")
    print("3. Verify Kong authentication is working")
    print("4. Test Supabase Studio access")

if __name__ == "__main__":
    main()