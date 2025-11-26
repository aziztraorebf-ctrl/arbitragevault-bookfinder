# Niche Bookmarks Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement user flow to save discovered niches, view saved niches, and re-run analysis with fresh Keepa data.

**Architecture:** MVP incremental approach with backend validation first, then frontend integration using React Query hooks for API communication. Backend bookmarks endpoints already exist but untested.

**Tech Stack:** FastAPI (backend), React 18 + TypeScript (frontend), React Query (data fetching), Tailwind CSS (styling)

---

## Task 1: Validate Backend Bookmarks Endpoints

**Goal:** Test all `/api/v1/bookmarks/niches` endpoints to verify they work correctly before frontend integration.

**Files:**
- Test: `backend/scripts/test_bookmarks_api.py` (create new)
- Reference: `backend/app/api/v1/bookmarks.py` (existing)

**Step 1: Write test script for bookmarks CRUD**

Create `backend/scripts/test_bookmarks_api.py`:

```python
"""
Test script for Niche Bookmarks API endpoints
Phase 5 - Validate backend before frontend integration
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "https://arbitragevault-backend-v2.onrender.com"

async def test_bookmarks_flow():
    """Test complete CRUD flow for niche bookmarks."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing Niche Bookmarks API Flow\n")

        # Test 1: Create a bookmark
        print("1. Creating bookmark...")
        create_payload = {
            "niche_name": "Test Niche - Python Books",
            "category_id": 3617,
            "category_name": "Programming Books",
            "description": "Testing bookmark creation",
            "filters": {
                "bsr_range": [10000, 50000],
                "price_range": [15, 40],
                "min_roi": 30
            },
            "last_score": 85.5
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/bookmarks/niches",
            json=create_payload
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        bookmark = response.json()
        bookmark_id = bookmark["id"]
        print(f"   SUCCESS: Bookmark created with ID {bookmark_id}")
        print(f"   Data: {json.dumps(bookmark, indent=2)}\n")

        # Test 2: List all bookmarks
        print("2. Listing all bookmarks...")
        response = await client.get(f"{BASE_URL}/api/v1/bookmarks/niches")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "niches" in data, "Response missing 'niches' field"
        assert len(data["niches"]) > 0, "Should have at least 1 bookmark"
        print(f"   SUCCESS: Found {len(data['niches'])} bookmark(s)\n")

        # Test 3: Get specific bookmark
        print(f"3. Getting bookmark {bookmark_id}...")
        response = await client.get(
            f"{BASE_URL}/api/v1/bookmarks/niches/{bookmark_id}"
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        retrieved = response.json()
        assert retrieved["id"] == bookmark_id
        assert retrieved["niche_name"] == create_payload["niche_name"]
        print(f"   SUCCESS: Retrieved bookmark matches created data\n")

        # Test 4: Get filters for re-run analysis
        print(f"4. Getting filters for bookmark {bookmark_id}...")
        response = await client.get(
            f"{BASE_URL}/api/v1/bookmarks/niches/{bookmark_id}/filters"
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        filters = response.json()
        assert "filters" in filters, "Response missing 'filters' field"
        assert filters["filters"] == create_payload["filters"]
        print(f"   SUCCESS: Filters retrieved: {json.dumps(filters['filters'], indent=2)}\n")

        # Test 5: Update bookmark
        print(f"5. Updating bookmark {bookmark_id}...")
        update_payload = {
            "description": "Updated description - tested",
            "niche_name": "Updated Test Niche"
        }

        response = await client.put(
            f"{BASE_URL}/api/v1/bookmarks/niches/{bookmark_id}",
            json=update_payload
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        updated = response.json()
        assert updated["description"] == update_payload["description"]
        assert updated["niche_name"] == update_payload["niche_name"]
        print(f"   SUCCESS: Bookmark updated\n")

        # Test 6: Delete bookmark
        print(f"6. Deleting bookmark {bookmark_id}...")
        response = await client.delete(
            f"{BASE_URL}/api/v1/bookmarks/niches/{bookmark_id}"
        )

        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
        print(f"   SUCCESS: Bookmark deleted\n")

        # Test 7: Verify deletion
        print(f"7. Verifying deletion...")
        response = await client.get(
            f"{BASE_URL}/api/v1/bookmarks/niches/{bookmark_id}"
        )

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"   SUCCESS: Bookmark not found (correctly deleted)\n")

        print("ALL TESTS PASSED")

if __name__ == "__main__":
    asyncio.run(test_bookmarks_flow())
```

**Step 2: Run validation tests**

Run: `cd backend && python scripts/test_bookmarks_api.py`

Expected: All 7 tests pass with SUCCESS messages

**Step 3: Document test results**

If tests fail, investigate errors and fix backend issues before continuing.
If tests pass, proceed to Task 2.

**Step 4: Commit validation script**

```bash
git add backend/scripts/test_bookmarks_api.py
git commit -m "test: validate bookmarks API endpoints for Phase 5"
```

---

## Task 2: Create TypeScript Bookmarks Service

**Goal:** Create typed API service for niche bookmarks with React Query integration.

**Files:**
- Create: `frontend/src/services/bookmarksService.ts`
- Create: `frontend/src/hooks/useBookmarks.ts`
- Create: `frontend/src/types/bookmarks.ts`

**Step 1: Create TypeScript types**

Create `frontend/src/types/bookmarks.ts`:

```typescript
export interface SavedNiche {
  id: string
  niche_name: string
  category_id?: number
  category_name?: string
  description?: string
  filters: Record<string, any>
  last_score?: number
  created_at: string
  updated_at: string
}

export interface CreateBookmarkRequest {
  niche_name: string
  category_id?: number
  category_name?: string
  description?: string
  filters: Record<string, any>
  last_score?: number
}

export interface UpdateBookmarkRequest {
  niche_name?: string
  description?: string
  filters?: Record<string, any>
}

export interface BookmarksListResponse {
  niches: SavedNiche[]
  total_count: number
}

export interface BookmarkFiltersResponse {
  filters: Record<string, any>
  category_id?: number
  category_name?: string
}
```

**Step 2: Create API service**

Create `frontend/src/services/bookmarksService.ts`:

```typescript
import { apiClient } from './api'
import type {
  SavedNiche,
  CreateBookmarkRequest,
  UpdateBookmarkRequest,
  BookmarksListResponse,
  BookmarkFiltersResponse,
} from '../types/bookmarks'

const BOOKMARKS_BASE = '/api/v1/bookmarks/niches'

export const bookmarksService = {
  async createBookmark(data: CreateBookmarkRequest): Promise<SavedNiche> {
    const response = await apiClient.post<SavedNiche>(BOOKMARKS_BASE, data)
    return response.data
  },

  async listBookmarks(params?: {
    skip?: number
    limit?: number
  }): Promise<BookmarksListResponse> {
    const response = await apiClient.get<BookmarksListResponse>(BOOKMARKS_BASE, {
      params,
    })
    return response.data
  },

  async getBookmark(nicheId: string): Promise<SavedNiche> {
    const response = await apiClient.get<SavedNiche>(
      `${BOOKMARKS_BASE}/${nicheId}`
    )
    return response.data
  },

  async updateBookmark(
    nicheId: string,
    data: UpdateBookmarkRequest
  ): Promise<SavedNiche> {
    const response = await apiClient.put<SavedNiche>(
      `${BOOKMARKS_BASE}/${nicheId}`,
      data
    )
    return response.data
  },

  async deleteBookmark(nicheId: string): Promise<void> {
    await apiClient.delete(`${BOOKMARKS_BASE}/${nicheId}`)
  },

  async getBookmarkFilters(nicheId: string): Promise<BookmarkFiltersResponse> {
    const response = await apiClient.get<BookmarkFiltersResponse>(
      `${BOOKMARKS_BASE}/${nicheId}/filters`
    )
    return response.data
  },
}
```

**Step 3: Create React Query hooks**

Create `frontend/src/hooks/useBookmarks.ts`:

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bookmarksService } from '../services/bookmarksService'
import type { CreateBookmarkRequest, UpdateBookmarkRequest } from '../types/bookmarks'

const QUERY_KEY = 'bookmarks'

export function useBookmarks(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => bookmarksService.listBookmarks(params),
  })
}

export function useBookmark(nicheId: string | undefined) {
  return useQuery({
    queryKey: [QUERY_KEY, nicheId],
    queryFn: () => bookmarksService.getBookmark(nicheId!),
    enabled: !!nicheId,
  })
}

export function useBookmarkFilters(nicheId: string | undefined) {
  return useQuery({
    queryKey: [QUERY_KEY, nicheId, 'filters'],
    queryFn: () => bookmarksService.getBookmarkFilters(nicheId!),
    enabled: !!nicheId,
  })
}

export function useCreateBookmark() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateBookmarkRequest) =>
      bookmarksService.createBookmark(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

export function useUpdateBookmark() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      nicheId,
      data,
    }: {
      nicheId: string
      data: UpdateBookmarkRequest
    }) => bookmarksService.updateBookmark(nicheId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, variables.nicheId] })
    },
  })
}

export function useDeleteBookmark() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (nicheId: string) => bookmarksService.deleteBookmark(nicheId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}
```

**Step 4: Build TypeScript to verify no errors**

Run: `cd frontend && npm run build`

Expected: Build succeeds with no TypeScript errors

**Step 5: Commit service layer**

```bash
git add frontend/src/types/bookmarks.ts frontend/src/services/bookmarksService.ts frontend/src/hooks/useBookmarks.ts
git commit -m "feat: add bookmarks service layer with React Query hooks"
```

---

## Task 3: Add Save Button to NicheCard

**Goal:** Add bookmark button to each niche card with toast confirmation.

**Files:**
- Modify: `frontend/src/components/niche-discovery/NicheCard.tsx`
- Verify: `frontend/src/types/niche.ts` has ValidatedNiche type

**Step 1: Update NicheCard component**

Modify `frontend/src/components/niche-discovery/NicheCard.tsx`:

Add imports:
```typescript
import { useCreateBookmark } from '../../hooks/useBookmarks'
import { Bookmark } from 'lucide-react'
```

Add hook inside component:
```typescript
const { mutate: saveBookmark, isPending: isSaving } = useCreateBookmark()
```

Add save handler:
```typescript
const handleSave = () => {
  saveBookmark(
    {
      niche_name: niche.name,
      category_id: niche.category_id,
      category_name: niche.category_name,
      description: niche.description,
      filters: {
        bsr_range: niche.bsr_range,
        price_range: niche.price_range,
        min_roi: niche.min_roi,
      },
      last_score: niche.niche_score,
    },
    {
      onSuccess: () => {
        // Toast will be added in next step
        console.log('Niche saved successfully')
      },
      onError: (error) => {
        console.error('Failed to save niche:', error)
      },
    }
  )
}
```

Add button to card header (find the card title section):
```typescript
<div className="flex items-center justify-between mb-4">
  <h3 className="text-xl font-bold text-gray-900">{niche.name}</h3>
  <button
    onClick={handleSave}
    disabled={isSaving}
    className="p-2 rounded-lg hover:bg-purple-50 transition-colors disabled:opacity-50"
    title="Sauvegarder cette niche"
  >
    <Bookmark
      className={`w-5 h-5 ${isSaving ? 'text-gray-400' : 'text-purple-600'}`}
    />
  </button>
</div>
```

**Step 2: Test UI changes**

Run: `cd frontend && npm run dev`

Navigate to Niche Discovery page, click "Explorer niches" and verify:
- Bookmark icon appears on each niche card
- Clicking icon logs success message
- Button disables while saving

**Step 3: Commit UI changes**

```bash
git add frontend/src/components/niche-discovery/NicheCard.tsx
git commit -m "feat: add save bookmark button to NicheCard"
```

---

## Task 4: Create Mes Niches Page

**Goal:** Create simple page to list saved niches with basic actions.

**Files:**
- Modify: `frontend/src/pages/MesNiches.tsx` (already exists, enhance it)
- Modify: `frontend/src/App.tsx` (verify route exists)

**Step 1: Implement Mes Niches page**

Replace content in `frontend/src/pages/MesNiches.tsx`:

```typescript
import { useState } from 'react'
import { useBookmarks, useDeleteBookmark } from '../hooks/useBookmarks'
import { Trash2, RefreshCw, Calendar, TrendingUp } from 'lucide-react'
import type { SavedNiche } from '../types/bookmarks'

export default function MesNiches() {
  const { data, isLoading, error } = useBookmarks()
  const { mutate: deleteBookmark } = useDeleteBookmark()

  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = (nicheId: string) => {
    if (!confirm('Supprimer cette niche sauvegardee ?')) return

    setDeletingId(nicheId)
    deleteBookmark(nicheId, {
      onSettled: () => setDeletingId(null),
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-blue-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-blue-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-900 mb-2">Erreur</h2>
            <p className="text-red-700">
              Impossible de charger vos niches sauvegardees
            </p>
          </div>
        </div>
      </div>
    )
  }

  const niches = data?.niches || []

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-blue-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Mes Niches</h1>
          <p className="text-gray-600 text-lg">
            {niches.length === 0
              ? 'Aucune niche sauvegardee'
              : `${niches.length} niche${niches.length > 1 ? 's' : ''} sauvegardee${niches.length > 1 ? 's' : ''}`}
          </p>
        </div>

        {/* Empty State */}
        {niches.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Aucune niche sauvegardee
            </h3>
            <p className="text-gray-600 mb-6">
              Decouvrez des niches rentables et sauvegardez vos favorites
            </p>
            <a
              href="/niche-discovery"
              className="inline-block px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Decouvrir des niches
            </a>
          </div>
        )}

        {/* Niches List */}
        {niches.length > 0 && (
          <div className="space-y-4">
            {niches.map((niche) => (
              <NicheListItem
                key={niche.id}
                niche={niche}
                onDelete={handleDelete}
                isDeleting={deletingId === niche.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface NicheListItemProps {
  niche: SavedNiche
  onDelete: (id: string) => void
  isDeleting: boolean
}

function NicheListItem({ niche, onDelete, isDeleting }: NicheListItemProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        {/* Left: Niche Info */}
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {niche.niche_name}
          </h3>
          {niche.description && (
            <p className="text-gray-600 mb-3">{niche.description}</p>
          )}
          {niche.category_name && (
            <p className="text-sm text-gray-500 mb-3">
              Categorie: {niche.category_name}
            </p>
          )}

          {/* Metadata */}
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>
                Sauvegarde le{' '}
                {new Date(niche.created_at).toLocaleDateString('fr-FR')}
              </span>
            </div>
            {niche.last_score && (
              <div className="flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                <span>Score: {niche.last_score.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => {
              /* TODO: Implement in Task 5 */
            }}
            className="p-2 rounded-lg hover:bg-purple-50 transition-colors"
            title="Relancer l'analyse"
          >
            <RefreshCw className="w-5 h-5 text-purple-600" />
          </button>
          <button
            onClick={() => onDelete(niche.id)}
            disabled={isDeleting}
            className="p-2 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
            title="Supprimer"
          >
            <Trash2 className="w-5 h-5 text-red-600" />
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify route exists in App.tsx**

Check `frontend/src/App.tsx` has route:
```typescript
<Route path="/mes-niches" element={<MesNiches />} />
```

If missing, add it.

**Step 3: Test Mes Niches page**

Run: `cd frontend && npm run dev`

Navigate to `/mes-niches`:
- Empty state shows if no bookmarks
- List shows if bookmarks exist
- Delete button works with confirmation

**Step 4: Commit Mes Niches page**

```bash
git add frontend/src/pages/MesNiches.tsx frontend/src/App.tsx
git commit -m "feat: implement Mes Niches page with list and delete"
```

---

## Task 5: Implement Re-run Analysis

**Goal:** Add "Relancer analyse" functionality with Keepa data refresh.

**Files:**
- Modify: `frontend/src/pages/MesNiches.tsx`
- Modify: `frontend/src/hooks/useNicheDiscovery.ts` (may need to add re-run method)

**Step 1: Add re-run handler to Mes Niches**

In `frontend/src/pages/MesNiches.tsx`, update imports:
```typescript
import { useNavigate } from 'react-router-dom'
import { useBookmarkFilters } from '../hooks/useBookmarks'
import { nicheDiscoveryService } from '../services/nicheDiscoveryService'
```

Add state and navigate:
```typescript
const navigate = useNavigate()
const [rerunningId, setRerunningId] = useState<string | null>(null)
```

Add re-run handler:
```typescript
const handleRerun = async (niche: SavedNiche) => {
  try {
    setRerunningId(niche.id)

    // Fetch original filters
    const { filters } = await bookmarksService.getBookmarkFilters(niche.id)

    // Re-run discovery with force_refresh=true
    const result = await nicheDiscoveryService.discoverManual({
      ...filters,
      force_refresh: true, // Force Keepa API refresh
    })

    // Navigate to results
    navigate('/niche-discovery', {
      state: { rerunResults: result, fromNiche: niche },
    })
  } catch (error) {
    console.error('Failed to re-run analysis:', error)
    alert('Erreur lors de la relance de l\'analyse')
  } finally {
    setRerunningId(null)
  }
}
```

Update button in NicheListItem:
```typescript
<button
  onClick={() => handleRerun(niche)}
  disabled={rerunningId === niche.id}
  className="p-2 rounded-lg hover:bg-purple-50 transition-colors disabled:opacity-50"
  title="Relancer l'analyse"
>
  <RefreshCw
    className={`w-5 h-5 text-purple-600 ${
      rerunningId === niche.id ? 'animate-spin' : ''
    }`}
  />
</button>
```

**Step 2: Handle re-run results in NicheDiscovery page**

In `frontend/src/pages/NicheDiscovery.tsx`, check for state:

```typescript
import { useLocation } from 'react-router-dom'

// Inside component
const location = useLocation()
const rerunResults = location.state?.rerunResults
const fromNiche = location.state?.fromNiche

// Show banner if re-run results
{rerunResults && (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
    <p className="text-blue-900">
      Analyse relancee pour <strong>{fromNiche?.niche_name}</strong> avec donnees Keepa a jour
    </p>
  </div>
)}
```

**Step 3: Test re-run flow**

1. Save a niche from discovery
2. Go to Mes Niches
3. Click refresh button
4. Verify:
   - Spinner shows while loading
   - Redirects to Niche Discovery with fresh results
   - Banner confirms re-run

**Step 4: Commit re-run feature**

```bash
git add frontend/src/pages/MesNiches.tsx frontend/src/pages/NicheDiscovery.tsx
git commit -m "feat: implement re-run analysis with Keepa refresh"
```

---

## Task 6: Add Toast Notifications

**Goal:** Add user feedback toasts for bookmark actions.

**Files:**
- Install: `react-hot-toast` package
- Modify: `frontend/src/main.tsx` (add Toaster)
- Modify: `frontend/src/components/niche-discovery/NicheCard.tsx` (add toast on save)

**Step 1: Install toast library**

Run: `cd frontend && npm install react-hot-toast`

**Step 2: Add Toaster to app root**

Modify `frontend/src/main.tsx`:

```typescript
import { Toaster } from 'react-hot-toast'

// Inside <StrictMode>
<>
  <BrowserRouter>
    <App />
  </BrowserRouter>
  <Toaster position="top-right" />
</>
```

**Step 3: Add toasts to NicheCard**

In `frontend/src/components/niche-discovery/NicheCard.tsx`:

```typescript
import toast from 'react-hot-toast'

// Update success handler
onSuccess: () => {
  toast.success(`Niche "${niche.name}" sauvegardee`)
}

// Update error handler
onError: (error) => {
  toast.error('Erreur lors de la sauvegarde')
  console.error(error)
}
```

**Step 4: Add toasts to Mes Niches**

In `frontend/src/pages/MesNiches.tsx`:

```typescript
import toast from 'react-hot-toast'

// Delete success
onSuccess: () => {
  toast.success('Niche supprimee')
}

// Re-run success (in navigate)
toast.success('Analyse relancee avec donnees a jour')
navigate(...)
```

**Step 5: Test toasts**

Verify toasts appear for:
- Save niche (success/error)
- Delete niche (success)
- Re-run analysis (success)

**Step 6: Commit toast integration**

```bash
git add frontend/package.json frontend/src/main.tsx frontend/src/components/niche-discovery/NicheCard.tsx frontend/src/pages/MesNiches.tsx
git commit -m "feat: add toast notifications for user feedback"
```

---

## Task 7: Add Navigation Link

**Goal:** Add "Mes Niches" link to sidebar navigation.

**Files:**
- Modify: `frontend/src/components/Layout/Layout.tsx` (or wherever nav is)

**Step 1: Add nav link**

Find navigation component (likely in `Layout.tsx`), add:

```typescript
<NavLink
  to="/mes-niches"
  className={({ isActive }) =>
    `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
      isActive
        ? 'bg-purple-100 text-purple-900'
        : 'text-gray-700 hover:bg-gray-100'
    }`
  }
>
  <Bookmark className="w-5 h-5" />
  <span>Mes Niches</span>
</NavLink>
```

**Step 2: Test navigation**

Verify link appears in sidebar and highlights when active.

**Step 3: Commit navigation**

```bash
git add frontend/src/components/Layout/Layout.tsx
git commit -m "feat: add Mes Niches navigation link"
```

---

## Task 8: E2E Testing and Validation

**Goal:** Validate complete user flow with real Keepa data.

**Files:**
- Create: `docs/validation/2025-11-02-niche-bookmarks-e2e.md`

**Step 1: Manual E2E test**

Execute this flow:

1. Navigate to Niche Discovery
2. Click "Explorer niches" (auto-discovery)
3. Save 2 niches using bookmark button
4. Verify toast confirmations
5. Navigate to Mes Niches via sidebar
6. Verify 2 niches appear in list
7. Click "Relancer analyse" on first niche
8. Verify redirect to Niche Discovery with fresh data
9. Verify banner shows re-run confirmation
10. Go back to Mes Niches
11. Delete one niche
12. Verify deletion confirmation and list update

**Step 2: Document results**

Create `docs/validation/2025-11-02-niche-bookmarks-e2e.md`:

```markdown
# Niche Bookmarks E2E Validation

**Date:** 2025-11-02
**Tester:** [Your Name]
**Backend:** https://arbitragevault-backend-v2.onrender.com
**Frontend:** Local dev server

## Test Results

| Step | Action | Expected | Actual | Status |
|------|--------|----------|--------|--------|
| 1 | Save niche | Toast + bookmark icon fills | | PASS/FAIL |
| 2 | Navigate to Mes Niches | 2 niches listed | | PASS/FAIL |
| 3 | Re-run analysis | Redirect + fresh data | | PASS/FAIL |
| 4 | Delete niche | Confirmation + removed from list | | PASS/FAIL |

## Issues Found

[List any issues]

## Screenshots

[Add screenshots if needed]

## Conclusion

[PASS / FAIL with notes]
```

**Step 3: Fix any issues found**

If issues discovered, create tasks to fix them.

**Step 4: Final commit**

```bash
git add docs/validation/2025-11-02-niche-bookmarks-e2e.md
git commit -m "docs: E2E validation results for niche bookmarks flow"
```

---

## Task 9: Final Build Verification

**Goal:** Verify production build succeeds (deployment will be done later).

**Step 1: Build frontend**

Run: `cd frontend && npm run build`

Expected: Build succeeds with no TypeScript errors

**Step 2: Test local build**

Run: `cd frontend && npm run preview`

Test complete flow on local preview:
- Frontend: http://localhost:4173 (preview server)
- Backend: https://arbitragevault-backend-v2.onrender.com

**Step 3: Update documentation**

Update `.claude/memory/compact_current.md` with:
- Feature completion status
- Local validation results
- Ready for production deployment (future step)

**Note:** Netlify deployment will be configured in a future session.

---

## Success Criteria

- All backend bookmarks endpoints tested and working
- Users can save niches from discovery
- Mes Niches page lists saved niches
- Re-run analysis fetches fresh Keepa data
- Toast notifications provide feedback
- Navigation link works
- E2E flow validates successfully
- Deployed to production

## Next Steps (Future Enhancements)

1. Add "Saved" badge to already-bookmarked niches in discovery
2. Add sorting/filtering on Mes Niches page
3. Add tags/categories for organizing niches
4. Add comparison view for multiple niches
5. Add export to CSV functionality

---

**Plan Complete**
