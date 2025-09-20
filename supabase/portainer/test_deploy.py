#!/usr/bin/env python3
"""
Simple test version to debug the deployment script
"""

import paramiko
import os
import sys
import time

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def test_connection():
    print("🔧 Testing SSH connection...")
    sys.stdout.flush()

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(f"📡 Connecting to {SERVER_IP}...")
        sys.stdout.flush()

        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)

        print("✅ SSH connection successful!")

        # Test a simple command
        print("🔍 Testing command execution...")
        stdin, stdout, stderr = ssh.exec_command("echo 'Hello from server'")
        output = stdout.read().decode().strip()

        print(f"📋 Server response: {output}")

        ssh.close()
        return True

    except Exception as e:
        print(f"❌ SSH test failed: {e}")
        return False

def main():
    print("🚀 Starting simple deployment test...")
    sys.stdout.flush()

    # Check local file
    if not os.path.exists("supabase.yml"):
        print("❌ supabase.yml not found")
        return False

    print("✅ supabase.yml found")

    # Test SSH
    if not test_connection():
        return False

    print("🎉 All tests passed!")
    return True

if __name__ == "__main__":
    main()