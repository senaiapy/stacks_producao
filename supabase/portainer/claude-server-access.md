# Claude Server Access & Environment Setup Guide

This guide explains how to set up a clean Python environment for Supabase deployment scripts and manage the script collection efficiently.

## 🐍 Python Environment Setup

### 1. Create Virtual Environment

```bash
# Navigate to the Supabase portainer directory
cd /home/galo/Desktop/stacks_producao/supabase/portainer

# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Verify you're in the virtual environment
which python3
# Should show: /home/galo/Desktop/stacks_producao/supabase/portainer/venv/bin/python3
```

### 2. Install Required Dependencies

```bash
# Make sure you're in the virtual environment (activated)
source venv/bin/activate

# Install required packages
pip install paramiko

# Create requirements file for future use
pip freeze > requirements.txt

# Verify installation
python3 -c "import paramiko; print('✅ Paramiko installed successfully')"
```

### 3. Deactivate Virtual Environment

```bash
# When you're done working
deactivate
```

## 🧹 Script Management & Cleanup

### Current Script Inventory

The folder contains many individual Python scripts created during troubleshooting. Here's the classification:

#### ✅ **Keep These Scripts (Core Functionality)**
```bash
# Main deployment scripts
unified_deployment.py          # 🌟 PRIMARY - Use this for deployment
deploy.py                     # Basic deployment
auto-deploy.sh               # Shell alternative

# Essential troubleshooting
final_working_solution.py    # Complete working solution
fix_auth_and_routing.py     # Auth & routing fixes
quick_service_restart.py    # Quick service management
```

#### 🗑️ **Archive These Scripts (Development/Debug)**
```bash
# Create archive directory
mkdir -p archive/debug-scripts
mkdir -p archive/troubleshooting

# Move debug/development scripts
mv analyze_port_conflicts.py archive/debug-scripts/
mv check_*.py archive/debug-scripts/
mv diagnose_*.py archive/troubleshooting/
mv fix_critical_*.py archive/troubleshooting/
mv fix_database_*.py archive/troubleshooting/
mv fix_kong_*.py archive/troubleshooting/
mv fix_network_*.py archive/troubleshooting/
mv fix_remaining_*.py archive/troubleshooting/
mv create_*.py archive/troubleshooting/
mv redeploy_*.py archive/troubleshooting/
mv restart_*.py archive/troubleshooting/
mv final_comprehensive_*.py archive/troubleshooting/
mv final_targeted_*.py archive/troubleshooting/
mv final_kong_*.py archive/troubleshooting/
mv quick_fix.py archive/troubleshooting/
```

### 4. Clean Directory Structure

After cleanup, your directory should look like:

```
supabase/portainer/
├── venv/                          # Python virtual environment
├── archive/                       # Archived scripts
│   ├── debug-scripts/            # Debug and analysis scripts
│   └── troubleshooting/          # Development troubleshooting scripts
├── volumes/                       # Configuration files
│   ├── api/kong.yml
│   ├── db/*.sql
│   └── logs/vector.yml
├── unified_deployment.py          # 🌟 MAIN DEPLOYMENT SCRIPT
├── deploy.py                      # Basic deployment
├── auto-deploy.sh                 # Shell deployment
├── final_working_solution.py      # Complete solution
├── fix_auth_and_routing.py        # Auth fixes
├── quick_service_restart.py       # Service management
├── supabase.yml                   # Docker Compose file
├── SUPABASE-MANUAL.md             # Complete manual
├── claude-server-access.md        # This file
├── requirements.txt               # Python dependencies
└── README.md                      # Quick start guide
```

## 🚀 Recommended Usage Workflow

### For New Deployments

```bash
# 1. Activate environment
cd /home/galo/Desktop/stacks_producao/supabase/portainer
source venv/bin/activate

# 2. Run unified deployment (recommended)
python3 unified_deployment.py

# 3. If issues occur, use targeted fixes
python3 final_working_solution.py
```

### For Maintenance

```bash
# Quick service restart
python3 quick_service_restart.py

# Auth and routing fixes
python3 fix_auth_and_routing.py

# Manual deployment
python3 deploy.py
```

## 📋 Environment Variables & Configuration

### Server Configuration (in scripts)
```python
SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "Ma1x1x0x_testing"  # ⚠️ Change for production
```

### Supabase Configuration
```yaml
# Key credentials in supabase.yml
POSTGRES_PASSWORD: Ma1x1x0x_testing
DASHBOARD_USERNAME: supabase
DASHBOARD_PASSWORD: Ma1x1x0x_testing
JWT_SECRET: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
```

## 🔧 Troubleshooting Environment Issues

### Python/Paramiko Issues

```bash
# If paramiko installation fails
sudo apt update
sudo apt install python3-dev libffi-dev libssl-dev

# Reinstall in virtual environment
source venv/bin/activate
pip install --upgrade pip
pip install paramiko
```

### SSH Connection Issues

```bash
# Test SSH connection manually
ssh root@217.79.184.8

# If connection fails, check:
# 1. Server is accessible
# 2. SSH service is running
# 3. Firewall allows SSH (port 22)
# 4. Credentials are correct
```

### Virtual Environment Issues

```bash
# If venv activation fails
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📚 Documentation References

- **SUPABASE-MANUAL.md**: Complete deployment and troubleshooting guide
- **unified_deployment.py --help**: Script usage and options
- **Docker Swarm docs**: https://docs.docker.com/engine/swarm/
- **Supabase docs**: https://supabase.com/docs/guides/self-hosting

## 🔐 Security Considerations

### For Production Use

1. **Change default passwords**:
   ```bash
   # Generate secure passwords
   openssl rand -base64 32  # For database
   openssl rand -hex 32     # For JWT secret
   ```

2. **Update supabase.yml** with new credentials

3. **Regenerate JWT keys**:
   ```bash
   # Use Supabase CLI or online JWT generator
   # Update ANON_KEY and SERVICE_KEY in scripts
   ```

4. **Secure SSH access**:
   ```bash
   # Use SSH keys instead of passwords
   ssh-keygen -t rsa -b 4096
   ssh-copy-id root@217.79.184.8
   ```

## ⚡ Quick Commands Reference

```bash
# Setup environment
source venv/bin/activate

# Deploy Supabase
python3 unified_deployment.py

# Check services
python3 -c "
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('217.79.184.8', username='root', password='Ma1x1x0x_testing')
stdin, stdout, stderr = ssh.exec_command('docker service ls --filter name=supabase')
print(stdout.read().decode())
ssh.close()
"

# Clean environment
deactivate
```

---

*This guide provides a clean, maintainable approach to managing your Supabase deployment scripts and Python environment.*