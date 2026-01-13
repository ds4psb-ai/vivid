"use client";

/**
 * EvidenceDisplay - P5+P6: 공통 AI 근거 표시 컴포넌트 (Hardened)
 *
 * 사용법:
 *   <EvidenceDisplay refs={result.evidence_refs} confidence={result.confidence} />
 *
 * 규칙:
 * - 섹션명: "AI 근거"
 * - 3개 초과 시 "더보기" 표시
 * - confidence < 0.5 면 기본 접힘
 * - refs 없으면 null 반환
 *
 * P5+ Hardening:
 * - Array.isArray guard for type safety
 * - Dedup by ref_id
 * - Sort by score descending
 * - Aria-labels for accessibility
 * - Score NaN/undefined protection
 * - React.memo for performance
 * - No dangerouslySetInnerHTML (XSS safe)
 *
 * P6-2: Zod schema validation
 * - Runtime validation of EvidenceRef structure
 * - Invalid refs dropped with console.warn
 */

import React, { useState, useEffect, useMemo, memo } from "react";
import { z } from "zod";

// P6-2: Zod schema for EvidenceRef validation
const EvidenceRefSchema = z.object({
    ref_id: z.string().min(1),
    source: z.string().optional(),
    content_preview: z.string().optional(),
    dataset_id: z.string().optional(),
    dataset_label: z.string().optional(),
    score: z.number().nullable().optional(),
});

export interface EvidenceRef {
    ref_id: string;
    source?: string;
    content_preview?: string;
    dataset_id?: string;
    dataset_label?: string;
    score?: number;
}

interface EvidenceDisplayProps {
    refs: EvidenceRef[] | undefined | null | string;  // Allow string for defensive handling
    confidence?: number;
    themeColor?: "amber" | "cyan" | "violet" | "emerald" | "rose";
    maxVisible?: number;
    defaultExpanded?: boolean;
}

// Theme color mappings
const THEME_COLORS = {
    amber: {
        bg: "bg-amber-50/50 dark:bg-amber-900/10",
        border: "border-amber-200 dark:border-amber-800/30",
        text: "text-amber-700 dark:text-amber-400",
        badge: "bg-amber-200 dark:bg-amber-800/50 text-amber-800 dark:text-amber-200",
    },
    cyan: {
        bg: "bg-cyan-50/50 dark:bg-cyan-900/10",
        border: "border-cyan-200 dark:border-cyan-800/30",
        text: "text-cyan-700 dark:text-cyan-400",
        badge: "bg-cyan-200 dark:bg-cyan-800/50 text-cyan-800 dark:text-cyan-200",
    },
    violet: {
        bg: "bg-violet-50/50 dark:bg-violet-900/10",
        border: "border-violet-200 dark:border-violet-800/30",
        text: "text-violet-700 dark:text-violet-400",
        badge: "bg-violet-200 dark:bg-violet-800/50 text-violet-800 dark:text-violet-200",
    },
    emerald: {
        bg: "bg-emerald-50/50 dark:bg-emerald-900/10",
        border: "border-emerald-200 dark:border-emerald-800/30",
        text: "text-emerald-700 dark:text-emerald-400",
        badge: "bg-emerald-200 dark:bg-emerald-800/50 text-emerald-800 dark:text-emerald-200",
    },
    rose: {
        bg: "bg-rose-50/50 dark:bg-rose-900/10",
        border: "border-rose-200 dark:border-rose-800/30",
        text: "text-rose-700 dark:text-rose-400",
        badge: "bg-rose-200 dark:bg-rose-800/50 text-rose-800 dark:text-rose-200",
    },
};

/**
 * Safe score formatter - handles undefined, null, NaN
 */
function formatScore(score: number | undefined | null): string | null {
    if (score === undefined || score === null) return null;
    if (typeof score !== "number" || Number.isNaN(score)) return null;
    if (score <= 0) return null;
    return `${Math.round(score * 100)}% match`;
}

/**
 * Process refs: validate with Zod, deduplicate by ref_id, sort by score desc
 */
function processRefs(refs: unknown[]): EvidenceRef[] {
    // P6-2: Validate each ref with Zod
    const validated: EvidenceRef[] = [];
    for (const ref of refs) {
        const result = EvidenceRefSchema.safeParse(ref);
        if (result.success) {
            validated.push(result.data as EvidenceRef);
        } else {
            console.warn("[EvidenceDisplay] Invalid ref dropped:", ref, result.error.issues);
        }
    }

    // Deduplicate by ref_id
    const seen = new Set<string>();
    const deduped = validated.filter((ref) => {
        if (!ref.ref_id || seen.has(ref.ref_id)) return false;
        seen.add(ref.ref_id);
        return true;
    });

    // Sort by score descending (undefined scores go last)
    return deduped.sort((a, b) => {
        const aScore = typeof a.score === "number" && !Number.isNaN(a.score) ? a.score : -1;
        const bScore = typeof b.score === "number" && !Number.isNaN(b.score) ? b.score : -1;
        return bScore - aScore;
    });
}

function EvidenceDisplayInner({
    refs,
    confidence = 1,
    themeColor = "amber",
    maxVisible = 3,
    defaultExpanded,
}: EvidenceDisplayProps) {
    // Type guard: ensure refs is array
    const safeRefs = useMemo(() => {
        if (!refs) return [];
        if (!Array.isArray(refs)) {
            // Handle string or other types gracefully
            console.warn("[EvidenceDisplay] refs is not an array:", typeof refs);
            return [];
        }
        return processRefs(refs);
    }, [refs]);

    // Auto-collapse if confidence < 0.5
    const autoCollapse = confidence < 0.5;
    const [expanded, setExpanded] = useState(defaultExpanded ?? !autoCollapse);
    const [showAll, setShowAll] = useState(false);

    // Reset expansion state when refs change
    useEffect(() => {
        setExpanded(defaultExpanded ?? !autoCollapse);
        setShowAll(false);
    }, [safeRefs, autoCollapse, defaultExpanded]);

    // No refs = null (empty state handled by parent)
    if (safeRefs.length === 0) return null;

    const theme = THEME_COLORS[themeColor] || THEME_COLORS.amber;
    const visibleRefs = showAll ? safeRefs : safeRefs.slice(0, maxVisible);
    const hasMore = safeRefs.length > maxVisible;

    return (
        <div className={`mt-4 p-4 ${theme.bg} border ${theme.border} rounded-xl`}>
            <button
                onClick={() => setExpanded(!expanded)}
                className={`flex items-center gap-2 text-xs font-medium ${theme.text} hover:opacity-80 transition-opacity`}
                aria-expanded={expanded}
                aria-label={expanded ? "AI 근거 접기" : "AI 근거 펼치기"}
            >
                <span aria-hidden="true">{expanded ? "▼" : "▶"}</span>
                <span>📚 AI 근거 ({safeRefs.length}개)</span>
                {autoCollapse && !expanded && (
                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 ml-2">
                        (신뢰도 낮음)
                    </span>
                )}
            </button>

            {expanded && (
                <div className="mt-3 space-y-2">
                    {visibleRefs.map((ref) => (
                        <div
                            key={ref.ref_id}
                            className="p-3 bg-white dark:bg-black/20 rounded-lg text-sm"
                        >
                            <div className="flex items-center gap-2 mb-1">
                                <span
                                    className={`text-[10px] px-1.5 py-0.5 rounded ${theme.badge}`}
                                >
                                    {ref.dataset_label || ref.dataset_id || "source"}
                                </span>
                                {formatScore(ref.score) && (
                                    <span className="text-[10px] text-slate-400 dark:text-zinc-500">
                                        {formatScore(ref.score)}
                                    </span>
                                )}
                            </div>
                            {/* Safe text rendering - no dangerouslySetInnerHTML */}
                            <p className="text-slate-600 dark:text-zinc-300 line-clamp-2">
                                {ref.content_preview || ref.ref_id}
                            </p>
                        </div>
                    ))}

                    {/* Show more button */}
                    {hasMore && !showAll && (
                        <button
                            onClick={() => setShowAll(true)}
                            className={`text-xs ${theme.text} hover:opacity-80 transition-opacity mt-2`}
                            aria-label={`나머지 ${safeRefs.length - maxVisible}개 근거 보기`}
                        >
                            + {safeRefs.length - maxVisible}개 더보기
                        </button>
                    )}

                    {/* Collapse button when showing all */}
                    {showAll && hasMore && (
                        <button
                            onClick={() => setShowAll(false)}
                            className={`text-xs ${theme.text} hover:opacity-80 transition-opacity mt-2`}
                            aria-label="근거 목록 접기"
                        >
                            접기
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

// Memoize for performance with many evidence refs
export const EvidenceDisplay = memo(EvidenceDisplayInner);
export default EvidenceDisplay;
