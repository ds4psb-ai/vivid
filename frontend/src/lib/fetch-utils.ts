/**
 * Fetch Utilities for Server Components
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * Provides retry logic with exponential backoff for server-side data fetching.
 * Used by server components to handle transient network failures gracefully.
 *
 * 2026 Best Practices:
 * - Exponential backoff with jitter to prevent thundering herd
 * - Configurable retry count and delays
 * - Proper error logging for observability
 * - Type-safe response handling
 */

// =============================================================================
// Types
// =============================================================================

export interface FetchWithRetryOptions extends RequestInit {
  /** Maximum number of retry attempts (default: 3) */
  maxRetries?: number;
  /** Base delay in ms before first retry (default: 1000) */
  baseDelay?: number;
  /** Maximum delay in ms between retries (default: 10000) */
  maxDelay?: number;
  /** Whether to add jitter to retry delays (default: true) */
  jitter?: boolean;
  /** Request timeout in ms (default: 30000) */
  timeout?: number;
}

export interface FetchResult<T> {
  data: T | null;
  error: string | null;
  status: number | null;
  retries: number;
}

// =============================================================================
// Retry Logic
// =============================================================================

/**
 * Calculate delay with exponential backoff and optional jitter
 */
function calculateDelay(
  attempt: number,
  baseDelay: number,
  maxDelay: number,
  jitter: boolean
): number {
  // Exponential backoff: baseDelay * 2^attempt
  let delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);

  // Add jitter (±25%) to prevent thundering herd
  if (jitter) {
    const jitterFactor = 0.75 + Math.random() * 0.5; // 0.75 to 1.25
    delay = Math.floor(delay * jitterFactor);
  }

  return delay;
}

/**
 * Check if error is retryable
 */
function isRetryableError(status: number | null, error: unknown): boolean {
  // Network errors are retryable
  if (error instanceof TypeError) return true;

  // Server errors (5xx) are retryable
  if (status && status >= 500 && status < 600) return true;

  // Rate limiting (429) is retryable
  if (status === 429) return true;

  // Request timeout (408) is retryable
  if (status === 408) return true;

  return false;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// =============================================================================
// Main Fetch Functions
// =============================================================================

/**
 * Fetch with automatic retry on transient failures
 *
 * @example
 * ```ts
 * const result = await fetchWithRetry<IPDetail>(
 *   `${API_URL}/api/v1/ip/catalog/${slug}`,
 *   {
 *     headers: { "Content-Type": "application/json" },
 *     next: { revalidate: 900 },
 *     maxRetries: 3,
 *   }
 * );
 *
 * if (result.error) {
 *   console.error(`Failed after ${result.retries} retries: ${result.error}`);
 *   return null;
 * }
 *
 * return result.data;
 * ```
 */
export async function fetchWithRetry<T>(
  url: string,
  options: FetchWithRetryOptions = {}
): Promise<FetchResult<T>> {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    jitter = true,
    timeout = 30000,
    ...fetchOptions
  } = options;

  let lastError: string | null = null;
  let lastStatus: number | null = null;
  let attempts = 0;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    attempts = attempt;

    try {
      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      lastStatus = response.status;

      if (response.ok) {
        const data = (await response.json()) as T;
        return {
          data,
          error: null,
          status: response.status,
          retries: attempt,
        };
      }

      // Non-2xx response
      lastError = `HTTP ${response.status}: ${response.statusText}`;

      // Check if we should retry
      if (!isRetryableError(response.status, null) || attempt >= maxRetries) {
        break;
      }

      // Wait before retry
      const delay = calculateDelay(attempt, baseDelay, maxDelay, jitter);
      console.warn(
        `[fetchWithRetry] Attempt ${attempt + 1}/${maxRetries + 1} failed for ${url}, ` +
          `status=${response.status}, retrying in ${delay}ms`
      );
      await sleep(delay);
    } catch (error) {
      // Network or timeout error
      if (error instanceof Error) {
        if (error.name === "AbortError") {
          lastError = `Request timeout (${timeout}ms)`;
        } else {
          lastError = error.message;
        }
      } else {
        lastError = "Unknown error";
      }

      // Check if we should retry
      if (!isRetryableError(null, error) || attempt >= maxRetries) {
        break;
      }

      // Wait before retry
      const delay = calculateDelay(attempt, baseDelay, maxDelay, jitter);
      console.warn(
        `[fetchWithRetry] Attempt ${attempt + 1}/${maxRetries + 1} failed for ${url}, ` +
          `error="${lastError}", retrying in ${delay}ms`
      );
      await sleep(delay);
    }
  }

  // All retries exhausted
  console.error(
    `[fetchWithRetry] All ${maxRetries + 1} attempts failed for ${url}: ${lastError}`
  );

  return {
    data: null,
    error: lastError,
    status: lastStatus,
    retries: attempts,
  };
}

/**
 * Simple fetch wrapper with type safety (no retry)
 * Use for endpoints where retry doesn't make sense (e.g., user input validation)
 */
export async function fetchJSON<T>(
  url: string,
  options: RequestInit = {}
): Promise<{ data: T | null; error: string | null }> {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      return {
        data: null,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = (await response.json()) as T;
    return { data, error: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}
