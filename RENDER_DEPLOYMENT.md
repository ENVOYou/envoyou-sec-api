# 🚀 Deploy to Render - Quick Start Guide

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Ensure your code is pushed to GitHub
3. **Environment Variables**: Prepare your production secrets

## 🚀 One-Click Deployment

### Step 1: Connect to Render
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select this repository

### Step 2: Configure Service
```yaml
# These settings will be auto-configured from render.yaml
Service Type: Web Service
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python start.py
```

### Step 3: Environment Variables
The following will be automatically configured from `render.yaml`:

#### 🔐 **Security (Auto-Generated)**
- `SECRET_KEY` - Auto-generated secure key
- `JWT_SECRET_KEY` - Auto-generated JWT secret
- `ENCRYPTION_KEY` - Auto-generated encryption key
- `SESSION_SECRET` - Auto-generated session secret
- `MASTER_API_KEY` - Auto-generated master API key

#### 🌐 **API Configuration**
- `CAMPD_API_KEY` - EPA CAMD API key
- `EIA_API_KEY` - EIA API key
- `AIRNOW_API_KEY` - AirNow API key
- `AMDALNET_API_URL` - Amdalnet API URL

#### ⚙️ **Application Settings**
- `PORT` - 10000 (Render default)
- `LOG_LEVEL` - INFO
- `ENVIRONMENT` - production
- `CORS_ORIGINS` - Your frontend domain

### Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait for build and deployment (usually 5-10 minutes)
3. Your API will be available at: `https://your-service-name.onrender.com`

## 🔧 Manual Configuration (Alternative)

If you prefer manual setup:

### Environment Variables to Set:
```bash
# Security
SECRET_KEY=your_generated_secret_key
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
SESSION_SECRET=your_session_secret

# API Keys
CAMPD_API_KEY=nANGR3eBqPq0agXJH3X0LFTk0YxbMICAfc9jOKgT
EIA_API_KEY=P58wd4mdLJ1wmyVz9g15aQryMuS32zlWVtJz4IcO
AIRNOW_API_KEY=72965683-08D9-40D7-9FF9-241726DCEE8E

# Application
PORT=10000
LOG_LEVEL=INFO
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-domain.com
```

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://your-service-name.onrender.com/health
```

### API Test
```bash
# Get demo API key
curl -X POST https://your-service-name.onrender.com/admin/request-demo-key \
  -H "Content-Type: application/json" \
  -d '{"tier": "premium"}'

# Test permits endpoint
curl https://your-service-name.onrender.com/permits
```

## 📊 Render Free Tier Limits

- **512 MB RAM**
- **750 hours/month** (about 31 days)
- **100 GB bandwidth/month**
- **1 GB disk space**
- **Auto-sleep** after 15 minutes of inactivity

## 🔄 Migration Strategy to AWS

### When to Migrate:
- ✅ Traffic exceeds Render limits
- ✅ Need more control over infrastructure
- ✅ Require custom domain SSL
- ✅ Need persistent database
- ✅ Enterprise features needed

### AWS Migration Path:
1. **AWS App Runner** (Recommended for simplicity)
2. **AWS ECS Fargate** (More control)
3. **AWS Lambda + API Gateway** (Serverless)

### Migration Steps:
1. Update `apprunner.yaml` with your configuration
2. Use existing AWS deployment scripts
3. Migrate database if needed
4. Update DNS and frontend configuration

## 🆘 Troubleshooting

### Build Fails
```bash
# Check build logs in Render dashboard
# Common issues:
# - Missing dependencies in requirements.txt
# - Python version mismatch
# - File path issues
```

### Runtime Errors
```bash
# Check application logs in Render dashboard
# Common issues:
# - Missing environment variables
# - Database connection issues
# - File permission issues
```

### Performance Issues
```bash
# Free tier limitations:
# - Cold starts (15-30 seconds)
# - Memory limits (512MB)
# - Auto-sleep after inactivity
```

## 📞 Support

- **Render Docs**: https://docs.render.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Project Issues**: Create GitHub issue

---

🎉 **Happy Deploying! Your API will be live in minutes!**
