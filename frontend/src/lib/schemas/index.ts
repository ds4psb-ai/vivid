/**
 * Schemas - Main Barrel Export
 *
 * Phase -1: F2 API Contract Implementation
 *
 * Usage:
 * ```typescript
 * import {
 *   Generate1DRequestSchema,
 *   type Generate1DRequest,
 *   validatedFetch,
 * } from "@/lib/schemas";
 * ```
 */

// Common schemas and types
export * from "./common";

// Dimension schemas
export * from "./dimension";

// Validated fetch utilities
export * from "./validated-fetch";
