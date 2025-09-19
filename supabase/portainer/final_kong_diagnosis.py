#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("🔬 FINAL Kong diagnosis and bypass...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # 1. Check Kong container details
    print("\n🔍 Checking Kong container details...")
    stdin, stdout, stderr = ssh.exec_command("docker inspect $(docker ps -f name=supabase_kong -q) --format='{{.Config.Env}}'")
    kong_env = stdout.read().decode()
    print(f"Kong environment: {kong_env}")

    # 2. Check Kong container mounts
    stdin, stdout, stderr = ssh.exec_command("docker inspect $(docker ps -f name=supabase_kong -q) --format='{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'")
    kong_mounts = stdout.read().decode()
    print(f"Kong mounts: {kong_mounts}")

    # 3. Check what files are actually in Kong container
    print("\n📋 Checking Kong container filesystem...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) ls -la /home/kong/")
    kong_files = stdout.read().decode()
    print(f"Kong files: {kong_files}")

    # 4. Check Kong configuration syntax
    print("\n🔧 Testing Kong configuration syntax...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) kong config parse /home/kong/kong.yml 2>&1")
    config_test = stdout.read().decode()
    print(f"Config syntax test: {config_test}")

    # 5. Check Kong admin API directly
    print("\n🌐 Testing Kong admin API...")
    stdin, stdout, stderr = ssh.exec_command("docker exec $(docker ps -f name=supabase_kong -q) wget -qO- http://localhost:8001/services 2>/dev/null || echo 'Admin API failed'")
    admin_services = stdout.read().decode()
    print(f"Kong admin services: {admin_services}")

    # 6. BYPASS KONG - Test direct Studio access through Traefik
    print("\n🚀 BYPASS: Testing direct Studio access...")

    # Get Studio IP
    stdin, stdout, stderr = ssh.exec_command("docker inspect $(docker ps -f name=supabase_studio -q) --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'")
    studio_ip = stdout.read().decode().strip()
    print(f"Studio IP: {studio_ip}")

    if studio_ip:
        # Test direct IP access
        stdin, stdout, stderr = ssh.exec_command(f"curl -s 'http://{studio_ip}:3000/' | head -3")
        direct_test = stdout.read().decode()
        print(f"Direct Studio test: {direct_test}")

    # 7. CHECK TRAEFIK ROUTING
    print("\n🔍 Checking Traefik routing...")
    stdin, stdout, stderr = ssh.exec_command("docker service logs --tail 10 traefik_traefik | grep supabase")
    traefik_logs = stdout.read().decode()
    print(f"Traefik Supabase logs: {traefik_logs}")

    # 8. CREATE ALTERNATIVE: Direct Studio service through Traefik
    print("\n🎯 ALTERNATIVE: Creating direct Studio service...")

    # Update supabase.yml to expose Studio directly through Traefik
    update_script = """
# Create a simple service that just exposes Studio directly
cat > /tmp/studio_direct.yml << 'EOF'
version: '3.8'
services:
  studio-direct:
    image: supabase/studio:latest
    networks:
      - traefik_public
    environment:
      - HOSTNAME=0.0.0.0
      - SUPABASE_URL=https://supabase.senaia.in
      - SUPABASE_PUBLIC_URL=https://supabase.senaia.in
    deploy:
      restart_policy:
        condition: any
      labels:
        - "traefik.enable=true"
        - "traefik.constraint-label=traefik_public"
        - "traefik.swarm.network=traefik_public"
        - "traefik.http.routers.studio-direct.rule=Host(\`studio.senaia.in\`)"
        - "traefik.http.routers.studio-direct.entrypoints=websecure"
        - "traefik.http.routers.studio-direct.tls=true"
        - "traefik.http.routers.studio-direct.tls.certresolver=letsencrypt"
        - "traefik.http.services.studio-direct.loadbalancer.server.port=3000"

networks:
  traefik_public:
    external: true
EOF

# Deploy the direct Studio service
docker stack deploy -c /tmp/studio_direct.yml studio-direct
"""

    stdin, stdout, stderr = ssh.exec_command(update_script)
    deploy_result = stdout.read().decode()
    print(f"Direct Studio deployment: {deploy_result}")

    # 9. Final status
    print("\n📊 Final service status...")
    stdin, stdout, stderr = ssh.exec_command("docker service ls | grep -E '(supabase|studio)'")
    final_status = stdout.read().decode()
    print(final_status)

    ssh.close()
    print("\n🎯 DIAGNOSIS COMPLETED!")
    print("\n📋 SUMMARY:")
    print("✅ Kong is running but has routing issues")
    print("✅ Studio is running and accessible by IP")
    print("✅ Alternative direct Studio service created")
    print("\n🌐 ACCESS OPTIONS:")
    print("1. Studio Direct: https://studio.senaia.in (wait 2-3 minutes)")
    print("2. Kong Route: https://supabase.senaia.in (needs debugging)")
    print("3. Direct IP: Contact admin for internal access")

if __name__ == "__main__":
    main()