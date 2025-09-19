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

print("🔧 Quick config redeployment...")

# Step 1: Recreate directory structure
print("1. Creating directory structure...")
result = ssh_exec("mkdir -p /opt/supabase/config && echo 'Directory created'")
print(result)

# Step 2: Transfer config files
print("2. Transferring config files...")

configs = [
    ("supabase/docker/volumes/api/kong.yml", "/opt/supabase/config/"),
    ("supabase/docker/volumes/logs/vector.yml", "/opt/supabase/config/"),
    ("supabase/docker/volumes/pooler/pooler.exs", "/opt/supabase/config/")
]

for local_file, remote_path in configs:
    print(f"Transferring: {local_file}")
    if scp_exec(local_file, remote_path):
        print(f"✅ {local_file} transferred")
    else:
        print(f"❌ Failed to transfer {local_file}")

# Step 3: Verify files
print("\n3. Verifying config files...")
result = ssh_exec("ls -la /opt/supabase/config/")
print(result)

# Step 4: Create Docker configs
print("\n4. Creating Docker configs...")

docker_configs = [
    ("supabase_kong_config", "/opt/supabase/config/kong.yml"),
    ("supabase_vector_config", "/opt/supabase/config/vector.yml"),
    ("supabase_pooler_config", "/opt/supabase/config/pooler.exs")
]

for config_name, config_path in docker_configs:
    print(f"Creating config: {config_name}")

    # Remove existing config if any
    ssh_exec(f"docker config rm {config_name} 2>/dev/null || true")

    # Create new config
    result = ssh_exec(f"docker config create {config_name} {config_path}")
    print(f"✅ {config_name} created")

# Step 5: Verify Docker configs
print("\n5. Verifying Docker configs...")
result = ssh_exec("docker config ls | grep supabase")
print(result)

print("\n✅ Config redeployment completed!")
print("You can now deploy the stack with:")
print("ssh root@217.79.184.8 'cd /opt/supabase && docker stack deploy -c supabase.yml supabase'")