# FULL-INSTALL-SUPABASE Manual

Complete automation script for Supabase deployment with Kong DNS resolution fixes.

⚡ **LATEST ENHANCEMENTS**: Enhanced with intelligent waiting (15-min timeout), auto-restart capabilities, multi-attempt service discovery, comprehensive endpoint testing, and detailed success assessment.

## 🚀 Overview

`FULL-INSTALL-SUPABASE.py` is a comprehensive Python script that automates the entire Supabase deployment process on your remote server. It handles everything from file uploads to Kong configuration fixes, database setup, and endpoint testing.

### What It Does

✅ **Complete Infrastructure Setup**
- Creates all required directories and networks
- Sets proper permissions for PostgreSQL
- Configures Docker Swarm node labels

✅ **File Management**
- Uploads supabase.yml configuration
- Transfers entire volumes/ directory
- Creates default Kong configuration if missing

✅ **Deployment Automation**
- Deploys Supabase stack with proper detached mode
- Monitors service startup progress
- Handles network conflicts automatically

✅ **Kong DNS Resolution Fix**
- Discovers actual service IP addresses
- Creates IP-based Kong routing configuration
- Eliminates "name resolution failed" errors

✅ **Database Configuration**
- Creates all required database users
- Sets up proper passwords and permissions
- Configures schemas for analytics and realtime

✅ **Service Management**
- Restarts failed services automatically
- Creates direct Studio access as fallback
- Force-restarts critical services

✅ **Comprehensive Testing**
- Tests all API endpoints
- Validates authentication flows
- Provides detailed status reports

## 📋 Prerequisites

### Local Machine Requirements

1. **Python 3** with paramiko module:
   ```bash
   # REQUIRED: Create virtual environment (modern Python systems)
   python3 -m venv venv

   # Activate virtual environment
   source venv/bin/activate

   # Install paramiko in virtual environment
   pip install paramiko

   # Verify installation
   python3 -c "import paramiko; print('✅ Paramiko installed successfully')"
   ```

   **Note**: Modern Python distributions require virtual environments for package management. Do not use `--break-system-packages` flag.

2. **Required Files** in current directory:
   ```bash
   # Essential
   supabase.yml              # Main Docker Compose file

   # Optional but recommended
   volumes/                  # Configuration directory
   ├── api/kong.yml         # Kong configuration
   ├── db/*.sql             # Database scripts
   └── logs/vector.yml      # Log configuration
   ```

### Server Requirements

1. **Docker Swarm** initialized:
   ```bash
   docker swarm init --advertise-addr=YOUR_SERVER_IP
   ```

2. **SSH Access** enabled for root user

3. **Ports** 80, 443, 8888 open for web access

4. **Minimum Resources**: 4GB RAM, 2 CPU cores, 50GB storage

## 🎯 Usage

### Basic Usage

```bash
# Navigate to the Supabase portainer directory
cd /home/galo/Desktop/stacks_producao/supabase/portainer

# REQUIRED: Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# REQUIRED: Install dependencies
pip install paramiko

# Run the installation
python3 FULL-INSTALL-SUPABASE.py
```

### With Help Information

```bash
# View detailed help
python3 FULL-INSTALL-SUPABASE.py --help
```

## 📊 Installation Process

The script executes 12 comprehensive steps:

### Step 1: Check Prerequisites
- ✅ Verifies required local files exist
- ✅ Tests SSH connection to server
- ✅ Confirms Docker Swarm is active

### Step 2: Prepare Server Environment
- 📁 Creates all required directories
- 🔐 Sets PostgreSQL permissions
- 🌐 Creates Docker overlay networks
- 🏷️ Adds required node labels

### Step 3: Upload Configuration Files
- 📤 Uploads supabase.yml to `/opt/supabase/`
- 📤 Transfers volumes/ directory to `/mnt/data/supabase/`
- 📝 Creates default Kong config if missing

### Step 4: Deploy Supabase Stack
- 🧹 Removes existing stack if present
- 🚀 Deploys with `--detach=true` flag
- 🔄 Handles network conflicts automatically

### Step 5: Wait for Services (Enhanced)
- ⏳ Monitors service startup for up to 15 minutes
- 📊 Shows real-time progress updates every 30 seconds
- 🔄 Auto-restarts stuck services after 3 minutes
- ✅ Continues when 9+ services are healthy or after 10 minutes with 7+ core services
- 💡 Provides intelligent retry logic for failed services

### Step 6: Get Service IP Addresses (Enhanced)
- 🔍 Discovers actual container IP addresses with 5 retry attempts
- 📋 Maps service names to IPs with 30-second intervals between retries
- 💾 Stores IPs for Kong configuration
- ⚠️ Provides fallback to service names if IPs not available
- ✅ Proceeds when at least 3 services have discoverable IPs

### Step 7: Fix Kong DNS Resolution
- 🔧 Creates IP-based Kong configuration
- 📤 Uploads new Kong config
- 🔄 Reloads Kong with new settings

### Step 8: Setup Database
- ⏳ Waits for database to be ready
- 👥 Creates/updates all required users
- 🔑 Sets proper passwords and permissions
- 📊 Creates analytics and realtime schemas

### Step 9: Restart Failed Services
- 🔍 Identifies services with 0/1 replicas
- 🔄 Restarts failed services
- ⚡ Force-restarts critical services

### Step 10: Create Direct Studio Access
- 🎨 Deploys standalone Studio service
- 🌐 Accessible at https://studio.senaia.in
- 🔄 Bypasses Kong if DNS issues persist

### Step 11: Test All Endpoints (Enhanced)
- 🧪 Tests Kong main route with multiple attempts
- 🎨 Tests direct Studio access
- 🔓 Tests Auth endpoints
- 📊 Tests REST API with API key
- 💾 Tests Storage API
- 📈 Tests Meta API
- 🔄 Performs up to 3 test attempts with 1-minute intervals
- ✅ Considers 401 (Auth Required) as successful response
- 📊 Provides final endpoint success percentage

### Step 12: Final Status Report (Enhanced)
- ⏳ Final 30-second stabilization wait
- 📊 Shows comprehensive final service status with health scoring
- 🌟 Provides deployment success assessment (Excellent/Good/Partial/Incomplete)
- 🔑 Lists all access credentials and endpoints
- 🛠️ Includes troubleshooting commands and tips
- 📍 Shows discovered service IP addresses
- 📋 Provides post-deployment checklist
- 💡 Includes next steps guidance for service optimization

## ⏱️ Deployment Timing & Process

### Expected Duration
- **Total deployment time**: 15-25 minutes
- **Core services startup**: 3-5 minutes
- **Full service stabilization**: 10-15 minutes
- **Final testing and verification**: 3-5 minutes

### Service Startup Sequence
1. **Immediate (0-2 minutes)**: Database, Vector, ImgProxy
2. **Early (2-5 minutes)**: Kong, Meta, Functions, Storage
3. **Dependent (5-10 minutes)**: Auth, REST, Studio (depend on database)
4. **Analytics (5-15 minutes)**: Realtime, Analytics (complex startup requirements)

### Intelligent Waiting Features
- **Auto-restart**: Services stuck for 3+ minutes are automatically restarted
- **Progressive timeouts**: Different wait times based on service criticality
- **Smart continuation**: Proceeds when core services are healthy
- **Retry logic**: Multiple attempts for IP discovery and endpoint testing

## 📈 Expected Output

### Successful Installation

```
================================================================================
🚀 SUPABASE FULL INSTALLATION STARTING
================================================================================
🎯 Target Server: 217.79.184.8
👤 User: root
📁 Local Directory: /home/galo/Desktop/stacks_producao/supabase/portainer

🔄 Executing Step 1/12: Check Prerequisites
📋 STEP 1: CHECK PREREQUISITES
✅ Required local files found
✅ SSH connection established to 217.79.184.8
✅ Docker Swarm is active

🔄 Executing Step 2/12: Prepare Server Environment
📋 STEP 2: PREPARE SERVER ENVIRONMENT
📁 Creating server directories...
  ✅ /opt/supabase
  ✅ /mnt/data/supabase/api
  [... more directories ...]
🔐 Setting PostgreSQL permissions...
🌐 Setting up Docker networks...
  ✅ app_network exists
  ✅ traefik_public exists
🏷️ Setting node labels...
✅ Server environment prepared

[... continues through all 12 steps ...]

================================================================================
🎉 SUPABASE FULL INSTALLATION COMPLETED!
================================================================================

✅ ACCESS INFORMATION:
🌐 Main Dashboard: https://supabase.senaia.in
🎨 Direct Studio: https://studio.senaia.in
🔐 Login: supabase / Ma1x1x0x_testing

🔑 API CREDENTIALS:
📧 Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
🔧 Service Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

🎉 Installation completed! Check the output above for access information.
```

### Service Status During Installation

```
📊 Service Status (Elapsed: 120s):
  ✅ supabase_db: 1/1
  ✅ supabase_kong: 1/1
  ✅ supabase_studio: 1/1
  ⏳ supabase_auth: 0/1
  ⏳ supabase_rest: 0/1
  ✅ supabase_meta: 1/1
  ✅ supabase_storage: 1/1
📈 Progress: 5/7 services healthy
```

### Endpoint Testing Results

```
🧪 Testing endpoints...
  ✅ Kong Main Route    : Working
  ✅ Direct Studio      : Working
  🔐 Auth Health        : Auth Required (Normal)
  ✅ REST API           : Working
  ✅ Meta Health        : Working
  ✅ Storage API        : Working
```

## 🔧 Configuration

### Server Settings (Hardcoded)

```python
SERVER_IP = "217.79.184.8"      # Your server IP
SERVER_USER = "root"            # SSH username
SERVER_PASS = "@450Ab6606"      # SSH password
```

### Supabase Credentials

```python
DB_PASSWORD = "Ma1x1x0x_testing"                # Database password
JWT_SECRET = "DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz"  # JWT signing secret
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Anonymous API key
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Service role key
```

### Domain Configuration

All services are configured for `senaia.in` domain:
- Main access: `https://supabase.senaia.in`
- Direct Studio: `https://studio.senaia.in`

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. SSH Connection Failed

**Error**: `❌ SSH connection failed: Authentication failed`

**Solutions**:
```bash
# Test SSH manually
ssh root@217.79.184.8

# If connection works manually, check:
# - Server firewall allows SSH (port 22)
# - SSH service is running on server
# - Credentials are correct in script
```

#### 2. Missing Local Files

**Error**: `❌ Missing required files: ['supabase.yml']`

**Solution**:
```bash
# Ensure you're in the correct directory
ls -la supabase.yml

# If file doesn't exist, create or copy it
# Make sure you're in: /home/galo/Desktop/stacks_producao/supabase/portainer/
```

#### 3. Docker Swarm Not Initialized

**Error**: `❌ Docker Swarm not initialized on server`

**Solution**:
```bash
# On your server, run:
ssh root@217.79.184.8
docker swarm init --advertise-addr=217.79.184.8
```

#### 4. Service Startup Taking Long Time

**Message**: `⚠️ Maximum wait time reached. Proceeding with available services.`

**This is normal** for complex deployments. The enhanced script now:
- Waits up to 15 minutes for all services
- Auto-restarts stuck services after 3 minutes
- Continues intelligently when core services are healthy

**What to do**:
```bash
# Check current service status
ssh root@217.79.184.8
docker service ls --filter name=supabase

# Manually restart any services showing 0/1
docker service update --force supabase_SERVICE_NAME

# The script provides this information in its final output
```

#### 5. Kong DNS Resolution Still Fails

**If Kong still shows name resolution errors**:

1. **Use Direct Studio Access**: `https://studio.senaia.in`
2. **Check service IPs manually**:
   ```bash
   docker network inspect app_network --format='{{range .Containers}}{{.Name}},{{.IPv4Address}}{{"\n"}}{{end}}' | grep supabase
   ```
3. **Manually update Kong config** with the discovered IPs

#### 6. Database Connection Issues

**Error**: Database authentication failures

**Solution** (run on server):
```bash
# Reset database passwords
docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c "ALTER USER supabase_admin WITH PASSWORD 'Ma1x1x0x_testing';"
docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c "ALTER USER supabase_auth_admin WITH PASSWORD 'Ma1x1x0x_testing';"

# Restart auth service
docker service update --force supabase_auth
```

### Advanced Troubleshooting

#### Manual Service Restart

```bash
# On server - restart specific service
docker service update --force supabase_SERVICE_NAME

# Restart all Supabase services
docker service ls --filter name=supabase --format '{{.Name}}' | xargs -I {} docker service update --force {}
```

#### Check Service Logs

```bash
# View logs for specific service
docker service logs -f supabase_kong
docker service logs -f supabase_studio
docker service logs -f supabase_auth

# View recent logs only
docker service logs --tail 50 supabase_SERVICE_NAME
```

#### Network Debugging

```bash
# Check networks
docker network ls | grep -E "(app_network|traefik_public)"

# Inspect network details
docker network inspect app_network

# Test service connectivity
docker exec $(docker ps -f name=supabase_studio -q) ping auth
```

## 🔒 Security Considerations

### For Production Use

1. **Change Default Passwords**:
   ```bash
   # Generate secure passwords
   openssl rand -base64 32  # For database
   openssl rand -hex 32     # For JWT secret
   ```

2. **Update Script Configuration**:
   - Modify `DB_PASSWORD` in the script
   - Update `JWT_SECRET`
   - Regenerate API keys using Supabase CLI

3. **Use SSH Keys Instead of Passwords**:
   ```bash
   # Generate SSH key pair
   ssh-keygen -t rsa -b 4096

   # Copy public key to server
   ssh-copy-id root@217.79.184.8

   # Update script to use key-based auth
   ```

4. **Firewall Configuration**:
   ```bash
   # On server - restrict SSH access
   ufw allow from YOUR_IP to any port 22
   ufw enable
   ```

## 📚 Manual Operations

### If Script Fails

You can run individual operations manually:

#### 1. Deploy Stack Only
```bash
ssh root@217.79.184.8
cd /opt/supabase
docker stack deploy --detach=true -c supabase.yml supabase
```

#### 2. Fix Kong Configuration Only
```bash
# Get service IPs
docker network inspect app_network --format='{{range .Containers}}{{.Name}},{{.IPv4Address}}{{"\n"}}{{end}}' | grep supabase

# Update Kong config with actual IPs (replace with your IPs)
sed -i 's/studio:3000/172.18.0.5:3000/g' /mnt/data/supabase/api/kong.yml
sed -i 's/auth:9999/172.18.0.6:9999/g' /mnt/data/supabase/api/kong.yml

# Reload Kong
docker exec $(docker ps -f name=supabase_kong -q) kong reload
```

#### 3. Database Setup Only
```bash
# Create users
docker exec $(docker ps -f name=supabase_db -q) psql -U postgres -c "ALTER USER supabase_admin WITH PASSWORD 'Ma1x1x0x_testing';"

# Restart auth
docker service update --force supabase_auth
```

## 🎯 Success Criteria

Installation is successful when:

✅ **All services show 1/1 replicas**:
```bash
docker service ls --filter name=supabase
```

✅ **Web access works**:
- Main dashboard: `https://supabase.senaia.in` (login: supabase/Ma1x1x0x_testing)
- Direct Studio: `https://studio.senaia.in`

✅ **API endpoints respond**:
- Auth: `https://supabase.senaia.in/auth/v1/health`
- REST: `https://supabase.senaia.in/rest/v1/` (with API key)
- Storage: `https://supabase.senaia.in/storage/v1/` (with API key)

✅ **No Kong DNS errors**: No "name resolution failed" messages

## 📞 Support

### Log Files

The script provides comprehensive output. Save the output for troubleshooting:

```bash
# Run with output logging
python3 FULL-INSTALL-SUPABASE.py 2>&1 | tee installation.log
```

### Key Information for Support

When seeking help, provide:

1. **Complete script output** (save with `tee` command above)
2. **Service status**: `docker service ls --filter name=supabase`
3. **Service logs**: `docker service logs supabase_kong`
4. **Network information**: `docker network ls`
5. **Server specifications** and Docker version

---

## 🎉 Conclusion

The `FULL-INSTALL-SUPABASE.py` script provides a complete, automated solution for deploying Supabase with all necessary fixes for Kong DNS resolution issues. It handles the complex process of:

- File management and uploads
- Network configuration
- Service deployment and monitoring
- Database setup and user management
- Kong configuration with IP-based routing
- Comprehensive testing and validation

After successful completion, you'll have a fully functional Supabase instance accessible via both the main Kong gateway and direct Studio access, with all APIs properly configured and tested.

---

*Generated for Supabase v2.151.0 with Kong DNS resolution fixes*
*Script version: 1.0*
*Last updated: September 2025*