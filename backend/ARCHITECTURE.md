# ArbitrageVault Backend - Architecture Documentation

## 🏗️ **System Architecture Overview**

### **Hybrid Architecture Pattern**

ArbitrageVault implements a **Hybrid Architecture** separating compute and data layers for optimal performance, scalability, and maintainability.

```
                    ┌─────────────────────────────────────────┐
                    │         PRODUCTION ENVIRONMENT          │
                    └─────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌─────────────────┐            ┌──────────────────┐            ┌─────────────────┐
│   FRONTEND      │            │    BACKEND       │            │    DATABASE     │
│                 │            │                  │            │                 │
│  React/Next.js  │◄───HTTP────┤  FastAPI + uv    │◄──AsyncPG──┤ Neon PostgreSQL │
│  (Future)       │            │  SQLAlchemy 2.0  │            │  300-500 conn   │
│                 │            │  Pydantic v2     │            │  Branch Support │
└─────────────────┘            └──────────────────┘            └─────────────────┘
                                        │                               
                               ┌──────────────────┐                    
                               │  EXTERNAL APIs   │                    
                               │  Keepa, OpenAI   │                    
                               └──────────────────┘                    
```

---

## 🎯 **Architecture Decisions & Benefits**

### **1. Hybrid Backend + Database Architecture**

#### **Decision**
- **Backend**: Render Web Service (Compute Layer)
- **Database**: Neon PostgreSQL (Data Layer)
- **Pattern**: Separation of concerns between compute and storage

#### **Benefits**
- **Scalability**: Independent scaling of compute vs storage resources
- **Performance**: 15x connection pool improvement (20 → 300-500 connections)
- **Reliability**: Database managed by Neon specialists, backend by Render
- **Cost Optimization**: Pay for compute and storage separately based on usage
- **Flexibility**: Can switch backend hosting without database migration

#### **Trade-offs**
- **Complexity**: Managing two services instead of one
- **Network Latency**: Slight increase due to external database connection
- **Configuration**: Need to manage connection strings and SSL certificates

---

## 🔧 **Technology Stack**

### **Backend Framework**
```python
FastAPI 0.104+
├── Async/Await Support          # Non-blocking I/O operations
├── Automatic OpenAPI Generation # API documentation
├── Pydantic Integration        # Request/response validation
├── Dependency Injection        # Service layer management
└── CORS Middleware            # Frontend integration support
```

### **Database Layer**
```sql
Neon PostgreSQL 16
├── Connection Pooling          # 300-500 concurrent connections
├── Branch-based Development   # Schema versioning and testing
├── Real-time Scaling          # Auto-scaling based on demand
├── Point-in-time Recovery     # Data protection and rollback
└── SSL/TLS Encryption         # Security in transit
```

### **ORM & Validation**
```python
SQLAlchemy 2.0
├── Async Engine               # Non-blocking database operations
├── Declarative Models         # Type-safe database schema
├── Migration Support          # Alembic integration
└── Connection Pool Management # Optimized for Neon

Pydantic v2
├── from_attributes=True       # SQLAlchemy model compatibility
├── Field Validators           # Custom validation logic
├── JSON Schema Generation     # OpenAPI integration
└── Type Safety               # Runtime type validation
```

---

## 🗂️ **Project Structure**

### **Application Architecture**
```
backend/
├── app/                           # Main application package
│   ├── main.py                    # FastAPI application entry point
│   ├── api/                       # API routes and endpoints
│   │   └── v1/                    # API version 1
│   │       ├── routers/           # Route handlers
│   │       │   ├── batches.py     # Batch management endpoints
│   │       │   ├── analyses.py    # Analysis CRUD endpoints
│   │       │   ├── health.py      # Health check endpoints
│   │       │   └── config.py      # Configuration endpoints
│   │       └── __init__.py        # API package initialization
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── base.py               # Base model with common fields
│   │   ├── batch.py              # Batch analysis model
│   │   ├── analysis.py           # Analysis result model
│   │   ├── user.py               # User management model
│   │   └── business_config.py    # Business configuration model
│   ├── schemas/                   # Pydantic validation schemas
│   │   ├── batch.py              # Batch request/response schemas
│   │   ├── analysis.py           # Analysis schemas
│   │   └── business_config_schemas.py # Configuration schemas
│   ├── repositories/              # Data access layer
│   │   ├── base_repository.py    # Generic CRUD operations
│   │   ├── batch_repository.py   # Batch-specific operations
│   │   └── analysis_repository.py # Analysis data operations
│   ├── services/                  # Business logic layer
│   │   ├── keepa_integration.py  # External API integration
│   │   └── business_logic.py     # Core business calculations
│   ├── core/                      # Core application components
│   │   ├── db.py                 # Database configuration
│   │   ├── config.py             # Application settings
│   │   ├── pagination.py         # Pagination utilities
│   │   └── exceptions.py         # Custom exception classes
│   └── utils/                     # Utility functions
│       ├── logging.py            # Structured logging setup
│       └── calculations.py       # Business calculation helpers
├── tests/                         # Test suite
│   ├── test_endpoints.py         # API endpoint tests
│   ├── test_models.py            # Model validation tests
│   ├── test_repository.py        # Data access tests
│   └── test_integration.py       # End-to-end tests
├── migrations/                    # Database migration files
│   └── versions/                 # Alembic version files
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml               # Python project configuration
├── .env.example                 # Environment variables template
└── README.md                    # Project documentation
```

---

## 🔄 **Data Flow Architecture**

### **Request Processing Flow**

```
1. HTTP Request
   ↓
2. FastAPI Middleware
   ↓
3. Pydantic Request Validation
   ↓
4. Route Handler (API Layer)
   ↓
5. Repository (Data Access Layer)
   ↓
6. SQLAlchemy ORM
   ↓
7. AsyncPG Database Driver
   ↓
8. Neon PostgreSQL
   ↓
9. Response Processing
   ↓
10. Pydantic Response Serialization
    ↓
11. HTTP Response
```

### **Database Connection Management**

```python
# Connection Pool Configuration
DATABASE_CONFIG = {
    "pool_size": 10,           # Base connections
    "max_overflow": 20,        # Additional connections
    "pool_timeout": 30,        # Wait time for connection
    "pool_recycle": 3600,      # Connection lifetime
    "pool_pre_ping": True,     # Health check connections
}

# Neon PostgreSQL Benefits
NEON_ADVANTAGES = {
    "connection_limit": "300-500 concurrent",
    "scaling": "Auto-scaling based on demand", 
    "branching": "Schema versioning support",
    "backups": "Point-in-time recovery",
    "monitoring": "Built-in performance metrics"
}
```

---

## 🛡️ **Security Architecture**

### **Data Protection**
- **SSL/TLS Encryption**: All database connections encrypted in transit
- **Environment Variables**: Sensitive data stored in environment configuration
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Input Validation**: Pydantic schemas validate all incoming data

### **Authentication & Authorization** (Planned)
```python
# Future Authentication Architecture
AUTHENTICATION_STACK = {
    "provider": "Stack Auth",
    "integration": "Neon Auth provisioning",
    "patterns": "JWT tokens + session management",
    "features": ["SSO", "MFA", "RBAC"]
}
```

---

## 📊 **Performance Architecture**

### **Database Optimization**

#### **Connection Pool Strategy**
```python
# Optimized for Neon PostgreSQL
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,              # Conservative base pool
    max_overflow=20,           # Burst capacity
    pool_timeout=30,           # Reasonable wait time
    pool_recycle=3600,         # Prevent stale connections
    pool_pre_ping=True,        # Health check before use
    echo=False                 # Disable SQL logging in production
)
```

#### **Query Optimization Patterns**
- **Async Operations**: All database calls use async/await pattern
- **Relationship Loading**: Strategic use of `selectinload()` for eager loading
- **Pagination**: Efficient offset/limit with total count optimization
- **Indexes**: Strategic indexes on frequently queried columns

### **Response Time Targets**
```
Health Endpoints:     < 50ms
Simple Queries:       < 200ms
Complex Queries:      < 500ms
Batch Operations:     < 2000ms
```

---

## 🔧 **Development & Deployment Architecture**

### **Development Workflow**

#### **Context7 + MCP Tools Integration**
```python
# Development Methodology
DEVELOPMENT_PATTERN = {
    "documentation_first": "Always consult Context7 before implementation",
    "mcp_tools": "Use MCP Neon tools for all database operations", 
    "build_test_validate": "Continuous validation with real data",
    "git_workflow": "Frequent commits with descriptive messages"
}
```

#### **Database Management**
```python
# MCP Tools for Database Operations
MCP_NEON_TOOLS = [
    "create_project",          # New database setup
    "run_sql",                # Execute SQL queries
    "prepare_database_migration", # Schema changes
    "describe_table_schema",   # Schema introspection
    "list_slow_queries",      # Performance monitoring
    "prepare_query_tuning",   # Query optimization
]
```

### **Deployment Pipeline**

```yaml
# Render Auto-Deploy Configuration
deployment:
  trigger: git_push_main
  service_id: srv-d3c9sbt6ubrc73ejrusg
  build_command: "cd backend && uv sync --no-dev --frozen"
  start_command: "cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  environment: production
  auto_deploy: true
  health_check: "/health"
```

---

## 📈 **Monitoring & Observability**

### **Health Monitoring**
```python
# Health Check Architecture
HEALTH_ENDPOINTS = {
    "/health": "Basic service availability",
    "/health/detailed": "Database connectivity + performance",
    "/health/dependencies": "External service status"
}
```

### **Performance Metrics**
- **Response Times**: Per-endpoint performance tracking
- **Database Connections**: Pool utilization monitoring
- **Error Rates**: Categorized error frequency analysis
- **Resource Usage**: Memory and CPU utilization

### **Logging Strategy**
```python
# Structured Logging Configuration
LOGGING_CONFIG = {
    "format": "json",
    "level": "INFO",  # Production
    "fields": ["timestamp", "level", "message", "request_id", "user_id"],
    "destinations": ["stdout", "file_rotation"]
}
```

---

## 🧪 **Testing Architecture**

### **Testing Strategy Pyramid**

```
                    ┌─────────────┐
                    │    E2E      │ ← Integration Tests
                    │   Tests     │   (Real API calls)
                    └─────────────┘
                  ┌─────────────────┐
                  │  Integration    │ ← Service Tests
                  │     Tests       │   (Database + API)
                  └─────────────────┘
                ┌─────────────────────┐
                │    Unit Tests       │ ← Component Tests
                │ (Models, Schemas,   │   (Isolated logic)
                │  Calculations)      │
                └─────────────────────┘
```

### **Test Environment Configuration**
```python
# Test Database Strategy
TEST_CONFIG = {
    "database": "Separate test branch on Neon",
    "data": "Real data samples, not just mocks",
    "isolation": "Transaction rollback after each test",
    "parallel": "Safe for concurrent test execution"
}
```

---

## 🔮 **Future Architecture Evolution**

### **Planned Enhancements**

#### **Frontend Integration (v2.1)**
- **Type Generation**: Auto-generate TypeScript types from OpenAPI
- **State Management**: Zustand with React Query for API caching
- **Real-time Updates**: WebSocket integration for batch processing status

#### **Advanced Features (v2.2)**
- **Caching Layer**: Redis integration for frequently accessed data
- **Message Queue**: Background job processing with Celery/RQ
- **Event Sourcing**: Audit trail and state reconstruction capabilities

#### **Enterprise Features (v2.3)**
- **Multi-tenancy**: User isolation and resource quotas
- **Advanced Analytics**: Time-series data and business intelligence
- **API Rate Limiting**: Protection against abuse and resource exhaustion
- **Disaster Recovery**: Multi-region deployment and failover

---

## 📋 **Architecture Decision Records (ADRs)**

### **ADR-001: Hybrid Architecture Choice**
- **Status**: Accepted
- **Context**: Need scalable database solution beyond Render PostgreSQL limits
- **Decision**: Separate backend (Render) and database (Neon) services
- **Consequences**: 15x performance improvement, increased complexity

### **ADR-002: Context7 Documentation-First Development**
- **Status**: Accepted  
- **Context**: Reduce technical debt and follow proven patterns
- **Decision**: Always consult Context7 before implementing new patterns
- **Consequences**: Higher code quality, consistent patterns, reduced bugs

### **ADR-003: MCP Tools for Database Operations**
- **Status**: Accepted
- **Context**: Need reliable, repeatable database management
- **Decision**: Use MCP Neon tools for all database operations
- **Consequences**: Automated operations, reduced human error, better auditability

---

*This architecture documentation reflects the current state of the ArbitrageVault backend and serves as a guide for future development and maintenance decisions.*