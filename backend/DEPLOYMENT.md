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

# External APIs (Configure as needed)
KEEPA_API_KEY=your_production_keepa_key
OPENAI_API_KEY=your_production_openai_key

# Security
SECRET_KEY=production_secret_key

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn
```

### **Render Service Configuration**
```yaml
# Render Service Settings
name: arbitragevault-backend-v2
type: web_service
runtime: python
build_command: "cd backend && uv sync --no-dev --frozen"
start_command: "cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT"
branch: main
auto_deploy: true
region: oregon
plan: starter
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

### **Manual Deployment (If Needed)**
```bash
# Via MCP Render Tools
# update_web_service(serviceId="srv-d3c9sbt6ubrc73ejrusg")

# Or via Render Dashboard
# https://dashboard.render.com/web/srv-d3c9sbt6ubrc73ejrusg
```

### **Deployment Monitoring**
```bash
# Check deployment status
curl "https://arbitragevault-backend-v2.onrender.com/health"

# Monitor deployment logs via MCP
# list_logs(resource=["srv-d3c9sbt6ubrc73ejrusg"])

# Verify specific endpoint
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/batches" | jq
```

---

## 🗄️ **Database Management**

### **Production Database Operations**

#### **Schema Migrations**
```python
# Using MCP Neon Tools
from mcp_neon import prepare_database_migration, complete_database_migration

# 1. Prepare migration in temporary branch
migration = prepare_database_migration(
    params={
        "projectId": "wild-poetry-07211341",
        "migrationSql": "ALTER TABLE batches ADD COLUMN new_field VARCHAR(255);"
    }
)

# 2. Test in temporary branch
run_sql(
    params={
        "projectId": "wild-poetry-07211341",
        "branchId": migration.temporary_branch_id,
        "sql": "SELECT * FROM batches LIMIT 1;"
    }
)

# 3. Apply to production after validation
complete_database_migration(
    params={"migrationId": migration.migration_id}
)
```

#### **Performance Monitoring**
```python
# Monitor slow queries
slow_queries = list_slow_queries(
    params={
        "projectId": "wild-poetry-07211341",
        "limit": 10,
        "minExecutionTime": 1000  # >1 second
    }
)

# Database metrics
metrics = get_metrics(
    resourceId="wild-poetry-07211341",
    metricTypes=["cpu_usage", "memory_usage", "active_connections"]
)
```

### **Backup & Recovery**
- **Automatic Backups**: Neon provides continuous backup
- **Point-in-time Recovery**: Available for last 30 days
- **Branch Creation**: Create development branches for testing
- **Rollback Capability**: Via MCP tools or Neon dashboard

---

## 🔍 **Monitoring & Debugging**

### **Application Monitoring**

#### **Health Checks**
```bash
# Basic health
curl "https://arbitragevault-backend-v2.onrender.com/health"

# Database connectivity (via application)
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/batches?page=1&per_page=1"
```

#### **Performance Monitoring**
```python
# Service metrics via MCP Render
service_metrics = get_metrics(
    resourceId="srv-d3c9sbt6ubrc73ejrusg",
    metricTypes=["cpu_usage", "memory_usage", "http_request_count", "http_latency"]
)

# Application logs
logs = list_logs(
    resource=["srv-d3c9sbt6ubrc73ejrusg"],
    startTime="2025-09-29T00:00:00Z",
    level=["error", "warning"]
)
```

### **Troubleshooting Common Issues**

#### **Database Connection Issues**
```bash
# Check connection string format
echo $DATABASE_URL | grep -E "postgresql://.*@.*\.neon\.tech/.*\?sslmode=require"

# Test database connectivity
python -c "
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect('$DATABASE_URL')
    result = await conn.fetchval('SELECT 1')
    await conn.close()
    print('✅ Database connection OK' if result == 1 else '❌ Connection failed')

asyncio.run(test_db())
"
```

#### **API Validation Errors**
```python
# Validate Pydantic schema alignment
from app.models.batch import Batch
from app.schemas.batch import BatchResponse

# Test model validation
batch_instance = Batch(...)  # From database
response = BatchResponse.model_validate(batch_instance)
# Should not raise validation errors
```

---

## 🔧 **Environment Management**

### **Environment Variables Update**
```python
# Via MCP Render Tools
update_environment_variables(
    serviceId="srv-d3c9sbt6ubrc73ejrusg",
    envVars=[
        {"key": "DATABASE_URL", "value": "postgresql://..."},
        {"key": "LOG_LEVEL", "value": "INFO"},
        {"key": "KEEPA_API_KEY", "value": "your_key"}
    ]
)
```

### **Configuration Validation**
```bash
# Verify environment variables are loaded correctly
curl "https://arbitragevault-backend-v2.onrender.com/health"

# Check specific configuration
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'Environment: {settings.environment}')
print(f'Database configured: {bool(settings.database_url)}')
"
```

---

## 🚨 **Emergency Procedures**

### **Rollback Process**
1. **Identify Last Good Deployment**
   - Check deployment history via Render dashboard
   - Identify commit SHA of stable version

2. **Emergency Rollback**
   ```bash
   # Revert to last stable commit
   git revert HEAD --no-edit
   git push origin main
   
   # Or rollback to specific commit
   git reset --hard <stable_commit_sha>
   git push origin main --force-with-lease
   ```

3. **Database Rollback** (if needed)
   ```python
   # Using MCP Neon tools
   # Create new branch from stable point
   # Restore database to known good state
   ```

### **Incident Response**
1. **Check Service Status**
   ```bash
   curl "https://arbitragevault-backend-v2.onrender.com/health"
   ```

2. **Review Recent Logs**
   ```python
   # Via MCP Render tools
   recent_logs = list_logs(
       resource=["srv-d3c9sbt6ubrc73ejrusg"],
       startTime="last_hour",
       level=["error"]
   )
   ```

3. **Database Health Check**
   ```python
   # Via MCP Neon tools
   metrics = get_metrics(
       resourceId="wild-poetry-07211341",
       metricTypes=["active_connections", "cpu_usage"]
   )
   ```

---

## 📞 **Support Contacts**

### **Service Providers**
- **Render Support**: For backend service issues
- **Neon Support**: For database-related issues
- **GitHub**: For repository and deployment pipeline issues

### **Monitoring Dashboards**
- **Render Dashboard**: https://dashboard.render.com/web/srv-d3c9sbt6ubrc73ejrusg
- **Neon Console**: https://console.neon.tech/app/projects/wild-poetry-07211341

---

*This deployment guide provides comprehensive information for managing the ArbitrageVault backend in production. Follow these procedures for reliable operation and efficient troubleshooting.*