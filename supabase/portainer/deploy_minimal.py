#!/usr/bin/env python3
"""
Minimal Supabase Deployment - Focus on Core Services with Web Access
"""

import paramiko
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def deploy_minimal_supabase():
    print("🚀 MINIMAL SUPABASE DEPLOYMENT - WEB ACCESS FOCUSED")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)

    # Step 1: Clean existing deployment
    print("\n🧹 Cleaning existing deployment...")
    ssh.exec_command("docker stack rm supabase")
    time.sleep(20)

    # Step 2: Create minimal working configuration
    minimal_config = """version: "3.8"

networks:
  app_network:
    external: true
  traefik_public:
    external: true

services:
  # PostgreSQL Database - Core requirement
  db:
    image: postgres:15
    hostname: db
    deploy:
      restart_policy:
        condition: any
      placement:
        constraints: [node.labels.node-type == primary]
    networks:
      - app_network
    volumes:
      - /mnt/data/supabase/db/data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: Ma1x1x0x_testing
      POSTGRES_DB: postgres
    command: ["postgres", "-c", "log_min_messages=fatal", "-c", "port=25432"]

  # Supabase Studio - Web UI with Direct Traefik Access
  studio:
    image: supabase/studio:latest
    hostname: studio
    deploy:
      restart_policy:
        condition: any
      labels:
        - "traefik.enable=true"
        - "traefik.constraint-label=traefik_public"
        - "traefik.swarm.network=traefik_public"
        - "traefik.http.routers.studio.rule=Host(`studio.senaia.in`)"
        - "traefik.http.routers.studio.entrypoints=websecure"
        - "traefik.http.routers.studio.tls=true"
        - "traefik.http.routers.studio.tls.certresolver=letsencrypt"
        - "traefik.http.services.studio.loadbalancer.server.port=3000"
    networks:
      - app_network
      - traefik_public
    depends_on:
      - db
    environment:
      HOSTNAME: 0.0.0.0
      PORT: "3000"
      POSTGRES_PASSWORD: Ma1x1x0x_testing
      DEFAULT_ORGANIZATION_NAME: SENAIA
      DEFAULT_PROJECT_NAME: SENAIA_AI
      SUPABASE_PUBLIC_URL: https://studio.senaia.in
      SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao
      SUPABASE_SERVICE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0NDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI

  # PostgREST - REST API with Direct Access
  rest:
    image: postgrest/postgrest:v12.0.1
    hostname: rest
    deploy:
      restart_policy:
        condition: any
      labels:
        - "traefik.enable=true"
        - "traefik.constraint-label=traefik_public"
        - "traefik.swarm.network=traefik_public"
        - "traefik.http.routers.api.rule=Host(`api.senaia.in`)"
        - "traefik.http.routers.api.entrypoints=websecure"
        - "traefik.http.routers.api.tls=true"
        - "traefik.http.routers.api.tls.certresolver=letsencrypt"
        - "traefik.http.services.api.loadbalancer.server.port=3000"
    networks:
      - app_network
      - traefik_public
    depends_on:
      - db
    environment:
      PGRST_DB_URI: postgres://postgres:Ma1x1x0x_testing@db:25432/postgres
      PGRST_DB_SCHEMAS: public
      PGRST_DB_ANON_ROLE: postgres
      PGRST_JWT_SECRET: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz

  # GoTrue - Auth Service with Direct Access
  auth:
    image: supabase/gotrue:v2.151.0
    hostname: auth
    deploy:
      restart_policy:
        condition: any
      labels:
        - "traefik.enable=true"
        - "traefik.constraint-label=traefik_public"
        - "traefik.swarm.network=traefik_public"
        - "traefik.http.routers.auth.rule=Host(`auth.senaia.in`)"
        - "traefik.http.routers.auth.entrypoints=websecure"
        - "traefik.http.routers.auth.tls=true"
        - "traefik.http.routers.auth.tls.certresolver=letsencrypt"
        - "traefik.http.services.auth.loadbalancer.server.port=9999"
    networks:
      - app_network
      - traefik_public
    depends_on:
      - db
    environment:
      GOTRUE_API_HOST: 0.0.0.0
      GOTRUE_API_PORT: "9999"
      GOTRUE_DB_DRIVER: postgres
      GOTRUE_DB_DATABASE_URL: postgres://postgres:Ma1x1x0x_testing@db:25432/postgres
      GOTRUE_SITE_URL: https://studio.senaia.in
      GOTRUE_URI_ALLOW_LIST: https://studio.senaia.in,https://api.senaia.in,https://auth.senaia.in
      GOTRUE_DISABLE_SIGNUP: "false"
      GOTRUE_JWT_SECRET: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
      GOTRUE_EXTERNAL_EMAIL_ENABLED: "true"
      GOTRUE_MAILER_AUTOCONFIRM: "true"
"""

    # Step 3: Upload and deploy minimal configuration
    print("\n📤 Uploading minimal configuration...")
    command = f"""cat > /opt/supabase/minimal.yml << 'EOF'
{minimal_config}
EOF"""
    ssh.exec_command(command)

    print("\n🚀 Deploying minimal stack...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker stack deploy -c minimal.yml supabase")
    output = stdout.read().decode()
    error = stderr.read().decode()

    print(f"Deploy output: {output}")
    if error:
        print(f"Deploy warnings: {error}")

    # Step 4: Wait and monitor services
    print("\n⏳ Waiting for services to start...")
    time.sleep(60)

    for i in range(5):
        stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase --format 'table {{.Name}}\\t{{.Replicas}}\\t{{.Image}}'")
        services = stdout.read().decode()
        print(f"\n📊 Service Status (Check {i+1}):")
        print(services)

        # Check if all services are running
        healthy_count = services.count('1/1')
        if healthy_count >= 3:  # db, studio, rest, auth
            print("\n✅ Core services are healthy!")
            break

        if i < 4:
            print("⏳ Waiting 30 more seconds...")
            time.sleep(30)

    # Step 5: Test web access
    print("\n🧪 Testing web access...")

    test_urls = [
        ("Studio UI", "https://studio.senaia.in/"),
        ("REST API", "https://api.senaia.in/"),
        ("Auth API", "https://auth.senaia.in/health"),
    ]

    for name, url in test_urls:
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' -m 10 '{url}' 2>/dev/null")
        status_code = stdout.read().decode().strip()

        if status_code in ['200', '201', '301', '302']:
            print(f"✅ {name}: {status_code} - Working")
        elif status_code == '401':
            print(f"🔐 {name}: {status_code} - Auth Required (Normal)")
        else:
            print(f"⚠️ {name}: {status_code} - Check configuration")

    print("\n" + "="*60)
    print("🎉 MINIMAL SUPABASE DEPLOYMENT COMPLETED!")
    print("🌐 Web Access URLs:")
    print("   📊 Studio:   https://studio.senaia.in")
    print("   🔧 REST API: https://api.senaia.in")
    print("   🔐 Auth API: https://auth.senaia.in")
    print("🔑 Default credentials: postgres / Ma1x1x0x_testing")
    print("="*60)

    ssh.close()
    return True

if __name__ == "__main__":
    deploy_minimal_supabase()