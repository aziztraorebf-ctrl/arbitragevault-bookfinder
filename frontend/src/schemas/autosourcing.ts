/**
 * Zod schemas for AutoSourcing API error responses.
 * Provides runtime type validation for error handling.
 */
import { z } from 'zod';

/**
 * Schema for JOB_TOO_EXPENSIVE error response.
 * Returned when estimated token cost exceeds MAX_TOKENS_PER_JOB.
 */
export const jobTooExpensiveErrorSchema = z.object({
  error: z.literal('JOB_TOO_EXPENSIVE'),
  estimated_tokens: z.number(),
  max_allowed: z.number(),
  suggestion: z.string(),
});

export type JobTooExpensiveError = z.infer<typeof jobTooExpensiveErrorSchema>;

/**
 * Schema for INSUFFICIENT_TOKENS error response.
 * Returned when Keepa API balance is too low.
 */
export const insufficientTokensErrorSchema = z.object({
  error: z.literal('INSUFFICIENT_TOKENS'),
  balance: z.number(),
  required: z.number(),
});

export type InsufficientTokensError = z.infer<typeof insufficientTokensErrorSchema>;

/**
 * Schema for timeout error response (HTTP 408).
 * Returned when job exceeds TIMEOUT_PER_JOB limit.
 */
export const timeoutErrorSchema = z.object({
  detail: z.string().regex(/timeout/i),
});

export type TimeoutError = z.infer<typeof timeoutErrorSchema>;

/**
 * Union schema for all AutoSourcing API error responses.
 */
export const autoSourcingErrorSchema = z.union([
  jobTooExpensiveErrorSchema,
  insufficientTokensErrorSchema,
  timeoutErrorSchema,
]);

export type AutoSourcingError = z.infer<typeof autoSourcingErrorSchema>;
