# Manual Completo - Docker Swarm Stack com Portainer

Este manual descreve como resolver o erro de migração do Supabase e implantar o Chatwoot com Baileys.

## 🚨 Problema Resolvido: Supabase Migration Error

**Erro anterior:**
```
"root" execution of the PostgreSQL server is not permitted.
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed
```

**✅ Solução:** O `supabase-migration.yml` foi corrigido para usar o PostgreSQL existente do stack ao invés de tentar executar um PostgreSQL separado como root.

## 📋 Pré-requisitos

Certifique-se de que os seguintes serviços estejam **rodando** no Docker Swarm:

- ✅ **PostgreSQL** (stack `postgres`)
- ✅ **Redis** (stack `redis`)
- ✅ **MinIO** (stack `minio`)
- ✅ **Traefik** (stack `traefik`)

### Verificar Serviços Ativos

```bash
# Listar todos os serviços ativos
docker service ls

# Verificar redes
docker network ls | grep -E "(app_network|traefik_public)"

# Verificar saúde dos serviços principais
docker service ps postgres_postgres
docker service ps redis_redis
docker service ps minio_minio
docker service ps traefik_traefik
```

## 🔧 Migração do Supabase (CORRIGIDA)

### 1. Executar Migração Supabase Corrigida


#creata a database supabase_db

#Acessar o console do container do Postgres
psql -U chatwoot_database -d chatwoot_database

 psql -U chatwoot_database -d postgres

  # 2. Inside PostgreSQL, run these 
  commands:
  CREATE DATABASE supabase_db;
  GRANT ALL PRIVILEGES ON DATABASE
  supabase_db TO chatwoot_database;

  # Switch to supabase_db
  \c supabase_db

  # Create extensions
  CREATE EXTENSION IF NOT EXISTS vector;
  CREATE EXTENSION IF NOT EXISTS
  pg_stat_statements;
  CREATE EXTENSION IF NOT EXISTS
  pg_trgm;
  CREATE EXTENSION IF NOT EXISTS
  pgcrypto;
  #CREATE EXTENSION IF NOT EXISTS pgjwt;
  CREATE EXTENSION IF NOT EXISTS
  "uuid-ossp";

  # Create schemas
  CREATE SCHEMA IF NOT EXISTS auth;
  CREATE SCHEMA IF NOT EXISTS storage;
  CREATE SCHEMA IF NOT EXISTS realtime;
  CREATE SCHEMA IF NOT EXISTS
  graphql_public;
  CREATE SCHEMA IF NOT EXISTS
  extensions;

  # Create supabase_admin user
  CREATE ROLE supabase_admin LOGIN
  SUPERUSER PASSWORD
  'Ma1x1x0x!!Ma1x1x0x!!';

  # Create other roles
  CREATE ROLE anon NOLOGIN;
  CREATE ROLE authenticated NOLOGIN;
  CREATE ROLE service_role NOLOGIN
  SUPERUSER;
  CREATE ROLE authenticator LOGIN
  PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!'
  NOINHERIT;

  # Grant permissions
  GRANT anon TO authenticator;
  GRANT authenticated TO authenticator;
  GRANT service_role TO authenticator;

  # Make supabase_admin owner of schemas
  ALTER SCHEMA auth OWNER TO
  supabase_admin;
  ALTER SCHEMA storage OWNER TO
  supabase_admin;
  ALTER SCHEMA realtime OWNER TO
  supabase_admin;
  ALTER SCHEMA graphql_public OWNER TO
  supabase_admin;

  # Exit PostgreSQL
  \q

```bash
# Deploy da migração corrigida
docker stack deploy -c supabase-migration.yml supabase-migrate

# Monitorar logs (vai mostrar progresso detalhado)
docker service logs -f supabase-migrate_supabase_migrate

# Aguardar mensagem: "Supabase database setup completed successfully!"

# Verificar status
docker service ps supabase-migrate_supabase_migrate

# Remover após conclusão
docker stack rm supabase-migrate
```

### 2. Verificar Database Criada

```bash
# Acessar PostgreSQL
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres_postgres" --format "{{.ID}}")
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -l

# Deve mostrar na lista:
# supabase_db | chatwoot_database | UTF8
```

### O que a Migração Corrigida Faz:

✅ **Conecta ao PostgreSQL existente** (não executa PostgreSQL separado)
✅ **Cria database `supabase_db`**
✅ **Instala extensões necessárias**: vector, pg_stat_statements, pg_trgm, pgcrypto, pgjwt, uuid-ossp
✅ **Cria schemas do Supabase**: auth, storage, realtime, graphql_public, extensions, pgsodium, vault
✅ **Cria roles do Supabase**: anon, authenticated, service_role, supabase_admin, authenticator
✅ **Configura permissões e RLS**

## 🗄️ Preparação para Chatwoot Baileys

### 1. Criar Database do Chatwoot Baileys

```bash
# Acessar PostgreSQL
POSTGRES_CONTAINER=$(docker ps --filter "name=postgres_postgres" --format "{{.ID}}")
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -d postgres

# Criar database
CREATE DATABASE chatwoot_baileys_db;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_baileys_db TO chatwoot_database;

# Habilitar extensão pgvector
\c chatwoot_baileys_db
CREATE EXTENSION IF NOT EXISTS vector;

# Verificar criação
\l

# Sair
\q
```

### 2. Criar Bucket MinIO

```bash
# Acessar MinIO Web UI: https://files.senaia.in
# Usuário: BN0t99DuuhNtbkiJQcHP
# Senha: enCejRo4tU9tmvCWa5LuwAfTods0vNfYlOMbXdyB

# Ou via CLI (se mc estiver instalado):
mc alias set minio https://files.senaia.in BN0t99DuuhNtbkiJQcHP enCejRo4tU9tmvCWa5LuwAfTods0vNfYlOMbXdyB

# Criar bucket
mc mb minio/chatwoot-baileys

# Verificar
mc ls minio/
```

## 🚀 Instalação Chatwoot com Baileys

### Passo 1: Migração Database Chatwoot

```bash
# Deploy migração
docker stack deploy -c chatwoot-baileys-migration.yml chatwoot-baileys-migrate

# Monitorar logs
docker service logs -f chatwoot-baileys-migrate_chatwoot_baileys_migrate

# Aguardar conclusão
# Remover após sucesso
docker stack rm chatwoot-baileys-migrate
```

### Passo 2: Deploy Stack Principal

```bash
# Deploy Chatwoot com Baileys
docker stack deploy -c chatwoot-baileys-portainer.yml chatwoot-baileys

# Verificar serviços
docker service ls | grep chatwoot-baileys

# Monitorar logs de inicialização
docker service logs -f chatwoot-baileys_chatwoot_baileys_rails
docker service logs -f chatwoot-baileys_baileys_api
```

## 🌐 Configuração e Acesso

### URLs de Acesso

- **Chatwoot Baileys**: https://baileys.senaia.in
- **MinIO Console**: https://files.senaia.in

### Configuração WhatsApp Baileys

1. Acesse https://baileys.senaia.in
2. Crie conta administrador
3. Configurações → Canais → Adicionar Canal → WhatsApp
4. Configure:
   - **Nome**: Chatwoot Baileys
   - **URL API**: `http://baileys_api:3025`
   - **API Key**: `194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77`

## 🐛 Resolução de Problemas

### Problemas Supabase

**1. Erro "root execution not permitted"**
```bash
# ✅ RESOLVIDO na nova versão
# A migração agora usa cliente PostgreSQL ao invés de executar servidor
```

**2. Verificar migração Supabase**
```bash
# Verificar database criada
docker exec -it $(docker ps --filter "name=postgres_postgres" --format "{{.ID}}") psql -U chatwoot_database -l | grep supabase

# Verificar roles criadas
docker exec -it $(docker ps --filter "name=postgres_postgres" --format "{{.ID}}") psql -U chatwoot_database -d supabase_db -c "\du"
```

### Problemas Chatwoot Baileys

**1. Erro conexão banco**
```bash
# Verificar PostgreSQL
docker service ps postgres_postgres

# Testar conectividade
docker run --rm --network app_network postgres:16-alpine pg_isready -h postgres -p 5432
```

**2. Erro conexão Redis**
```bash
# Verificar Redis
docker service ps redis_redis

# Testar conexão
docker exec -it $(docker ps --filter "name=redis_redis" --format "{{.ID}}") redis-cli -a J40geWtC08VoaUqoZ ping
```

**3. Problemas Baileys API**
```bash
# Logs detalhados
docker service logs chatwoot-baileys_baileys_api --tail 100

# Testar conectividade interna
docker exec -it $(docker ps --filter "name=chatwoot-baileys_chatwoot_baileys_rails" --format "{{.ID}}") wget -qO- http://baileys_api:3025/status
```

## 📊 Monitoramento

### Status dos Serviços

```bash
# Status geral
docker stack ps chatwoot-baileys
docker stack ps supabase (se usando)

# Health checks
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Recursos
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Logs Úteis

```bash
# Chatwoot Rails
docker service logs chatwoot-baileys_chatwoot_baileys_rails --since 30m

# Baileys API
docker service logs chatwoot-baileys_baileys_api --since 30m

# PostgreSQL
docker service logs postgres_postgres --since 30m
```

## 🔄 Manutenção

### Backup

```bash
# Backup Supabase
docker exec $(docker ps --filter "name=postgres_postgres" --format "{{.ID}}") pg_dump -U chatwoot_database supabase_db > supabase_backup_$(date +%Y%m%d).sql

# Backup Chatwoot Baileys
docker exec $(docker ps --filter "name=postgres_postgres" --format "{{.ID}}") pg_dump -U chatwoot_database chatwoot_baileys_db > chatwoot_baileys_backup_$(date +%Y%m%d).sql

# Backup MinIO
mc mirror minio/chatwoot-baileys ./backup_baileys_$(date +%Y%m%d)
```

### Atualizações

```bash
# Atualizar Chatwoot
docker service update --image ghcr.io/fazer-ai/chatwoot:latest chatwoot-baileys_chatwoot_baileys_rails
docker service update --image ghcr.io/fazer-ai/chatwoot:latest chatwoot-baileys_chatwoot_baileys_sidekiq

# Atualizar Baileys API
docker service update --image ghcr.io/fazer-ai/baileys-api:latest chatwoot-baileys_baileys_api
```

---

## ✅ Resumo da Solução

**Problema Original**: supabase-migration.yml tentava executar PostgreSQL como root
**Solução**: Migração corrigida conecta ao PostgreSQL existente do stack
**Resultado**: Migração bem-sucedida sem conflitos de permissão

**Stack Completo**:
1. ✅ Supabase: Database e schemas criados corretamente
2. ✅ Chatwoot Baileys: Deploy funcional com WhatsApp integration
3. ✅ Sem conflitos de porta ou permissão
4. ✅ Traefik: SSL automático para https://baileys.senaia.in

**Acesso Final**: https://baileys.senaia.in