/**
 * useDNALabWorkflow Hook Tests
 *
 * Phase P2-1: Unit tests for DNA Lab workflow state management
 */

import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDNALabWorkflow } from "./useDNALabWorkflow";
import {
  DNA_LAB_STEPS,
  DNA_LAB_DEFAULT_STEP,
  DNA_LAB_INPUT_MAP,
  type DNALabStepId,
} from "../constants";

// Mock Next.js navigation hooks
const mockPush = vi.fn();
const mockGet = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => ({
    get: mockGet,
    toString: () => "",
  }),
  usePathname: () => "/dna-lab",
}));

// Mock DimensionChainContext
const mockSetChainData = vi.fn();
const mockChainData: Record<string, { output: Record<string, unknown> }> = {};

vi.mock("@/contexts/DimensionChainContext", () => ({
  useDimensionChainOptional: () => ({
    chainData: mockChainData,
    setChainData: mockSetChainData,
  }),
}));

describe("useDNALabWorkflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockReturnValue(null);
    Object.keys(mockChainData).forEach((key) => delete mockChainData[key]);
  });

  describe("Initial State", () => {
    it("returns default step when no URL parameter", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.currentStepId).toBe(DNA_LAB_DEFAULT_STEP);
      expect(result.current.currentStep.id).toBe(DNA_LAB_DEFAULT_STEP);
    });

    it("returns correct step from URL parameter", () => {
      mockGet.mockReturnValue("mirror");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.currentStepId).toBe("mirror");
      expect(result.current.currentStep.id).toBe("mirror");
    });

    it("falls back to default step for invalid URL parameter", () => {
      mockGet.mockReturnValue("invalid-step");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.currentStepId).toBe(DNA_LAB_DEFAULT_STEP);
    });

    it("initializes all steps with pending status when no data", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      const pendingSteps = result.current.steps.filter(
        (s) => s.status === "pending" || s.status === "active"
      );
      expect(pendingSteps.length).toBe(DNA_LAB_STEPS.length);
    });
  });

  describe("Step Navigation", () => {
    it("goToStep navigates with correct URL parameter", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      act(() => {
        result.current.goToStep("mirror");
      });

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("step=mirror")
      );
    });

    it("goToNext moves to next step", () => {
      mockGet.mockReturnValue("analysis");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.nextStep?.id).toBe("mirror");
      expect(result.current.canGoNext).toBe(true);

      act(() => {
        result.current.goToNext();
      });

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("step=mirror")
      );
    });

    it("goToPrevious moves to previous step", () => {
      mockGet.mockReturnValue("mirror");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.previousStep?.id).toBe("analysis");
      expect(result.current.canGoPrevious).toBe(true);

      act(() => {
        result.current.goToPrevious();
      });

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("step=analysis")
      );
    });

    it("cannot go previous from first step", () => {
      mockGet.mockReturnValue("analysis");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.canGoPrevious).toBe(false);
      expect(result.current.previousStep).toBeUndefined();
    });

    it("cannot go next from last step", () => {
      mockGet.mockReturnValue("qc");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.canGoNext).toBe(false);
      expect(result.current.nextStep).toBeUndefined();
    });
  });

  describe("Step Status", () => {
    it("marks step as active when it is current", () => {
      mockGet.mockReturnValue("mirror");

      const { result } = renderHook(() => useDNALabWorkflow());

      const mirrorState = result.current.steps.find(
        (s) => s.step.id === "mirror"
      );
      expect(mirrorState?.status).toBe("active");
    });

    it("marks step as completed when it has data", () => {
      mockGet.mockReturnValue("mirror");
      mockChainData["analysis"] = { output: { logicVector: {} } };

      const { result } = renderHook(() => useDNALabWorkflow());

      const analysisState = result.current.steps.find(
        (s) => s.step.id === "analysis"
      );
      expect(analysisState?.status).toBe("completed");
    });

    it("calculates completedSteps correctly", () => {
      // Analysis step's dimensionKey is "analysis", not a different key
      // The hook maps chainData[step.dimensionKey]?.output to step data
      mockChainData["analysis"] = { output: { logicVector: {} } };

      // Switch to mirror step to see analysis as completed (not active)
      mockGet.mockReturnValue("mirror");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.completedSteps).toContain("analysis");
    });

    it("calculates completionPercentage correctly", () => {
      // With 3 steps total, 1 completed = 33%
      mockChainData["analysis"] = { output: { data: {} } };
      // Need to be on a different step for analysis to show as "completed" not "active"
      mockGet.mockReturnValue("mirror");

      const { result } = renderHook(() => useDNALabWorkflow());

      expect(result.current.completionPercentage).toBe(33);
    });
  });

  describe("Chain Data Integration", () => {
    it("getStepData returns data for step", () => {
      mockChainData["analysis"] = { output: { logicVector: { key: "value" } } };

      const { result } = renderHook(() => useDNALabWorkflow());

      const data = result.current.getStepData("analysis");
      expect(data).toEqual({ logicVector: { key: "value" } });
    });

    it("getStepData returns undefined for step without data", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      const data = result.current.getStepData("mirror");
      expect(data).toBeUndefined();
    });

    it("getInputDataForStep returns data from dependency steps", () => {
      mockChainData["analysis"] = { output: { logicVector: {} } };

      const { result } = renderHook(() => useDNALabWorkflow());

      const inputData = result.current.getInputDataForStep("mirror");
      expect(inputData["analysis"]).toBeDefined();
    });

    it("markStepComplete stores data in chain context", () => {
      const { result } = renderHook(() => useDNALabWorkflow());
      const testData = { result: "test" };

      act(() => {
        result.current.markStepComplete("analysis", testData);
      });

      expect(mockSetChainData).toHaveBeenCalledWith(
        "analysis", // dimensionKey
        testData,
        expect.any(String), // summary
        [] // evidence refs
      );
    });
  });

  describe("Missing Inputs Detection", () => {
    it("getMissingInputsForStep returns empty array for analysis", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      const missing = result.current.getMissingInputsForStep("analysis");
      expect(missing).toEqual([]);
    });

    it("getMissingInputsForStep returns analysis when not present", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      const missing = result.current.getMissingInputsForStep("mirror");
      expect(missing).toContain("analysis");
    });

    it("getMissingInputsForStep returns empty when deps satisfied", () => {
      mockChainData["analysis"] = { output: { data: {} } };

      const { result } = renderHook(() => useDNALabWorkflow());

      const missing = result.current.getMissingInputsForStep("mirror");
      expect(missing).toEqual([]);
    });
  });

  describe("AI Inference Support", () => {
    it("canInferForStep returns true for mirror step with missing inputs", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      // Mirror has canInferInput: true in constants
      const canInfer = result.current.canInferForStep("mirror");
      expect(canInfer).toBe(true);
    });

    it("canInferForStep returns false for analysis step", () => {
      const { result } = renderHook(() => useDNALabWorkflow());

      // Analysis has canInferInput: false
      const canInfer = result.current.canInferForStep("analysis");
      expect(canInfer).toBe(false);
    });

    it("canInferForStep returns false when all inputs present", () => {
      mockChainData["analysis"] = { output: { data: {} } };

      const { result } = renderHook(() => useDNALabWorkflow());

      // Mirror has inputs satisfied, so no inference needed
      const canInfer = result.current.canInferForStep("mirror");
      expect(canInfer).toBe(false);
    });
  });

  describe("Step Index Calculation", () => {
    it("returns correct index for each step", () => {
      const steps: DNALabStepId[] = ["analysis", "mirror", "qc"];

      steps.forEach((stepId, expectedIndex) => {
        mockGet.mockReturnValue(stepId);
        const { result } = renderHook(() => useDNALabWorkflow());

        expect(result.current.currentStepIndex).toBe(expectedIndex);
      });
    });
  });
});
