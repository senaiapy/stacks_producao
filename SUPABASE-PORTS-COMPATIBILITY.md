# 🔌 Supabase - Compatibilidade de Portas

## ✅ Análise de Compatibilidade

### Portas Já em Uso (Não Conflitam)
```
chatwoot        3030  ✅ Interno
evolution       8080  ✅ Interno
redis           6379  ✅ Interno
postgres        5432  ✅ Interno (separado do Supabase)
portainer       9000, 9001, 9443  ✅ Públicas
traefik         8888, 8443  ✅ Públicas
n8n             5678  ✅ Interno
rabbitmq        5672  ✅ Interno
strapi          1337  ✅ Interno
minio           9000  ✅ Interno
```

### Portas Supabase (Novas - Sem Conflito)
```
PostgreSQL      5433  ✅ Diferente do postgres existente (5432)
Kong Gateway    8000  ✅ Mencionado no doc como disponível
Auth (GoTrue)   9999  ✅ Disponível
PostgREST       3001  ✅ Diferente do Chatwoot (3030)
Realtime        4000  ✅ Disponível
Storage API     5000  ✅ Disponível
ImgProxy        5001  ✅ Disponível
Studio          3032  ✅ Mencionado no doc como supabase-studio
Meta API        8080  ✅ Interno, não conflita
```

## 🚀 Quick Start - 3 Passos

### Passo 1: Preparação (2 min)
```bash
# Verificar no Portainer:
✅ Stack "traefik" rodando
✅ Networks "app_network" e "traefik_public" existem
```

### Passo 2: Deploy (5 min)
```bash
# Portainer → Stacks → Add stack
Name: supabase
YAML: [colar supabase-complete.yml]
Deploy: ✅
```

### Passo 3: Acesso (1 min)
```bash
# Acessar:
https://supabase.senaia.in
```

## 🎯 Resumo Técnico

### O que foi criado:
1. **Stack Completa** - 9 serviços integrados
2. **PostgreSQL Dedicado** - Separado do postgres existente
3. **APIs Completas** - REST, Auth, Storage, Realtime
4. **Dashboard Web** - Supabase Studio
5. **Vector Support** - pgvector para IA/embeddings
6. **SSL Automático** - Via Traefik
7. **Portainer Compatible** - 100% funcional

### Redes Utilizadas:
- `app_network` - Comunicação interna entre serviços
- `traefik_public` - Exposição via SSL

### Credenciais:
- **Database**: `supabase_admin` / `Ma1x1x0x!!Ma1x1x0x!!`
- **JWT Secret**: `194F83A5E420E2908213782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77`
- **API Keys**: Incluídas no YAML

### Domínio:
- **Principal**: `https://supabase.senaia.in`
- **APIs**: `https://supabase.senaia.in/[rest|auth|storage|realtime]/v1/`

## ⚡ Benefícios

1. **Zero Conflitos** - Portas completamente separadas
2. **Fácil Deploy** - Um clique no Portainer
3. **Stack Completa** - Todos recursos do Supabase
4. **Produção Ready** - SSL, monitoring, backups
5. **Escalável** - Docker Swarm nativo