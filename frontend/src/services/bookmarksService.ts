/**
 * Bookmarks Service - API client for saved niches
 * Phase 5 - Niche Bookmarks Flow
 */

import { api } from './api'
import type {
  SavedNiche,
  CreateBookmarkRequest,
  UpdateBookmarkRequest,
  BookmarkListResponse,
  BookmarkFiltersResponse,
} from '../types/bookmarks'

const BOOKMARKS_BASE = '/api/v1/bookmarks/niches'

export const bookmarksService = {
  async createBookmark(data: CreateBookmarkRequest): Promise<SavedNiche> {
    const response = await api.post<SavedNiche>(BOOKMARKS_BASE, data)
    return response.data
  },

  async listBookmarks(params?: {
    skip?: number
    limit?: number
  }): Promise<BookmarkListResponse> {
    const response = await api.get<BookmarkListResponse>(BOOKMARKS_BASE, {
      params,
    })
    return response.data
  },

  async getBookmark(nicheId: string): Promise<SavedNiche> {
    const response = await api.get<SavedNiche>(
      `${BOOKMARKS_BASE}/${nicheId}`
    )
    return response.data
  },

  async updateBookmark(
    nicheId: string,
    data: UpdateBookmarkRequest
  ): Promise<SavedNiche> {
    const response = await api.put<SavedNiche>(
      `${BOOKMARKS_BASE}/${nicheId}`,
      data
    )
    return response.data
  },

  async deleteBookmark(nicheId: string): Promise<void> {
    await api.delete(`${BOOKMARKS_BASE}/${nicheId}`)
  },

  async getBookmarkFilters(nicheId: string): Promise<BookmarkFiltersResponse> {
    const response = await api.get<BookmarkFiltersResponse>(
      `${BOOKMARKS_BASE}/${nicheId}/filters`
    )
    return response.data
  },
}
