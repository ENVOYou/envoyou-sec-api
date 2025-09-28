# 🛡️ Security Prevention Guide

## Automated Protection Setup

### ✅ Pre-commit Hook
- **Location**: `.git/hooks/pre-commit`
- **Function**: Scans for credentials before each commit
- **Status**: Active - will block commits with potential credentials

### ✅ Enhanced .gitignore
- **Added**: Comprehensive credential file patterns
- **Protects**: API keys, certificates, database dumps, config files
- **Coverage**: 50+ sensitive file patterns

### ✅ GitHub Actions Security Scan
- **File**: `.github/workflows/security-scan.yml`
- **Tools**: GitGuardian + TruffleHog
- **Triggers**: Push to main/develop, Pull Requests

### ✅ Local Security Check
- **Script**: `scripts/security-check.sh`
- **Usage**: `./scripts/security-check.sh`
- **Function**: Manual security scan before commits

## Daily Security Practices

### 1. Before Every Commit
```bash
# Run security check
./scripts/security-check.sh

# Check what you're committing
git diff --cached

# Commit with verification
git commit -m "your message"
```

### 2. Environment Variables Only
```bash
# ❌ NEVER do this
DATABASE_URL="postgresql://user:password@host:5432/db"

# ✅ Always do this
DATABASE_URL="${DATABASE_URL}"
```

### 3. Use .env.example Templates
```bash
# Create template without real values
cp .env .env.example
# Replace real values with placeholders in .env.example
```

## File Patterns to NEVER Commit

### Credential Files
- `*.pem`, `*.key`, `*.crt` - Certificates
- `*_credentials.txt`, `*_secrets.txt` - Credential files
- `config.json`, `secrets.json` - Config with secrets
- `serviceAccountKey.json` - Cloud credentials

### Database Files
- `*.sql`, `*.dump`, `*.backup` - Database dumps
- `*.db` (except empty templates)

### Environment Files
- `.env` (with real values)
- `.env.production`, `.env.staging`
- `local.env`, `.env.secrets`

## Emergency Response Plan

### If Credentials Are Committed:

1. **Immediate Actions**
   ```bash
   # Remove from current commit
   git reset HEAD~1
   git add .
   git commit -m "Remove credentials"
   ```

2. **Revoke Credentials**
   - Database: Reset password immediately
   - API Keys: Regenerate/revoke in provider dashboard
   - Certificates: Revoke and reissue

3. **Clean Git History** (if needed)
   ```bash
   # Remove from all history (DESTRUCTIVE)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch FILENAME' \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

## Security Tools Integration

### GitGuardian (Recommended)
1. Sign up at [gitguardian.com](https://gitguardian.com)
2. Add `GITGUARDIAN_API_KEY` to GitHub Secrets
3. Automatic scanning on every push

### TruffleHog
- Included in GitHub Actions
- Scans for verified secrets
- Runs on pull requests

## Team Guidelines

### Code Review Checklist
- [ ] No hardcoded credentials
- [ ] Environment variables used properly
- [ ] No sensitive files in commit
- [ ] .env.example updated if needed

### Onboarding New Developers
1. Run `./scripts/security-check.sh` to verify setup
2. Review this guide
3. Test pre-commit hook with dummy credential
4. Ensure they have proper .env setup

## Monitoring & Alerts

### GitHub Repository Settings
- Enable "Push protection for yourself and collaborators"
- Enable "Push protection for yourself"
- Set up branch protection rules

### Regular Audits
- Weekly: Run `./scripts/security-check.sh`
- Monthly: Review .gitignore patterns
- Quarterly: Audit all environment variables

## Quick Reference

### Test Pre-commit Hook
```bash
# Create test file with fake credential
echo 'password="test123456789"' > test_cred.txt
git add test_cred.txt
git commit -m "test" # Should be blocked
rm test_cred.txt
```

### Manual Security Scan
```bash
./scripts/security-check.sh
```

### Check Git History for Secrets
```bash
git log --all -S "password" --source --all
```

---

**Remember**: Security is everyone's responsibility. When in doubt, ask for review!