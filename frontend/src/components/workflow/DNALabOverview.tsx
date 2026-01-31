"use client";

/**
 * DNALabOverview - Simplified Overview for DNA Lab
 *
 * 2026 Pattern: Silicon Valley Minimal Design
 * - Clean 2x2 grid layout
 * - No redundant information
 * - Focus on action
 */

import { useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import { Video, Brain, CheckCircle, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

export interface DNALabOverviewProps {
  /** IP slug for data loading */
  ipSlug?: string | null;
  /** Callback when step card is clicked */
  onStepClick: (stepId: string) => void;
  /** Custom className */
  className?: string;
}

/**
 * Step definitions - Phase 1-2 unified
 * VPE + AD merged into "analysis"
 */
const STEPS: {
  id: string;
  name: string;
  subtitle: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
}[] = [
  {
    id: "analysis",
    name: "통합 분석",
    subtitle: "영상 분석 + 미학 적용",
    icon: Video,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  {
    id: "mirror",
    name: "창작 DNA",
    subtitle: "페르소나 분석",
    icon: Brain,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
  },
  {
    id: "qc",
    name: "품질 검증",
    subtitle: "최종 검수",
    icon: CheckCircle,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
  },
];

// =============================================================================
// Main Component
// =============================================================================

/**
 * DNALabOverview - Minimal 2x2 grid overview
 */
export function DNALabOverview({
  ipSlug,
  onStepClick,
  className,
}: DNALabOverviewProps) {
  const handleStepClick = useCallback(
    (stepId: string) => {
      onStepClick(stepId);
    },
    [onStepClick]
  );

  return (
    <div className={cn("p-6 max-w-4xl mx-auto", className)}>
      {/* Simple Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          DNA <span className="text-[var(--fg-primary)]">분석</span>
        </h1>
        <p className="text-gray-400 font-light">
          단계를 선택해서 시작하세요.
        </p>
      </div>

      {/* 2x2 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          return (
            <motion.button
              key={step.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.3 }}
              onClick={() => handleStepClick(step.id)}
              className={cn(
                "group relative text-left rounded-2xl overflow-hidden",
                "bg-white/[0.04] border border-white/10",
                "p-6 min-h-[140px]",
                "transition-all duration-200",
                "hover:border-[var(--stitch-primary)]/30",
                "hover:bg-white/[0.06]",
                "hover:shadow-[0_0_25px_rgba(255,0,60,0.1)]"
              )}
            >
              {/* Icon */}
              <div
                className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center mb-4",
                  step.bgColor
                )}
              >
                <Icon className={cn("w-5 h-5", step.color)} />
              </div>

              {/* Title */}
              <h3 className="text-lg font-semibold text-white mb-1">
                {step.name}
              </h3>

              {/* Subtitle */}
              <p className="text-sm text-gray-500">
                {step.subtitle}
              </p>

              {/* CTA */}
              <div className="absolute bottom-5 right-5 opacity-0 group-hover:opacity-100 transition-opacity">
                <ArrowUpRight className="w-5 h-5 text-[var(--stitch-primary)]" />
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

export default DNALabOverview;
