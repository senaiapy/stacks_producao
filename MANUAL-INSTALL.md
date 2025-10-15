# Manual de Instalação - Stack de Produção WhatsApp Business

## 📋 Visão Geral

Este manual contém todos os procedimentos e credenciais para instalação completa do stack de produção WhatsApp Business com Docker Swarm.

## 🚀 1. Preparação do Sistema


> ⚠️ **IMPORTANTE**: NÃO instale NGINX ou outros apps no aaPanel

### 1.1 Atualização do Sistema
```bash
sudo apt-get update && apt-get upgrade -y 

sudo apt-get install  zip unzip curl git apt-transport-https net-tools libcurl4-openssl-dev nmon htop ufw locales  nmap zsh nodejs npm ca-certificates  systemd-timesyncd   software-properties-common libxslt1-dev libcurl4 libgeoip-dev  apparmor-utils python3-pip sshpass -y

```
### 1.2 Configuração de Fuso Horário
```bash
# Brasil
sudo timedatectl set-timezone America/Sao_Paulo

# Paraguai
sudo timedatectl set-timezone America/Asuncion
```

### 1.3 Configuração do Hostname
```bash
# Definir nome do servidor (substitua 'paraguays' pelo nome desejado)
hostnamectl set-hostname paraguays

# Editar arquivo hosts
nano /etc/hosts
# Alterar linha: 127.0.0.1 paraguays se houver referncias tb

systemctl reboot
```

### 1.4 Instalação do aaPanel (Opcional)
```bash
URL=https://www.aapanel.com/script/install_7.0_en.sh && if [ -f /usr/bin/curl ];then curl -ksSO "$URL" ;else wget --no-check-certificate -O install_7.0_en.sh "$URL";fi;bash install_7.0_en.sh aapanel
```

### 2 Configurar Orion Auto Install(opcional)

bash <(curl -sSL setup.oriondesign.art.br)

## 🐳 2.0 Instalação do Docker

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
- **Usuário:** [CONFIGURE_YOUR_USERNAME]
- **Senha:** [CONFIGURE_YOUR_PASSWORD]
- **Database Principal:** [CONFIGURE_YOUR_DATABASE]

**Configuração:**
```bash
# Acessar PostgreSQL
psql -U [YOUR_USERNAME] -d [YOUR_DATABASE]

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
- **Senha:** [CONFIGURE_YOUR_REDIS_PASSWORD]

### 4.3 MinIO (Storage S3) #############################################################
**Credenciais:**
- **Usuário:** [CONFIGURE_YOUR_MINIO_USER]
- **Senha:** [CONFIGURE_YOUR_MINIO_PASSWORD]
- **URLs:**
  - Server: https://files.yourdomain.com
  - Console: https://minio.yourdomain.com

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
- **Usuário:** [CONFIGURE_YOUR_EMAIL]
- **Senha:** [CONFIGURE_YOUR_PASSWORD]
- **Encryption Key:** [GENERATE_32_CHAR_KEY]

**Gmail App Password:** [CONFIGURE_YOUR_APP_PASSWORD]

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
- `@johnlindquist/n8n-nodes-claudecode`

## 💬 6. Chatwoot (Atendimento) ##############################################################

### 6.1 Configuração
**Credenciais:**
- **Usuário:** [CONFIGURE_YOUR_EMAIL]
- **Senha:** [CONFIGURE_YOUR_PASSWORD]
- **API Key:** [GENERATE_API_KEY]
- **SECRET_KEY_BASE:** [GENERATE_64_CHAR_SECRET]

**MinIO Keys (Chatwoot):**
- **Access Key:** [GENERATE_MINIO_ACCESS_KEY]
- **Secret Key:** [GENERATE_MINIO_SECRET_KEY]

**MinIO Keys (Chatwoot-Baileys):**
- **Access Key:** [GENERATE_BAILEYS_ACCESS_KEY]
- **Secret Key:** [GENERATE_BAILEYS_SECRET_KEY]

### 6.2 Migração (OBRIGATÓRIA)
```bash
# 1. Subir stack de migração
docker stack deploy -c chatwoot-portainer.yml chatwoot-migrate

# 2. Aguardar conclusão e verificar tabelas
psql -U [YOUR_USERNAME] -d [YOUR_DATABASE] -c "\dt"

# 3. Remover stack de migração
docker stack rm chatwoot-migrate

# 4. Subir stack definitivo
docker stack deploy -c chatwoot.yml chatwoot
```

## 📱 7. Evolution API (WhatsApp) ############################################################

### 7.1 Configuração
**Credenciais:**
- **URL:** evo.yourdomain.com
- **Senha:** [CONFIGURE_YOUR_EVOLUTION_PASSWORD]

**MinIO Keys (Evolution):**
- **Access Key:** [GENERATE_EVOLUTION_ACCESS_KEY]
- **Secret Key:** [GENERATE_EVOLUTION_SECRET_KEY]

**Instância Configurada:**
- **Nome:** [YOUR_INSTANCE_NAME]
- **ID:** [GENERATE_INSTANCE_ID]
- **Telefone:** [YOUR_PHONE_NUMBER]

### 7.2 Integração com Chatwoot
1. Ativar botão de integração Chatwoot
2. URL do Chatwoot: https://chat.yourdomain.com
3. Configurar API token do Chatwoot
4. Dias de importação: 7
5. Ativar autocreate

## 🌐 8. Nginx Proxy Manager ###############################################################

### 8.1 Configuração
**Credenciais:**
- **Usuário:** [CONFIGURE_YOUR_EMAIL] (padrão: admin@example.com)
- **Senha:** [CONFIGURE_YOUR_PASSWORD] (padrão: changeme)
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
http://YOUR_SERVER_IP:8181/

## ☁️ 9. Supabase #############################################################################
#### OPEN PORTAS 8000 5432 3000 4000 6543 7946 2377
### 9.0 Configuraçãoope
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

- **Painel:** painel.yourdomain.com (Portainer)
- **Files:** files.yourdomain.com (MinIO Server)
- **MinIO Console:** minio.yourdomain.com
- **Editor:** editor.yourdomain.com (N8N)
- **Workflow:** workflow.yourdomain.com (N8N)
- **Chat:** chat.yourdomain.com (Chatwoot)
- **Evolution:** evo.yourdomain.com

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

