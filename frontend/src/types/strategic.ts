/**
 * Strategic Views Types for Phase 9
 * Backend: /api/v1/strategic-views/*
 */
import { z } from 'zod'

export type ViewType = 'velocity' | 'competition' | 'volatility' | 'consistency' | 'confidence'

export const StrategicMetricSchema = z.object({
  score: z.number(),
  label: z.string(),
  description: z.string(),
  color: z.enum(['green', 'yellow', 'red', 'gray']),
})

export type StrategicMetric = z.infer<typeof StrategicMetricSchema>

export const StrategicViewResponseSchema = z.object({
  view_type: z.string(),
  metrics: z.record(StrategicMetricSchema).optional(),
  summary: z.object({
    total_products: z.number(),
    avg_score: z.number(),
    recommendation: z.string(),
  }),
  calculated_at: z.string(),
})

export type StrategicViewResponse = z.infer<typeof StrategicViewResponseSchema>

export const TargetPriceProductSchema = z.object({
  asin: z.string(),
  title: z.string().optional().nullable(),
  current_price: z.number(),
  target_price: z.number(),
  expected_roi: z.number(),
  confidence: z.number(),
})

export type TargetPriceProduct = z.infer<typeof TargetPriceProductSchema>

export const TargetPricesSchema = z.object({
  view_type: z.string(),
  products: z.array(TargetPriceProductSchema),
})

export type TargetPrices = z.infer<typeof TargetPricesSchema>
