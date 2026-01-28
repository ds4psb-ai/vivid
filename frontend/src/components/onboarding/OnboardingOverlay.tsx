"use client";

/**
 * OnboardingOverlay - Visual overlay for onboarding steps
 *
 * Highlights target elements and shows tooltips for each step.
 * Uses spotlight effect to focus attention.
 *
 * 2026 UX Pattern: Non-blocking contextual guidance
 */

import { useEffect, useState, useRef } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";
import type { OnboardingStep } from "./OnboardingProvider";

export interface OnboardingOverlayProps {
  steps: OnboardingStep[];
  currentStep: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onComplete: () => void;
}

interface TargetRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

export function OnboardingOverlay({
  steps,
  currentStep,
  onNext,
  onPrev,
  onSkip,
  onComplete,
}: OnboardingOverlayProps) {
  const prefersReducedMotion = useReducedMotion();
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const step = steps[currentStep];
  const isFirst = currentStep === 0;
  const isLast = currentStep === steps.length - 1;

  // Find and highlight target element
  useEffect(() => {
    if (!step?.target) {
      setTargetRect(null);
      return;
    }

    const findTarget = () => {
      const target = document.querySelector(step.target);
      if (target) {
        const rect = target.getBoundingClientRect();
        setTargetRect({
          top: rect.top + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width,
          height: rect.height,
        });

        // Scroll target into view
        target.scrollIntoView({
          behavior: prefersReducedMotion ? "auto" : "smooth",
          block: "center",
        });
      } else {
        setTargetRect(null);
      }
    };

    // Initial find
    findTarget();

    // Reposition on resize
    window.addEventListener("resize", findTarget);
    return () => window.removeEventListener("resize", findTarget);
  }, [step?.target, prefersReducedMotion]);

  // Calculate tooltip position
  const getTooltipStyle = (): React.CSSProperties => {
    if (!targetRect || !step) return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };

    const padding = 16;
    const tooltipWidth = 320;
    const tooltipHeight = 200; // Approximate

    switch (step.position) {
      case "top":
        return {
          top: targetRect.top - tooltipHeight - padding,
          left: targetRect.left + targetRect.width / 2,
          transform: "translateX(-50%)",
        };
      case "bottom":
        return {
          top: targetRect.top + targetRect.height + padding,
          left: targetRect.left + targetRect.width / 2,
          transform: "translateX(-50%)",
        };
      case "left":
        return {
          top: targetRect.top + targetRect.height / 2,
          left: targetRect.left - tooltipWidth - padding,
          transform: "translateY(-50%)",
        };
      case "right":
        return {
          top: targetRect.top + targetRect.height / 2,
          left: targetRect.left + targetRect.width + padding,
          transform: "translateY(-50%)",
        };
      default:
        return {
          top: targetRect.top + targetRect.height + padding,
          left: targetRect.left + targetRect.width / 2,
          transform: "translateX(-50%)",
        };
    }
  };

  return (
    <div className="fixed inset-0 z-[200]">
      {/* Semi-transparent overlay with spotlight */}
      <svg className="absolute inset-0 w-full h-full pointer-events-auto">
        <defs>
          <mask id="spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {targetRect && (
              <rect
                x={targetRect.left - 8}
                y={targetRect.top - 8}
                width={targetRect.width + 16}
                height={targetRect.height + 16}
                rx="12"
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(0, 0, 0, 0.75)"
          mask="url(#spotlight-mask)"
          onClick={onSkip}
        />
      </svg>

      {/* Highlight border around target */}
      {targetRect && (
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
          animate={prefersReducedMotion ? {} : { opacity: 1, scale: 1 }}
          className="absolute pointer-events-none border-2 border-emerald-400 rounded-xl"
          style={{
            top: targetRect.top - 8,
            left: targetRect.left - 8,
            width: targetRect.width + 16,
            height: targetRect.height + 16,
            boxShadow: "0 0 0 9999px transparent, 0 0 20px rgba(16, 185, 129, 0.5)",
          }}
        />
      )}

      {/* Tooltip */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          ref={tooltipRef}
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
          animate={prefersReducedMotion ? {} : { opacity: 1, y: 0 }}
          exit={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
          className="absolute w-80 bg-[var(--surface-0)] border border-[var(--border-subtle)] rounded-xl shadow-2xl p-4 pointer-events-auto"
          style={getTooltipStyle()}
        >
          {/* Close button */}
          <button
            onClick={onSkip}
            className="absolute top-3 right-3 p-1 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="온보딩 건너뛰기"
          >
            <X className="w-4 h-4 text-[var(--fg-subtle)]" />
          </button>

          {/* Content */}
          <div className="pr-6">
            <h3 className="text-base font-semibold text-[var(--fg-0)] mb-2">
              {step?.title}
            </h3>
            <p className="text-sm text-[var(--fg-muted)] mb-4">
              {step?.description}
            </p>
          </div>

          {/* Progress dots */}
          <div className="flex items-center justify-center gap-1.5 mb-4">
            {steps.map((_, i) => (
              <div
                key={i}
                className={cn(
                  "w-2 h-2 rounded-full transition-colors",
                  i === currentStep ? "bg-emerald-500" : "bg-white/20"
                )}
              />
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between gap-3">
            <button
              onClick={onSkip}
              className="text-sm text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors"
            >
              건너뛰기
            </button>

            <div className="flex items-center gap-2">
              {!isFirst && (
                <button
                  onClick={onPrev}
                  className="flex items-center gap-1 px-3 py-2 text-sm text-[var(--fg-subtle)] hover:text-[var(--fg-0)] hover:bg-white/5 rounded-lg transition-colors min-h-[44px]"
                >
                  <ChevronLeft className="w-4 h-4" />
                  이전
                </button>
              )}
              <button
                onClick={isLast ? onComplete : onNext}
                className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors min-h-[44px]"
              >
                {isLast ? "완료" : "다음"}
                {!isLast && <ChevronRight className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
