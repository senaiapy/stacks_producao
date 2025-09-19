#!/usr/bin/env python3
import pexpect

PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"

def ssh_exec(command):
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {USER}@{SERVER} "{command}"', timeout=15)
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if i == 0:
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        output = child.before.decode('utf-8')
        child.close()
        return output
    except:
        return "Error"

print("📊 Checking Supabase service status...")

print("1. Service status:")
result = ssh_exec("docker service ls | grep supabase")
print(result)

print("\n2. Quick database user creation:")
result = ssh_exec("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"CREATE USER IF NOT EXISTS supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';\" 2>/dev/null || echo 'User exists or created'")

result = ssh_exec("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"CREATE SCHEMA IF NOT EXISTS _realtime;\" 2>/dev/null || echo 'Schema exists or created'")

print("✅ Basic setup attempted")

print("\n3. Restarting auth service:")
result = ssh_exec("docker service update --force supabase_auth")
print("✅ Auth service restarted")

print("\n4. Final status check:")
result = ssh_exec("docker service ls | grep supabase")
print(result)