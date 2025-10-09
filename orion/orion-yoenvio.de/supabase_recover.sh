#!/bin/bash

################################################################################
# Supabase Recovery Script
# Server: 89.163.146.106 (yoenvio.de)
# Purpose: Complete recovery of all Supabase services
# Usage: ./supabase_recover.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="89.163.146.106"
SERVER_USER="root"
SERVER_PASS="@450Ab6606289828server"
STACK_FILE="/root/supabase.yaml"
DB_PASSWORD="949d2fafe7dee2ab620252a58dbb6bdd"
JWT_SECRET="11b614eb3cb2373fdf35f510db20bcbc0c55db74"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

execute_remote() {
    local description=$1
    local command=$2

    print_step "$description"

    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$command"

    if [ $? -eq 0 ]; then
        print_success "$description - Concluído"
        return 0
    else
        print_error "$description - Falhou"
        return 1
    fi
}

wait_with_spinner() {
    local duration=$1
    local message=$2

    echo -ne "${YELLOW}⏳ $message "

    for ((i=1; i<=duration; i++)); do
        echo -n "."
        sleep 1
    done

    echo -e " ✓${NC}"
}

################################################################################
# MAIN RECOVERY PROCESS
################################################################################

print_header "🚀 SUPABASE RECOVERY SCRIPT - YOENVIO.DE"

echo -e "${BLUE}Servidor:${NC} $SERVER_IP"
echo -e "${BLUE}Stack:${NC} $STACK_FILE"
echo -e ""
read -p "Deseja continuar com a recuperação? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operação cancelada."
    exit 0
fi

################################################################################
# STEP 1: Remove existing stack
################################################################################

print_header "PASSO 1: Removendo Stack Existente"

execute_remote "Removendo stack supabase" "docker stack rm supabase"

wait_with_spinner 30 "Aguardando remoção completa"

################################################################################
# STEP 2: Create directories and set permissions
################################################################################

print_header "PASSO 2: Preparando Estrutura de Diretórios"

execute_remote "Criando diretórios base" "mkdir -p /root/supabase/docker/volumes/db/data"
execute_remote "Criando diretório storage" "mkdir -p /root/supabase/docker/volumes/storage"
execute_remote "Criando diretório functions" "mkdir -p /root/supabase/docker/volumes/functions"

execute_remote "Definindo permissões (UID 999)" "chown -R 999:999 /root/supabase/docker/volumes/db/data"
execute_remote "Definindo permissões de acesso" "chmod 700 /root/supabase/docker/volumes/db/data"

################################################################################
# STEP 3: Verify required files
################################################################################

print_header "PASSO 3: Verificando Arquivos Necessários"

sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "ls -la /root/supabase/docker/volumes/db/*.sql 2>/dev/null" > /tmp/supabase_files.txt

if grep -q "roles.sql" /tmp/supabase_files.txt; then
    print_success "Arquivos SQL encontrados"
else
    print_error "Arquivos SQL não encontrados!"
    echo "Os seguintes arquivos devem existir em /root/supabase/docker/volumes/db/:"
    echo "  - _supabase.sql"
    echo "  - jwt.sql"
    echo "  - logs.sql"
    echo "  - pooler.sql"
    echo "  - realtime.sql"
    echo "  - roles.sql"
    echo "  - webhooks.sql"
fi

################################################################################
# STEP 4: Create Docker volumes
################################################################################

print_header "PASSO 4: Verificando Volumes Docker"

sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << 'ENDSSH'
if ! docker volume ls | grep -q supabase_db_config; then
    docker volume create supabase_db_config
    echo "Volume supabase_db_config criado"
else
    echo "Volume supabase_db_config já existe"
fi
ENDSSH

print_success "Volumes verificados"

################################################################################
# STEP 5: Deploy stack
################################################################################

print_header "PASSO 5: Deploying Stack Supabase"

execute_remote "Deploy da stack" "cd /root && docker stack deploy -c supabase.yaml supabase"

wait_with_spinner 60 "Aguardando inicialização dos serviços"

################################################################################
# STEP 6: Verify initial deployment
################################################################################

print_header "PASSO 6: Verificando Status Inicial"

echo -e "${BLUE}Status dos Serviços:${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker service ls | grep supabase"

wait_with_spinner 30 "Aguardando estabilização"

################################################################################
# STEP 7: Create _supabase database and schemas
################################################################################

print_header "PASSO 7: Criando Database e Schemas"

execute_remote "Criando database _supabase e schemas" "docker exec \$(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
-- Criar database _supabase
CREATE DATABASE _supabase;

-- Conectar ao _supabase
\c _supabase

-- Criar schema _analytics
CREATE SCHEMA IF NOT EXISTS _analytics;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE _supabase TO supabase_admin;
GRANT ALL ON SCHEMA _analytics TO supabase_admin;

-- Voltar ao postgres
\c postgres

-- Verificar databases
SELECT datname FROM pg_database WHERE datname NOT IN ('template0', 'template1');
EOF
"

if [ $? -eq 0 ]; then
    print_success "Database _supabase criado com sucesso"
else
    print_error "Falha ao criar database _supabase"
fi

################################################################################
# STEP 8: Restart analytics service
################################################################################

print_header "PASSO 8: Reiniciando Analytics Service"

execute_remote "Reiniciando supabase_analytics" "docker service update --force supabase_analytics"

wait_with_spinner 20 "Aguardando restart do analytics"

################################################################################
# STEP 9: Fix auth schema permissions
################################################################################

print_header "PASSO 9: Configurando Permissões do Auth Schema"

execute_remote "Configurando permissões auth" "docker exec \$(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres << 'EOF'
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

-- Transferir ownership de tabelas existentes
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'auth'
    LOOP
        EXECUTE 'ALTER TABLE auth.' || quote_ident(r.tablename) || ' OWNER TO supabase_auth_admin';
    END LOOP;
END \$\$;

-- Conceder permissões em todas as tabelas
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO supabase_auth_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO supabase_auth_admin;

-- Definir permissões padrão para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO supabase_auth_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON SEQUENCES TO supabase_auth_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON FUNCTIONS TO supabase_auth_admin;

-- Criar schemas adicionais se não existirem
CREATE SCHEMA IF NOT EXISTS storage;
CREATE SCHEMA IF NOT EXISTS _realtime;

-- Conceder permissões
GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
GRANT ALL ON SCHEMA _realtime TO supabase_admin;
EOF
"

if [ $? -eq 0 ]; then
    print_success "Permissões do auth configuradas"
else
    print_error "Falha ao configurar permissões do auth"
fi

################################################################################
# STEP 10: Restart auth service
################################################################################

print_header "PASSO 10: Reiniciando Auth Service"

execute_remote "Reiniciando supabase_auth" "docker service update --force supabase_auth"

wait_with_spinner 30 "Aguardando restart do auth"

################################################################################
# STEP 11: Restart all potentially affected services
################################################################################

print_header "PASSO 11: Reiniciando Serviços Dependentes"

services=("supabase_rest" "supabase_realtime" "supabase_storage" "supabase_supavisor")

for service in "${services[@]}"; do
    execute_remote "Reiniciando $service" "docker service update --force $service"
    sleep 5
done

wait_with_spinner 30 "Aguardando estabilização final"

################################################################################
# STEP 12: Final verification
################################################################################

print_header "PASSO 12: Verificação Final"

echo -e "${BLUE}Status Final dos Serviços:${NC}"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker service ls | grep supabase"

echo ""
print_step "Contando serviços com status 1/1"

services_ok=$(sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker service ls | grep supabase | grep -c '1/1'")
total_services=$(sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker service ls | grep supabase | wc -l")

echo -e "${BLUE}Serviços funcionando:${NC} $services_ok de $total_services"

if [ "$services_ok" -ge 12 ]; then
    print_success "Recuperação bem-sucedida! (12+ serviços ativos)"
elif [ "$services_ok" -ge 10 ]; then
    echo -e "${YELLOW}⚠ Recuperação parcial ($services_ok serviços ativos)${NC}"
else
    print_error "Recuperação com problemas ($services_ok serviços ativos)"
fi

################################################################################
# STEP 13: Test endpoints
################################################################################

print_header "PASSO 13: Testando Endpoints"

print_step "Testando Studio (HTTPS)"
if curl -s -I https://supabase.yoenvio.de | grep -q "200\|301\|302"; then
    print_success "Studio acessível"
else
    print_error "Studio não acessível"
fi

print_step "Testando REST API"
if curl -s -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.yzIH3Tb0PeX8SIiIQruWNNjFxRi6TIgV3C85pBgpNaA" https://supabase.yoenvio.de/rest/v1/ | grep -q "message\|hint\|error\|tables"; then
    print_success "REST API respondendo"
else
    print_error "REST API não está respondendo corretamente"
fi

################################################################################
# STEP 14: Database verification
################################################################################

print_header "PASSO 14: Verificando Banco de Dados"

print_step "Listando databases"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker exec \$(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres -c '\l' 2>/dev/null | grep -E '(postgres|_supabase)'"

print_step "Listando schemas"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker exec \$(docker ps -q -f name=supabase_db) psql -U supabase_admin -d postgres -c '\dn' 2>/dev/null | grep -E '(auth|storage|_realtime|_analytics)'"

################################################################################
# STEP 15: Generate report
################################################################################

print_header "PASSO 15: Relatório de Recuperação"

# Get service details
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "docker service ls | grep supabase" > /tmp/supabase_status.txt

echo -e "${BLUE}┌─────────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│                    RELATÓRIO DE RECUPERAÇÃO                     │${NC}"
echo -e "${BLUE}├─────────────────────────────────────────────────────────────────┤${NC}"

# Count services
while IFS= read -r line; do
    service_name=$(echo "$line" | awk '{print $2}')
    replicas=$(echo "$line" | awk '{print $4}')

    if [[ "$replicas" == "1/1" ]]; then
        echo -e "${BLUE}│${NC} ${GREEN}✓${NC} $(printf '%-59s' "$service_name") ${BLUE}│${NC}"
    else
        echo -e "${BLUE}│${NC} ${RED}✗${NC} $(printf '%-59s' "$service_name") ${BLUE}│${NC}"
    fi
done < /tmp/supabase_status.txt

echo -e "${BLUE}├─────────────────────────────────────────────────────────────────┤${NC}"
echo -e "${BLUE}│ Total de Serviços:${NC} $(printf '%45s' "$total_services") ${BLUE}│${NC}"
echo -e "${BLUE}│ Serviços Ativos:${NC} $(printf '%47s' "$services_ok") ${BLUE}│${NC}"
echo -e "${BLUE}│ Serviços com Problemas:${NC} $(printf '%38s' "$((total_services - services_ok))") ${BLUE}│${NC}"
echo -e "${BLUE}├─────────────────────────────────────────────────────────────────┤${NC}"
echo -e "${BLUE}│ URLs de Acesso:                                                 │${NC}"
echo -e "${BLUE}│${NC}   Studio: https://supabase.yoenvio.de                        ${BLUE}│${NC}"
echo -e "${BLUE}│${NC}   API:    https://supabase.yoenvio.de/rest/v1/               ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────────┘${NC}"

################################################################################
# CLEANUP AND FINAL MESSAGES
################################################################################

print_header "✅ RECUPERAÇÃO CONCLUÍDA"

echo -e "${GREEN}Próximos passos:${NC}"
echo "1. Acesse o Studio: https://supabase.yoenvio.de"
echo "2. Verifique os logs de serviços com problemas:"
echo "   docker service logs supabase_SERVICE_NAME --tail 50"
echo "3. Para serviços que ainda estão 0/1, execute:"
echo "   docker service update --force supabase_SERVICE_NAME"
echo ""

if [ "$services_ok" -lt 12 ]; then
    echo -e "${YELLOW}⚠ Alguns serviços ainda apresentam problemas.${NC}"
    echo "Execute os seguintes comandos no servidor para diagnóstico:"
    echo ""

    # List problematic services
    while IFS= read -r line; do
        replicas=$(echo "$line" | awk '{print $4}')
        service_name=$(echo "$line" | awk '{print $2}')

        if [[ "$replicas" != "1/1" ]]; then
            echo "  docker service logs $service_name --tail 20"
        fi
    done < /tmp/supabase_status.txt

    echo ""
fi

echo -e "${GREEN}Para mais informações, consulte:${NC}"
echo "  - Manual completo: orion/orion-yoenvio.de/supabase/MANUAL.md"
echo "  - Logs do servidor: ssh root@89.163.146.106"
echo ""

# Save recovery log
RECOVERY_LOG="/tmp/supabase_recovery_$(date +%Y%m%d_%H%M%S).log"
echo "Log de recuperação salvo em: $RECOVERY_LOG"

{
    echo "Supabase Recovery Log"
    echo "Data: $(date)"
    echo "Servidor: $SERVER_IP"
    echo "Serviços ativos: $services_ok de $total_services"
    echo ""
    echo "Status dos Serviços:"
    cat /tmp/supabase_status.txt
} > "$RECOVERY_LOG"

print_success "Script de recuperação finalizado!"

exit 0
