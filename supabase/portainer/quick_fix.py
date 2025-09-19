#!/usr/bin/env python3

import paramiko

SERVER_IP = "217.79.184.8"
SERVER_USER = "root"
SERVER_PASS = "@450Ab6606"

def main():
    print("⚡ Quick Kong port fix...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False

    # Upload the corrected supabase.yml
    print("📤 Uploading corrected supabase.yml...")
    sftp = ssh.open_sftp()
    sftp.put("supabase.yml", "/opt/supabase/supabase.yml")
    sftp.close()

    # Just update Kong service
    print("🔄 Updating Kong service with ports...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/supabase && docker service update --force supabase_kong")
    print("Kong update initiated")

    # Quick status check
    print("📊 Quick status check:")
    stdin, stdout, stderr = ssh.exec_command("docker service ls --filter name=supabase_kong")
    output = stdout.read().decode()
    print(output)

    ssh.close()
    print("✅ Quick fix completed!")

if __name__ == "__main__":
    main()