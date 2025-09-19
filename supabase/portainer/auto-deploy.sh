#!/bin/bash

# Supabase Auto-Deployment Script
# Run this script from your local machine with sshpass installed

SERVER_IP="217.79.184.8"
SERVER_USER="root"
SERVER_PASS="@450Ab6606"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    print_error "sshpass is not installed. Please install it first:"
    echo "  Ubuntu/Debian: sudo apt-get install sshpass"
    echo "  CentOS/RHEL: sudo yum install sshpass"
    echo "  macOS: brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# Function to execute remote commands
remote_exec() {
    print_status "Executing: $1"
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER_USER@$SERVER_IP "$1"
    if [ $? -eq 0 ]; then
        print_status "✅ Command completed successfully"
    else
        print_error "❌ Command failed"
        return 1
    fi
}

# Function to copy files
remote_copy() {
    print_status "Copying: $1 → $2"
    sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "$1" $SERVER_USER@$SERVER_IP:"$2"
    if [ $? -eq 0 ]; then
        print_status "✅ File copied successfully"
    else
        print_error "❌ File copy failed"
        return 1
    fi
}

echo "🚀 Starting Supabase deployment to $SERVER_IP"
echo "=================================================="

# Step 1: Verify connection and Docker Swarm
print_status "📋 Step 1: Verifying Docker Swarm..."
remote_exec "docker node ls" || {
    print_error "Docker Swarm is not running or accessible"
    exit 1
}

# Step 2: Create directories
print_status "📂 Step 2: Creating directories..."
remote_exec "mkdir -p /opt/supabase"
remote_exec "mkdir -p /mnt/data/supabase/{api,storage,db,functions,logs}"
remote_exec "mkdir -p /mnt/data/supabase/db/{data,init}"

# Step 3: Copy files
print_status "📤 Step 3: Copying files..."
remote_copy "supabase.yml" "/opt/supabase/"
remote_copy "volumes/" "/opt/supabase/"
remote_copy "SUPABASE-MANUAL.md" "/opt/supabase/"

# Step 4: Setup configuration files
print_status "🔧 Step 4: Setting up configuration files..."
remote_exec "cp /opt/supabase/volumes/api/kong.yml /mnt/data/supabase/api/"
remote_exec "cp /opt/supabase/volumes/logs/vector.yml /mnt/data/supabase/logs/"
remote_exec "cp /opt/supabase/volumes/db/*.sql /mnt/data/supabase/db/ 2>/dev/null || true"
remote_exec "cp -r /opt/supabase/volumes/db/init/* /mnt/data/supabase/db/init/ 2>/dev/null || true"

# Set proper permissions
remote_exec "chown -R 999:999 /mnt/data/supabase/db"
remote_exec "chmod 700 /mnt/data/supabase/db/data"

# Step 5: Create Docker networks
print_status "🌐 Step 5: Creating Docker networks..."
remote_exec "docker network create --driver=overlay traefik_public || echo 'Network traefik_public already exists'"
remote_exec "docker network create --driver=overlay app_network || echo 'Network app_network already exists'"

# Verify networks
remote_exec "docker network ls | grep overlay"

# Step 6: Deploy Supabase stack
print_status "🗄️ Step 6: Deploying Supabase stack..."
remote_exec "cd /opt/supabase && docker stack deploy -c supabase.yml supabase"

# Step 7: Wait for services to start
print_status "⏳ Step 7: Waiting for services to start..."
sleep 30

# Step 8: Check service status
print_status "📊 Step 8: Checking service status..."
remote_exec "docker service ls"

# Step 9: Verify specific services
print_status "🔍 Step 9: Verifying deployment..."
sleep 30
remote_exec "docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}'"

# Test database
print_status "🗄️ Testing database connection..."
remote_exec "timeout 10 docker exec \$(docker ps -f name=supabase_db -q) pg_isready -U postgres || echo 'Database still starting...'"

echo ""
echo "=================================================="
print_status "✅ Deployment completed!"
echo ""
echo "🌍 Access URLs:"
echo "  - Supabase Studio: https://supabase.senaia-bank.in"
echo "  - API Endpoint: https://supabase.senaia-bank.in/rest/v1/"
echo ""
echo "👤 Default Credentials:"
echo "  - Username: supabase"
echo "  - Password: Ma1x1x0x_testing"
echo ""
echo "🔑 API Keys:"
echo "  - ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao"
echo ""
echo "📋 To monitor deployment:"
echo "  ssh root@$SERVER_IP"
echo "  docker service ls"
echo "  docker service logs supabase_kong"
echo ""
echo "🔧 If issues occur:"
echo "  docker service logs supabase_SERVICE_NAME"
echo "  docker service update --force supabase_SERVICE_NAME"