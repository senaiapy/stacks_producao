# Supabase Docker Swarm Migration Manual

## Overview

This manual provides comprehensive instructions for migrating Supabase from Docker Compose to Docker Swarm mode, including all necessary configuration steps, volume management, and operational procedures.

## Prerequisites

- Docker Swarm initialized
- External PostgreSQL stack running (postgres.yml)
- Networks created: `app_network`, `traefik_public`
- Traefik v3 reverse proxy deployed

## 🔧 Pre-Migration Setup

### 1. Deploy Configuration Files to Server

**IMPORTANT**: The Supabase configuration files need to be deployed to your server first.

#### 🚀 Automated Deployment (Recommended)

Use the Python deployment script for complete automation:

```bash
# Make script executable
chmod +x deploy_ssh.py

# Deploy to your server (replace with your credentials)
python3 deploy_ssh.py
# Script will prompt for: SERVER_IP, USERNAME, PASSWORD
```

**What the script does:**
- ✅ Creates server directory structure at `/opt/supabase/`
- ✅ Transfers all configuration files (kong.yml, vector.yml, pooler.exs)
- ✅ Transfers database migration files
- ✅ Creates Docker configs automatically
- ✅ Deploys the Supabase stack
- ✅ Verifies deployment

#### 📋 Manual Deployment (Alternative)

👉 **See: `SUPABASE-SERVER-DEPLOYMENT-GUIDE.md`** for detailed manual deployment steps.

```bash
# Quick manual setup on your server
sudo mkdir -p /opt/supabase/{config,db-migrations,reference}
sudo chown -R $(whoami):docker /opt/supabase

# Transfer files from local machine to server
scp supabase/docker/volumes/api/kong.yml your-user@your-server:/opt/supabase/config/
scp supabase/docker/volumes/logs/vector.yml your-user@your-server:/opt/supabase/config/
scp supabase/docker/volumes/pooler/pooler.exs your-user@your-server:/opt/supabase/config/

# Create Docker configs
docker config create supabase_kong_config /opt/supabase/config/kong.yml
docker config create supabase_vector_config /opt/supabase/config/vector.yml
docker config create supabase_pooler_config /opt/supabase/config/pooler.exs
```

### 2. Setup External Database (CRITICAL)

**🚨 IMPORTANT**: This step is REQUIRED for Supabase services to work properly.

#### 🚀 Automated Database Setup (Recommended)

Use the Python database fix script:

```bash
# Execute automated database setup
chmod +x fix_supabase_db_v2.py
python3 fix_supabase_db_v2.py
```

#### 📋 Manual Database Setup

**Connect to your PostgreSQL instance:**

```bash
# Option 1: Connect directly to PostgreSQL container
docker exec -it $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database

# Option 2: From PostgreSQL service
psql -U chatwoot_database -d chatwoot_database
```

**Execute these SQL commands:**

```sql
  psql -U chatwoot_database -d chatwoot_database
-- Create required Supabase users
CREATE USER supabase_auth_admin WITH LOGIN  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_storage_admin  LOGIN  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_functions_admin WITH LOGIN  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER authenticator WITH LOGIN  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER pgbouncer  LOGIN  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_admin WITH LOGIN  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';

-- Grant database permissions
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_storage_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_functions_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO authenticator;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_admin;

-- Create required schemas
CREATE SCHEMA IF NOT EXISTS _realtime;
CREATE SCHEMA IF NOT EXISTS _analytics;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS graphql_public;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS extensions;

-- Grant schema permissions
GRANT ALL ON SCHEMA _realtime TO supabase_auth_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_auth_admin;
GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
GRANT ALL ON SCHEMA extensions TO supabase_admin;
GRANT ALL ON SCHEMA graphql_public TO supabase_admin;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Note: pgjwt extension requires manual installation, skip if not available
-- CREATE EXTENSION IF NOT EXISTS pgjwt;

-- Create basic realtime table
CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);

SELECT 'Supabase database setup completed successfully!' as result;
```

**Verify setup:**

```sql
-- Check users exist
SELECT usename FROM pg_user WHERE usename LIKE 'supabase%';

-- Check schemas exist
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('_realtime', 'storage', 'auth', '_analytics');
```

### 3. Initialize Required Volumes

```bash
# Create named volumes for persistent data
docker volume create supabase_storage
docker volume create supabase_functions
docker volume create supabase_vector_config
```

## 📋 Environment Variables

### Critical Variables to Verify in Production

The following environment variables are hardcoded in the current `supabase.yml` but should be updated for production:

**Security Keys (CHANGE THESE):**
```bash
POSTGRES_PASSWORD=Ma1x1x0x!!Ma1x1x0x!!
JWT_SECRET=DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
SECRET_KEY_BASE=UpNVntn3cDxHJpq99YMc1T1AQgQpc8kfYTuRgBiYa15BLrx8etQoXz3gZv1/u2oq
VAULT_ENC_KEY=DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
```

**API Keys (CHANGE THESE):**
```bash
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI
```

**Logflare Keys (CHANGE THESE):**
```bash
LOGFLARE_PUBLIC_ACCESS_TOKEN=7a5f8b3c9d2e1f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9
LOGFLARE_PRIVATE_ACCESS_TOKEN=7a5f8b3c9d2e1f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9
```

**Domain Configuration:**
```bash
# Update these domains to match your setup
SUPABASE_PUBLIC_URL=https://supabase.senaia.in
API_EXTERNAL_URL=https://supabase.senaia.in
```

## 🚀 Deployment Sequence

### Phase 1: Pre-Deployment (Required)

**1. Run automated deployment:**
```bash
# Complete deployment with Python script
python3 deploy_ssh.py
```

**2. Setup database (if not done automatically):**
```bash
# Fix database configuration
python3 fix_supabase_db_v2.py
```

### Phase 2: Manual Deployment (Alternative)

**1. Deploy services:**
```bash
# Deploy Supabase stack
docker stack deploy -c supabase.yml supabase

# Wait for services to start
sleep 30
```

**2. Monitor initial startup:**
```bash
# Check service status
docker service ls | grep supabase

# Check for errors in key services
docker service logs supabase_auth
docker service logs supabase_storage
docker service logs supabase_realtime
```

### Phase 3: Fix Common Issues

**If services fail with database authentication errors:**

```bash
# 1. Create missing users and schemas
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS _realtime;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS storage;"

# 2. Restart affected services
docker service update --force supabase_auth
docker service update --force supabase_storage
docker service update --force supabase_realtime
```

### Phase 4: Verification

```bash
# Check all services are running
docker service ps $(docker service ls -q --filter name=supabase)

# Check service health
docker service ls | grep supabase

# Test key service endpoints
curl -f http://localhost:9001/health  # Vector
curl -f http://localhost:4000/health  # Analytics (may take time)
```

## 🗃️ Volume Management

### Persistent Data Locations

1. **supabase_storage**: `/var/lib/storage` - File uploads and static assets
2. **supabase_functions**: `/home/deno/functions` - Edge function code
3. **supabase_vector_config**: `/etc/vector` - Log collection configuration

### Backup Strategy

```bash
# Backup storage volume
docker run --rm -v supabase_storage:/source -v $(pwd):/backup alpine tar czf /backup/supabase_storage_$(date +%Y%m%d).tar.gz -C /source .

# Backup functions volume
docker run --rm -v supabase_functions:/source -v $(pwd):/backup alpine tar czf /backup/supabase_functions_$(date +%Y%m%d).tar.gz -C /source .

# Backup vector config
docker run --rm -v supabase_vector_config:/source -v $(pwd):/backup alpine tar czf /backup/supabase_vector_$(date +%Y%m%d).tar.gz -C /source .
```

### Restore Procedure

```bash
# Restore storage volume
docker run --rm -v supabase_storage:/target -v $(pwd):/backup alpine tar xzf /backup/supabase_storage_YYYYMMDD.tar.gz -C /target

# Restore functions volume
docker run --rm -v supabase_functions:/target -v $(pwd):/backup alpine tar xzf /backup/supabase_functions_YYYYMMDD.tar.gz -C /target

# Restore vector config
docker run --rm -v supabase_vector_config:/target -v $(pwd):/backup alpine tar xzf /backup/supabase_vector_YYYYMMDD.tar.gz -C /target
```

## 🔄 Database Migrations

### 🚀 Automated Migration (Recommended)

The Python deployment script automatically handles migrations:

```bash
# Complete migration with automation
python3 deploy_ssh.py
# This script:
# ✅ Transfers all migration files to /opt/supabase/db-migrations/
# ✅ Creates required database users and schemas
# ✅ Executes migration scripts
# ✅ Verifies setup
```

### 📋 Manual Migration Process

**Required Database Setup Scripts:**

1. **roles.sql** - Creates required database users
2. **realtime.sql** - Sets up realtime schema
3. **jwt.sql** - Configures JWT settings
4. **logs.sql** - Sets up logging schema
5. **pooler.sql** - Configures connection pooling
6. **_supabase.sql** - Internal Supabase schemas

**Migration Commands:**

```bash
# On your server, copy files to PostgreSQL container
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker cp /opt/supabase/db-migrations/*.sql $POSTGRES_CONTAINER:/tmp/

# Execute migrations
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/roles.sql
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/realtime.sql
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/jwt.sql
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/logs.sql
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/pooler.sql
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -f /tmp/_supabase.sql
```

**Alternative - Direct PostgreSQL connection:**

```bash
# Connect to PostgreSQL and run migrations
psql -U chatwoot_database -d chatwoot_database
\i /opt/supabase/db-migrations/roles.sql
\i /opt/supabase/db-migrations/realtime.sql
\i /opt/supabase/db-migrations/jwt.sql
\i /opt/supabase/db-migrations/logs.sql
\i /opt/supabase/db-migrations/pooler.sql
\i /opt/supabase/db-migrations/_supabase.sql
```

### ✅ Migration Verification

```sql
-- Verify required schemas exist
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('_realtime', '_analytics', 'storage', 'graphql_public', 'auth');

-- Verify required users exist
SELECT usename FROM pg_user
WHERE usename IN ('authenticator', 'pgbouncer', 'supabase_auth_admin', 'supabase_storage_admin', 'supabase_admin');

-- Verify extensions (pgjwt is optional)
SELECT extname FROM pg_extension
WHERE extname IN ('vector', 'pg_stat_statements', 'pgcrypto');

-- Check if pgjwt is available (optional)
SELECT CASE
    WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgjwt')
    THEN 'pgjwt extension is installed'
    ELSE 'pgjwt extension not available (this is OK for basic functionality)'
END as pgjwt_status;

-- Test user connections
-- This should work without errors:
SELECT current_user;
```

### 🛠️ Migration Troubleshooting

**If migrations fail:**

```bash
# Check PostgreSQL container logs
docker logs $(docker ps -q -f name=postgres)

# Verify file permissions
ls -la /opt/supabase/db-migrations/

# Test PostgreSQL connectivity
docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c "SELECT 1;"

# Re-run specific migration
docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -f /tmp/roles.sql
```

## 🔧 Configuration Updates for Swarm

### Key Changes from Docker Compose

1. **Removed `depends_on`**: Docker Swarm doesn't support conditional dependencies
2. **Added external configs**: Kong, Vector, and Pooler configurations
3. **Updated network labels**: Changed `traefik.swarm.network` to `traefik.docker.network`
4. **Service discovery**: All internal communications use service names
5. **Proper hostname templates**: Using `{{.Service.Name}}.{{.Task.Slot}}`

### Health Check Adjustments

- Vector: `http://localhost:9001/health`
- Analytics: `http://localhost:4000/health`
- Storage: `http://localhost:5000/status`
- Auth: `http://localhost:9999/health`
- Meta: No health check (lightweight service)

## 🚦 Operational Procedures

### Service Management

```bash
# Scale a service
docker service scale supabase_studio=2

# Update service image
docker service update --image supabase/studio:latest supabase_studio

# Rolling restart
docker service update --force supabase_auth

# View service logs
docker service logs -f supabase_kong

# Check service status
docker service ps supabase_storage
```

### Network Troubleshooting

```bash
# Test internal connectivity
docker exec $(docker ps -q -f name=supabase_kong) ping analytics
docker exec $(docker ps -q -f name=supabase_auth) nslookup postgres

# Check network configuration
docker network inspect app_network
docker network inspect traefik_public
```

### Health Monitoring

```bash
# Check all service health
for service in $(docker service ls --format "{{.Name}}" | grep supabase); do
  echo "=== $service ==="
  docker service ps $service
done

# Monitor resource usage
docker stats $(docker ps -q -f name=supabase)
```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Changed all default passwords and keys
- [ ] Generated new JWT secrets with proper length
- [ ] Updated domain configurations
- [ ] Configured proper SMTP settings
- [ ] Set up SSL certificates via Traefik
- [ ] Restricted database access to required users only
- [ ] Enabled proper firewall rules
- [ ] Configured log rotation and retention

### Network Security

- Services communicate via overlay networks only
- External access only through Traefik reverse proxy
- Database connections are internal to the swarm
- No direct external database exposure

## 🚨 Troubleshooting

### 🔴 Critical Database Authentication Errors

**Error:** `FATAL: password authentication failed for user "supabase_auth_admin"`

**Cause:** Missing Supabase users in PostgreSQL database

**Solution:**
```bash
# Quick fix - create missing users
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE USER supabase_storage_admin WITH PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';"

# Restart affected services
docker service update --force supabase_auth
docker service update --force supabase_storage
```

**Automated fix:**
```bash
python3 fix_supabase_db_v2.py
```

### 🔴 Schema Migration Errors

**Error:** `ERROR 3F000 (invalid_schema_name) no schema has been selected to create in`

**Cause:** Missing required schemas (_realtime, storage, auth)

**Solution:**
```bash
# Create missing schemas
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS _realtime;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS storage;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE SCHEMA IF NOT EXISTS auth;"

# Restart realtime service
docker service update --force supabase_realtime
```

### 🔴 Edge Functions Boot Error

**Error:** `worker boot error: failed to bootstrap runtime: could not find an appropriate entrypoint`

**Cause:** Missing function entrypoint configuration

**Solution:**
```bash
# Restart functions service
docker service update --force supabase_functions

# Check if functions volume exists
docker volume ls | grep functions

# If missing, create volume
docker volume create supabase_functions
```

### 🔴 pgjwt Extension Error

**Error:** `extension "pgjwt" is not available`

**Cause:** pgjwt extension not installed in PostgreSQL container

**Quick Fix (Skip pgjwt):**
```sql
-- Connect to database and skip pgjwt extension
psql -U chatwoot_database -d chatwoot_database
-- Run all other extensions except pgjwt:
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Skip: CREATE EXTENSION IF NOT EXISTS pgjwt;
```

**Complete Fix (Install pgjwt):**
```bash
# Run automated pgjwt fix
python3 fix_pgjwt_extension.py
```

**Manual pgjwt Installation:**
```bash
# Install in PostgreSQL container
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker exec $POSTGRES_CONTAINER apt-get update
docker exec $POSTGRES_CONTAINER apt-get install -y git build-essential postgresql-server-dev-16
docker exec $POSTGRES_CONTAINER git clone https://github.com/michelp/pgjwt.git /tmp/pgjwt
docker exec $POSTGRES_CONTAINER sh -c "cd /tmp/pgjwt && make && make install"

# Try to create extension
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "CREATE EXTENSION IF NOT EXISTS pgjwt;"
```

**Note:** Supabase can work without pgjwt for basic functionality. JWT operations may be limited.

### 🔧 Common Issues

1. **Kong fails to start**
   - Verify kong config exists: `docker config ls | grep kong`
   - Check config syntax: validate kong.yml format
   - **Fix:** `docker config create supabase_kong_config /opt/supabase/config/kong.yml`

2. **Vector logs errors**
   - Verify Docker socket access: `/var/run/docker.sock`
   - Check Logflare connectivity to analytics service
   - **Fix:** Restart vector service: `docker service update --force supabase_vector`

3. **Storage service fails**
   - Verify supabase_storage volume exists
   - Check imgproxy service health
   - **Fix:** Create volume: `docker volume create supabase_storage`

4. **Auth service connection errors**
   - Verify PostgreSQL connectivity
   - Check database users and permissions
   - **Fix:** Run database setup: `python3 fix_supabase_db_v2.py`

5. **Studio interface not accessible**
   - Check Traefik labels and routing
   - Verify meta service is running
   - **Fix:** `docker service update --force supabase_studio`

### 📊 Service Health Check Commands

```bash
# Check all Supabase services
docker service ls | grep supabase

# Check service logs for errors
docker service logs supabase_auth 2>&1 | grep -i error
docker service logs supabase_storage 2>&1 | grep -i error
docker service logs supabase_realtime 2>&1 | grep -i error

# Check database connectivity
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT 1;"

# List database users
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT usename FROM pg_user;"

# List schemas
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "SELECT schema_name FROM information_schema.schemata;"
```

### Debug Commands

```bash
# Check service details
docker service inspect supabase_kong

# View container logs
docker logs $(docker ps -q -f name=supabase_auth)

# Test service connectivity
docker exec -it $(docker ps -q -f name=supabase_studio) wget -O- http://meta:8080

# Validate configurations
docker config inspect supabase_kong_config
```

## 📊 Monitoring and Logging

### Log Collection

All services send logs to the analytics service via Vector. Log sources include:
- Kong: API gateway logs
- Auth: GoTrue authentication logs
- Rest: PostgREST API logs
- Realtime: WebSocket connection logs
- Storage: File operation logs
- Functions: Edge function execution logs

### Metrics Access

- Analytics dashboard: `https://studio.senaia.in`
- Vector health endpoint: `http://vector:9001/health`
- Individual service logs: `docker service logs -f <service_name>`

## 🔄 Update Procedures

### Rolling Updates

```bash
# Update specific service
docker service update --image supabase/studio:latest supabase_studio

# Update all services (use with caution)
docker stack deploy -c supabase.yml supabase
```

### Configuration Updates

```bash
# Update external config
docker config rm supabase_kong_config
docker config create supabase_kong_config supabase/docker/volumes/api/kong.yml

# Force service restart to use new config
docker service update --force supabase_kong
```

## 🛠️ Deployment Scripts Reference

### Available Python Scripts

1. **`deploy_ssh.py`** - Complete automated deployment
   ```bash
   python3 deploy_ssh.py
   # Handles: file transfer, config creation, stack deployment
   ```

2. **`fix_supabase_db_v2.py`** - Database setup and error fixes
   ```bash
   python3 fix_supabase_db_v2.py
   # Handles: user creation, schema setup, service restart
   ```

3. **`simple_db_fix.py`** - Simple database fixes
   ```bash
   python3 simple_db_fix.py
   # Handles: basic user/schema creation
   ```

4. **`fix_pgjwt_extension.py`** - Fix pgjwt extension issues
   ```bash
   python3 fix_pgjwt_extension.py
   # Handles: pgjwt installation, alternative JWT functions
   ```

### Manual Deployment Files

- **`MANUAL-DEPLOYMENT-STEPS.md`** - Step-by-step manual instructions
- **`SUPABASE-ERRORS-ANALYSIS.md`** - Complete error analysis and solutions
- **`deploy-supabase-server.sh`** - Bash deployment script (requires SSH keys)

## 📚 Additional Resources

- [Supabase Self-Hosting Guide](https://supabase.com/docs/guides/self-hosting)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [Traefik v3 Configuration](https://doc.traefik.io/traefik/)
- **Local Documentation:**
  - `SUPABASE-SERVER-DEPLOYMENT-GUIDE.md`
  - `PORT-CONFLICT-ANALYSIS.md`
  - `SUPABASE-ERRORS-ANALYSIS.md`

## ⚠️ Important Notes

1. **Database Dependency**: This setup requires an external PostgreSQL database running separately
2. **Required Database Setup**: Supabase users and schemas MUST be created before services will work
3. **Persistent Storage**: Ensure volume backups are configured before production deployment
4. **Security**: All default credentials must be changed for production use
5. **Monitoring**: Set up proper monitoring and alerting for all services
6. **SSL**: Traefik handles SSL termination - ensure certificates are properly configured
7. **Python Scripts**: Use provided Python scripts for reliable deployment automation

## 🎯 Quick Success Checklist

- [ ] PostgreSQL database running and accessible
- [ ] Database users created (supabase_auth_admin, supabase_storage_admin, etc.)
- [ ] Required schemas created (_realtime, storage, auth)
- [ ] Configuration files deployed to `/opt/supabase/config/`
- [ ] Docker configs created (kong, vector, pooler)
- [ ] Supabase stack deployed successfully
- [ ] All services running without authentication errors
- [ ] External domains accessible through Traefik

---

**Last Updated**: September 2025
**Version**: 2.0 (Updated with Python scripts and error fixes)
**Author**: Claude Code Assistant