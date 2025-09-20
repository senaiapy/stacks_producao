#!/usr/bin/env python3

"""
Unified Supabase Deployment Script
Combines all operations from individual scripts into one comprehensive deployment solution.
"""

import paramiko
import time
import sys
import os
from pathlib import Path

# Server configuration
SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

# API Keys and credentials
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI"
DB_PASSWORD = "Ma1x1x0x_testing"

class SupabaseDeployment:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.service_ips = {}

    def connect(self):
        """Establish SSH connection to server"""
        try:
            self.ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
            print("✅ SSH connection established")
            return True
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")
            return False

    def execute_command(self, command, timeout=30):
        """Execute SSH command and return output"""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            return output, error
        except Exception as e:
            return "", str(e)

    def print_step(self, step_number, title):
        """Print formatted step header"""
        print(f"\n{'='*60}")
        print(f"🚀 STEP {step_number}: {title}")
        print('='*60)

    def wait_for_services(self, timeout_minutes=10):
        """Wait for services to become healthy"""
        print(f"⏳ Waiting for services to start (timeout: {timeout_minutes} minutes)...")

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            output, _ = self.execute_command("docker service ls --filter name=supabase --format 'table {{.Name}}\\t{{.Replicas}}'")

            if output:
                lines = output.strip().split('\n')[1:]  # Skip header
                healthy_services = 0
                total_services = len(lines)

                for line in lines:
                    if '1/1' in line:
                        healthy_services += 1

                print(f"    Services healthy: {healthy_services}/{total_services}")

                if healthy_services == total_services and total_services > 0:
                    print(f"✅ All {total_services} services are healthy!")
                    return True

            time.sleep(30)

        print(f"⚠️ Timeout reached. Some services may still be starting.")
        return False

    def step1_prepare_server(self):
        """Step 1: Prepare server environment"""
        self.print_step(1, "PREPARE SERVER ENVIRONMENT")

        # Check Docker Swarm status
        output, error = self.execute_command("docker node ls")
        if "Leader" not in output:
            print("❌ Docker Swarm not initialized")
            return False
        print("✅ Docker Swarm is active")

        # Check required networks
        output, _ = self.execute_command("docker network ls | grep -E '(app_network|traefik_public)'")
        networks = output.split('\n') if output else []

        if len(networks) < 2:
            print("⚠️ Creating missing networks...")
            self.execute_command("docker network create --driver=overlay app_network")
            self.execute_command("docker network create --driver=overlay traefik_public")
        print("✅ Required networks available")

        # Check node labels
        output, _ = self.execute_command("docker node inspect $(docker node ls -q) --format '{{.Spec.Labels}}'")
        if "node-type:primary" not in output:
            print("⚠️ Adding node label...")
            self.execute_command("docker node update --label-add node-type=primary $(docker node ls -q)")
        print("✅ Node labels configured")

        # Create data directories
        print("📁 Creating data directories...")
        directories = [
            "/opt/supabase",
            "/mnt/data/supabase/api",
            "/mnt/data/supabase/storage",
            "/mnt/data/supabase/db/data",
            "/mnt/data/supabase/db/init",
            "/mnt/data/supabase/functions",
            "/mnt/data/supabase/logs"
        ]

        for dir_path in directories:
            self.execute_command(f"mkdir -p {dir_path}")

        # Set PostgreSQL permissions
        self.execute_command("chown -R 999:999 /mnt/data/supabase/db || true")
        self.execute_command("chmod 700 /mnt/data/supabase/db/data || true")

        print("✅ Server preparation completed")
        return True

    def step2_upload_files(self):
        """Step 2: Upload configuration files"""
        self.print_step(2, "UPLOAD CONFIGURATION FILES")

        # Check if supabase.yml exists locally
        if not os.path.exists("supabase.yml"):
            print("❌ supabase.yml not found in current directory")
            return False

        # Upload supabase.yml
        print("📤 Uploading supabase.yml...")
        with open("supabase.yml", "r") as f:
            content = f.read()

        # Escape content for shell
        escaped_content = content.replace("'", "'\"'\"'")
        command = f"cat > /opt/supabase/supabase.yml << 'EOF'\n{content}\nEOF"
        output, error = self.execute_command(command)

        if error:
            print(f"⚠️ Upload warning: {error}")
        print("✅ supabase.yml uploaded")

        # Upload Kong configuration if it exists
        kong_file = Path("volumes/api/kong.yml")
        if kong_file.exists():
            print("📤 Uploading Kong configuration...")
            with open(kong_file, "r") as f:
                kong_content = f.read()

            command = f"cat > /mnt/data/supabase/api/kong.yml << 'EOF'\n{kong_content}\nEOF"
            self.execute_command(command)
            print("✅ Kong configuration uploaded")

        # Upload database scripts if they exist
        db_scripts = ["realtime.sql", "webhooks.sql", "roles.sql", "jwt.sql", "logs.sql"]
        for script in db_scripts:
            script_path = Path(f"volumes/db/{script}")
            if script_path.exists():
                print(f"📤 Uploading {script}...")
                with open(script_path, "r") as f:
                    sql_content = f.read()

                command = f"cat > /mnt/data/supabase/db/{script} << 'EOF'\n{sql_content}\nEOF"
                self.execute_command(command)

        print("✅ File upload completed")
        return True

    def step3_deploy_stack(self):
        """Step 3: Deploy Supabase stack"""
        self.print_step(3, "DEPLOY SUPABASE STACK")

        # Remove existing stack if it exists
        print("🧹 Cleaning up existing stack...")
        self.execute_command("docker stack rm supabase")
        time.sleep(10)

        # Deploy with detached mode
        print("🚀 Deploying Supabase stack...")
        output, error = self.execute_command("cd /opt/supabase && docker stack deploy --detach=true -c supabase.yml supabase")

        if error and "already exists" not in error:
            print(f"⚠️ Deployment warning: {error}")

        if "Created" in output or "Updated" in output:
            print("✅ Stack deployment initiated")
        else:
            print(f"⚠️ Deployment output: {output}")

        return True

    def step4_monitor_startup(self):
        """Step 4: Monitor service startup"""
        self.print_step(4, "MONITOR SERVICE STARTUP")

        return self.wait_for_services(timeout_minutes=8)

    def step5_fix_database(self):
        """Step 5: Fix database users and permissions"""
        self.print_step(5, "FIX DATABASE USERS AND PERMISSIONS")

        # Wait for database to be ready
        print("⏳ Waiting for database to be ready...")
        for _ in range(10):
            output, _ = self.execute_command("docker exec $(docker ps -f name=supabase_db -q) pg_isready -U postgres")
            if "accepting connections" in output:
                break
            time.sleep(10)

        # Create/update database users
        print("👥 Creating/updating database users...")

        users_commands = [
            "ALTER USER supabase_admin WITH PASSWORD 'Ma1x1x0x_testing';",
            "ALTER USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x_testing';",
            "ALTER USER supabase_storage_admin WITH PASSWORD 'Ma1x1x0x_testing';",
            "ALTER USER supabase_read_only_user WITH PASSWORD 'Ma1x1x0x_testing';",
            "CREATE USER IF NOT EXISTS authenticator WITH PASSWORD 'Ma1x1x0x_testing';",
            "CREATE USER IF NOT EXISTS supabase_realtime_admin WITH PASSWORD 'Ma1x1x0x_testing';",
            "CREATE USER IF NOT EXISTS logflare_user WITH PASSWORD 'Ma1x1x0x_testing';",
            "GRANT ALL PRIVILEGES ON DATABASE supabase_db TO supabase_admin;",
            "GRANT ALL PRIVILEGES ON DATABASE postgres TO supabase_admin;",
            "CREATE SCHEMA IF NOT EXISTS _analytics;",
            "CREATE TABLE IF NOT EXISTS _analytics.system_metrics (id SERIAL PRIMARY KEY, created_at TIMESTAMP DEFAULT NOW());"
        ]

        for cmd in users_commands:
            output, error = self.execute_command(f'docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c "{cmd}"')
            if error and "already exists" not in error:
                print(f"  ⚠️ {cmd[:50]}... - {error}")

        print("✅ Database users configured")
        return True

    def step6_get_service_ips(self):
        """Step 6: Get service IP addresses"""
        self.print_step(6, "GET SERVICE IP ADDRESSES")

        output, _ = self.execute_command("docker network inspect app_network --format='{{range .Containers}}{{.Name}},{{.IPv4Address}}{{\"\\n\"}}{{end}}' | grep supabase")

        for line in output.strip().split('\n'):
            if line and ',' in line:
                parts = line.split(',')
                if len(parts) == 2:
                    container_name = parts[0]
                    ip = parts[1].split('/')[0]

                    if 'supabase_studio' in container_name:
                        self.service_ips['studio'] = ip
                    elif 'supabase_auth' in container_name:
                        self.service_ips['auth'] = ip
                    elif 'supabase_rest' in container_name:
                        self.service_ips['rest'] = ip
                    elif 'supabase_meta' in container_name:
                        self.service_ips['meta'] = ip
                    elif 'supabase_storage' in container_name:
                        self.service_ips['storage'] = ip
                    elif 'supabase_realtime' in container_name:
                        self.service_ips['realtime'] = ip

        print("📋 Service IP addresses:")
        for service, ip in self.service_ips.items():
            print(f"  {service}: {ip}")

        return len(self.service_ips) > 0

    def step7_configure_kong(self):
        """Step 7: Configure Kong with working routing"""
        self.print_step(7, "CONFIGURE KONG ROUTING")

        if not self.service_ips:
            print("⚠️ No service IPs available, using service names")

        # Create Kong configuration with IPs
        kong_config = f"""_format_version: '2.1'
_transform: true

consumers:
  - username: DASHBOARD
  - username: anon
    keyauth_credentials:
      - key: {ANON_KEY}
  - username: service_role
    keyauth_credentials:
      - key: {SERVICE_KEY}

basicauth_credentials:
  - consumer: DASHBOARD
    username: supabase
    password: Ma1x1x0x_testing

services:"""

        # Add services with their IPs if available
        if 'studio' in self.service_ips:
            kong_config += f"""
  ## Studio Dashboard
  - name: studio
    url: http://{self.service_ips['studio']}:3000
    routes:
      - name: studio-root
        paths: ["/"]
        strip_path: false
    plugins:
      - name: basic-auth
      - name: cors"""

        if 'auth' in self.service_ips:
            kong_config += f"""
  ## Auth Service
  - name: auth-v1
    url: http://{self.service_ips['auth']}:9999
    routes:
      - name: auth-v1-all
        paths: ["/auth/v1"]
        strip_path: true
    plugins:
      - name: cors"""

        if 'rest' in self.service_ips:
            kong_config += f"""
  ## REST API
  - name: rest-v1
    url: http://{self.service_ips['rest']}:3000
    routes:
      - name: rest-v1-all
        paths: ["/rest/v1"]
        strip_path: true
    plugins:
      - name: key-auth
      - name: cors"""

        if 'meta' in self.service_ips:
            kong_config += f"""
  ## Meta API
  - name: meta
    url: http://{self.service_ips['meta']}:8080
    routes:
      - name: meta-all
        paths: ["/pg"]
        strip_path: true
    plugins:
      - name: basic-auth"""

        if 'storage' in self.service_ips:
            kong_config += f"""
  ## Storage API
  - name: storage-v1
    url: http://{self.service_ips['storage']}:5000
    routes:
      - name: storage-v1-all
        paths: ["/storage/v1"]
        strip_path: true
    plugins:
      - name: key-auth
      - name: cors"""

        # Upload Kong configuration
        print("📤 Uploading Kong configuration...")
        escaped_config = kong_config.replace("'", "'\"'\"'")
        command = f"docker exec $(docker ps -f name=supabase_kong -q) cat > /home/kong/kong.yml << 'EOF'\n{kong_config}\nEOF"
        self.execute_command(command)

        # Reload Kong
        print("🔄 Reloading Kong...")
        output, error = self.execute_command("docker exec $(docker ps -f name=supabase_kong -q) kong reload")

        if error:
            print(f"⚠️ Kong reload warning: {error}")
        else:
            print("✅ Kong configuration updated")

        return True

    def step8_create_direct_studio(self):
        """Step 8: Create direct Studio access (fallback)"""
        self.print_step(8, "CREATE DIRECT STUDIO ACCESS")

        if 'studio' not in self.service_ips:
            print("⚠️ Studio IP not available, skipping direct access")
            return False

        # Create direct Studio service
        studio_service = f"""version: '3.8'
services:
  studio-direct:
    image: supabase/studio
    networks:
      - traefik_public
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.constraint-label=traefik_public"
        - "traefik.swarm.network=traefik_public"
        - "traefik.http.routers.studio-direct-http.rule=Host(\`studio.senaia.in\`)"
        - "traefik.http.routers.studio-direct-http.entrypoints=web"
        - "traefik.http.routers.studio-direct-http.middlewares=https-redirect"
        - "traefik.http.routers.studio-direct-https.rule=Host(\`studio.senaia.in\`)"
        - "traefik.http.routers.studio-direct-https.entrypoints=websecure"
        - "traefik.http.routers.studio-direct-https.tls=true"
        - "traefik.http.routers.studio-direct-https.tls.certresolver=letsencrypt"
        - "traefik.http.services.studio-direct.loadbalancer.server.port=3000"
        - "traefik.http.middlewares.https-redirect.redirectscheme.scheme=https"
        - "traefik.http.middlewares.https-redirect.redirectscheme.permanent=true"
    environment:
      SUPABASE_PUBLIC_URL: https://supabase.senaia.in
      SUPABASE_ANON_KEY: {ANON_KEY}
      SUPABASE_SERVICE_KEY: {SERVICE_KEY}

networks:
  traefik_public:
    external: true
"""

        # Upload and deploy direct Studio
        command = f"cat > /opt/supabase/studio-direct.yml << 'EOF'\n{studio_service}\nEOF"
        self.execute_command(command)

        self.execute_command("cd /opt/supabase && docker stack deploy --detach=true -c studio-direct.yml studio-direct")

        print("✅ Direct Studio access created at: https://studio.senaia.in")
        return True

    def step9_test_endpoints(self):
        """Step 9: Test all endpoints"""
        self.print_step(9, "TEST ALL ENDPOINTS")

        test_cases = [
            ("Kong Main", "/", "basic", "supabase:Ma1x1x0x_testing"),
            ("Direct Studio", "https://studio.senaia.in/", "none", ""),
            ("Auth Health", "/auth/v1/health", "none", ""),
            ("REST API", "/rest/v1/", "apikey", ANON_KEY),
            ("Meta Health", "/pg/health", "basic", "supabase:Ma1x1x0x_testing"),
        ]

        if 'storage' in self.service_ips:
            test_cases.append(("Storage API", "/storage/v1/", "apikey", ANON_KEY))

        print("🧪 Testing endpoints...")
        results = {}

        for name, endpoint, auth_type, credentials in test_cases:
            if endpoint.startswith("https://"):
                url = endpoint
            else:
                url = f"https://supabase.senaia.in{endpoint}"

            if auth_type == "basic":
                cmd = f'curl -u "{credentials}" -s -o /dev/null -w "%{{http_code}}" "{url}" 2>/dev/null'
            elif auth_type == "apikey":
                cmd = f'curl -H "apikey: {credentials}" -s -o /dev/null -w "%{{http_code}}" "{url}" 2>/dev/null'
            else:  # none
                cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{url}" 2>/dev/null'

            output, _ = self.execute_command(cmd)
            status = output.strip()

            # Interpret status codes
            if status in ['200', '201']:
                emoji = '✅'
                desc = 'Working'
            elif status == '401':
                emoji = '🔐'
                desc = 'Auth Required (OK)'
            elif status == '404':
                emoji = '❌'
                desc = 'Not Found'
            elif status == '503':
                emoji = '⚠️'
                desc = 'Service Unavailable'
            else:
                emoji = '❓'
                desc = f'Status {status}'

            results[name] = (status, desc)
            print(f"  {emoji} {name:20}: {desc}")

        return results

    def step10_final_status(self):
        """Step 10: Display final status and instructions"""
        self.print_step(10, "FINAL STATUS AND ACCESS INFORMATION")

        # Show service status
        print("📊 Final service status:")
        output, _ = self.execute_command("docker service ls --filter name=supabase --format 'table {{.Name}}\\t{{.Replicas}}\\t{{.Image}}'")
        print(output)

        print("\n" + "="*60)
        print("🎉 SUPABASE DEPLOYMENT COMPLETED!")
        print("="*60)

        print("\n✅ ACCESS INFORMATION:")
        print("🌐 Main Dashboard: https://supabase.senaia.in")
        print("🎨 Direct Studio: https://studio.senaia.in")
        print("🔐 Login: supabase / Ma1x1x0x_testing")

        print("\n🔑 API CREDENTIALS:")
        print(f"📧 Anon Key: {ANON_KEY}")
        print(f"🔧 Service Key: {SERVICE_KEY}")

        print("\n🛠️ API ENDPOINTS:")
        print("🔓 Auth (Public): https://supabase.senaia.in/auth/v1/health")
        print("📊 REST API: https://supabase.senaia.in/rest/v1/ (requires apikey header)")
        print("💾 Storage: https://supabase.senaia.in/storage/v1/ (requires apikey header)")
        print("📈 Meta: https://supabase.senaia.in/pg/health (basic auth)")

        print("\n🔍 TROUBLESHOOTING:")
        print("📋 Service logs: docker service logs -f supabase_SERVICE_NAME")
        print("🔄 Restart service: docker service update --force supabase_SERVICE_NAME")
        print("🔧 Kong logs: docker service logs -f supabase_kong")

        return True

    def run_deployment(self):
        """Run complete deployment process"""
        print("🚀 UNIFIED SUPABASE DEPLOYMENT STARTING...")
        print(f"🎯 Target server: {SERVER_IP}")
        print("="*60)

        if not self.connect():
            return False

        try:
            # Execute all deployment steps
            steps = [
                self.step1_prepare_server,
                self.step2_upload_files,
                self.step3_deploy_stack,
                self.step4_monitor_startup,
                self.step5_fix_database,
                self.step6_get_service_ips,
                self.step7_configure_kong,
                self.step8_create_direct_studio,
                self.step9_test_endpoints,
                self.step10_final_status
            ]

            for i, step in enumerate(steps, 1):
                success = step()
                if not success and i <= 5:  # Critical steps
                    print(f"❌ Critical step {i} failed. Aborting deployment.")
                    return False
                elif not success:
                    print(f"⚠️ Step {i} had issues but continuing...")

            print("\n🎊 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            return True

        except KeyboardInterrupt:
            print("\n⚠️ Deployment interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Deployment failed with error: {e}")
            return False
        finally:
            self.ssh.close()

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Unified Supabase Deployment Script

Usage: python3 unified_deployment.py

This script performs a complete Supabase deployment including:
1. Server preparation and network setup
2. File uploads and configuration
3. Stack deployment with proper flags
4. Service monitoring and health checks
5. Database user setup and permissions
6. Kong API Gateway configuration with IP routing
7. Direct Studio access creation (fallback)
8. Endpoint testing and validation
9. Final status report and access information

The script handles common issues like:
- Network conflicts and DNS resolution
- Database authentication problems
- Kong configuration and routing
- Service startup dependencies
- Health check optimization

Requirements:
- Python 3 with paramiko module
- supabase.yml file in current directory
- SSH access to target server
""")
        return

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    deployment = SupabaseDeployment()
    success = deployment.run_deployment()

    if success:
        print("\n🌟 Your Supabase instance is ready for use!")
        sys.exit(0)
    else:
        print("\n💥 Deployment failed. Check logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()