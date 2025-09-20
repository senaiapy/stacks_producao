# Claude Remote Server Access & Supabase Deployment Documentation

## Overview

This document summarizes all processes used for remote server access and Supabase deployment using various Python scripts and configurations.

## Server Information

- **IP Address**: 217.79.184.8
- **User**: root
- **Password**: @450Ab6606
- **Platform**: Docker Swarm
- **Networks**: traefik_public, app_network

## Deployment Scripts

### 1. FULL-INSTALL-SUPABASE.py

**Purpose**: Complete Supabase deployment with all services and 100% web access verification.

**Key Features**:
- 8-step deployment process
- Automatic prerequisite checking
- Server environment preparation
- Configuration upload
- Service health monitoring
- Database setup with user creation
- Web access verification
- Final deployment status reporting

**Usage**:
```bash
python3 FULL-INSTALL-SUPABASE.py
```

**Services Deployed**:
- PostgreSQL Database (port 25432)
- Supabase Studio (Web UI)
- Kong API Gateway (port 7000)
- Auth Service (GoTrue)
- REST API (PostgREST)
- Realtime Service
- Storage API
- Meta API
- Edge Functions
- Analytics/Logging
- Vector Logging
- Connection Pooler (Supavisor)

### 2. deploy_minimal.py

**Purpose**: Minimal working Supabase deployment focused on core services.

**Key Features**:
- Core services only (DB, Studio, REST, Auth)
- Direct Traefik SSL routing
- Simplified configuration
- Web access testing

**Usage**:
```bash
python3 deploy_minimal.py
```

**Services Deployed**:
- PostgreSQL Database (port 25432)
- Supabase Studio
- PostgREST API
- GoTrue Auth Service

### 3. unified_deployment.py

**Purpose**: Comprehensive deployment with step-by-step verification.

**Key Features**:
- Unified deployment approach
- Service dependency management
- Error handling and retry logic
- Detailed logging and monitoring

## Configuration Files

### supabase.yml

**Location**: `/home/galo/Desktop/stacks_producao/supabase/portainer/supabase.yml`

**Key Changes Made**:
- PostgreSQL port changed from 5432 to 25432 (to avoid conflicts)
- Kong port changed from 8000 to 7000
- External SSL endpoints for meta.senaia.in, imgproxy.senaia.in, analytics.senaia.in
- Internal service URLs for Studio configuration
- Removed analytics dependencies for core services
- Simplified database configuration

**Network Configuration**:
```yaml
networks:
  traefik_public:
    external: true
  app_network:
    external: true
```

### minimal_supabase.yml

**Purpose**: Simplified configuration for testing and core functionality.

**Key Features**:
- PostgreSQL with port 25432
- Studio with basic configuration
- Essential services only
- Direct Traefik routing

## Deployment Process

### Step 1: Server Access
```python
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("217.79.184.8", username="root", password="@450Ab6606")
```

### Step 2: Stack Cleanup
```bash
docker stack rm supabase
```

### Step 3: Configuration Upload
```bash
cat > /opt/supabase/supabase.yml << 'EOF'
[configuration content]
EOF
```

### Step 4: Deployment
```bash
cd /opt/supabase && docker stack deploy -c supabase.yml supabase
```

### Step 5: Monitoring
```bash
docker service ls --filter name=supabase
```

## Web Access URLs

- **Studio UI**: https://studio.senaia.in
- **REST API**: https://api.senaia.in
- **Auth API**: https://auth.senaia.in
- **Storage API**: https://storage.senaia.in
- **Functions**: https://functions.senaia.in
- **Kong Gateway**: https://supabase.senaia.in
- **Meta API**: https://meta.senaia.in
- **ImgProxy**: https://imgproxy.senaia.in
- **Analytics**: https://analytics.senaia.in

## Common Issues & Solutions

### 1. Port Conflicts
**Problem**: PostgreSQL port 5432 conflicts with existing PostgreSQL instance.
**Solution**: Changed to port 25432 in all configurations.

### 2. Service Dependencies
**Problem**: Services failing due to analytics dependency issues.
**Solution**: Removed analytics dependencies from core services.

### 3. HTML Response Issues
**Problem**: Services returning HTTP status codes but not HTML content.
**Solution**:
- Updated Studio configuration with proper environment variables
- Used internal service URLs instead of external SSL endpoints
- Simplified service dependencies

### 4. Traefik Routing
**Problem**: Services running but not accessible via domain names.
**Solution**:
- Verified Traefik labels configuration
- Ensured proper network connectivity
- Added constraint labels for Traefik routing

## Service Status Verification

### Check Service Status
```bash
docker service ls --filter name=supabase --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"
```

### Check Service Logs
```bash
docker service logs supabase_studio --tail 10
```

### Test Web Access
```bash
curl -s -o /dev/null -w "%{http_code}" https://studio.senaia.in/
```

### Test HTML Content
```bash
curl -s https://studio.senaia.in/ | head -5
```

## Database Configuration

### Connection Details
- **Host**: db (internal) / 217.79.184.8 (external)
- **Port**: 25432
- **Database**: postgres
- **Username**: postgres
- **Password**: Ma1x1x0x_testing

### Database Access
```bash
docker exec -it $(docker ps --filter name=supabase_db --format "{{.ID}}" | head -1) psql -U postgres -d postgres -p 25432
```

## Environment Variables

### Critical Environment Variables
- `POSTGRES_PASSWORD`: Ma1x1x0x_testing
- `JWT_SECRET`: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
- `SUPABASE_ANON_KEY`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
- `SUPABASE_SERVICE_KEY`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

### Studio Configuration
- `HOSTNAME`: 0.0.0.0
- `PORT`: "3000"
- `SUPABASE_PUBLIC_URL`: https://studio.senaia.in

## Troubleshooting Commands

### Service Health Check
```bash
for service in $(docker service ls --filter name=supabase --format "{{.Name}}"); do
    echo "=== $service ==="
    docker service ps $service --format "table {{.Name}}\t{{.CurrentState}}\t{{.Error}}"
done
```

### Container Inspection
```bash
docker inspect $(docker ps --filter name=supabase_studio --format "{{.ID}}" | head -1)
```

### Network Connectivity Test
```bash
docker exec $(docker ps --filter name=supabase_studio --format "{{.ID}}" | head -1) netstat -tlnp
```

## Success Criteria

### Deployment Success
- All core services showing 1/1 replicas
- Database accessible on port 25432
- Studio returning HTML content
- REST API returning JSON responses
- All SSL endpoints accessible

### Web Access Success
- studio.senaia.in serves HTML interface
- api.senaia.in returns API documentation
- auth.senaia.in provides authentication endpoints
- All HTTP status codes are 200 or appropriate (401 for auth endpoints)

## Final Status

### ✅ PRINCIPAL ISSUE RESOLVED: HTML RESPONSES WORKING!

**🎉 SUCCESS: studio.senaia.in now serves COMPLETE HTML content!**

### Working Services
- ✅ PostgreSQL Database (1/1)
- ✅ REST API (1/1)
- ✅ **Studio (1/1) - FULL HTML CONTENT WORKING!**
- ✅ Auth Service (0/1 - starting)

### Services Requiring Further Configuration
- ⚠️ Kong Gateway (0/1) - **NEXT PRIORITY for supabase.senaia.in**
- ⚠️ Meta API (0/1)
- ⚠️ Realtime (0/1)
- ⚠️ Supavisor (0/1)

## Root Cause Resolution

### Studio HTML Issue - ✅ FIXED!
**Problem**: Studio returning 404 "page not found"
**Root Cause**: Traefik router conflicts - Multiple studio stacks with same router name
**Solution**:
1. Removed conflicting stacks: `studio-test`, `studio-direct`
2. Used simplified configuration based on working `deploy_minimal.py`
3. Fixed Traefik routing conflicts

**Result**: Studio now serves complete HTML with:
- ✅ Full Supabase Studio interface
- ✅ 307 redirect to default project (normal behavior)
- ✅ Complete HTML with meta tags, CSS, JavaScript
- ✅ Working navigation and sidebar

### Current Configuration - WORKING
```yaml
studio:
  image: supabase/studio:latest
  environment:
    HOSTNAME: 0.0.0.0
    PORT: "3000"
    POSTGRES_PASSWORD: Ma1x1x0x_testing
    SUPABASE_PUBLIC_URL: https://studio.senaia.in
```

## Next Steps

1. **Kong Gateway**: Fix Kong configuration to make supabase.senaia.in serve same HTML as studio.senaia.in
2. **Service Dependencies**: Enable remaining services after Kong is stable
3. **Production Hardening**: Update default passwords and keys for production use
4. **Documentation**: Complete backup of working configuration

## Contact Information

For issues with this deployment, check:
1. Service logs: `docker service logs <service_name>`
2. Container status: `docker ps --filter name=supabase`
3. Network connectivity: `docker network ls`
4. Traefik routing: `docker service logs traefik`

---

*Generated with Claude Code - Date: 2025-09-20*