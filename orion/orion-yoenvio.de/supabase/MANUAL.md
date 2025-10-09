# Supabase Docker Swarm - Complete Fix Manual
# Server: 89.163.146.106 (yoenvio.de)

Este manual contém todas as correções necessárias para resolver problemas comuns do Supabase em Docker Swarm, incluindo a correção do serviço `supabase_auth`.

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)
3. [Fix Completo - Todos os Serviços](#fix-completo---todos-os-serviços)
4. [Fix Específico - supabase_auth](#fix-específico---supabase_auth)
5. [Verificação Final](#verificação-final)
6. [Comandos de Manutenção](#comandos-de-manutenção)

---

## Pré-requisitos

### Informações do Servidor
- **IP**: 89.163.146.106
- **Usuário**: root
- **Senha**: @450Ab6606289828server
- **Domínio**: yoenvio.de

### Credenciais do Banco de Dados
- **Password**: 949d2fafe7dee2ab620252a58dbb6bdd
- **JWT Secret**: 11b614eb3cb2373fdf35f510db20bcbc0c55db74

### Arquivos Necessários
- Stack file: `/root/supabase.yaml`
- Volume base: `/root/supabase/docker/volumes/`

---

## Problemas Comuns e Soluções

### Problema 1: Analytics Service Failing (database "_supabase" does not exist)

**Erro:**
```
FATAL 3D000 (invalid_catalog_name) database "_supabase" does not exist
```

**Solução:**
```bash
# Conectar ao container do banco
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
-- Criar database _supabase
CREATE DATABASE _supabase;

-- Criar schema _analytics
\c _supabase
CREATE SCHEMA IF NOT EXISTS _analytics;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE _supabase TO supabase_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_admin;
EOF

# Reiniciar serviço
docker service update --force supabase_analytics
```

---

### Problema 2: Database Service Failing (bind source path does not exist)

**Erro:**
```
invalid mount config for type "bind": bind source path does not exist: /root/supabase/docker/volumes/db/data
```

**Solução:**
```bash
# Criar diretório de dados
mkdir -p /root/supabase/docker/volumes/db/data

# Definir permissões corretas (PostgreSQL usa UID 999)
chown -R 999:999 /root/supabase/docker/volumes/db/data
chmod 700 /root/supabase/docker/volumes/db/data

# Reiniciar serviço
docker service update --force supabase_db
```

---

### Problema 3: Auth/REST Services Failing (password authentication failed)

**Erro:**
```
FATAL: password authentication failed for user "supabase_auth_admin"
FATAL: password authentication failed for user "authenticator"
```

**Causa:** Usuários do banco de dados não foram criados automaticamente.

**Solução:** Ver seção [Fix Completo](#fix-completo---todos-os-serviços) abaixo.

---

## Fix Completo - Todos os Serviços

### Passo 1: Remover Stack Existente

```bash
# Conectar ao servidor
ssh root@89.163.146.106

# Remover stack
docker stack rm supabase

# Aguardar remoção completa
sleep 30
```

---

### Passo 2: Limpar Dados Antigos (CUIDADO: Remove todos os dados!)

```bash
# Backup dos dados (se necessário)
tar -czf /root/supabase_backup_$(date +%Y%m%d_%H%M%S).tar.gz /root/supabase/docker/volumes/db/data

# Remover dados antigos
rm -rf /root/supabase/docker/volumes/db/data

# Recriar diretório
mkdir -p /root/supabase/docker/volumes/db/data
chown -R 999:999 /root/supabase/docker/volumes/db/data
chmod 700 /root/supabase/docker/volumes/db/data
```

---

### Passo 3: Verificar Arquivos de Inicialização

```bash
# Verificar se os arquivos SQL existem
ls -la /root/supabase/docker/volumes/db/*.sql

# Devem existir:
# - _supabase.sql
# - jwt.sql
# - logs.sql
# - pooler.sql
# - realtime.sql
# - roles.sql
# - webhooks.sql
```

Se algum arquivo estiver faltando, copie da configuração original do Supabase.

---

### Passo 4: Criar Volume Docker Config (se não existir)

```bash
# Verificar se o volume existe
docker volume ls | grep supabase_db_config

# Se não existir, criar
docker volume create supabase_db_config
```

---

### Passo 5: Redeploy da Stack

```bash
# Deploy
cd /root
docker stack deploy -c supabase.yaml supabase

# Aguardar inicialização (importante!)
sleep 60
```

---

### Passo 6: Verificar Status

```bash
# Listar serviços
docker service ls | grep supabase

# Verificar logs do banco
docker service logs supabase_db --tail 50
```

**Resultado Esperado:**
- Todos os serviços devem estar 1/1, exceto possivelmente `supabase_auth`

---

### Passo 7: Criar Database e Schemas Adicionais

```bash
# Conectar ao PostgreSQL
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
-- Criar database _supabase
CREATE DATABASE IF NOT EXISTS _supabase;

-- Conectar ao _supabase
\c _supabase

-- Criar schemas
CREATE SCHEMA IF NOT EXISTS _analytics;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE _supabase TO supabase_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_admin;

-- Voltar ao postgres
\c postgres

-- Verificar schemas existentes
SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema';
EOF
```

---

### Passo 8: Reiniciar Serviços que Falharam

```bash
# Verificar serviços com problemas
docker service ls | grep supabase | grep '0/1'

# Reiniciar analytics se necessário
docker service update --force supabase_analytics

# Aguardar
sleep 20

# Verificar status final
docker service ls | grep supabase
```

---

## Fix Específico - supabase_auth

O serviço `supabase_auth` tem requisitos especiais de permissões no banco de dados.

### Problema: ERROR: must be owner of function uid (SQLSTATE 42501)

**Causa:** O GoTrue (supabase_auth) tenta criar funções no schema `auth`, mas precisa de permissões de superusuário ou ownership do schema.

---

### Solução 1: Fix Manual de Permissões (Recomendado)

```bash
# Conectar ao servidor
ssh root@89.163.146.106

# Executar fix de permissões
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
-- Garantir que o schema auth existe
CREATE SCHEMA IF NOT EXISTS auth;

-- Transferir ownership do schema para supabase_auth_admin
ALTER SCHEMA auth OWNER TO supabase_auth_admin;

-- Conceder todas as permissões
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
GRANT ALL ON SCHEMA auth TO authenticator;

-- Remover funções existentes que podem causar conflito
DROP FUNCTION IF EXISTS auth.uid() CASCADE;
DROP FUNCTION IF EXISTS auth.role() CASCADE;

-- Conceder permissões para criar funções
GRANT CREATE ON SCHEMA auth TO supabase_auth_admin;

-- Se as tabelas já existirem, transferir ownership
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'auth'
    LOOP
        EXECUTE 'ALTER TABLE auth.' || quote_ident(r.tablename) || ' OWNER TO supabase_auth_admin';
    END LOOP;
END $$;

-- Conceder permissões em todas as tabelas
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO supabase_auth_admin;

-- Definir permissões padrão para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO supabase_auth_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON SEQUENCES TO supabase_auth_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON FUNCTIONS TO supabase_auth_admin;
EOF

# Reiniciar serviço auth
docker service update --force supabase_auth

# Aguardar e verificar
sleep 30
docker service logs supabase_auth --tail 20
```

---

### Solução 2: Recriar Database Completo (Se Solução 1 Falhar)

**⚠️ ATENÇÃO: Esta solução apaga TODOS os dados!**

```bash
# Remover stack
docker stack rm supabase
sleep 30

# Remover dados completamente
rm -rf /root/supabase/docker/volumes/db/data

# Recriar estrutura
mkdir -p /root/supabase/docker/volumes/db/data
chown -R 999:999 /root/supabase/docker/volumes/db/data
chmod 700 /root/supabase/docker/volumes/db/data

# Redeploy
docker stack deploy -c /root/supabase.yaml supabase

# Aguardar inicialização COMPLETA (importante!)
sleep 120

# Verificar se o banco inicializou corretamente
docker service logs supabase_db --tail 50

# Criar database _supabase novamente
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
CREATE DATABASE IF NOT EXISTS _supabase;
\c _supabase
CREATE SCHEMA IF NOT EXISTS _analytics;
GRANT ALL PRIVILEGES ON DATABASE _supabase TO supabase_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_admin;
EOF

# Reiniciar analytics
docker service update --force supabase_analytics
sleep 20

# Verificar status
docker service ls | grep supabase
```

---

### Solução 3: Desabilitar Auth Service (Última Opção)

Se o auth não for crítico para sua aplicação:

```bash
# Editar o arquivo supabase.yaml
nano /root/supabase.yaml

# Comentar a seção completa do serviço auth:
# Procurar por:
#   auth:
#     image: supabase/gotrue:v2.176.1
#     ...
# E adicionar # no início de cada linha

# Ou remover apenas o serviço auth
docker service rm supabase_auth

# Nota: Kong gateway ainda funcionará, mas sem autenticação
```

---

## Verificação Final

### Checklist Completo

```bash
# 1. Verificar todos os serviços
docker service ls | grep supabase

# Resultado esperado (12-13 serviços 1/1):
# supabase_analytics    1/1
# supabase_auth         1/1  (ou 0/1 se não corrigido)
# supabase_db           1/1
# supabase_functions    1/1
# supabase_imgproxy     1/1
# supabase_kong         1/1
# supabase_meta         1/1
# supabase_realtime     1/1
# supabase_rest         1/1
# supabase_storage      1/1
# supabase_studio       1/1
# supabase_supavisor    1/1
# supabase_vector       1/1
```

```bash
# 2. Testar acesso ao Studio
curl -I https://supabase.yoenvio.de

# Deve retornar: HTTP/2 200
```

```bash
# 3. Verificar banco de dados
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres -c '\l'

# Devem existir:
# - postgres
# - _supabase
# - template0
# - template1
```

```bash
# 4. Verificar schemas
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres -c '\dn'

# Devem existir:
# - public
# - auth
# - storage
# - _realtime
# - extensions
```

```bash
# 5. Testar API REST
curl -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.yzIH3Tb0PeX8SIiIQruWNNjFxRi6TIgV3C85pBgpNaA" \
  https://supabase.yoenvio.de/rest/v1/

# Deve retornar informações sobre a API
```

---

## Comandos de Manutenção

### Reiniciar Serviço Específico

```bash
# Syntax
docker service update --force supabase_SERVICE_NAME

# Exemplos
docker service update --force supabase_auth
docker service update --force supabase_analytics
docker service update --force supabase_db
```

---

### Reiniciar Todos os Serviços Supabase

```bash
# Listar todos os serviços e reiniciar
for service in $(docker service ls --filter name=supabase --format "{{.Name}}"); do
  echo "Reiniciando $service..."
  docker service update --force $service
  sleep 5
done
```

---

### Ver Logs de Serviços

```bash
# Ver logs de um serviço específico
docker service logs supabase_SERVICE_NAME --tail 50 --follow

# Ver logs com timestamp
docker service logs supabase_SERVICE_NAME --timestamps --tail 100

# Ver apenas erros
docker service logs supabase_SERVICE_NAME 2>&1 | grep -iE '(error|fatal|fail)'
```

---

### Verificar Status Detalhado

```bash
# Status de um serviço
docker service ps supabase_SERVICE_NAME --no-trunc

# Ver recursos utilizados
docker stats --no-stream | grep supabase

# Inspecionar serviço
docker service inspect supabase_SERVICE_NAME --pretty
```

---

### Backup do Banco de Dados

```bash
# Backup completo
docker exec $(docker ps -q -f name=supabase_db) pg_dumpall -U supabase_admin > /root/supabase_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup de database específico
docker exec $(docker ps -q -f name=supabase_db) pg_dump -U supabase_admin -d postgres > /root/postgres_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup de arquivos
tar -czf /root/supabase_volumes_$(date +%Y%m%d_%H%M%S).tar.gz /root/supabase/docker/volumes/
```

---

### Restore do Banco de Dados

```bash
# Restore completo
cat /root/supabase_backup_TIMESTAMP.sql | docker exec -i $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres

# Restore de database específico
cat /root/postgres_backup_TIMESTAMP.sql | docker exec -i $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres
```

---

### Limpeza de Recursos

```bash
# Remover containers parados
docker container prune -f

# Remover imagens não utilizadas
docker image prune -a -f

# Remover volumes não utilizados (CUIDADO!)
docker volume prune -f

# Remover networks não utilizadas
docker network prune -f
```

---

## URLs de Acesso

- **Studio (UI)**: https://supabase.yoenvio.de
- **Kong Gateway**: https://supabase.yoenvio.de
- **REST API**: https://supabase.yoenvio.de/rest/v1/
- **Auth API**: https://supabase.yoenvio.de/auth/v1/
- **Storage API**: https://supabase.yoenvio.de/storage/v1/

---

## Credenciais

### API Keys

**Anon Key** (público):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.yzIH3Tb0PeX8SIiIQruWNNjFxRi6TIgV3C85pBgpNaA
```

**Service Role Key** (privado):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogInNlcnZpY2Vfcm9sZSIsCiAgImlzcyI6ICJzdXBhYmFzZSIsCiAgImlhdCI6IDE3MTUwNTA4MDAsCiAgImV4cCI6IDE4NzI4MTcyMDAKfQ.Pci2Eil44xwiIGv20iDPalEeuLEXi8wFJHj2mYmm6eY
```

### Database

- **Host**: db (interno) ou 89.163.146.106 (externo via SSH tunnel)
- **Port**: 5432
- **Database**: postgres
- **User**: supabase_admin
- **Password**: 949d2fafe7dee2ab620252a58dbb6bdd

### JWT Secret
```
11b614eb3cb2373fdf35f510db20bcbc0c55db74
```

---

## Troubleshooting Adicional

### Problema: Serviços Reiniciando Constantemente

```bash
# Verificar logs para identificar o problema
docker service logs supabase_SERVICE_NAME --tail 100

# Verificar recursos do sistema
free -h
df -h
docker system df
```

### Problema: Slow Queries / Performance Issues

```bash
# Conectar ao banco e verificar conexões
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres -c 'SELECT count(*) FROM pg_stat_activity;'

# Ver queries ativas
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres -c 'SELECT pid, usename, application_name, state, query FROM pg_stat_activity WHERE state != '\''idle'\'';'
```

### Problema: Porta em Uso

```bash
# Verificar portas em uso
netstat -tlnp | grep :5432
netstat -tlnp | grep :8000

# Parar serviço que está usando a porta
systemctl stop postgresql  # Se PostgreSQL local estiver rodando
```

---

## Script Automatizado - Deploy Completo

Salve este script como `/root/deploy_supabase.sh`:

```bash
#!/bin/bash

echo "🚀 Supabase Deploy Completo - yoenvio.de"
echo "=========================================="

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Passo 1: Remover stack existente
echo -e "${YELLOW}📦 Removendo stack existente...${NC}"
docker stack rm supabase
sleep 30

# Passo 2: Criar diretórios
echo -e "${YELLOW}📁 Criando estrutura de diretórios...${NC}"
mkdir -p /root/supabase/docker/volumes/db/data
mkdir -p /root/supabase/docker/volumes/storage
mkdir -p /root/supabase/docker/volumes/functions

# Passo 3: Definir permissões
echo -e "${YELLOW}🔐 Definindo permissões...${NC}"
chown -R 999:999 /root/supabase/docker/volumes/db/data
chmod 700 /root/supabase/docker/volumes/db/data

# Passo 4: Verificar volume config
echo -e "${YELLOW}📦 Verificando volumes Docker...${NC}"
if ! docker volume ls | grep -q supabase_db_config; then
    docker volume create supabase_db_config
    echo -e "${GREEN}✓ Volume supabase_db_config criado${NC}"
fi

# Passo 5: Deploy
echo -e "${YELLOW}🚀 Deploying stack...${NC}"
cd /root
docker stack deploy -c supabase.yaml supabase

# Passo 6: Aguardar inicialização
echo -e "${YELLOW}⏳ Aguardando inicialização (60s)...${NC}"
sleep 60

# Passo 7: Criar database _supabase
echo -e "${YELLOW}💾 Criando database _supabase...${NC}"
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
CREATE DATABASE IF NOT EXISTS _supabase;
\c _supabase
CREATE SCHEMA IF NOT EXISTS _analytics;
GRANT ALL PRIVILEGES ON DATABASE _supabase TO supabase_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_admin;
EOF

# Passo 8: Reiniciar analytics
echo -e "${YELLOW}🔄 Reiniciando analytics...${NC}"
docker service update --force supabase_analytics
sleep 20

# Passo 9: Fix auth permissions
echo -e "${YELLOW}🔧 Configurando permissões do auth...${NC}"
docker exec $(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
CREATE SCHEMA IF NOT EXISTS auth;
ALTER SCHEMA auth OWNER TO supabase_auth_admin;
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
DROP FUNCTION IF EXISTS auth.uid() CASCADE;
DROP FUNCTION IF EXISTS auth.role() CASCADE;
GRANT CREATE ON SCHEMA auth TO supabase_auth_admin;
EOF

# Passo 10: Reiniciar auth
echo -e "${YELLOW}🔄 Reiniciando auth...${NC}"
docker service update --force supabase_auth
sleep 20

# Passo 11: Status final
echo -e "${GREEN}=========================================="
echo -e "✅ Deploy concluído!"
echo -e "==========================================${NC}"
echo ""
docker service ls | grep supabase

echo ""
echo -e "${GREEN}🌐 Acesso: https://supabase.yoenvio.de${NC}"
```

**Uso:**
```bash
chmod +x /root/deploy_supabase.sh
/root/deploy_supabase.sh
```

---

## Suporte

Para problemas adicionais, verifique:
1. Logs dos serviços: `docker service logs supabase_SERVICE_NAME`
2. Status dos containers: `docker service ps supabase_SERVICE_NAME --no-trunc`
3. Documentação oficial: https://supabase.com/docs/guides/self-hosting/docker

---

**Criado em**: 2025-10-08
**Servidor**: 89.163.146.106 (yoenvio.de)
**Stack File**: /root/supabase.yaml
**Versão Supabase**: Studio 2025.06.30, GoTrue v2.176.1, PostgreSQL 15.8.1
