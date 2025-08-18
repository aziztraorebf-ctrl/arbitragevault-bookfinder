# ArbitrageVault Backend

FastAPI backend for book arbitrage analysis with PostgreSQL, JWT authentication, and async operations.

## 🚀 Quick Start (< 5 minutes)

### Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose** (for PostgreSQL)  
- **uv** (Python package manager)

### 1. Install uv (if not already installed)
```bash
# Windows
powershell -Command "Set-ExecutionPolicy RemoteSigned -scope CurrentUser -Force; iwr https://astral.sh/uv/install.ps1 -useb | iex"

# Alternative: pip install uv
```

### 2. Clone & Setup
```bash
cd backend/
cp .env.example .env
uv sync
```

### 3. Start Development Environment
```bash
make dev
# This will:
# - Start PostgreSQL (Docker)
# - Run database migrations
# - Start FastAPI server with hot reload
```

### 4. Verify Installation
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/live
- **Database Health**: http://localhost:8000/api/v1/health/ready

## 📋 Available Commands

```bash
make help              # Show all commands
make dev               # Start development server
make test              # Run all tests with coverage
make lint              # Run linting (ruff + black)
make type              # Run type checking (mypy)
make migrate           # Run database migrations
make revision msg="x"  # Create new migration
make db.reset          # Reset database (DEV ONLY!)
```

## 🏗️ Architecture Overview

```
app/
├── main.py                 # FastAPI entry point
├── api/v1/                # API routes (versioned)
│   ├── routers/           # Route handlers
│   ├── deps.py            # Common dependencies  
│   └── errors.py          # Error handling
├── core/                  # Core configuration
│   ├── settings.py        # App settings
│   ├── security.py        # Auth & crypto
│   ├── db.py             # Database config
│   └── logging.py        # Structured logging
├── models/               # SQLAlchemy models
├── repositories/         # Data access layer
├── services/            # Business logic layer
└── schemas/             # Pydantic schemas
```

## 🔐 Security Features

- **Argon2 password hashing** with pepper
- **JWT tokens** (access + refresh with rotation)
- **Role-based access control** (Admin/Sourcer)
- **Scope-based permissions**
- **Rate limiting** on authentication endpoints
- **CORS protection** with whitelist

## 🧪 Testing

```bash
make test              # Full test suite + coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests (requires DB)
make test-e2e         # End-to-end API tests
```

**Coverage requirement**: ≥80% for all new code

## 📊 API Endpoints

### Health & Monitoring
- `GET /api/v1/health/live` - Application liveness
- `GET /api/v1/health/ready` - Database connectivity

### Authentication  
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login  
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (revoke tokens)
- `GET /api/v1/auth/me` - Current user info

### Users (Admin only)
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user
- `PATCH /api/v1/users/{id}` - Update user role

### Batches & Analysis (Phase 2)
- Endpoints for batch processing and analysis results

## 🐳 Development with Docker

The PostgreSQL database runs in Docker for consistent development:

```bash
# Start services
make dev

# Stop services  
make docker-down

# Reset everything (removes volumes)
make db.reset
```

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://memex:memex@localhost:5432/memex

# JWT Security
JWT_SECRET=your-secure-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=20
REFRESH_TOKEN_EXPIRE_DAYS=14

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000
# Kill the process or use different port
uvicorn app.main:app --port 8001
```

### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.dev.yml ps
# View logs
docker-compose -f docker-compose.dev.yml logs postgres
# Reset database
make db.reset
```

### Dependencies Issues
```bash
# Clean install
make clean
uv sync --no-cache
```

## 📈 Performance

- **Response time target**: < 200ms for simple queries
- **Database**: Connection pooling with asyncpg
- **Logging**: Structured JSON with request tracing
- **Monitoring**: Health checks separate for app/database

## 🔄 CI/CD

GitHub Actions automatically run on pull requests:
- **Linting**: ruff + black
- **Type checking**: mypy  
- **Tests**: pytest with PostgreSQL service
- **Coverage**: Must be ≥80%

## 📦 Production Deployment

1. Set secure environment variables
2. Use production-grade PostgreSQL
3. Configure proper CORS origins
4. Set up monitoring and logs aggregation
5. Consider Redis for rate limiting

---

**Phase 1 Complete**: Secure foundation ready for Keepa integration and business logic

🤖 Generated with [Memex](https://memex.tech)