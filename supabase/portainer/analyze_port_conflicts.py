#!/usr/bin/env python3

import os
import yaml
import re
from pathlib import Path

def extract_ports_from_yml(file_path):
    """Extract port mappings from a Docker Compose YAML file"""
    ports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Load YAML
        data = yaml.safe_load(content)

        if 'services' in data:
            for service_name, service_config in data['services'].items():
                # Check ports section
                if 'ports' in service_config:
                    service_ports = service_config['ports']
                    if isinstance(service_ports, list):
                        for port in service_ports:
                            if isinstance(port, str):
                                # Format: "host:container" or "port"
                                if ':' in port:
                                    host_port = port.split(':')[0]
                                else:
                                    host_port = port
                                ports.append({
                                    'service': service_name,
                                    'port': host_port,
                                    'mapping': port
                                })
                            elif isinstance(port, dict):
                                # Format: {target: X, published: Y, protocol: tcp}
                                if 'published' in port:
                                    ports.append({
                                        'service': service_name,
                                        'port': str(port['published']),
                                        'mapping': f"{port.get('published', '')}:{port.get('target', '')}"
                                    })

                # Check labels for Traefik port configurations
                if 'deploy' in service_config and 'labels' in service_config['deploy']:
                    labels = service_config['deploy']['labels']
                    for label in labels:
                        if 'loadbalancer.server.port' in label:
                            port_match = re.search(r'loadbalancer\.server\.port=(\d+)', label)
                            if port_match:
                                ports.append({
                                    'service': service_name,
                                    'port': port_match.group(1),
                                    'mapping': f'traefik-internal:{port_match.group(1)}'
                                })

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return ports

def main():
    print("🔍 Analyzing port conflicts across all stack files...")

    # Define paths
    stacks_dir = Path("/home/galo/Desktop/stacks_producao/stacks")
    supabase_file = Path("/home/galo/Desktop/stacks_producao/supabase/portainer/supabase.yml")

    all_ports = {}

    # Analyze Supabase first
    print("\n📊 Analyzing Supabase ports...")
    supabase_ports = extract_ports_from_yml(supabase_file)
    all_ports['supabase'] = supabase_ports

    print("Supabase ports:")
    for port_info in supabase_ports:
        print(f"  - {port_info['service']}: {port_info['mapping']}")

    # Analyze all stack files
    print("\n📊 Analyzing existing stack files...")
    for yml_file in stacks_dir.glob("*.yml"):
        if yml_file.name.startswith('.'):
            continue

        stack_name = yml_file.stem
        print(f"\nAnalyzing {stack_name}...")

        stack_ports = extract_ports_from_yml(yml_file)
        all_ports[stack_name] = stack_ports

        if stack_ports:
            print(f"{stack_name} ports:")
            for port_info in stack_ports:
                print(f"  - {port_info['service']}: {port_info['mapping']}")
        else:
            print(f"{stack_name}: No external ports found")

    # Check for conflicts
    print("\n🚨 CONFLICT ANALYSIS:")
    print("=" * 50)

    port_usage = {}
    conflicts = []

    for stack_name, ports in all_ports.items():
        for port_info in ports:
            port = port_info['port']
            if port in port_usage:
                conflicts.append({
                    'port': port,
                    'stack1': port_usage[port],
                    'stack2': f"{stack_name}:{port_info['service']}"
                })
            else:
                port_usage[port] = f"{stack_name}:{port_info['service']}"

    if conflicts:
        print("⚠️  PORT CONFLICTS FOUND:")
        for conflict in conflicts:
            print(f"  🔴 Port {conflict['port']}: {conflict['stack1']} vs {conflict['stack2']}")
    else:
        print("✅ NO PORT CONFLICTS DETECTED!")

    # Summary
    print(f"\n📋 SUMMARY:")
    print(f"Total stacks analyzed: {len(all_ports)}")
    print(f"Total unique ports: {len(port_usage)}")
    print(f"Port conflicts: {len(conflicts)}")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if conflicts:
        print("1. Resolve port conflicts before deploying Supabase")
        print("2. Consider using different ports or removing conflicting stacks")
        print("3. Use Traefik routing instead of direct port exposure where possible")
    else:
        print("1. All ports are compatible - safe to deploy Supabase")
        print("2. Continue with current Traefik + Kong configuration")

    return len(conflicts) == 0

if __name__ == "__main__":
    main()