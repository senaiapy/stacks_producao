# 🚀 Manual Completo - Supabase Stack no Portainer

Este manual detalha como fazer deploy da stack completa do Supabase usando Portainer, incluindo PostgreSQL com pgvector, Auth, Storage, Realtime, e Studio Dashboard.

## 📋 Arquitetura Supabase

### Serviços Incluídos
- **PostgreSQL 15** - Banco principal com pgvector para embeddings
- **Kong API Gateway** - Gateway de APIs e roteamento
- **GoTrue** - Serviço de autenticação e autorização
- **PostgREST** - API REST automática do PostgreSQL
- **Realtime** - WebSockets e subscriptions em tempo real
- **Storage API** - Gerenciamento de arquivos e storage
- **ImgProxy** - Processamento e redimensionamento de imagens
- **Studio Dashboard** - Interface web de administração
- **Meta API** - API de metadados do banco
- **Vector Support** - Suporte completo para embeddings e IA

### Domínios Configurados
- **Dashboard**: `https://supabase.senaia.in` (Supabase Studio)
- **API**: `https://supabase.senaia.in/rest/v1/` (REST API)
- **Auth**: `https://supabase.senaia.in/auth/v1/` (Authentication)
- **Storage**: `https://supabase.senaia.in/storage/v1/` (File Storage)
- **Realtime**: `https://supabase.senaia.in/realtime/v1/` (WebSockets)

## ✅ Pré-requisitos

### 1. Verificar Dependências no Portainer
**Portainer → Stacks** - Confirmar que estão rodando:
- ✅ `traefik` (Reverse proxy com SSL)
- ✅ Networks: `app_network` e `traefik_public`

### 2. Verificar Portas Disponíveis
Portas que serão usadas internamente (não conflitam):
- PostgreSQL: 5432 (interno)
- Kong Gateway: 8000 (interno)
- Auth (GoTrue): 9999 (interno)
- PostgREST: 3000 (interno)
- Realtime: 4000 (interno)
- Storage: 5000 (interno)
- Studio: 3000 (interno)

## 🗄️ Preparação do Banco de Dados

### 1. Criar Stack de Inicialização
**Portainer → Stacks → Add stack**

**Name:** `supabase-init`
**YAML:**

```yaml
version: "3.8"

services:
  supabase_init:
    image: supabase/postgres:15.1.0.147
    networks:
      - app_network
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=supabase_admin
      - POSTGRES_PASSWORD=Ma1x1x0x!!Ma1x1x0x!!
      - POSTGRES_INITDB_ARGS=--locale=C.UTF-8 --encoding=UTF8
    command: >
      bash -c "
      postgres &
      sleep 30 &&
      psql -U supabase_admin -d postgres -c 'CREATE EXTENSION IF NOT EXISTS vector;' &&
      psql -U supabase_admin -d postgres -c 'CREATE EXTENSION IF NOT EXISTS pg_stat_statements;' &&
      psql -U supabase_admin -d postgres -c 'CREATE SCHEMA IF NOT EXISTS auth;' &&
      psql -U supabase_admin -d postgres -c 'CREATE SCHEMA IF NOT EXISTS storage;' &&
      psql -U supabase_admin -d postgres -c 'CREATE SCHEMA IF NOT EXISTS realtime;' &&
      psql -U supabase_admin -d postgres -c 'CREATE SCHEMA IF NOT EXISTS graphql_public;' &&
      psql -U supabase_admin -d postgres -c 'CREATE ROLE anon;' &&
      psql -U supabase_admin -d postgres -c 'CREATE ROLE authenticated;' &&
      psql -U supabase_admin -d postgres -c 'CREATE ROLE authenticator LOGIN PASSWORD \"Ma1x1x0x!!Ma1x1x0x!!\";' &&
      psql -U supabase_admin -d postgres -c 'GRANT anon TO authenticator;' &&
      psql -U supabase_admin -d postgres -c 'GRANT authenticated TO authenticator;' &&
      echo 'Database initialization completed' &&
      tail -f /dev/null
      "
    volumes:
      - supabase_db_data:/var/lib/postgresql/data
    deploy:
      mode: replicated
      replicas: 1
      restart_policy:
        condition: none

networks:
  app_network:
    external: true

volumes:
  supabase_db_data:
    driver: local
```

### 2. Monitorar Inicialização
**Stacks → supabase-init → Service logs**

Aguardar mensagem: `Database initialization completed`

### 3. Remover Stack de Inicialização
**Stacks → supabase-init → Delete this stack**

## 🚀 Deploy da Stack Supabase Completa

### 1. Criar Stack Principal
**Portainer → Stacks → Add stack**

**Name:** `supabase`
**Build method:** Web editor
**YAML:** Copiar todo o conteúdo de `supabase-complete.yml`

### 2. Configurar Environment Variables (Opcional)
Na seção **Environment variables**:
```
POSTGRES_PASSWORD=Ma1x1x0x!!Ma1x1x0x!!
JWT_SECRET=194F83A5E420E2908213782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77
SMTP_PASSWORD=edmoauhradsarvmw
```

### 3. Deploy
**Clicar "Deploy the stack"**

## 🔍 Monitoramento via Portainer

### 1. Verificar Services
**Stacks → supabase → Services** - Todos devem estar (1/1):
- ✅ `supabase_supabase_db`
- ✅ `supabase_supabase_kong`
- ✅ `supabase_supabase_auth`
- ✅ `supabase_supabase_rest`
- ✅ `supabase_supabase_realtime`
- ✅ `supabase_supabase_storage`
- ✅ `supabase_supabase_studio`
- ✅ `supabase_supabase_meta`

### 2. Ordem de Inicialização
Os serviços devem subir nesta ordem:
1. **PostgreSQL** (primeiro)
2. **Meta API**
3. **Auth (GoTrue)**
4. **PostgREST**
5. **Storage**
6. **Realtime**
7. **Studio** (último)

### 3. Verificar Logs
**Services → [service_name] → Service logs**

**PostgreSQL logs esperados:**
```
database system is ready to accept connections
```

**Studio logs esperados:**
```
Ready on http://localhost:3000
```

## 🌐 Configuração e Primeiro Acesso

### 1. Acessar Supabase Studio
- URL: `https://supabase.senaia.in`
- Deve carregar o dashboard do Supabase Studio

### 2. Configuração Inicial do Projeto
No Studio:
1. **Create new project** ou usar projeto existente
2. **Database URL**: `postgresql://supabase_admin:Ma1x1x0x!!Ma1x1x0x!!@supabase_db:5432/postgres`
3. **API URL**: `https://supabase.senaia.in`

### 3. Testar APIs
**REST API:**
```bash
curl -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0" \
https://supabase.senaia.in/rest/v1/
```

**Auth API:**
```bash
curl https://supabase.senaia.in/auth/v1/settings
```

## 🔧 Configurações Avançadas

### 1. Configurar Storage Buckets
**Via Studio:**
1. Storage → Buckets
2. Create bucket: `public`, `private`
3. Configurar policies conforme necessário

### 2. Configurar Authentication
**Via Studio:**
1. Authentication → Settings
2. Configurar providers (Email, Google, etc.)
3. Configurar Email templates

### 3. Configurar Database
**Via Studio:**
1. SQL Editor
2. Table Editor
3. Database → Extensions → Habilitar extensões necessárias

## 📊 Monitoramento e Maintenance

### 1. Health Check via Portainer
**Containers → [container] → Stats**
- CPU/Memory usage
- Network traffic
- Container status

### 2. Logs em Tempo Real
**Services → [service] → Service logs**
- ✅ Sem erros críticos
- ✅ Conexões estabelecidas
- ✅ APIs respondendo

### 3. Database Monitoring
**Via Studio → Reports:**
- Query performance
- Table sizes
- Active connections

## 🔒 Segurança e Performance

### 1. JWT Tokens
- **Anon Key**: Para requests públicos
- **Service Key**: Para requests administrativos
- Configurar RLS (Row Level Security) nas tabelas

### 2. Rate Limiting
Kong Gateway inclui rate limiting automático

### 3. SSL/TLS
Traefik cuida automaticamente dos certificados

## ⚠️ Troubleshooting

### Problemas Comuns

#### 1. Studio não carrega
**Verificar:**
```bash
# Via container console:
curl -I http://localhost:3000
```

#### 2. API não responde
**Verificar Kong Gateway:**
```bash
# Container kong console:
curl -I http://localhost:8000/health
```

#### 3. Database connection error
**Verificar PostgreSQL:**
```bash
# Container database console:
pg_isready -U supabase_admin -d postgres
```

#### 4. Authentication não funciona
**Verificar GoTrue:**
```bash
# Container auth console:
curl http://localhost:9999/health
```

### Stack Rollback
**Stacks → supabase → Editor**
- Fazer alterações necessárias
- **Update the stack**

### Restart Completo
```bash
# Via Portainer:
Stacks → supabase → Delete this stack
# Aguardar limpeza
# Refazer deploy
```

## 📱 APIs e Endpoints

### REST API
- **Base URL**: `https://supabase.senaia.in/rest/v1/`
- **Headers**: `apikey: [anon_key]`

### Authentication
- **Base URL**: `https://supabase.senaia.in/auth/v1/`
- **Sign up**: `POST /signup`
- **Sign in**: `POST /token?grant_type=password`

### Storage
- **Base URL**: `https://supabase.senaia.in/storage/v1/`
- **Upload**: `POST /object/[bucket]/[path]`
- **Download**: `GET /object/public/[bucket]/[path]`

### Realtime
- **WebSocket**: `wss://supabase.senaia.in/realtime/v1/websocket`

## 🎯 Casos de Uso

### 1. Aplicação Web/Mobile
```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://supabase.senaia.in'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
const supabase = createClient(supabaseUrl, supabaseKey)
```

### 2. Vector/Embeddings para IA
```sql
-- Criar tabela com vetores
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  content TEXT,
  embedding VECTOR(1536)
);

-- Busca por similaridade
SELECT * FROM documents
ORDER BY embedding <-> '[0.1, 0.2, 0.3...]'
LIMIT 5;
```

### 3. Realtime Subscriptions
```javascript
const subscription = supabase
  .channel('public:posts')
  .on('postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'posts' },
      payload => console.log(payload)
  )
  .subscribe()
```

## 📝 Checklist Final

- [ ] PostgreSQL rodando com extensões instaladas
- [ ] Todos os services (1/1) no Portainer
- [ ] Studio acessível via `https://supabase.senaia.in`
- [ ] APIs REST respondendo
- [ ] Authentication funcionando
- [ ] Storage configurado
- [ ] Realtime conectando
- [ ] SSL funcionando via Traefik
- [ ] Logs sem erros críticos

**🎉 Supabase completo rodando no Portainer com todos os recursos!**


MANUAL MIGRATIONS

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
  CREATE EXTENSION IF NOT EXISTS pgjwt;
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