/**
 * Configuration Types for Phase 9
 * Backend: /api/v1/config/*
 */
import { z } from 'zod'

// Business config schema - matches backend BusinessConfigSchema (unified field names)
export const RoiConfigSchema = z.object({
  target_pct: z.number(),
  min_acceptable: z.number(),
  excellent_threshold: z.number(),
  good_threshold: z.number().optional(),
  fair_threshold: z.number().optional(),
  source_price_factor: z.number().optional(),
})

export const CombinedScoreConfigSchema = z.object({
  roi_weight: z.number(),
  velocity_weight: z.number(),
})

export const FeesConfigSchema = z.object({
  buffer_pct_default: z.number(),
  books: z.record(z.number()).optional(),
  media: z.record(z.number()).optional(),
  default: z.record(z.number()).optional(),
})

export const VelocityConfigSchema = z.object({
  fast_threshold: z.number(),
  medium_threshold: z.number(),
  slow_threshold: z.number(),
  benchmarks: z.record(z.number()).optional(),
})

export const BusinessConfigSchema = z.object({
  roi: RoiConfigSchema.optional(),
  combined_score: CombinedScoreConfigSchema.optional(),
  fees: FeesConfigSchema.optional(),
  velocity: VelocityConfigSchema.optional(),
  recommendation_rules: z.array(z.record(z.unknown())).optional(),
  demo_asins: z.array(z.string()).optional(),
  meta: z.record(z.unknown()).optional(),
})

export type BusinessConfig = z.infer<typeof BusinessConfigSchema>

export const ConfigResponseSchema = z.object({
  scope: z.string(),
  config: BusinessConfigSchema,
  version: z.number(),
  effective_config: BusinessConfigSchema.optional(),
  sources: z.record(z.string(), z.boolean()).optional(),
  updated_at: z.string(),
})

export type ConfigResponse = z.infer<typeof ConfigResponseSchema>

export const ConfigStatsSchema = z.object({
  total_configs: z.number(),
  by_scope: z.record(z.string(), z.number()),
  last_updated: z.string().nullable(),
  cache_status: z.string(),
})

export type ConfigStats = z.infer<typeof ConfigStatsSchema>

export interface ConfigUpdateRequest {
  config_patch: Partial<BusinessConfig>
  change_reason?: string
}
