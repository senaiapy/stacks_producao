# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker Swarm production stack for WhatsApp Business automation and customer service. The stack includes multiple integrated services for automation, customer support, and messaging infrastructure.

## Architecture

### Core Infrastructure
- **Docker Swarm Mode**: All services are deployed as Docker Swarm stacks
- **Traefik v3**: Reverse proxy with automatic SSL certificates (Let's Encrypt)
- **PostgreSQL 16**: Primary database with pgvector extension for AI features
- **Redis 7**: Cache and message broker
- **MinIO**: S3-compatible object storage

### Application Services
- **N8N**: Workflow automation platform (4 separate services: editor, webhook, worker, mcp)
- **Chatwoot**: Customer service platform
- **Evolution API**: WhatsApp Business integration
- **Portainer**: Docker Swarm management interface

### Network Architecture
- `traefik_public`: External network for Traefik reverse proxy
- `app_network`: Internal network for service-to-service communication
- `network_public`: Alternative public network for containers

## Common Commands

### Quick Stack Management
```bash
# Deploy all infrastructure services in parallel
docker stack deploy -c portainer.yml portainer && \
docker stack deploy -c traefik.yml traefik && \
docker stack deploy -c postgres.yml postgres && \
docker stack deploy -c redis.yml redis && \
docker stack deploy -c minio.yml minio

# Deploy all N8N services in parallel
docker stack deploy -c n8n_editor.yml n8n-editor && \
docker stack deploy -c n8n_webhook.yml n8n-webhook && \
docker stack deploy -c n8n_worker.yml n8n-worker && \
docker stack deploy -c n8n_mcp.yml n8n-mcp

# Restart all services in a stack (useful for configuration updates)
for service in $(docker service ls --filter label=com.docker.stack.namespace=STACK_NAME --format "{{.Name}}"); do
  docker service update --force $service
done
```

### Docker Swarm Management
```bash
# Initialize swarm (replace with your server IP)
docker swarm init --advertise-addr=YOUR_IP_HERE

# Create required networks
docker network create --driver=overlay traefik_public
docker network create --driver=overlay app_network
docker network create --driver=overlay network_public
docker network create --driver=overlay traefik_baileys_public
docker network create --driver=overlay app_baileys_network
docker network create --driver=overlay supabase-net

# List all services
docker service ls

# View service logs
docker service logs -f SERVICE_NAME

# Update/restart a service
docker service update --force SERVICE_NAME

# Remove a stack
docker stack rm STACK_NAME

# Deploy stack with options
docker stack deploy --prune --resolve-image always -c STACK_FILE.yml STACK_NAME
```

### Stack Deployment Order
```bash
# 1. Infrastructure
docker stack deploy -c portainer.yml portainer
docker stack deploy -c traefik.yml traefik

# 2. Databases
docker stack deploy -c postgres.yml postgres
docker stack deploy -c redis.yml redis

# 3. Storage
docker stack deploy -c minio.yml minio

# 4. Applications
docker stack deploy -c n8n_editor.yml n8n-editor
docker stack deploy -c n8n_webhook.yml n8n-webhook
docker stack deploy -c n8n_worker.yml n8n-worker
docker stack deploy -c n8n_mcp.yml n8n-mcp
docker stack deploy -c evolution.yml evolution

# 5. Chatwoot (requires migration first - see below)
# 6. Optional services
docker stack deploy -c calendar.yml calendar
docker stack deploy -c strapi.yml strapi
docker stack deploy -c supabase.yml supabase
docker stack deploy -c pgadmin.yml pgadmin
docker stack deploy -c rabbitmq.yml rabbitmq
docker stack deploy -c nproxy.yml nginx-proxy
```

### Chatwoot Migration (Required Before Deployment)
```bash
# Run migration container
docker service create --name chatwoot-migrate \
  --network app_network \
  --restart-condition none \
  -e NODE_ENV=production \
  -e RAILS_ENV=production \
  -e SECRET_KEY_BASE=YOUR_SECRET_KEY \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_USERNAME=chatwoot_database \
  -e POSTGRES_PASSWORD="YOUR_POSTGRES_PASSWORD" \
  -e POSTGRES_DATABASE=chatwoot_db \
  -e POSTGRES_PORT=5432 \
  -e REDIS_URL=redis://:YOUR_REDIS_PASSWORD@redis:6379 \
  chatwoot/chatwoot:v4.2.0 \
  bundle exec rails db:chatwoot_prepare

# Monitor migration
docker service logs -f chatwoot-migrate

# Clean up after migration
docker service rm chatwoot-migrate

# Deploy Chatwoot
docker stack deploy -c chatwoot.yml chatwoot
```

### Database Operations
```bash
# Access PostgreSQL (find container dynamically)
POSTGRES_CONTAINER=$(docker ps -q -f name=postgres)
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database

# Create required databases
CREATE DATABASE n8n_database;
CREATE DATABASE evolution_database;
CREATE DATABASE chatwoot_db;
CREATE DATABASE chatwoot_baileys_db;
CREATE DATABASE supabase_db;

# Enable pgvector extension (for AI features)
CREATE EXTENSION IF NOT EXISTS vector;

# List all databases
\l

# Test Redis connection (find container dynamically)
REDIS_CONTAINER=$(docker ps -q -f name=redis)
docker exec -it $REDIS_CONTAINER redis-cli -a J40geWtC08VoaUqoZ ping

# Test PostgreSQL connection
psql -h localhost -U chatwoot_database -d chatwoot_database -c "SELECT 1"

# Database backup
docker exec $POSTGRES_CONTAINER pg_dump -U chatwoot_database chatwoot_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Database restore
cat backup_file.sql | docker exec -i $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database
```

### Security Key Generation
```bash
# Generate SECRET_KEY_BASE (64 chars)
openssl rand -hex 32

# Generate N8N_ENCRYPTION_KEY (32 chars)
openssl rand -hex 16

# Generate secure passwords
openssl rand -base64 32
```

## Service Configuration

### Important Environment Variables to Customize

**PostgreSQL**: Update password in `postgres.yml`
**Redis**: Update password in `redis.yml`
**MinIO**: Update credentials in `minio.yml`
**Chatwoot**: Update SECRET_KEY_BASE and storage keys in `chatwoot.yml`
**N8N**: Update N8N_ENCRYPTION_KEY in all N8N service files
**Evolution API**: Update AUTHENTICATION_API_KEY in `evolution.yml`

### N8N Plugin Installation
After N8N deployment, install required plugins via Settings > Plugins:
- `n8n-nodes-evolution-api`
- `@devlikeapro/n8n-nodes-chatwoot`

### MinIO Bucket Creation
After MinIO deployment, create required buckets via web console:
- `evolution` - for Evolution API file storage
- `chatwoot` - for Chatwoot attachments
- Additional buckets as needed for other services

### Domain Configuration

All services are configured with `senaia.in` domains. Update these in the respective YAML files:
- Portainer: `painel.seudominio.com`
- MinIO: `files.seudominio.com` / `minio.seudominio.com`
- N8N: `editor.seudominio.com` / `workflow.seudominio.com`
- Chatwoot: `chat.seudominio.com`
- Evolution: `evo.seudominio.com`
- Calendar: `agenda.seudominio.com`
- Strapi: `strapi.seudominio.com`
- Supabase: `supabase.seudominio.com`
- PGAdmin: `pgadmin.seudominio.com`
- RabbitMQ: `rabbitmq.seudominio.com`

## Port Usage

### Internal Ports (Container Only)
- PostgreSQL: 5432 or 25432 (depending on configuration)
- Redis: 6379
- MinIO: 9000 (API), 9001 (Console)
- N8N: 5678
- Chatwoot: 3030
- Evolution: 8080
- Supabase: 8000 (API), 3032 (Studio)
- RabbitMQ: 5672 (AMQP), 15672 (Management)
- Strapi: 1337
- Calendar: 3000

### External Ports (Host Exposed)
- Traefik: 80 (HTTP), 443 (HTTPS), 8888 (Dashboard)
- Portainer: 9000, 9001, 9443
- RabbitMQ: 5672 (AMQP)
- Calendar: 6000 (mapped to internal 3000)
- Nginx Proxy Manager: 8181

### Port Conflict Notes
- Evolution API uses port 8080 internally only (no host exposure)
- Port 8443 is available for future services
- PostgreSQL may use custom port 25432 to avoid system conflicts
- All web services use Traefik reverse proxy for external access

## Troubleshooting

### Service Health Checks
```bash
# Check service status
docker service ps SERVICE_NAME

# View detailed service info
docker service inspect SERVICE_NAME

# Check Docker events
docker events

# Monitor resource usage
docker stats
```

### Common Issues
- **SSL certificates**: Check Traefik logs and verify DNS records using dnschecker
- **Database connections**: Verify network connectivity and credentials
- **Service startup**: Check placement constraints and resource limits
- **Storage**: Ensure MinIO directories exist with proper permissions (`mkdir -p /var/data/minio`)
- **N8N plugins**: Install required plugins manually after deployment
- **Chatwoot migration**: Always run migration before deploying Chatwoot stack
- **Domain resolution**: Verify DNS propagation before deployment to avoid Let's Encrypt blocks

### Pre-deployment Checklist
1. Verify DNS records are propagated (use dnschecker.org)
2. Create required directories: `/var/data/minio`, `/var/data/npm`
3. Update all domain names in YAML files
4. Change default passwords and encryption keys
5. Ensure Docker Swarm networks are created

## Development Workflow

1. **Local Testing**: Test configuration changes on individual services first
2. **Staging Deployment**: Deploy to staging environment with similar setup
3. **Production Updates**: Use rolling updates with `docker service update`
4. **Backup Strategy**: Regular backups of PostgreSQL, MinIO buckets, and Docker volumes

## File Structure

### Stack Files (`/stacks/`)
- `*.yml`: Docker Compose/Swarm stack files (29 total)
- Core stacks: `traefik.yml`, `postgres.yml`, `redis.yml`, `minio.yml`
- Application stacks: `n8n_*.yml`, `chatwoot.yml`, `evolution.yml`
- Optional stacks: `calendar.yml`, `strapi.yml`, `supabase.yml`, `pgadmin.yml`

### Documentation
- `README.md`: Comprehensive installation and deployment guide (Portuguese)
- `MANUAL-INSTALL.md`: Detailed manual with credentials and step-by-step instructions
- `PORTS-COMPATIBILITY.md`: Port usage analysis and conflict resolution
- `DOC/COMANDOS-INSTALL copy.md`: Installation commands and credentials reference
- `.vscode/settings.json`: VS Code configuration

### Alternative Configurations
- `/orion/`: Alternative stack configurations (ORION deployment)
- `/docker-local/`: Local development configurations
- `/supabase/`: Supabase-specific configurations
- `/manuals/`: Additional documentation and guides

### Environment Files
- `.env`: Environment variables and configuration
- `.gitignore`: Git ignore patterns

## Security Notes

- All sensitive credentials should be changed from defaults
- Services communicate via internal networks only
- Traefik handles SSL termination with automatic certificates
- PostgreSQL and Redis are not exposed externally
- Regular security updates should be applied to base images

## Environment-Specific Commands

### System Preparation (Production Setup)
```bash
# Set timezone (adjust as needed)
sudo timedatectl set-timezone America/Asuncion

# Install system dependencies
sudo apt-get update && apt-get install -y apparmor-utils sshpass

# Configure hostname
hostnamectl set-hostname YOUR_HOSTNAME
echo "127.0.0.1 YOUR_HOSTNAME" >> /etc/hosts

# Create required directories
sudo mkdir -p /var/data/minio /var/data/npm
sudo chown -R $USER:docker /var/data/minio
```

### Development and Testing
```bash
# Quick health check for all services
docker service ls --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"

# Monitor service resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check service placement across nodes
docker service ps $(docker service ls -q) --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}"

# View aggregated logs for troubleshooting
docker service logs --tail=50 --follow SERVICE_NAME 2>&1 | grep -E "(ERROR|WARN|FATAL)"
```

### Configuration Validation
```bash
# Validate YAML files before deployment
for file in *.yml; do
  echo "Validating $file..."
  docker-compose -f "$file" config > /dev/null && echo "✓ Valid" || echo "✗ Invalid"
done

# Check DNS resolution for all configured domains
for domain in painel.senaia.in minio.senaia.in chat.senaia.in evo.senaia.in editor.senaia.in; do
  echo "Checking $domain..."
  nslookup $domain || echo "DNS issue for $domain"
done

# Verify SSL certificate status
for domain in painel.senaia.in minio.senaia.in chat.senaia.in evo.senaia.in editor.senaia.in; do
  echo "SSL status for $domain:"
  curl -I -s --connect-timeout 5 https://$domain | head -n 1
done
```