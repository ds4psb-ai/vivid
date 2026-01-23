/**
 * ChainData Zod Schema
 *
 * Runtime validation schema for dimension chain data.
 * Mirrors the ChainData interface from DimensionChainContext.
 */

import { z } from "zod";

/**
 * Schema for chain data stored for each dimension.
 */
export const ChainDataSchema = z.object({
  /** Dimension route key */
  dimensionKey: z.string().min(1, "dimensionKey is required"),
  /** Output data from the dimension */
  output: z.record(z.string(), z.unknown()),
  /** Timestamp of when data was generated */
  timestamp: z.number().int().positive(),
  /** Summary text for display */
  summary: z.string().optional(),
});

/**
 * Schema for a record of chain data indexed by dimension key.
 */
export const ChainDataRecordSchema = z.record(z.string(), ChainDataSchema);

/**
 * Validated ChainData type inferred from schema.
 */
export type ValidatedChainData = z.infer<typeof ChainDataSchema>;

/**
 * Validated ChainData record type.
 */
export type ValidatedChainDataRecord = z.infer<typeof ChainDataRecordSchema>;

/**
 * Validate chain data at runtime.
 *
 * @param data - Data to validate
 * @returns Validated chain data
 * @throws ZodError if validation fails
 */
export function validateChainData(data: unknown): ValidatedChainData {
  return ChainDataSchema.parse(data);
}

/**
 * Safely validate chain data without throwing.
 *
 * @param data - Data to validate
 * @returns Validated chain data or null if invalid
 */
export function safeValidateChainData(data: unknown): ValidatedChainData | null {
  const result = ChainDataSchema.safeParse(data);
  return result.success ? result.data : null;
}

/**
 * Validate a record of chain data.
 *
 * @param data - Record to validate
 * @returns Validated record or null if invalid
 */
export function safeValidateChainDataRecord(
  data: unknown
): ValidatedChainDataRecord | null {
  const result = ChainDataRecordSchema.safeParse(data);
  return result.success ? result.data : null;
}
