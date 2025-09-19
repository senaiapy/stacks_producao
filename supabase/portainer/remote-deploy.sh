#!/usr/bin/expect -f

# Supabase Remote Deployment Script
set timeout 60
set server "217.79.184.8"
set user "root"
set password "@450Ab6606"

# Function to execute command on remote server
proc remote_exec {cmd} {
    global server user password
    spawn ssh $user@$server $cmd
    expect {
        "password:" { send "$password\r"; exp_continue }
        "yes/no" { send "yes\r"; exp_continue }
        eof
    }
}

puts "🚀 Starting Supabase deployment to $server"

puts "📋 Step 1: Verifying Docker Swarm..."
remote_exec "docker node ls"

puts "📂 Step 2: Creating directories..."
remote_exec "mkdir -p /opt/supabase"
remote_exec "mkdir -p /mnt/data/supabase/{api,storage,db,functions,logs}"
remote_exec "mkdir -p /mnt/data/supabase/db/{data,init}"

puts "✅ Deployment preparation complete!"
puts "Next: Transfer files manually and run deployment"