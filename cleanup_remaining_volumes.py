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

print("🧹 Cleaning up remaining Supabase volumes...")

volumes_to_remove = [
    "supabase-migration_supabase_db_data",
    "supabase_supabase_db_config",
    "supabase_supabase_db_data",
    "supabase_supabase_functions",
    "supabase_supabase_kong_config",
    "supabase_supabase_kong_data",
    "supabase_supabase_pooler_config",
    "supabase_supabase_storage",
    "supabase_supabase_storage_data",
    "supabase_supabase_vector_config",
    "supabse_supabase_kong_config"
]

for volume in volumes_to_remove:
    print(f"Removing volume: {volume}")
    result = ssh_exec(f"docker volume rm {volume} 2>/dev/null || echo 'Volume {volume} not found or in use'")

print("\n🔍 Final verification:")
result = ssh_exec("docker volume ls | grep supabase || echo 'No Supabase volumes found'")
print(result)

print("\n✅ Volume cleanup completed!")