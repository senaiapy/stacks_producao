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

print("🔍 Verifying Supabase removal...")

print("\n1. Checking for services:")
result = ssh_exec("docker service ls | grep supabase || echo 'No Supabase services found'")
print(result)

print("\n2. Checking for configs:")
result = ssh_exec("docker config ls | grep supabase || echo 'No Supabase configs found'")
print(result)

print("\n3. Checking for volumes:")
result = ssh_exec("docker volume ls | grep supabase || echo 'No Supabase volumes found'")
print(result)

print("\n4. Checking server files:")
result = ssh_exec("ls -la /opt/supabase 2>/dev/null || echo 'Directory /opt/supabase not found'")
print(result)

print("\n✅ Verification completed!")