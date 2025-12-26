import { z } from 'zod'

// Stock estimate response schema
export const StockEstimateSchema = z.object({
  asin: z.string(),
  estimated_stock: z.number().nullable(),
  confidence: z.enum(['high', 'medium', 'low']).nullable(),
  method: z.string().nullable(),
  last_updated: z.string().nullable(),
  data_points: z.number().nullable(),
  range: z.object({
    min: z.number(),
    max: z.number(),
  }).nullable(),
})

export type StockEstimate = z.infer<typeof StockEstimateSchema>

// For batch queries
export const StockEstimateListSchema = z.object({
  estimates: z.array(StockEstimateSchema),
  total: z.number(),
})

export type StockEstimateList = z.infer<typeof StockEstimateListSchema>
