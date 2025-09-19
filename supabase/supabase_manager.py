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

def show_status():
    """Show Supabase services status"""
    print_header("Status dos Serviços Supabase")

    # Services status
    print_step(1, "Status dos serviços")
    result = ssh_exec("docker service ls | grep supabase || echo 'Nenhum serviço Supabase encontrado'")
    print(result)

    # Check failed services
    print_step(2, "Serviços com problemas (0/1)")
    result = ssh_exec("docker service ls | grep supabase | grep -E '0/1|0/0' || echo 'Todos os serviços estão 1/1'")
    print(result)

    # Check service tasks
    print_step(3, "Status detalhado dos containers")
    result = ssh_exec("docker service ps $(docker service ls -q --filter name=supabase) --no-trunc | head -15")
    print(result)

def troubleshoot():
    """Run troubleshooting commands"""
    print_header("Troubleshooting Supabase")

    # Check failed services
    print_step(1, "Identificando serviços com problemas")
    result = ssh_exec("docker service ls | grep supabase | grep -E '0/1|0/0'")

    if result and "0/" in result:
        print("Serviços com problemas encontrados:")
        print(result)

        print_step(2, "Reiniciando serviços com problemas")
        failed_services = ["functions", "vector", "realtime", "storage"]

        for service in failed_services:
            print(f"Reiniciando supabase_{service}...")
            ssh_exec(f"docker service update --force supabase_{service}")
            time.sleep(5)

        print_success("Serviços reiniciados")

        print_step(3, "Aguardando reinicialização")
        time.sleep(30)

        print_step(4, "Verificando status após restart")
        result = ssh_exec("docker service ls | grep supabase")
        print(result)
    else:
        print_success("Todos os serviços estão rodando")

def fix_worker_errors():
    """Fix worker boot errors specifically"""
    print_header("Corrigindo Erros de Worker Boot")

    # Fix functions worker error
    print_step(1, "Criando diretório para Edge Functions")
    ssh_exec("docker exec $(docker service ps -q supabase_functions 2>/dev/null || echo 'no-container') mkdir -p /home/deno/functions/main 2>/dev/null || true")

    # Create a basic function
    print_step(2, "Criando função básica")
    ssh_exec("""docker exec $(docker service ps -q supabase_functions 2>/dev/null || echo 'no-container') sh -c 'echo "import { serve } from \\"https://deno.land/std@0.168.0/http/server.ts\\"; serve(() => new Response(\\"Hello Supabase!\\"));" > /home/deno/functions/main/index.ts' 2>/dev/null || true""")

    # Restart functions service
    print_step(3, "Reiniciando serviço de functions")
    ssh_exec("docker service update --force supabase_functions")

    # Restart vector service
    print_step(4, "Reiniciando serviço vector")
    ssh_exec("docker service update --force supabase_vector")

    print_success("Correções aplicadas")

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

def show_logs():
    """Show recent logs from problematic services"""
    print_header("Logs dos Serviços Supabase")

    services = ["auth", "functions", "vector", "storage", "studio"]

    for service in services:
        print_step(service.upper(), f"Logs do serviço supabase_{service}")
        result = ssh_exec(f"docker service logs supabase_{service} 2>&1 | tail -10 || echo 'Serviço não encontrado'")
        print(result)
        print("-" * 60)

def show_help():
    """Show help information"""
    print_header("Supabase Manager - Ajuda")
    print("""
Comandos disponíveis:

📊 STATUS E DIAGNÓSTICO
    python3 supabase_manager.py status
    - Mostra status de todos os serviços

    python3 supabase_manager.py troubleshoot
    - Diagnósticos e restart automático

    python3 supabase_manager.py fix-workers
    - Corrige erros específicos de worker boot

    python3 supabase_manager.py logs
    - Mostra logs recentes dos serviços

🗑️ REMOÇÃO
    python3 supabase_manager.py remove
    - Remove APENAS a stack (preserva configs/volumes)

🌐 ACESSO AOS SERVIÇOS
    - Studio: https://studio.senaia.in
    - API: https://supabase.senaia.in/rest/v1/

📖 MANUAL COMPLETO
    Ver: SUPABASE-COMPLETE-MANUAL.md
""")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "status":
        show_status()
    elif command == "troubleshoot":
        troubleshoot()
    elif command == "fix-workers":
        fix_worker_errors()
    elif command == "logs":
        show_logs()
    elif command == "remove":
        remove_stack_only()
    elif command == "help":
        show_help()
    else:
        print_error(f"Comando desconhecido: {command}")
        show_help()

if __name__ == "__main__":
    main()