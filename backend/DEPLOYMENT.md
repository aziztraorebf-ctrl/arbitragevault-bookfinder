# ArbitrageVault Backend - Deployment Guide

## 🚀 **Production Deployment Information**

### **Current Production Environment**

#### **Backend Service**
- **Platform**: Render Web Service
- **Service ID**: `srv-d3c9sbt6ubrc73ejrusg`
- **URL**: https://arbitragevault-backend-v2.onrender.com
- **Region**: Oregon (us-west)
- **Plan**: Starter (suitable for current usage)
- **Auto-Deploy**: ✅ Enabled on `main` branch

#### **Database**
- **Platform**: Neon PostgreSQL
- **Project ID**: `wild-poetry-07211341`
- **Branch**: `production` (br-billowing-art-adbbfufp)
- **Region**: US East (us-east-1)
- **Connection Pool**: 300-500 concurrent connections
- **SSL**: Required (`sslmode=require`)

---

## 🔧 **Environment Configuration**

### **Production Environment Variables**
```env
# Database Connection (Neon PostgreSQL)
DATABASE_URL=postgresql://neondb_owner:***@ep-damp-thunder-ado6n9o2-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=["*"]

# Firebase Authentication (Required)
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY=your_firebase_private_key
FIREBASE_CLIENT_EMAIL=your_firebase_client_email

# External APIs (Configure as needed)
KEEPA_API_KEY=your_production_keepa_key
OPENAI_API_KEY=your_production_openai_key

# Security
SECRET_KEY=production_secret_key

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn
```

---

## 📦 **Deployment Process**

### **Automatic Deployment**
```bash
# Deploy via Git Push
git add .
git commit -m "feat: your feature description

Generated with [Memex](https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>"
git push origin main

# Render automatically:
# 1. Detects git push to main branch
# 2. Triggers new deployment
# 3. Runs build_command
# 4. Starts service with start_command  
# 5. Performs health check
# 6. Routes traffic to new deployment
```

### **Deployment Monitoring**
```bash
# Check deployment status
curl "https://arbitragevault-backend-v2.onrender.com/health"

# Verify specific endpoint
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/batches" | jq
```

---

## 🗄️ **Database Management**

### **Production Database Operations**

#### **Schema Migrations**
```python
# Using MCP Neon Tools
# 1. Prepare migration in temporary branch
# 2. Test in temporary branch
# 3. Apply to production after validation
```

#### **Performance Monitoring**
```python
# Monitor slow queries and database metrics
# Use MCP Neon tools for real-time monitoring
```

---

## 🚨 **Emergency Procedures**

### **Rollback Process**
1. **Identify Last Good Deployment**
2. **Emergency Rollback**
   ```bash
   git revert HEAD --no-edit
   git push origin main
   ```

### **Incident Response**
1. **Check Service Status**: `curl /health`
2. **Review Recent Logs**: Via MCP Render tools
3. **Database Health Check**: Via MCP Neon tools

---

*This deployment guide provides comprehensive information for managing the ArbitrageVault backend in production.*
