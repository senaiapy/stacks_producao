# Quick Supabase Stack Removal Guide

## 🚀 Automated Removal (Recommended)

```bash
# Run the automated removal script
python3 remove_supabase_stack.py
```

**What the script does:**
- ✅ Removes Docker stack and all services
- ✅ Removes Docker configs (kong, vector, pooler)
- ✅ Optionally removes volumes (with data)
- ✅ Optionally removes server files
- ✅ Optionally cleans database users/schemas
- ✅ Verifies complete removal

## ⚡ Quick Manual Removal

### Step 1: Remove Docker Stack
```bash
ssh root@217.79.184.8
docker stack rm supabase
```

### Step 2: Wait for Services to Stop
```bash
# Wait 30 seconds for all services to be removed
sleep 30

# Verify services are gone
docker service ls | grep supabase
```

### Step 3: Remove Docker Configs
```bash
docker config rm supabase_kong_config
docker config rm supabase_vector_config
docker config rm supabase_pooler_config
```

### Step 4: Remove Docker Volumes (Optional - Contains Data!)
```bash
# List Supabase volumes first
docker volume ls | grep supabase

# Remove volumes (THIS DELETES ALL DATA!)
docker volume rm supabase_storage
docker volume rm supabase_functions
docker volume rm supabase_vector_config
```

### Step 5: Remove Server Files (Optional)
```bash
# Remove configuration files
rm -rf /opt/supabase
```

### Step 6: Clean Database (Optional)
```bash
# Connect to PostgreSQL
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)

# Remove Supabase schemas
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP SCHEMA IF EXISTS _realtime CASCADE;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP SCHEMA IF EXISTS storage CASCADE;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP SCHEMA IF EXISTS auth CASCADE;"

# Remove Supabase users
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP USER IF EXISTS supabase_auth_admin;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP USER IF EXISTS supabase_storage_admin;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP USER IF EXISTS supabase_functions_admin;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP USER IF EXISTS authenticator;"
docker exec $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database -c "DROP USER IF EXISTS supabase_admin;"
```

## 🔍 Verification Commands

### Check if removal was successful:
```bash
# No services should be found
docker service ls | grep supabase

# No configs should be found
docker config ls | grep supabase

# No volumes should be found (if you removed them)
docker volume ls | grep supabase

# Check server files are gone
ls -la /opt/supabase

# Check database users are gone
docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c "SELECT usename FROM pg_user WHERE usename LIKE 'supabase%';"
```

## ⚠️ Important Notes

### What Gets Removed:
- ✅ All Supabase Docker services
- ✅ Supabase Docker configs
- ✅ Supabase volumes (if chosen)
- ✅ Configuration files in /opt/supabase
- ✅ Database users and schemas (if chosen)

### What Remains Untouched:
- ✅ PostgreSQL database and main data
- ✅ Other Docker stacks (N8N, Chatwoot, etc.)
- ✅ Traefik configuration
- ✅ Docker networks
- ✅ Your main chatwoot_database data

### Domains Affected:
After removal, these domains will return 404 errors:
- `supabase.senaia.in`
- `studio.senaia.in`
- `pooler.senaia.in`

## 🔄 Re-deployment

To redeploy Supabase later:
```bash
# Use the deployment script
python3 deploy_ssh.py
```

---

**Safe removal with confirmation prompts and data preservation options**