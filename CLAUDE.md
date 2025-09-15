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

### Docker Swarm Management
```bash
# Initialize swarm (replace with your server IP)
docker swarm init --advertise-addr=YOUR_IP_HERE

# Create required networks
docker network create --driver=overlay traefik_public
docker network create --driver=overlay app_network
docker network create --driver=overlay network_public

# List all services
docker service ls

# View service logs
docker service logs -f SERVICE_NAME

# Update/restart a service
docker service update --force SERVICE_NAME
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
# Access PostgreSQL
docker exec -it POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database

# Create required databases
CREATE DATABASE n8n_database;
CREATE DATABASE evolution_database;
CREATE DATABASE chatwoot_db;

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Test Redis connection
docker exec -it REDIS_CONTAINER redis-cli ping
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

### Domain Configuration

All services are configured with `senaia.in` domains. Update these in the respective YAML files:
- Portainer: `painel.seudominio.com`
- MinIO: `files.seudominio.com` / `minio.seudominio.com`
- N8N: `editor.seudominio.com` / `workflow.seudominio.com`
- Chatwoot: `chat.seudominio.com`
- Evolution: `evo.seudominio.com`

## Port Usage

- PostgreSQL: 5432 (internal)
- Redis: 6379 (internal)
- MinIO: 9000 (internal)
- N8N: 5678 (internal)
- Chatwoot: 3030 (internal)
- Evolution: 8080 (internal)
- Portainer: 9000, 9001, 9443
- Traefik: 8888, 8443

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
- **SSL certificates**: Check Traefik logs and verify DNS records
- **Database connections**: Verify network connectivity and credentials
- **Service startup**: Check placement constraints and resource limits
- **Storage**: Ensure MinIO directories exist with proper permissions

## Development Workflow

1. **Local Testing**: Test configuration changes on individual services first
2. **Staging Deployment**: Deploy to staging environment with similar setup
3. **Production Updates**: Use rolling updates with `docker service update`
4. **Backup Strategy**: Regular backups of PostgreSQL, MinIO buckets, and Docker volumes

## File Structure

- `*.yml`: Docker Compose/Swarm stack files
- `README.md`: Comprehensive installation and deployment guide
- `DOC/COMANDOS-INSTALL.TXT`: Detailed installation commands and credentials
- `.vscode/settings.json`: VS Code configuration

## Security Notes

- All sensitive credentials should be changed from defaults
- Services communicate via internal networks only
- Traefik handles SSL termination with automatic certificates
- PostgreSQL and Redis are not exposed externally
- Regular security updates should be applied to base images