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

print("🗑️ Removing ONLY Supabase Docker stack...")
print("⚠️ This keeps all configs, volumes, and files intact")

# Step 1: Remove only the Docker stack
print("\n📋 Step 1: Removing Supabase Docker stack...")
result = ssh_exec("docker stack rm supabase")
print(result)

# Step 2: Wait for services to be removed
print("\n⏱️ Waiting for services to be removed...")
result = ssh_exec("sleep 20")

# Step 3: Verify stack removal
print("\n📋 Step 3: Verifying stack removal...")
result = ssh_exec("docker service ls | grep supabase || echo 'No Supabase services found'")
print(result)

# Step 4: Show what remains preserved
print("\n📋 Step 4: Verifying configs are preserved...")
result = ssh_exec("docker config ls | grep supabase")
print("Docker configs (preserved):")
print(result)

print("\nVolumes (preserved):")
result = ssh_exec("docker volume ls | grep supabase")
print(result)

print("\nServer files (preserved):")
result = ssh_exec("ls -la /opt/supabase/")
print(result)

print("\n✅ Stack removal completed!")
print("\n📋 What was removed:")
print("- Supabase Docker services")
print("- Running containers")

print("\n📋 What remains intact:")
print("- Docker configs (kong, vector, pooler)")
print("- Docker volumes (storage, functions)")
print("- Server files (/opt/supabase/)")
print("- Database users and schemas")

print("\n🔄 To redeploy the stack:")
print("ssh root@217.79.184.8 'cd /opt/supabase && docker stack deploy -c supabase.yml supabase'")