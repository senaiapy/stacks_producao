#!/bin/bash
# Supabase Server Deployment Script
# Usage: ./deploy-supabase-server.sh [SERVER_IP] [SERVER_USER]

set -e

# Configuration
SERVER_IP="${1:-}"
SERVER_USER="${2:-root}"
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validation
validate_inputs() {
    if [ -z "$SERVER_IP" ]; then
        print_error "Server IP is required!"
        echo "Usage: $0 <SERVER_IP> [SERVER_USER]"
        echo "Example: $0 192.168.1.100 ubuntu"
        exit 1
    fi

    if ! command_exists "scp"; then
        print_error "scp command not found. Please install openssh-client."
        exit 1
    fi

    if ! command_exists "ssh"; then
        print_error "ssh command not found. Please install openssh-client."
        exit 1
    fi

    if [ ! -d "$LOCAL_CONFIG_PATH" ]; then
        print_error "Local Supabase config directory not found: $LOCAL_CONFIG_PATH"
        print_error "Please run this script from the stacks_producao directory."
        exit 1
    fi
}

# Function to test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection to $SERVER_USER@$SERVER_IP..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" exit 2>/dev/null; then
        print_success "SSH connection successful"
    else
        print_error "SSH connection failed. Please check:"
        echo "  - Server IP: $SERVER_IP"
        echo "  - Username: $SERVER_USER"
        echo "  - SSH key authentication is set up"
        echo "  - Server is reachable"
        exit 1
    fi
}

# Function to create server directory structure
create_server_directories() {
    print_status "Creating directory structure on server..."

    ssh "$SERVER_USER@$SERVER_IP" "
        # Create directories
        sudo mkdir -p $SERVER_PATH/{config,db-migrations,reference,scripts}
        sudo mkdir -p $SERVER_PATH/db-migrations/init
        sudo mkdir -p $SERVER_PATH/reference/{api,logs,pooler,db,authelia}

        # Set ownership and permissions
        sudo chown -R \$(whoami):docker $SERVER_PATH 2>/dev/null || sudo chown -R \$(whoami):\$(whoami) $SERVER_PATH
        sudo chmod -R 755 $SERVER_PATH

        echo 'Directory structure created successfully'
    "

    if [ $? -eq 0 ]; then
        print_success "Server directories created"
    else
        print_error "Failed to create server directories"
        exit 1
    fi
}

# Function to transfer configuration files
transfer_config_files() {
    print_status "Transferring Supabase configuration files..."

    # Transfer core config files
    print_status "Transferring core configuration files..."
    if [ -f "$LOCAL_CONFIG_PATH/api/kong.yml" ]; then
        scp "$LOCAL_CONFIG_PATH/api/kong.yml" "$SERVER_USER@$SERVER_IP:$SERVER_PATH/config/"
        print_success "Kong configuration transferred"
    else
        print_error "Kong configuration file not found: $LOCAL_CONFIG_PATH/api/kong.yml"
        exit 1
    fi

    if [ -f "$LOCAL_CONFIG_PATH/logs/vector.yml" ]; then
        scp "$LOCAL_CONFIG_PATH/logs/vector.yml" "$SERVER_USER@$SERVER_IP:$SERVER_PATH/config/"
        print_success "Vector configuration transferred"
    else
        print_error "Vector configuration file not found: $LOCAL_CONFIG_PATH/logs/vector.yml"
        exit 1
    fi

    if [ -f "$LOCAL_CONFIG_PATH/pooler/pooler.exs" ]; then
        scp "$LOCAL_CONFIG_PATH/pooler/pooler.exs" "$SERVER_USER@$SERVER_IP:$SERVER_PATH/config/"
        print_success "Pooler configuration transferred"
    else
        print_error "Pooler configuration file not found: $LOCAL_CONFIG_PATH/pooler/pooler.exs"
        exit 1
    fi

    # Transfer database migration files
    print_status "Transferring database migration files..."
    if [ -d "$LOCAL_CONFIG_PATH/db" ]; then
        scp "$LOCAL_CONFIG_PATH/db"/*.sql "$SERVER_USER@$SERVER_IP:$SERVER_PATH/db-migrations/" 2>/dev/null || true
        if [ -f "$LOCAL_CONFIG_PATH/db/init/data.sql" ]; then
            scp "$LOCAL_CONFIG_PATH/db/init/data.sql" "$SERVER_USER@$SERVER_IP:$SERVER_PATH/db-migrations/init/"
        fi
        print_success "Database migration files transferred"
    else
        print_warning "Database migration directory not found: $LOCAL_CONFIG_PATH/db"
    fi

    # Transfer reference files for backup
    print_status "Transferring reference files..."
    scp -r "$LOCAL_CONFIG_PATH/"* "$SERVER_USER@$SERVER_IP:$SERVER_PATH/reference/" 2>/dev/null || true
    print_success "Reference files transferred"
}

# Function to create Docker configs
create_docker_configs() {
    print_status "Creating Docker configs on server..."

    ssh "$SERVER_USER@$SERVER_IP" "
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

    if [ $? -eq 0 ]; then
        print_success "Docker configs created successfully"
    else
        print_error "Failed to create Docker configs"
        exit 1
    fi
}

# Function to transfer supabase.yml
transfer_stack_file() {
    print_status "Transferring supabase.yml stack file..."

    if [ -f "supabase.yml" ]; then
        scp "supabase.yml" "$SERVER_USER@$SERVER_IP:$SERVER_PATH/"
        print_success "supabase.yml transferred"
    else
        print_error "supabase.yml not found in current directory"
        exit 1
    fi
}

# Function to create migration script
create_migration_script() {
    print_status "Creating database migration script on server..."

    ssh "$SERVER_USER@$SERVER_IP" "cat > $SERVER_PATH/scripts/run-migrations.sh << 'EOF'
#!/bin/bash
# Database Migration Script for Supabase

set -e

DB_HOST=\${1:-postgres}
DB_USER=\${2:-postgres}
DB_NAME=\${3:-chatwoot_database}

echo \"Running Supabase database migrations...\"
echo \"Database: \$DB_HOST, User: \$DB_USER, Database: \$DB_NAME\"

MIGRATION_DIR=\"$SERVER_PATH/db-migrations\"

# Check if PostgreSQL is accessible
if ! docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -c 'SELECT 1;' >/dev/null 2>&1; then
    echo \"ERROR: Cannot connect to PostgreSQL. Please check:\"
    echo \"  - PostgreSQL service is running\"
    echo \"  - Database credentials are correct\"
    echo \"  - Network connectivity\"
    exit 1
fi

# Run migrations in order
echo \"Executing migration files...\"

if [ -f \"\$MIGRATION_DIR/roles.sql\" ]; then
    echo \"Running roles.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/roles.sql
fi

if [ -f \"\$MIGRATION_DIR/realtime.sql\" ]; then
    echo \"Running realtime.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/realtime.sql
fi

if [ -f \"\$MIGRATION_DIR/jwt.sql\" ]; then
    echo \"Running jwt.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/jwt.sql
fi

if [ -f \"\$MIGRATION_DIR/logs.sql\" ]; then
    echo \"Running logs.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/logs.sql
fi

if [ -f \"\$MIGRATION_DIR/pooler.sql\" ]; then
    echo \"Running pooler.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/pooler.sql
fi

if [ -f \"\$MIGRATION_DIR/_supabase.sql\" ]; then
    echo \"Running _supabase.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/_supabase.sql
fi

if [ -f \"\$MIGRATION_DIR/webhooks.sql\" ]; then
    echo \"Running webhooks.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/webhooks.sql
fi

if [ -f \"\$MIGRATION_DIR/init/data.sql\" ]; then
    echo \"Running init/data.sql...\"
    docker exec postgres_postgres psql -h \$DB_HOST -U \$DB_USER -d \$DB_NAME -f /tmp/init/data.sql
fi

echo \"✅ Database migrations completed successfully!\"
EOF

chmod +x $SERVER_PATH/scripts/run-migrations.sh
echo 'Migration script created at $SERVER_PATH/scripts/run-migrations.sh'
"

    print_success "Migration script created"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."

    ssh "$SERVER_USER@$SERVER_IP" "
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
    echo "1. 📊 Run database migrations:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo "   $SERVER_PATH/scripts/run-migrations.sh"
    echo
    echo "2. 🚀 Deploy the Supabase stack:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo "   cd $SERVER_PATH && docker stack deploy -c supabase.yml supabase"
    echo
    echo "3. 📈 Monitor deployment:"
    echo "   docker service ls | grep supabase"
    echo "   docker service logs -f supabase_vector"
    echo "   docker service logs -f supabase_analytics"
    echo
    echo "4. 🌐 Access services:"
    echo "   - Supabase API: https://supabase.yourdomain.com"
    echo "   - Supabase Studio: https://studio.yourdomain.com"
    echo "   - Connection Pooler: https://pooler.yourdomain.com"
    echo
    echo -e "${YELLOW}⚠️  Remember to:${NC}"
    echo "   - Update domain names in supabase.yml if needed"
    echo "   - Change default passwords and secrets for production"
    echo "   - Verify SSL certificates are properly configured"
}

# Main execution
main() {
    echo -e "${GREEN}🚀 Supabase Server Deployment Script${NC}"
    echo -e "${BLUE}Target Server: $SERVER_USER@$SERVER_IP${NC}"
    echo

    validate_inputs
    test_ssh_connection
    create_server_directories
    transfer_config_files
    create_docker_configs
    transfer_stack_file
    create_migration_script
    verify_deployment
    display_next_steps
}

# Run main function
main "$@"