/**
 * Configuration Types for Phase 9
 * Backend: /api/v1/config/*
 */
import { z } from 'zod'

// Business config schema - matches backend BusinessConfigSchema
export const BusinessConfigSchema = z.object({
  roi_thresholds: z.object({
    minimum: z.number(),
    target: z.number(),
    excellent: z.number(),
  }),
  bsr_limits: z.object({
    max_acceptable: z.number(),
    ideal_max: z.number(),
  }),
  pricing: z.object({
    min_profit_margin: z.number(),
    fee_estimate_percent: z.number(),
  }),
  velocity: z.object({
    min_score: z.number(),
    weight_in_scoring: z.number(),
  }),
})

export type BusinessConfig = z.infer<typeof BusinessConfigSchema>

export const ConfigResponseSchema = z.object({
  scope: z.string(),
  config: BusinessConfigSchema,
  version: z.number(),
  effective_config: BusinessConfigSchema,
  sources: z.record(z.string()).optional(),
  updated_at: z.string(),
})

export type ConfigResponse = z.infer<typeof ConfigResponseSchema>

export const ConfigStatsSchema = z.object({
  total_configs: z.number(),
  by_scope: z.record(z.number()),
  last_updated: z.string().nullable(),
  cache_status: z.string(),
})

export type ConfigStats = z.infer<typeof ConfigStatsSchema>

export interface ConfigUpdateRequest {
  config: Partial<BusinessConfig>
  description?: string
}
