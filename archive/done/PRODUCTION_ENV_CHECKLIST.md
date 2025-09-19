# =============================================================================
# ENVOYOU PRODUCTION ENVIRONMENT VARIABLES CHECKLIST
# =============================================================================
# Environment Variables needed for Production Deployment
# =============================================================================

## 🚨 PRIORITY 1: CRITICAL (Harus ada sebelum deployment)

### AWS S3 Configuration (SKIP - menggunakan Supabase Storage)
- [x] ~~AWS_ACCESS_KEY_ID="your-aws-access-key-id"~~ (SKIP - using Supabase)
- [x] ~~AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"~~ (SKIP - using Supabase)
- [x] ~~AWS_S3_BUCKET="envoyou-uploads"~~ (SKIP - using envoyou-cdn)

### Supabase Storage (ALREADY ACTIVE ✅)
- [x] SUPABASE_STORAGE_KEY="configured"
- [x] SUPABASE_STORAGE_BUCKET="envoyou-cdn"
- [x] SUPABASE_STORAGE_URL="https://cdn.envoyou.com"

### Backup & Recovery
- [ ] BACKUP_ENCRYPTION_KEY="your-backup-encryption-key"

### Backup & Recovery
- [ ] BACKUP_ENCRYPTION_KEY="your-backup-encryption-key"

## 🚨 PRIORITY 2: HIGH (Important for production features)

### Payment Processing
- [ ] STRIPE_SECRET_KEY="sk_live_your-stripe-secret-key"
- [ ] STRIPE_WEBHOOK_SECRET="whsec_your-webhook-secret"
- [ ] STRIPE_PRICE_ID="price_your-price-id"

### Alternative Payment (PayPal)
- [ ] PAYPAL_CLIENT_ID="your-paypal-client-id"
- [ ] PAYPAL_CLIENT_SECRET="your-paypal-client-secret"

### Analytics & Tracking
- [ ] HOTJAR_ID="your-hotjar-id"
- [ ] MIXPANEL_TOKEN="your-mixpanel-token"

## 🚨 PRIORITY 3: MEDIUM (For monitoring & alerts)

### Alert Webhooks
- [ ] SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
- [ ] DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"

### Customer Support
- [ ] INTERCOM_APP_ID="your-intercom-app-id"
- [ ] ZENDESK_SUBDOMAIN="envoyou"
- [ ] FRESHWORKS_WIDGET_ID="your-freshworks-widget-id"

## ✅ PRIORITY 4: OPTIONAL (For advanced features)

### Social Authentication (sudah ada Google & GitHub)
- [ ] FACEBOOK_CLIENT_ID="your-facebook-client-id"
- [ ] FACEBOOK_CLIENT_SECRET="your-facebook-client-secret"

### Advanced Analytics
- [ ] GOOGLE_ANALYTICS_ID="G-HJPHVX4X02" (sudah ada)
- [ ] SEGMENT_WRITE_KEY="your-segment-write-key"

### Performance Monitoring
- [ ] DATADOG_API_KEY="your-datadog-api-key"
- [ ] NEW_RELIC_LICENSE_KEY="your-new-relic-license-key"

## 📋 ALREADY AVAILABLE (No changes needed)

### Infrastructure (sudah configured)
- [x] DATABASE_URL (Supabase)
- [x] REDIS_URL (Upstash)
- [x] SENTRY_DSN (Error tracking)
- [x] MAILGUN_API_KEY (Email service)
- [x] SUPABASE_STORAGE_KEY (File storage - envoyou-cdn)
- [x] SUPABASE_STORAGE_URL (CDN - https://cdn.envoyou.com)

### Domain Configuration (sudah configured)
- [x] ALLOWED_ORIGINS
- [x] CORS_ALLOWED_ORIGINS
- [x] COOKIE_DOMAIN
- [x] Authentication redirects

### Security (sudah configured)
- [x] JWT_SECRET_KEY
- [x] ENCRYPTION_KEY
- [x] SESSION_SECRET

# =============================================================================
# HOW TO GET ENVIRONMENT VARIABLES
# =============================================================================

## 1. AWS S3 (SKIP - using Supabase Storage)
```
✅ NO LONGER REQUIRED
- Already using Supabase Storage with bucket: envoyou-cdn
- CDN active at: https://cdn.envoyou.com
- Status: Active and working
```

## 1.1. Supabase Storage (ALREADY ACTIVE ✅)
```
✅ ALREADY CONFIGURED
- Bucket: envoyou-cdn
- CDN URL: https://cdn.envoyou.com
- Status: Production ready
```

## 2. Stripe (for payments)
1. Open Stripe Dashboard: https://dashboard.stripe.com/
2. Create product and pricing
3. Generate webhook endpoint
4. Copy secret keys

## 3. PayPal (alternative payment)
1. Open PayPal Developer: https://developer.paypal.com/
2. Create app
3. Get client ID & secret

## 4. Analytics Tools
1. Hotjar: https://www.hotjar.com/
2. Mixpanel: https://mixpanel.com/
3. Segment: https://segment.com/

## 5. Alert Webhooks
1. Slack: https://api.slack.com/apps (create app, add webhook)
2. Discord: Server settings > Integrations > Webhooks

## 6. Customer Support
1. Intercom: https://app.intercom.com/
2. Zendesk: https://envoyou.zendesk.com/
3. Freshworks: https://freshworks.com/

# =============================================================================
# VERIFICATION CHECKLIST
# =============================================================================

## Pre-Deployment Verification
- [ ] Semua PRIORITY 1 variables sudah ada
- [ ] Test AWS S3 connection
- [ ] Test Stripe webhook
- [ ] Test email sending (Mailgun)
- [ ] Test database connection
- [ ] Test Redis connection

## Post-Deployment Testing
- [ ] File upload functionality
- [ ] Payment processing
- [ ] Email notifications
- [ ] Error tracking (Sentry)
- [ ] Analytics tracking
- [ ] Alert webhooks

# =============================================================================
# COST ESTIMATION
# =============================================================================

## Monthly Costs (approximate)
- AWS S3: $0.023/GB storage + $0.09/GB transfer
- Stripe: 2.9% + $0.30 per transaction
- Supabase: $25-99/month (depending on usage)
- Upstash Redis: $10-50/month
- Sentry: $26-299/month
- Mailgun: $15-119/month
- Analytics tools: $0-99/month each

## Free Tiers Available
- Supabase: 500MB database, 50MB file storage
- Upstash: 10,000 requests/day
- Sentry: 5,000 events/month
- Mailgun: 5,000 emails/month

# =============================================================================
# SECURITY NOTES
# =============================================================================

## 🔐 Security Best Practices
1. Never commit secrets to git
2. Use different keys for staging/production
3. Rotate keys regularly (every 90 days)
4. Use principle of least privilege for IAM
5. Enable 2FA for all service accounts
6. Monitor for unusual activity

## 🔄 Key Rotation Schedule
- ~~AWS Keys: Every 90 days~~ (Not using AWS S3)
- JWT Secrets: Every 30 days
- Database passwords: Every 60 days
- API Keys: When compromised
- Supabase Keys: Every 90 days

# =============================================================================
# 📊 UPDATED SUMMARY (AFTER SUPABASE STORAGE)
# =============================================================================

## 🎯 CURRENT STATUS
- **Storage Solution**: ✅ Supabase Storage (envoyou-cdn) - ACTIVE
- **CDN**: ✅ https://cdn.envoyou.com - WORKING
- **AWS S3**: ⏳ Future consideration (when 1000+ users)

## 📋 REMAINING ENVIRONMENT VARIABLES TO ACQUIRE
**Total: ~15-20 items** (Reduced from 25-30 due to Supabase Storage)

### Still Needed:
1. Security Keys (JWT, Encryption) - 5 items
2. Stripe Payment - 3 items  
3. Email Service - 2-3 items
4. Analytics Tools - 3-5 items
5. Customer Support - 2-3 items

### Already Available:
- ✅ Database (Supabase)
- ✅ Redis (Upstash)
- ✅ File Storage (Supabase Storage)
- ✅ CDN (cdn.envoyou.com)
- ✅ Error Tracking (Sentry)
- ✅ Email Service (Mailgun)

# =============================================================================
# EMERGENCY CONTACTS
# =============================================================================

## Service Provider Contacts
- AWS Support: aws.amazon.com/support
- Stripe Support: support.stripe.com
- Supabase Support: supabase.com/support
- Railway Support: railway.app/support
- Netlify Support: netlify.com/support

## Emergency Procedures
1. If service down: Check Railway dashboard
2. If payment issues: Check Stripe dashboard
3. If database issues: Check Supabase dashboard
4. If file upload issues: Check Supabase Storage (envoyou-cdn bucket)
5. If domain issues: Check Cloudflare dashboard

# =============================================================================
# END OF CHECKLIST
# =============================================================================
