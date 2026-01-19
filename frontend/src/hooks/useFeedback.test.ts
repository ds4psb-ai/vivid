/**
 * Phase -1: useFeedback Hook Unit Tests
 *
 * Tests for P6 RAG Feedback API integration hook
 */
import { describe, test, expect, beforeEach, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import {
  useFeedback,
  createSourceClickHandler,
  createTextCopyHandler,
  trackSessionEnd,
} from "./useFeedback";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("useFeedback", () => {
  const TEST_RESPONSE_ID = "test-response-123";

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("submitExplicit", () => {
    test("submits positive feedback successfully", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const onSuccess = vi.fn();
      const { result } = renderHook(() =>
        useFeedback({
          responseId: TEST_RESPONSE_ID,
          onSuccess,
        })
      );

      expect(result.current.hasSubmitted).toBe(false);
      expect(result.current.isSubmitting).toBe(false);

      await act(async () => {
        await result.current.submitExplicit("positive", 5, "Great response!");
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/rag/feedback/explicit"),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            response_id: TEST_RESPONSE_ID,
            feedback_type: "thumbs_up",
            rating: 5,
            comment: "Great response!",
          }),
        })
      );

      expect(result.current.hasSubmitted).toBe(true);
      expect(onSuccess).toHaveBeenCalled();
    });

    test("submits negative feedback successfully", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.submitExplicit("negative");
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/rag/feedback/explicit"),
        expect.objectContaining({
          body: JSON.stringify({
            response_id: TEST_RESPONSE_ID,
            feedback_type: "thumbs_down",
          }),
        })
      );

      expect(result.current.hasSubmitted).toBe(true);
    });

    test("handles submission error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: "Server error" }),
      });

      const onError = vi.fn();
      const { result } = renderHook(() =>
        useFeedback({
          responseId: TEST_RESPONSE_ID,
          onError,
        })
      );

      // The hook throws the error, so we need to catch it
      let thrownError: Error | null = null;
      await act(async () => {
        try {
          await result.current.submitExplicit("positive");
        } catch (err) {
          thrownError = err as Error;
        }
      });

      expect(thrownError).not.toBeNull();
      expect(thrownError!.message).toBe("Server error");
      expect(result.current.error?.message).toBe("Server error");
      expect(onError).toHaveBeenCalled();
      expect(result.current.hasSubmitted).toBe(false);
    });

    test("prevents duplicate submissions", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.submitExplicit("positive");
      });

      // Try to submit again
      await act(async () => {
        await result.current.submitExplicit("positive");
      });

      // Should only have been called once
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test("ignores invalid rating values", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.submitExplicit("positive", 10); // Invalid rating
      });

      // Rating should not be included
      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(callBody.rating).toBeUndefined();
    });
  });

  describe("trackImplicit", () => {
    test("tracks source click", async () => {
      mockFetch.mockResolvedValueOnce({ ok: true });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.trackImplicit("source_click", {
          source_id: "doc-123",
          source_index: 0,
        });
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/rag/feedback/implicit"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            response_id: TEST_RESPONSE_ID,
            event_type: "source_click",
            source_id: "doc-123",
            source_index: 0,
          }),
        })
      );
    });

    test("prevents duplicate implicit events", async () => {
      mockFetch.mockResolvedValue({ ok: true });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.trackImplicit("source_click", {
          source_id: "doc-123",
          source_index: 0,
        });
      });

      // Try to track the same event again
      await act(async () => {
        await result.current.trackImplicit("source_click", {
          source_id: "doc-123",
          source_index: 0,
        });
      });

      // Should only have been called once
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test("allows multiple session_end events", async () => {
      mockFetch.mockResolvedValue({ ok: true });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.trackImplicit("session_end", { duration_ms: 1000 });
      });

      await act(async () => {
        await result.current.trackImplicit("session_end", { duration_ms: 2000 });
      });

      // session_end should allow duplicates
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    test("does not throw on implicit tracking error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));
      const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      // Should not throw
      await act(async () => {
        await result.current.trackImplicit("source_click", {
          source_id: "doc-123",
          source_index: 0,
        });
      });

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe("state management", () => {
    test("clearError clears error state", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: "Error" }),
      });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        try {
          await result.current.submitExplicit("positive");
        } catch {
          // Expected - the hook rethrows the error
        }
      });

      expect(result.current.error).not.toBeNull();

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    test("reset clears all state", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      const { result } = renderHook(() =>
        useFeedback({ responseId: TEST_RESPONSE_ID })
      );

      await act(async () => {
        await result.current.submitExplicit("positive");
      });

      expect(result.current.hasSubmitted).toBe(true);

      act(() => {
        result.current.reset();
      });

      expect(result.current.hasSubmitted).toBe(false);
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });
});

describe("Utility Functions", () => {
  const mockTrackImplicit = vi.fn();

  beforeEach(() => {
    mockTrackImplicit.mockClear();
  });

  test("createSourceClickHandler creates click handler", () => {
    const handler = createSourceClickHandler(mockTrackImplicit, "doc-123", 2);
    handler();

    expect(mockTrackImplicit).toHaveBeenCalledWith("source_click", {
      source_id: "doc-123",
      source_index: 2,
    });
  });

  test("createTextCopyHandler creates copy handler", () => {
    const handler = createTextCopyHandler(mockTrackImplicit, 150);
    handler();

    expect(mockTrackImplicit).toHaveBeenCalledWith("text_copy", {
      copied_length: 150,
    });
  });

  test("trackSessionEnd tracks with duration", () => {
    const startTime = Date.now() - 5000; // 5 seconds ago
    trackSessionEnd(mockTrackImplicit, startTime);

    expect(mockTrackImplicit).toHaveBeenCalledWith("session_end", {
      duration_ms: expect.any(Number),
    });

    const calledDuration = mockTrackImplicit.mock.calls[0][1].duration_ms;
    expect(calledDuration).toBeGreaterThanOrEqual(5000);
    expect(calledDuration).toBeLessThan(6000);
  });
});
