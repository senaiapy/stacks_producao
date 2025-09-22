# Port Compatibility Analysis - Docker Swarm Stack Production

**Generated**: September 20, 2025
**Status**: ✅ All services analyzed - No critical conflicts detected

## Executive Summary

This document analyzes port usage across all Docker Swarm stacks to identify potential conflicts, especially focusing on ports **8080** and **8443** as requested. All services use proper overlay networks and Traefik reverse proxy, minimizing direct port exposure.

## Port Allocation Overview

### External Ports (Host Exposed)
| Service | Host Port | Container Port | Protocol | Purpose | Conflict Risk |
|---------|-----------|----------------|----------|---------|---------------|
| **Traefik** | 80 | 80 | TCP | HTTP (redirects to HTTPS) | ✅ Standard |
| **Traefik** | 443 | 443 | TCP | HTTPS/SSL | ✅ Standard |
| **Portainer** | 9443 | 9443 | TCP | HTTPS Management | ✅ Safe |
| **RabbitMQ** | 5672 | 5672 | TCP | AMQP Protocol | ✅ Safe |
| **Calendar** | 6000 | 3000 | TCP | HTTP Service | ✅ Safe |

### Internal Ports (Container-only)
| Service | Internal Port | Purpose | Network |
|---------|---------------|---------|---------|
| **Supabase Studio** | 3000 | Web UI | app_network |
| **Supabase REST** | 3000 | PostgREST API | app_network |
| **Supabase Auth** | 9999 | GoTrue Auth | app_network |
| **Supabase Nginx Proxy** | 80 | Proxy to Studio | app_network |
| **PostgreSQL** | 25432 | Database (custom port) | app_network |
| **Evolution API** | 8080 | WhatsApp API | app_network |
| **N8N Editor** | 5678 | Workflow Editor | app_network |
| **Chatwoot Rails** | 3000 | Web Application | app_network |
| **Redis** | 6379 | Cache/Queue | app_network |
| **MinIO** | 9000 | S3 API | traefik_public |
| **MinIO Console** | 9001 | Web Console | traefik_public |

## Critical Port Analysis: 8080 & 8443

### Port 8080 Analysis ✅ NO CONFLICTS
- **Evolution API**: Uses port 8080 internally (container port)
- **Supabase**: No services using 8080
- **Traefik**: 8080 commented out (dashboard disabled)
- **Kong**: Not used in current configuration (replaced with nginx proxy)
- **Conflict Status**: ✅ **SAFE** - Only Evolution uses 8080 internally

### Port 8443 Analysis ✅ NO CONFLICTS
- **No services currently using port 8443**
- **Traefik**: 8443 commented out in configuration
- **Kong**: No longer used (replaced with nginx proxy)
- **Conflict Status**: ✅ **SAFE** - Port 8443 is available

## Detailed Service Analysis

### 1. Traefik (Reverse Proxy)
```yaml
Exposed Ports:
  - 80:80   (HTTP → HTTPS redirect)
  - 443:443 (HTTPS/SSL)
Commented Ports:
  - 8080    (Dashboard - disabled for production)
  - 8443    (Alternative HTTPS - not used)
```
**Status**: ✅ Production-ready configuration

### 2. Supabase Stack
```yaml
PostgreSQL:     25432 (internal) - Changed from 5432 to avoid conflicts
Studio:         3000  (internal) - Accessed via studio.senaia.in
REST API:       3000  (internal) - Accessed via api.senaia.in
Auth:           9999  (internal) - Accessed via auth.senaia.in
Nginx Proxy:    80    (internal) - Routes supabase.senaia.in to Studio
```
**Status**: ✅ No external ports, all traffic via Traefik

### 3. Evolution API
```yaml
Internal Port: 8080 (containerized)
External Access: evo.senaia.in (via Traefik)
```
**Status**: ✅ No host port exposure, uses internal 8080 safely

### 4. PostgreSQL
```yaml
Internal Port: 25432 (changed from standard 5432)
Access: Internal network only
```
**Status**: ✅ Custom port prevents conflicts with system PostgreSQL

### 5. N8N Services
```yaml
Editor:   5678 (internal) - editor.senaia.in
Webhook:  5678 (internal) - workflow.senaia.in
Worker:   5678 (internal)
MCP:      5678 (internal)
```
**Status**: ✅ All share same internal port, differentiated by routing

### 6. Chatwoot
```yaml
Rails:    3000 (internal) - chat.senaia.in
Sidekiq:  3000 (internal) - background worker
```
**Status**: ✅ Internal access only

### 7. MinIO Storage
```yaml
S3 API:   9000 (internal) - files.senaia.in
Console:  9001 (internal) - minio.senaia.in
```
**Status**: ✅ No port conflicts

### 8. Redis
```yaml
Internal Port: 6379
Access: Password protected, internal network only
```
**Status**: ✅ Standard Redis port, internal only

### 9. RabbitMQ
```yaml
Exposed Port: 5672:5672 (AMQP)
Management: 15672 (internal) - rabbitmq.senaia-bank.in
```
**Status**: ✅ Standard AMQP port exposed safely

### 10. Portainer
```yaml
Exposed Port: 9443:9443 (HTTPS)
Management: 9000 (internal, commented out)
```
**Status**: ✅ Secure HTTPS access only

### 11. Calendar (Cal.com)
```yaml
Exposed Port: 6000:3000
Access: agenda.senaia-bank.in
```
**Status**: ✅ Custom mapping prevents conflicts

## Network Architecture

### Network Segmentation
```yaml
traefik_public:
  Purpose: External access via Traefik
  Services: All public-facing services

app_network:
  Purpose: Internal service communication
  Services: Database, cache, internal APIs

network_public:
  Purpose: Legacy network (used by some services)
  Services: RabbitMQ, Calendar
```

### Security Analysis
- ✅ **Minimal Port Exposure**: Only essential ports (80, 443, 9443, 5672, 6000) exposed
- ✅ **Service Isolation**: Internal communication via overlay networks
- ✅ **SSL Termination**: All HTTPS handled by Traefik with Let's Encrypt
- ✅ **Access Control**: No direct database or cache access from external

## Port Conflict Prevention

### Implemented Solutions
1. **Custom PostgreSQL Port**: 25432 instead of 5432
2. **Internal Routing**: All services use Traefik for external access
3. **Network Segregation**: Overlay networks prevent port conflicts
4. **Service Discovery**: Docker Swarm DNS resolution

### Reserved Ports
```yaml
System Reserved:
  - 22    (SSH)
  - 80    (Traefik HTTP)
  - 443   (Traefik HTTPS)

Application Reserved:
  - 5432  (System PostgreSQL)
  - 8080  (Evolution API - internal)
  - 8443  (Available for future use)
  - 9443  (Portainer HTTPS)
```

## Recommendations

### ✅ Current State
- All services properly configured with no conflicts
- Port 8080 safely used internally by Evolution API
- Port 8443 available for future services
- Production-ready security posture

### 🔧 Future Considerations
1. **Monitor Resource Usage**: Some services share internal ports (3000, 5678)
2. **SSL Certificate Management**: Ensure Let's Encrypt limits not exceeded
3. **Database Scaling**: Consider PostgreSQL connection pooling if load increases
4. **Backup Strategy**: Implement regular backups for persistent volumes

### 🚨 Critical Ports to Avoid
- **5432**: Reserved for system PostgreSQL
- **3306**: Reserved for MySQL (if needed)
- **80/443**: Reserved for Traefik
- **22**: SSH access

## Conclusion

✅ **No port conflicts detected**
✅ **Evolution API safely uses port 8080 internally**
✅ **Port 8443 available for future use**
✅ **All services properly isolated and secured**
✅ **Production-ready configuration**

The current stack configuration demonstrates excellent port management with proper network isolation, minimal external exposure, and no conflicts between services. The architecture supports scalability and maintains security best practices.

---

  🚀 Deployment Steps to Fix 404:

  Step 1: Database Setup

  Cal.com needs a database to be created and migrated:

  # Create Cal.com database
  docker exec -it $(docker ps -q -f name=postgres) psql -U postgres -c ""

  # Grant permissions (if needed)
  docker exec -it $(docker ps -q -f name=postgres) psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE calcom TO postgres;"

  Step 2: Redeploy Cal.com Service

  # Deploy with fixed configuration
  docker stack deploy -c calcom.yaml calcom

  # Wait for service to start
  sleep 30

  # Check service status
  docker service ps calcom_calcom

  Step 3: Run Database Migrations

  Cal.com requires database migrations to run:

  # Run migrations (Cal.com should do this automatically, but if not...)
  docker service logs calcom_calcom | grep -i migration

  # If migrations fail, you might need to run them manually:
  docker exec -it $(docker ps -q -f name=calcom) npm run db:migrate

  🔍 Troubleshooting Commands:

  Check Service Health:

  # Service status
  docker service ls | grep calcom
  docker service ps calcom_calcom

  # Service logs
  docker service logs calcom_calcom

  # Check if port 3001 is responding
  curl -I http://localhost:3001

  Verify Database Connection:

  # Test database connection
  docker exec -it $(docker ps -q -f name=postgres) psql -U postgres -d calcom -c "SELECT 1"

  # Check if Cal.com tables exist
  docker exec -it $(docker ps -q -f name=postgres) psql -U postgres -d calcom -c "\dt"

  DNS and SSL Check:

  # Check DNS resolution
  nslookup cal.senaia.in

  # Test HTTPS certificate
  curl -I https://cal.senaia.in

  🎯 Most Likely Causes of 404:

  1. Database not initialized - Cal.com needs migrations to run
  2. Service startup failure - Check logs for errors
  3. SSL certificate issues - Check Traefik logs
  4. Network connectivity - Verify service is on traefik_public network

● The main issue was the incorrect CALENDSO_ENCRYPTION_KEY configuration that was pointing to a database URL instead of being an
  encryption key. This would cause Cal.com to fail during startup.

  Next Steps:
  1. Ensure the calcom database exists in PostgreSQL
  2. Redeploy the service with the fixed configuration
  3. Check service logs to verify it's starting properly
  4. Test the URL again after deployment

**Document Version**: 1.0
**Last Updated**: September 20, 2025
**Next Review**: October 20, 2025