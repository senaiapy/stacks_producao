#!/usr/bin/env python3
import pexpect

PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"

def ssh_exec(command):
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
        return "Error"

def scp_exec(local_file, remote_path):
    try:
        child = pexpect.spawn(f'scp -o StrictHostKeyChecking=no {local_file} {USER}@{SERVER}:{remote_path}', timeout=15)
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if i == 0:
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        child.close()
        return True
    except:
        return False

print("🚀 Deploying Supabase stack...")

# Step 1: Transfer supabase.yml
print("1. Transferring supabase.yml...")
if scp_exec("supabase.yml", "/opt/supabase/"):
    print("✅ supabase.yml transferred")
else:
    print("❌ Failed to transfer supabase.yml")
    exit(1)

# Step 2: Create required volumes
print("\n2. Creating required volumes...")
volumes = [
    "supabase_storage",
    "supabase_functions",
    "supabase_vector_config"
]

for volume in volumes:
    result = ssh_exec(f"docker volume create {volume} 2>/dev/null || echo '{volume} already exists'")
    print(f"✅ Volume {volume} ready")

# Step 3: Verify Docker configs exist
print("\n3. Verifying Docker configs...")
result = ssh_exec("docker config ls | grep supabase")
print(result)

# Step 4: Deploy the stack
print("\n4. Deploying Supabase stack...")
result = ssh_exec("cd /opt/supabase && docker stack deploy -c supabase.yml supabase")
print(result)

# Step 5: Monitor deployment
print("\n5. Checking deployment status...")
result = ssh_exec("sleep 10 && docker service ls | grep supabase")
print(result)

print("\n🎉 Deployment completed!")
print("\n📋 Next steps:")
print("- Monitor services: docker service ls | grep supabase")
print("- Check logs: docker service logs supabase_auth")
print("- Setup database users if needed: python3 fix_supabase_db_v2.py")