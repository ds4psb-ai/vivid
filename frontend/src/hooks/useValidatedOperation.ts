"use client";

/**
 * useValidatedOperation - Enhanced useAsyncOperation with Zod validation
 *
 * Phase -1: F2 API Contract Implementation
 *
 * Features:
 * - Request validation before API call
 * - Response validation after API call
 * - Type-safe with inferred types from schemas
 * - Compatible with existing useAsyncOperation pattern
 */

import { useState, useCallback, useRef } from "react";
import { ZodSchema } from "zod";
import {
  validateRequest,
  formatZodError,
  type ZodErrorTree,
} from "@/lib/schemas/validated-fetch";

// =============================================================================
// Types
// =============================================================================

export interface UseValidatedOperationOptions<TRes> {
  /** Called when operation succeeds */
  onSuccess?: (data: TRes) => void;
  /** Called when operation fails */
  onError?: (error: Error) => void;
  /** Called on validation error */
  onValidationError?: (errors: ZodErrorTree) => void;
  /** Maximum retry attempts (default: 3) */
  retryCount?: number;
  /** Base delay for exponential backoff in ms (default: 1000) */
  retryDelay?: number;
  /** Error messages that should NOT trigger retry */
  nonRetryableErrors?: string[];
  /** Request timeout in ms (default: 120000) */
  timeout?: number;
  /** Skip response validation (for legacy endpoints) */
  skipResponseValidation?: boolean;
}

export interface UseValidatedOperationReturn<TReq, TRes> {
  // State
  isLoading: boolean;
  error: string | null;
  validationErrors: ZodErrorTree | null;
  data: TRes | null;

  // Actions
  execute: (
    url: string,
    body: TReq,
    headers?: Record<string, string>
  ) => Promise<TRes | null>;
  validate: (body: unknown) => boolean;
  reset: () => void;
  clearValidationErrors: () => void;

  // Computed
  canRetry: boolean;
  isRetrying: boolean;
  currentRetryCount: number;
}

// =============================================================================
// Hook
// =============================================================================

export function useValidatedOperation<TReq, TRes>(
  requestSchema: ZodSchema<TReq>,
  responseSchema: ZodSchema<TRes>,
  options: UseValidatedOperationOptions<TRes> = {}
): UseValidatedOperationReturn<TReq, TRes> {
  const {
    onSuccess,
    onError,
    onValidationError,
    retryCount = 3,
    retryDelay = 1000,
    nonRetryableErrors = [],
    timeout = 120000,
    skipResponseValidation = false,
  } = options;

  // State
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ZodErrorTree | null>(null);
  const [data, setData] = useState<TRes | null>(null);
  const [currentRetryCount, setCurrentRetryCount] = useState(0);

  // Refs for retry
  const lastRequestRef = useRef<{
    url: string;
    body: TReq;
    headers?: Record<string, string>;
  } | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Validate request without executing
   */
  const validate = useCallback(
    (body: unknown): boolean => {
      const result = requestSchema.safeParse(body);
      if (!result.success) {
        const errors = formatZodError(result.error);
        setValidationErrors(errors);
        onValidationError?.(errors);
        return false;
      }
      setValidationErrors(null);
      return true;
    },
    [requestSchema, onValidationError]
  );

  /**
   * Clear validation errors
   */
  const clearValidationErrors = useCallback(() => {
    setValidationErrors(null);
  }, []);

  /**
   * Reset all state
   */
  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
    setValidationErrors(null);
    setData(null);
    setCurrentRetryCount(0);
    lastRequestRef.current = null;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  /**
   * Check if error is retryable
   */
  const isRetryable = useCallback(
    (errorMsg: string): boolean => {
      return !nonRetryableErrors.some((pattern) =>
        errorMsg.toLowerCase().includes(pattern.toLowerCase())
      );
    },
    [nonRetryableErrors]
  );

  /**
   * Execute with validation
   */
  const execute = useCallback(
    async (
      url: string,
      body: TReq,
      headers?: Record<string, string>
    ): Promise<TRes | null> => {
      // 1. Request Validation
      const reqResult = validateRequest(body, requestSchema);
      if (!reqResult.success) {
        setValidationErrors(reqResult.validationErrors!);
        onValidationError?.(reqResult.validationErrors!);
        return null;
      }

      const validatedBody = reqResult.data;
      setValidationErrors(null);

      // Store for retry
      lastRequestRef.current = { url, body: validatedBody, headers };

      // 2. Setup
      setIsLoading(true);
      setError(null);

      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      const timeoutId = setTimeout(() => {
        abortControllerRef.current?.abort();
      }, timeout);

      try {
        // 3. Fetch
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...headers,
          },
          body: JSON.stringify(validatedBody),
          signal: abortControllerRef.current.signal,
        });

        clearTimeout(timeoutId);

        // 4. Handle HTTP errors
        if (!response.ok) {
          let errorMessage = `HTTP ${response.status}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.error || errorMessage;
          } catch {
            // Response is not JSON
          }

          throw new Error(errorMessage);
        }

        // 5. Parse response
        const responseData = await response.json();

        // 6. Response validation
        if (!skipResponseValidation) {
          const resResult = responseSchema.safeParse(responseData);
          if (!resResult.success) {
            console.warn(
              "[useValidatedOperation] Response validation warning:",
              formatZodError(resResult.error)
            );
            // Continue anyway for backward compatibility
          }
        }

        // 7. Success
        setData(responseData as TRes);
        setCurrentRetryCount(0);
        onSuccess?.(responseData as TRes);

        return responseData as TRes;
      } catch (err) {
        clearTimeout(timeoutId);

        const errorMessage =
          err instanceof Error
            ? err.name === "AbortError"
              ? "Request timeout or cancelled"
              : err.message
            : "Unknown error";

        setError(errorMessage);

        // Check if should retry
        if (
          currentRetryCount < retryCount &&
          isRetryable(errorMessage) &&
          lastRequestRef.current
        ) {
          setCurrentRetryCount((prev) => prev + 1);

          // Exponential backoff
          const delay = retryDelay * Math.pow(2, currentRetryCount);
          await new Promise((resolve) => setTimeout(resolve, delay));

          // Retry
          return execute(
            lastRequestRef.current.url,
            lastRequestRef.current.body,
            lastRequestRef.current.headers
          );
        }

        onError?.(new Error(errorMessage));
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [
      requestSchema,
      responseSchema,
      onSuccess,
      onError,
      onValidationError,
      retryCount,
      retryDelay,
      timeout,
      skipResponseValidation,
      isRetryable,
      currentRetryCount,
    ]
  );

  return {
    // State
    isLoading,
    error,
    validationErrors,
    data,

    // Actions
    execute,
    validate,
    reset,
    clearValidationErrors,

    // Computed
    canRetry: currentRetryCount < retryCount && !!lastRequestRef.current,
    isRetrying: currentRetryCount > 0 && isLoading,
    currentRetryCount,
  };
}

// =============================================================================
// Convenience Wrapper
// =============================================================================

/**
 * Create a pre-configured validated operation hook for a specific API
 *
 * @example
 * const useGenerate1D = createValidatedOperation(
 *   Generate1DRequestSchema,
 *   Generate1DResponseSchema
 * );
 *
 * // In component:
 * const { execute, data, validationErrors } = useGenerate1D({
 *   onSuccess: (data) => console.log(data),
 * });
 */
export function createValidatedOperation<TReq, TRes>(
  requestSchema: ZodSchema<TReq>,
  responseSchema: ZodSchema<TRes>
) {
  return (options?: UseValidatedOperationOptions<TRes>) =>
    useValidatedOperation(requestSchema, responseSchema, options);
}

export default useValidatedOperation;
