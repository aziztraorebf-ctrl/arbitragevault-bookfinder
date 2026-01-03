# Phase 10 Optimisee - Unified Product Table (Cleanup)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finaliser Phase 10 en supprimant les pages redondantes (AnalyseStrategique, StockEstimates) et nettoyer le code.

**Architecture:** Tasks 1-3 de Phase 10 sont DEJA COMPLETES. Ce plan couvre uniquement Task 4 (suppression) et Task 5 (verification). Les composants UnifiedProductTable, types unified, et integration dans les 3 modules sont deja en place.

**Tech Stack:** React, TypeScript, Vite

**Etat Actuel (deja fait):**
- [x] Task 1: Types `DisplayableProduct` + normalisation (`frontend/src/types/unified.ts`)
- [x] Task 2: `UnifiedProductTable` composant (`frontend/src/components/unified/`)
- [x] Task 3: Integration 3 modules (NicheDiscovery, AnalyseManuelle, AutoSourcing utilisent `UnifiedProductTable`)

**Ce qui reste:**
- [ ] Task 4: Suppression pages AnalyseStrategique et StockEstimates
- [ ] Task 5: Verification finale

---

## Task 1: Supprimer routes dans App.tsx

**Files:**
- Modify: `frontend/src/App.tsx:13-14,40-41`

**Step 1: Read current App.tsx**

Run: Lire le fichier pour voir le contexte exact

**Step 2: Remove imports and routes**

Supprimer les lignes suivantes de `frontend/src/App.tsx`:

```typescript
// SUPPRIMER ces imports (lignes 13-14):
import AnalyseStrategique from './pages/AnalyseStrategique'
import StockEstimates from './pages/StockEstimates'

// SUPPRIMER ces routes (lignes 40-41):
<Route path="/analyse-strategique" element={<AnalyseStrategique />} />
<Route path="/stock-estimates" element={<StockEstimates />} />
```

**Step 3: Run build to verify no errors**

Run: `cd frontend && npm run build`
Expected: SUCCESS (no TypeScript errors about missing imports)

**Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "chore(phase10): remove AnalyseStrategique and StockEstimates routes

Routes removed as these pages are redundant per external validation.
Strategic signals integrated into UnifiedProductTable.

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Supprimer liens navigation dans Layout.tsx

**Files:**
- Modify: `frontend/src/components/Layout/Layout.tsx:17-18`

**Step 1: Read current Layout.tsx**

Run: Lire le fichier pour voir le contexte exact des NAV_ITEMS

**Step 2: Remove nav items**

Supprimer les lignes suivantes du tableau NAV_ITEMS:

```typescript
// SUPPRIMER ces lignes (17-18):
{ name: 'Analyse Strategique', emoji: 'chart', href: '/analyse-strategique' },
{ name: 'Stock Estimates', emoji: 'package', href: '/stock-estimates' },
```

**Step 3: Run build to verify**

Run: `cd frontend && npm run build`
Expected: SUCCESS

**Step 4: Commit**

```bash
git add frontend/src/components/Layout/Layout.tsx
git commit -m "chore(phase10): remove redundant nav links from Layout

Removed Analyse Strategique and Stock Estimates from navigation.

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Supprimer les fichiers de pages

**Files:**
- Delete: `frontend/src/pages/AnalyseStrategique.tsx`
- Delete: `frontend/src/pages/StockEstimates.tsx`

**Step 1: Delete page files**

```bash
rm frontend/src/pages/AnalyseStrategique.tsx
rm frontend/src/pages/StockEstimates.tsx
```

**Step 2: Run build to verify**

Run: `cd frontend && npm run build`
Expected: SUCCESS (routes already removed, so no missing imports)

**Step 3: Commit**

```bash
git add -A
git commit -m "chore(phase10): delete redundant page files

Deleted:
- AnalyseStrategique.tsx
- StockEstimates.tsx

These pages were identified as breaking the natural decision flow.
Strategic signals are now integrated into UnifiedProductTable.

BREAKING CHANGE: /analyse-strategique and /stock-estimates URLs no longer exist.

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Supprimer les tests associes (si existants)

**Files:**
- Delete: `frontend/src/pages/__tests__/AnalyseStrategique.test.tsx` (if exists)
- Delete: `frontend/src/pages/__tests__/StockEstimates.test.tsx` (if exists)

**Step 1: Check if test files exist**

```bash
ls frontend/src/pages/__tests__/AnalyseStrategique.test.tsx 2>/dev/null && echo "EXISTS" || echo "NOT FOUND"
ls frontend/src/pages/__tests__/StockEstimates.test.tsx 2>/dev/null && echo "EXISTS" || echo "NOT FOUND"
```

**Step 2: Delete if they exist**

```bash
rm -f frontend/src/pages/__tests__/AnalyseStrategique.test.tsx
rm -f frontend/src/pages/__tests__/StockEstimates.test.tsx
```

**Step 3: Commit if files were deleted**

```bash
git add -A
git commit -m "chore(phase10): remove tests for deleted pages

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Supprimer hooks associes (si non utilises ailleurs)

**Files:**
- Check: `frontend/src/hooks/useStrategicViews.ts`
- Check: `frontend/src/hooks/useStockEstimate.ts`
- Check: `frontend/src/types/strategic.ts`

**Step 1: Check if hooks are used elsewhere**

```bash
cd frontend/src && grep -r "useStrategicView\|useStockEstimate" --include="*.tsx" --include="*.ts" | grep -v "hooks/" | grep -v "__tests__"
```

Si aucun resultat: les hooks ne sont utilises que par les pages supprimees.

**Step 2: Decision**

- Si hooks utilises ailleurs: GARDER
- Si hooks non utilises: Marquer comme @deprecated (garder pour Phase 11 potentiellement)

**Note:** Ne pas supprimer les hooks pour l'instant. Ils pourraient etre utiles pour Phase 11 ou futures features. Ajouter un commentaire @deprecated si desire.

---

## Task 6: Verification finale

**Step 1: Run full build**

```bash
cd frontend && npm run build
```

Expected: SUCCESS avec 0 erreurs TypeScript

**Step 2: Run tests**

```bash
cd frontend && npm run test
```

Expected: Tous les tests passent (tests des pages supprimees devraient etre gone aussi)

**Step 3: Start dev server and verify navigation**

```bash
cd frontend && npm run dev
```

Verification manuelle:
1. Ouvrir http://localhost:5173
2. Verifier que le menu ne contient plus "Analyse Strategique" et "Stock Estimates"
3. Verifier que /analyse-strategique et /stock-estimates retournent 404 (ou redirect)
4. Verifier que NicheDiscovery, AnalyseManuelle, AutoSourcing fonctionnent toujours

**Step 4: E2E Quick Test (optionnel)**

Lancer les tests E2E existants pour verifier que rien n'est casse.

**Step 5: Commit final (si pas deja fait)**

Si tous les commits precedents sont faits, pas de commit supplementaire necessaire.

---

## Summary

| Task | Description | Effort |
|------|-------------|--------|
| Task 1 | Supprimer routes App.tsx | 5 min |
| Task 2 | Supprimer nav links Layout.tsx | 5 min |
| Task 3 | Supprimer fichiers pages | 5 min |
| Task 4 | Supprimer tests associes | 5 min |
| Task 5 | Verifier hooks (garder pour l'instant) | 5 min |
| Task 6 | Verification finale | 15 min |
| **Total** | | **~40 min** |

---

## Post-Completion

Apres Phase 10:
1. Mettre a jour `compact_current.md` avec status Phase 10 COMPLETE
2. Preparer plan Phase 11 (Page Centrale Recherches)
