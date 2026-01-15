/**
 * Validated Fetch - Type-safe API client with Zod validation
 *
 * Phase -1: F2 API Contract Implementation
 *
 * Features:
 * - Request validation before sending
 * - Response validation after receiving
 * - Unified error handling with z.treeifyError()
 * - Non-throwing API (always returns Result type)
 */
import { z, ZodSchema, ZodError } from "zod";

// =============================================================================
// Types
// =============================================================================

export interface ValidatedFetchOptions<TReq, TRes> {
  /** API endpoint URL */
  url: string;
  /** HTTP method */
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** Zod schema for request validation (optional for GET) */
  requestSchema?: ZodSchema<TReq>;
  /** Zod schema for response validation */
  responseSchema: ZodSchema<TRes>;
  /** Additional headers */
  headers?: Record<string, string>;
  /** Request timeout in ms (default: 30000) */
  timeout?: number;
  /** Skip response validation (use for legacy endpoints) */
  skipResponseValidation?: boolean;
}

export type ValidatedResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; validationErrors?: ZodErrorTree; statusCode?: number };

/**
 * Zod v4 error tree structure from z.treeifyError()
 *
 * In Zod v4, treeifyError returns:
 * {
 *   errors: string[],
 *   properties: { [fieldName]: { errors: string[], properties?: ... } }
 * }
 */
export interface ZodErrorTree {
  errors: string[];
  properties?: Record<string, ZodErrorTree>;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Convert ZodError to tree structure using z.treeifyError()
 * Zod v4 deprecates .flatten() and .format()
 */
export function formatZodError(error: ZodError): ZodErrorTree {
  return z.treeifyError(error) as ZodErrorTree;
}

/**
 * Extract first error message from ZodErrorTree
 */
export function getFirstError(tree: ZodErrorTree): string {
  // Check root level errors first
  if (tree.errors && tree.errors.length > 0) {
    return tree.errors[0];
  }

  // Check field-level errors in properties
  if (tree.properties) {
    for (const [key, nested] of Object.entries(tree.properties)) {
      if (nested.errors && nested.errors.length > 0) {
        return `${key}: ${nested.errors[0]}`;
      }
    }
  }

  return "Validation failed";
}

/**
 * Get field-specific errors from ZodErrorTree
 */
export function getFieldErrors(tree: ZodErrorTree, field: string): string[] {
  if (tree.properties && tree.properties[field]) {
    return tree.properties[field].errors || [];
  }
  return [];
}

// =============================================================================
// Main Function
// =============================================================================

/**
 * Type-safe fetch with Zod validation
 *
 * @example
 * const result = await validatedFetch(
 *   { topic: "AI movie", style: "cinematic" },
 *   {
 *     url: "/api/dimension/1d/generate",
 *     requestSchema: Generate1DRequestSchema,
 *     responseSchema: Generate1DResponseSchema,
 *   }
 * );
 *
 * if (result.success) {
 *   console.log(result.data);
 * } else {
 *   console.error(result.error, result.validationErrors);
 * }
 */
export async function validatedFetch<TReq, TRes>(
  body: TReq,
  options: ValidatedFetchOptions<TReq, TRes>
): Promise<ValidatedResult<TRes>> {
  const {
    url,
    method = "POST",
    requestSchema,
    responseSchema,
    headers = {},
    timeout = 30000,
    skipResponseValidation = false,
  } = options;

  // ==========================================================================
  // 1. Request Validation
  // ==========================================================================
  if (requestSchema) {
    const reqResult = requestSchema.safeParse(body);
    if (!reqResult.success) {
      const errorTree = formatZodError(reqResult.error);
      return {
        success: false,
        error: getFirstError(errorTree),
        validationErrors: errorTree,
      };
    }
    // Use validated data (with defaults applied)
    body = reqResult.data;
  }

  // ==========================================================================
  // 2. Fetch with Timeout
  // ==========================================================================
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const fetchOptions: RequestInit = {
      method,
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      signal: controller.signal,
    };

    // Only add body for non-GET requests
    if (method !== "GET" && body !== undefined) {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);

    // ==========================================================================
    // 3. HTTP Error Handling
    // ==========================================================================
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.error || errorMessage;
      } catch {
        // Response is not JSON
      }

      return {
        success: false,
        error: errorMessage,
        statusCode: response.status,
      };
    }

    // ==========================================================================
    // 4. Parse Response
    // ==========================================================================
    const data = await response.json();

    // ==========================================================================
    // 5. Response Validation
    // ==========================================================================
    if (!skipResponseValidation) {
      const resResult = responseSchema.safeParse(data);
      if (!resResult.success) {
        // Log warning but don't fail - backend might be ahead
        console.warn(
          "[validatedFetch] Response validation warning:",
          formatZodError(resResult.error)
        );
        // Return data anyway for backward compatibility
        return { success: true, data: data as TRes };
      }
      return { success: true, data: resResult.data };
    }

    return { success: true, data: data as TRes };
  } catch (err) {
    clearTimeout(timeoutId);

    if (err instanceof Error) {
      if (err.name === "AbortError") {
        return {
          success: false,
          error: "Request timeout",
        };
      }
      return {
        success: false,
        error: err.message,
      };
    }

    return {
      success: false,
      error: "Unknown error occurred",
    };
  }
}

// =============================================================================
// Convenience Wrappers
// =============================================================================

/**
 * Validate request data without making API call
 * Useful for form validation before submission
 */
export function validateRequest<T>(
  data: unknown,
  schema: ZodSchema<T>
): ValidatedResult<T> {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }

  const errorTree = formatZodError(result.error);
  return {
    success: false,
    error: getFirstError(errorTree),
    validationErrors: errorTree,
  };
}

/**
 * Parse and validate with defaults applied
 * Returns undefined on failure
 */
export function parseWithDefaults<T>(
  data: unknown,
  schema: ZodSchema<T>
): T | undefined {
  const result = schema.safeParse(data);
  return result.success ? result.data : undefined;
}

// =============================================================================
// Export Types
// =============================================================================

export type { ZodError };
