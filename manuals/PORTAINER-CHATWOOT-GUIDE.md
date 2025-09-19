# 🐳 Guia Portainer - Deploy Chatwoot Stack

Este guia detalha como fazer deploy do Chatwoot usando a interface do Portainer em modo Docker Swarm.

## ✅ Compatibilidade Portainer

**SIM, o arquivo `chatwoot-new.yml` é 100% compatível com Portainer Swarm!**

Todos os comandos Docker foram adaptados para funcionar perfeitamente na interface do Portainer.

## 📋 Pré-requisitos no Portainer

### 1. Verificar Stacks Existentes
Acesse Portainer → **Stacks** e verifique se estão rodando:
- ✅ `postgres` (PostgreSQL)
- ✅ `redis` (Redis)
- ✅ `minio` (MinIO)
- ✅ `traefik` (Traefik)

### 2. Verificar Networks
Acesse Portainer → **Networks** e confirme:
- ✅ `app_network` (overlay)
- ✅ `traefik_public` (overlay)

**Se não existirem, criar via Portainer:**
- Networks → **Add network**
- Name: `app_network`
- Driver: `overlay`
- Attachable: ✅ Yes

## 🗄️ Preparação do Banco (Via Portainer)

### 1. Acessar PostgreSQL Container
1. Portainer → **Containers**
2. Localizar container `postgres_postgres.X.XXXXX`
3. Clicar no **ícone >_** (Console)
4. Command: `/bin/bash`
5. Clicar **Connect**

### 2. Executar Comandos no Terminal
```bash
# No terminal do container PostgreSQL:
psql -U chatwoot_database -d chatwoot_database

# Comandos SQL:
CREATE DATABASE chatwoot_db;
\c chatwoot_db
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\l
\q
exit
```

## 🚀 Método 1: Migração via Portainer (Recomendado)

### 1. Criar Stack de Migração Temporária

1. **Portainer → Stacks → Add stack**
2. **Name:** `chatwoot-migration`
3. **Build method:** Web editor
4. **Docker Compose:**

```yaml
version: "3.8"

services:
  chatwoot_migrate:
    image: chatwoot/chatwoot:v4.2.0
    networks:
      - app_network
    environment:
      - NODE_ENV=production
      - RAILS_ENV=production
      - SECRET_KEY_BASE=194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77
      - POSTGRES_HOST=postgres
      - POSTGRES_USERNAME=chatwoot_database
      - POSTGRES_PASSWORD=Ma1x1x0x!!Ma1x1x0x!!
      - POSTGRES_DATABASE=chatwoot_db
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://:J40geWtC08VoaUqoZ@redis:6379
      - ACTIVE_STORAGE_SERVICE=s3_compatible
      - STORAGE_BUCKET_NAME=chatwoot
      - STORAGE_ACCESS_KEY_ID=YLBhnYvXT1vsOqlWh9Ml
      - STORAGE_SECRET_ACCESS_KEY=8IvkSaEjjEjAPOzioeIxGQWkKkVFqQUVH97s3UpB
      - STORAGE_REGION=us-east-1
      - STORAGE_ENDPOINT=https://files.senaia.in
      - STORAGE_FORCE_PATH_STYLE=true
    command: bundle exec rails db:chatwoot_prepare
    deploy:
      mode: replicated
      replicas: 1
      restart_policy:
        condition: none  # Não reiniciar após completar

networks:
  app_network:
    external: true
```

5. **Clicar "Deploy the stack"**

### 2. Monitorar Migração
1. **Stacks → chatwoot-migration**
2. **Container logs** (ícone 📄)
3. Aguardar mensagens:
   - "Database creation completed"
   - "Running migrations"
   - "Installation completed"

### 3. Remover Stack de Migração
1. **Stacks → chatwoot-migration**
2. **Delete this stack**

## 📦 Método 2: Deploy do Chatwoot Principal

### 1. Criar Stack Chatwoot
1. **Portainer → Stacks → Add stack**
2. **Name:** `chatwoot-new`
3. **Build method:** Web editor
4. **Copiar todo o conteúdo de `chatwoot-new.yml`**

### 2. Ambiente Variables (Opcional)
Na seção **Environment variables**, adicionar se necessário:
```
SECRET_KEY_BASE=194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77
POSTGRES_PASSWORD=Ma1x1x0x!!Ma1x1x0x!!
REDIS_PASSWORD=J40geWtC08VoaUqoZ
```

### 3. Deploy
**Clicar "Deploy the stack"**

## 🔍 Monitoramento via Portainer

### 1. Verificar Services
**Stacks → chatwoot-new → Services:**
- ✅ `chatwoot-new_chatwoot_rails` (1/1)
- ✅ `chatwoot-new_chatwoot_sidekiq` (1/1)

### 2. Verificar Logs
**Services → chatwoot-new_chatwoot_rails → Service logs**

Logs esperados:
```
=> Booting Puma
=> Rails 7.x.x application starting
=> Run `bin/rails server --help` for more startup options
Puma starting in single mode...
* Listening on http://0.0.0.0:3000
```

### 3. Verificar Health
**Services → chatwoot-new_chatwoot_rails → Tasks**
- Status deve estar **Running**
- Health deve estar **Healthy**

## 🌐 Verificação Final

### 1. Teste via Portainer
**Containers → chatwoot_rails container → Console:**
```bash
curl -I http://localhost:3000
# Deve retornar: HTTP/1.1 200 OK
```

### 2. Teste Externo
- Acessar: `https://chat.senaia.in`
- Deve carregar página de login do Chatwoot

## 🔧 Comandos Administrativos via Portainer

### Rails Console
1. **Containers → chatwoot_rails**
2. **Console → /bin/bash**
3. Executar:
```bash
bundle exec rails console
# User.count
# Account.first
# exit
```

### Restart Services
**Services → chatwoot-new_chatwoot_rails → Update service**
- Force update: ✅
- **Update service**

## ⚠️ Troubleshooting Portainer

### Problemas Comuns

#### 1. Service não sobe
**Services → chatwoot_rails → Tasks → View logs**
Verificar:
- Erros de conexão com banco
- Problemas de rede
- Recursos insuficientes

#### 2. Database Connection Error
**Verificar via Container console:**
```bash
# No container chatwoot:
nc -zv postgres 5432
# Deve retornar: Connection succeeded
```

#### 3. Redis Connection Error
```bash
# No container chatwoot:
nc -zv redis 6379
# Deve retornar: Connection succeeded
```

#### 4. SSL/Traefik Issues
**Verificar Traefik stack:**
- Services → traefik_traefik
- Service logs
- Verificar se certificate foi gerado

### Stack Rollback
**Stacks → chatwoot-new → Editor**
- Fazer alterações necessárias
- **Update the stack**

### Complete Restart
```bash
# Via terminal (se necessário):
docker stack rm chatwoot-new
# Aguardar limpeza completa
# Refazer deploy via Portainer
```

## 📱 Interface Portainer vs Terminal

| Ação | Terminal | Portainer |
|------|----------|-----------|
| Ver stacks | `docker stack ls` | **Stacks** |
| Ver services | `docker service ls` | **Services** |
| Ver containers | `docker ps` | **Containers** |
| Ver logs | `docker service logs` | **Service logs** |
| Restart service | `docker service update --force` | **Update service** |
| Remove stack | `docker stack rm` | **Delete stack** |

## 🎯 Vantagens do Portainer

1. **Interface visual** para monitoramento
2. **Logs em tempo real** com interface amigável
3. **Rollback fácil** via web interface
4. **Monitoring integrado** de recursos
5. **Gestão de volumes** visual
6. **Network management** simplificado

## 📝 Checklist Final

- [ ] PostgreSQL rodando com banco `chatwoot_db`
- [ ] Redis acessível com senha
- [ ] MinIO com bucket `chatwoot`
- [ ] Networks `app_network` e `traefik_public` criadas
- [ ] Migração executada com sucesso
- [ ] Stack `chatwoot-new` deployado
- [ ] Services healthy (1/1)
- [ ] Logs sem erros críticos
- [ ] Interface web acessível
- [ ] SSL funcionando via Traefik

**🎉 Com Portainer, todo o processo fica visual e mais fácil de gerenciar!**