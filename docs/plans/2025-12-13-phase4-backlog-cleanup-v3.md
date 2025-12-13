# Phase 4 - Backlog Cleanup Implementation Plan (v3)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **IMPORTANT:** Chaque tache inclut des checkpoints OBLIGATOIRES. Ne pas sauter d'etapes.

**Goal:** Nettoyer le backlog technique en resolvant 5 issues identifiees (I3-I7), consolidant l'architecture routers, et supprimant les placeholders.

**Architecture:** Approche bottom-up - d'abord les fixes simples (I6), puis placeholders (I3, I5), async (I4), et enfin consolidation routers (I7) qui est le plus risque.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, React/TypeScript, PostgreSQL, pytest

---

## Statut des Issues

| ID | Description | Effort | Statut |
|----|-------------|--------|--------|
| I6 | Frontend Toggle manquant | 15 min | COMPLETE |
| I3 | Config Stats placeholders | 1h | COMPLETE |
| I5 | Strategic Views placeholders | 2h | COMPLETE |
| I4 | Async Job non-persistant | 2h | A FAIRE |
| I7 | Router Architecture dupliquee | 4-6h | A FAIRE |

**Effort Restant:** 6-8 heures

---

## Task 4: Implement Async Job Persistence (I4)

### Pre-Implementation Checkpoints

#### Checkpoint 4.1: Context7-First
- [ ] Consulter doc SQLAlchemy 2.0 async sessions
- [ ] Consulter doc FastAPI background tasks
- [ ] Noter les patterns recommandes

**Commande Context7:**
```
mcp__context7__get-library-docs avec context7CompatibleLibraryID="/sqlalchemy/sqlalchemy" topic="async session"
```

#### Checkpoint 4.2: TDD - Ecrire les tests AVANT
- [ ] Creer `backend/tests/api/test_async_job_persistence.py`
- [ ] Test: `test_async_job_creates_db_record`
- [ ] Test: `test_async_job_updates_status`
- [ ] Test: `test_async_job_stores_results`
- [ ] Verifier que les tests FAIL (pas encore implemente)

**Fichier test a creer:**
```python
# backend/tests/api/test_async_job_persistence.py
import pytest
from app.models.autosourcing import AutoSourcingJob, JobStatus

@pytest.mark.asyncio
async def test_async_job_creates_db_record(db_session):
    """Async batch processing should create a job record in database."""
    from app.api.v1.routers.keepa_debug import create_async_job

    job = await create_async_job(
        db=db_session,
        profile_name="test_profile",
        identifiers=["B001", "B002"],
        config={"test": True}
    )

    assert job.id is not None
    assert job.status == JobStatus.PENDING
    assert job.profile_name == "test_profile"


@pytest.mark.asyncio
async def test_async_job_updates_status(db_session):
    """Job status should update during processing."""
    from app.api.v1.routers.keepa_debug import create_async_job, update_job_status

    job = await create_async_job(
        db=db_session,
        profile_name="test",
        identifiers=["B001"],
        config={}
    )

    await update_job_status(db_session, job.id, JobStatus.RUNNING)
    await db_session.refresh(job)
    assert job.status == JobStatus.RUNNING
```

### Implementation

#### Step 4.3: Modifier keepa_debug.py
- [ ] Ajouter imports necessaires
- [ ] Implementer `create_async_job()`
- [ ] Implementer `update_job_status()`
- [ ] Modifier `process_batch_async()` pour persister

**Fichiers:**
- Modify: `backend/app/api/v1/routers/keepa_debug.py:207-251`
- Use: `backend/app/models/autosourcing.py` (AutoSourcingJob model)

### Post-Implementation Checkpoints

#### Checkpoint 4.4: Tests passent
- [ ] `pytest tests/api/test_async_job_persistence.py -v`
- [ ] Tous les tests PASS

#### Checkpoint 4.5: Hostile Code Review
- [ ] Edge case: job_id None ou invalide?
- [ ] Edge case: db_session ferme pendant update?
- [ ] Edge case: identifiers liste vide?
- [ ] Error handling: Exception pendant processing?
- [ ] Pas de secrets hardcodes?

#### Checkpoint 4.6: Verification finale
- [ ] Invoquer skill `verification-before-completion`
- [ ] Fournir preuve des tests

---

## Task 5: Consolidate Router Architecture (I7)

> **ATTENTION:** Cette tache est la plus risquee. Proceder avec prudence.

### Pre-Implementation Checkpoints

#### Checkpoint 5.1: Context7-First
- [ ] Consulter doc FastAPI routers et include_router
- [ ] Consulter patterns de structuration d'API

#### Checkpoint 5.2: Documenter l'etat actuel
- [ ] Lister tous les routers dans `backend/app/main.py`
- [ ] Lister tous les routers dans `backend/app/routers/`
- [ ] Lister tous les routers dans `backend/app/api/v1/routers/`
- [ ] Lister tous les endpoints dans `backend/app/api/v1/endpoints/`
- [ ] Identifier les duplications

#### Checkpoint 5.3: TDD - Test de regression
- [ ] Creer `backend/tests/test_routes_regression.py`
- [ ] Lister TOUTES les routes attendues
- [ ] Verifier que le test PASS avant migration

**Fichier test a creer:**
```python
# backend/tests/test_routes_regression.py
import pytest
from httpx import AsyncClient

EXPECTED_ROUTES = [
    "/api/v1/health",
    "/api/v1/config",
    "/api/v1/config/stats",
    "/api/v1/products",
    "/api/v1/niches",
    "/api/v1/views",
    "/api/v1/bookmarks",
    "/api/v1/analyses",
    "/api/v1/batches",
    # Ajouter toutes les routes
]

@pytest.mark.asyncio
async def test_all_routes_accessible(client: AsyncClient):
    """Verify all expected routes are accessible after consolidation."""
    for route in EXPECTED_ROUTES:
        response = await client.options(route)
        assert response.status_code in [200, 204, 405], f"Route {route} not accessible"
```

### Implementation

#### Step 5.4: Migration incrementale
Pour chaque fichier dans `backend/app/routers/`:

1. [ ] Copier vers `backend/app/api/v1/routers/`
2. [ ] Mettre a jour les imports
3. [ ] Mettre a jour `main.py`
4. [ ] Executer tests de regression
5. [ ] Si OK, supprimer l'ancien fichier

**Ordre de migration:**
1. `bookmarks.py`
2. `strategic_views.py`
3. `stock_estimate.py`
4. `niche_discovery.py`

#### Step 5.5: Consolider endpoints redondants
- [ ] Comparer `endpoints/config.py` vs `routers/config.py`
- [ ] Merger le code unique
- [ ] Supprimer fichiers redondants

#### Step 5.6: Nettoyer main.py
- [ ] Un seul chemin d'import: `app.api.v1.routers`
- [ ] Supprimer imports de `app.routers`
- [ ] Supprimer imports de `app.api.v1.endpoints`

### Post-Implementation Checkpoints

#### Checkpoint 5.7: Tests passent
- [ ] `pytest tests/ -v --tb=short`
- [ ] Tous les 514+ tests PASS

#### Checkpoint 5.8: Test manuel routes critiques
- [ ] GET /api/v1/health
- [ ] GET /api/v1/config/stats
- [ ] GET /api/v1/products (avec ASIN test)

#### Checkpoint 5.9: Hostile Code Review
- [ ] Routes cassees?
- [ ] Imports circulaires?
- [ ] Prefixes dupliques?

#### Checkpoint 5.10: Verification finale
- [ ] Invoquer skill `verification-before-completion`
- [ ] Fournir preuve des tests

---

## Task 6: Final Validation

### Checkpoint 6.1: Suite de tests complete
```bash
cd backend && pytest tests/ -v --tb=short
```
Expected: 514+ tests pass, 0 failures

### Checkpoint 6.2: Build frontend
```bash
cd frontend && npm run build
```
Expected: Build succeeds, 0 errors

### Checkpoint 6.3: Type check
```bash
cd frontend && npm run type-check
```
Expected: 0 type errors

### Checkpoint 6.4: Verification croisee
- [ ] Tous les placeholders supprimes
- [ ] Async jobs persistent en DB
- [ ] Architecture routers unifiee
- [ ] Frontend toggle fonctionne
- [ ] Tests passent avec vraies donnees

### Checkpoint 6.5: Commit final
- [ ] Invoquer skill `verification-before-completion`
- [ ] Hostile Code Review fait
- [ ] Preuves documentees
- [ ] Commit avec message descriptif

---

## Commits Suggeres

1. `feat(async): add job persistence for batch processing (I4)`
2. `refactor(routers): consolidate router architecture (I7)`
3. `chore: cleanup obsolete endpoints directory`

---

## Workflow Obligatoire par Tache

```
1. Context7-First     -> Consulter documentation
2. TDD                -> Ecrire tests (doivent FAIL)
3. Implementation     -> Ecrire le code
4. Tests              -> Verifier que tests PASS
5. Hostile Review     -> Chercher les bugs
6. Verification       -> Skill verification-before-completion
7. Commit             -> Seulement apres validation
```

**Plan complete. Effort restant: 6-8 heures.**
