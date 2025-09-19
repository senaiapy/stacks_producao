# 📋 Manual de Migração e Inicialização Chatwoot

Este manual detalha o processo completo para inicializar e migrar o banco de dados do Chatwoot usando o arquivo `chatwoot-new.yml`.

## 🔧 Pré-requisitos

Antes de iniciar a migração do Chatwoot, certifique-se de que os seguintes serviços estão rodando:

### 1. Verificar Serviços Necessários
```bash
# Verificar se todos os serviços dependentes estão ativos
docker service ls | grep -E "(postgres|redis|minio)"

# Deve mostrar:
# postgres_postgres    1/1      Running
# redis_redis          1/1      Running
# minio_minio          1/1      Running
```

### 2. Verificar Redes Docker
```bash
# Verificar se as redes existem
docker network ls | grep -E "(app_network|traefik_public)"

# Se não existirem, criar:
docker network create --driver=overlay app_network
docker network create --driver=overlay traefik_public
```

## 🗄️ Preparação do Banco de Dados

### 1. Acessar PostgreSQL e Criar Database
```bash
# Encontrar o container do PostgreSQL
POSTGRES_CONTAINER=$(docker ps --format "table {{.Names}}" | grep postgres | head -1)

# Acessar o PostgreSQL
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_database
```

### 2. Comandos SQL no PostgreSQL
```sql
-- Criar o banco específico do Chatwoot (se não existir)
CREATE DATABASE chatwoot_db;

-- Verificar se o banco foi criado
\l

-- Conectar ao banco do Chatwoot
\c chatwoot_db

-- Habilitar extensão pgvector (necessária para funcionalidades de IA)
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilitar outras extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Verificar extensões instaladas
\dx

-- Sair do PostgreSQL
\q
```

### 3. Verificar Conexão Redis
```bash
# Encontrar container do Redis
REDIS_CONTAINER=$(docker ps --format "table {{.Names}}" | grep redis | head -1)

# Testar conexão Redis
docker exec -it $REDIS_CONTAINER redis-cli -a J40geWtC08VoaUqoZ ping

# Deve retornar: PONG
```

### 4. Verificar MinIO e Criar Bucket
```bash
# Acessar MinIO via web: https://minio.senaia.in
# Credenciais: marceluphd / 1:7khB-=2898

# Ou via linha de comando (se mc estiver instalado):
# mc alias set minio https://files.senaia.in marceluphd "1:7khB-=2898"
# mc mb minio/chatwoot
```

## 🚀 Migração do Banco de Dados

### Método 1: Container Temporário para Migração (Recomendado)

```bash
# 1. Criar serviço temporário para migração
docker service create --name chatwoot-migrate-new \
  --network app_network \
  --restart-condition none \
  --mount type=tmpfs,destination=/tmp \
  --env NODE_ENV=production \
  --env RAILS_ENV=production \
  --env SECRET_KEY_BASE=194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77 \
  --env POSTGRES_HOST=postgres \
  --env POSTGRES_USERNAME=chatwoot_database \
  --env POSTGRES_PASSWORD="Ma1x1x0x!!Ma1x1x0x!!" \
  --env POSTGRES_DATABASE=chatwoot_db \
  --env POSTGRES_PORT=5432 \
  --env REDIS_URL=redis://:J40geWtC08VoaUqoZ@redis:6379 \
  --env REDIS_PASSWORD=J40geWtC08VoaUqoZ \
  --env ACTIVE_STORAGE_SERVICE=s3_compatible \
  --env STORAGE_BUCKET_NAME=chatwoot \
  --env STORAGE_ACCESS_KEY_ID=YLBhnYvXT1vsOqlWh9Ml \
  --env STORAGE_SECRET_ACCESS_KEY=8IvkSaEjjEjAPOzioeIxGQWkKkVFqQUVH97s3UpB \
  --env STORAGE_REGION=us-east-1 \
  --env STORAGE_ENDPOINT=https://files.senaia.in \
  --env STORAGE_FORCE_PATH_STYLE=true \
  chatwoot/chatwoot:v4.2.0 \
  bundle exec rails db:chatwoot_prepare

# 2. Monitorar o progresso da migração
docker service logs -f chatwoot-migrate-new

# 3. Aguardar conclusão (pode levar alguns minutos)
# Saída esperada deve incluir:
# - "Database creation completed"
# - "Running migrations"
# - "Seeding database"
# - "Installation completed"
```

### 4. Verificar Status da Migração
```bash
# Verificar se a migração foi bem-sucedida
docker service ps chatwoot-migrate-new

# Se o status for "Complete", a migração foi bem-sucedida
# Se houver erro, verificar logs:
docker service logs chatwoot-migrate-new --tail 50
```

### 5. Limpeza após Migração
```bash
# Remover o serviço temporário
docker service rm chatwoot-migrate-new

# Verificar se foi removido
docker service ls | grep chatwoot
```

### 6. Validar Estrutura do Banco
```bash
# Acessar PostgreSQL novamente
docker exec -it $POSTGRES_CONTAINER psql -U chatwoot_database -d chatwoot_db

# Verificar tabelas criadas
\dt

# Verificar algumas tabelas importantes
SELECT count(*) FROM accounts;
SELECT count(*) FROM users;
SELECT count(*) FROM conversations;

# Sair
\q
```

## 📦 Deploy do Chatwoot

### 1. Deploy do Stack Chatwoot
```bash
# Fazer deploy usando o novo arquivo YAML
docker stack deploy -c chatwoot-new.yml chatwoot-new

# Verificar se os serviços subiram
docker service ls | grep chatwoot-new
```

### 2. Monitorar Inicialização
```bash
# Acompanhar logs do Rails
docker service logs -f chatwoot-new_chatwoot_rails

# Acompanhar logs do Sidekiq
docker service logs -f chatwoot-new_chatwoot_sidekiq
```

### 3. Verificar Saúde dos Serviços
```bash
# Verificar status dos containers
docker service ps chatwoot-new_chatwoot_rails
docker service ps chatwoot-new_chatwoot_sidekiq

# Verificar se o healthcheck está passando
docker service inspect chatwoot-new_chatwoot_rails --format '{{json .ServiceStatus}}'
```

## 🌐 Verificação Final

### 1. Teste de Conectividade
```bash
# Testar se o Chatwoot está respondendo
curl -I https://chat.senaia.in

# Deve retornar: HTTP/2 200
```

### 2. Verificar Interface Web
- Acessar: https://chat.senaia.in
- Deve carregar a página de login do Chatwoot
- Criar conta de administrador inicial

### 3. Verificar Logs de Aplicação
```bash
# Logs em tempo real
docker service logs -f chatwoot-new_chatwoot_rails --tail 100

# Verificar se não há erros críticos
docker service logs chatwoot-new_chatwoot_rails | grep -i error
```

## 🔧 Comandos de Manutenção

### Rails Console
```bash
# Acessar Rails console para debug/administração
docker exec -it $(docker ps -q -f name=chatwoot-new_chatwoot_rails) bundle exec rails console

# Exemplos de comandos no console:
# User.count
# Account.first
# exit
```

### Rollback em Caso de Problemas
```bash
# Fazer rollback do stack
docker service rollback chatwoot-new_chatwoot_rails
docker service rollback chatwoot-new_chatwoot_sidekiq

# Ou remover completamente e refazer
docker stack rm chatwoot-new
```

### Backup do Banco
```bash
# Fazer backup do banco do Chatwoot
docker exec $(docker ps -q -f name=postgres) pg_dump -U chatwoot_database chatwoot_db > chatwoot_backup_$(date +%Y%m%d_%H%M%S).sql
```

## ⚠️ Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está acessível
docker exec $(docker ps -q -f name=chatwoot) nc -zv postgres 5432
```

#### 2. Erro de Conexão com Redis
```bash
# Verificar se Redis está acessível
docker exec $(docker ps -q -f name=chatwoot) nc -zv redis 6379
```

#### 3. Erro de Storage (MinIO)
```bash
# Verificar se MinIO está acessível
docker exec $(docker ps -q -f name=chatwoot) nc -zv minio 9000
```

#### 4. Serviço não Inicia
```bash
# Verificar eventos do Docker
docker events --filter service=chatwoot-new_chatwoot_rails

# Verificar constraints de placement
docker service inspect chatwoot-new_chatwoot_rails --format '{{json .Spec.TaskTemplate.Placement}}'
```

### Logs Importantes para Debug
```bash
# Logs de inicialização
docker service logs chatwoot-new_chatwoot_rails --timestamps

# Logs de erro específicos
docker service logs chatwoot-new_chatwoot_rails | grep -i "error\|fatal\|exception"

# Logs de conexão com banco
docker service logs chatwoot-new_chatwoot_rails | grep -i "postgres\|database"
```

## 📝 Notas Importantes

1. **Credenciais**: Todas as credenciais usadas neste manual são as existentes no ambiente
2. **SSL**: O Traefik cuida automaticamente dos certificados SSL
3. **Backup**: Sempre faça backup antes de grandes mudanças
4. **Monitoramento**: Monitore os logs durante as primeiras 24h após deploy
5. **Performance**: Ajuste os recursos conforme necessário baseado no uso

## 🔄 Próximos Passos

Após a instalação bem-sucedida:

1. Configurar primeiro usuário administrador
2. Configurar integrações (WhatsApp via Evolution API)
3. Personalizar configurações da empresa
4. Configurar webhooks se necessário
5. Implementar backup automatizado
6. Configurar monitoramento de performance