#!/bin/bash
# Supabase Server Deployment Script with Password Authentication
# Usage: ./deploy-supabase-server-with-password.sh [SERVER_IP] [SERVER_USER] [PASSWORD]

set -e

# Configuration
SERVER_IP="${1:-}"
SERVER_USER="${2:-root}"
SERVER_PASSWORD="${3:-}"
SERVER_PATH="/opt/supabase"
LOCAL_CONFIG_PATH="supabase/docker/volumes"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation
validate_inputs() {
    if [ -z "$SERVER_IP" ]; then
        print_error "Server IP is required!"
        echo "Usage: $0 <SERVER_IP> [SERVER_USER] [PASSWORD]"
        echo "Example: $0 192.168.1.100 ubuntu mypassword"
        exit 1
    fi

    if [ -z "$SERVER_PASSWORD" ]; then
        print_error "Password is required for this script!"
        echo "Usage: $0 <SERVER_IP> [SERVER_USER] [PASSWORD]"
        exit 1
    fi

    if [ ! -d "$LOCAL_CONFIG_PATH" ]; then
        print_error "Local Supabase config directory not found: $LOCAL_CONFIG_PATH"
        print_error "Please run this script from the stacks_producao directory."
        exit 1
    fi
}

# Function to execute SSH commands with password
ssh_exec() {
    expect -c "
        spawn ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP \"$1\"
        expect \"password:\"
        send \"$SERVER_PASSWORD\r\"
        expect eof
    "
}

# Function to execute SCP with password
scp_exec() {
    expect -c "
        spawn scp -o StrictHostKeyChecking=no $1 $SERVER_USER@$SERVER_IP:$2
        expect \"password:\"
        send \"$SERVER_PASSWORD\r\"
        expect eof
    "
}

# Function to test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection to $SERVER_USER@$SERVER_IP..."

    # Check if expect is available
    if ! command -v expect >/dev/null 2>&1; then
        print_error "expect command not found. Installing..."
        # Try to install expect
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update && sudo apt-get install -y expect
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y expect
        else
            print_error "Cannot install expect. Please install it manually."
            exit 1
        fi
    fi

    if ssh_exec "echo 'SSH connection test successful'"; then
        print_success "SSH connection successful"
    else
        print_error "SSH connection failed. Please check credentials and connectivity."
        exit 1
    fi
}

# Function to create server directory structure
create_server_directories() {
    print_status "Creating directory structure on server..."

    ssh_exec "
        # Create directories
        sudo mkdir -p $SERVER_PATH/{config,db-migrations,reference,scripts}
        sudo mkdir -p $SERVER_PATH/db-migrations/init
        sudo mkdir -p $SERVER_PATH/reference/{api,logs,pooler,db,authelia}

        # Set ownership and permissions
        sudo chown -R \$(whoami):docker $SERVER_PATH 2>/dev/null || sudo chown -R \$(whoami):\$(whoami) $SERVER_PATH
        sudo chmod -R 755 $SERVER_PATH

        echo 'Directory structure created successfully'
    "

    print_success "Server directories created"
}

# Function to transfer configuration files
transfer_config_files() {
    print_status "Transferring Supabase configuration files..."

    # Transfer core config files
    print_status "Transferring core configuration files..."
    if [ -f "$LOCAL_CONFIG_PATH/api/kong.yml" ]; then
        scp_exec "$LOCAL_CONFIG_PATH/api/kong.yml" "$SERVER_PATH/config/"
        print_success "Kong configuration transferred"
    else
        print_error "Kong configuration file not found: $LOCAL_CONFIG_PATH/api/kong.yml"
        exit 1
    fi

    if [ -f "$LOCAL_CONFIG_PATH/logs/vector.yml" ]; then
        scp_exec "$LOCAL_CONFIG_PATH/logs/vector.yml" "$SERVER_PATH/config/"
        print_success "Vector configuration transferred"
    else
        print_error "Vector configuration file not found: $LOCAL_CONFIG_PATH/logs/vector.yml"
        exit 1
    fi

    if [ -f "$LOCAL_CONFIG_PATH/pooler/pooler.exs" ]; then
        scp_exec "$LOCAL_CONFIG_PATH/pooler/pooler.exs" "$SERVER_PATH/config/"
        print_success "Pooler configuration transferred"
    else
        print_error "Pooler configuration file not found: $LOCAL_CONFIG_PATH/pooler/pooler.exs"
        exit 1
    fi

    # Transfer database migration files
    print_status "Transferring database migration files..."
    if [ -d "$LOCAL_CONFIG_PATH/db" ]; then
        for sql_file in "$LOCAL_CONFIG_PATH/db"/*.sql; do
            if [ -f "$sql_file" ]; then
                scp_exec "$sql_file" "$SERVER_PATH/db-migrations/"
            fi
        done

        if [ -f "$LOCAL_CONFIG_PATH/db/init/data.sql" ]; then
            scp_exec "$LOCAL_CONFIG_PATH/db/init/data.sql" "$SERVER_PATH/db-migrations/init/"
        fi
        print_success "Database migration files transferred"
    else
        print_warning "Database migration directory not found: $LOCAL_CONFIG_PATH/db"
    fi
}

# Function to create Docker configs
create_docker_configs() {
    print_status "Creating Docker configs on server..."

    ssh_exec "
        cd $SERVER_PATH

        # Check if Docker Swarm is initialized
        if ! docker info | grep -q 'Swarm: active'; then
            echo 'Docker Swarm not active. Initializing...'
            docker swarm init 2>/dev/null || echo 'Swarm already initialized or failed to initialize'
        fi

        # Create Docker configs (remove existing ones first)
        echo 'Creating Docker configurations...'

        # Kong config
        docker config rm supabase_kong_config 2>/dev/null || true
        docker config create supabase_kong_config config/kong.yml
        echo 'Kong config created'

        # Vector config
        docker config rm supabase_vector_config 2>/dev/null || true
        docker config create supabase_vector_config config/vector.yml
        echo 'Vector config created'

        # Pooler config
        docker config rm supabase_pooler_config 2>/dev/null || true
        docker config create supabase_pooler_config config/pooler.exs
        echo 'Pooler config created'

        # List created configs
        echo 'Created configs:'
        docker config ls | grep supabase
    "

    print_success "Docker configs created successfully"
}

# Function to transfer supabase.yml
transfer_stack_file() {
    print_status "Transferring supabase.yml stack file..."

    if [ -f "supabase.yml" ]; then
        scp_exec "supabase.yml" "$SERVER_PATH/"
        print_success "supabase.yml transferred"
    else
        print_error "supabase.yml not found in current directory"
        exit 1
    fi
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."

    ssh_exec "
        echo '=== Directory Structure ==='
        ls -la $SERVER_PATH/

        echo -e '\n=== Config Files ==='
        ls -la $SERVER_PATH/config/

        echo -e '\n=== Migration Files ==='
        ls -la $SERVER_PATH/db-migrations/

        echo -e '\n=== Docker Configs ==='
        docker config ls | grep supabase

        echo -e '\n=== Stack File ==='
        ls -la $SERVER_PATH/supabase.yml
    "

    print_success "Deployment verification completed"
}

# Function to display next steps
display_next_steps() {
    print_success "🎉 Supabase server deployment completed successfully!"
    echo
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. 🚀 Deploy the Supabase stack:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo "   cd $SERVER_PATH && docker stack deploy -c supabase.yml supabase"
    echo
    echo "2. 📈 Monitor deployment:"
    echo "   docker service ls | grep supabase"
    echo "   docker service logs -f supabase_vector"
    echo "   docker service logs -f supabase_analytics"
    echo
    echo "3. 🌐 Access services:"
    echo "   - Supabase API: https://supabase.senaia.in"
    echo "   - Supabase Studio: https://studio.senaia.in"
    echo "   - Connection Pooler: https://pooler.senaia.in"
    echo
    echo -e "${YELLOW}⚠️  Remember to:${NC}"
    echo "   - Update domain names in supabase.yml if needed"
    echo "   - Change default passwords and secrets for production"
    echo "   - Verify SSL certificates are properly configured"
}

# Main execution
main() {
    echo -e "${GREEN}🚀 Supabase Server Deployment Script (Password Auth)${NC}"
    echo -e "${BLUE}Target Server: $SERVER_USER@$SERVER_IP${NC}"
    echo

    validate_inputs
    test_ssh_connection
    create_server_directories
    transfer_config_files
    create_docker_configs
    transfer_stack_file
    verify_deployment
    display_next_steps
}

# Run main function
main "$@"