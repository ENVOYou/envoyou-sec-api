# Production Deployment Guide for Authentication System

This guide covers the production deployment of the comprehensive authentication system with security, monitoring, and backup features.

## 📋 Pre-Deployment Checklist

### 🔒 Security Configuration
- [ ] JWT secrets configured (`JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`)
- [ ] SMTP credentials configured for email service
- [ ] Backup encryption key configured
- [ ] HTTPS/TLS certificates installed
- [ ] Database encryption at rest enabled
- [ ] Security headers configured

### 🏗️ Infrastructure Setup
- [ ] Production database configured (PostgreSQL/MySQL recommended)
- [ ] Redis configured for session storage (optional but recommended)
- [ ] Load balancer configured
- [ ] CDN configured for static assets
- [ ] Monitoring and alerting systems configured

### 📊 Application Configuration
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Database migrations applied
- [ ] Static files configured
- [ ] Email service tested

## 🚀 Deployment Steps

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd project-permit-api

# Create production environment file
cp .env.example .env.production
```

### 2. Configure Environment Variables

Edit `.env.production` with production values:

```bash
# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key
JWT_REFRESH_SECRET_KEY=your-different-refresh-secret-key
BACKUP_ENCRYPTION_KEY=your-backup-encryption-key

# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourdomain.com

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
BACKUP_ENABLED=true

# Security
CORS_ORIGINS=https://yourdomain.com
SECURITY_HEADERS_ENABLED=true
```

### 3. Database Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -c "from app.models import create_tables; create_tables()"

# Validate database connection
python -c "from app.database import get_db; next(get_db())"
```

### 4. Pre-Deployment Validation

```bash
# Run production configuration validation
python production_auth_config.py

# Run deployment validation
python scripts/validate_auth_deployment.py

# Run CI/CD tests
python scripts/ci_cd_auth_tests.py
```

### 5. Application Deployment

#### Using Gunicorn (Recommended)

```bash
# Install production server
pip install gunicorn

# Start application
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

#### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
```

### 6. Reverse Proxy Configuration

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
}
```

### 7. SSL/TLS Configuration

```bash
# Using Let's Encrypt
certbot --nginx -d yourdomain.com

# Or using custom certificates
# Place certificate files in /etc/ssl/certs/
# Place private key in /etc/ssl/private/
```

## 🔧 Post-Deployment Configuration

### 1. Monitoring Setup

```bash
# Start monitoring system
python scripts/monitor_auth_system.py

# Configure log rotation
cat > /etc/logrotate.d/permit-api << EOF
/var/log/permit-api/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    create 644 www-data www-data
    postrotate
        systemctl reload permit-api
    endscript
}
EOF
```

### 2. Backup Configuration

```bash
# Create backup script
cat > /usr/local/bin/auth-backup.sh << 'EOF'
#!/bin/bash
cd /home/husni/project-permit-api
python scripts/backup_auth_data.py backup
EOF

chmod +x /usr/local/bin/auth-backup.sh

# Add to cron for daily backups
echo "0 2 * * * /usr/local/bin/auth-backup.sh" | crontab -
```

### 3. Load Testing

```bash
# Run load tests
python scripts/load_test_auth.py

# Run stress tests
python scripts/stress_test_db.py
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# API Health Check
curl -f https://yourdomain.com/health

# Authentication Health Check
curl -f https://yourdomain.com/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrong"}'
```

### Log Monitoring

```bash
# View application logs
tail -f /var/log/permit-api/auth.log

# Monitor authentication events
grep "authentication" /var/log/permit-api/auth.log

# Monitor security events
grep "security\|attack\|suspicious" /var/log/permit-api/auth.log
```

### Performance Monitoring

```bash
# Monitor system resources
htop

# Monitor database connections
python -c "
import psycopg2
conn = psycopg2.connect('your-connection-string')
cur = conn.cursor()
cur.execute('SELECT count(*) FROM pg_stat_activity;')
print('Active connections:', cur.fetchone()[0])
"
```

## 🚨 Security Considerations

### Network Security
- [ ] Configure firewall rules
- [ ] Enable fail2ban for brute force protection
- [ ] Set up intrusion detection system
- [ ] Configure VPN for administrative access

### Application Security
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Monitor for vulnerabilities
- [ ] Implement rate limiting
- [ ] Use security headers

### Data Protection
- [ ] Encrypt sensitive data at rest
- [ ] Implement data backup encryption
- [ ] Regular backup testing
- [ ] Secure backup storage

## 🔄 Updates & Maintenance

### Rolling Updates
```bash
# Create backup before update
python scripts/backup_auth_data.py backup

# Update application
git pull origin main
pip install -r requirements.txt

# Run migrations
python -c "from app.models import migrate_database; migrate_database()"

# Restart services
sudo systemctl restart permit-api

# Validate deployment
python scripts/validate_auth_deployment.py
```

### Emergency Procedures

#### Service Down
1. Check application logs
2. Verify database connectivity
3. Check system resources
4. Restart services if necessary
5. Contact development team

#### Security Incident
1. Isolate affected systems
2. Preserve logs and evidence
3. Notify security team
4. Apply security patches
5. Update incident response plan

## 📞 Support & Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
python -c "from app.database import test_connection; test_connection()"

# Verify connection string
echo $DATABASE_URL
```

#### Authentication Failures
```bash
# Check JWT configuration
python -c "from app.auth import validate_jwt_config; validate_jwt_config()"

# Test authentication endpoints
python scripts/validate_auth_deployment.py
```

#### Email Delivery Issues
```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('username', 'password')
print('SMTP connection successful')
"
```

### Performance Optimization

#### Database Optimization
```sql
-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```

#### Application Optimization
```python
# Enable connection pooling
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20

# Configure caching
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
```

## 📈 Scaling Considerations

### Horizontal Scaling
- [ ] Load balancer configuration
- [ ] Session storage in Redis
- [ ] Database read replicas
- [ ] CDN for static content

### Vertical Scaling
- [ ] Monitor resource usage
- [ ] Upgrade server specifications
- [ ] Optimize database queries
- [ ] Implement caching layers

## 🔧 Configuration Reference

### Environment Variables
See `production_auth_config.py` for all available configuration options.

### File Permissions
```bash
# Secure configuration files
chmod 600 .env.production
chmod 600 backup-encryption-key

# Secure log files
chmod 644 /var/log/permit-api/*.log
chown www-data:www-data /var/log/permit-api/
```

### Backup Strategy
- Daily full backups
- Weekly offsite backups
- Monthly archive backups
- Test restoration quarterly

---

## ✅ Deployment Validation

After deployment, run these validation checks:

```bash
# Complete validation suite
python scripts/validate_auth_deployment.py
python scripts/ci_cd_auth_tests.py
python scripts/load_test_auth.py

# Check all systems
curl -f https://yourdomain.com/health
```

**Deployment is complete when all validation tests pass and the application is serving requests successfully.**
