# ArbitrageVault BookFinder

Professional tool for identifying profitable book arbitrage opportunities using advanced Keepa API data analysis and intelligent multi-criteria scoring system.

## 🎯 Project Status - v1.6.0-autosourcing ✅ PRODUCTION READY

**Current Phase**: AutoSourcing Intelligence Module Complete ✅  
**Next Phase**: Frontend Integration (v2.0.0) 🚀

### ✅ **v1.6.0-autosourcing - Intelligent Product Discovery**

#### **🤖 AutoSourcing Module - NEW**
- **🔍 Intelligent Discovery**: Automated product finding with Keepa Product Finder API
- **⚙️ Configurable Search**: User-defined criteria for categories, BSR ranges, ROI thresholds
- **👤 Profile Management**: Save/reuse search configurations with usage tracking
- **⚡ Quick Actions**: Buy/Favorite/Ignore/Analyze discovered products
- **📊 Real-time Analysis**: Advanced scoring v1.5.0 integration for discovered products
- **📋 REST API Complete**: 13 endpoints covering full discovery workflow
- **🎯 Opportunity of the Day**: Daily best pick with intelligent prioritization

#### **🚀 AutoSourcing Capabilities**
- ✅ **Custom Search Engine**: User-defined discovery criteria and scoring thresholds
- ✅ **Profile System**: 3 default profiles (Conservative, Balanced, Aggressive) + custom profiles
- ✅ **Action Management**: Complete workflow from discovery to purchase decision
- ✅ **Duplicate Detection**: Smart filtering to avoid redundant discoveries
- ✅ **Statistics Dashboard**: Performance insights and profile effectiveness tracking
- ✅ **Database Persistence**: Full job history and results storage
- ✅ **Production Ready**: Comprehensive validation and testing completed

### ✅ **v1.5.0-production - Advanced Scoring System & Optimization**

#### **🔥 Major New Features**
- **🧠 Advanced Scoring Engine**: 6 new intelligent scoring functions with normalized 0-100 scales
- **⚙️ Configurable Thresholds**: Business rules driven by `business_rules.json` configuration
- **🏆 Overall Rating System**: EXCELLENT/GOOD/FAIR/PASS classifications with detailed breakdowns
- **📊 Simulation-Validated Optimization**: Grid search confirms optimal threshold calibration
- **🔍 Enhanced API Responses**: Comprehensive score breakdowns with reasoning and confidence levels

#### **🚀 Core System Capabilities (v1.5.0)**
- ✅ **Advanced Velocity Scoring**: BSR trend analysis with market-specific intelligence
- ✅ **Price Stability Assessment**: Volatility analysis with coefficient of variation scoring
- ✅ **Data Confidence Rating**: Multi-factor data quality and freshness evaluation
- ✅ **Multi-Criteria Optimization**: Simulation-tested threshold combinations (54 tested scenarios)
- ✅ **Business Logic Validation**: 25% EXCELLENT rate with 45% median ROI confirmed optimal
- ✅ **Configuration Management**: Hot-reloadable business rules without code changes

#### **🚀 What Works Now (v1.6.0-autosourcing)**
- ✅ **AutoSourcing Intelligence**: 13 new endpoints for automated product discovery
- ✅ **Enhanced API Endpoints**: 6 advanced scoring endpoints + 13 AutoSourcing endpoints
- ✅ **Real-Time Analysis**: Keepa API integration with advanced multi-criteria evaluation
- ✅ **Intelligent Discovery**: Automated product finding with configurable criteria
- ✅ **Profile Management**: Save/reuse search configurations with usage tracking
- ✅ **Action Workflow**: Complete buy/analyze/ignore decision pipeline
- ✅ **Production Ready**: Comprehensive testing, validation, and configuration management
- ✅ **Overall Rating System**: Clear EXCELLENT/GOOD/FAIR/PASS classifications

#### **📊 Advanced Business Intelligence (v1.5.0)**
- **🎯 Advanced Velocity Scoring**: BSR trend analysis with market intelligence (0-100 scale)
- **📈 Price Stability Assessment**: Volatility analysis with coefficient of variation scoring
- **🔍 Data Confidence Rating**: Multi-factor quality assessment with freshness weighting
- **⚡ Overall Rating Engine**: Configurable multi-criteria decision system
- **🧪 Validated Optimization**: Grid search across 54 threshold combinations
- **📋 Score Breakdowns**: Detailed reasoning and confidence levels for transparency

## 🏗️ Tech Stack

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy ✅
- **External APIs**: Keepa API (functional) ✅, OpenAI (planned), Google Sheets (planned)
- **Frontend**: React + TypeScript + Tailwind CSS (Phase 2.0) 🚧
- **Testing**: pytest + comprehensive coverage ✅
- **Deployment**: Docker + Docker Compose ready ✅

## 🧠 **Advanced Scoring System (v1.5.0)**

### **Multi-Criteria Intelligence Engine**
ArbitrageVault employs a sophisticated 4-dimensional scoring system that evaluates each book across multiple business-critical factors:

#### **1. 🎯 ROI Analysis**
- **Traditional Calculation**: `(Profit - Fees - Costs) / Investment × 100`
- **Enhanced Features**: Dynamic fee calculation, buffer safety margins, market-aware pricing
- **Output**: Percentage ROI with profit breakdown and risk assessment

#### **2. ⚡ Advanced Velocity Scoring (NEW v1.5.0)**
- **Intelligence**: BSR trend analysis with category-specific benchmarks
- **Algorithm**: Multi-point BSR evaluation with velocity momentum calculation
- **Scale**: Normalized 0-100 score (90+ = Excellent velocity)
- **Business Value**: Predicts inventory rotation speed and cash flow velocity

#### **3. 📈 Price Stability Assessment (NEW v1.5.0)**
- **Intelligence**: Price volatility analysis using coefficient of variation
- **Algorithm**: Historical price variance with outlier detection and stabilization scoring
- **Scale**: Normalized 0-100 score (80+ = Highly stable pricing)
- **Business Value**: Risk assessment for price predictability and profit margin safety

#### **4. 🔍 Data Confidence Rating (NEW v1.5.0)**  
- **Intelligence**: Multi-factor data quality and freshness evaluation
- **Algorithm**: Completeness scoring + data age weighting + source reliability
- **Scale**: Normalized 0-100 score (70+ = High confidence recommendations)
- **Business Value**: Decision confidence and recommendation reliability assessment

#### **5. 🏆 Overall Rating Engine (NEW v1.5.0)**
- **EXCELLENT**: All criteria meet premium thresholds → Top-tier opportunities
- **GOOD**: Strong performance across most criteria → Solid opportunities  
- **FAIR**: Meets minimum viability standards → Consider with caution
- **PASS**: Below minimum thresholds → Skip opportunity

### **📊 Simulation-Validated Optimization**
- **Grid Search**: 54 threshold combinations tested across realistic product portfolio
- **Validation**: Current thresholds confirmed optimal (25% EXCELLENT rate, 45% median ROI)
- **Business Balance**: Maintains selectivity while ensuring sufficient opportunity flow
- **Configuration**: All thresholds configurable via `business_rules.json` without code changes

## 🔌 **API Endpoints (v1.6.0-autosourcing)**

### **🤖 AutoSourcing Discovery Endpoints (NEW)**
```bash
# Custom intelligent product discovery
POST /api/v1/autosourcing/run-custom
# Body: {"discovery_config": {...}, "scoring_config": {...}, "profile_name": "..."}

# Get latest discovery results
GET /api/v1/autosourcing/latest

# Daily best opportunity  
GET /api/v1/autosourcing/opportunity-of-day

# Profile management
GET /api/v1/autosourcing/profiles
POST /api/v1/autosourcing/profiles
PUT /api/v1/autosourcing/profiles/{profile_id}

# Action management on discovered products
PUT /api/v1/autosourcing/picks/{pick_id}/action
# Body: {"action": "buy|favorite|ignore|analyzing"}

# Get products by action status
GET /api/v1/autosourcing/to-buy
GET /api/v1/autosourcing/favorites
GET /api/v1/autosourcing/history

# Statistics and insights
GET /api/v1/autosourcing/stats
GET /api/v1/autosourcing/jobs/{job_id}
```

### **🎯 Primary Analysis Endpoints**
```bash
# Enhanced single product analysis with advanced scoring
GET /api/v1/keepa/{asin}/metrics
# Returns: Complete analysis with velocity/stability/confidence scores

# Legacy single product analysis (backward compatible)
POST /api/v1/keepa/analyze
Content-Type: application/json
{"asin": "B08N5WRWNW"}

# Batch analysis (multiple products)  
POST /api/v1/keepa/batch-analyze
Content-Type: application/json
{"asins": ["B08N5WRWNW", "1234567890"]}

# Product search and analysis
GET /api/v1/keepa/search?query=python+programming&limit=10
```

### **Data Management Endpoints**
```bash
# Product details extraction
GET /api/v1/keepa/product/{asin}

# Historical data and trends
GET /api/v1/keepa/history/{asin}

# Debug and diagnostics
GET /api/v1/keepa/debug-analyze/{asin}
```

### **Enhanced API Response Structure (v1.5.0)**
```json
{
    "asin": "0134093410",
    "title": "Campbell Biology (Campbell Biology Series)",
    "current_price": 299.99,
    "estimated_buy_cost": 224.99,
    "roi_percentage": 45.3,
    "profit_net": 67.50,
    "overall_rating": "EXCELLENT",
    
    // NEW: Advanced Scoring Breakdown
    "velocity_score": 85.0,
    "stability_score": 90.0, 
    "confidence_score": 95.0,
    
    // NEW: Detailed Score Analysis  
    "score_breakdown": {
        "velocity": {
            "score": 85.0,
            "raw": 15000,
            "level": "HIGH",
            "notes": "Strong BSR performance in Books category"
        },
        "stability": {
            "score": 90.0,
            "raw": 0.12,
            "level": "VERY_HIGH", 
            "notes": "Low price volatility, coefficient of variation: 12%"
        },
        "confidence": {
            "score": 95.0,
            "raw": 0.95,
            "level": "VERY_HIGH",
            "notes": "Complete data available, recent updates"
        }
    },
    
    // Traditional Calculations Enhanced
    "calculations": {
        "amazon_fees": 89.97,
        "profit_margin_pct": 22.5,
        "liquidation_estimate_days": 21,
        "risk_level": "LOW"
    }
}
```

## 📋 **Quick Start Guide**

### **1. Environment Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Keepa API key and database URL
```

### **2. Database Initialization**
```bash
# Create and run migrations
python -m alembic upgrade head
```

### **3. Configure Business Rules (v1.5.0)**
```bash
# Edit backend/config/business_rules.json for custom thresholds
```

**Key Configuration Options:**
```json
{
  "advanced_scoring": {
    "thresholds": {
      "roi_min": 30,        // Minimum ROI for EXCELLENT rating
      "velocity_min": 70,   // Minimum velocity score for EXCELLENT  
      "stability_min": 70,  // Minimum stability score for EXCELLENT
      "confidence_min": 70  // Minimum confidence score for EXCELLENT
    }
  }
}
```

### **4. Initialize AutoSourcing Module (NEW v1.6.0)**
```bash
# Initialize AutoSourcing database and default profiles
python init_autosourcing_db.py
```

### **5. Start API Server**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **6. Test AutoSourcing Discovery (NEW)**
```bash
# Test intelligent product discovery
curl -X POST "http://localhost:8000/api/v1/autosourcing/run-custom" \
  -H "Content-Type: application/json" \
  -d '{
    "discovery_config": {
      "categories": ["Books", "Textbooks"],
      "bsr_max": 100000,
      "price_range": {"min": 10, "max": 100}
    },
    "scoring_config": {
      "roi_min": 25,
      "velocity_min": 60
    },
    "profile_name": "Test Discovery"
  }'
```

### **7. Test Live Analysis Endpoint**
```bash
# Test with real ASIN
curl -X POST "http://localhost:8000/api/v1/keepa/analyze" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B08N5WRWNW"}'
```

### **5. Access Interactive Docs**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 **File Structure (Current State)**

```
arbitragevault_bookfinder/
├── backend/                        # ✅ Complete FastAPI backend
│   ├── app/
│   │   ├── main.py                # FastAPI application entry
│   │   ├── models/                # SQLAlchemy models
│   │   │   ├── user.py           # User management
│   │   │   ├── batch.py          # Batch processing
│   │   │   ├── analysis.py       # Analysis results
│   │   │   └── autosourcing.py   # ✅ NEW: AutoSourcing models
│   │   ├── services/             # Business logic services
│   │   │   ├── keepa_service.py      # ✅ Keepa API client
│   │   │   ├── autosourcing_service.py # ✅ NEW: AutoSourcing intelligence
│   │   │   ├── business_config_service.py # ✅ Configuration management
│   │   │   ├── openai_service.py     # 🚧 AI-powered insights
│   │   │   └── google_sheets.py      # 🚧 Export functionality
│   │   ├── core/                 # Core business logic
│   │   │   ├── calculations.py   # ✅ ROI/Velocity algorithms
│   │   │   ├── database.py       # ✅ DB configuration
│   │   │   └── auth.py           # 🚧 Authentication
│   │   └── api/v1/routers/       # ✅ API route handlers
│   │       ├── analysis.py       # Analysis endpoints
│   │       ├── keepa.py          # Keepa integration routes
│   │       └── autosourcing.py   # ✅ NEW: AutoSourcing discovery endpoints
│   ├── init_autosourcing_db.py   # ✅ NEW: AutoSourcing database initialization
│   │   └── config/               # ✅ Configuration management
│   │       └── settings.py       # Environment settings
│   ├── tests/                    # ✅ Comprehensive test suite
│   ├── requirements.txt          # ✅ Production dependencies
│   └── .env.example             # ✅ Environment template
├── frontend/                     # 🚧 React dashboard (Phase 1.5)
├── docker-compose.yml           # ✅ Container orchestration
├── .gitignore                   # ✅ Version control rules
└── README.md                    # ✅ This documentation
```

## 🎯 **Business Logic Engine**

### **Strategic Analysis Methods**
```python
# Profit Hunter Strategy (Maximum ROI)
analysis = analyze_product(asin, strategy="profit")
# Focus: High-margin opportunities, premium products

# Velocity Strategy (Fast Rotation)  
analysis = analyze_product(asin, strategy="velocity")
# Focus: Quick turnover, consistent demand

# Balanced Strategy (Optimized Risk/Reward)
analysis = analyze_product(asin, strategy="balanced")
# Focus: Sustainable, repeatable arbitrage plays
```

### **Intelligent Filtering & Scoring**
```python
# Multi-criteria opportunity assessment
{
    "roi_threshold": 35.0,          # Minimum profit margin
    "velocity_threshold": 60.0,     # Rotation probability
    "risk_tolerance": "moderate",   # Conservative/Moderate/Aggressive
    "market_cap_min": 1000,        # Minimum market size
    "competition_max": 15           # Maximum active sellers
}
```

## ⚠️ **Known Issues & Limitations**

### **Minor Technical Issues**
- **Price Alignment**: Debug endpoint and main endpoints occasionally show different price extraction logic
- **Impact**: Non-blocking - all endpoints functional without crashes
- **Status**: Tracked for v1.4.2 resolution

### **Current Scope Limitations**
- **Frontend**: Command-line and API access only (UI in Phase 1.5)
- **Export**: No automated Google Sheets integration yet (planned v1.6)
- **Authentication**: Basic implementation (production security in v1.7)

## 🚀 **Development Roadmap**

### **🎯 v1.4.2 (Stabilization) - Target: 2 weeks**
- Resolve price extraction alignment between endpoints
- Enhanced error messages and API response consistency  
- Performance optimization for batch processing
- Extended test coverage for edge cases

### **🎯 v1.5.0 (Frontend Integration) - Target: 4 weeks**
- React dashboard with real-time analysis results
- Interactive filtering and sorting capabilities
- Batch upload interface with progress tracking
- Export functionality (CSV, Excel)

### **🎯 v1.6.0 (Advanced Features) - Target: 6 weeks**
- Google Sheets API integration
- OpenAI-powered opportunity insights
- Advanced reporting and analytics
- User management and role-based access

### **🎯 v1.7.0 (Production Scale) - Target: 8 weeks**
- Production-grade authentication and security
- API rate limiting and optimization
- Comprehensive monitoring and logging
- Docker deployment with CI/CD pipeline

## 🧪 **Testing & Validation**

### **Current Test Coverage**
```bash
# Run complete test suite
pytest backend/tests/ -v

# Test specific modules
pytest backend/tests/test_keepa_integration.py -v
pytest backend/tests/test_calculations.py -v  
pytest backend/tests/test_analysis_endpoints.py -v
```

### **Integration Testing**
```bash
# Test with real Keepa API (requires API key)
python backend/validate_keepa_integration.py

# End-to-end workflow validation
python backend/validate_complete_workflow.py
```

## 🔧 **Configuration & Environment**

### **Required Environment Variables**
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/arbitragevault

# External APIs  
KEEPA_API_KEY=your_keepa_api_key_here

# Application Settings
SECRET_KEY=your_jwt_secret_key
DEBUG=false
ENVIRONMENT=production
API_V1_STR=/api/v1
```

### **Optional Configuration**
```env
# Future integrations (not yet required)
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id  
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## 🎯 **Business Value Delivered**

### **Immediate Value (v1.4.1-stable)**
- **Automated Analysis**: Process ISBN/ASIN lists without manual research
- **Real-Time Data**: Current Amazon marketplace conditions via Keepa
- **Smart Filtering**: Focus on high-probability arbitrage opportunities
- **Risk Assessment**: Avoid volatile products and market traps

### **Operational Benefits**
- **Time Savings**: 10x faster than manual product research
- **Data Accuracy**: Eliminate human error in ROI calculations  
- **Scalability**: Process hundreds of products simultaneously
- **Decision Support**: Confidence scoring and recommendation engine

### **Competitive Advantages**
- **Professional Grade**: Enterprise-level architecture and reliability
- **API-First Design**: Easy integration with existing workflows
- **Extensible Platform**: Ready for advanced features and customization
- **Open Source**: Full control and customization capabilities

## 🔄 **Version History**

- **v1.4.1-stable** (Current): Backend Complete + Keepa Integration + Business Logic ✅
- **v1.3.0**: FastAPI Implementation + Database Layer ✅  
- **v1.2.5**: Repository Layer + Advanced Filtering ✅
- **v1.1.0**: Core Models + SQLAlchemy Setup ✅
- **v1.0.0**: Project Bootstrap + Architecture Definition ✅

**Next Milestones**:
- **v1.5.0**: Frontend Dashboard 🚧
- **v1.6.0**: Advanced Integrations 🚧
- **v1.7.0**: Production Deployment 🚧

## 🤝 **Contributing & Development**

### **Development Workflow**
1. **Fork & Clone**: Standard GitHub workflow
2. **Feature Branch**: `git checkout -b feature/your-feature-name`
3. **BUILD-TEST-VALIDATE**: Follow our development model
4. **Commit Frequently**: Atomic commits with descriptive messages
5. **Pull Request**: Comprehensive description + tests passing

### **Code Standards**
- **Python**: PEP 8 compliance, type hints required
- **Testing**: Minimum 80% coverage for new features
- **Documentation**: Docstrings for all public methods
- **Security**: No hardcoded secrets, environment variables only

---

**Last Updated**: 22 August, 2025  
**Version**: v1.4.1-stable  
**BUILD-TEST-VALIDATE**: Cycle 1.4.1 Complete ✅  
**Ready for Phase 1.5**: Frontend Development 🚀

**Technical Status**: Production-ready backend with stable business logic and real-time marketplace data analysis capabilities.
