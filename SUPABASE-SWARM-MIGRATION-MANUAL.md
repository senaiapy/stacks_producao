# 🚀 Manual Completo - Supabase Stack Docker Swarm

Este manual detalha como fazer deploy da stack completa do Supabase usando Docker Swarm em modo produção, incluindo PostgreSQL com pgvector, Auth, Storage, Realtime, Studio Dashboard e Connection Pooler.

## 📋 Arquitetura Supabase Swarm

### Serviços Incluídos
- **PostgreSQL 15.8** - Banco principal com pgvector para embeddings e IA
- **Kong API Gateway** - Gateway de APIs, roteamento e rate limiting
- **GoTrue** - Serviço de autenticação e autorização
- **PostgREST** - API REST automática do PostgreSQL
- **Realtime** - WebSockets e subscriptions em tempo real
- **Storage API** - Gerenciamento de arquivos e storage
- **ImgProxy** - Processamento e redimensionamento de imagens
- **Studio Dashboard** - Interface web de administração
- **Meta API** - API de metadados do banco
- **Edge Functions** - Execução de funções serverless
- **Analytics** - Coleta e análise de logs
- **Vector** - Coleta de logs e métricas
- **Supavisor** - Connection pooler para PostgreSQL

### Domínios Configurados
- **Studio**: `https://studio.senaia.in` (Supabase Studio Dashboard)
- **API**: `https://supabase.senaia.in/rest/v1/` (REST API via Kong)
- **Auth**: `https://supabase.senaia.in/auth/v1/` (Authentication)
- **Storage**: `https://supabase.senaia.in/storage/v1/` (File Storage)
- **Realtime**: `https://supabase.senaia.in/realtime/v1/` (WebSockets)
- **Pooler**: `https://pooler.senaia.in` (Database Connection Pooler)

## ✅ Pré-requisitos

### 1. Docker Swarm Inicializado
```bash
# Verificar se Swarm está ativo
docker node ls

# Se não estiver ativo, inicializar:
docker swarm init --advertise-addr=YOUR_SERVER_IP
```

### 2. Redes Docker Swarm
```bash
# Criar redes necessárias
docker network create --driver=overlay app_network
docker network create --driver=overlay traefik_public

# Verificar redes criadas
docker network ls | grep overlay
```

### 3. Stacks Dependentes
Verificar que estão rodando via `docker service ls`:
- ✅ `traefik` (Reverse proxy com SSL automático)
- ✅ `postgres` (PostgreSQL principal do sistema)

### 4. Verificar Portas Disponíveis
Portas usadas internamente (sem conflitos):
- PostgreSQL: 5432 (interno)
- Kong Gateway: 8000 (interno)
- Auth (GoTrue): 9999 (interno)
- PostgREST: 3000 (interno)
- Realtime: 4000 (interno)
- Storage: 5000 (interno)
- Studio: 3000 (interno)
- Analytics: 4000 (interno)
- ImgProxy: 5001 (interno)
- Meta API: 8080 (interno)
- Vector: 9001 (interno)
- Supavisor: 6543 (interno para pooling)

## 🗄️ Preparação do Banco de Dados

### 1. Conectar ao PostgreSQL Principal
```bash
# Acessar container PostgreSQL existente
docker exec -it $(docker ps -q -f "name=postgres") psql -U chatwoot_database -d postgres
```

### 2. Executar Migrações Manuais
Dentro do PostgreSQL, executar:

```sql
-- Criar banco para Supabase
CREATE DATABASE supabase_db;
GRANT ALL PRIVILEGES ON DATABASE supabase_db TO chatwoot_database;

-- Conectar ao banco supabase
\c supabase_db

-- Instalar extensões necessárias
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pgjwt;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS http;

-- Criar schemas obrigatórios
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS realtime;
CREATE SCHEMA IF NOT EXISTS graphql_public;
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE SCHEMA IF NOT EXISTS _analytics;
CREATE SCHEMA IF NOT EXISTS _realtime;

-- Criar usuário supabase_admin
CREATE ROLE supabase_admin LOGIN SUPERUSER PASSWORD 'Ma1x1x0x_testing';

-- Criar roles específicos do Supabase
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN SUPERUSER;
CREATE ROLE authenticator LOGIN PASSWORD 'Ma1x1x0x_testing' NOINHERIT;
CREATE ROLE supabase_auth_admin LOGIN PASSWORD 'Ma1x1x0x_testing';
CREATE ROLE supabase_storage_admin LOGIN PASSWORD 'Ma1x1x0x_testing';

-- Configurar permissões
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;

-- Transferir ownership dos schemas
ALTER SCHEMA auth OWNER TO supabase_admin;
ALTER SCHEMA storage OWNER TO supabase_admin;
ALTER SCHEMA realtime OWNER TO supabase_admin;
ALTER SCHEMA graphql_public OWNER TO supabase_admin;
ALTER SCHEMA extensions OWNER TO supabase_admin;
ALTER SCHEMA _analytics OWNER TO supabase_admin;
ALTER SCHEMA _realtime OWNER TO supabase_admin;

-- Criar função para validação JWT
CREATE OR REPLACE FUNCTION extensions.jwt_decode(token text)
RETURNS json
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT json_object_agg(key, value)
  FROM json_each_text(
    convert_from(
      decode(
        translate(
          split_part(token, '.', 2),
          '-_', '+/'
        ) || repeat('=', (4 - length(split_part(token, '.', 2)) % 4) % 4),
        'base64'
      ),
      'utf8'
    )::json
  );
$$;

-- Sair do PostgreSQL
\q
```

### 3. Verificar Preparação
```bash
# Verificar se banco foi criado
docker exec -it $(docker ps -q -f "name=postgres") psql -U chatwoot_database -l | grep supabase
```

## 🚀 Deploy da Stack Supabase

### 1. Deploy via Docker Swarm
```bash
# Navegar para o diretório da stack
cd /home/galo/Desktop/stacks_producao

# Deploy da stack Supabase
docker stack deploy -c supabase.yml supabase
```

### 2. Monitorar Deploy
```bash
# Verificar serviços sendo criados
docker service ls | grep supabase

# Monitorar logs de inicialização
docker service logs -f supabase_db
docker service logs -f supabase_analytics
docker service logs -f supabase_meta
```

## 🔍 Monitoramento e Verificação

### 1. Verificar Status dos Serviços
```bash
# Listar todos os serviços Supabase
docker service ls | grep supabase

# Verificar réplicas ativas (devem estar 1/1)
docker service ps supabase_studio
docker service ps supabase_kong
docker service ps supabase_auth
docker service ps supabase_rest
docker service ps supabase_realtime
docker service ps supabase_storage
docker service ps supabase_meta
docker service ps supabase_functions
docker service ps supabase_analytics
docker service ps supabase_db
docker service ps supabase_vector
docker service ps supabase_supavisor
```

### 2. Ordem de Inicialização Esperada
Os serviços devem subir nesta ordem:
1. **Vector** (coleta de logs)
2. **PostgreSQL** (banco de dados)
3. **Analytics** (processamento de logs)
4. **Meta API** (metadados do banco)
5. **Auth (GoTrue)** (autenticação)
6. **PostgREST** (API REST)
7. **ImgProxy** (processamento de imagens)
8. **Storage** (armazenamento de arquivos)
9. **Realtime** (websockets)
10. **Functions** (edge functions)
11. **Kong** (API gateway)
12. **Supavisor** (connection pooler)
13. **Studio** (interface web)

### 3. Verificar Logs de Inicialização
```bash
# PostgreSQL deve mostrar:
docker service logs supabase_db 2>&1 | tail -10
# Esperado: "database system is ready to accept connections"

# Analytics deve mostrar:
docker service logs supabase_analytics 2>&1 | tail -10
# Esperado: sem erros críticos

# Studio deve mostrar:
docker service logs supabase_studio 2>&1 | tail -10
# Esperado: "Ready on http://localhost:3000"

# Kong deve mostrar:
docker service logs supabase_kong 2>&1 | tail -10
# Esperado: "started"
```

### 4. Verificar Health Checks
```bash
# Verificar status dos containers
docker service ps supabase_studio --no-trunc
docker service ps supabase_kong --no-trunc
docker service ps supabase_db --no-trunc

# Containers devem estar "Running" há mais de 2 minutos
```

## 🌐 Configuração e Primeiro Acesso

### 1. Acessar Supabase Studio
- **URL**: `https://studio.senaia.in`
- **Deve carregar**: Dashboard do Supabase Studio
- **Login**: Criar uma conta ou usar credenciais configuradas

### 2. Configuração Inicial do Projeto
No Studio Dashboard:

1. **Database Settings**:
   - Host: `db` (interno) ou `pooler.senaia.in` (externo)
   - Port: `5432` (interno) ou `6543` (pooler)
   - Database: `supabase_db`
   - Username: `supabase_admin`
   - Password: `Ma1x1x0x_testing`

2. **API Settings**:
   - **Project URL**: `https://supabase.senaia.in`
   - **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao`
   - **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI`

### 3. Testar APIs via CURL
```bash
# Testar REST API
curl -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao" \
https://supabase.senaia.in/rest/v1/

# Testar Auth API
curl https://supabase.senaia.in/auth/v1/settings

# Testar Storage API
curl -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao" \
https://supabase.senaia.in/storage/v1/buckets

# Testar Connection Pooler
psql "postgresql://supabase_admin:Ma1x1x0x_testing@pooler.senaia.in:6543/supabase_db"
```

## 🔧 Configurações Avançadas

### 1. Configurar Storage Buckets
Via Supabase Studio:
```sql
-- Via SQL Editor no Studio
INSERT INTO storage.buckets (id, name, public) VALUES ('public', 'public', true);
INSERT INTO storage.buckets (id, name, public) VALUES ('private', 'private', false);

-- Configurar policies para bucket público
CREATE POLICY "Public bucket read access" ON storage.objects
FOR SELECT USING (bucket_id = 'public');

CREATE POLICY "Public bucket upload access" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'public');
```

### 2. Configurar Authentication Providers
Via Studio → Authentication → Settings:
```json
{
  "SITE_URL": "https://supabase.senaia.in",
  "REDIRECT_URLS": ["https://yourdomain.com/*"],
  "JWT_EXPIRY": 3600,
  "DISABLE_SIGNUP": false,
  "EMAIL_CONFIRM": false
}
```

### 3. Configurar Edge Functions
```bash
# Criar diretório para functions
docker exec -it $(docker service ps -q supabase_functions) mkdir -p /home/deno/functions/hello

# Exemplo de function
cat > hello.ts << 'EOF'
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  return new Response(
    JSON.stringify({ message: "Hello from Supabase Edge Functions!" }),
    { headers: { "Content-Type": "application/json" } }
  )
})
EOF
```

### 4. Configurar Database com pgvector
```sql
-- Via Studio SQL Editor ou psql
-- Criar tabela para embeddings
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  content TEXT,
  metadata JSONB,
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar índice para busca vetorial
CREATE INDEX documents_embedding_idx ON documents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Exemplo de inserção
INSERT INTO documents (content, embedding) VALUES
('Exemplo de documento', '[0.1, 0.2, 0.3, ...]');

-- Busca por similaridade
SELECT content, 1 - (embedding <=> '[0.1, 0.2, 0.3, ...]') AS similarity
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, 0.3, ...]'
LIMIT 5;
```

## 📊 Monitoramento em Produção

### 1. Health Checks Automáticos
```bash
# Script para monitorar todos os serviços
#!/bin/bash
services=("studio" "kong" "auth" "rest" "realtime" "storage" "meta" "functions" "analytics" "db" "vector" "supavisor")

for service in "${services[@]}"; do
  status=$(docker service ps "supabase_$service" --format "table {{.CurrentState}}" | grep -c "Running")
  echo "supabase_$service: $status/1 running"
done
```

### 2. Verificar Logs em Tempo Real
```bash
# Monitorar logs críticos
docker service logs -f supabase_db | grep -E "(ERROR|FATAL|PANIC)"
docker service logs -f supabase_kong | grep -E "(error|ERROR)"
docker service logs -f supabase_studio | grep -E "(Error|ERROR)"
```

### 3. Verificar Performance
```bash
# CPU e Memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep supabase

# Verificar conexões PostgreSQL
docker exec -it $(docker service ps -q supabase_db) psql -U supabase_admin -d supabase_db -c "
SELECT
  datname,
  numbackends,
  xact_commit,
  xact_rollback
FROM pg_stat_database
WHERE datname = 'supabase_db';"
```

## 🔒 Segurança e Performance

### 1. Configurações de Segurança
```sql
-- Habilitar Row Level Security (RLS)
ALTER TABLE public.your_table ENABLE ROW LEVEL SECURITY;

-- Criar policy para usuários autenticados
CREATE POLICY "Users can only see their own data" ON public.your_table
FOR ALL USING (auth.uid() = user_id);

-- Configurar roles com mínimos privilégios
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.your_table TO authenticated;
```

### 2. Rate Limiting (Kong)
Kong Gateway já inclui rate limiting automático configurado.

### 3. SSL/TLS
Traefik gerencia automaticamente certificados Let's Encrypt.

### 4. Backup Strategy
```bash
# Script de backup automatizado
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/supabase"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec $(docker service ps -q supabase_db) pg_dump \
  -U supabase_admin \
  -d supabase_db \
  --no-password \
  --verbose \
  --clean \
  --create > "$BACKUP_DIR/supabase_db_$DATE.sql"

# Backup Storage files
docker run --rm \
  --volumes-from $(docker service ps -q supabase_storage) \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/storage_$DATE.tar.gz /var/lib/storage

echo "Backup completed: $DATE"
```

## ⚠️ Troubleshooting

### Problemas Comuns

#### 1. Studio não carrega
```bash
# Verificar se Studio está rodando
docker service ps supabase_studio

# Verificar logs
docker service logs supabase_studio 2>&1 | tail -20

# Verificar se Analytics está funcionando (dependência)
docker service logs supabase_analytics 2>&1 | tail -10

# Testar internamente
docker exec -it $(docker service ps -q supabase_studio) curl -I http://localhost:3000
```

#### 2. API não responde (Kong Gateway)
```bash
# Verificar Kong
docker service ps supabase_kong

# Verificar configuração Kong
docker service logs supabase_kong 2>&1 | tail -20

# Verificar se Analytics está rodando (dependência)
docker service ps supabase_analytics

# Testar Kong internamente
docker exec -it $(docker service ps -q supabase_kong) curl -I http://localhost:8000/health
```

#### 3. Database connection error
```bash
# Verificar PostgreSQL
docker service ps supabase_db

# Verificar logs do banco
docker service logs supabase_db 2>&1 | tail -20

# Testar conexão
docker exec -it $(docker service ps -q supabase_db) pg_isready -U supabase_admin -d supabase_db

# Verificar roles e permissões
docker exec -it $(docker service ps -q supabase_db) psql -U supabase_admin -d supabase_db -c "\du"
```

#### 4. Authentication não funciona (GoTrue)
```bash
# Verificar GoTrue
docker service ps supabase_auth

# Verificar logs
docker service logs supabase_auth 2>&1 | tail -20

# Testar health endpoint
docker exec -it $(docker service ps -q supabase_auth) wget -qO- http://localhost:9999/health
```

#### 5. Realtime não conecta
```bash
# Verificar Realtime
docker service ps supabase_realtime

# Verificar logs
docker service logs supabase_realtime 2>&1 | tail -20

# Verificar se banco está acessível
docker exec -it $(docker service ps -q supabase_realtime) nc -zv db 5432
```

### Comandos de Recovery

#### Restart de Serviço Específico
```bash
# Restart individual
docker service update --force supabase_studio
docker service update --force supabase_kong
docker service update --force supabase_auth
```

#### Restart da Stack Completa
```bash
# Remove stack
docker stack rm supabase

# Aguardar limpeza completa (30-60 segundos)
sleep 60

# Verificar se volumes persistem
docker volume ls | grep supabase

# Re-deploy
docker stack deploy -c supabase.yml supabase
```

#### Verificar e Limpar Recursos
```bash
# Listar serviços órfãos
docker service ls | grep -E "(0/1|0/0)"

# Remover serviços órfãos
docker service rm $(docker service ls -q -f "label=com.docker.stack.namespace=supabase")

# Verificar volumes não utilizados
docker volume ls | grep supabase
```

## 📱 Integração com Aplicações

### 1. Client JavaScript/TypeScript
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://supabase.senaia.in'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao'

export const supabase = createClient(supabaseUrl, supabaseKey)

// Exemplo de uso
const { data, error } = await supabase
  .from('your_table')
  .select('*')
```

### 2. Conexão Externa via Pooler
```javascript
// Para aplicações que precisam de conexão direta PostgreSQL
import { Client } from 'pg'

const client = new Client({
  host: 'pooler.senaia.in',
  port: 6543,
  database: 'supabase_db',
  user: 'supabase_admin',
  password: 'Ma1x1x0x_testing',
  ssl: true // Recomendado para produção
})

await client.connect()
```

### 3. Vector/Embeddings para IA
```javascript
// Exemplo com OpenAI embeddings
import OpenAI from 'openai'

const openai = new OpenAI()

// Gerar embedding
const response = await openai.embeddings.create({
  model: "text-embedding-ada-002",
  input: "Seu texto aqui",
})

const embedding = response.data[0].embedding

// Salvar no Supabase
const { data, error } = await supabase
  .from('documents')
  .insert({
    content: "Seu texto aqui",
    embedding: embedding
  })

// Buscar por similaridade
const { data: similar } = await supabase
  .rpc('match_documents', {
    query_embedding: embedding,
    similarity_threshold: 0.8,
    match_count: 5
  })
```

### 4. Realtime Subscriptions
```javascript
// Subscrever mudanças em tempo real
const subscription = supabase
  .channel('public:posts')
  .on('postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'posts' },
      payload => {
        console.log('New post:', payload.new)
      }
  )
  .on('postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'posts' },
      payload => {
        console.log('Updated post:', payload.new)
      }
  )
  .subscribe()
```

## 📝 Checklist Final

### Deploy
- [ ] Docker Swarm inicializado
- [ ] Redes `app_network` e `traefik_public` criadas
- [ ] PostgreSQL principal rodando
- [ ] Traefik stack ativa
- [ ] Banco `supabase_db` criado com extensões
- [ ] Roles e schemas configurados
- [ ] Stack `supabase` deployada com sucesso

### Verificação de Serviços
- [ ] `supabase_db` (1/1) - PostgreSQL rodando
- [ ] `supabase_vector` (1/1) - Log collector ativo
- [ ] `supabase_analytics` (1/1) - Analytics processando
- [ ] `supabase_meta` (1/1) - Meta API respondendo
- [ ] `supabase_auth` (1/1) - GoTrue funcionando
- [ ] `supabase_rest` (1/1) - PostgREST ativo
- [ ] `supabase_imgproxy` (1/1) - Image processing ativo
- [ ] `supabase_storage` (1/1) - Storage API funcionando
- [ ] `supabase_realtime` (1/1) - Realtime conectando
- [ ] `supabase_functions` (1/1) - Edge Functions ativas
- [ ] `supabase_kong` (1/1) - API Gateway roteando
- [ ] `supabase_supavisor` (1/1) - Connection pooler ativo
- [ ] `supabase_studio` (1/1) - Dashboard acessível

### Acesso e Funcionalidade
- [ ] Studio acessível via `https://studio.senaia.in`
- [ ] APIs REST respondendo via `https://supabase.senaia.in`
- [ ] Authentication funcionando
- [ ] Storage buckets configurados
- [ ] Realtime subscriptions ativas
- [ ] Connection pooler acessível externamente
- [ ] SSL certificados válidos (Let's Encrypt)
- [ ] Logs sem erros críticos

### Segurança
- [ ] Senhas alteradas dos padrões
- [ ] RLS habilitado em tabelas públicas
- [ ] Policies de segurança configuradas
- [ ] Rate limiting ativo (Kong)
- [ ] Certificados SSL válidos

### Monitoramento
- [ ] Health checks funcionando
- [ ] Logs centralizados via Vector
- [ ] Analytics coletando métricas
- [ ] Backup strategy implementada
- [ ] Alertas configurados

**🎉 Supabase Stack Docker Swarm completa e funcionando em produção!**

## 📞 Suporte e Manutenção

### Logs Centralizados
```bash
# Ver todos os logs Supabase
docker service logs supabase_analytics | grep -E "(ERROR|WARN|error|warning)"

# Monitorar específico
docker service logs -f supabase_studio
```

### Atualizações
```bash
# Atualizar imagem específica
docker service update --image supabase/studio:latest supabase_studio

# Atualizar stack completa
docker stack deploy -c supabase.yml supabase
```

### Escalabilidade
```bash
# Escalar serviços conforme necessário
docker service scale supabase_rest=2
docker service scale supabase_realtime=2
```

Este manual garante uma instalação completa e funcional do Supabase em Docker Swarm com alta disponibilidade, monitoramento e segurança adequados para ambiente de produção.