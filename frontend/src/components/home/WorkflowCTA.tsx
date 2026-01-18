"use client";

/**
 * WorkflowCTA - Call-to-action for custom workflow creation
 *
 * Encourages users to explore the Flow page for building
 * custom dimension chains.
 *
 * Gated by FLOW_ENABLED feature flag - returns null when disabled.
 */

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Workflow, Zap } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { FLOW_ENABLED } from "@/lib/feature-flags";

interface WorkflowCTAProps {
    variant?: "default" | "compact";
}

const BRAND_PRIMARY = {
    bgSoft: "bg-[var(--color-brand-primary)]/5",
    bg: "bg-[var(--color-brand-primary)]/10",
    text: "text-[var(--color-brand-primary)]",
    border: "border-[var(--color-brand-primary)]/20",
};

const BRAND_SECONDARY = {
    bgSoft: "bg-[var(--color-brand-secondary)]/5",
    bg: "bg-[var(--color-brand-secondary)]/10",
    bgStrong: "bg-[var(--color-brand-secondary)]/20",
    text: "text-[var(--color-brand-secondary)]",
    border: "border-[var(--color-brand-secondary)]/20",
    borderHover: "hover:border-[var(--color-brand-secondary)]/30",
};

const BRAND_ACCENT = {
    text: "text-[var(--color-brand-accent)]",
};

export function WorkflowCTA({ variant = "default" }: WorkflowCTAProps) {
    const { language } = useLanguage();

    // Feature gate: hide entire CTA when Flow is disabled
    if (!FLOW_ENABLED) {
        return null;
    }

    if (variant === "compact") {
        return (
            <Link
                href="/flow"
                className={`group flex items-center justify-between p-4 rounded-2xl border border-gray-200 dark:border-white/10 bg-gradient-to-r from-[var(--color-brand-secondary)]/5 via-transparent to-[var(--color-brand-primary)]/5 ${BRAND_SECONDARY.borderHover} transition-all`}
            >
                <div className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-xl ${BRAND_SECONDARY.bg} flex items-center justify-center border ${BRAND_SECONDARY.border}`}>
                        <Workflow className={`h-5 w-5 ${BRAND_SECONDARY.text}`} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                            {language === "ko" ? "차원 플로우" : "Dimension Flow"}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-slate-400">
                            {language === "ko" ? "여러 차원을 직접 조합" : "Combine multiple dimensions"}
                        </p>
                    </div>
                </div>
                <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-[var(--color-brand-secondary)] group-hover:translate-x-1 transition-all" />
            </Link>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
        >
            <Link
                href="/flow"
                className={`group block relative overflow-hidden rounded-2xl border border-dashed border-gray-300 dark:border-white/10 ${BRAND_SECONDARY.borderHover} bg-gradient-to-r from-[var(--color-brand-secondary)]/5 via-transparent to-[var(--color-brand-primary)]/5 p-6 transition-all`}
            >
                {/* Animated background */}
                <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-brand-secondary)]/10 via-transparent to-[var(--color-brand-primary)]/10 opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="relative flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <div className={`absolute inset-0 ${BRAND_SECONDARY.bgStrong} blur-xl rounded-full animate-pulse`} />
                            <div className={`relative h-14 w-14 rounded-2xl bg-gradient-to-br from-[var(--color-brand-secondary)]/20 to-[var(--color-brand-primary)]/20 flex items-center justify-center border border-gray-200 dark:border-white/10`}>
                                <Workflow className={`h-7 w-7 ${BRAND_SECONDARY.text}`} />
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <Zap className={`h-3.5 w-3.5 ${BRAND_ACCENT.text}`} />
                                <span className={`text-[10px] font-bold uppercase tracking-widest ${BRAND_ACCENT.text}`}>
                                    {language === "ko" ? "파워 유저" : "Power User"}
                                </span>
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-[var(--color-brand-secondary)] transition-colors">
                                {language === "ko" ? "차원 플로우 시작하기" : "Start Dimension Flow"}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
                                {language === "ko"
                                    ? "여러 차원 도구를 직접 조합하여 나만의 AI 파이프라인을 구축하세요"
                                    : "Combine multiple dimension tools to build your own AI pipeline"}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400 group-hover:text-[var(--color-brand-secondary)] transition-colors">
                        <span className="text-sm font-medium hidden sm:block">
                            {language === "ko" ? "차원 플로우" : "Flow"}
                        </span>
                        <ArrowRight className="h-5 w-5 group-hover:translate-x-2 transition-transform" />
                    </div>
                </div>
            </Link>
        </motion.div>
    );
}
