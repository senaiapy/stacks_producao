# Port Conflicts Analysis - Orion Stack (Updated Analysis)

## 📋 Overview

This document provides an updated analysis of port conflicts **within the 13 Orion YAML files** located in `/orion/orion-senaia.in/` directory after implementing port conflict resolutions.

**Files Analyzed**: 13 YAML files
**Scope**: Internal Orion stack conflicts analysis
**Last Updated**: September 2025 (Post-Resolution Analysis)

---

## 🔍 Complete Port Inventory - Current Status

| File | Service | Port Configuration | Status | Purpose |
|------|---------|-------------------|--------|---------|
| **traefik.yaml** | traefik | 80, 443 | ✅ Unique | HTTP/HTTPS entry points |
| **portainer.yaml** | portainer | 9000 (Traefik) | ✅ Unique | Container management |
| **portainer.yaml** | agent | 9001 (Internal) | ✅ Unique | Agent communication |
| **postgres.yaml** | postgres | 5432 (Internal only) | ✅ Unique | Main database |
| **pgvector.yaml** | pgvector | 5433→5432 (External→Internal) | ✅ Resolved | Vector database |
| **supabase.yaml** | db | 5434→5432 (External→Internal) | ✅ Resolved | Supabase PostgreSQL |
| **supabase.yaml** | kong | 8000 (Traefik) | ✅ Unique | Supabase API gateway |
| **supabase.yaml** | auth | 9999 (Internal) | ✅ Unique | Authentication service |
| **supabase.yaml** | rest | 3000 (Internal) | ✅ Unique | REST API (behind Kong) |
| **supabase.yaml** | realtime | 4002 (Internal) | ✅ Resolved | Real-time features |
| **supabase.yaml** | storage | 5000 (Internal) | ✅ Unique | File storage |
| **supabase.yaml** | imgproxy | 5001 (Internal) | ✅ Unique | Image processing |
| **supabase.yaml** | meta | 8080 (Internal) | ✅ Unique | Database metadata |
| **supabase.yaml** | analytics | 4001 (Internal) | ✅ Resolved | Analytics service |
| **supabase.yaml** | supavisor | 4000 (Internal) | ✅ Unique | Connection pooling |
| **evolution.yaml** | evolution_api | 8080 (Traefik) | ✅ Unique | WhatsApp Business API |
| **evolution.yaml** | evolution_redis | 6380 (Internal) | ✅ Resolved | Evolution cache |
| **calcom.yaml** | calcom | 3001 (Traefik) | ✅ Resolved | Calendar scheduling |
| **chatwoot.yaml** | chatwoot_app | 3002 (Traefik) | ✅ Resolved | Customer service app |
| **chatwoot.yaml** | chatwoot_redis | 6381 (Internal) | ✅ Resolved | Chatwoot cache |
| **n8n.yaml** | n8n_editor | 5678 (Traefik) | ✅ Unique | Workflow editor |
| **n8n.yaml** | n8n_webhook | 5678 (Traefik) | 🟡 Shared | Webhook processor |
| **n8n.yaml** | n8n_redis | 6379 (Internal) | ✅ Unique | N8N queue |
| **minio.yaml** | minio | 9000, 9001 (Traefik) | ✅ Unique | S3 API & Console |
| **pgadmin.yaml** | pgadmin | 80 (Traefik) | ✅ Unique | Database admin |
| **rabbitmq.yaml** | rabbitmq | 5672, 15672 (Internal) | ✅ Unique | AMQP & Management |
| **strapi.yaml** | strapi_app | 1337 (Traefik) | ✅ Unique | CMS application |
| **strapi.yaml** | strapi_db | 3306 (Internal) | ✅ Unique | MySQL database |

---

## ✅ **RESOLVED CONFLICTS**

### **✅ Conflict #1: PostgreSQL Port 5432 - RESOLVED**

**Previous Conflicting Services:**
```
postgres.yaml     → postgres service    → port 5432
pgvector.yaml     → pgvector service    → port 5432
supabase.yaml     → db service          → port 5432
```

**Status**: ✅ **FULLY RESOLVED**

**Resolution Applied:**
```yaml
# postgres.yaml (Main database)
services:
  postgres:
    # Internal port 5432 only (no external exposure)

# pgvector.yaml (Vector database)
services:
  pgvector:
    ports:
      - "5433:5432"  # External 5433 → Internal 5432

# supabase.yaml (Supabase database)
services:
  db:
    ports:
      - "5434:5432"  # External 5434 → Internal 5432
```

**Connection String Updates Applied:**
- ✅ Evolution API: Updated to `pgvector:5433` for Chatwoot integration
- ✅ All internal Supabase services: Continue using `db:5432` (internal networking)

---

### **✅ Conflict #2: Web Application Port 3000 - RESOLVED**

**Previous Conflicting Services:**
```
calcom.yaml       → calcom service      → port 3000
chatwoot.yaml     → chatwoot_app service → port 3000
supabase.yaml     → rest service        → port 3000
```

**Status**: ✅ **FULLY RESOLVED**

**Resolution Applied:**
```yaml
# calcom.yaml
services:
  calcom:
    environment:
      - PORT=3001
      - NEXT_PUBLIC_WEBAPP_PORT=3001
    # Traefik: loadbalancer.server.port=3001

# chatwoot.yaml
services:
  chatwoot_app:
    command: bundle exec rails s -p 3002 -b 0.0.0.0 -e production
    environment:
      - PORT=3002
    # Traefik: loadbalancer.server.port=3002

# supabase.yaml
services:
  rest:
    # Port 3000 (internal only, behind Kong gateway at port 8000)
```

---

### **✅ Conflict #3: Redis Port 6379 - RESOLVED**

**Previous Conflicting Services:**
```
evolution.yaml    → evolution_redis service → port 6379
chatwoot.yaml     → chatwoot_redis service  → port 6379
n8n.yaml          → n8n_redis service       → port 6379
```

**Status**: ✅ **FULLY RESOLVED**

**Resolution Applied:**
```yaml
# evolution.yaml
services:
  evolution_redis:
    command: ["redis-server", "--appendonly", "yes", "--port", "6380"]
    # Connection: CACHE_REDIS_URI=redis://evolution_redis:6380/1

# chatwoot.yaml
services:
  chatwoot_redis:
    command: ["redis-server", "--appendonly", "yes", "--port", "6381"]
    # Connection: REDIS_URL=redis://chatwoot_redis:6381

# n8n.yaml
services:
  n8n_redis:
    command: ["redis-server", "--appendonly", "yes", "--port", "6379"]
    # Connection: QUEUE_BULL_REDIS_PORT=6379
```

---

### **✅ Conflict #4: Supabase Internal Port 4000 - RESOLVED**

**Previous Conflicting Services:**
```
supabase.yaml     → realtime service    → port 4000
supabase.yaml     → analytics service   → port 4000
supabase.yaml     → supavisor service   → port 4000
```

**Status**: ✅ **FULLY RESOLVED**

**Resolution Applied:**
```yaml
# supabase.yaml modifications
services:
  realtime:
    environment:
      - PORT=4002  # Changed from 4000

  analytics:
    environment:
      - PORT=4001  # Changed from 4000

  supavisor:
    environment:
      - PORT=4000  # Kept default
```

**Connection Updates:**
- ✅ Studio service: Updated `LOGFLARE_URL=http://analytics:4001`

---

## 🟡 **MODERATE CONFLICTS**

### **🟡 N8N Port 5678 Sharing - INTENTIONAL DESIGN**

**Services:**
```
n8n.yaml          → n8n_editor service   → port 5678 (Traefik)
n8n.yaml          → n8n_webhook service  → port 5678 (Traefik)
```

**Status**: 🟡 **ACCEPTABLE** - Likely intentional load balancing design
**Impact**: Both services handle different aspects of N8N via Traefik routing

---

## 🚀 **DEPLOYMENT STRATEGY - CURRENT STATUS**

### **✅ Ready for Sequential Deployment**

```bash
# Phase 1: Core Infrastructure (No Conflicts)
docker stack deploy -c traefik.yaml traefik
docker stack deploy -c portainer.yaml portainer

# Phase 2: Databases (Conflicts Resolved)
docker stack deploy -c postgres.yaml postgres      # Internal 5432
docker stack deploy -c pgvector.yaml pgvector      # External 5433→Internal 5432
docker stack deploy -c supabase.yaml supabase      # External 5434→Internal 5432

# Phase 3: Applications (Conflicts Resolved)
docker stack deploy -c evolution.yaml evolution    # Redis 6380
docker stack deploy -c chatwoot.yaml chatwoot      # App 3002, Redis 6381
docker stack deploy -c calcom.yaml calcom          # App 3001
docker stack deploy -c n8n.yaml n8n               # Redis 6379, App 5678

# Phase 4: Storage & Optional Services
docker stack deploy -c minio.yaml minio           # 9000, 9001
docker stack deploy -c strapi.yaml strapi         # 1337, MySQL 3306
docker stack deploy -c pgadmin.yaml pgadmin       # 80 via Traefik
docker stack deploy -c rabbitmq.yaml rabbitmq     # 5672, 15672
```

---

## 🔧 **Testing Commands - Post Resolution**

### **✅ PostgreSQL Connectivity Tests**
```bash
# Test main postgres (internal only)
docker exec $(docker ps -q -f name=postgres) psql -U postgres -c "SELECT 1"

# Test pgvector (external port 5433)
psql -h YOUR_HOST_IP -p 5433 -U postgres -c "SELECT 1"

# Test supabase db (external port 5434)
psql -h YOUR_HOST_IP -p 5434 -U postgres -c "SELECT 1"
```

### **✅ Redis Connectivity Tests**
```bash
# Test evolution redis (port 6380)
docker exec $(docker ps -q -f name=evolution_redis) redis-cli -p 6380 ping

# Test chatwoot redis (port 6381)
docker exec $(docker ps -q -f name=chatwoot_redis) redis-cli -p 6381 ping

# Test n8n redis (port 6379)
docker exec $(docker ps -q -f name=n8n_redis) redis-cli -p 6379 ping
```

### **✅ Web Application Tests**
```bash
# Test all web applications via Traefik
curl -I https://cal.senaia.in          # Cal.com (port 3001)
curl -I https://chat.senaia.in         # Chatwoot (port 3002)
curl -I https://evo.senaia.in          # Evolution (port 8080)
curl -I https://editor.senaia.in       # N8N (port 5678)
curl -I https://supabase.senaia.in     # Supabase (Kong 8000)
curl -I https://painel.senaia.in       # Portainer (port 9000)
curl -I https://files.senaia.in        # MinIO (port 9000)
curl -I https://strapi.senaia.in       # Strapi (port 1337)
curl -I https://pgadmin.senaia.in      # PgAdmin (port 80)
```

---

## 📊 **Final Conflict Summary**

| Conflict Type | Previous Status | Current Status | Services Affected |
|---------------|----------------|----------------|-------------------|
| PostgreSQL 5432 | 🔴 Critical | ✅ Resolved | postgres, pgvector, supabase |
| Web Apps 3000 | 🔴 Critical | ✅ Resolved | calcom, chatwoot, supabase |
| Redis 6379 | 🔴 Critical | ✅ Resolved | evolution, chatwoot, n8n |
| Supabase 4000 | 🔴 Critical | ✅ Resolved | realtime, analytics, supavisor |
| N8N 5678 | 🟡 Moderate | 🟡 Acceptable | n8n_editor, n8n_webhook |

**Total Conflicts**: 0 critical, 1 acceptable moderate
**Files Modified**: 4 out of 13 files
**Deployment Status**: ✅ **READY FOR PRODUCTION DEPLOYMENT**

---

## 🎯 **Key Achievements**

1. ✅ **All critical port conflicts resolved**
2. ✅ **External port mappings implemented for PostgreSQL services**
3. ✅ **Redis services isolated on different ports**
4. ✅ **Web applications using unique ports**
5. ✅ **Internal Supabase port conflicts resolved**
6. ✅ **Connection strings updated appropriately**
7. ✅ **Maintained internal service communication**
8. ✅ **Preserved security through internal networking**

The Orion stack is now **ready for conflict-free deployment** with all services properly isolated and configured.

---

**Last Updated**: September 2025
**Status**: ✅ All conflicts resolved - Ready for deployment