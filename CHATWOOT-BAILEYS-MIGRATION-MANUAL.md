# Manual de Instalação - Chatwoot com Baileys no Portainer

Este manual descreve como implantar o Chatwoot com integração Baileys (WhatsApp) usando Docker Swarm e Portainer.

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de que os seguintes serviços estejam **rodando** no Docker Swarm:

- ✅ **PostgreSQL** (stack `postgres`)
- ✅ **Redis** (stack `redis`)
- ✅ **MinIO** (stack `minio`)
- ✅ **Traefik** (stack `traefik`)

### Verificar Serviços Ativos

```bash
# Listar todos os serviços ativos
docker service ls

# Verificar se as redes existem
docker network ls | grep -E "(app_network|traefik_public)"

# Verificar saúde dos serviços
docker service ps postgres_postgres
docker service ps redis_redis
docker service ps minio_minio
docker service ps traefik_traefik
```

## 🗄️ Preparação do Banco de Dados

### 1. Criar Database no PostgreSQL

```bash
# Acessar container PostgreSQL
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres_postgres" --format "{{.ID}}")
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -d postgres

# Dentro do PostgreSQL, executar:
CREATE DATABASE chatwoot_baileys_db;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_baileys_db TO chatwoot_database;

# Habilitar extensão pgvector (se necessário)
\c chatwoot_baileys_db
CREATE EXTENSION IF NOT EXISTS vector;

# Verificar criação
\l

# Sair
\q
```

sudo add-apt-repository ppa:eugenesan/ppa
sudo apt-get update
sudo apt install mc
### 2. Criar Bucket no MinIO

```bash
# Acessar MinIO Web UI em: https://files.senaia.in
# Ou via CLI (se mc estiver instalado):

# Configurar alias MinIO
mc alias set minio https://files.senaia.in YLBhnYvXT1vsOqlWh9Ml 8IvkSaEjjEjAPOzioeIxGQWkKkVFqQUVH97s3UpB

# Criar bucket
mc mb minio/chatwoot-baileys

# Definir política pública para upload (opcional)
mc anonymous set public minio/chatwoot-baileys

# Verificar bucket
mc ls minio/
```

## 🚀 Processo de Instalação

### Passo 1: Executar Migração do Banco

```bash
# 1. Deploy do serviço de migração
docker stack deploy -c chatwoot-baileys-migration.yml chatwoot-baileys-migrate

# 2. Monitorar logs da migração
docker service logs -f chatwoot-baileys-migrate

# 3. Aguardar conclusão (vai mostrar algo como: "Database migration completed")

# 4. Verificar se migração foi bem-sucedida
docker service ps chatwoot-baileys-migrate

# 5. Acessar PostgreSQL
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_baileys_db

# Verificar tabelas criadas
\dt

# Verificar algumas tabelas importantes
SELECT count(*) FROM accounts;
SELECT count(*) FROM users;
SELECT count(*) FROM conversations;

# Sair
\q
# 5. Remover serviço de migração após conclusão
docker stack rm chatwoot-baileys-migrate
```

### Passo 2: Deploy do Chatwoot com Baileys

```bash
# 1. Deploy do stack principal
docker stack deploy -c chatwoot-baileys-portainer.yml chatwoot-baileys

# 2. Verificar implantação
docker service ls | grep chatwoot-baileys

# 3. Monitorar logs de inicialização
docker service logs -f chatwoot-baileys_chatwoot_baileys_rails
docker service logs -f chatwoot-baileys_chatwoot_baileys_sidekiq
docker service logs -f chatwoot-baileys_baileys_api

# 4. Verificar saúde dos serviços
docker service ps chatwoot-baileys_chatwoot_baileys_rails
docker service ps chatwoot-baileys_chatwoot_baileys_sidekiq
docker service ps chatwoot-baileys_baileys_api
```

## 🌐 Acesso e Configuração

### URLs de Acesso

- **Chatwoot Baileys**: https://baileys.senaia.in
- **Traefik Dashboard**: https://traefik.senaia.in (se configurado)
- **MinIO Console**: https://files.senaia.in

### Primeiro Acesso ao Chatwoot

1. Acesse https://baileys.senaia.in
2. Crie a primeira conta de administrador
3. Configure a conta e workspace

### Configuração do WhatsApp (Baileys)

1. No painel do Chatwoot, vá em **Configurações** → **Canais**
2. Clique em **Adicionar Canal** → **WhatsApp**
3. Configure o provider Baileys:
   - **Nome**: Chatwoot Baileys
   - **URL da API**: `http://baileys_api:3025` (interno)
   - **API Key**: `194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77`

## 🔧 Comandos de Administração

### Verificar Status dos Serviços

```bash
# Status geral do stack
docker stack ps chatwoot-baileys

# Logs detalhados
docker service logs chatwoot-baileys_chatwoot_baileys_rails --since 30m
docker service logs chatwoot-baileys_baileys_api --since 30m

# Verificar recursos utilizados
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Reiniciar Serviços

```bash
# Reiniciar serviço específico
docker service update --force chatwoot-baileys_chatwoot_baileys_rails
docker service update --force chatwoot-baileys_baileys_api

# Reiniciar todo o stack
docker stack rm chatwoot-baileys
sleep 30
docker stack deploy -c chatwoot-baileys-portainer.yml chatwoot-baileys
```

### Backup e Manutenção

```bash
# Backup do banco de dados
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres_postgres" --format "{{.ID}}")
docker exec $POSTGRES_CONTAINER pg_dump -U chatwoot_database chatwoot_baileys_db > chatwoot_baileys_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup dos arquivos MinIO
mc mirror minio/chatwoot-baileys ./backup_chatwoot_baileys_$(date +%Y%m%d)

# Limpeza de logs antigos
docker system prune -f
```

## 🐛 Resolução de Problemas

### Problemas Comuns

**1. Erro de conexão com banco de dados**
```bash
# Verificar se PostgreSQL está rodando
docker service ps postgres_postgres

# Verificar se database existe
docker exec -it $(docker ps --filter "name=postgres_postgres" --format "{{.ID}}") psql -U chatwoot_database -l
```

**2. Erro de conexão com Redis**
```bash
# Verificar Redis
docker service ps redis_redis

# Testar conexão
docker exec -it $(docker ps --filter "name=redis_redis" --format "{{.ID}}") redis-cli -a J40geWtC08VoaUqoZ ping
```

**3. Problemas com MinIO/Storage**
```bash
# Verificar MinIO
docker service ps minio_minio

# Verificar bucket
mc ls minio/chatwoot-baileys
```

**4. Problemas com Baileys API**
```bash
# Verificar logs do Baileys API
docker service logs chatwoot-baileys_baileys_api --tail 100

# Verificar conectividade interna
docker exec -it $(docker ps --filter "name=chatwoot-baileys_chatwoot_baileys_rails" --format "{{.ID}}") wget -qO- http://baileys_api:3025/status
```

### Logs de Debug

```bash
# Logs com timestamp
docker service logs -t chatwoot-baileys_chatwoot_baileys_rails

# Seguir logs em tempo real
docker service logs -f chatwoot-baileys_chatwoot_baileys_rails

# Logs de todas as replicas
docker service logs chatwoot-baileys_chatwoot_baileys_rails --raw
```

## 📊 Monitoramento

### Health Checks

```bash
# Verificar health checks
docker service inspect chatwoot-baileys_chatwoot_baileys_rails --format '{{json .Spec.TaskTemplate.ContainerSpec.Healthcheck}}'

# Status de saúde dos containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Métricas de Performance

```bash
# Uso de recursos por serviço
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Informações de deploy
docker service inspect chatwoot-baileys_chatwoot_baileys_rails --format '{{json .Spec.TaskTemplate.Resources}}'
```

## 🔄 Atualizações

### Atualizar Imagem do Chatwoot

```bash
# Atualizar para nova versão
docker service update --image ghcr.io/fazer-ai/chatwoot:latest chatwoot-baileys_chatwoot_baileys_rails
docker service update --image ghcr.io/fazer-ai/chatwoot:latest chatwoot-baileys_chatwoot_baileys_sidekiq

# Atualizar Baileys API
docker service update --image ghcr.io/fazer-ai/baileys-api:latest chatwoot-baileys_baileys_api
```

### Rollback em Caso de Problema

```bash
# Rollback para versão anterior
docker service rollback chatwoot-baileys_chatwoot_baileys_rails
docker service rollback chatwoot-baileys_baileys_api
```

## 📞 Suporte

Se encontrar problemas:

1. Verifique logs dos serviços
2. Confirme se todos os pré-requisitos estão rodando
3. Verifique conectividade de rede entre serviços
4. Consulte a documentação do Docker Swarm
5. Verifique configurações de DNS/domínio

---

**✅ Instalação Concluída!**

Acesse https://baileys.senaia.in e configure seu WhatsApp Business via Baileys.