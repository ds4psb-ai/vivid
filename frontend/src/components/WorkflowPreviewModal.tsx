"use client";

/**
 * Workflow Preview Modal
 *
 * IP 상세 페이지에서 생성하기 버튼 클릭 시 추천된 워크플로우를 미리 보여주고
 * 첫 번째 앱으로 리다이렉트하는 모달입니다.
 */

import React, { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Sparkles,
  ArrowRight,
  ChevronRight,
  Brain,
  Search,
  Layers,
  Palette,
  Image as ImageIcon,
  Video,
  Music,
  Users,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/contexts/LanguageContext";
import { saveWorkflowState, buildStepUrl } from "@/lib/workflow-state";

// Icon mapping
const ICON_MAP: Record<string, React.ElementType> = {
  brain: Brain,
  search: Search,
  layers: Layers,
  palette: Palette,
  image: ImageIcon,
  video: Video,
  music: Music,
  users: Users,
  sparkles: Sparkles,
};

export interface WorkflowStep {
  app: string;
  href: string;
  badge: string;
  name_ko: string;
  name_en: string;
}

export interface WorkflowData {
  generation_id: string;
  workflow_key: string;
  workflow_name_ko: string;
  workflow_name_en: string;
  workflow_steps: WorkflowStep[];
  redirect_url: string;
  message: string;
}

interface WorkflowPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowData: WorkflowData | null;
  ipSlug: string;
  ipName: string;
  userPrompt?: string; // 사용자가 입력한 프롬프트
}

export function WorkflowPreviewModal({
  isOpen,
  onClose,
  workflowData,
  ipSlug,
  ipName,
  userPrompt,
}: WorkflowPreviewModalProps) {
  const router = useRouter();
  const { language } = useLanguage();
  const ko = language === "ko";

  // 워크플로우 상태 저장 및 첫 번째 단계로 이동
  const handleConfirm = useCallback(() => {
    if (!workflowData) return;

    // 1. 워크플로우 상태 저장
    saveWorkflowState({
      ipSlug,
      workflowKey: workflowData.workflow_key,
      currentStep: 1,
      totalSteps: workflowData.workflow_steps.length,
      steps: workflowData.workflow_steps.map((step) => ({
        app: step.app,
        href: step.href,
        badge: step.badge,
        name_ko: step.name_ko,
        name_en: step.name_en,
      })),
      startedAt: new Date().toISOString(),
      results: {},
      userPrompt: userPrompt || undefined,
    });

    // 2. 첫 번째 단계 URL 생성 (쿼리 파라미터 포함)
    const firstStep = workflowData.workflow_steps[0];
    const url = buildStepUrl(
      {
        app: firstStep.app,
        href: firstStep.href,
        badge: firstStep.badge,
        name_ko: firstStep.name_ko,
        name_en: firstStep.name_en,
      },
      ipSlug,
      1,
      workflowData.workflow_key,
      userPrompt || undefined
    );

    router.push(url);
  }, [workflowData, ipSlug, userPrompt, router]);

  // 특정 단계로 직접 이동
  const handleStepClick = useCallback(
    (step: WorkflowStep, index: number) => {
      if (!workflowData) return;

      // 워크플로우 상태 저장 (해당 단계부터 시작)
      saveWorkflowState({
        ipSlug,
        workflowKey: workflowData.workflow_key,
        currentStep: index + 1,
        totalSteps: workflowData.workflow_steps.length,
        steps: workflowData.workflow_steps.map((s) => ({
          app: s.app,
          href: s.href,
          badge: s.badge,
          name_ko: s.name_ko,
          name_en: s.name_en,
        })),
        startedAt: new Date().toISOString(),
        results: {},
        userPrompt: userPrompt || undefined,
      });

      // URL 생성 및 이동
      const url = buildStepUrl(
        {
          app: step.app,
          href: step.href,
          badge: step.badge,
          name_ko: step.name_ko,
          name_en: step.name_en,
        },
        ipSlug,
        index + 1,
        workflowData.workflow_key,
        userPrompt || undefined
      );

      router.push(url);
    },
    [workflowData, ipSlug, userPrompt, router]
  );

  // Get icon for app
  const getAppIcon = (app: string): React.ElementType => {
    const appLower = app.toLowerCase();
    if (appLower.includes("reference") || appLower.includes("decoder")) return Search;
    if (appLower.includes("abyss") || appLower.includes("mirror")) return Brain;
    if (appLower.includes("story") || appLower.includes("architect")) return Layers;
    if (appLower.includes("aesthetic") || appLower.includes("director")) return Palette;
    if (appLower.includes("visual") || appLower.includes("realizer")) return ImageIcon;
    if (appLower.includes("video") || appLower.includes("maker")) return Video;
    if (appLower.includes("sound") || appLower.includes("crafter")) return Music;
    return Sparkles;
  };

  if (!workflowData) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-[var(--bg-elevated)] rounded-[var(--workflow-card-radius)] shadow-[var(--workflow-card-shadow)] w-full max-w-lg overflow-hidden border border-[var(--workflow-card-border)]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-5 border-b border-[var(--border-default)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-[var(--bg-primary-subtle)]">
                    <Sparkles className="w-5 h-5 text-[var(--fg-primary)]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-[var(--fg-default)]">
                      {ko ? "추천 워크플로우" : "Recommended Workflow"}
                    </h2>
                    <p className="text-sm text-[var(--fg-muted)]">
                      {ko ? workflowData.workflow_name_ko : workflowData.workflow_name_en}
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-[var(--bg-interactive-hover)] transition-[var(--transition-interactive)]"
                >
                  <X className="w-5 h-5 text-[var(--fg-muted)]" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-5">
              {/* IP Info */}
              <div className="mb-5 p-3 rounded-xl bg-[var(--bg-subtle)]">
                <p className="text-sm text-[var(--fg-muted)]">
                  <span className="font-medium text-[var(--fg-default)]">{ipName}</span>
                  {ko ? "로 창작을 시작합니다" : " will be used as reference"}
                </p>
              </div>

              {/* Workflow Steps */}
              <div className="space-y-3">
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                  {ko ? `${workflowData.workflow_steps.length}단계 워크플로우` : `${workflowData.workflow_steps.length}-Step Workflow`}
                </p>

                <div className="space-y-2">
                  {workflowData.workflow_steps.map((step, index) => {
                    const Icon = getAppIcon(step.app);
                    const isFirst = index === 0;
                    const isLast = index === workflowData.workflow_steps.length - 1;

                    return (
                      <div key={step.app} className="relative">
                        {/* Connecting Line */}
                        {!isLast && (
                          <div className="absolute left-5 top-12 w-0.5 h-4 bg-gradient-to-b from-violet-300 to-violet-100 dark:from-violet-600 dark:to-violet-800" />
                        )}

                        <button
                          onClick={() => handleStepClick(step, index)}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all text-left hover:shadow-md ${
                            isFirst
                              ? "border-violet-500 bg-violet-50 dark:bg-violet-900/20 hover:bg-violet-100 dark:hover:bg-violet-900/30"
                              : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/30 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                          }`}
                        >
                          {/* Step Number + Icon */}
                          <div className="relative flex-shrink-0">
                            <div
                              className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                                isFirst
                                  ? "bg-violet-500 text-white"
                                  : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                              }`}
                            >
                              <Icon className="w-5 h-5" />
                            </div>
                            <div
                              className={`absolute -top-1 -right-1 w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center ${
                                isFirst
                                  ? "bg-white dark:bg-slate-900 text-violet-500"
                                  : "bg-slate-200 dark:bg-slate-600 text-slate-600 dark:text-slate-300"
                              }`}
                            >
                              {index + 1}
                            </div>
                          </div>

                          {/* Step Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p
                                className={`font-medium text-sm ${
                                  isFirst
                                    ? "text-violet-700 dark:text-violet-300"
                                    : "text-slate-700 dark:text-slate-300"
                                }`}
                              >
                                {ko ? step.name_ko : step.name_en}
                              </p>
                              <span
                                className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                  isFirst
                                    ? "bg-violet-500 text-white"
                                    : "bg-slate-200 dark:bg-slate-600 text-slate-600 dark:text-slate-300"
                                }`}
                              >
                                {step.badge}
                              </span>
                            </div>
                          </div>

                          {/* Arrow for all steps - shows clickability */}
                          <ChevronRight className={`w-5 h-5 flex-shrink-0 ${isFirst ? "text-violet-500" : "text-slate-400"}`} />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-5 border-t border-[var(--border-default)] bg-[var(--bg-subtle)]">
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 py-2.5 px-4 rounded-[var(--cta-secondary-radius)] border border-[var(--cta-secondary-border)] bg-[var(--cta-secondary-bg)] text-[var(--cta-secondary-fg)] hover:bg-[var(--cta-secondary-bg-hover)] transition-[var(--transition-interactive)] font-medium"
                >
                  {ko ? "취소" : "Cancel"}
                </button>
                <button
                  onClick={handleConfirm}
                  className="flex-1 py-2.5 px-4 rounded-[var(--cta-primary-radius)] bg-[var(--bg-primary)] hover:bg-[var(--bg-primary-hover)] text-[var(--fg-on-primary)] shadow-[var(--cta-primary-shadow)] hover:shadow-[var(--cta-primary-shadow-hover)] transition-[var(--transition-interactive)] font-medium flex items-center justify-center gap-2"
                >
                  {ko ? "시작하기" : "Start"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-center text-[var(--fg-subtle)] mt-3">
                {ko
                  ? "첫 번째 단계로 이동합니다. IP 레퍼런스가 자동으로 전달됩니다."
                  : "You will be redirected to the first step. IP reference will be passed automatically."}
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default WorkflowPreviewModal;
