# Manual de Instalação - Stack de Produção WhatsApp Business

## 📋 Visão Geral

Este manual contém todos os procedimentos e credenciais para instalação completa do stack de produção WhatsApp Business com Docker Swarm.

## 🚀 1. Preparação do Sistema

### 1.1 Configuração de Fuso Horário
```bash
# Brasil
sudo timedatectl set-timezone America/Sao_Paulo

# Paraguai
sudo timedatectl set-timezone America/Asuncion
```

### 1.2 Instalação do aaPanel (Opcional)
```bash
URL=https://www.aapanel.com/script/install_7.0_en.sh && if [ -f /usr/bin/curl ];then curl -ksSO "$URL" ;else wget --no-check-certificate -O install_7.0_en.sh "$URL";fi;bash install_7.0_en.sh aapanel
```
> ⚠️ **IMPORTANTE**: NÃO instale NGINX ou outros apps no aaPanel

### 1.3 Atualização do Sistema
```bash
sudo apt-get update && apt-get install -y apparmor-utils
sudo apt update && sudo apt install -y sshpass
```

### 1.4 Configuração do Hostname
```bash
# Definir nome do servidor (substitua 'manager1' pelo nome desejado)
hostnamectl set-hostname manager1

# Editar arquivo hosts
nano /etc/hosts
# Alterar linha: 127.0.0.1 manager1
```

## 🐳 2. Instalação do Docker

### 2.1 Instalar Docker
```bash
curl -fsSL https://get.docker.com | bash
```

### 2.2 Configurar Docker Swarm
```bash
# Limpar configuração anterior (se existir)
docker swarm leave --force

# Inicializar Swarm
docker swarm init

# Criar redes necessárias
docker network create --driver=overlay network_public
docker network create --driver=overlay traefik_baileys_public
docker network create --driver=overlay app_baileys_network
docker network create --driver=overlay supabase-net
```

## 🔧 3. Configuração dos Serviços


### 3.1 Portainer (Gerenciamento Docker) ####################################
```bash
# Instalar Portainer
docker run -d -p 9000:9000 --name portainer --restart always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest --http-enabled
```

### 3.2 Traefik (Proxy Reverso) ##############################################
```bash
# Editar configuração
nano traefik.yaml

# Implantar stack
docker stack deploy --prune --resolve-image always -c traefik.yaml traefik
```


## 🗃️ 4. Bancos de Dados

### 4.1 PostgreSQL  ###########################################################
**Credenciais:**
- **Porta:** 5432
- **Usuário:** chatwoot_database
- **Senha:** Ma1x1x0x!!Ma1x1x0x!!
- **Database Principal:** chatwoot_database

**Configuração:**
```bash
# Acessar PostgreSQL
psql -U chatwoot_database -d chatwoot_database

# Habilitar extensão vector
CREATE EXTENSION IF NOT EXISTS vector;

# Criar bancos de dados
CREATE DATABASE n8n_database;
CREATE DATABASE evolution_database;
CREATE DATABASE chatwoot_db;
CREATE DATABASE chatwoot_baileys_db;
CREATE DATABASE supabase_db;

# Listar bancos
\l
```

### 4.2 Redis  #######################################################################
**Credenciais:**
- **Porta:** 6379
- **Senha:** J40geWtC08VoaUqoZ

### 4.3 MinIO (Storage S3) #############################################################
**Credenciais:**
- **Usuário:** marceluphd
- **Senha:** 1:7khB-=2898
- **URLs:**
  - Server: https://files.senaia.in
  - Console: https://minio.senaia.in

**Configuração:**
```bash
# Criar diretório MinIO
mkdir -p /var/data/minio

# Buckets a criar via interface:
# - evolution
# - chatwoot
```

## 📧 5. N8N (Automação) ##################################################################

### 5.1 Configuração
**Credenciais:**
- **Usuário:** marcelu.phd@gmail.com
- **Senha:** @450A...0628....n8n
- **Encryption Key:** KRpMlPWMaRCeL0Ehy6sHuYYweuLes4RT

**Gmail App Password:** dmaatsjzgzxqxmil

### 5.2 Stacks para Deploy
```bash
# Implantar na ordem:
docker stack deploy -c n8n_editor.yml n8n-editor
docker stack deploy -c n8n_mcp.yml n8n-mcp
docker stack deploy -c n8n_webhook.yml n8n-webhook
docker stack deploy -c n8n_worker.yml n8n-worker
```

### 5.3 Plugins N8N
Instalar via Settings > Plugins:
- `n8n-nodes-evolution-api`
- `@devlikeapro/n8n-nodes-chatwoot`

## 💬 6. Chatwoot (Atendimento) ##############################################################

### 6.1 Configuração
**Credenciais:**
- **Usuário:** marcelu.phd@gmail.com
- **Senha:** @450A...0628....chatwoot
- **API Key:** VfQrr8ruFjVjarMgADhLtnnw
- **SECRET_KEY_BASE:** 194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77

**MinIO Keys (Chatwoot):**
- **Access Key:** YLBhnYvXT1vsOqlWh9Ml
- **Secret Key:** 8IvkSaEjjEjAPOzioeIxGQWkKkVFqQUVH97s3UpB

**MinIO Keys (Chatwoot-Baileys):**
- **Access Key:** BN0t99DuuhNtbkiJQcHP
- **Secret Key:** enCejRo4tU9tmvCWa5LuwAfTods0vNfYlOMbXdyB

### 6.2 Migração (OBRIGATÓRIA)
```bash
# 1. Subir stack de migração
docker stack deploy -c chatwoot-portainer.yml chatwoot-migrate

# 2. Aguardar conclusão e verificar tabelas
psql -U chatwoot_database -d chatwoot_db -c "\dt"

# 3. Remover stack de migração
docker stack rm chatwoot-migrate

# 4. Subir stack definitivo
docker stack deploy -c chatwoot.yml chatwoot
```

## 📱 7. Evolution API (WhatsApp) ############################################################

### 7.1 Configuração
**Credenciais:**
- **URL:** evo.senaia.in
- **Senha:** LcXEtOWi3xX0HNFY4EbMT9sPWcMbT1nu

**MinIO Keys (Evolution):**
- **Access Key:** 5lsFUYQkaj36mjULwzaC
- **Secret Key:** gggQxoMDzHlH9AVOFSdB25lftDSoBnWZgeTFyt6g

**Instância Configurada:**
- **Nome:** clubdeofertas
- **ID:** 1230F54682FF-4CDA-839C-AA9FBCBF910A
- **Telefone:** 595985511359

### 7.2 Integração com Chatwoot
1. Ativar botão de integração Chatwoot
2. URL do Chatwoot: https://chat.senaia.in
3. Configurar API token do Chatwoot
4. Dias de importação: 7
5. Ativar autocreate

## 🌐 8. Nginx Proxy Manager ###############################################################

### 8.1 Configuração
**Credenciais:**
- **Usuário:** marcelu.phd@gmail.com (padrão: admin@example.com)
- **Senha:** @450Ab----28----nproxy (padrão: changeme)
- **Porta:** 8181

### 8.2 Preparação
```bash
# Criar diretórios
mkdir -p /var/data/npm/data
mkdir -p /var/data/npm/letsencrypt

# Implantar stack
docker stack deploy -c nproxy.yml nginx-proxy
```
# http access
http://217.79.184.8:8181/

## ☁️ 9. Supabase #############################################################################

### 9.1 Configuração
**Portas:**
- **Supabase:** 8000
- **Supabase Studio:** 3032

### 9.2 Banco de Dados
Database criada: `supabase_db`

##############################################################################################
##############################################################################################
## 📊 10. Portas em Uso

| Serviço | Porta | Tipo |
|---------|-------|------|
| PostgreSQL | 5432 | Interno |
| Redis | 6379 | Interno |
| MinIO | 9000 | Interno |
| Portainer | 9000, 9001, 9443 | Externo/Interno |
| Traefik | 8888 | Dashboard |
| N8N | 5678 | Interno |
| Chatwoot | 3030 | Interno |
| Evolution | 8080 | Interno |
| Supabase | 8000 | Interno |
| Supabase Studio | 3032 | Interno |
| Nginx Proxy | 8181 | Externo |
| RabbitMQ | 5672 | Interno |
| Strapi | 1337 | Interno |

## 🌍 11. Domínios Configurados

- **Painel:** painel.senaia.in (Portainer)
- **Files:** files.senaia.in (MinIO Server)
- **MinIO Console:** minio.senaia.in
- **Editor:** editor.senaia.in (N8N)
- **Workflow:** workflow.senaia.in (N8N)
- **Chat:** chat.senaia.in (Chatwoot)
- **Evolution:** evo.senaia.in

## ⚠️ 12. Observações Importantes

### Segurança
- ✅ Todas as senhas devem ser alteradas dos padrões
- ✅ Verificar DNS antes de executar (dnschecker)
- ✅ Serviços comunicam via redes internas apenas
- ✅ SSL automático via Let's Encrypt

### Ordem de Deploy
1. **Infraestrutura:** Traefik, Portainer
2. **Bancos:** PostgreSQL, Redis
3. **Storage:** MinIO
4. **Aplicações:** N8N, Evolution, Chatwoot
5. **Proxy:** Nginx Proxy Manager (opcional)

### Backup Recomendado
- 📁 Volumes Docker
- 🗃️ Bancos PostgreSQL
- 📦 Buckets MinIO
- ⚙️ Arquivos de configuração YAML

---

**📝 Nota:** Este manual contém informações sensíveis. Mantenha-o seguro e atualize as credenciais conforme necessário.