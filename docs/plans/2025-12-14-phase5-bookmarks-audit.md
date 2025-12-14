# Phase 5 - Niche Bookmarks Audit & Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Auditer la Phase 5 Bookmarks existante, creer les tests manquants, et valider le flux E2E avec Playwright.

**Architecture:** Le systeme de bookmarks permet aux utilisateurs de sauvegarder des niches decouvertes pour re-analyse ulterieure. Backend CRUD (FastAPI + SQLAlchemy) + Frontend React Query hooks.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic V2, React, TypeScript, Playwright

---

## Pre-Requis CLAUDE.md

Avant chaque tache, respecter le workflow Zero-Tolerance Engineering :

1. **Context7-First** : Verifier documentation officielle si API externe
2. **TDD** : Ecrire test AVANT implementation
3. **Hostile Review** : Chercher edge cases avant commit
4. **verification-before-completion** : Invoquer skill avant de dire "termine"

---

## Evaluation Playwright

**Verdict : OUI - Playwright necessaire**

| Critere | Evaluation |
|---------|------------|
| Flux utilisateur complet | OUI - Create/List/Update/Delete niches |
| Interaction complexe | OUI - Formulaires, modals, pagination |
| Validation visuelle | OUI - Liste niches, etats vides |

**Tests Playwright recommandes :**
1. Test flux creation bookmark depuis NicheDiscovery
2. Test affichage liste bookmarks (page MesNiches)
3. Test suppression bookmark avec confirmation
4. Test "Relancer analyse" avec force_refresh

---

## Task 1: Backend Unit Tests - BookmarkService

**Files:**
- Create: backend/tests/services/test_bookmark_service.py
- Reference: backend/app/services/bookmark_service.py

**Objectif:** 12 tests unitaires couvrant CRUD + edge cases

**Tests a implementer:**
- test_create_niche_success
- test_create_niche_duplicate_name_raises_409
- test_get_niche_by_id_found
- test_get_niche_by_id_not_found
- test_list_niches_returns_paginated
- test_update_niche_success
- test_update_niche_not_found_raises_404
- test_delete_niche_success
- test_delete_niche_not_found_returns_false
- test_get_filters_returns_dict
- test_get_filters_returns_none_when_not_found

**Commit:** test(phase5): add unit tests for BookmarkService

---

## Task 2: Backend API Integration Tests

**Files:**
- Create: backend/tests/api/test_bookmarks_api.py
- Reference: backend/app/api/v1/routers/bookmarks.py

**Objectif:** Tests integration HTTP pour tous les endpoints

**Tests a implementer:**
- test_create_bookmark_requires_auth (401)
- test_create_bookmark_validates_name_required (422)
- test_list_bookmarks_requires_auth (401)
- test_list_bookmarks_returns_empty_list (200)
- test_get_bookmark_not_found (404)
- test_update_bookmark_not_found (404)
- test_delete_bookmark_not_found (404)
- test_get_filters_not_found (404)

**Commit:** test(phase5): add API integration tests for bookmarks

---

## Task 3: Hostile Code Review

**Files a reviewer:**
- backend/app/api/v1/routers/bookmarks.py
- backend/app/services/bookmark_service.py
- backend/app/schemas/bookmark.py

**Checklist:**
- [ ] Types stricts (pas de Any sans raison)
- [ ] Error handling complet (try/except + rollback)
- [ ] Input validation (Pydantic validators)
- [ ] Auth sur tous endpoints (Depends(get_current_user_id))
- [ ] Pas de SQL injection (queries parametrees)
- [ ] Empty string handling (strip())

**Commit:** fix(phase5): address hostile review findings (si bugs trouves)

---

## Task 4: Playwright E2E Tests

**Files:**
- Create: frontend/tests/e2e/bookmarks.spec.ts
- Reference: frontend/src/pages/MesNiches.tsx

**Tests Playwright:**
1. should display empty state when no bookmarks
2. should navigate to niche discovery from empty state
3. should save a niche from discovery results
4. should list saved bookmarks
5. should delete a bookmark with confirmation
6. should re-run analysis from saved bookmark

**Pre-requis:** Backend running + User authentifie

**Commit:** test(phase5): add Playwright E2E tests for bookmarks

---

## Task 5: Verification & Checkpoint

**Actions:**
1. Executer tous les tests:
   - pytest tests/services/test_bookmark_service.py -v
   - pytest tests/api/test_bookmarks_api.py -v
   - npx playwright test bookmarks.spec.ts

2. Invoquer skill verification-before-completion

3. Creer checkpoint_validated.json

**Commit:** feat(phase5): complete bookmarks audit with tests

---

## Task 6: Update Memory Files

**Files:**
- Update: .claude/compact_current.md
- Update: .claude/compact_master.md

**Changements:**
- Phase 5 Status: DEPLOYE -> AUDITE
- Tests ajoutes: X unit + Y integration + Z E2E
- Date audit: 14 Dec 2025

**Commit:** docs: update memory files after Phase 5 audit

---

## Summary

| Task | Description | Estimated Time |
|------|-------------|----------------|
| Task 1 | Backend Unit Tests | 15 min |
| Task 2 | Backend API Tests | 15 min |
| Task 3 | Hostile Code Review | 10 min |
| Task 4 | Playwright E2E Tests | 20 min |
| Task 5 | Verification & Checkpoint | 10 min |
| Task 6 | Update Memory Files | 5 min |
| **Total** | | **~75 min** |
