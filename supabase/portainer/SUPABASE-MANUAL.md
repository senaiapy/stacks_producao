# Supabase Self-Hosted Docker Swarm Deployment Manual

Complete production-ready guide for deploying Supabase with all fixes and troubleshooting solutions included.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Preparation](#server-preparation)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Deployment](#deployment)
6. [Post-Deployment Setup](#post-deployment-setup)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)
10. [Quick Reference](#quick-reference)

---

## 🔧 Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04+ or CentOS 7+
- **RAM**: Minimum 4GB, Recommended 8GB+
- **CPU**: 2+ cores
- **Storage**: 50GB+ SSD
- **Network**: Public IP with ports 80, 443, 8888 open

### Required Software
- Docker 20.10+
- Docker Swarm initialized
- Domain with DNS pointing to server IP

### Domain Configuration
Ensure your domain points to your server IP. Example:
- Domain: `supabase.senaia.in`
- Server IP: `217.79.184.8`

---

## 🚀 Server Preparation

### 1. Initialize Docker Swarm
```bash
# Replace with your server IP
docker swarm init --advertise-addr=YOUR_SERVER_IP

# Verify swarm status
docker node ls
```

### 2. Create Required Networks
```bash
# Create overlay networks for Traefik and internal communication
docker network create --driver=overlay traefik_public
docker network create --driver=overlay app_network

# Verify networks
docker network ls | grep overlay
```

### 3. Create Data Directories
```bash
# Create persistent data directories
mkdir -p /opt/supabase
mkdir -p /mnt/data/supabase/{api,storage,db,functions,logs}
mkdir -p /mnt/data/supabase/db/{data,init}

# Set proper permissions for PostgreSQL
chown -R 999:999 /mnt/data/supabase/db
chmod 700 /mnt/data/supabase/db/data
```

### 4. Add Node Labels
```bash
# Add required node label for service placement
docker node update --label-add node-type=primary $(docker node ls -q)
```

---

## 📦 Installation

### Method 1: Automated Installation (Recommended)

**Using Python Script:**
```bash
# Ensure Python 3 is installed
python3 --version

# Run the deployment script
python3 deploy.py
```

**Using Bash Script:**
```bash
# Make script executable
chmod +x auto-deploy.sh

# Run deployment
./auto-deploy.sh
```

### Method 2: Manual Installation

1. **Upload Files to Server**
   ```bash
   # Copy this entire folder to /opt/supabase/
   scp -r ./* root@YOUR_SERVER_IP:/opt/supabase/
   ```

2. **Setup Configuration Files**
   ```bash
   # Copy configuration files to data directories
   cp /opt/supabase/volumes/api/kong.yml /mnt/data/supabase/api/
   cp /opt/supabase/volumes/logs/vector.yml /mnt/data/supabase/logs/
   cp /opt/supabase/volumes/db/*.sql /mnt/data/supabase/db/ 2>/dev/null || true
   cp -r /opt/supabase/volumes/db/init/* /mnt/data/supabase/db/init/ 2>/dev/null || true
   ```

---

## ⚙️ Configuration

### Pre-configured Environment Variables

All environment variables are already configured in `supabase.yml`:

| Variable | Value | Purpose |
|----------|-------|---------|
| `POSTGRES_PASSWORD` | `Ma1x1x0x_testing` | PostgreSQL password |
| `JWT_SECRET` | `DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz` | JWT signing secret |
| `ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Anonymous access key |
| `SERVICE_ROLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Service role key |
| `DASHBOARD_USERNAME` | `supabase` | Studio username |
| `DASHBOARD_PASSWORD` | `Ma1x1x0x_testing` | Studio password |

### Domain Configuration

Update domains in `supabase.yml` if needed:
```bash
# Replace senaia.in with your domain
sed -i 's/senaia\.in/yourdomain.com/g' supabase.yml
```

### Security Configuration (Production)

For production deployment, update these critical values:

```bash
# Generate new passwords
NEW_DB_PASSWORD=$(openssl rand -base64 32)
NEW_JWT_SECRET=$(openssl rand -hex 32)
NEW_DASHBOARD_PASSWORD=$(openssl rand -base64 16)

# Update in supabase.yml
sed -i "s/Ma1x1x0x_testing/$NEW_DB_PASSWORD/g" supabase.yml
sed -i "s/DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz/$NEW_JWT_SECRET/g" supabase.yml
```

---

## 🚀 Deployment

### 1. Deploy the Stack
```bash
cd /opt/supabase
docker stack deploy -c supabase.yml supabase
```

### 2. Monitor Deployment
```bash
# Check service status (run every 30 seconds)
watch -n 30 'docker service ls --filter name=supabase'

# Expected services:
# - supabase_db (1/1) - PostgreSQL database
# - supabase_kong (1/1) - API Gateway
# - supabase_studio (1/1) - Web Dashboard
# - supabase_auth (1/1) - Authentication service
# - supabase_rest (1/1) - REST API
# - supabase_realtime (1/1) - Realtime subscriptions
# - supabase_storage (1/1) - File storage
# - supabase_imgproxy (1/1) - Image processing
# - supabase_meta (1/1) - Database metadata
# - supabase_vector (1/1) - Log processing
# - supabase_analytics (1/1) - Analytics
# - supabase_functions (1/1) - Edge functions
```

### 3. Wait for Full Initialization
```bash
# Services typically take 3-7 minutes to fully start
# Wait until all services show 1/1 replicas
```

---

## 🔧 Post-Deployment Setup

### 1. Database User Configuration

If authentication errors occur, fix database users:

```bash
# Connect to database
docker exec -it $(docker ps -f name=supabase_db -q) psql -U postgres

# Create/update required users
ALTER USER supabase_admin WITH PASSWORD 'Ma1x1x0x_testing';
ALTER USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x_testing';
ALTER USER supabase_storage_admin WITH PASSWORD 'Ma1x1x0x_testing';
ALTER USER supabase_read_only_user WITH PASSWORD 'Ma1x1x0x_testing';

# Create missing users if needed
CREATE USER supabase_realtime_admin WITH PASSWORD 'Ma1x1x0x_testing';
CREATE USER logflare_user WITH PASSWORD 'Ma1x1x0x_testing';

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE postgres TO supabase_admin;
GRANT ALL PRIVILEGES ON DATABASE supabase_db TO supabase_admin;
GRANT ALL PRIVILEGES ON DATABASE postgres TO supabase_realtime_admin;
GRANT ALL PRIVILEGES ON DATABASE supabase_db TO supabase_realtime_admin;
GRANT ALL PRIVILEGES ON DATABASE postgres TO logflare_user;
```

### 2. Restart Failed Services
```bash
# If any services show 0/1 replicas, restart them:
docker service update --force supabase_auth
docker service update --force supabase_studio
docker service update --force supabase_storage
docker service update --force supabase_realtime
docker service update --force supabase_analytics
```

### 3. Verify Web Access
```bash
# Test web access
curl -I https://supabase.senaia.in

# Should return HTTP 200 or redirect, not connection errors
```

---

## 📊 Monitoring & Logs

### Service Status Commands
```bash
# Check all Supabase services
docker service ls --filter name=supabase

# Check specific service details
docker service ps supabase_studio
docker service inspect supabase_kong

# Check service placement and constraints
docker service ps supabase_db --no-trunc
```

### Viewing Logs
```bash
# View logs for specific services
docker service logs -f supabase_studio
docker service logs -f supabase_kong
docker service logs -f supabase_auth

# View recent logs (last 50 lines)
docker service logs --tail 50 supabase_db

# View logs with timestamps
docker service logs -f --timestamps supabase_rest
```

### Health Checks
```bash
# Test Kong API Gateway
curl -I http://localhost:8888/

# Test database connection
docker exec $(docker ps -f name=supabase_db -q) pg_isready -U postgres

# Test internal connectivity
docker exec $(docker ps -f name=supabase_studio -q) ping db

# Test API endpoints
curl -H "apikey: YOUR_ANON_KEY" https://supabase.senaia.in/rest/v1/
```

---

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### 1. Services Show 0/1 Replicas

**Symptoms**: Services stuck at 0/1 in `docker service ls`

**Diagnosis**:
```bash
# Check service logs for errors
docker service logs supabase_SERVICE_NAME

# Check service placement
docker service ps supabase_SERVICE_NAME --no-trunc

# Check node labels
docker node inspect $(docker node ls -q) --format '{{.Spec.Labels}}'
```

**Solutions**:
```bash
# Add missing node label
docker node update --label-add node-type=primary $(docker node ls -q)

# Force restart service
docker service update --force supabase_SERVICE_NAME

# Check network connectivity
docker network ls | grep -E "(app_network|traefik_public)"
```

#### 2. Database Authentication Errors

**Symptoms**: Logs show "password authentication failed for user"

**Example Error**:
```
FATAL 28P01 (invalid_password) password authentication failed for user "supabase_admin"
```

**Solution**:
```bash
# Update database user passwords
docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c "ALTER USER supabase_admin WITH PASSWORD 'Ma1x1x0x_testing';"
docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c "ALTER USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x_testing';"

# Restart affected services
docker service update --force supabase_auth
docker service update --force supabase_analytics
```

#### 3. Kong Configuration Errors

**Symptoms**: Kong fails with YAML parsing errors

**Example Error**:
```
failed parsing declarative configuration: found character that cannot start any token
```

**Solution**:
```bash
# Check Kong configuration syntax
docker service logs supabase_kong

# Fix YAML escaping in kong.yml (passwords with special characters)
# Ensure proper quoting: password: '@450Ab6606289828supabase' (single quotes)

# Upload corrected configuration and restart
docker service update --force supabase_kong
```

#### 4. Web Access Issues

**Symptoms**: Website returns 404 or connection refused

**Diagnosis**:
```bash
# Check if Kong is running
docker service ps supabase_kong

# Test local Kong connectivity
curl -I http://localhost:8888/

# Check DNS resolution
nslookup supabase.senaia.in

# Test SSL certificate
openssl s_client -connect supabase.senaia.in:443 -servername supabase.senaia.in
```

**Solutions**:
```bash
# Ensure Kong service is running (1/1 replicas)
docker service ls --filter name=supabase_kong

# Verify domain DNS points to correct IP
dig supabase.senaia.in

# Check that ports 80/443 are open
netstat -tlpn | grep -E ":80|:443"

# Wait for all services to fully start (5-10 minutes after deployment)
```

#### 5. Edge Functions Not Working

**Symptoms**: Functions service shows errors about missing files

**Example Error**:
```
called `Result::unwrap()` on an `Err` value: Os { code: 2, kind: NotFound, message: "No such file or directory" }
```

**Solution**:
```bash
# Create functions directory structure
mkdir -p /mnt/data/supabase/functions
mkdir -p /opt/supabase/volumes/functions

# Copy example functions if available
cp -r volumes/functions/* /mnt/data/supabase/functions/ 2>/dev/null || true

# Restart functions service
docker service update --force supabase_functions
```

#### 6. Database Migration Issues

**Symptoms**: Services fail during startup with migration errors

**Solution**:
```bash
# Check database is accessible
docker exec $(docker ps -f name=supabase_db -q) pg_isready -U postgres

# Check database logs
docker service logs supabase_db

# Manually run migrations if needed
docker service update --force supabase_auth
docker service update --force supabase_realtime
```

### Advanced Troubleshooting

#### Network Connectivity Issues
```bash
# Check network configuration
docker network ls
docker network inspect app_network
docker network inspect traefik_public

# Test service-to-service connectivity
docker exec $(docker ps -f name=supabase_studio -q) ping db
docker exec $(docker ps -f name=supabase_auth -q) ping kong

# Recreate networks if needed
docker network rm app_network traefik_public
docker network create --driver=overlay app_network
docker network create --driver=overlay traefik_public
```

#### Resource Issues
```bash
# Check system resources
docker stats
free -m
df -h

# Check Docker system information
docker system df
docker system info

# Clean up if needed
docker system prune -f
```

#### Service Dependencies
```bash
# Check service startup order
# Database should start first, then Kong, then other services

# Manually control startup order if needed:
docker service scale supabase_db=1
sleep 60
docker service scale supabase_kong=1
sleep 30
docker service scale supabase_auth=1 supabase_studio=1
```

---

## 🔄 Maintenance

### Regular Maintenance Tasks

#### 1. Health Monitoring Script
```bash
#!/bin/bash
# Save as: /opt/scripts/supabase-health.sh

echo "=== Supabase Health Check $(date) ==="
docker service ls --filter name=supabase --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"

echo -e "\n=== Failed Services ==="
docker service ls --filter name=supabase --format "table {{.Name}}\t{{.Replicas}}" | grep "0/"

echo -e "\n=== Web Access Test ==="
curl -I -s https://supabase.senaia.in | head -1

echo -e "\n=== Database Connection ==="
docker exec $(docker ps -f name=supabase_db -q) pg_isready -U postgres
```

#### 2. Automated Backup Script
```bash
#!/bin/bash
# Save as: /opt/scripts/supabase-backup.sh

BACKUP_DIR="/opt/backups/supabase"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
docker exec $(docker ps -f name=supabase_db -q) pg_dump -U postgres -d supabase_db > $BACKUP_DIR/supabase_db_$DATE.sql

# Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/supabase_config_$DATE.tar.gz /opt/supabase/ /mnt/data/supabase/

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR"
```

#### 3. Log Rotation Configuration
```bash
# Configure Docker log rotation
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

# Restart Docker daemon
sudo systemctl restart docker
```

#### 4. Service Updates
```bash
# Update specific service
docker service update --image supabase/studio:latest supabase_studio

# Update entire stack (use with caution)
docker stack deploy -c supabase.yml supabase

# Rolling update with no downtime
docker service update --update-parallelism 1 --update-delay 10s supabase_studio
```

### Security Maintenance

#### 1. Update System Packages
```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y

# Restart if kernel updated
reboot
```

#### 2. Docker Security Updates
```bash
# Update Docker
curl -fsSL https://get.docker.com | sh

# Update Docker Compose
pip3 install docker-compose --upgrade
```

#### 3. SSL Certificate Monitoring
```bash
# Check certificate expiry
openssl s_client -connect supabase.senaia.in:443 -servername supabase.senaia.in 2>/dev/null | openssl x509 -noout -dates
```

---

## 📞 Quick Reference

### Access URLs
- **Supabase Studio**: https://supabase.senaia.in
- **API Endpoint**: https://supabase.senaia.in/rest/v1/
- **Auth Endpoint**: https://supabase.senaia.in/auth/v1/
- **Storage**: https://supabase.senaia.in/storage/v1/
- **Realtime**: wss://supabase.senaia.in/realtime/v1/

### Default Credentials
- **Database**: `postgres` / `Ma1x1x0x_testing`
- **Studio Dashboard**: `supabase` / `Ma1x1x0x_testing`
- **API Keys**: See kong.yml configuration

### Essential Commands
```bash
# Service management
docker service ls --filter name=supabase
docker service logs -f supabase_SERVICE_NAME
docker service update --force supabase_SERVICE_NAME
docker service scale supabase_SERVICE_NAME=0  # Stop
docker service scale supabase_SERVICE_NAME=1  # Start

# Database access
docker exec -it $(docker ps -f name=supabase_db -q) psql -U postgres

# Health checks
curl -I https://supabase.senaia.in
docker service ps supabase_kong --no-trunc

# Emergency commands
docker stack rm supabase  # Remove entire stack
docker stack deploy -c supabase.yml supabase  # Redeploy
docker system prune -f  # Cleanup
```

### Troubleshooting Checklist

**Before asking for help, verify:**
- [ ] All services show 1/1 replicas
- [ ] Networks exist (app_network, traefik_public)
- [ ] Node has proper labels (node-type=primary)
- [ ] Database users exist with correct passwords
- [ ] Domain DNS points to server IP
- [ ] Ports 80/443 are accessible
- [ ] Kong configuration is valid YAML
- [ ] Services have been running for at least 5 minutes

### File Locations
```bash
# Main configuration
/opt/supabase/supabase.yml

# Data directories
/mnt/data/supabase/api/kong.yml
/mnt/data/supabase/db/
/mnt/data/supabase/logs/

# Logs location
docker service logs supabase_SERVICE_NAME
```

---

## 📋 Deployment Checklist

**Pre-deployment:**
- [ ] Docker Swarm initialized
- [ ] Networks created (`traefik_public`, `app_network`)
- [ ] Data directories created with proper permissions
- [ ] Node labels added (`node-type=primary`)
- [ ] Domain DNS configured

**During deployment:**
- [ ] Files uploaded to `/opt/supabase/`
- [ ] Configuration files copied to data directories
- [ ] Stack deployed successfully
- [ ] All services monitored until 1/1 replicas

**Post-deployment:**
- [ ] All services showing 1/1 replicas
- [ ] Database users created/updated
- [ ] Web access working (https://supabase.senaia.in)
- [ ] API endpoints responding
- [ ] SSL certificates valid
- [ ] Backup procedures configured

---

## 🆘 Emergency Procedures

### Complete Service Recovery
```bash
# 1. Stop all services
docker stack rm supabase

# 2. Wait for cleanup
sleep 30

# 3. Verify networks still exist
docker network ls | grep -E "(app_network|traefik_public)"

# 4. Recreate networks if missing
docker network create --driver=overlay app_network
docker network create --driver=overlay traefik_public

# 5. Redeploy stack
docker stack deploy -c supabase.yml supabase

# 6. Monitor recovery
watch -n 10 'docker service ls --filter name=supabase'
```

### Database Recovery
```bash
# 1. Stop all services except database
docker service scale supabase_auth=0 supabase_studio=0 supabase_storage=0

# 2. Create database backup
docker exec $(docker ps -f name=supabase_db -q) pg_dump -U postgres -d supabase_db > emergency_backup.sql

# 3. Fix database issues
docker exec -it $(docker ps -f name=supabase_db -q) psql -U postgres

# 4. Restart services
docker service scale supabase_auth=1 supabase_studio=1 supabase_storage=1
```

---

*Generated with Claude Code 🤖*
*Last Updated: September 2025*
*Supabase Version: v2.151.0*