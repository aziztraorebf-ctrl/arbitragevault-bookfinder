# ArbitrageVault - Architecture Backend

> **Version**: 1.0.0
> **Dernière mise à jour**: 28 Novembre 2025
> **Refactoring SRP**: Complété (Phase 3)

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture en couches](#architecture-en-couches)
3. [Modules Keepa (Refactoring SRP)](#modules-keepa-refactoring-srp)
4. [Patterns de conception](#patterns-de-conception)
5. [Flux de données](#flux-de-données)
6. [Guide développeur](#guide-développeur)
7. [Conventions de code](#conventions-de-code)

---

## 🎯 Vue d'ensemble

ArbitrageVault est une plateforme d'analyse d'arbitrage Amazon construite sur FastAPI avec intégration Keepa API. L'architecture suit les principes SOLID avec une séparation claire des responsabilités.

### Stack Technologique

- **Framework**: FastAPI (Python 3.11+)
- **Base de données**: PostgreSQL (Neon)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic V2
- **API externe**: Keepa API
- **Monitoring**: Sentry
- **Déploiement**: Render

### Principes Architecturaux

1. **Separation of Concerns** (SRP) - Chaque module a une seule responsabilité
2. **Dependency Injection** - Via FastAPI `Depends()`
3. **Layer Isolation** - API → Services → Repositories → Models
4. **Defensive Programming** - Validation à chaque couche
5. **Resilience Patterns** - Circuit Breaker, Throttling, Caching

---

## 🏛️ Architecture en couches

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (Routers)                     │
│  FastAPI endpoints, request/response validation (Pydantic)   │
│  - /api/v1/keepa, /api/v1/autosourcing, /api/v1/analytics   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  Business logic, orchestration, external API calls           │
│  - KeepaService, AutoSourcingService, AnalyticsService       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Repository Layer                          │
│  Data persistence, database queries (SQLAlchemy)             │
│  - AnalysisRepository, BatchRepository, UserRepository       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Model Layer                             │
│  SQLAlchemy ORM models, database schema                      │
│  - Analysis, Batch, User, BusinessConfig                     │
└─────────────────────────────────────────────────────────────┘

                   Cross-Cutting Concerns
┌─────────────────────────────────────────────────────────────┐
│                        Core Layer                            │
│  - Logging, Exceptions, Config, Auth, CORS                   │
│  - Calculations: ROI, Velocity, Advanced Scoring             │
│  - Guards: Token requirements, rate limiting                 │
└─────────────────────────────────────────────────────────────┘
```

### Structure des Dossiers

```
backend/app/
├── api/
│   └── v1/
│       ├── endpoints/     # Endpoints complexes (analytics, products, niches)
│       └── routers/       # Routers principaux (keepa, auth, batches)
│
├── services/              # Business logic
│   ├── keepa_*.py        # Keepa integration (10+ modules)
│   ├── autosourcing_*.py # AutoSourcing logic
│   ├── *_service.py      # Domain services
│   └── ...
│
├── repositories/          # Data access layer
│   ├── base_repository.py
│   ├── analysis_repository.py
│   ├── batch_repository.py
│   └── ...
│
├── models/                # SQLAlchemy ORM models
│   ├── base.py
│   ├── analysis.py
│   ├── batch.py
│   ├── autosourcing.py
│   └── ...
│
├── core/                  # Core utilities
│   ├── settings.py        # Pydantic Settings
│   ├── db.py             # Database connection
│   ├── exceptions.py     # Custom exceptions
│   ├── logging.py        # Logging configuration
│   ├── auth.py           # JWT authentication
│   ├── calculations.py   # Business calculations
│   ├── advanced_scoring.py
│   ├── roi_calculations.py
│   ├── velocity_calculations.py
│   └── guards/           # Request guards
│
├── routers/              # Additional routers
│   ├── stock_estimate.py
│   ├── strategic_views.py
│   └── ...
│
└── main.py               # Application entry point
```

---

## 🔧 Modules Keepa (Refactoring SRP)

Le système Keepa a été refactoré selon le **Single Responsibility Principle** en 10 modules spécialisés.

### Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                       Keepa Integration                           │
│                   (API Router + Service Layer)                    │
└──────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
    ┌───────────────────────┐        ┌──────────────────────┐
    │    API Layer (379 LOC)│        │  Service Layer       │
    │  keepa.py (Facade)    │        │  (668 LOC)           │
    │  ├─ keepa_schemas.py  │        │  keepa_service.py    │
    │  ├─ keepa_utils.py    │        │  (Facade)            │
    │  └─ keepa_debug.py    │        └──────────────────────┘
    └───────────────────────┘                 │
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        │                     │                     │
                        ▼                     ▼                     ▼
            ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐
            │  keepa_models.py │  │  keepa_cache.py  │  │keepa_throttle.py│
            │  Data Models     │  │  Multi-tier      │  │Token Bucket     │
            │  (118 LOC)       │  │  Caching         │  │Rate Limiting    │
            │                  │  │  (152 LOC)       │  │(171 LOC)        │
            └──────────────────┘  └──────────────────┘  └─────────────────┘
```

### Module Breakdown

#### 1. API Layer (Routers)

##### `keepa.py` - Main Router (Facade, 379 LOC)
- **Responsabilité**: Orchestration des endpoints Keepa
- **Endpoints principaux**:
  - `POST /ingest` - Ingestion batch d'ASINs/ISBNs
  - `GET /{asin}/metrics` - Métriques complètes produit
  - `GET /{asin}/raw` - Données brutes Keepa
- **Délégation**: Importe et orchestre `keepa_schemas`, `keepa_utils`, `keepa_debug`

##### `keepa_schemas.py` - Request/Response Models (156 LOC)
- **Responsabilité**: Validation Pydantic des requêtes/réponses
- **Schemas clés**:
  - `IngestBatchRequest` - Validation batch ingestion
  - `MetricsResponse` - Structure réponse métriques
  - `ConfigAudit`, `KeepaMetadata`, `AnalysisResult`

##### `keepa_utils.py` - Utility Functions (160 LOC)
- **Responsabilité**: Fonctions utilitaires réutilisables
- **Fonctions principales**:
  - `generate_trace_id()` - Génération UUID pour traçabilité
  - `normalize_identifier()` - Nettoyage ASIN/ISBN
  - `analyze_product()` - Analyse complète produit

##### `keepa_debug.py` - Debug & Health Endpoints (380 LOC)
- **Responsabilité**: Endpoints de débogage et santé
- **Endpoints**:
  - `GET /health` - Health check avec métriques token
  - `GET /test` - Test connexion Keepa
  - `POST /debug/analyze` - Debug analyse produit
- **Background Jobs**: `process_batch_async()` pour ingestion asynchrone

#### 2. Service Layer

##### `keepa_service.py` - Main Service (Facade, 668 LOC)
- **Responsabilité**: Client Keepa avec résilience et monitoring
- **Features**:
  - Client HTTP async avec timeouts
  - Throttling token-aware
  - Circuit breaker pour fault tolerance
  - Multi-tier caching (meta, pricing, BSR)
  - Métriques complètes et logging
- **Délégation**: Utilise `KeepaCache`, `KeepaThrottle`, `keepa_models`

##### `keepa_models.py` - Data Models (118 LOC)
- **Responsabilité**: Dataclasses, enums, constantes
- **Classes principales**:
  - `CircuitState` - États circuit breaker
  - `CacheEntry` - Entrée cache avec TTL
  - `TokenMetrics` - Tracking usage tokens
  - `CircuitBreaker` - Implémentation circuit breaker
- **Constantes**:
  - `ENDPOINT_COSTS` - Coûts tokens par endpoint
  - `MIN_BALANCE_THRESHOLD`, `SAFETY_BUFFER`

##### `keepa_cache.py` - Cache Management (152 LOC)
- **Responsabilité**: Système de cache multi-tiers
- **Features**:
  - TTLs différenciés par type de données:
    - `meta`: 24h (métadonnées produit stables)
    - `pricing`: 30min (prix volatiles)
    - `bsr`: 60min (BSR semi-volatiles)
  - Quick cache pour tests répétés (10min TTL)
  - Cleanup automatique des entrées expirées
  - Statistiques cache (hits/misses)

##### `keepa_throttle.py` - Rate Limiting (171 LOC)
- **Responsabilité**: Prévention épuisement tokens
- **Algorithme**: Token Bucket
- **Configuration**:
  - 20 tokens/minute (limite plan Keepa)
  - Burst capacity: 200 tokens
  - Warning threshold: 80 tokens
  - Critical threshold: 40 tokens
- **Features**:
  - Thread-safe (asyncio.Lock)
  - Auto-refill tokens
  - Métriques usage (total requests, wait time)

#### 3. Modules Spécialisés (Services)

##### `keepa_constants.py`
- Constantes globales Keepa
- Mapping domaines/catégories

##### `keepa_extractors.py`
- Extraction données depuis réponses Keepa
- Parsing BSR, prix, sellers

##### `keepa_parser_v2.py`
- Parser v2 pour nouveaux formats Keepa
- Gestion backward compatibility

##### `keepa_product_finder.py`
- Discovery produits via Keepa
- Recherche bestsellers/deals

##### `keepa_service_factory.py`
- Factory pattern pour KeepaService
- Configuration contextualisée

### Diagramme de Flux - Ingestion Batch

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ POST /api/v1/keepa/ingest
       ▼
┌──────────────────────────────────────────────────────────────┐
│  keepa.py - ingest_batch()                                   │
│  1. Generate trace_id                                        │
│  2. Validate request (keepa_schemas.IngestBatchRequest)      │
│  3. Get effective config (BusinessConfigService)             │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  keepa_utils.analyze_product() - Pour chaque ASIN           │
│  1. Normalize identifier                                     │
│  2. Call keepa_service.get_product_data()                    │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  keepa_service.KeepaService                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Check keepa_cache (get)                             │ │
│  │    ├─ HIT → Return cached data                         │ │
│  │    └─ MISS → Continue                                  │ │
│  │                                                          │ │
│  │ 2. Acquire tokens (keepa_throttle.acquire)             │ │
│  │    ├─ Check bucket tokens                              │ │
│  │    ├─ Wait if necessary (refill)                       │ │
│  │    └─ Acquire when available                           │ │
│  │                                                          │ │
│  │ 3. Check circuit breaker                                │ │
│  │    ├─ OPEN → Reject (fail fast)                        │ │
│  │    ├─ HALF_OPEN → Allow test request                   │ │
│  │    └─ CLOSED → Proceed                                 │ │
│  │                                                          │ │
│  │ 4. Call Keepa API (httpx.AsyncClient)                  │ │
│  │    └─ Retry logic (tenacity)                           │ │
│  │                                                          │ │
│  │ 5. Parse response (keepa_parser_v2)                    │ │
│  │                                                          │ │
│  │ 6. Update cache (keepa_cache.set)                      │ │
│  │    └─ Store with appropriate TTL                       │ │
│  │                                                          │ │
│  │ 7. Update metrics (TokenMetrics)                       │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  keepa_utils.analyze_product() - Continue                   │
│  1. Calculate ROI (core.roi_calculations)                    │
│  2. Calculate velocity (core.velocity_calculations)          │
│  3. Generate recommendation (advanced_scoring)               │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────┐
│  keepa.py - Return IngestResponse                           │
│  - batch_id, total_items, successful, failed                 │
│  - results[] with status per ASIN                            │
│  - trace_id for debugging                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎨 Patterns de conception

### 1. Facade Pattern

**Utilisé dans**: `keepa.py`, `keepa_service.py`

```python
# keepa.py - API Facade
from .keepa_schemas import IngestBatchRequest, MetricsResponse
from .keepa_utils import generate_trace_id, analyze_product
from .keepa_debug import router as debug_router

router = APIRouter()
router.include_router(debug_router)

@router.post("/ingest")
async def ingest_batch(...):
    # Orchestre keepa_utils et keepa_service
    pass
```

**Avantages**:
- Interface simple pour complexité sous-jacente
- Backward compatibility lors refactoring
- Point d'entrée unique pour testing

### 2. Repository Pattern

**Utilisé dans**: Couche Repositories

```python
# base_repository.py
class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Any) -> Optional[T]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
```

**Avantages**:
- Abstraction de la persistence
- Facilite testing (mock repositories)
- Réutilisation du code (CRUD générique)

### 3. Circuit Breaker Pattern

**Utilisé dans**: `keepa_service.py`, `keepa_models.CircuitBreaker`

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        # ...

    def can_proceed(self) -> bool:
        if self.state == CircuitState.OPEN:
            if time.time() - self.opened_at > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True
```

**États**:
- **CLOSED**: Trafic normal
- **OPEN**: Rejette toutes requêtes (fail fast)
- **HALF_OPEN**: Test de récupération

**Avantages**:
- Prévient cascade failures
- Récupération automatique
- Améliore résilience système

### 4. Token Bucket Algorithm

**Utilisé dans**: `keepa_throttle.py`

```python
class KeepaThrottle:
    async def acquire(self, cost: int = 1):
        async with self._lock:
            # Refill tokens based on elapsed time
            elapsed = time.monotonic() - self.last_refill
            refill = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + refill)

            # Wait if insufficient tokens
            if self.tokens < cost:
                wait_time = (cost - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= cost
```

**Avantages**:
- Lissage du trafic API
- Gestion bursts contrôlés
- Prévention token exhaustion

### 5. Dependency Injection

**Utilisé dans**: Tous les routers FastAPI

```python
@router.post("/ingest")
async def ingest_batch(
    request: IngestBatchRequest,
    keepa_service: KeepaService = Depends(get_keepa_service),
    config_service: BusinessConfigService = Depends(get_business_config_service)
):
    # Services injectés automatiquement
    pass
```

**Avantages**:
- Découplage des dépendances
- Facilite testing (mock dependencies)
- Configuration centralisée

---

## 🌊 Flux de données

### AutoSourcing Pipeline (Exemple complet)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER REQUEST                                                 │
│    POST /api/v1/autosourcing/run_custom                         │
│    {                                                             │
│      "profile_name": "Tech Books",                              │
│      "discovery_config": { categories: ["books"], ... },        │
│      "scoring_config": { roi_min: 30, velocity_min: 70 }        │
│    }                                                             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. AUTOSOURCING_SERVICE.run_custom_search()                     │
│    - Validate request (autosourcing_validator)                  │
│    - Estimate cost (autosourcing_cost_estimator)                │
│    - Check token balance                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. PRODUCT DISCOVERY (keepa_product_finder)                     │
│    - Call Keepa Bestsellers/Deals API                           │
│    - Filter by BSR range, price range, categories               │
│    - Return 50-100 candidate ASINs                              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. BATCH ANALYSIS (keepa_service + keepa_utils)                 │
│    For each ASIN (parallel with semaphore):                     │
│    ┌───────────────────────────────────────────────────────┐   │
│    │ a. Get product data (keepa_service)                   │   │
│    │    - Check cache → API call if miss → Store cache     │   │
│    │ b. Calculate metrics (keepa_utils.analyze_product)    │   │
│    │    - ROI (core.roi_calculations)                      │   │
│    │    - Velocity (core.velocity_calculations)            │   │
│    │    - Risk score (risk_scoring_service)                │   │
│    │    - Price stability                                  │   │
│    │ c. Generate recommendation (advanced_scoring)         │   │
│    │    - STRONG_BUY, BUY, CONSIDER, SKIP                  │   │
│    └───────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SCORING & FILTERING (scoring_v2)                             │
│    - Apply scoring_config thresholds:                           │
│      • roi_min, velocity_min, stability_min                     │
│      • rating_required, confidence_min                          │
│    - Sort by combined score (ROI * Velocity)                    │
│    - Return top N results                                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. PERSISTENCE (autosourcing models + repositories)             │
│    - Create AutoSourcingJob record                              │
│    - Create AutoSourcingPick records (top results)              │
│    - Update job status (COMPLETED/FAILED)                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. RESPONSE                                                     │
│    {                                                             │
│      "id": "uuid",                                               │
│      "profile_name": "Tech Books",                              │
│      "status": "COMPLETED",                                     │
│      "total_tested": 87,                                        │
│      "total_selected": 12,                                      │
│      "picks": [                                                 │
│        { asin, title, roi_percentage, velocity_score, ... }     │
│      ]                                                           │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👨‍💻 Guide développeur

### Où ajouter du nouveau code ?

#### 1. Nouveau endpoint API

**Scénario**: Ajouter endpoint `GET /api/v1/keepa/{asin}/competitors`

```python
# backend/app/api/v1/routers/keepa.py

@router.get("/{asin}/competitors")
async def get_competitors(
    asin: str,
    keepa_service: KeepaService = Depends(get_keepa_service)
):
    """Get competitor analysis for an ASIN."""
    data = await keepa_service.get_product_data(asin)
    # Extract competitor data
    competitors = extract_competitors(data)
    return {"asin": asin, "competitors": competitors}
```

**Checklist**:
- [ ] Ajouter schema Pydantic dans `keepa_schemas.py` (request/response)
- [ ] Ajouter fonction utilitaire dans `keepa_utils.py` si réutilisable
- [ ] Documenter endpoint (docstring avec OpenAPI tags)
- [ ] Ajouter tests dans `tests/api/v1/test_keepa.py`

#### 2. Nouvelle logique business (Service)

**Scénario**: Calculer "Amazon dominance score"

```python
# backend/app/services/amazon_dominance_service.py

class AmazonDominanceService:
    """Calculate Amazon's market dominance for a product."""

    def calculate_dominance(
        self,
        amazon_on_listing: bool,
        amazon_has_buybox: bool,
        total_sellers: int,
        fba_sellers: int
    ) -> float:
        """
        Calculate dominance score 0-100.

        Returns:
            0-100 score (100 = Amazon dominates completely)
        """
        score = 0.0

        if amazon_on_listing:
            score += 50  # Major factor

        if amazon_has_buybox:
            score += 30  # Strong factor

        # Seller competition factor
        if total_sellers > 0:
            fba_ratio = fba_sellers / total_sellers
            score += (1 - fba_ratio) * 20  # Less FBA = more Amazon dominance

        return min(100.0, score)


def get_amazon_dominance_service() -> AmazonDominanceService:
    """Dependency injection factory."""
    return AmazonDominanceService()
```

**Checklist**:
- [ ] Créer nouveau fichier service avec responsabilité unique
- [ ] Ajouter factory function pour DI (`get_*_service`)
- [ ] Documenter méthodes avec docstrings
- [ ] Ajouter tests unitaires dans `tests/services/`

#### 3. Nouveau calcul (Core)

**Scénario**: Calculer "breakeven days"

```python
# backend/app/core/breakeven_calculations.py

from decimal import Decimal

def calculate_breakeven_days(
    net_profit: Decimal,
    sale_price: Decimal,
    monthly_storage_cost: Decimal
) -> int:
    """
    Calculate days to breakeven considering storage costs.

    Args:
        net_profit: Net profit per unit after all fees
        sale_price: Expected sale price
        monthly_storage_cost: Monthly FBA storage cost

    Returns:
        Estimated days to breakeven (accounting for storage erosion)
    """
    if net_profit <= 0:
        return 999  # Never profitable

    daily_storage = monthly_storage_cost / Decimal("30")

    # Find day where: net_profit - (daily_storage * days) = 0
    breakeven = int(net_profit / daily_storage)

    return max(1, breakeven)
```

**Checklist**:
- [ ] Placer dans `backend/app/core/` (pas de dépendances externes)
- [ ] Utiliser `Decimal` pour calculs financiers précis
- [ ] Documenter formules et assumptions
- [ ] Ajouter edge cases handling
- [ ] Tester avec pytest (100% coverage pour core)

#### 4. Nouveau modèle database

**Scénario**: Tracker historique prix produit

```python
# backend/app/models/price_history.py

from sqlalchemy import Column, String, DECIMAL, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class PriceHistory(Base):
    """Historical price tracking for products."""

    __tablename__ = "price_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asin = Column(String, nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    seller_count = Column(Integer, nullable=True)
    amazon_on_listing = Column(Boolean, default=False)
    tracked_at = Column(DateTime, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_asin_tracked_at", "asin", "tracked_at"),
    )
```

**Migrations Alembic**:

```bash
# Créer migration
cd backend
alembic revision --autogenerate -m "Add price_history table"

# Vérifier migration générée
cat alembic/versions/xxxx_add_price_history_table.py

# Appliquer migration
alembic upgrade head
```

**Checklist**:
- [ ] Créer modèle SQLAlchemy dans `app/models/`
- [ ] Ajouter indexes appropriés (query patterns)
- [ ] Générer migration Alembic
- [ ] Appliquer migration en dev/staging avant production
- [ ] Créer repository correspondant (`price_history_repository.py`)

#### 5. Nouvelle configuration business

**Scénario**: Ajouter configuration "textbook strategy"

```python
# backend/app/models/business_config.py - Update schema

from pydantic import BaseModel, Field

class TextbookStrategyConfig(BaseModel):
    """Textbook-specific strategy parameters."""

    roi_boost: float = Field(default=1.2, description="ROI multiplier for textbooks")
    velocity_penalty: float = Field(default=0.8, description="Velocity reduced (seasonal)")
    prefer_fba: bool = Field(default=True, description="Prefer FBA sellers")


class BusinessConfigSchema(BaseModel):
    """Business configuration schema."""

    # ... existing fields ...

    textbook_strategy: Optional[TextbookStrategyConfig] = None
```

**Migration**:

```python
# alembic/versions/xxxx_add_textbook_strategy.py

def upgrade():
    # PostgreSQL JSON columns support nested updates
    op.execute("""
        UPDATE business_configs
        SET config = jsonb_set(
            config,
            '{textbook_strategy}',
            '{"roi_boost": 1.2, "velocity_penalty": 0.8, "prefer_fba": true}'
        )
        WHERE scope = 'global'
    """)

def downgrade():
    op.execute("""
        UPDATE business_configs
        SET config = config - 'textbook_strategy'
    """)
```

**Checklist**:
- [ ] Ajouter schema Pydantic dans `business_config.py`
- [ ] Créer migration Alembic pour default values
- [ ] Mettre à jour `BusinessConfigService` pour merge hiérarchique
- [ ] Documenter nouvelle config dans `CONFIGURATION.md`
- [ ] Ajouter tests pour validation schema

### Structure d'un nouveau module

Template pour créer un nouveau service respectant SRP:

```python
"""
[Module Name] Service
=====================
[Brief description of single responsibility]

Author: [Your Name]
Date: [YYYY-MM-DD]
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class [ModuleName]Service:
    """
    [Service description with clear responsibility statement]

    Responsibilities:
    - [Responsibility 1]
    - [Responsibility 2]
    - [Responsibility 3]

    Dependencies:
    - [Dependency 1]: [Usage]
    - [Dependency 2]: [Usage]
    """

    def __init__(self, dependency1: Type1, dependency2: Type2):
        """
        Initialize service with dependencies.

        Args:
            dependency1: [Description]
            dependency2: [Description]
        """
        self.dependency1 = dependency1
        self.dependency2 = dependency2

    async def main_method(self, param: str) -> Dict[str, Any]:
        """
        [Method description]

        Args:
            param: [Description]

        Returns:
            [Description of return value]

        Raises:
            ValueError: [When this is raised]
            CustomException: [When this is raised]
        """
        logger.info(f"Starting main_method with param={param}")

        try:
            # Implementation
            result = await self._internal_method(param)
            return result

        except Exception as e:
            logger.error(f"Error in main_method: {str(e)}", exc_info=True)
            raise

    async def _internal_method(self, param: str) -> Any:
        """Internal helper method (private)."""
        pass


# Dependency Injection Factory
def get_[module_name]_service(
    dependency1: Type1 = Depends(get_dependency1),
    dependency2: Type2 = Depends(get_dependency2)
) -> [ModuleName]Service:
    """
    FastAPI dependency injection factory.

    Usage:
        @router.get("/endpoint")
        async def endpoint(
            service: [ModuleName]Service = Depends(get_[module_name]_service)
        ):
            ...
    """
    return [ModuleName]Service(dependency1, dependency2)
```

---

## 📜 Conventions de code

### 1. Naming Conventions

```python
# Modules/Files: snake_case
keepa_service.py
roi_calculations.py
business_config_service.py

# Classes: PascalCase
class KeepaService:
class BusinessConfigService:
class AutoSourcingJob:

# Functions/Variables: snake_case
def calculate_roi():
async def get_product_data():
total_tokens = 100

# Constants: UPPER_SNAKE_CASE
ENDPOINT_COSTS = {...}
MIN_BALANCE_THRESHOLD = 10
DEFAULT_CACHE_TTL = 3600

# Private methods: _leading_underscore
def _internal_calculation():
async def _validate_request():

# Type hints: Always use
def calculate(value: Decimal) -> Decimal:
async def fetch(asin: str) -> Optional[Dict[str, Any]]:
```

### 2. Import Order

```python
# 1. Standard library
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

# 3. Local application
from app.core.exceptions import InsufficientTokensError
from app.services.keepa_service import KeepaService
from app.models.analysis import Analysis
```

### 3. Docstrings - Google Style

```python
def calculate_roi(
    buy_price: Decimal,
    sell_price: Decimal,
    fees: Decimal
) -> Decimal:
    """
    Calculate Return on Investment percentage.

    This function calculates net ROI after deducting all fees
    from the gross profit margin.

    Args:
        buy_price: Acquisition cost per unit
        sell_price: Expected selling price
        fees: Total fees (Amazon + FBA + prep)

    Returns:
        ROI percentage (0-100+)

    Raises:
        ValueError: If buy_price is zero or negative

    Example:
        >>> calculate_roi(
        ...     buy_price=Decimal("10.00"),
        ...     sell_price=Decimal("20.00"),
        ...     fees=Decimal("5.00")
        ... )
        Decimal("50.00")
    """
    if buy_price <= 0:
        raise ValueError("buy_price must be positive")

    net_profit = sell_price - fees - buy_price
    roi = (net_profit / buy_price) * 100

    return roi
```

### 4. Error Handling

```python
# Custom exceptions (backend/app/core/exceptions.py)
class ArbitrageVaultException(Exception):
    """Base exception for all custom errors."""
    pass

class InsufficientTokensError(ArbitrageVaultException):
    """Raised when Keepa token balance too low."""
    pass

class KeepaRateLimitError(ArbitrageVaultException):
    """Raised when Keepa rate limit exceeded."""
    pass


# Usage in services
async def get_product_data(self, asin: str) -> Dict[str, Any]:
    """Get product data with proper error handling."""

    try:
        # Check token balance
        if self.token_balance < MIN_BALANCE_THRESHOLD:
            raise InsufficientTokensError(
                f"Token balance {self.token_balance} < {MIN_BALANCE_THRESHOLD}"
            )

        # Make API call
        response = await self.client.get(...)

        return response.json()

    except httpx.TimeoutException as e:
        logger.error(f"Keepa API timeout for {asin}: {str(e)}")
        raise KeepaRateLimitError("API timeout - possible rate limit")

    except Exception as e:
        logger.error(f"Unexpected error for {asin}: {str(e)}", exc_info=True)
        raise
```

### 5. Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

# Levels:
# - DEBUG: Detailed diagnostic info (off in production)
# - INFO: Confirmation things working as expected
# - WARNING: Something unexpected but handled
# - ERROR: Serious problem, function failed
# - CRITICAL: System-level failure

async def ingest_batch(identifiers: List[str]):
    """Example with structured logging."""

    # INFO: High-level flow
    logger.info(
        f"Starting batch ingestion",
        extra={
            "count": len(identifiers),
            "trace_id": trace_id
        }
    )

    # DEBUG: Detailed diagnostics
    logger.debug(f"Identifiers: {identifiers[:5]}...")  # Don't log all

    try:
        results = await process_identifiers(identifiers)

        # INFO: Success
        logger.info(
            f"Batch ingestion completed",
            extra={
                "successful": len(results['success']),
                "failed": len(results['failed'])
            }
        )

    except InsufficientTokensError as e:
        # WARNING: Handled gracefully
        logger.warning(f"Token limit reached: {str(e)}")
        raise

    except Exception as e:
        # ERROR: Unhandled failure
        logger.error(
            f"Batch ingestion failed",
            extra={"error": str(e)},
            exc_info=True  # Include stack trace
        )
        raise
```

### 6. Type Hints & Pydantic

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal

# Pydantic models for validation
class ProductMetrics(BaseModel):
    """Product analysis metrics with validation."""

    asin: str = Field(..., min_length=10, max_length=10)
    roi_percentage: Decimal = Field(..., ge=0, le=1000)
    velocity_score: int = Field(..., ge=0, le=100)
    confidence_score: int = Field(..., ge=0, le=100)

    @validator('asin')
    def validate_asin(cls, v):
        """Ensure ASIN is alphanumeric."""
        if not v.isalnum():
            raise ValueError('ASIN must be alphanumeric')
        return v.upper()

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)  # JSON serialization
        }


# Type hints in functions
async def analyze_products(
    asins: List[str],
    config: Dict[str, Any]
) -> List[ProductMetrics]:
    """
    Analyze multiple products.

    Args:
        asins: List of Amazon ASINs
        config: Analysis configuration

    Returns:
        List of validated ProductMetrics objects
    """
    results: List[ProductMetrics] = []

    for asin in asins:
        metrics = await calculate_metrics(asin, config)
        # Pydantic validates automatically
        validated = ProductMetrics(**metrics)
        results.append(validated)

    return results
```

### 7. Async/Await Best Practices

```python
import asyncio
from typing import List

# Good: Concurrent execution with semaphore
async def process_batch_concurrent(asins: List[str], concurrency: int = 3):
    """Process ASINs concurrently with controlled parallelism."""

    semaphore = asyncio.Semaphore(concurrency)

    async def process_with_semaphore(asin: str):
        async with semaphore:
            return await process_asin(asin)

    # Execute all concurrently, max 3 at a time
    results = await asyncio.gather(
        *[process_with_semaphore(asin) for asin in asins],
        return_exceptions=True  # Don't fail entire batch on one error
    )

    return results


# Bad: Sequential processing (slow)
async def process_batch_sequential(asins: List[str]):
    """DON'T DO THIS - processes one at a time."""
    results = []
    for asin in asins:
        result = await process_asin(asin)  # Waits for each
        results.append(result)
    return results


# Good: Timeout protection
async def fetch_with_timeout(url: str, timeout: int = 30):
    """Fetch with timeout to prevent hanging."""
    try:
        async with asyncio.timeout(timeout):
            response = await httpx.get(url)
            return response.json()
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {url}")
        raise
```

---

## 📚 Références Additionnelles

### Documentation Interne

- `backend/docs/AUTOSOURCING_SAFEGUARDS.md` - Safeguards Phase 7.0
- `backend/docs/audits/` - Audits Phase 1-3
- `.claude/CLAUDE.md` - Instructions développement

### API Externes

- **Keepa API**: https://keepa.com/#!api
- **Keepa Product.java**: https://github.com/keepacom/api_backend

### FastAPI & SQLAlchemy

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pydantic V2**: https://docs.pydantic.dev/latest/

---

## 🔄 Changelog Architecture

### v1.0.0 - 28 Novembre 2025 (Refactoring SRP)

**Modules créés**:
- `keepa_schemas.py` (156 LOC) - Pydantic models
- `keepa_utils.py` (160 LOC) - Utility functions
- `keepa_debug.py` (380 LOC) - Debug endpoints
- `keepa_models.py` (118 LOC) - Data classes
- `keepa_cache.py` (152 LOC) - Cache management
- `keepa_throttle.py` (171 LOC) - Rate limiting

**Refactored**:
- `keepa.py` - Router facade (379 LOC)
- `keepa_service.py` - Service facade (668 LOC)

**Patterns ajoutés**:
- Facade Pattern (API & Service)
- Token Bucket Algorithm
- Multi-tier Caching

**Total LOC**: ~2,184 LOC (Keepa integration)

---

**Auteur**: Documentation générée par Claude Code
**Contact**: Voir `.claude/CLAUDE.md` pour instructions projet
**License**: Proprietary - ArbitrageVault
