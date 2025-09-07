#!/usr/bin/env python3
"""
Railway Environment Variables Checker
Script to check and compare environment variables between local .env and Railway
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Set

def load_env_file(filepath: str) -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")

    return env_vars

def check_railway_cli() -> bool:
    """Check if Railway CLI is installed and user is logged in"""
    try:
        result = subprocess.run(['railway', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Railway CLI installed: {result.stdout.strip()}")

            # Check if logged in
            result = subprocess.run(['railway', 'whoami'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Logged in as: {result.stdout.strip()}")
                return True
            else:
                print("❌ Not logged in to Railway")
                print("Run: railway login")
                return False
        else:
            print("❌ Railway CLI not installed")
            print("Install with: npm install -g @railway/cli")
            return False
    except FileNotFoundError:
        print("❌ Railway CLI not found")
        print("Install with: npm install -g @railway/cli")
        return False
    except Exception as e:
        print(f"❌ Error checking Railway CLI: {e}")
        return False

def get_railway_variables() -> Dict[str, str]:
    """Get environment variables from Railway project"""
    try:
        print("🔍 Fetching Railway environment variables...")

        # Get variables
        result = subprocess.run(['railway', 'variables'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            # Parse the output (Railway CLI typically outputs in a table format)
            lines = result.stdout.strip().split('\n')
            railway_vars = {}

            # Skip header lines and parse variable lines
            for line in lines[1:]:  # Skip first line (header)
                if line.strip() and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value != '-':  # Skip unset variables
                            railway_vars[key] = value

            return railway_vars
        else:
            print(f"❌ Failed to get Railway variables: {result.stderr}")
            return {}

    except subprocess.TimeoutExpired:
        print("❌ Timeout getting Railway variables")
        return {}
    except Exception as e:
        print(f"❌ Error getting Railway variables: {e}")
        return {}

def compare_variables(local_vars: Dict[str, str], railway_vars: Dict[str, str]) -> Dict[str, List[str]]:
    """Compare local and Railway environment variables"""
    local_keys = set(local_vars.keys())
    railway_keys = set(railway_vars.keys())

    return {
        'only_local': sorted(list(local_keys - railway_keys)),
        'only_railway': sorted(list(railway_keys - local_keys)),
        'both': sorted(list(local_keys & railway_keys)),
        'missing_in_railway': sorted(list(local_keys - railway_keys))
    }

def generate_railway_commands(missing_vars: List[str], local_vars: Dict[str, str]) -> str:
    """Generate Railway CLI commands to set missing variables"""
    commands = []
    commands.append("# Railway CLI commands to set missing variables:")
    commands.append("")

    for var in missing_vars:
        value = local_vars.get(var, '')
        if value:
            # Mask sensitive values
            if any(sensitive in var.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                commands.append(f"railway variables set {var}=\"***\"  # Set actual value in dashboard")
            else:
                commands.append(f"railway variables set {var}=\"{value}\"")

    return '\n'.join(commands)

def main():
    """Main function"""
    print("🚂 Railway Environment Variables Checker")
    print("=" * 50)

    # Check Railway CLI
    if not check_railway_cli():
        return

    # Load local environment files
    env_files = ['.env', '.env.railway', '.env.production']
    local_vars = {}

    print("\n📁 Loading local environment files...")
    for env_file in env_files:
        if Path(env_file).exists():
            vars_in_file = load_env_file(env_file)
            local_vars.update(vars_in_file)
            print(f"✅ Loaded {len(vars_in_file)} variables from {env_file}")
        else:
            print(f"⚠️  {env_file} not found")

    if not local_vars:
        print("❌ No local environment variables found")
        return

    print(f"\n📊 Total local variables: {len(local_vars)}")

    # Get Railway variables
    railway_vars = get_railway_variables()

    if not railway_vars:
        print("❌ Could not retrieve Railway variables")
        print("Make sure you're in the correct Railway project:")
        print("  railway link")
        return

    print(f"📊 Railway variables: {len(railway_vars)}")

    # Compare variables
    comparison = compare_variables(local_vars, railway_vars)

    print("\n📈 Comparison Results:")
    print(f"✅ Variables in both: {len(comparison['both'])}")
    print(f"📍 Only in local: {len(comparison['only_local'])}")
    print(f"🚂 Only in Railway: {len(comparison['only_railway'])}")
    print(f"❌ Missing in Railway: {len(comparison['missing_in_railway'])}")

    # Show details
    if comparison['missing_in_railway']:
        print("\n❌ Variables MISSING in Railway (need to be added):")
        for var in comparison['missing_in_railway'][:20]:  # Show first 20
            value = local_vars.get(var, '')
            if any(sensitive in var.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                print(f"   🔐 {var} = ***")
            else:
                print(f"   📝 {var} = {value}")

        if len(comparison['missing_in_railway']) > 20:
            print(f"   ... and {len(comparison['missing_in_railway']) - 20} more")

        # Generate commands
        print("\n🔧 Commands to add missing variables:")
        commands = generate_railway_commands(comparison['missing_in_railway'], local_vars)
        print(commands)

    if comparison['only_railway']:
        print("\n🚂 Variables ONLY in Railway (not in local files):")
        for var in comparison['only_railway'][:10]:  # Show first 10
            print(f"   🚂 {var}")
        if len(comparison['only_railway']) > 10:
            print(f"   ... and {len(comparison['only_railway']) - 10} more")

    # Summary
    print("\n" + "=" * 50)
    if comparison['missing_in_railway']:
        print(f"⚠️  ACTION REQUIRED: Add {len(comparison['missing_in_railway'])} missing variables to Railway")
        print("💡 Tip: Use Railway dashboard for sensitive values (passwords, API keys)")
    else:
        print("✅ All local variables are set in Railway!")

if __name__ == "__main__":
    main()
