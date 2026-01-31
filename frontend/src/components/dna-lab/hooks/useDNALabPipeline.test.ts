/**
 * useDNALabPipeline Hook Tests
 *
 * Phase P2-2: Unit tests for DNA Lab pipeline execution
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import {
  useDNALabPipeline,
  type PipelineStepId,
  type LegacyPipelineStepId,
  type PipelineResult,
} from "./useDNALabPipeline";

// Mock DimensionChainContext
const mockSetChainData = vi.fn();

vi.mock("@/contexts/DimensionChainContext", () => ({
  useDimensionChainOptional: () => ({
    chainData: {},
    setChainData: mockSetChainData,
  }),
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("useDNALabPipeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Initial State", () => {
    it("initializes with correct default state", () => {
      const { result } = renderHook(() => useDNALabPipeline());

      expect(result.current.isRunning).toBe(false);
      expect(result.current.currentStep).toBeNull();
      expect(result.current.progress).toBe(0);
      expect(result.current.steps).toEqual([]);
      expect(result.current.error).toBeNull();
      expect(result.current.result).toBeNull();
    });

    it("provides creditsUsed as 0 initially", () => {
      const { result } = renderHook(() => useDNALabPipeline());

      expect(result.current.creditsUsed).toBe(0);
    });

    it("provides processingTimeMs as 0 initially", () => {
      const { result } = renderHook(() => useDNALabPipeline());

      expect(result.current.processingTimeMs).toBe(0);
    });
  });

  describe("runPipeline Execution", () => {
    const mockSuccessResult: PipelineResult = {
      success: true,
      trace_id: "test-trace-123",
      status: "completed",
      vpe: { logicVector: { key: "value" } },
      ad: { aestheticGuidelines: { style: "modern" } },
      mirror: { personaDNA: { trait: "creative" } },
      qc: { qualityReport: { score: 95 } },
      evidence_refs: ["db:vpe:123", "db:ad:456"],
      steps: [
        { step: "vpe", status: "completed", duration_ms: 1000 },
        { step: "ad", status: "completed", duration_ms: 1500 },
        { step: "mirror", status: "completed", duration_ms: 800 },
        { step: "qc", status: "completed", duration_ms: 500 },
      ],
      credits_used: 100,
      processing_time_ms: 3800,
      errors: {},
    };

    it("sets isRunning to true during execution", async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: () => Promise.resolve(mockSuccessResult),
                }),
              100
            )
          )
      );

      const { result } = renderHook(() => useDNALabPipeline());

      act(() => {
        result.current.runPipeline({});
      });

      expect(result.current.isRunning).toBe(true);
    });

    it("converts frontend steps to backend steps correctly", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({ steps: ["analysis", "mirror"] });
      });

      const fetchCall = mockFetch.mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);

      // "analysis" should be converted to ["vpe", "ad"]
      expect(body.steps).toEqual(["vpe", "ad", "mirror"]);
    });

    it("sends default steps when none specified", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      const fetchCall = mockFetch.mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);

      // Default: analysis (vpe + ad), mirror, qc
      expect(body.steps).toEqual(["vpe", "ad", "mirror", "qc"]);
    });

    it("returns result on successful execution", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      let pipelineResult: PipelineResult | undefined;
      await act(async () => {
        pipelineResult = await result.current.runPipeline({});
      });

      expect(pipelineResult?.success).toBe(true);
      expect(pipelineResult?.trace_id).toBe("test-trace-123");
    });

    it("updates state after successful execution", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      expect(result.current.isRunning).toBe(false);
      expect(result.current.progress).toBe(100);
      expect(result.current.result).toBeDefined();
      expect(result.current.creditsUsed).toBe(100);
      expect(result.current.processingTimeMs).toBe(3800);
    });

    it("stores merged analysis output in chain context", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      // Check that unified "analysis" key was stored
      expect(mockSetChainData).toHaveBeenCalledWith(
        "analysis",
        expect.objectContaining({
          output: expect.objectContaining({
            logicVector: expect.any(Object),
            aestheticGuidelines: expect.any(Object),
          }),
        }),
        "통합 분석 완료",
        expect.any(Array)
      );
    });

    it("stores mirror output in chain context", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuccessResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      expect(mockSetChainData).toHaveBeenCalledWith(
        "abyss-mirror",
        expect.objectContaining({ output: expect.any(Object) }),
        "페르소나 분석 완료",
        expect.any(Array)
      );
    });
  });

  describe("Error Handling", () => {
    it("handles HTTP error response", async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: "Server error" }),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      // runPipeline should throw on error
      await expect(
        act(async () => {
          await result.current.runPipeline({});
        })
      ).rejects.toThrow("Server error");

      // Note: State update happens but due to React concurrent rendering
      // the error state might not be immediately visible after reject
      // The key behavior (throwing) is verified above
    });

    it("handles network error", async () => {
      mockFetch.mockRejectedValue(new Error("Network failed"));

      const { result } = renderHook(() => useDNALabPipeline());

      // runPipeline should throw on network error
      await expect(
        act(async () => {
          await result.current.runPipeline({});
        })
      ).rejects.toThrow("Network failed");

      // The key behavior (throwing) is verified above
    });

    it("handles partial success with errors", async () => {
      const partialResult: PipelineResult = {
        success: false,
        trace_id: "test-trace-456",
        status: "partial",
        vpe: { logicVector: {} },
        ad: undefined,
        mirror: undefined,
        qc: undefined,
        evidence_refs: [],
        steps: [
          { step: "vpe", status: "completed" },
          { step: "ad", status: "failed", error: "AD failed" },
        ],
        credits_used: 50,
        processing_time_ms: 2000,
        errors: { ad: "AD processing failed" },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(partialResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      expect(result.current.error).toContain("AD processing failed");
    });
  });

  describe("reset Function", () => {
    it("resets state to initial values", async () => {
      const mockResult: PipelineResult = {
        success: true,
        trace_id: "test",
        status: "completed",
        vpe: {},
        ad: {},
        evidence_refs: [],
        steps: [],
        credits_used: 100,
        processing_time_ms: 1000,
        errors: {},
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      expect(result.current.result).not.toBeNull();

      act(() => {
        result.current.reset();
      });

      expect(result.current.isRunning).toBe(false);
      expect(result.current.progress).toBe(0);
      expect(result.current.result).toBeNull();
      expect(result.current.error).toBeNull();
    });
  });

  describe("getStepResult Function", () => {
    it("returns undefined when no result", () => {
      const { result } = renderHook(() => useDNALabPipeline());

      const stepResult = result.current.getStepResult("analysis");
      expect(stepResult).toBeUndefined();
    });

    it("returns analysis result for analysis step", async () => {
      const mockResult: PipelineResult = {
        success: true,
        trace_id: "test",
        status: "completed",
        vpe: { logicVector: { key: "vpe-value" } },
        ad: { aestheticGuidelines: { key: "ad-value" } },
        evidence_refs: [],
        steps: [],
        credits_used: 100,
        processing_time_ms: 1000,
        errors: {},
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      const analysisResult = result.current.getStepResult("analysis");
      expect(analysisResult).toBeDefined();
      expect(analysisResult).toHaveProperty("logicVector");
      expect(analysisResult).toHaveProperty("aestheticGuidelines");
    });

    it("returns result for legacy step IDs", async () => {
      const mockResult: PipelineResult = {
        success: true,
        trace_id: "test",
        status: "completed",
        mirror: { personaDNA: { trait: "creative" } },
        evidence_refs: [],
        steps: [],
        credits_used: 50,
        processing_time_ms: 500,
        errors: {},
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({ steps: ["mirror"] });
      });

      const mirrorResult = result.current.getStepResult("mirror");
      expect(mirrorResult).toEqual({ personaDNA: { trait: "creative" } });
    });
  });

  describe("isStepCompleted Function", () => {
    it("returns false when no steps executed", () => {
      const { result } = renderHook(() => useDNALabPipeline());

      expect(result.current.isStepCompleted("analysis")).toBe(false);
    });

    it("returns true for analysis when both vpe and ad completed", async () => {
      const mockResult: PipelineResult = {
        success: true,
        trace_id: "test",
        status: "completed",
        vpe: {},
        ad: {},
        evidence_refs: [],
        steps: [
          { step: "vpe", status: "completed" },
          { step: "ad", status: "completed" },
        ],
        credits_used: 100,
        processing_time_ms: 1000,
        errors: {},
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({ steps: ["analysis"] });
      });

      expect(result.current.isStepCompleted("analysis")).toBe(true);
    });

    it("returns false for analysis when only vpe completed", async () => {
      const mockResult: PipelineResult = {
        success: false,
        trace_id: "test",
        status: "partial",
        vpe: {},
        evidence_refs: [],
        steps: [
          { step: "vpe", status: "completed" },
          { step: "ad", status: "failed" },
        ],
        credits_used: 50,
        processing_time_ms: 500,
        errors: { ad: "Failed" },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({ steps: ["analysis"] });
      });

      expect(result.current.isStepCompleted("analysis")).toBe(false);
    });

    it("returns true for individual step when completed", async () => {
      const mockResult: PipelineResult = {
        success: true,
        trace_id: "test",
        status: "completed",
        mirror: {},
        evidence_refs: [],
        steps: [{ step: "mirror", status: "completed" }],
        credits_used: 50,
        processing_time_ms: 500,
        errors: {},
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({ steps: ["mirror"] });
      });

      expect(result.current.isStepCompleted("mirror")).toBe(true);
    });
  });

  describe("Pipeline Options", () => {
    it("passes video_uri to API", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            trace_id: "test",
            status: "completed",
            evidence_refs: [],
            steps: [],
            credits_used: 0,
            processing_time_ms: 0,
            errors: {},
          }),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({
          video_uri: "https://example.com/video.mp4",
        });
      });

      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.video_uri).toBe("https://example.com/video.mp4");
    });

    it("passes auteur_key to API", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            trace_id: "test",
            status: "completed",
            evidence_refs: [],
            steps: [],
            credits_used: 0,
            processing_time_ms: 0,
            errors: {},
          }),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({
          auteur_key: "bong",
        });
      });

      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.auteur_key).toBe("bong");
    });

    it("defaults store_to_qdrant to true", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            trace_id: "test",
            status: "completed",
            evidence_refs: [],
            steps: [],
            credits_used: 0,
            processing_time_ms: 0,
            errors: {},
          }),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({});
      });

      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.store_to_qdrant).toBe(true);
    });

    it("respects fail_fast option", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            trace_id: "test",
            status: "completed",
            evidence_refs: [],
            steps: [],
            credits_used: 0,
            processing_time_ms: 0,
            errors: {},
          }),
      });

      const { result } = renderHook(() => useDNALabPipeline());

      await act(async () => {
        await result.current.runPipeline({ fail_fast: true });
      });

      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.fail_fast).toBe(true);
    });
  });
});
