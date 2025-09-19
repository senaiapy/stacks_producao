#!/usr/bin/env python3
"""
Supabase Docker Swarm Manager
Único script para deploy, remoção, status e troubleshooting do Supabase
"""

import pexpect
import sys
import time

# Configurações do servidor
PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"
TIMEOUT = 30

def ssh_exec(command):
    """Execute SSH command with password authentication"""
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {USER}@{SERVER} "{command}"', timeout=TIMEOUT)
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if i == 0:
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        output = child.before.decode('utf-8')
        child.close()
        return output
    except:
        return "Error"

def scp_exec(local_file, remote_path):
    """Execute SCP command with password authentication"""
    try:
        child = pexpect.spawn(f'scp -o StrictHostKeyChecking=no {local_file} {USER}@{SERVER}:{remote_path}', timeout=TIMEOUT)
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        if i == 0:
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)
        child.close()
        return True
    except:
        return False

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Print formatted step"""
    print(f"\n📋 Passo {step}: {description}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def deploy_supabase():
    """Deploy complete Supabase stack"""
    print_header("Deploy Completo do Supabase")

    # Step 1: Create server directories
    print_step(1, "Criando estrutura de diretórios no servidor")
    result = ssh_exec("mkdir -p /opt/supabase/{config,db-migrations,reference}")
    print_success("Diretórios criados")

    # Step 2: Transfer config files
    print_step(2, "Transferindo arquivos de configuração")
    configs = [
        ("supabase/docker/volumes/api/kong.yml", "/opt/supabase/config/"),
        ("supabase/docker/volumes/logs/vector.yml", "/opt/supabase/config/"),
        ("supabase/docker/volumes/pooler/pooler.exs", "/opt/supabase/config/"),
        ("supabase.yml", "/opt/supabase/")
    ]

    for local_file, remote_path in configs:
        if scp_exec(local_file, remote_path):
            print_success(f"{local_file} transferido")
        else:
            print_error(f"Falha ao transferir {local_file}")

    # Step 3: Create Docker configs
    print_step(3, "Criando Docker configs")
    docker_configs = [
        ("supabase_kong_config", "/opt/supabase/config/kong.yml"),
        ("supabase_vector_config", "/opt/supabase/config/vector.yml"),
        ("supabase_pooler_config", "/opt/supabase/config/pooler.exs")
    ]

    for config_name, config_path in docker_configs:
        ssh_exec(f"docker config rm {config_name} 2>/dev/null || true")
        ssh_exec(f"docker config create {config_name} {config_path}")
        print_success(f"{config_name} criado")

    # Step 4: Setup database
    print_step(4, "Configurando banco de dados")
    db_commands = [
        "CREATE USER IF NOT EXISTS supabase_auth_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "CREATE USER IF NOT EXISTS supabase_storage_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "CREATE USER IF NOT EXISTS supabase_functions_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "CREATE USER IF NOT EXISTS authenticator WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "CREATE USER IF NOT EXISTS supabase_admin WITH LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';",
        "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_auth_admin;",
        "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_storage_admin;",
        "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_functions_admin;",
        "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO authenticator;",
        "GRANT ALL PRIVILEGES ON DATABASE chatwoot_database TO supabase_admin;",
        "CREATE SCHEMA IF NOT EXISTS _realtime;",
        "CREATE SCHEMA IF NOT EXISTS _analytics;",
        "CREATE SCHEMA IF NOT EXISTS storage;",
        "CREATE SCHEMA IF NOT EXISTS auth;",
        "CREATE SCHEMA IF NOT EXISTS extensions;",
        "GRANT ALL ON SCHEMA _realtime TO supabase_auth_admin;",
        "GRANT ALL ON SCHEMA storage TO supabase_storage_admin;",
        "GRANT ALL ON SCHEMA auth TO supabase_auth_admin;",
        "CREATE EXTENSION IF NOT EXISTS vector;",
        "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;",
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        "CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (version bigint NOT NULL, inserted_at timestamp(0) without time zone);"
    ]

    for cmd in db_commands:
        ssh_exec(f"docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"{cmd}\" 2>/dev/null")

    print_success("Banco de dados configurado")

    # Step 5: Create volumes
    print_step(5, "Criando volumes")
    volumes = ["supabase_storage", "supabase_functions"]
    for volume in volumes:
        ssh_exec(f"docker volume create {volume} 2>/dev/null || true")
    print_success("Volumes criados")

    # Step 6: Deploy stack
    print_step(6, "Deployando stack Supabase")
    result = ssh_exec("cd /opt/supabase && docker stack deploy -c supabase.yml supabase")
    print_success("Stack deployada")

    # Step 7: Wait and verify
    print_step(7, "Aguardando inicialização dos serviços")
    time.sleep(20)

    print_success("🎉 Deploy do Supabase concluído!")
    print_info("Aguarde alguns minutos para todos os serviços iniciarem")
    print_info("Use 'python3 supabase_manager.py status' para verificar")
    print_info("Acesse: https://studio.senaia.in")

def remove_stack_only():
    """Remove only Supabase stack, keep configs and volumes"""
    print_header("Removendo APENAS a Stack Supabase")
    print_info("Configurações, volumes e arquivos serão preservados")

    # Remove stack
    print_step(1, "Removendo stack Docker")
    result = ssh_exec("docker stack rm supabase")
    print_success("Stack removida")

    # Wait for cleanup
    print_step(2, "Aguardando limpeza dos serviços")
    time.sleep(20)

    # Verify removal
    print_step(3, "Verificando remoção")
    result = ssh_exec("docker service ls | grep supabase || echo 'Nenhum serviço Supabase encontrado'")
    print(result)

    print_success("✅ Stack removida com sucesso!")
    print_info("Configurações preservadas em /opt/supabase/")
    print_info("Para redeploy: python3 supabase_manager.py deploy")

def cleanup_complete():
    """Complete removal - stack, configs, volumes, files"""
    print_header("Remoção Completa do Supabase")
    print_error("⚠️  ATENÇÃO: Isso removerá TODOS os dados do Supabase!")

    # Remove stack
    print_step(1, "Removendo stack")
    ssh_exec("docker stack rm supabase")
    print_success("Stack removida")

    # Wait
    print_step(2, "Aguardando limpeza")
    time.sleep(20)

    # Remove configs
    print_step(3, "Removendo Docker configs")
    configs = ["supabase_kong_config", "supabase_vector_config", "supabase_pooler_config"]
    for config in configs:
        ssh_exec(f"docker config rm {config} 2>/dev/null || true")
    print_success("Configs removidos")

    # Remove volumes
    print_step(4, "Removendo volumes")
    volumes = ["supabase_storage", "supabase_functions"]
    for volume in volumes:
        ssh_exec(f"docker volume rm {volume} 2>/dev/null || true")
    print_success("Volumes removidos")

    # Remove files
    print_step(5, "Removendo arquivos do servidor")
    ssh_exec("rm -rf /opt/supabase")
    print_success("Arquivos removidos")

    print_success("🎉 Remoção completa concluída!")
    print_info("Todos os dados e configurações do Supabase foram removidos")

def show_status():
    """Show Supabase services status"""
    print_header("Status dos Serviços Supabase")

    # Services status
    print_step(1, "Status dos serviços")
    result = ssh_exec("docker service ls | grep supabase || echo 'Nenhum serviço Supabase encontrado'")
    print(result)

    # Check configs
    print_step(2, "Docker configs")
    result = ssh_exec("docker config ls | grep supabase || echo 'Nenhum config Supabase encontrado'")
    print(result)

    # Check volumes
    print_step(3, "Volumes")
    result = ssh_exec("docker volume ls | grep supabase || echo 'Nenhum volume Supabase encontrado'")
    print(result)

    # Check files
    print_step(4, "Arquivos no servidor")
    result = ssh_exec("ls -la /opt/supabase/ 2>/dev/null || echo 'Diretório /opt/supabase não encontrado'")
    print(result)

    # Recent logs
    print_step(5, "Logs recentes (erros)")
    services = ["auth", "storage", "studio", "kong"]
    for service in services:
        result = ssh_exec(f"docker service logs supabase_{service} 2>&1 | grep -i error | tail -3 2>/dev/null || echo 'Sem erros em supabase_{service}'")
        if result.strip() and "Sem erros" not in result:
            print(f"🔍 {service}: {result}")

def troubleshoot():
    """Run troubleshooting commands"""
    print_header("Troubleshooting Supabase")

    # Check failed services
    print_step(1, "Serviços com problemas")
    result = ssh_exec("docker service ls | grep supabase | grep -E '0/1|0/0' || echo 'Todos os serviços estão rodando'")
    print(result)

    # Restart problematic services
    if "0/" in result:
        print_step(2, "Reiniciando serviços com problemas")
        services = ["auth", "storage", "realtime", "functions", "studio"]
        for service in services:
            ssh_exec(f"docker service update --force supabase_{service} 2>/dev/null")
            print_success(f"supabase_{service} reiniciado")

    # Check database connectivity
    print_step(3, "Testando conectividade do banco")
    result = ssh_exec("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c 'SELECT 1;' 2>/dev/null && echo 'Banco OK' || echo 'Erro no banco'")
    print(result)

    # Check missing configs
    print_step(4, "Verificando configs ausentes")
    result = ssh_exec("docker config ls | grep supabase")
    if not result or "supabase_kong_config" not in result:
        print_error("Configs ausentes! Execute: python3 supabase_manager.py deploy")
    else:
        print_success("Configs OK")

def show_help():
    """Show help information"""
    print_header("Supabase Manager - Ajuda")
    print("""
Comandos disponíveis:

📦 DEPLOY
    python3 supabase_manager.py deploy
    - Deploy completo da stack Supabase
    - Cria configs, volumes, usuários do banco
    - Deploy da stack Docker Swarm

🗑️ REMOÇÃO
    python3 supabase_manager.py remove
    - Remove APENAS a stack (preserva configs/volumes)
    - Útil para restart rápido

    python3 supabase_manager.py cleanup
    - Remoção COMPLETA (configs, volumes, arquivos)
    - ⚠️  Remove todos os dados!

📊 STATUS E TROUBLESHOOTING
    python3 supabase_manager.py status
    - Mostra status de todos os serviços
    - Verifica configs, volumes, arquivos

    python3 supabase_manager.py troubleshoot
    - Diagnósticos automáticos
    - Reinicia serviços com problemas

🌐 ACESSO AOS SERVIÇOS
    - Studio: https://studio.senaia.in
    - API: https://supabase.senaia.in/rest/v1/
    - Pooler: pooler.senaia.in:6543

📖 MANUAL COMPLETO
    Ver: SUPABASE-COMPLETE-MANUAL.md
""")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "deploy":
        deploy_supabase()
    elif command == "remove":
        remove_stack_only()
    elif command == "cleanup":
        cleanup_complete()
    elif command == "status":
        show_status()
    elif command == "troubleshoot":
        troubleshoot()
    elif command == "help":
        show_help()
    else:
        print_error(f"Comando desconhecido: {command}")
        show_help()

if __name__ == "__main__":
    main()