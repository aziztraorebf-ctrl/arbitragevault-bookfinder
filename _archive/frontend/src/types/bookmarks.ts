/**
 * TypeScript types for Niche Bookmarks API
 * Phase 5 - Niche Bookmarks Flow
 */

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

export interface BookmarkListResponse {
  niches: SavedNiche[]
  total_count: number
}

export interface BookmarkFiltersResponse {
  filters: Record<string, any>
  category_id?: number
  category_name?: string
}
