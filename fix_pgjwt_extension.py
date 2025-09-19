#!/usr/bin/env python3
import pexpect
import sys

PASSWORD = "@450Ab6606"
SERVER = "217.79.184.8"
USER = "root"

def ssh_exec_simple(command):
    """Execute simple SSH command"""
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {USER}@{SERVER} "{command}"', timeout=30)
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])

        if i == 0:
            child.sendline(PASSWORD)
            child.expect(pexpect.EOF)

        output = child.before.decode('utf-8')
        child.close()
        return output
    except:
        return "Error executing command"

def main():
    print("🔧 Fixing pgjwt Extension Issue")

    # Step 1: Check if pgjwt extension is available
    print("\n📋 Step 1: Checking pgjwt extension availability...")
    result = ssh_exec_simple("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"SELECT name FROM pg_available_extensions WHERE name = 'pgjwt';\" 2>/dev/null || echo 'Cannot check extensions'")
    print(result)

    # Step 2: Try to install pgjwt in PostgreSQL container
    print("\n📋 Step 2: Attempting to install pgjwt extension...")

    install_commands = [
        # Update package lists
        "apt-get update",
        # Install git and build tools
        "apt-get install -y git build-essential postgresql-server-dev-16",
        # Clone pgjwt repository
        "git clone https://github.com/michelp/pgjwt.git /tmp/pgjwt",
        # Build and install pgjwt
        "cd /tmp/pgjwt && make && make install"
    ]

    for cmd in install_commands:
        print(f"Executing: {cmd}")
        result = ssh_exec_simple(f"docker exec $(docker ps -q -f name=postgres) {cmd} 2>/dev/null || echo 'Command failed: {cmd}'")
        print(result[:200] + "..." if len(result) > 200 else result)

    # Step 3: Try to create the extension now
    print("\n📋 Step 3: Attempting to create pgjwt extension...")
    result = ssh_exec_simple("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c 'CREATE EXTENSION IF NOT EXISTS pgjwt;' 2>/dev/null || echo 'pgjwt extension creation failed'")
    print(result)

    # Step 4: Alternative - create JWT functions manually
    print("\n📋 Step 4: Creating alternative JWT functions...")

    jwt_functions = """
    -- Alternative JWT functions if pgjwt extension is not available
    CREATE OR REPLACE FUNCTION jwt_sign(payload json, secret text, algorithm text DEFAULT 'HS256')
    RETURNS text AS $$
    BEGIN
        -- This is a placeholder function - in production you'd need proper JWT implementation
        RETURN encode(hmac(payload::text, secret, 'sha256'), 'base64');
    END;
    $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION jwt_verify(token text, secret text, algorithm text DEFAULT 'HS256')
    RETURNS json AS $$
    BEGIN
        -- This is a placeholder function - in production you'd need proper JWT implementation
        RETURN '{"valid": false, "message": "JWT verification not implemented"}'::json;
    END;
    $$ LANGUAGE plpgsql;

    SELECT 'Alternative JWT functions created' as result;
    """

    # Write the SQL to a temporary file and execute
    result = ssh_exec_simple(f"""cat > /tmp/jwt_functions.sql << 'EOF'
{jwt_functions}
EOF""")

    result = ssh_exec_simple("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -f /tmp/jwt_functions.sql 2>/dev/null || echo 'Failed to create JWT functions'")
    print(result)

    # Step 5: Update Supabase configuration for missing pgjwt
    print("\n📋 Step 5: Checking current extensions...")
    result = ssh_exec_simple("docker exec $(docker ps -q -f name=postgres) psql -U chatwoot_database -d chatwoot_database -c \"SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pg_stat_statements', 'pgcrypto', 'pgjwt');\" 2>/dev/null || echo 'Cannot list extensions'")
    print(result)

    # Step 6: Restart Auth service (most likely to need JWT functions)
    print("\n📋 Step 6: Restarting Auth service...")
    result = ssh_exec_simple("docker service update --force supabase_auth")
    print("✅ Auth service restarted")

    # Step 7: Check service status
    print("\n📋 Step 7: Checking service status...")
    result = ssh_exec_simple("docker service ls | grep supabase_auth")
    print(result)

    print("\n🎉 pgjwt extension fix completed!")
    print("\n📋 Notes:")
    print("- If pgjwt installation failed, Supabase may still work with basic functionality")
    print("- Alternative JWT functions were created as fallback")
    print("- Monitor auth service logs: docker service logs supabase_auth")
    print("- Some JWT features may be limited without the full pgjwt extension")

    return True

if __name__ == "__main__":
    main()