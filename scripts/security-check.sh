#!/bin/bash

# Security check script for local development
# Run this before committing to catch potential credential exposure

echo "🔍 Running security checks..."

# Check for common credential patterns
echo "Checking for credential patterns..."
PATTERNS=(
    "password.*=.*['\"][^'\"]{8,}['\"]"
    "secret.*=.*['\"][^'\"]{16,}['\"]"
    "key.*=.*['\"][^'\"]{16,}['\"]"
    "token.*=.*['\"][^'\"]{16,}['\"]"
    "postgresql://.*:.*@"
    "supabase\.com"
    "aws_access_key_id"
    "AKIA[0-9A-Z]{16}"
)

FOUND=false
for pattern in "${PATTERNS[@]}"; do
    if grep -r -E "$pattern" . --exclude-dir=.git --exclude-dir=node_modules --exclude="*.log" --exclude="security-check.sh"; then
        echo "❌ Found potential credential: $pattern"
        FOUND=true
    fi
done

# Check for large files that might contain data dumps
echo "Checking for large files..."
find . -type f -size +10M -not -path "./.git/*" -not -path "./node_modules/*" | while read file; do
    echo "⚠️  Large file detected: $file"
done

# Check .env files for real values
echo "Checking .env files..."
if [ -f ".env" ]; then
    if grep -E "(password|secret|key).*=.*[^_example]" .env; then
        echo "⚠️  .env file contains real values - ensure it's not committed"
    fi
fi

if [ "$FOUND" = true ]; then
    echo "🚨 Security issues found! Please review before committing."
    exit 1
else
    echo "✅ No security issues detected."
    exit 0
fi