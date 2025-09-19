#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 FIXING Kong variables and credentials...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Upload the Kong configuration file to the server
    print("\n📤 Uploading Kong configuration...")
    sftp = ssh.open_sftp()
    sftp.put("volumes/api/kong.yml", "/opt/supabase/volumes/api/kong.yml")
    sftp.close()

    # 2. Replace variables in Kong config with actual values
    print("\n🔧 Replacing variables in Kong configuration...")

    # Create a script to replace variables
    replace_script = '''#!/bin/bash
cd /opt/supabase/volumes/api/

# Replace variables with actual values
sed -i 's/$SUPABASE_ANON_KEY/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao/g' kong.yml
sed -i 's/$SUPABASE_SERVICE_KEY/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI/g' kong.yml
sed -i 's/$DASHBOARD_USERNAME/supabase/g' kong.yml
sed -i 's/$DASHBOARD_PASSWORD/Ma1x1x0x_testing/g' kong.yml

echo "Kong config variables replaced"
'''

    # Write and execute the script
    stdin, stdout, stderr = ssh.exec_command(f"cat > /tmp/fix_kong.sh << 'EOF'\n{replace_script}\nEOF")
    stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/fix_kong.sh && /tmp/fix_kong.sh")
    output = stdout.read().decode()
    print(f"Variable replacement result: {output}")

    # 3. Copy the fixed Kong config to the container
    print("\n📋 Copying fixed Kong config to container...")
    stdin, stdout, stderr = ssh.exec_command("docker cp /opt/supabase/volumes/api/kong.yml $(docker ps -f name=supabase_kong -q):/home/kong/kong.yml")

    # 4. Check if the config was copied properly
    print("\n🔍 Verifying Kong config in container...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) head -40 /home/kong/kong.yml")
    kong_content = stdout.read().decode()
    print("Kong config in container:")
    print(kong_content)

    # 5. Reload Kong with the new configuration
    print("\n🔄 Reloading Kong...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_result = stdout.read().decode()
    print(f"Kong reload: {reload_result}")

    # 6. Test Kong health
    print("\n🧪 Testing Kong health...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health")
    health_result = stdout.read().decode()
    print(f"Kong health: {health_result}")

    # 7. Test external access with correct credentials
    print("\n🌐 Testing external access...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' 'https://supabase.senaia.in/' 2>/dev/null")
    status_code = stdout.read().decode().strip()
    print(f"External access status: {status_code}")

    # 8. Test Studio access
    print("\n🎨 Testing Studio access...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/project/default' 2>&1 | head -5")
    studio_test = stdout.read().decode()
    print(f"Studio test: {studio_test}")

    # 9. Test basic Studio access
    print("\n🎨 Testing basic Studio route...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/' 2>&1 | head -3")
    basic_test = stdout.read().decode()
    print(f"Basic test: {basic_test}")

    ssh.close()
    print("\n🎉 Kong variables fix completed!")
    print("\n✅ SUPABASE SHOULD NOW BE ACCESSIBLE!")
    print("\nAccess at: https://supabase.senaia.in")
    print("Username: supabase")
    print("Password: Ma1x1x0x_testing")

if __name__ == "__main__":
    main()