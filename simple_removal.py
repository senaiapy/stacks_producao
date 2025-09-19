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

print("🗑️ Removing Supabase Stack...")

# Remove stack
print("1. Removing Docker stack...")
result = ssh_exec("docker stack rm supabase")
print("✅ Stack removal initiated")

# Remove configs
print("2. Removing configs...")
ssh_exec("docker config rm supabase_kong_config 2>/dev/null || true")
ssh_exec("docker config rm supabase_vector_config 2>/dev/null || true")
ssh_exec("docker config rm supabase_pooler_config 2>/dev/null || true")
print("✅ Configs removed")

# Remove volumes
print("3. Removing volumes...")
ssh_exec("docker volume rm supabase_storage 2>/dev/null || true")
ssh_exec("docker volume rm supabase_functions 2>/dev/null || true")
ssh_exec("docker volume rm supabase_vector_config 2>/dev/null || true")
print("✅ Volumes removed")

# Remove files
print("4. Removing files...")
ssh_exec("rm -rf /opt/supabase")
print("✅ Files removed")

print("\n🎉 Supabase stack removed successfully!")
print("Your PostgreSQL and other services remain untouched.")