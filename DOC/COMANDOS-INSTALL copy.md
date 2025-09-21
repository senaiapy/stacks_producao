#DEFINIR FUSO HORARIO
sudo timedatectl set-timezone America/Sao_Paulo

sudo timedatectl set-timezone America/Asuncion


#instalar aapenel
URL=https://www.aapanel.com/script/install_7.0_en.sh && if [ -f /usr/bin/curl ];then curl -ksSO "$URL" ;else wget --no-check-certificate -O install_7.0_en.sh "$URL";fi;bash install_7.0_en.sh aapanel

#### NOT INSTALL NGINX OR OTHER APPS ####


Guia de Instalação
🚀 Instalação Evolution V2
1️⃣ Atualização do Sistema e Instalação de Dependências
Abra o terminal e execute o seguinte comando:
sudo apt-get update ; apt-get install -y apparmor-utils


2️⃣ Definição do Nome do Servidor
Você pode substituir manager1 por um nome de sua escolha:
hostnamectl set-hostname manager1


3️⃣ Configuração do Arquivo /etc/hosts
Edite o arquivo de hosts com o comando:
nano /etc/hosts

Altere a linha do localhost para o nome definido no passo anterior (exemplo: manager1):
127.0.0.1 manager1

Depois de editar, salve e saia (Ctrl+X, pressione Y e Enter).

4️⃣ Instalação do Docker
Execute este comando para instalar o Docker:
curl -fsSL https://get.docker.com | bash


5️⃣ Inicialização do Swarm
Após a instalação, inicie o Docker Swarm com:

docker swarm leave --force

docker swarm init


6️⃣ Criação da Rede
Agora, crie a rede para os containers:
docker network create --driver=overlay network_public
docker network create  --driver=overlay  traefik_baileys_public
docker network create  --driver=overlay app_baileys_network
docker network create  --driver=overlay supabase-net

7️⃣ Configuração do Arquivo traefik.yaml
Abra o editor de texto:
nano traefik.yaml

Após editar o arquivo, salve e saia (Ctrl+X, pressione Y e Enter).

8️⃣ Implantação do Stack
Por fim, rode o comando abaixo para implantar o Traefik:
docker stack deploy --prune --resolve-image always -c traefik.yaml traefik


9️⃣ Instalação do Portainer
##
##cria uma pasta onde roda o portainer
##mkdir -p /var/data/config_externa
##
##e colque la o aqruivo baileys.yml 
##e coloque o arquivo supabase.yml
##
para redirecionar as portas externas do trefik

Execute o seguinte comando para instalar o Portainer:
docker run -d -p 9000:9000 --name portainer --restart always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest --http-enabled


💡 Dica: Verifique se os comandos foram executados corretamente antes de prosseguir para os próximos passos.

ip:9000 portainer

@450A...0628....portainer

getstarted- local - stack - postgres

 POSTGRES_PASSWORD=Ma1x1x0x!!Ma1x1x0x!!
 America/Asuncion

 disable acess control
 deploy

 the same with redis, evolution but in this change

# in postgress acess terminal and access user and create db
psql -U chatwoot_database -d chatwoot_database
CREATE EXTENSION IF NOT EXISTS vector;

# in minio access portainer folder and create folder
mkdir -p /var/data/minio

#create buckets login in minio.senaia.in
buckets -> create buckets 
evolution
chatwoot

################ mail google
#access google account (2 factors enabled) in security in search app password or senha app dreate a paste name
# n8n_full copy and past without spaces.

################ N8N #################


conect with postgress and create a n8n database

#Acessar o console do container do Postgres
psql -U chatwoot_database -d chatwoot_database

#Crie o Banco de Dados do N8N
CREATE DATABASE n8n_database;
CREATE DATABASE evolution_database;

# to list all dbs
 \l

#  #### install n8n-evolution-api
#  #settings->plugins->install plugin
#  
#  # n8n-nodes-evolution-api
#  # @devlikeapro/n8n-nodes-chatwoot

## go to docker hub, search for n8n TAGS and take the last version an palace in
# yml files n8nio/n8n:1.111.0

#add STACKS
n8n_editor
n8n_mcp 
n8n_webhook 
n8n_worker 


#  #### install n8n-evolution-api
#  #settings->plugins->install plugin
#  
#  # n8n-nodes-evolution-api
#  # @devlikeapro/n8n-nodes-chatwoot

################ CHATWOOT #################


#Acessar o console do container do Postgres
psql -U chatwoot_database -d chatwoot_database

#Crie o Banco de Dados do CHATWOOT
CREATE DATABASE chatwoot_db;

psql -U chatwoot_database -d chatwoot_database

#Crie o Banco de Dados do CHATWOOT
CREATE DATABASE chatwoot_baileys_db;

SECRET_KEY_BASE=194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77 

# goto minio create a chatwoot api key
# PLACE SECRET AN KEY

**⚠️ IMPORTANTE**: Execute a migração antes de subir o Chatwoot:

### 1. Container Temporário para Migração
#crie o stack chatwoot-portainer-yml
#suba o stack e aguarde a configuracao finalizada
#verifique se as tabelas foram criadas no postgres
psql -U chatwoot_database -d chatwoot_db -c "\dt"

#remova o stack e crie o stack 
chatwoot.yml

#    ### 2. Monitorar Migração
#    # Acompanhar logs
#    docker service logs -f chatwoot-migrate
#    ### 3. Limpar e Verificar
#    # Remover serviço temporário
#    docker service rm chatwoot-migrate
#    # Verificar tabelas criadas
#    docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_db -c "\dt"

################ EVOLUTION #################

# create database evolution_database

# goto minio create a chatwoot api key
# PLACE SECRET ANonKEY

####### integrar com CHATWOOT
ativar botao
vae emn integracao chatwoot url do chatwoot https://chat.senaia.in
conta 1 ver dashboard endereco
vae chatwoot configuracoes de perfil token api e colocar 
dias importacao mensagen 7
botao autocreate

## SETTINGS -CREATE A NEW INBOX -

################ BAILEYS #################


################ SUPABASE #################

#creata a database supabase_db

#Acessar o console do container do Postgres
psql -U chatwoot_database -d chatwoot_database

#Crie o Banco de Dados do CHATWOOT
CREATE DATABASE supabase_db;


################ NGINX PROXY MANAGER #################

# OPEN PORTS 8181
# CREATE A DIR /var/data/npm
# mkdir -p /var/data/npm/data
# mkdir -p /var/data/npm/letsencrypt
# up stack nproxy.yml

# Creating a new user: admin@example.com with password: changeme

#   
#   ## Step 1: Create the Proxy Host in Nginx Proxy Manager
#   Now, log into your NPM web interface (e.g., https://npm.yourdomain.#   com or http://your-server-ip:8181).
#   Go to Hosts -> Proxy Hosts.
#   Click Add Proxy Host.
#   Fill out the form exactly like this:
#   Under the Details Tab:
#   
#   Domain Names: portainer.yourdomain.com (The public address you #  #  want to use).
#   
#   Scheme: http
#   
#   Forward Hostname / IP: portainer
#   
#   This is the magic part. You are using the Docker service name from #   the docker-compose.yml file. Because NPM and Portainer are on the #   same #web-proxy network, NPM can find the Portainer container just #   its #name. You don't need to know its internal IP address.
#   
#   Forward Port: 9000
#   
#   This is the default internal port that Portainer uses.
#   Enable Block Common Exploits.
#   Under the SSL Tab:
#   SSL Certificate: Select "Request a new SSL Certificate".
#   Enable Force SSL and HTTP/2 Support.
#   Agree to the Let's Encrypt Terms of Service.
#   Click Save.
#   ############################################################
############################################################
############################################################
############################################################

####### PORTAINER RUNNING IN http://217.79.184.8:9000
####### AND ACCESS FOR https://painel.senaia.in


##### ANTES DE RODAR SENPRE VERIFICAR SE ESTAO LIBERADOS DOMINIOS NO DNSCHECKER PARA EVITAR BLOQUEIO ######

####### PORTS IN USE

chatwoot 3030
evolution 8080
redis 6379
postgres 5432
portainer 9000 9001 9443
traefik 8888
n8n 5678
rabbitmq 5672
strapi 1337
supabase 8000
supabase-studio 3032
minio 9000 interno

#-----------------------------POSTGRES

postgress porta 5432
user chatwoot_database
db chatwoot_database
password Ma1x1x0x!!Ma1x1x0x!!

#-----------------------------REDIS

redis porta 6379
password   J40geWtC08VoaUqoZ      

#-----------------------------MINIO

- MINIO_ROOT_USER=marceluphd
      - MINIO_ROOT_PASSWORD=1:7khB-=2898
      
      # URLs para integração com Traefik
      - MINIO_SERVER_URL=https://files.senaia.in
      - MINIO_BROWSER_REDIRECT_URL=https://minio.senaia.in
      
      gmail password to connect dmaatsjzgzxqxmil
      mardelu.phd
#---------------------------- CHATWOOT
chatwoot-baileys 
acceskey BN0t99DuuhNtbkiJQcHP
secretkey enCejRo4tU9tmvCWa5LuwAfTods0vNfYlOMbXdyB

chatwoot
    - STORAGE_ACCESS_KEY_ID=YLBhnYvXT1vsOqlWh9Ml
      - STORAGE_SECRET_ACCESS_KEY=8IvkSaEjjEjAPOzioeIxGQWkKkVFqQUVH97s3UpB

evolutiom
- S3_ACCESS_KEY=5lsFUYQkaj36mjULwzaC
      - S3_SECRET_KEY=gggQxoMDzHlH9AVOFSdB25lftDSoBnWZgeTFyt6g

chat.b7g.app
user marcelu.phd@gmail.com
pass 194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77

#-----------------------------N8N

user marcelu.phd@gmail.com
pass @450A...0628....n8n


- N8N_ENCRYPTION_KEY=KRpMlPWMaRCeL0Ehy6sHuYYweuLes4RT

#-----------------------------CHATWOOT
  SECRET_KEY_BASE=194F83A5E420E2898283782FE1E64C2E7C07B5C3F7409BA90138E2D1E658BD77 

marcelu.phd@gmail.com
@450A...0628....chatwoot
apikey= VfQrr8ruFjVjarMgADhLtnnw

##---------------------------- evolution
 
user evo.senaia.in      
pass LcXEtOWi3xX0HNFY4EbMT9sPWcMbT1nu      

evo.senaia.in
clubdeofertas 1230F54682FF-4CDA-839C-AA9FBCBF910A 595985511359

##---------------------------- nginx proxy manager
user marcelu.phd@gmail.com
pass @450Ab----28----nproxy

##---------------------------- SMTP
SMTP_HOST=smtp.gmail.com
PORT=587
USER=marcelu.phd@gmail.com
PASS=dmaatsjzgzxqxmil
SENDER=marcelu.phd@gmail.com


##----------------------STACKS
cal.b7g.app       calendar  
chat.b7g.app      chatwoot
evo.b7g.app       evolution
minio.b7g.app     minio
storage.b7g.app   storage minio
traefik           
editor.b7g.app    n8n_editor
n8n_mcp
editor-webhook    n8n_webhook
n8n_worker
nproxy
pgamdin.b7g.app   pgadmin
painel.b7g.app     portainer
postgres
rabbitmq.b7g.app  rabbitmq
redis
strapi.b7g.app    strapi
supabase.b7g.app  supabase
