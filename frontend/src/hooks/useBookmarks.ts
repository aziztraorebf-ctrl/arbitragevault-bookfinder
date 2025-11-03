/**
 * React Query hooks for Niche Bookmarks
 * Phase 5 - Niche Bookmarks Flow
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bookmarksService } from '../services/bookmarksService'
import type {
  CreateBookmarkRequest,
  UpdateBookmarkRequest,
} from '../types/bookmarks'

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
