"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { WORKFLOW_STEPS, getWorkflowStepIndex, getTheme } from "./constants";
import type { WorkflowProgressProps } from "./types";

/**
 * WorkflowProgress - 3-step workflow navigation
 *
 * Features:
 * - Highlights current app
 * - Shows previous/next navigation
 * - Theme-colored active state
 * - Hidden on mobile (md:flex)
 */
export function WorkflowProgress({ currentAppId }: WorkflowProgressProps) {
  const currentIndex = getWorkflowStepIndex(currentAppId);
  const theme = getTheme(currentAppId);

  return (
    <div className="hidden md:flex items-center justify-center gap-2 py-2 px-4 border-b bg-black/20 border-white/5">
      {WORKFLOW_STEPS.map((step, index) => {
        const isActive = step.id === currentAppId;
        const isPast = index < currentIndex;
        const stepTheme = getTheme(step.id);

        return (
          <div key={step.id} className="flex items-center">
            {/* Step Link */}
            <Link
              href={step.href}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all
                ${
                  isActive
                    ? "bg-white/10 text-white font-medium"
                    : isPast
                      ? "text-white/60 hover:text-white/80"
                      : "text-white/40 hover:text-white/60"
                }
              `}
              style={
                isActive
                  ? {
                      boxShadow: `0 0 12px ${theme.glowColor}`,
                      borderColor: `oklch(0.64 0.18 ${theme.hue} / 0.3)`,
                    }
                  : undefined
              }
            >
              {/* Step Number */}
              <span
                className={`
                  w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold
                  ${isActive ? "bg-white/20" : isPast ? "bg-white/10" : "bg-white/5"}
                `}
                style={
                  isActive
                    ? { backgroundColor: `oklch(0.64 0.18 ${stepTheme.hue} / 0.3)` }
                    : undefined
                }
              >
                {index + 1}
              </span>

              {/* Step Label */}
              <span>{step.label}</span>
            </Link>

            {/* Chevron Separator */}
            {index < WORKFLOW_STEPS.length - 1 && (
              <ChevronRight className="w-4 h-4 text-white/20 mx-1" />
            )}
          </div>
        );
      })}
    </div>
  );
}
