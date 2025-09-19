# Supabase Server Deployment Guide

## Overview

This guide provides instructions for deploying Supabase configuration files to an external server and updating the deployment configuration for production use.

## Required Files for Server Deployment

### Core Configuration Files (Required for Docker Configs)
```
/opt/supabase/config/
├── kong.yml              # API Gateway configuration
├── vector.yml             # Log collection configuration
└── pooler.exs             # Connection pooler configuration
```

### Database Migration Files (For PostgreSQL Setup)
```
/opt/supabase/db-migrations/
├── roles.sql              # Database users and roles
├── realtime.sql           # Realtime schema setup
├── jwt.sql                # JWT configuration
├── logs.sql               # Logging schema
├── pooler.sql             # Connection pooler schema
├── _supabase.sql          # Internal Supabase schemas
├── webhooks.sql           # Webhook functionality
└── init/
    └── data.sql           # Initial data setup
```

### Optional Files (Reference/Backup)
```
/opt/supabase/reference/
├── authelia/
│   └── configuration.yml  # Authelia config (if needed)
└── db/
    └── schema-authelia.sh  # Authelia schema script
```

## Step 1: Create Server Directory Structure

### On Your Server, run:
```bash
# Create main Supabase configuration directory
sudo mkdir -p /opt/supabase/{config,db-migrations,reference}
sudo mkdir -p /opt/supabase/db-migrations/init
sudo mkdir -p /opt/supabase/reference/{authelia,db}

# Set appropriate permissions
sudo chown -R $(whoami):docker /opt/supabase
sudo chmod -R 755 /opt/supabase
```

## Step 2: Transfer Files to Server

### Option A: Using SCP (from local machine)
```bash
# From your local machine where files exist
SERVER_IP="your-server-ip"
SERVER_USER="your-username"

# Transfer core config files
scp supabase/docker/volumes/api/kong.yml $SERVER_USER@$SERVER_IP:/opt/supabase/config/
scp supabase/docker/volumes/logs/vector.yml $SERVER_USER@$SERVER_IP:/opt/supabase/config/
scp supabase/docker/volumes/pooler/pooler.exs $SERVER_USER@$SERVER_IP:/opt/supabase/config/

# Transfer database migration files
scp supabase/docker/volumes/db/*.sql $SERVER_USER@$SERVER_IP:/opt/supabase/db-migrations/
scp supabase/docker/volumes/db/init/data.sql $SERVER_USER@$SERVER_IP:/opt/supabase/db-migrations/init/

# Transfer reference files
scp supabase/docker/volumes/authelia/configuration.yml $SERVER_USER@$SERVER_IP:/opt/supabase/reference/authelia/
scp supabase/docker/volumes/db/schema-authelia.sh $SERVER_USER@$SERVER_IP:/opt/supabase/reference/db/
```

### Option B: Using rsync (Recommended)
```bash
# Sync entire directory structure
rsync -avz --progress supabase/docker/volumes/ $SERVER_USER@$SERVER_IP:/opt/supabase/reference/

# Copy specific files to correct locations
ssh $SERVER_USER@$SERVER_IP "
cp /opt/supabase/reference/api/kong.yml /opt/supabase/config/
cp /opt/supabase/reference/logs/vector.yml /opt/supabase/config/
cp /opt/supabase/reference/pooler/pooler.exs /opt/supabase/config/
cp /opt/supabase/reference/db/*.sql /opt/supabase/db-migrations/
cp /opt/supabase/reference/db/init/data.sql /opt/supabase/db-migrations/init/
"
```

### Option C: Direct Download (if files are in Git repository)
```bash
# On your server
cd /opt/supabase

# If you have Git access to the repository
git clone <your-repo-url> temp-repo
cp temp-repo/supabase/docker/volumes/api/kong.yml config/
cp temp-repo/supabase/docker/volumes/logs/vector.yml config/
cp temp-repo/supabase/docker/volumes/pooler/pooler.exs config/
cp temp-repo/supabase/docker/volumes/db/*.sql db-migrations/
cp temp-repo/supabase/docker/volumes/db/init/data.sql db-migrations/init/
rm -rf temp-repo
```

## Step 3: Verify File Transfer

### On your server, verify all files are present:
```bash
# Check core config files
ls -la /opt/supabase/config/
# Should show: kong.yml, vector.yml, pooler.exs

# Check database migration files
ls -la /opt/supabase/db-migrations/
# Should show: *.sql files

# Check init data
ls -la /opt/supabase/db-migrations/init/
# Should show: data.sql

# Verify file permissions
find /opt/supabase -type f -exec ls -la {} \;
```

## Step 4: Create Docker Configs

### On your server, create Docker configs from the transferred files:
```bash
# Navigate to server directory
cd /opt/supabase

# Create Docker configs (requires Docker Swarm to be initialized)
docker config create supabase_kong_config config/kong.yml
docker config create supabase_vector_config config/vector.yml
docker config create supabase_pooler_config config/pooler.exs

# Verify configs were created
docker config ls | grep supabase
```

## Step 5: Run Database Migrations

### Connect to your PostgreSQL instance and run migrations:
```bash
# Option A: Using psql directly
psql -h your-postgres-host -U postgres -d your-database

# Run each migration file
\i /opt/supabase/db-migrations/roles.sql
\i /opt/supabase/db-migrations/realtime.sql
\i /opt/supabase/db-migrations/jwt.sql
\i /opt/supabase/db-migrations/logs.sql
\i /opt/supabase/db-migrations/pooler.sql
\i /opt/supabase/db-migrations/_supabase.sql
\i /opt/supabase/db-migrations/webhooks.sql
\i /opt/supabase/db-migrations/init/data.sql
```

### Option B: Using Docker exec (if PostgreSQL is in Docker)
```bash
# Copy migration files to PostgreSQL container
docker cp /opt/supabase/db-migrations postgres_postgres:/tmp/

# Execute migrations
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/roles.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/realtime.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/jwt.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/logs.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/pooler.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/_supabase.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/webhooks.sql
docker exec -it postgres_postgres psql -U postgres -d chatwoot_database -f /tmp/init/data.sql
```

## Step 6: Deploy Supabase Stack

### The updated supabase.yml (with server paths) is ready to deploy:
```bash
# Deploy the Supabase stack
docker stack deploy -c supabase.yml supabase

# Monitor deployment
docker service ls | grep supabase
docker service logs -f supabase_vector
docker service logs -f supabase_analytics
```

## Step 7: Verification and Testing

### Check service health:
```bash
# Verify all services are running
docker service ps $(docker service ls -q --filter name=supabase)

# Test internal connectivity
docker exec $(docker ps -q -f name=supabase_kong) ping analytics
docker exec $(docker ps -q -f name=supabase_auth) nslookup postgres

# Check external access
curl -f https://supabase.yourdomain.com/health
curl -f https://studio.yourdomain.com
```

## Automation Script

### Create a deployment automation script:
```bash
#!/bin/bash
# save as: deploy-supabase-server.sh

set -e

SERVER_IP="${1:-your-server-ip}"
SERVER_USER="${2:-your-username}"

echo "🚀 Deploying Supabase to server: $SERVER_USER@$SERVER_IP"

# 1. Create server directory structure
ssh $SERVER_USER@$SERVER_IP "
sudo mkdir -p /opt/supabase/{config,db-migrations,reference}
sudo mkdir -p /opt/supabase/db-migrations/init
sudo chown -R \$(whoami):docker /opt/supabase
sudo chmod -R 755 /opt/supabase
"

# 2. Transfer files
echo "📁 Transferring configuration files..."
rsync -avz --progress supabase/docker/volumes/ $SERVER_USER@$SERVER_IP:/opt/supabase/reference/

# 3. Organize files on server
ssh $SERVER_USER@$SERVER_IP "
cp /opt/supabase/reference/api/kong.yml /opt/supabase/config/
cp /opt/supabase/reference/logs/vector.yml /opt/supabase/config/
cp /opt/supabase/reference/pooler/pooler.exs /opt/supabase/config/
cp /opt/supabase/reference/db/*.sql /opt/supabase/db-migrations/
cp /opt/supabase/reference/db/init/data.sql /opt/supabase/db-migrations/init/
"

# 4. Create Docker configs
echo "🐳 Creating Docker configs..."
ssh $SERVER_USER@$SERVER_IP "
cd /opt/supabase
docker config create supabase_kong_config config/kong.yml 2>/dev/null || echo 'Kong config already exists'
docker config create supabase_vector_config config/vector.yml 2>/dev/null || echo 'Vector config already exists'
docker config create supabase_pooler_config config/pooler.exs 2>/dev/null || echo 'Pooler config already exists'
"

# 5. Transfer and deploy supabase.yml
echo "🚢 Deploying Supabase stack..."
scp supabase.yml $SERVER_USER@$SERVER_IP:/opt/supabase/
ssh $SERVER_USER@$SERVER_IP "cd /opt/supabase && docker stack deploy -c supabase.yml supabase"

echo "✅ Deployment completed! Check service status with:"
echo "   ssh $SERVER_USER@$SERVER_IP 'docker service ls | grep supabase'"
```

### Make script executable and run:
```bash
chmod +x deploy-supabase-server.sh
./deploy-supabase-server.sh your-server-ip your-username
```

## Troubleshooting

### Common Issues:

1. **Permission Denied**
   ```bash
   sudo chown -R $(whoami):docker /opt/supabase
   sudo chmod -R 755 /opt/supabase
   ```

2. **Docker Config Already Exists**
   ```bash
   # Remove and recreate
   docker config rm supabase_kong_config
   docker config create supabase_kong_config /opt/supabase/config/kong.yml
   ```

3. **File Not Found Errors**
   ```bash
   # Verify file locations
   find /opt/supabase -name "*.yml" -o -name "*.exs"
   ```

4. **Service Connection Issues**
   ```bash
   # Check Docker network
   docker network inspect app_network
   docker service logs supabase_kong
   ```

## Security Considerations

### File Permissions:
- Config files should be readable by Docker daemon
- Avoid world-readable permissions for sensitive files
- Use Docker secrets for production credentials

### Network Security:
- Ensure firewall rules allow Docker Swarm communication
- Restrict access to /opt/supabase directory
- Use SSH keys for file transfers

---

**Next Steps**: After completing this guide, your Supabase configuration will be properly deployed on your server with all necessary files in place.