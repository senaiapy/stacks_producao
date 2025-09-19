#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔍 Deep diagnosis of Supabase deployment issues...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Check overall service status
    print("\n📊 Current service status:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase")
    output = stdout.read().decode()
    print(output)

    # 2. Check which services are actually failing
    print("\n🔍 Checking failed services in detail:")
    services = ["supabase_auth", "supabase_rest", "supabase_realtime", "supabase_analytics", "supabase_functions", "supabase_studio"]

    for service in services:
        print(f"\n--- {service} ---")
        stdin, stdout, stderr = ssh.exec_command(f"docker service ps {service} --no-trunc")
        output = stdout.read().decode()
        print(output)

        print(f"Recent logs for {service}:")
        stdin, stdout, stderr = ssh.exec_command(f"docker service logs --tail 5 {service}")
        output = stdout.read().decode()
        if output.strip():
            print(output)
        else:
            print("No logs available")

    # 3. Check Kong specifically
    print("\n🔍 Kong API Gateway detailed check:")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 10 supabase_kong")
    output = stdout.read().decode()
    print(output)

    # 4. Test internal connectivity
    print("\n🌐 Testing internal connectivity:")
    stdin, stdout, stderr = ssh.exec_command("curl -I http://localhost:8888/ 2>/dev/null || echo 'Kong not responding'")
    output = stdout.read().decode()
    print(f"Kong local test: {output}")

    # 5. Check database status
    print("\n🗄️ Database status check:")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_db -q) pg_isready -U postgres 2>/dev/null || echo 'Database not accessible'")
    output = stdout.read().decode()
    print(f"Database status: {output}")

    # 6. Check database users
    print("\n👤 Database users check:")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c \"\\du\" 2>/dev/null || echo 'Cannot check users'")
    output = stdout.read().decode()
    print(output)

    # 7. Check networks
    print("\n🌐 Network status:")
    stdin, stdout, stderr = ssh.exec_command("docker network ls | grep -E '(app_network|traefik_public)'")
    output = stdout.read().decode()
    print(output)

    # 8. Check node labels
    print("\n🏷️ Node labels:")
    stdin, stdout, stderr = ssh.exec_command("docker node inspect $(docker node ls -q) --format '{{.Spec.Labels}}'")
    output = stdout.read().decode()
    print(output)

    # 9. Test external access
    print("\n🌍 External access test:")
    stdin, stdout, stderr = ssh.exec_command("curl -I https://supabase.senaia.in 2>/dev/null || echo 'External access failed'")
    output = stdout.read().decode()
    print(f"External access: {output}")

    ssh.close()
    print("\n✅ Diagnosis completed!")

if __name__ == "__main__":
    main()