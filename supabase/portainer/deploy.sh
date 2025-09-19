#!/bin/bash

# Supabase Deployment Script
SERVER_IP="217.79.184.8"
SERVER_USER="root"
SERVER_PASS="@450Ab6606"

echo "🚀 Starting Supabase deployment to $SERVER_IP"

# Function to execute remote commands
remote_exec() {
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$1"
}

# Function to copy files
remote_copy() {
    sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$1" $SERVER_USER@$SERVER_IP:"$2"
}

echo "📋 Step 1: Verifying Docker Swarm..."
remote_exec "docker node ls"

echo "📂 Step 2: Creating directories..."
remote_exec "mkdir -p /opt/supabase"
remote_exec "mkdir -p /mnt/data/supabase/{api,storage,db,functions,logs}"
remote_exec "mkdir -p /mnt/data/supabase/db/{data,init}"

echo "📤 Step 3: Copying files..."
remote_copy "supabase.yml" "/opt/supabase/"
remote_copy "volumes/" "/opt/supabase/"
remote_copy "SUPABASE-MANUAL.md" "/opt/supabase/"

echo "🔧 Step 4: Setting up configuration files..."
remote_exec "cp /opt/supabase/volumes/api/kong.yml /mnt/data/supabase/api/"
remote_exec "cp /opt/supabase/volumes/logs/vector.yml /mnt/data/supabase/logs/"
remote_exec "cp /opt/supabase/volumes/db/*.sql /mnt/data/supabase/db/ 2>/dev/null || true"
remote_exec "cp -r /opt/supabase/volumes/db/init/* /mnt/data/supabase/db/init/ 2>/dev/null || true"

echo "🌐 Step 5: Creating Docker networks..."
remote_exec "docker network create --driver=overlay traefik_public || true"
remote_exec "docker network create --driver=overlay app_network || true"

echo "🗄️ Step 6: Deploying Supabase stack..."
remote_exec "cd /opt/supabase && docker stack deploy -c supabase.yml supabase"

echo "⏳ Step 7: Waiting for services to start..."
sleep 30

echo "📊 Step 8: Checking service status..."
remote_exec "docker service ls"

echo "✅ Deployment complete!"
echo "🌍 Access your Supabase at: https://supabase.senaia-bank.in"
echo "👤 Dashboard credentials: supabase / Ma1x1x0x_testing"