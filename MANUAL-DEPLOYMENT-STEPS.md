# Manual Deployment Steps for Server 217.79.184.8

## Prerequisites
- SSH access to server 217.79.184.8 as root
- Password: @450Ab6606

## Step 1: Connect to Your Server
```bash
ssh root@217.79.184.8
# Enter password: @450Ab6606
```

## Step 2: Create Directory Structure on Server
```bash
# Create main Supabase configuration directory
sudo mkdir -p /opt/supabase/{config,db-migrations,reference,scripts}
sudo mkdir -p /opt/supabase/db-migrations/init
sudo mkdir -p /opt/supabase/reference/{api,logs,pooler,db,authelia}

# Set appropriate permissions
sudo chown -R $(whoami):docker /opt/supabase 2>/dev/null || sudo chown -R $(whoami):$(whoami) /opt/supabase
sudo chmod -R 755 /opt/supabase

echo "Directory structure created successfully"
```

## Step 3: Transfer Configuration Files from Local Machine

### On your LOCAL machine (run these commands):

#### Transfer Kong configuration:
```bash
scp supabase/docker/volumes/api/kong.yml root@217.79.184.8:/opt/supabase/config/
```

#### Transfer Vector configuration:
```bash
scp supabase/docker/volumes/logs/vector.yml root@217.79.184.8:/opt/supabase/config/
```

#### Transfer Pooler configuration:
```bash
scp supabase/docker/volumes/pooler/pooler.exs root@217.79.184.8:/opt/supabase/config/
```

#### Transfer database migration files:
```bash
scp supabase/docker/volumes/db/*.sql root@217.79.184.8:/opt/supabase/db-migrations/
scp supabase/docker/volumes/db/init/data.sql root@217.79.184.8:/opt/supabase/db-migrations/init/
```

#### Transfer supabase.yml stack file:
```bash
scp supabase.yml root@217.79.184.8:/opt/supabase/
```

## Step 4: Verify Files on Server
```bash
# Check core config files
ls -la /opt/supabase/config/
# Should show: kong.yml, vector.yml, pooler.exs

# Check database migration files
ls -la /opt/supabase/db-migrations/
# Should show: *.sql files

# Check stack file
ls -la /opt/supabase/supabase.yml
```

## Step 5: Initialize Docker Swarm (if not already done)
```bash
# Check if Docker Swarm is active
docker info | grep -i swarm

# If not active, initialize it
docker swarm init

# Create required networks (if they don't exist)
docker network create --driver=overlay app_network 2>/dev/null || echo "app_network already exists"
docker network create --driver=overlay traefik_public 2>/dev/null || echo "traefik_public already exists"
```

## Step 6: Create Docker Configs
```bash
cd /opt/supabase

# Remove existing configs (if any)
docker config rm supabase_kong_config 2>/dev/null || true
docker config rm supabase_vector_config 2>/dev/null || true
docker config rm supabase_pooler_config 2>/dev/null || true

# Create new Docker configs
docker config create supabase_kong_config config/kong.yml
docker config create supabase_vector_config config/vector.yml
docker config create supabase_pooler_config config/pooler.exs

# Verify configs were created
docker config ls | grep supabase
```

## Step 7: Run Database Migrations (if needed)
```bash
# If you have a PostgreSQL service running, execute migrations:
# docker exec -it POSTGRES_CONTAINER psql -U postgres -d your_database

# Example migration commands:
# \i /opt/supabase/db-migrations/roles.sql
# \i /opt/supabase/db-migrations/realtime.sql
# \i /opt/supabase/db-migrations/jwt.sql
# \i /opt/supabase/db-migrations/logs.sql
# \i /opt/supabase/db-migrations/pooler.sql
# \i /opt/supabase/db-migrations/_supabase.sql
```

## Step 8: Deploy Supabase Stack
```bash
cd /opt/supabase

# Deploy the Supabase stack
docker stack deploy -c supabase.yml supabase

# Monitor deployment
docker service ls | grep supabase
```

## Step 9: Verify Deployment
```bash
# Check all services are running
docker service ps $(docker service ls -q --filter name=supabase)

# Check service logs
docker service logs -f supabase_vector
docker service logs -f supabase_analytics

# Check health endpoints (when services are ready)
curl -f http://localhost:9001/health  # Vector
curl -f http://localhost:4000/health  # Analytics
```

## Step 10: Access Services
Once deployed, your services will be available at:
- **Supabase API**: https://supabase.senaia.in
- **Supabase Studio**: https://studio.senaia.in
- **Connection Pooler**: https://pooler.senaia.in

## Troubleshooting

### If configs fail to create:
```bash
# Check file permissions
ls -la /opt/supabase/config/

# Verify file contents
cat /opt/supabase/config/kong.yml
cat /opt/supabase/config/vector.yml
cat /opt/supabase/config/pooler.exs
```

### If services fail to start:
```bash
# Check service status
docker service ps supabase_kong
docker service ps supabase_studio

# Check logs
docker service logs supabase_kong
docker service logs supabase_auth
```

### If network issues occur:
```bash
# Check networks
docker network ls
docker network inspect app_network
docker network inspect traefik_public
```

## Security Reminders
- ⚠️ Change all default passwords and secrets for production
- ⚠️ Update domain names in supabase.yml if needed
- ⚠️ Verify SSL certificates are properly configured
- ⚠️ Ensure firewall rules are properly configured

---

**Execute these steps in order, and your Supabase stack will be deployed successfully!**