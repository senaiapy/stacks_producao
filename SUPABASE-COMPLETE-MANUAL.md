# 🚀 Supabase Docker Swarm - Manual Completo

Este é o **único manual necessário** para deploy, migração, remoção e troubleshooting do Supabase em Docker Swarm.

## 📋 Comandos Rápidos

### Deploy Completo (Recomendado)
```bash
python3 supabase_manager.py deploy
```

### Remover Stack (Preserva Configurações)
```bash
python3 supabase_manager.py remove
```

### Remover Tudo (Completo)
```bash
python3 supabase_manager.py cleanup
```

### Verificar Status
```bash
python3 supabase_manager.py status
```

## 🎯 Deploy Manual Passo a Passo

### 1. Preparar Servidor
```bash
# No servidor: Criar diretórios
ssh root@seu-servidor
mkdir -p /opt/supabase/{config,db-migrations}
```

### 2. Transferir Arquivos
```bash
# Da máquina local para servidor
scp supabase/docker/volumes/api/kong.yml root@seu-servidor:/opt/supabase/config/
scp supabase/docker/volumes/logs/vector.yml root@seu-servidor:/opt/supabase/config/
scp supabase/docker/volumes/pooler/pooler.exs root@seu-servidor:/opt/supabase/config/
#scp supabase.yml root@seu-servidor:/opt/supabase/
```

### 3. Criar Docker Configs
```bash
# No servidor
cd /opt/supabase
docker config create supabase_kong_config config/kong.yml
docker config create supabase_vector_config config/vector.yml
docker config create supabase_pooler_config config/pooler.exs
```

### 4. Preparar Banco de Dados
```bash
# Conectar ao PostgreSQL existente
docker exec -it $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database

psql -U chatwoot_database -d chatwoot_database

# Executar no PostgreSQL:
CREATE USER supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_storage_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_functions_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER authenticator WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
CREATE USER supabase_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';

GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_storage_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_functions_admin;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO authenticator;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_admin;

CREATE SCHEMA _realtime;
CREATE SCHEMA _analytics;
CREATE SCHEMA storage;
CREATE SCHEMA auth;
CREATE SCHEMA extensions;

GRANT ALL ON SCHEMA _realtime TO supabase_auth_admin;
GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;

CREATE EXTENSION vector;
CREATE EXTENSION pg_stat_statements;
CREATE EXTENSION pgcrypto;

CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);

\q
```

### 5. Deploy Stack
```bash
# No servidor
cd /opt/supabase
docker stack deploy -c supabase.yml supabase
```

### 6. Verificar Deploy
```bash
# Verificar serviços
docker service ls | grep supabase

# Monitorar logs
docker service logs supabase_auth
docker service logs supabase_storage
```

## 🗑️ Remoção Manual

### Remover Apenas Stack (Preserva Configurações)
```bash
# Remove apenas os serviços
docker stack rm supabase
```

### Remoção Completa
```bash
# 1. Remover stack
docker stack rm supabase

# 2. Remover configs
docker config rm supabase_kong_config supabase_vector_config supabase_pooler_config

# 3. Remover volumes (ATENÇÃO: Remove dados!)
docker volume rm supabase_storage supabase_functions

# 4. Remover arquivos do servidor
rm -rf /opt/supabase
```

## 🔍 Verificação e Status

### Verificar Serviços
```bash
# Listar serviços Supabase
docker service ls | grep supabase

# Status detalhado
docker service ps supabase_studio
docker service ps supabase_auth
```

### Verificar Logs
```bash
# Logs de erros
docker service logs supabase_auth 2>&1 | grep -i error
docker service logs supabase_storage 2>&1 | grep -i error

# Monitorar em tempo real
docker service logs -f supabase_studio
```

### Testar APIs
```bash
# Testar Studio
curl -I https://studio.senaia.in

# Testar API
curl -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao" https://supabase.senaia.in/rest/v1/
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Config não encontrado
**Erro**: `config not found: supabase_vector_config`
**Solução**: Recriar configs
```bash
cd /opt/supabase
docker config create supabase_kong_config config/kong.yml
docker config create supabase_vector_config config/vector.yml
docker config create supabase_pooler_config config/pooler.exs
```

#### 2. Erro de autenticação no banco
**Erro**: `password authentication failed for user "supabase_auth_admin"`
**Solução**: Criar usuários no banco
```bash
docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c "CREATE USER supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';"
```

#### 3. Serviços 0/1
**Solução**: Restart forçado
```bash
docker service update --force supabase_auth
docker service update --force supabase_storage
```

#### 4. Studio não carrega
**Solução**: Verificar dependências
```bash
# Verificar analytics
docker service logs supabase_analytics

# Restart studio
docker service update --force supabase_studio
```

### Comandos de Recovery

#### Restart Individual
```bash
docker service update --force supabase_studio
docker service update --force supabase_auth
docker service update --force supabase_storage
```

#### Restart Completo da Stack
```bash
docker stack rm supabase
sleep 30
docker stack deploy -c /opt/supabase/supabase.yml supabase
```

## 🌐 Acesso aos Serviços

### URLs Principais
- **Studio Dashboard**: https://studio.senaia.in
- **API REST**: https://supabase.senaia.in/rest/v1/
- **Auth API**: https://supabase.senaia.in/auth/v1/
- **Storage API**: https://supabase.senaia.in/storage/v1/
- **Connection Pooler**: pooler.senaia.in:6543

### Credenciais Padrão
- **Database User**: supabase_admin
- **Database Password**: Ma1x1x0x!!Ma1x1x0x!!
- **Database Name**: chatwoot_database
- **JWT Secret**: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz

### Chaves API
- **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao`
- **Service Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI`

## 📊 Checklist Final

### Pré-requisitos
- [ ] Docker Swarm inicializado
- [ ] Redes `app_network` e `traefik_public` criadas
- [ ] PostgreSQL stack rodando
- [ ] Traefik stack ativo

### Deploy
- [ ] Arquivos transferidos para `/opt/supabase/`
- [ ] Docker configs criados
- [ ] Usuários do banco criados
- [ ] Schemas criados
- [ ] Stack deployada

### Verificação
- [ ] Todos os serviços 1/1
- [ ] Studio acessível via HTTPS
- [ ] APIs respondendo
- [ ] Logs sem erros críticos

---

**Este é o manual único e completo para Supabase Docker Swarm. Use `python3 supabase_manager.py` para automação.**