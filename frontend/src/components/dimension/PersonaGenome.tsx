"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Dna, Fingerprint, Brain, Database, Heart, Sparkles, Activity } from "lucide-react";

interface PersonaData {
    saju?: Record<string, unknown>;
    mbti?: Record<string, unknown>;
    subconscious?: Record<string, unknown>;
    unconscious?: Record<string, unknown>;
    background?: Record<string, unknown>;
    [key: string]: unknown;
}

interface PersonaGenomeProps {
    data: PersonaData;
    stage: string;
}

const SECTION_ICONS: Record<string, React.ReactNode> = {
    saju: <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />,
    mbti: <Brain className="w-4 h-4 text-violet-600 dark:text-violet-400" />,
    subconscious: <Database className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />,
    unconscious: <Fingerprint className="w-4 h-4 text-rose-600 dark:text-rose-400" />,
    background: <Heart className="w-4 h-4 text-amber-600 dark:text-amber-400" />,
};

const SECTION_LABELS: Record<string, string> = {
    saju: "기질 분석 (Four Pillars)",
    mbti: "인지 기능 (Cognitive)",
    subconscious: "잠재의식 (Subconscious)",
    unconscious: "그림자 (Shadow)",
    background: "성장 배경 (Origins)",
};

export default function PersonaGenome({ data, stage }: PersonaGenomeProps) {
    const sections = Object.keys(data).filter(key =>
        ["saju", "mbti", "subconscious", "unconscious", "background"].includes(key)
    );

    return (
        <div className="h-full flex flex-col bg-slate-50 dark:bg-slate-900/40 border-l border-slate-200 dark:border-white/5 backdrop-blur-md overflow-hidden">
            {/* Header */}
            <div className="flex-shrink-0 h-16 flex items-center px-6 border-b border-slate-200 dark:border-white/5 bg-white/50 dark:bg-slate-900/20">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                        <Dna className="w-5 h-5" />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold text-slate-900 dark:text-white tracking-wide">PERSONA GENOME</h2>
                        <span className="text-[10px] text-slate-500 dark:text-white/40 font-mono tracking-wider">LIVE DATA STREAM</span>
                    </div>
                </div>
            </div>

            {/* Content Scroller */}
            <div className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
                {sections.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                        <Dna className="w-12 h-12 text-slate-300 dark:text-white/10 mb-4 animate-pulse" />
                        <p className="text-sm text-slate-500 dark:text-white/30">분석 데이터 대기 중...</p>
                        <p className="text-[10px] text-slate-400 dark:text-white/20 mt-2">대화를 시작하면<br />창작 유전자가 추출됩니다.</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <AnimatePresence mode="popLayout">
                            {sections.map((key) => (
                                <motion.div
                                    key={key}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="bg-white dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10 overflow-hidden shadow-sm dark:shadow-none"
                                >
                                    {/* Section Header */}
                                    <div className="px-4 py-3 bg-slate-50 dark:bg-white/5 flex items-center gap-2 border-b border-slate-200 dark:border-white/5">
                                        {SECTION_ICONS[key] || <Sparkles className="w-4 h-4 text-slate-400" />}
                                        <span className="text-xs font-bold text-slate-700 dark:text-white/80 uppercase tracking-wider">
                                            {SECTION_LABELS[key] || key}
                                        </span>
                                    </div>

                                    {/* JSON Tree View */}
                                    <div className="p-4 font-mono text-[11px] leading-relaxed text-slate-600 dark:text-slate-300 overflow-x-auto">
                                        {renderRecursive(data[key] as Record<string, unknown>)}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}
            </div>

            {/* Status Footer */}
            <div className="flex-shrink-0 px-6 py-3 border-t border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-slate-900/40">
                <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-500 dark:text-white/30">STATUS</span>
                    <span className={stage === "synthesis" ? "text-emerald-600 dark:text-emerald-400" : "text-indigo-600 dark:text-indigo-400 animate-pulse"}>
                        {stage === "synthesis" ? "COMPLETE" : "ANALYZING..."}
                    </span>
                </div>
            </div>
        </div>
    );
}

function renderRecursive(obj: Record<string, unknown>, depth = 0): React.ReactNode {
    if (!obj || Object.keys(obj).length === 0) return <span className="text-slate-400 dark:text-white/20 italic">No data</span>;

    return (
        <ul className="space-y-1">
            {Object.entries(obj).map(([key, value]) => (
                <li key={key} style={{ paddingLeft: depth > 0 ? '12px' : '0' }}>
                    <span className="text-indigo-600 dark:text-indigo-300/80 mr-1.5">{key}:</span>
                    {typeof value === 'object' && value !== null ? (
                        Array.isArray(value) ? (
                            <span className="text-emerald-600 dark:text-emerald-200/80">[{value.join(", ")}]</span>
                        ) : (
                            renderRecursive(value as Record<string, unknown>, depth + 1)
                        )
                    ) : (
                        <span className="text-amber-700 dark:text-amber-100/70">"{String(value)}"</span>
                    )}
                </li>
            ))}
        </ul>
    );
}
