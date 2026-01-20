"use client";

/**
 * Workflow Preview Modal
 *
 * IP 상세 페이지에서 생성하기 버튼 클릭 시 추천된 워크플로우를 미리 보여주고
 * 첫 번째 앱으로 리다이렉트하는 모달입니다.
 */

import React from "react";
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
}

export function WorkflowPreviewModal({
  isOpen,
  onClose,
  workflowData,
  ipSlug,
  ipName,
}: WorkflowPreviewModalProps) {
  const router = useRouter();
  const { language } = useLanguage();
  const ko = language === "ko";

  const handleConfirm = () => {
    if (workflowData?.redirect_url) {
      router.push(workflowData.redirect_url);
    }
  };

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
            className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-violet-500/10">
                    <Sparkles className="w-5 h-5 text-violet-500" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                      {ko ? "추천 워크플로우" : "Recommended Workflow"}
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {ko ? workflowData.workflow_name_ko : workflowData.workflow_name_en}
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-5">
              {/* IP Info */}
              <div className="mb-5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  <span className="font-medium text-slate-900 dark:text-white">{ipName}</span>
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

                        <div
                          className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                            isFirst
                              ? "border-violet-500 bg-violet-50 dark:bg-violet-900/20"
                              : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/30"
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

                          {/* Arrow for first step */}
                          {isFirst && (
                            <ChevronRight className="w-5 h-5 text-violet-500 flex-shrink-0" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-5 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30">
              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors font-medium"
                >
                  {ko ? "취소" : "Cancel"}
                </button>
                <button
                  onClick={handleConfirm}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-violet-600 hover:bg-violet-700 text-white transition-colors font-medium flex items-center justify-center gap-2"
                >
                  {ko ? "시작하기" : "Start"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-center text-slate-500 dark:text-slate-400 mt-3">
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
