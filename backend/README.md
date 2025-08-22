# ArbitrageVault FastAPI Backend - Quick Start

Production-ready FastAPI backend for ArbitrageVault BookFinder with complete Keepa API integration.

## 🚀 **Quick Start (v1.4.1-stable)**

### **1. Environment Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Keepa API key and database URL
```

### **2. Start Development Server**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **3. Test Endpoints**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/
- **Test Analysis**: 
  ```bash
  curl -X POST "http://localhost:8000/api/v1/keepa/analyze" \
    -H "Content-Type: application/json" \
    -d '{"asin": "B08N5WRWNW"}'
  ```

## 📊 **Available Endpoints (v1.4.1-stable)**

### **Keepa Integration - Production Ready**
- ✅ `POST /api/v1/keepa/analyze` - Single product analysis
- ✅ `POST /api/v1/keepa/batch-analyze` - Batch processing  
- ✅ `GET /api/v1/keepa/search` - Product search with analysis
- ✅ `GET /api/v1/keepa/product/{asin}` - Product details
- ✅ `GET /api/v1/keepa/history/{asin}` - Historical data
- ✅ `GET /api/v1/keepa/debug-analyze/{asin}` - Debug endpoint

### **Repository Layer**
- ✅ `GET/POST /api/v1/analyses` - Analysis CRUD operations
- ✅ `GET /api/v1/batches` - Batch management
- ✅ `GET /api/v1/health/` - System health checks

## 🔧 **Configuration**

### **Required Environment Variables**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/arbitragevault

# Keepa API (Required)
KEEPA_API_KEY=your_keepa_api_key_here

# Application
SECRET_KEY=your_jwt_secret_key
DEBUG=false
ENVIRONMENT=production
```

### **Optional Variables**
```env
# Business Logic Thresholds
DEFAULT_ROI_THRESHOLD=20.0
DEFAULT_VELOCITY_THRESHOLD=50.0
DEFAULT_PROFIT_THRESHOLD=10.0

# Performance
KEEPA_REQUEST_TIMEOUT=30
BATCH_SIZE_LIMIT=100
```

## 🏗️ **Architecture (Current State)**

```
backend/app/
├── main.py                      # ✅ FastAPI entry point
├── api/
│   ├── keepa_integration.py     # ✅ Keepa API client (functional)
│   ├── openai_service.py        # 🚧 AI insights (planned)
│   └── google_sheets.py         # 🚧 Export (planned)
├── core/
│   ├── calculations.py          # ✅ Business logic algorithms
│   ├── database.py              # ✅ Database configuration
│   └── middleware.py            # ✅ Error handling
├── routers/
│   ├── keepa.py                 # ✅ Keepa endpoints
│   ├── analyses.py              # ✅ Analysis operations
│   └── health.py                # ✅ Health checks
├── models/                      # ✅ SQLAlchemy models
├── repositories/                # ✅ Data access layer
└── config/                      # ✅ Settings management
```

## 🧪 **Testing & Validation**

```bash
# Run all tests
pytest tests/ -v

# Test Keepa integration
pytest tests/test_keepa_integration.py -v

# Test with real API
python -c "
from app.api.keepa_integration import KeepAPIIntegration
result = KeepAPIIntegration().get_product('B08N5WRWNW')
print('✅ Keepa API Working' if result else '❌ Check API Key')
"
```

## ⚠️ **Known Issues (v1.4.1)**

- **Minor**: Debug endpoint vs main endpoints price alignment
- **Impact**: Non-blocking, all endpoints functional
- **Workaround**: Use debug endpoint for detailed analysis
- **Status**: Resolution tracked for v1.4.2

## 📈 **Business Logic Features**

### **Strategic Analysis**
- **Profit Hunter**: Maximum ROI identification
- **Velocity**: Fast rotation analysis  
- **Risk Assessment**: Price volatility and market analysis
- **Confidence Scoring**: Data quality and reliability metrics

### **Real-Time Data**
- Current Amazon marketplace prices via Keepa
- BSR history and velocity calculations
- Competition analysis and market sizing
- ROI calculations with Amazon fees

## 🎯 **Production Status**

**v1.4.1-stable** is production-ready with:
- ✅ **5/5 Keepa endpoints functional**
- ✅ **Error handling and resilience**  
- ✅ **Business logic calculations stable**
- ✅ **Real marketplace data analysis**
- ✅ **Comprehensive logging and debugging**

## 📋 **Next Steps**

- **v1.4.2**: Price alignment resolution
- **v1.5.0**: Frontend React integration  
- **v1.6.0**: OpenAI and Google Sheets APIs
- **v1.7.0**: Production security and monitoring

---

**For complete documentation**: See `README_FASTAPI.md`  
**Status**: ✅ Production Ready - Real arbitrage analysis operational  
**Last Updated**: January 17, 2025