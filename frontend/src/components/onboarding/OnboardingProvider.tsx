"use client";

/**
 * OnboardingProvider - Guided walkthrough system
 *
 * Provides first-time user onboarding with:
 * - Step-by-step highlights
 * - Tooltips for key features
 * - Progress tracking
 * - Skip/complete persistence
 *
 * 2026 UX Pattern: Contextual onboarding without blocking
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { OnboardingOverlay } from "./OnboardingOverlay";

// =============================================================================
// Types
// =============================================================================

export interface OnboardingStep {
  /** Unique step identifier */
  id: string;
  /** CSS selector for target element (data-onboarding attribute) */
  target: string;
  /** Step title */
  title: string;
  /** Step description */
  description: string;
  /** Tooltip position relative to target */
  position?: "top" | "bottom" | "left" | "right";
  /** Optional action button text */
  action?: string;
  /** Optional action callback */
  onAction?: () => void;
}

export interface OnboardingContextValue {
  /** Whether onboarding is currently active */
  isActive: boolean;
  /** Current step index */
  currentStep: number;
  /** Total number of steps */
  totalSteps: number;
  /** Current step data */
  step: OnboardingStep | null;
  /** Start onboarding */
  start: () => void;
  /** Go to next step */
  next: () => void;
  /** Go to previous step */
  prev: () => void;
  /** Skip onboarding */
  skip: () => void;
  /** Complete onboarding */
  complete: () => void;
  /** Reset onboarding (for testing) */
  reset: () => void;
}

// =============================================================================
// Default Steps
// =============================================================================

export const DEFAULT_ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: "welcome",
    target: "[data-onboarding='welcome']",
    title: "Crebit Studio에 오신 것을 환영합니다!",
    description: "AI 기반 콘텐츠 생성 플랫폼을 시작해볼까요?",
    position: "bottom",
  },
  {
    id: "workflow-progress",
    target: "[data-onboarding='workflow-progress']",
    title: "워크플로우 진행 상황",
    description: "DNA Lab → Story Engine → Production 순서로 진행됩니다. 각 단계에서 생성한 결과가 다음 단계로 자동 전달됩니다.",
    position: "bottom",
  },
  {
    id: "chain-sidebar",
    target: "[data-onboarding='chain-sidebar']",
    title: "체인 데이터",
    description: "이전 단계의 결과가 여기에 표시됩니다. 클릭하면 상세 내용을 확인할 수 있습니다.",
    position: "left",
  },
  {
    id: "dimension-panel",
    target: "[data-onboarding='dimension-panel']",
    title: "Dimension 패널",
    description: "각 도구에서 프롬프트를 입력하고 AI 결과를 생성합니다. 생성 버튼을 눌러 시작하세요.",
    position: "right",
  },
  {
    id: "credits",
    target: "[data-onboarding='credits']",
    title: "크레딧 시스템",
    description: "각 생성 작업은 크레딧을 소모합니다. 크레딧 잔액을 여기서 확인하세요.",
    position: "bottom",
  },
];

// =============================================================================
// Context
// =============================================================================

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function useOnboarding(): OnboardingContextValue {
  const context = useContext(OnboardingContext);
  if (!context) {
    // Return no-op context if not wrapped
    return {
      isActive: false,
      currentStep: 0,
      totalSteps: 0,
      step: null,
      start: () => {},
      next: () => {},
      prev: () => {},
      skip: () => {},
      complete: () => {},
      reset: () => {},
    };
  }
  return context;
}

// =============================================================================
// Provider
// =============================================================================

const STORAGE_KEY = "crebit_onboarding_complete";

export interface OnboardingProviderProps {
  children: React.ReactNode;
  /** Custom steps (optional, uses DEFAULT_ONBOARDING_STEPS if not provided) */
  steps?: OnboardingStep[];
  /** Onboarding ID for storage (optional) */
  id?: string;
  /** Auto-start for first-time users (default: true) */
  autoStart?: boolean;
}

export function OnboardingProvider({
  children,
  steps = DEFAULT_ONBOARDING_STEPS,
  id = "default",
  autoStart = true,
}: OnboardingProviderProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isComplete, setIsComplete] = useState(true); // Default to complete (no overlay)

  const storageKey = `${STORAGE_KEY}_${id}`;

  // Check completion status on mount
  useEffect(() => {
    if (typeof window === "undefined") return;

    const completed = localStorage.getItem(storageKey);
    if (completed) {
      setIsComplete(true);
    } else if (autoStart) {
      // Delay auto-start to allow page to render
      const timer = setTimeout(() => {
        setIsComplete(false);
        setIsActive(true);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [storageKey, autoStart]);

  const start = useCallback(() => {
    setCurrentStep(0);
    setIsActive(true);
    setIsComplete(false);
  }, []);

  const next = useCallback(() => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((s) => s + 1);
    } else {
      // Last step - complete
      setIsActive(false);
      setIsComplete(true);
      localStorage.setItem(storageKey, "true");
    }
  }, [currentStep, steps.length, storageKey]);

  const prev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((s) => s - 1);
    }
  }, [currentStep]);

  const skip = useCallback(() => {
    setIsActive(false);
    setIsComplete(true);
    localStorage.setItem(storageKey, "true");
  }, [storageKey]);

  const complete = useCallback(() => {
    setIsActive(false);
    setIsComplete(true);
    localStorage.setItem(storageKey, "true");
  }, [storageKey]);

  const reset = useCallback(() => {
    localStorage.removeItem(storageKey);
    setIsComplete(false);
    setCurrentStep(0);
    setIsActive(true);
  }, [storageKey]);

  const contextValue: OnboardingContextValue = {
    isActive,
    currentStep,
    totalSteps: steps.length,
    step: steps[currentStep] || null,
    start,
    next,
    prev,
    skip,
    complete,
    reset,
  };

  return (
    <OnboardingContext.Provider value={contextValue}>
      {children}
      {isActive && !isComplete && (
        <OnboardingOverlay
          steps={steps}
          currentStep={currentStep}
          onNext={next}
          onPrev={prev}
          onSkip={skip}
          onComplete={complete}
        />
      )}
    </OnboardingContext.Provider>
  );
}
