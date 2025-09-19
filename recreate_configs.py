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

print("🔧 Recreating Supabase Docker configs...")

# Check if config files exist
print("1. Checking for config files...")
result = ssh_exec("ls -la /opt/supabase/config/ 2>/dev/null || echo 'Config directory not found'")
print(result)

# If config directory doesn't exist, we need to redeploy files first
if "not found" in result:
    print("❌ Config files missing. Need to redeploy configuration files first.")
    print("Run: python3 deploy_ssh.py")
    exit(1)

# Create Docker configs
print("2. Creating Docker configs...")

configs = [
    ("supabase_kong_config", "/opt/supabase/config/kong.yml"),
    ("supabase_vector_config", "/opt/supabase/config/vector.yml"),
    ("supabase_pooler_config", "/opt/supabase/config/pooler.exs")
]

for config_name, config_path in configs:
    print(f"Creating config: {config_name}")

    # Remove existing config if any
    ssh_exec(f"docker config rm {config_name} 2>/dev/null || true")

    # Create new config
    result = ssh_exec(f"docker config create {config_name} {config_path}")
    if "Error" not in result:
        print(f"✅ {config_name} created")
    else:
        print(f"❌ Failed to create {config_name}")

# Verify configs
print("\n3. Verifying configs...")
result = ssh_exec("docker config ls | grep supabase")
print(result)

print("\n✅ Docker configs recreation completed!")
print("Now you can deploy the stack with: docker stack deploy -c supabase.yml supabase")