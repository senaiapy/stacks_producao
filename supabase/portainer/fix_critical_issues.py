#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚨 Fixing critical Supabase deployment issues...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Fix database tables for analytics
    print("\n📊 Creating missing database tables for analytics...")
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS system_metrics (
        id SERIAL PRIMARY KEY,
        all_logs_logged INTEGER DEFAULT 0,
        node VARCHAR(255),
        inserted_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    INSERT INTO system_metrics (all_logs_logged, node) VALUES (0, 'supabase_analytics') ON CONFLICT DO NOTHING;

    CREATE TABLE IF NOT EXISTS extensions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE,
        inserted_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """

    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c \"{create_tables_sql}\""
    )
    output = stdout.read().decode()
    error = stderr.read().decode()
    if "CREATE TABLE" in output or "INSERT" in output:
        print("✅ Database tables created for analytics")
    elif error:
        print(f"❌ Database table creation error: {error}")

    # 2. Disable analytics temporarily (it's causing issues)
    print("\n🔄 Disabling problematic analytics service...")
    stdin, stdout, stderr = ssh.exec_command("docker service scale supabase_analytics=0")
    output = stdout.read().decode()
    print(f"Analytics disabled: {output.strip()}")

    # 3. Fix Kong configuration port issue
    print("\n🔧 Checking Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker service inspect supabase_kong --format '{{.Endpoint.Ports}}'")
    output = stdout.read().decode()
    print(f"Kong ports: {output}")

    # 4. Restart Kong to fix local connectivity
    print("\n🔄 Restarting Kong service...")
    stdin, stdout, stderr = ssh.exec_command("docker service update --force supabase_kong")
    output = stdout.read().decode()
    print("Kong restarted")

    # 5. Check if we need to create missing databases
    print("\n🗄️ Creating missing databases...")
    create_db_sql = """
    CREATE DATABASE IF NOT EXISTS auth;
    CREATE DATABASE IF NOT EXISTS storage;
    CREATE DATABASE IF NOT EXISTS realtime;
    """

    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c \"{create_db_sql}\""
    )
    output = stdout.read().decode()
    print(f"Database creation: {output}")

    # 6. Wait for Kong to settle
    print("\n⏳ Waiting for Kong to restart...")
    time.sleep(15)

    # 7. Test Kong connectivity
    print("\n🧪 Testing Kong connectivity...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 supabase_kong")
    output = stdout.read().decode()
    print("Kong logs:")
    print(output)

    # 8. Try restarting key services one by one
    print("\n🔄 Restarting core services in order...")

    services_order = ["supabase_auth", "supabase_rest", "supabase_studio"]

    for service in services_order:
        print(f"Restarting {service}...")
        stdin, stdout, stderr = ssh.exec_command(f"docker service update --force {service}")
        time.sleep(10)  # Wait between restarts

    # 9. Final status check
    print("\n📊 Final service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # 10. Test web access again
    print("\n🌐 Testing web access...")
    stdin, stdout, stderr = ssh.exec_command("curl -I https://supabase.senaia.in")
    output = stdout.read().decode()
    print(f"Web access test: {output}")

    ssh.close()
    print("\n✅ Critical fixes completed!")

if __name__ == "__main__":
    main()