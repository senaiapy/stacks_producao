#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 Diagnosing remaining service issues...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Check logs for failing services
    failing_services = ['auth', 'realtime', 'rest', 'analytics', 'functions', 'studio']

    for service in failing_services:
        print(f"\n📋 === {service.upper()} SERVICE DIAGNOSIS ===")

        # Get service status
        stdin, stdout, stderr = ssh.exec_command(f"docker service ps supabase_{service} --no-trunc")
        status = stdout.read().decode()
        print(f"Service status:\n{status}")

        # Get recent logs
        stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 10 supabase_{service}")
        logs = stdout.read().decode()
        print(f"Recent logs:\n{logs}")

    # Check database connectivity for each user
    print(f"\n🗄️ === DATABASE CONNECTIVITY TESTS ===")

    users = ['authenticator', 'supabase_auth_admin', 'supabase_storage_admin', 'dashboard_user']

    for user in users:
        stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=postgres_postgres -q) psql -U {user} -d supabase_database -c 'SELECT current_user;' 2>&1")
        result = stdout.read().decode()
        print(f"{user}: {result.strip()}")

    # Check Kong status specifically
    print(f"\n🔒 === KONG DETAILED STATUS ===")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health 2>/dev/null || echo 'Kong health check failed'")
    kong_health = stdout.read().decode()
    print(f"Kong health: {kong_health}")

    # Test Traefik connectivity
    print(f"\n🌐 === TRAEFIK CONNECTIVITY ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/ 2>/dev/null")
    status_code = stdout.read().decode().strip()
    print(f"HTTPS status: {status_code}")

    # Test with Kong credentials
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' https://supabase.senaia.in/ 2>/dev/null")
    auth_status = stdout.read().decode().strip()
    print(f"Authenticated status: {auth_status}")

    # Check if database port is accessible internally
    print(f"\n🔗 === INTERNAL CONNECTIVITY ===")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) nc -zv db 25432 2>&1 || echo 'DB port test failed'")
    db_connectivity = stdout.read().decode()
    print(f"DB connectivity from Kong: {db_connectivity}")

    ssh.close()
    print("\n✅ Diagnosis completed!")

if __name__ == "__main__":
    main()