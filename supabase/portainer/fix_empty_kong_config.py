#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🚨 FIXING EMPTY Kong configuration...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Check the Kong environment variable for config template
    print("\n📋 Checking Kong environment variables...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) env | grep KONG")
    kong_env = stdout.read().decode()
    print(f"Kong environment: {kong_env}")

    # 2. Check if temp.yml exists
    print("\n🔍 Checking for temp.yml template...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) ls -la ~/temp.yml")
    temp_yml = stdout.read().decode()
    print(f"temp.yml status: {temp_yml}")

    # 3. Check the content of temp.yml
    print("\n📋 Checking temp.yml content...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cat ~/temp.yml | head -50")
    temp_content = stdout.read().decode()
    print("temp.yml content (first 50 lines):")
    print(temp_content)

    # 4. Check if kong.yml is being generated properly
    print("\n🔧 Checking how Kong generates kong.yml...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) eval 'echo \"$$(cat ~/temp.yml)\"' | head -20")
    generated_config = stdout.read().decode()
    print("Generated config (first 20 lines):")
    print(generated_config)

    # 5. Manually create the kong.yml from template
    print("\n🔧 Manually generating kong.yml from template...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) sh -c 'eval \"echo \\\"\\$(cat ~/temp.yml)\\\"\" > ~/kong.yml'")

    # 6. Verify the kong.yml was created
    print("\n📋 Verifying kong.yml was created...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) wc -l ~/kong.yml")
    line_count = stdout.read().decode()
    print(f"kong.yml line count: {line_count}")

    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) head -30 ~/kong.yml")
    kong_content = stdout.read().decode()
    print("kong.yml content (first 30 lines):")
    print(kong_content)

    # 7. Reload Kong with the new configuration
    print("\n🔄 Reloading Kong with new configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_result = stdout.read().decode()
    print(f"Kong reload result: {reload_result}")

    # 8. Test Kong health
    print("\n🧪 Testing Kong health...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health")
    health_result = stdout.read().decode()
    print(f"Kong health: {health_result}")

    # 9. Test external access
    print("\n🌐 Testing external access after config fix...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' 'https://supabase.senaia.in/' 2>/dev/null")
    status_code = stdout.read().decode().strip()
    print(f"External access status: {status_code}")

    # 10. Test Studio access specifically
    print("\n🎨 Testing Studio access...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/project/default' 2>&1 | head -3")
    studio_test = stdout.read().decode()
    print(f"Studio test result: {studio_test}")

    ssh.close()
    print("\n✅ Kong configuration fix completed!")

if __name__ == "__main__":
    main()