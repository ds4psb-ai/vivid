"use client";

import { useState, useCallback, useRef, useEffect } from "react";

/**
 * Progress event from SSE stream or manual updates.
 */
export interface ProgressEvent {
  /** Progress percentage (0-100) */
  percent: number;
  /** Human-readable status message */
  message: string;
  /** Current processing stage */
  stage?: "starting" | "processing" | "finalizing" | "complete" | "error";
}

/**
 * SSE event types from backend.
 */
interface SSEProgressEvent {
  type: "progress";
  percent: number;
  message: string;
  stage?: string;
}

interface SSECompleteEvent {
  type: "complete";
  data: unknown;
}

interface SSEErrorEvent {
  type: "error";
  error: string;
}

type SSEEvent = SSEProgressEvent | SSECompleteEvent | SSEErrorEvent;

/**
 * Options for useAsyncOperation hook.
 */
export interface UseAsyncOperationOptions<T> {
  /** Called when operation succeeds */
  onSuccess?: (data: T) => void;
  /** Called when operation fails */
  onError?: (error: Error) => void;
  /** Called on each progress update */
  onProgress?: (progress: ProgressEvent) => void;
  /** Maximum retry attempts (default: 3) */
  retryCount?: number;
  /** Base delay for exponential backoff in ms (default: 1000) */
  retryDelay?: number;
  /** Error messages that should NOT trigger retry (e.g., 4xx errors) */
  nonRetryableErrors?: string[];
  /** Request timeout in ms (default: 120000 = 2 minutes) */
  timeout?: number;
}

/**
 * Return type for useAsyncOperation hook.
 */
export interface UseAsyncOperationReturn<T> {
  // State
  isLoading: boolean;
  progress: ProgressEvent | null;
  error: string | null;
  data: T | null;

  // Actions
  execute: (url: string, body: object, headers?: Record<string, string>) => Promise<T | null>;
  executeStream: (url: string, body: object, headers?: Record<string, string>) => Promise<T | null>;
  cancel: () => void;
  retry: () => Promise<T | null>;
  reset: () => void;

  // Computed
  canRetry: boolean;
  isRetrying: boolean;
  currentRetryCount: number;
}

/**
 * Parse error response body (JSON or text).
 */
async function parseErrorResponse(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type");

  try {
    if (contentType?.includes("application/json")) {
      const json = await response.json() as { error?: string; detail?: string; message?: string };
      return json.error || json.detail || json.message || `HTTP ${response.status}`;
    }
    const text = await response.text();
    return text || `HTTP ${response.status}`;
  } catch {
    return `HTTP ${response.status}`;
  }
}

/**
 * Classify error for user-friendly messages.
 */
function classifyError(error: string, statusCode?: number): string {
  const errorLower = error.toLowerCase();

  // Credit errors
  if (errorLower.includes("크레딧") || errorLower.includes("credit") || statusCode === 402) {
    return "크레딧이 부족합니다. 충전 후 다시 시도해주세요.";
  }

  // Auth errors
  if (errorLower.includes("401") || errorLower.includes("unauthorized") || statusCode === 401) {
    return "로그인이 필요합니다.";
  }

  // Forbidden
  if (errorLower.includes("403") || errorLower.includes("forbidden") || statusCode === 403) {
    return "접근 권한이 없습니다.";
  }

  // Not found
  if (errorLower.includes("404") || statusCode === 404) {
    return "요청한 리소스를 찾을 수 없습니다.";
  }

  // Timeout
  if (errorLower.includes("timeout") || errorLower.includes("timed out") || statusCode === 504) {
    return "요청 시간이 초과되었습니다. 다시 시도해주세요.";
  }

  // Network errors
  if (errorLower.includes("network") || errorLower.includes("fetch") || errorLower.includes("failed to fetch")) {
    return "네트워크 연결을 확인해주세요.";
  }

  // Server errors (5xx)
  if (statusCode && statusCode >= 500) {
    return "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
  }

  // Return original if no classification matches
  return error;
}

/**
 * Check if an error is retryable (5xx, network errors).
 */
function isRetryableError(error: string, nonRetryable: string[]): boolean {
  const errorLower = error.toLowerCase();

  // Check non-retryable patterns
  for (const pattern of nonRetryable) {
    if (errorLower.includes(pattern.toLowerCase())) {
      return false;
    }
  }

  // Retryable patterns: network errors, timeouts, 5xx
  const retryablePatterns = [
    "network",
    "timeout",
    "timed out",
    "fetch failed",
    "500",
    "502",
    "503",
    "504",
    "서버 오류",
    "네트워크 오류",
  ];

  return retryablePatterns.some((p) => errorLower.includes(p));
}

/**
 * Unified hook for managing async operations with:
 * - Progress tracking (via SSE or manual updates)
 * - Cancellation (via AbortController)
 * - Retry with exponential backoff
 *
 * @example
 * ```tsx
 * const { execute, isLoading, progress, error, cancel, retry } = useAsyncOperation({
 *   onSuccess: (data) => console.log('Success:', data),
 *   onError: (err) => console.error('Error:', err),
 * });
 *
 * // Regular JSON request
 * await execute('/api/dimension/1d/generate', { topic: 'sunset' });
 *
 * // SSE streaming request with progress
 * await executeStream('/api/dimension/veo/generate/stream', { prompt: '...' });
 * ```
 */
export function useAsyncOperation<T = unknown>(
  options: UseAsyncOperationOptions<T> = {}
): UseAsyncOperationReturn<T> {
  const {
    onSuccess,
    onError,
    onProgress,
    retryCount = 3,
    retryDelay = 1000,
    nonRetryableErrors = ["400", "401", "402", "403", "404", "크레딧"],
    timeout = 120000, // 2 minutes default
  } = options;

  // State
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [currentRetryCount, setCurrentRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  // Refs for cancellation and retry
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<{
    url: string;
    body: object;
    headers?: Record<string, string>;
    isStream: boolean;
  } | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  /**
   * Update progress and call onProgress callback.
   */
  const updateProgress = useCallback(
    (newProgress: ProgressEvent) => {
      setProgress(newProgress);
      onProgress?.(newProgress);
    },
    [onProgress]
  );

  /**
   * Handle error with proper state updates.
   */
  const handleError = useCallback(
    (err: unknown) => {
      const errorMessage =
        err instanceof Error
          ? err.message
          : typeof err === "string"
            ? err
            : "알 수 없는 오류가 발생했습니다.";

      setError(errorMessage);
      setProgress({
        percent: 0,
        message: errorMessage,
        stage: "error",
      });
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    },
    [onError]
  );

  /**
   * Parse SSE stream and update progress.
   */
  const handleSSEStream = useCallback(
    async (response: Response): Promise<T | null> => {
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("스트림 연결에 실패했습니다.");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let resultData: T | null = null;
      let lastProgressTime = Date.now();
      const STALL_TIMEOUT = 60000; // 60 seconds without progress = stall

      try {
        while (true) {
          const { done, value } = await reader.read();

          // Check for stall (no data for too long)
          if (!done && !value) {
            if (Date.now() - lastProgressTime > STALL_TIMEOUT) {
              throw new Error("연결이 끊어졌습니다. 다시 시도해주세요.");
            }
            continue;
          }

          if (done) {
            // Stream ended without complete event
            if (!resultData) {
              // Check if there's remaining data in buffer
              if (buffer.trim()) {
                console.warn("Stream ended with unparsed data:", buffer);
              }
            }
            break;
          }

          lastProgressTime = Date.now();
          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events (format: "data: {...}\n\n")
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || ""; // Keep incomplete data in buffer

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;

            try {
              const eventData = JSON.parse(line.slice(6)) as SSEEvent;

              if (eventData.type === "progress") {
                updateProgress({
                  percent: eventData.percent,
                  message: eventData.message,
                  stage: (eventData.stage as ProgressEvent["stage"]) || "processing",
                });
              } else if (eventData.type === "complete") {
                resultData = eventData.data as T;
                updateProgress({
                  percent: 100,
                  message: "완료",
                  stage: "complete",
                });
                setData(resultData);
                onSuccess?.(resultData);
              } else if (eventData.type === "error") {
                throw new Error(classifyError(eventData.error));
              }
            } catch (parseError) {
              // Only log if it's not a JSON parse error (could be a real error thrown above)
              if (parseError instanceof SyntaxError) {
                console.warn("Failed to parse SSE event:", line);
              } else {
                throw parseError;
              }
            }
          }
        }
      } catch (err) {
        // Re-throw to be handled by executeStream
        throw err;
      } finally {
        reader.releaseLock();
      }

      return resultData;
    },
    [updateProgress, onSuccess]
  );

  /**
   * Execute a regular JSON POST request.
   */
  const execute = useCallback(
    async (
      url: string,
      body: object,
      headers?: Record<string, string>
    ): Promise<T | null> => {
      // Abort previous request
      abortControllerRef.current?.abort();
      abortControllerRef.current = new AbortController();

      // Store for retry
      lastRequestRef.current = { url, body, headers, isStream: false };

      // Reset state
      setIsLoading(true);
      setError(null);
      setData(null);
      updateProgress({ percent: 1, message: "시작 중...", stage: "starting" });

      // Setup timeout
      const timeoutId = setTimeout(() => {
        abortControllerRef.current?.abort();
      }, timeout);

      let statusCode: number | undefined;

      // Handle FormData vs JSON body
      const isFormData = body instanceof FormData;
      const requestBody = isFormData ? body : JSON.stringify(body);
      const requestHeaders = isFormData
        ? headers // FormData: let browser set Content-Type with boundary
        : { "Content-Type": "application/json", ...headers };

      try {
        const response = await fetch(url, {
          method: "POST",
          body: requestBody,
          headers: requestHeaders,
          signal: abortControllerRef.current.signal,
        });

        statusCode = response.status;

        if (!response.ok) {
          const errorText = await parseErrorResponse(response);
          throw new Error(classifyError(errorText, statusCode));
        }

        updateProgress({ percent: 90, message: "응답 처리 중...", stage: "finalizing" });

        const responseData = (await response.json()) as T;
        setData(responseData);
        updateProgress({ percent: 100, message: "완료", stage: "complete" });
        onSuccess?.(responseData);
        setCurrentRetryCount(0); // Reset retry count on success

        return responseData;
      } catch (err) {
        // Ignore abort errors (intentional cancellation)
        if (err instanceof Error && err.name === "AbortError") {
          // Check if it was a timeout
          const isTimeout = !abortControllerRef.current?.signal.aborted;
          if (isTimeout) {
            handleError(new Error("요청 시간이 초과되었습니다. 다시 시도해주세요."));
          }
          return null;
        }

        // Classify and handle error
        const errorMessage = err instanceof Error ? err.message : String(err);
        handleError(new Error(classifyError(errorMessage, statusCode)));
        return null;
      } finally {
        clearTimeout(timeoutId);
        setIsLoading(false);
      }
    },
    [updateProgress, onSuccess, handleError, timeout]
  );

  /**
   * Execute an SSE streaming POST request with progress updates.
   */
  const executeStream = useCallback(
    async (
      url: string,
      body: object,
      headers?: Record<string, string>
    ): Promise<T | null> => {
      // Abort previous request
      abortControllerRef.current?.abort();
      abortControllerRef.current = new AbortController();

      // Store for retry
      lastRequestRef.current = { url, body, headers, isStream: true };

      // Reset state
      setIsLoading(true);
      setError(null);
      setData(null);
      updateProgress({ percent: 1, message: "시작 중...", stage: "starting" });

      // Setup timeout (longer for streaming - 5 minutes)
      const streamTimeout = Math.max(timeout, 300000);
      const timeoutId = setTimeout(() => {
        abortControllerRef.current?.abort();
      }, streamTimeout);

      let statusCode: number | undefined;
      let wasTimedOut = false;

      try {
        const response = await fetch(url, {
          method: "POST",
          body: JSON.stringify(body),
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
            ...headers,
          },
          signal: abortControllerRef.current.signal,
        });

        statusCode = response.status;

        if (!response.ok) {
          const errorText = await parseErrorResponse(response);
          throw new Error(classifyError(errorText, statusCode));
        }

        // Clear initial timeout once streaming starts
        clearTimeout(timeoutId);

        const contentType = response.headers.get("content-type");
        if (contentType?.includes("text/event-stream")) {
          const result = await handleSSEStream(response);
          setCurrentRetryCount(0); // Reset retry count on success
          return result;
        } else {
          // Fallback to JSON if not SSE
          const responseData = (await response.json()) as T;
          setData(responseData);
          updateProgress({ percent: 100, message: "완료", stage: "complete" });
          onSuccess?.(responseData);
          setCurrentRetryCount(0);
          return responseData;
        }
      } catch (err) {
        // Ignore abort errors (intentional cancellation)
        if (err instanceof Error && err.name === "AbortError") {
          // Check if it was a timeout
          wasTimedOut = !abortControllerRef.current?.signal.aborted;
          if (wasTimedOut) {
            handleError(new Error("요청 시간이 초과되었습니다. 다시 시도해주세요."));
          }
          return null;
        }

        // Classify and handle error
        const errorMessage = err instanceof Error ? err.message : String(err);
        handleError(new Error(classifyError(errorMessage, statusCode)));
        return null;
      } finally {
        clearTimeout(timeoutId);
        setIsLoading(false);
      }
    },
    [updateProgress, handleSSEStream, onSuccess, handleError, timeout]
  );

  /**
   * Cancel the current operation.
   */
  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
    setProgress(null);
    setError(null);
  }, []);

  /**
   * Retry the last failed operation with exponential backoff.
   */
  const retry = useCallback(async (): Promise<T | null> => {
    if (!lastRequestRef.current || currentRetryCount >= retryCount) {
      return null;
    }

    const { url, body, headers, isStream } = lastRequestRef.current;

    // Check if error is retryable
    if (error && !isRetryableError(error, nonRetryableErrors)) {
      return null;
    }

    setIsRetrying(true);
    setError(null);

    // Exponential backoff delay with progress indication
    const delay = retryDelay * Math.pow(2, currentRetryCount);
    const nextAttempt = currentRetryCount + 1;
    updateProgress({
      percent: 0,
      message: `재시도 대기 중... (${nextAttempt}/${retryCount})`,
      stage: "starting",
    });

    // Show countdown during delay
    const startTime = Date.now();
    const updateInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, Math.ceil((delay - elapsed) / 1000));
      updateProgress({
        percent: Math.min(90, (elapsed / delay) * 90),
        message: `${remaining}초 후 재시도... (${nextAttempt}/${retryCount})`,
        stage: "starting",
      });
    }, 100);

    await new Promise((resolve) => setTimeout(resolve, delay));
    clearInterval(updateInterval);

    setCurrentRetryCount(nextAttempt);
    setIsRetrying(false);

    if (isStream) {
      return executeStream(url, body, headers);
    } else {
      return execute(url, body, headers);
    }
  }, [
    currentRetryCount,
    retryCount,
    retryDelay,
    error,
    nonRetryableErrors,
    execute,
    executeStream,
    updateProgress,
  ]);

  /**
   * Reset all state to initial values.
   */
  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
    setProgress(null);
    setError(null);
    setData(null);
    setCurrentRetryCount(0);
    setIsRetrying(false);
    lastRequestRef.current = null;
  }, []);

  /**
   * Check if retry is available.
   */
  const canRetry =
    !!error &&
    !!lastRequestRef.current &&
    currentRetryCount < retryCount &&
    isRetryableError(error, nonRetryableErrors);

  return {
    // State
    isLoading,
    progress,
    error,
    data,

    // Actions
    execute,
    executeStream,
    cancel,
    retry,
    reset,

    // Computed
    canRetry,
    isRetrying,
    currentRetryCount,
  };
}

export default useAsyncOperation;
