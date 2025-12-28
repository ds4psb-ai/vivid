"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { History, ChevronDown, ChevronUp, FileText } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface PatternVersion {
    id: string;
    pattern_id: string;
    version: number;
    snapshot: Record<string, unknown>;
    note: string | null;
    created_at: string;
}

interface PatternVersionHistoryProps {
    limit?: number;
    className?: string;
}

export default function PatternVersionHistory({
    limit = 5,
    className = "",
}: PatternVersionHistoryProps) {
    const { t } = useLanguage();
    const [versions, setVersions] = useState<PatternVersion[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    useEffect(() => {
        async function fetchVersions() {
            try {
                setIsLoading(true);
                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100"}/api/v1/ops/patterns/versions?limit=${limit}`,
                    { headers: { "X-Admin-Mode": "true" } }
                );
                if (!response.ok) throw new Error("Failed to fetch");
                const data = await response.json();
                setVersions(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load");
            } finally {
                setIsLoading(false);
            }
        }
        fetchVersions();
    }, [limit]);


    const toggleExpand = (id: string) => {
        setExpandedId(expandedId === id ? null : id);
    };

    if (isLoading) {
        return (
            <div className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}>
                <div className="flex items-center gap-2 text-slate-400">
                    <History className="h-4 w-4 animate-pulse" />
                    <span className="text-sm">Loading pattern versions...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`rounded-xl border border-rose-500/20 bg-rose-900/10 p-4 ${className}`}>
                <div className="text-sm text-rose-400">{error}</div>
            </div>
        );
    }

    if (versions.length === 0) {
        return (
            <div className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}>
                <div className="flex items-center gap-2 text-slate-500">
                    <History className="h-4 w-4" />
                    <span className="text-sm">{t("noPatternVersions" as any) || "No pattern versions"}</span>
                </div>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}
        >
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10">
                    <History className="h-4 w-4 text-amber-400" />
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-slate-100">
                        {t("patternVersionHistory" as any) || "Pattern Version History"}
                    </h3>
                    <p className="text-xs text-slate-500">
                        {t("recentVersions" as any) || `Recent ${versions.length} versions`}
                    </p>
                </div>
            </div>

            {/* Version List */}
            <div className="space-y-2">
                {versions.map((version) => (
                    <div
                        key={version.id}
                        className="rounded-lg border border-white/5 bg-slate-950/50"
                    >
                        <button
                            onClick={() => toggleExpand(version.id)}
                            className="w-full flex items-center justify-between p-3 text-left hover:bg-white/5 transition-colors rounded-lg"
                        >
                            <div className="flex items-center gap-3">
                                <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-xs font-mono text-sky-300">
                                    v{version.version}
                                </span>
                                <span className="text-xs text-slate-400">
                                    {new Date(version.created_at).toLocaleDateString()}
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                {version.note && (
                                    <span className="max-w-[150px] truncate text-xs text-slate-500">
                                        {version.note}
                                    </span>
                                )}
                                {expandedId === version.id ? (
                                    <ChevronUp className="h-4 w-4 text-slate-500" />
                                ) : (
                                    <ChevronDown className="h-4 w-4 text-slate-500" />
                                )}
                            </div>
                        </button>

                        {expandedId === version.id && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="border-t border-white/5 p-3"
                            >
                                <div className="flex items-start gap-2 text-xs">
                                    <FileText className="h-3 w-3 text-slate-500 mt-0.5" />
                                    <div className="text-slate-400">
                                        {version.note || "No notes"}
                                    </div>
                                </div>
                                <div className="mt-2 text-[10px] text-slate-600 font-mono">
                                    ID: {version.pattern_id.slice(0, 8)}...
                                </div>
                            </motion.div>
                        )}
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
