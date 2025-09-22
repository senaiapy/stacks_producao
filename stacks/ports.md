# Port Conflicts Analysis - Orion Stack Only

## 📋 Overview

This document analyzes port conflicts **within the 13 Orion YAML files** located in `/orion/orion-senaia.in/` directory. This analysis focuses solely on internal conflicts within the Orion stack itself.

**Files Analyzed**: 13 YAML files
**Scope**: Internal Orion stack conflicts only

---

## 🔍 Complete Port Inventory - Orion Stack

| File | Service | Port | Type | Purpose |
|------|---------|------|------|---------|
| **traefik.yaml** | traefik | 80, 443 | External | HTTP/HTTPS entry points |
| **portainer.yaml** | portainer | 9000 | Internal | Container management |
| **portainer.yaml** | agent | 9001 | Internal | Agent communication |
| **postgres.yaml** | postgres | 5432 | Internal | Main database |
| **pgvector.yaml** | pgvector | 5432 | Internal | Vector database |
| **evolution.yaml** | evolution_api | 8080 | Internal | WhatsApp Business API |
| **evolution.yaml** | evolution_redis | 6379 | Internal | Evolution cache |
| **calcom.yaml** | calcom | 3000 | Internal | Calendar scheduling |
| **chatwoot.yaml** | chatwoot_app | 3000 | Internal | Customer service app |
| **chatwoot.yaml** | chatwoot_redis | 6379 | Internal | Chatwoot cache |
| **minio.yaml** | minio | 9000, 9001 | Internal | S3 API & Console |
| **n8n.yaml** | n8n_editor | 5678 | Internal | Workflow editor |
| **n8n.yaml** | n8n_webhook | 5678 | Internal | Webhook processor |
| **n8n.yaml** | n8n_redis | 6379 | Internal | N8N queue |
| **pgadmin.yaml** | pgadmin | 80 | Internal | Database admin |
| **rabbitmq.yaml** | rabbitmq | 5672, 15672 | Internal | AMQP & Management |
| **strapi.yaml** | strapi_app | 1337 | Internal | CMS application |
| **strapi.yaml** | strapi_db | 3306 | Internal | MySQL database |
| **supabase.yaml** | kong | 8000 | Internal | API gateway |
| **supabase.yaml** | auth | 9999 | Internal | Authentication |
| **supabase.yaml** | rest | 3000 | Internal | REST API |
| **supabase.yaml** | realtime | 4000 | Internal | Real-time features |
| **supabase.yaml** | storage | 5000 | Internal | File storage |
| **supabase.yaml** | imgproxy | 5001 | Internal | Image processing |
| **supabase.yaml** | meta | 8080 | Internal | Database metadata |
| **supabase.yaml** | db | 5432 | Internal | PostgreSQL |
| **supabase.yaml** | analytics | 4000 | Internal | Analytics service |
| **supabase.yaml** | supavisor | 4000 | Internal | Connection pooling |

---

## ⚠️ **CRITICAL PORT CONFLICTS**

### 🔴 **Conflict #1: PostgreSQL Port 5432**

**Conflicting Services:**
```
postgres.yaml     → postgres service    → port 5432
pgvector.yaml     → pgvector service    → port 5432
supabase.yaml     → db service          → port 5432
```

**Impact**: 3 PostgreSQL instances cannot bind to the same port
**Status**: 🔴 BLOCKING - Cannot deploy all three simultaneously

**Resolution Example:**
```yaml
# postgres.yaml (Main database - keep default)
services:
  postgres:
    # Internal port 5432 (no external exposure)

# pgvector.yaml (Vector database - change external port)
services:
  pgvector:
    ports:
      - "5433:5432"  # External 5433 → Internal 5432

# supabase.yaml (Supabase database - change external port)
services:
  db:
    ports:
      - "5434:5432"  # External 5434 → Internal 5432
```

### 🔴 **Conflict #2: Web Application Port 3000**

**Conflicting Services:**
```
calcom.yaml       → calcom service      → port 3000
chatwoot.yaml     → chatwoot_app service → port 3000
supabase.yaml     → rest service        → port 3000
```

**Impact**: 3 web applications cannot share the same port
**Status**: 🔴 BLOCKING - Service startup conflicts

**Resolution Example:**
```yaml
# calcom.yaml (Keep default)
services:
  calcom:
    # Port 3000 (via Traefik)

# chatwoot.yaml (Change internal port)
services:
  chatwoot_app:
    environment:
      - PORT=3001  # Use port 3001 instead
    # Update Traefik labels to use port 3001

# supabase.yaml (Keep internal - accessed via Kong)
services:
  rest:
    # Port 3000 (internal only, behind Kong gateway)
```

### 🔴 **Conflict #3: Redis Port 6379**

**Conflicting Services:**
```
evolution.yaml    → evolution_redis service → port 6379
chatwoot.yaml     → chatwoot_redis service  → port 6379
n8n.yaml          → n8n_redis service       → port 6379
```

**Impact**: 3 Redis instances cannot use the same port
**Status**: 🔴 BLOCKING - Redis connection conflicts

**Resolution Example:**
```yaml
# evolution.yaml (Keep default)
services:
  evolution_redis:
    command: redis-server --port 6379
    # Keep port 6379

# chatwoot.yaml (Use different port)
services:
  chatwoot_redis:
    command: redis-server --port 6380
    ports:
      - "6380:6380"
    # Update connection strings to use port 6380

# n8n.yaml (Use different port)
services:
  n8n_redis:
    command: redis-server --port 6381
    ports:
      - "6381:6381"
    # Update N8N Redis URI to redis://n8n_redis:6381
```

### 🔴 **Conflict #4: Supabase Internal Port 4000**

**Conflicting Services (within supabase.yaml):**
```
supabase.yaml     → realtime service    → port 4000
supabase.yaml     → analytics service   → port 4000
supabase.yaml     → supavisor service   → port 4000
```

**Impact**: 3 Supabase services cannot share port 4000
**Status**: 🔴 BLOCKING - Internal Supabase communication issues

**Resolution Example:**
```yaml
# supabase.yaml modifications
services:
  realtime:
       environment:
      - PORT=4002  # Change to port 4002
      
  analytics:
    environment:
      - PORT=4001  # Change to port 4001

  supavisor:
     # Keep port 4000

 
```

---

## 🟡 **MODERATE CONFLICTS**

### **N8N Port 5678 Sharing**

**Services:**
```
n8n.yaml          → n8n_editor service   → port 5678
n8n.yaml          → n8n_webhook service  → port 5678
```

**Impact**: May be intentional for load balancing or service routing
**Status**: 🟡 REVIEW - Check if intentional design

**Notes**: Both services use the same port but may be designed to work together or route differently via Traefik.

---

## ✅ **NO CONFLICTS (Unique Ports)**

These ports are used by only one service each:

| Port | Service | File | Status |
|------|---------|------|--------|
| 80, 443 | traefik | traefik.yaml | ✅ Unique |
| 9000 | portainer | portainer.yaml | ✅ Unique |
| 9001 | agent | portainer.yaml | ✅ Unique |
| 8080 | evolution_api | evolution.yaml | ✅ Unique |
| 80 | pgadmin | pgadmin.yaml | ✅ Unique |
| 5672, 15672 | rabbitmq | rabbitmq.yaml | ✅ Unique |
| 1337 | strapi_app | strapi.yaml | ✅ Unique |
| 3306 | strapi_db | strapi.yaml | ✅ Unique |
| 8000 | kong | supabase.yaml | ✅ Unique |
| 9999 | auth | supabase.yaml | ✅ Unique |
| 5000 | storage | supabase.yaml | ✅ Unique |
| 5001 | imgproxy | supabase.yaml | ✅ Unique |

---

## 🚀 **Deployment Strategy for Conflict Resolution**

### **Phase 1: Core Infrastructure (No Conflicts)**
```bash
docker stack deploy -c traefik.yaml traefik
docker stack deploy -c portainer.yaml portainer
```

### **Phase 2: Databases (Resolve Conflicts First)**
```bash
# Modify port conflicts before deployment:
# 1. Update pgvector.yaml → port 5433
# 2. Update supabase.yaml → port 5434
docker stack deploy -c postgres.yaml postgres
docker stack deploy -c pgvector.yaml pgvector  # After port change
```

### **Phase 3: Applications (Resolve Conflicts First)**
```bash
# Modify Redis conflicts before deployment:
# 1. Update chatwoot.yaml Redis → port 6380
# 2. Update n8n.yaml Redis → port 6381
# 3. Update chatwoot.yaml app → port 3001
docker stack deploy -c evolution.yaml evolution
docker stack deploy -c chatwoot.yaml chatwoot    # After port changes
docker stack deploy -c n8n.yaml n8n             # After port changes
```

### **Phase 4: Storage & Optional Services**
```bash
docker stack deploy -c minio.yaml minio
docker stack deploy -c calcom.yaml calcom
docker stack deploy -c strapi.yaml strapi
docker stack deploy -c pgadmin.yaml pgadmin
docker stack deploy -c rabbitmq.yaml rabbitmq
```

### **Phase 5: Supabase (Resolve Internal Conflicts)**
```bash
# Modify supabase.yaml internal port conflicts:
# 1. analytics → port 4001
# 2. supavisor → port 4002
docker stack deploy -c supabase.yaml supabase   # After internal fixes
```

---

## 🔧 **Testing Commands**

### **Check Port Conflicts Before Deployment:**
```bash
# Check if any conflicting ports are in use
netstat -tulpn | grep -E ':(5432|3000|6379|4000|5678)'

# Docker service check
docker service ls | grep -E '(postgres|redis|chatwoot|calcom|n8n|supabase)'
```

### **Verify Resolved Conflicts:**
```bash
# Test database connections
docker exec POSTGRES_CONTAINER psql -h postgres -p 5432 -U postgres -c "SELECT 1"
docker exec PGVECTOR_CONTAINER psql -h pgvector -p 5433 -U postgres -c "SELECT 1"

# Test Redis connections
docker exec EVOLUTION_CONTAINER redis-cli -h evolution_redis -p 6379 ping
docker exec CHATWOOT_CONTAINER redis-cli -h chatwoot_redis -p 6380 ping
docker exec N8N_CONTAINER redis-cli -h n8n_redis -p 6381 ping

# Test web applications
curl -I https://cal.senaia.in
curl -I https://chat.senaia.in
curl -I https://editor.senaia.in
```

---

## 📊 **Conflict Summary**

| Conflict Type | Services Affected | Severity | Resolution Required |
|---------------|-------------------|----------|-------------------|
| PostgreSQL 5432 | 3 services | 🔴 Critical | Port separation |
| Web Apps 3000 | 3 services | 🔴 Critical | Port/config changes |
| Redis 6379 | 3 services | 🔴 Critical | Port separation |
| Supabase 4000 | 3 services | 🔴 Critical | Internal port changes |
| N8N 5678 | 2 services | 🟡 Moderate | Review design |

**Total Conflicts**: 4 critical, 1 moderate
**Services Requiring Changes**: 8 out of 13 files
**Deployment Impact**: Cannot deploy without resolving conflicts

---

## 📋 **Action Items**

1. **Immediate**: Resolve critical port conflicts before deployment
2. **Update YAML files** with suggested port changes
3. **Test connectivity** after each service deployment
4. **Document final port assignments** for future reference
5. **Create deployment scripts** with proper sequencing

---

**Last Updated**: September 2025
**Status**: Conflicts identified - Resolution required before deployment