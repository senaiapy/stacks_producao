#!/usr/bin/env python3

import os
import re
from pathlib import Path

def update_health_check(file_path, new_timeout="120s", new_interval="30s", new_retries=10, new_start_period="300s"):
    """Update health check configuration in a YAML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Pattern to match healthcheck section
        healthcheck_pattern = r'(healthcheck:\s*\n(?:\s+.*\n)*?)'

        # New healthcheck configuration
        new_healthcheck = f"""healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/api/v1/accounts/1/profile || exit 1"]
      timeout: {new_timeout}
      interval: {new_interval}
      retries: {new_retries}
      start_period: {new_start_period}
"""

        # Update existing healthcheck or add if not present
        if 'healthcheck:' in content:
            # Replace existing healthcheck
            content = re.sub(
                r'healthcheck:\s*\n(?:\s+.*\n)*?(?=\s*[a-zA-Z_]|\Z)',
                new_healthcheck,
                content,
                flags=re.MULTILINE
            )

        # Update specific timeout and interval values if they exist
        content = re.sub(r'timeout:\s*\d+s', f'timeout: {new_timeout}', content)
        content = re.sub(r'interval:\s*\d+s', f'interval: {new_interval}', content)
        content = re.sub(r'retries:\s*\d+', f'retries: {new_retries}', content)
        content = re.sub(r'start_period:\s*\d+s', f'start_period: {new_start_period}', content)

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    print("🔧 Updating health checks for longer Supabase startup times...")

    # Define the base directory
    base_dir = Path("/home/galo/Desktop/stacks_producao")

    # Files to update with their specific configurations
    files_to_update = {
        # Chatwoot services
        "stacks/chatwoot.yml": {
            "timeout": "180s",
            "interval": "45s",
            "retries": 15,
            "start_period": "600s"
        },
        "stacks/chatwoot-baileys.yml": {
            "timeout": "180s",
            "interval": "45s",
            "retries": 15,
            "start_period": "600s"
        },
        "stacks/chatwoot-migration.yml": {
            "timeout": "300s",
            "interval": "60s",
            "retries": 20,
            "start_period": "900s"
        },

        # Evolution API
        "stacks/evolution.yml": {
            "timeout": "120s",
            "interval": "30s",
            "retries": 12,
            "start_period": "300s"
        },

        # PostgreSQL
        "stacks/postgres.yml": {
            "timeout": "60s",
            "interval": "15s",
            "retries": 20,
            "start_period": "120s"
        },

        # N8N services
        "stacks/n8n_editor.yml": {
            "timeout": "120s",
            "interval": "30s",
            "retries": 15,
            "start_period": "300s"
        },
        "stacks/n8n_webhook.yml": {
            "timeout": "90s",
            "interval": "20s",
            "retries": 12,
            "start_period": "240s"
        },
        "stacks/n8n_worker.yml": {
            "timeout": "90s",
            "interval": "20s",
            "retries": 12,
            "start_period": "240s"
        },
        "stacks/n8n_mcp.yml": {
            "timeout": "90s",
            "interval": "20s",
            "retries": 12,
            "start_period": "240s"
        }
    }

    updated_files = []

    for file_path, config in files_to_update.items():
        full_path = base_dir / file_path

        if full_path.exists():
            print(f"📝 Updating {file_path}...")

            try:
                with open(full_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Update health check values
                original_content = content

                # Update timeout values
                content = re.sub(
                    r'timeout:\s*\d+s',
                    f'timeout: {config["timeout"]}',
                    content
                )

                # Update interval values
                content = re.sub(
                    r'interval:\s*\d+s',
                    f'interval: {config["interval"]}',
                    content
                )

                # Update retries values
                content = re.sub(
                    r'retries:\s*\d+',
                    f'retries: {config["retries"]}',
                    content
                )

                # Update start_period values
                content = re.sub(
                    r'start_period:\s*\d+s',
                    f'start_period: {config["start_period"]}',
                    content
                )

                # For PostgreSQL, also update specific health check commands
                if 'postgres.yml' in file_path:
                    content = re.sub(
                        r'test:\s*\["CMD-SHELL",\s*"pg_isready.*?\]',
                        'test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB || exit 1"]',
                        content
                    )

                # For N8N services, update health check endpoints
                if 'n8n_' in file_path:
                    content = re.sub(
                        r'test:\s*\[.*?curl.*?\]',
                        'test: ["CMD-SHELL", "curl -f http://localhost:5678/healthz || exit 1"]',
                        content
                    )

                # For Evolution, update health check
                if 'evolution.yml' in file_path:
                    content = re.sub(
                        r'test:\s*\[.*?curl.*?\]',
                        'test: ["CMD-SHELL", "curl -f http://localhost:8080/manager/health || exit 1"]',
                        content
                    )

                # For Chatwoot, update health check
                if 'chatwoot' in file_path:
                    content = re.sub(
                        r'test:\s*\[.*?curl.*?\]',
                        'test: ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]',
                        content
                    )

                # Write back if changes were made
                if content != original_content:
                    with open(full_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    updated_files.append(file_path)
                    print(f"  ✅ Updated: timeout={config['timeout']}, interval={config['interval']}, retries={config['retries']}, start_period={config['start_period']}")
                else:
                    print(f"  ℹ️  No changes needed")

            except Exception as e:
                print(f"  ❌ Error updating {file_path}: {e}")
        else:
            print(f"  ⚠️  File not found: {file_path}")

    print(f"\n📊 Summary:")
    print(f"✅ Successfully updated {len(updated_files)} files")

    if updated_files:
        print(f"\n📝 Updated files:")
        for file_path in updated_files:
            print(f"  - {file_path}")

        print(f"\n🔄 Recommended next steps:")
        print(f"1. Review the updated configurations")
        print(f"2. Restart affected services: docker service update --force SERVICE_NAME")
        print(f"3. Monitor service startup times")
        print(f"4. Adjust values further if needed")

        # Show example commands for restarting services
        print(f"\n💡 Example restart commands:")
        service_names = {
            "chatwoot.yml": "chatwoot_chatwoot_rails",
            "evolution.yml": "evolution_evolution_v2",
            "postgres.yml": "postgres_postgres",
            "n8n_editor.yml": "n8n-editor_n8n_editor"
        }

        for file_path in updated_files:
            for file_key, service_name in service_names.items():
                if file_key in file_path:
                    print(f"  docker service update --force {service_name}")
                    break

    print(f"\n🎯 Health check improvements:")
    print(f"📈 Increased timeouts: 60s → 120-300s")
    print(f"📈 Increased intervals: 10s → 15-60s")
    print(f"📈 Increased retries: 3-5 → 10-20")
    print(f"📈 Increased start periods: 30s → 120-900s")
    print(f"\n✅ Services should now be more tolerant of Supabase startup delays!")

if __name__ == "__main__":
    main()