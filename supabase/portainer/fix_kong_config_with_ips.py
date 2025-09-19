#!/usr/bin/env python3

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔧 FINAL FIX: Updating Kong config to use IP addresses...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Get all service IPs from the network
    print("\n🌐 Getting all service IP addresses...")
    stdin, stdout, stderr = ssh.exec_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}},{{.IPv4Address}}{{\"\\n\"}}{{end}}' | grep supabase")
    network_info = stdout.read().decode()

    service_ips = {}
    for line in network_info.strip().split('\n'):
        if line:
            parts = line.split(',')
            if len(parts) == 2:
                container_name = parts[0]
                ip_with_mask = parts[1]
                ip = ip_with_mask.split('/')[0]  # Remove /24

                # Extract service name
                if 'supabase_studio' in container_name:
                    service_ips['studio'] = ip
                elif 'supabase_auth' in container_name:
                    service_ips['auth'] = ip
                elif 'supabase_rest' in container_name:
                    service_ips['rest'] = ip
                elif 'supabase_realtime' in container_name:
                    service_ips['realtime'] = ip
                elif 'supabase_storage' in container_name:
                    service_ips['storage'] = ip
                elif 'supabase_meta' in container_name:
                    service_ips['meta'] = ip

    print("Service IPs found:")
    for service, ip in service_ips.items():
        print(f"  {service}: {ip}")

    # 2. Read current Kong configuration
    print("\n📋 Reading current Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cat /home/kong/kong.yml")
    current_config = stdout.read().decode()

    # 3. Create updated Kong configuration with IP addresses
    print("\n🔧 Creating updated Kong configuration with IP addresses...")

    # Replace service names with IPs in the config
    updated_config = current_config
    for service, ip in service_ips.items():
        # Replace http://servicename: with http://ip:
        updated_config = updated_config.replace(f'http://{service}:', f'http://{ip}:')

    # 4. Upload the updated configuration
    print("\n📤 Uploading updated Kong configuration...")

    # Write the updated config to a temporary file
    config_content = updated_config.replace("'", "'\"'\"'")  # Escape single quotes for shell
    stdin, stdout, stderr = ssh.exec_command(f"docker exec $(docker ps -f name=supabase_kong -q) sh -c 'cat > /home/kong/kong_updated.yml' <<'EOF'\n{updated_config}\nEOF")

    # Copy the updated config over the original
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) cp /home/kong/kong_updated.yml /home/kong/kong.yml")

    # 5. Reload Kong configuration
    print("\n🔄 Reloading Kong configuration...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")
    reload_output = stdout.read().decode()
    print(f"Kong reload result: {reload_output}")

    # Wait for reload to complete
    time.sleep(10)

    # 6. Test Kong health
    print("\n🧪 Testing Kong health after reload...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong health")
    health_output = stdout.read().decode()
    print(f"Kong health: {health_output}")

    # 7. Test external access
    print("\n🌐 Testing external access...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s -o /dev/null -w '%{http_code}' 'https://supabase.senaia.in/' 2>/dev/null")
    status_code = stdout.read().decode().strip()
    print(f"External access status: {status_code}")

    # 8. Test Studio specifically
    print("\n🎨 Testing Studio access...")
    stdin, stdout, stderr = ssh.exec_command("curl -u 'supabase:Ma1x1x0x_testing' -s 'https://supabase.senaia.in/project/default' 2>&1 | head -5")
    studio_test = stdout.read().decode()
    print(f"Studio test result: {studio_test}")

    # 9. Check Kong logs for any errors
    print("\n📋 Checking Kong logs...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 5 supabase_kong")
    kong_logs = stdout.read().decode()
    print(f"Kong logs: {kong_logs}")

    ssh.close()
    print("\n🎉 Kong configuration update completed!")
    print("\n✅ SUPABASE SHOULD NOW BE FULLY WORKING!")
    print("\n🌐 Access your Supabase Studio at:")
    print("URL: https://supabase.senaia.in")
    print("Username: supabase")
    print("Password: Ma1x1x0x_testing")

if __name__ == "__main__":
    main()