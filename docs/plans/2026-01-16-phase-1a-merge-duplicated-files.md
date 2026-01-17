# Phase 1A: Merge Duplicated Files - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminer les fichiers dupliques dans le codebase pour reduire la confusion et les bugs potentiels.

**Architecture:** Consolider les fichiers dupliques en gardant la version la plus complete/recente, puis mettre a jour tous les imports. Approche conservative avec tests a chaque etape.

**Tech Stack:** TypeScript (frontend), Python (backend), pytest, npm

---

## Sommaire des Duplications Identifiees

| # | Fichier A (GARDER) | Fichier B (SUPPRIMER) | Raison |
|---|-------------------|----------------------|--------|
| 1 | `components/accordions/AccordionContent.tsx` | `components/unified/AccordionContent.tsx` | Version accordions plus complete (Phase 5 features) |
| 2 | `services/keepa_constants.py` | `utils/keepa_constants.py` | Version services plus complete (KeepaCSVType enum) |
| 3 | `services/keepa_service.py::get_keepa_service` | `services/keepa_service_factory.py` | Factory entiere redondante |
| 4 | `api/v1/routers/config.py` | `api/v1/endpoints/config.py` | Routers utilise BusinessConfigService (actif), endpoints utilise ConfigService (legacy) |

---

## Task 1: Merger keepa_constants.py (Backend)

**Files:**
- Keep: `backend/app/services/keepa_constants.py`
- Delete: `backend/app/utils/keepa_constants.py`
- Modify: `backend/app/utils/keepa_utils.py:302,338`
- Test: `backend/tests/unit/test_keepa_constants.py`

**Step 1.1: Creer le test unitaire pour keepa_constants**

```python
# backend/tests/unit/test_keepa_constants.py
"""
Unit tests for Keepa constants - ensures all required constants are exported.
"""
import pytest


class TestKeepaConstants:
    """Test suite for keepa_constants module."""

    def test_keepa_csv_type_enum_exists(self):
        """Verify KeepaCSVType enum is importable from services."""
        from app.services.keepa_constants import KeepaCSVType

        assert KeepaCSVType.AMAZON == 0
        assert KeepaCSVType.NEW == 1
        assert KeepaCSVType.USED == 2
        assert KeepaCSVType.SALES == 3
        assert KeepaCSVType.NEW_FBA == 10

    def test_keepa_time_constants_exist(self):
        """Verify time conversion constants are available."""
        from app.services.keepa_constants import (
            KEEPA_TIME_OFFSET_MINUTES,
            KEEPA_NULL_VALUE,
            KEEPA_PRICE_DIVISOR
        )

        assert KEEPA_TIME_OFFSET_MINUTES == 21564000
        assert KEEPA_NULL_VALUE == -1
        assert KEEPA_PRICE_DIVISOR == 100

    def test_condition_codes_exist(self):
        """Verify condition codes are defined."""
        from app.services.keepa_constants import (
            KEEPA_CONDITION_CODES,
            DEFAULT_CONDITIONS,
            ALL_CONDITION_KEYS
        )

        assert 1 in KEEPA_CONDITION_CODES
        assert KEEPA_CONDITION_CODES[1][0] == 'new'
        assert 'new' in DEFAULT_CONDITIONS
        assert 'acceptable' in ALL_CONDITION_KEYS

    def test_all_exports_defined(self):
        """Verify __all__ includes all required exports."""
        from app.services import keepa_constants

        expected_exports = [
            'KeepaCSVType',
            'KEEPA_CONDITION_CODES',
            'DEFAULT_CONDITIONS',
            'ALL_CONDITION_KEYS',
            'KEEPA_TIME_OFFSET_MINUTES',
            'KEEPA_NULL_VALUE',
            'KEEPA_PRICE_DIVISOR'
        ]

        for export in expected_exports:
            assert hasattr(keepa_constants, export), f"Missing export: {export}"
```

**Step 1.2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_keepa_constants.py -v`
Expected: FAIL - `KEEPA_TIME_OFFSET_MINUTES` not found in services/keepa_constants.py

**Step 1.3: Merger les constantes dans services/keepa_constants.py**

Ajouter les constantes de utils/keepa_constants.py dans services/keepa_constants.py:

```python
# backend/app/services/keepa_constants.py
"""
Keepa API Constants and Enumerations
=====================================
Official CSV type indices from Keepa Java API.

Source: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java
Keepa Support Email (October 15, 2025)
"""

from enum import IntEnum


class KeepaCSVType(IntEnum):
    """
    Official Keepa CSV Type indices from Java API.
    Source: https://github.com/keepacom/api_backend/blob/master/src/main/java/com/keepa/api/backend/structs/Product.java
    """
    AMAZON = 0              # Amazon price
    NEW = 1                 # Marketplace New price (includes Amazon)
    USED = 2                # Used price
    SALES = 3               # Sales Rank (BSR) - INTEGER not price!
    LISTPRICE = 4           # List price
    COLLECTIBLE = 5         # Collectible price
    REFURBISHED = 6         # Refurbished price
    NEW_FBM_SHIPPING = 7    # FBM with shipping
    LIGHTNING_DEAL = 8      # Lightning deal price
    WAREHOUSE = 9           # Amazon Warehouse
    NEW_FBA = 10            # FBA price (3rd party only)
    COUNT_NEW = 11          # New offer count
    COUNT_USED = 12         # Used offer count
    COUNT_REFURBISHED = 13  # Refurbished count
    COUNT_COLLECTIBLE = 14  # Collectible count
    RATING = 15             # Product rating (0-50, e.g., 45 = 4.5 stars)
    COUNT_REVIEWS = 16      # Review count
    BUY_BOX_SHIPPING = 18   # Buy Box price with shipping


# ===============================================================================
# OFFICIAL KEEPA TIME CONVERSION
# ===============================================================================

# Official Keepa time offset (in minutes)
# Formula from Keepa Support: unix_seconds = (keepa_time + 21564000) * 60
#
# Example validation (from Keepa Support):
# keepa_time = 7777548
# -> (7777548 + 21564000) * 60 = 1760454880 seconds
# -> Oct 15 2025 01:48:00 UTC (03:48:00 GMT+0200)
KEEPA_TIME_OFFSET_MINUTES = 21564000

# Keepa null value indicator (used in arrays)
KEEPA_NULL_VALUE = -1

# Keepa price divisor (prices stored as integers, divide by 100 for dollars)
KEEPA_PRICE_DIVISOR = 100


# ===============================================================================
# CONDITION CODES
# ===============================================================================

# Keepa condition codes for offers
KEEPA_CONDITION_CODES = {
    1: ('new', 'New'),
    3: ('very_good', 'Used - Very Good'),
    4: ('good', 'Used - Good'),
    5: ('acceptable', 'Used - Acceptable')
}

# Default conditions for filtering (excludes 'acceptable' per user preference)
DEFAULT_CONDITIONS = ['new', 'very_good', 'good']

# All available condition keys
ALL_CONDITION_KEYS = ['new', 'very_good', 'good', 'acceptable']


__all__ = [
    'KeepaCSVType',
    'KEEPA_CONDITION_CODES',
    'DEFAULT_CONDITIONS',
    'ALL_CONDITION_KEYS',
    'KEEPA_TIME_OFFSET_MINUTES',
    'KEEPA_NULL_VALUE',
    'KEEPA_PRICE_DIVISOR'
]
```

**Step 1.4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_keepa_constants.py -v`
Expected: PASS (7 tests)

**Step 1.5: Mettre a jour les imports dans keepa_utils.py**

Modifier `backend/app/utils/keepa_utils.py` lignes 302 et 338:

```python
# Line 302 - Change from:
from app.utils.keepa_constants import KEEPA_TIME_OFFSET_MINUTES, KEEPA_NULL_VALUE
# To:
from app.services.keepa_constants import KEEPA_TIME_OFFSET_MINUTES, KEEPA_NULL_VALUE

# Line 338 - Change from:
from app.utils.keepa_constants import KEEPA_TIME_OFFSET_MINUTES
# To:
from app.services.keepa_constants import KEEPA_TIME_OFFSET_MINUTES
```

**Step 1.6: Supprimer utils/keepa_constants.py**

Run: `del backend\app\utils\keepa_constants.py` (Windows) ou `rm backend/app/utils/keepa_constants.py` (Unix)

**Step 1.7: Run all Keepa-related tests**

Run: `cd backend && python -m pytest tests/ -k "keepa" -v --tb=short`
Expected: All tests PASS

**Step 1.8: Commit**

```bash
git add backend/app/services/keepa_constants.py backend/app/utils/keepa_utils.py backend/tests/unit/test_keepa_constants.py
git rm backend/app/utils/keepa_constants.py
git commit -m "$(cat <<'EOF'
refactor(backend): merge keepa_constants into services module

- Consolidate utils/keepa_constants.py into services/keepa_constants.py
- Add time conversion constants (KEEPA_TIME_OFFSET_MINUTES, etc.)
- Update imports in keepa_utils.py
- Add unit tests for all constants

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Supprimer keepa_service_factory.py (Backend)

**Files:**
- Keep: `backend/app/services/keepa_service.py` (has `get_keepa_service`)
- Delete: `backend/app/services/keepa_service_factory.py`
- Modify: `backend/app/api/v1/routers/niche_discovery.py:21,32`
- Test: Existing tests

**Step 2.1: Verifier que get_keepa_service existe dans keepa_service.py**

Run: `cd backend && python -c "from app.services.keepa_service import get_keepa_service; print('OK')""`
Expected: `OK`

**Step 2.2: Mettre a jour niche_discovery.py imports**

Modifier `backend/app/api/v1/routers/niche_discovery.py`:

```python
# Line 21 - Change from:
from app.services.keepa_service_factory import get_keepa_service
# To:
from app.services.keepa_service import get_keepa_service, KeepaService
```

Note: Line 32 uses `get_keepa_service()` directly without await - verifier si c'est correct.

**Step 2.3: Verifier usage de get_keepa_service dans niche_discovery.py**

Lire ligne 32 de niche_discovery.py. Si `keepa_service = get_keepa_service()` sans `await`, corriger:

```python
# Line ~32 - Si necessaire, changer:
keepa_service = get_keepa_service()
# En:
keepa_service = await get_keepa_service()
```

**Step 2.4: Supprimer keepa_service_factory.py**

Run: `del backend\app\services\keepa_service_factory.py` (Windows)

**Step 2.5: Run tests for niche discovery**

Run: `cd backend && python -m pytest tests/ -k "niche" -v --tb=short`
Expected: All tests PASS

**Step 2.6: Commit**

```bash
git add backend/app/api/v1/routers/niche_discovery.py
git rm backend/app/services/keepa_service_factory.py
git commit -m "$(cat <<'EOF'
refactor(backend): remove redundant keepa_service_factory.py

- Delete keepa_service_factory.py (duplicate of keepa_service.get_keepa_service)
- Update niche_discovery.py to import from keepa_service
- Single source of truth for KeepaService instantiation

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Supprimer endpoints/config.py legacy (Backend)

**Files:**
- Keep: `backend/app/api/v1/routers/config.py` (BusinessConfigService)
- Delete: `backend/app/api/v1/endpoints/config.py` (ConfigService legacy)
- Verify: No active imports of endpoints/config.py

**Step 3.1: Verifier qu'aucun fichier n'importe endpoints/config.py**

Run: `cd backend && findstr /s /i "from app.api.v1.endpoints.config" *.py` (Windows)
ou `grep -r "from app.api.v1.endpoints.config" backend/app/` (Unix)
Expected: No results (or only the file itself)

**Step 3.2: Verifier le router registration dans main.py ou api.py**

Rechercher comment les routers sont enregistres:

Run: `cd backend && findstr /s "endpoints.config" app\*.py` (Windows)
Expected: Identifier si endpoints/config est monte quelque part

**Step 3.3: Si endpoints/config.py est monte, le decommenter/supprimer**

Dans le fichier d'enregistrement des routes (probablement `app/api/v1/__init__.py` ou `app/main.py`), supprimer la ligne qui monte endpoints/config.

**Step 3.4: Supprimer endpoints/config.py**

Run: `del backend\app\api\v1\endpoints\config.py` (Windows)

**Step 3.5: Run config-related tests**

Run: `cd backend && python -m pytest tests/ -k "config" -v --tb=short`
Expected: All tests PASS

**Step 3.6: Commit**

```bash
git rm backend/app/api/v1/endpoints/config.py
git commit -m "$(cat <<'EOF'
refactor(backend): remove legacy endpoints/config.py

- Delete endpoints/config.py (uses deprecated ConfigService)
- routers/config.py with BusinessConfigService is the active endpoint
- Eliminates dual config API confusion

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Merger AccordionContent.tsx (Frontend)

**Files:**
- Keep: `frontend/src/components/accordions/AccordionContent.tsx` (Phase 5 features)
- Delete: `frontend/src/components/unified/AccordionContent.tsx`
- Modify: `frontend/src/components/unified/index.ts`
- Modify: `frontend/src/pages/AnalyseManuelle.tsx:5`
- Test: npm run build

**Step 4.1: Analyser les differences entre les deux fichiers**

**accordions/AccordionContent.tsx** (GARDER):
- Import depuis `./types` (AccordionContentProps)
- Utilise RoiDetailsSection, VelocityDetailsSection, RecommendationSection
- Support Phase 5 ConditionBreakdown
- Animation CSS avec max-h transition

**unified/AccordionContent.tsx** (SUPPRIMER):
- Define AccordionContentProps inline
- Calculs manuels de profit
- Plus de details (Amazon status, Quick actions)
- Animation CSS slide-in

**Conclusion**: Les deux ont des features differentes. Il faut:
1. Garder accordions/AccordionContent.tsx (architecture modulaire)
2. Mettre a jour unified/index.ts pour re-exporter depuis accordions/

**Step 4.2: Mettre a jour unified/index.ts pour re-exporter**

Modifier `frontend/src/components/unified/index.ts`:

```typescript
// Re-export AccordionContent from accordions module (canonical source)
export { AccordionContent } from '../accordions/AccordionContent'
export type { AccordionContentProps } from '../accordions/types'
```

**Step 4.3: Supprimer unified/AccordionContent.tsx**

Run: `del frontend\src\components\unified\AccordionContent.tsx` (Windows)

**Step 4.4: Verifier que AnalyseManuelle.tsx compile**

Le fichier importe depuis `../components/unified` qui re-exporte maintenant depuis accordions.

Run: `cd frontend && npm run build`
Expected: Build SUCCESS

**Step 4.5: Run TypeScript type check**

Run: `cd frontend && npm run type-check` (ou `npx tsc --noEmit`)
Expected: No errors

**Step 4.6: Commit**

```bash
git add frontend/src/components/unified/index.ts
git rm frontend/src/components/unified/AccordionContent.tsx
git commit -m "$(cat <<'EOF'
refactor(frontend): consolidate AccordionContent to accordions module

- Remove duplicate unified/AccordionContent.tsx
- Re-export from accordions/ in unified/index.ts
- accordions/ version has Phase 5 ConditionBreakdown support
- Single source of truth for accordion components

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Supprimer autosourcing.py local get_keepa_service (Backend)

**Files:**
- Modify: `backend/app/api/v1/routers/autosourcing.py:144`
- Test: Existing autosourcing tests

**Step 5.1: Identifier la fonction locale dans autosourcing.py**

Line 144 definit localement:
```python
async def get_keepa_service() -> KeepaService:
    ...
```

Cette fonction duplique celle de `app.services.keepa_service`.

**Step 5.2: Remplacer par import depuis keepa_service**

Modifier `backend/app/api/v1/routers/autosourcing.py`:

```python
# Au debut du fichier, ajouter/modifier l'import:
from app.services.keepa_service import KeepaService, get_keepa_service

# Supprimer la definition locale de get_keepa_service (lignes ~144-155)
```

**Step 5.3: Run autosourcing tests**

Run: `cd backend && python -m pytest tests/ -k "autosourcing" -v --tb=short`
Expected: All tests PASS

**Step 5.4: Commit**

```bash
git add backend/app/api/v1/routers/autosourcing.py
git commit -m "$(cat <<'EOF'
refactor(backend): remove local get_keepa_service from autosourcing

- Import get_keepa_service from services.keepa_service
- Remove duplicate local definition
- Consistent service instantiation across all routers

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Verification Finale et Tests Complets

**Step 6.1: Run backend full test suite**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 6.2: Run frontend build**

Run: `cd frontend && npm run build`
Expected: Build SUCCESS

**Step 6.3: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 6.4: Verifier qu'il n'y a plus de duplications**

Run searches to confirm:
```bash
# Verifier pas de utils/keepa_constants.py
dir backend\app\utils\keepa_constants.py 2>nul || echo "OK: File deleted"

# Verifier pas de keepa_service_factory.py
dir backend\app\services\keepa_service_factory.py 2>nul || echo "OK: File deleted"

# Verifier pas de endpoints/config.py
dir backend\app\api\v1\endpoints\config.py 2>nul || echo "OK: File deleted"

# Verifier pas de unified/AccordionContent.tsx
dir frontend\src\components\unified\AccordionContent.tsx 2>nul || echo "OK: File deleted"
```

**Step 6.5: Final commit (si necessaire)**

Si des ajustements ont ete faits:

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore: Phase 1A complete - all duplications removed

Merged files:
- keepa_constants.py (services/ is canonical)
- get_keepa_service (keepa_service.py is canonical)
- config.py (routers/ with BusinessConfigService is canonical)
- AccordionContent.tsx (accordions/ is canonical)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Checklist de Completion

| # | Task | Status |
|---|------|--------|
| 1 | Merger keepa_constants.py | [ ] |
| 2 | Supprimer keepa_service_factory.py | [ ] |
| 3 | Supprimer endpoints/config.py | [ ] |
| 4 | Merger AccordionContent.tsx | [ ] |
| 5 | Supprimer local get_keepa_service autosourcing | [ ] |
| 6 | Tests complets backend | [ ] |
| 7 | Build frontend | [ ] |
| 8 | Type check frontend | [ ] |

---

## Risques et Mitigations

| Risque | Mitigation |
|--------|-----------|
| Import casse apres suppression | Tests a chaque etape, commits atomiques |
| ConfigService encore utilise ailleurs | Search global avant suppression |
| AccordionContent features manquantes | Analyser differences avant merge |
| get_keepa_service signature differente | Verifier async/await compatibilite |

---

## Post-Phase 1A

Apres completion, les fichiers suivants seront les sources de verite:
- `backend/app/services/keepa_constants.py` - Toutes les constantes Keepa
- `backend/app/services/keepa_service.py` - Service et factory
- `backend/app/api/v1/routers/config.py` - Config API avec BusinessConfigService
- `frontend/src/components/accordions/AccordionContent.tsx` - Accordion UI
