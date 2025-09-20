#!/usr/bin/env python3

import os
import re
from pathlib import Path

def main():
    print("🔧 Updating additional health checks...")

    # Update the Chatwoot Baileys file in not_used folder
    baileys_file = Path("/home/galo/Desktop/stacks_producao/stacks/not_used/chatwoot-baileys.yml")

    if baileys_file.exists():
        print("📝 Updating Chatwoot Baileys health checks...")

        with open(baileys_file, 'r', encoding='utf-8') as file:
            content = file.read()

        # Update health check values
        content = re.sub(r'timeout:\s*\d+s', 'timeout: 180s', content)
        content = re.sub(r'interval:\s*\d+s', 'interval: 45s', content)
        content = re.sub(r'retries:\s*\d+', 'retries: 15', content)
        content = re.sub(r'start_period:\s*\d+s', 'start_period: 600s', content)

        with open(baileys_file, 'w', encoding='utf-8') as file:
            file.write(content)

        print("  ✅ Updated Chatwoot Baileys health checks")

    # Also update the local version
    local_baileys = Path("/home/galo/Desktop/stacks_producao/docker-local/chatwoot-baileys-local.yml")

    if local_baileys.exists():
        print("📝 Updating local Chatwoot Baileys health checks...")

        with open(local_baileys, 'r', encoding='utf-8') as file:
            content = file.read()

        # Update health check values
        content = re.sub(r'timeout:\s*\d+s', 'timeout: 180s', content)
        content = re.sub(r'interval:\s*\d+s', 'interval: 45s', content)
        content = re.sub(r'retries:\s*\d+', 'retries: 15', content)
        content = re.sub(r'start_period:\s*\d+s', 'start_period: 600s', content)

        with open(local_baileys, 'w', encoding='utf-8') as file:
            file.write(content)

        print("  ✅ Updated local Chatwoot Baileys health checks")

    print("\n✅ Additional health check updates completed!")

if __name__ == "__main__":
    main()