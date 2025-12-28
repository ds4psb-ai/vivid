"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, FileWarning, RefreshCw } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface QuarantineItem {
    id: string;
    sheet_name: string;
    row_number: number;
    reason: string;
    raw_data: Record<string, unknown>;
    created_at: string;
}

interface QuarantineSampleProps {
    limit?: number;
    className?: string;
    onRetry?: (id: string) => void;
}

export default function QuarantineSample({
    limit = 5,
    className = "",
    onRetry,
}: QuarantineSampleProps) {
    const { t } = useLanguage();
    const [items, setItems] = useState<QuarantineItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function fetchQuarantine() {
            try {
                setIsLoading(true);
                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100"}/api/v1/ops/quarantine?limit=${limit}`,
                    { headers: { "X-Admin-Mode": "true" } }
                );
                if (!response.ok) {
                    setItems([]);
                    return;
                }
                const data = await response.json();
                setItems(data);
            } catch {
                // Quarantine endpoint may not exist yet
                setItems([]);
            } finally {
                setIsLoading(false);
            }
        }
        fetchQuarantine();
    }, [limit]);


    if (isLoading) {
        return (
            <div className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}>
                <div className="flex items-center gap-2 text-slate-400">
                    <AlertTriangle className="h-4 w-4 animate-pulse" />
                    <span className="text-sm">Loading quarantine...</span>
                </div>
            </div>
        );
    }

    if (items.length === 0) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-xl border border-emerald-500/20 bg-emerald-900/10 p-4 ${className}`}
            >
                <div className="flex items-center gap-2 text-emerald-400">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm font-medium">
                        {t("noQuarantineItems" as any) || "No quarantine items"}
                    </span>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10">
                        <FileWarning className="h-4 w-4 text-rose-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-slate-100">
                            {t("quarantineSample" as any) || "Quarantine Sample"}
                        </h3>
                        <p className="text-xs text-slate-500">
                            {items.length} items need review
                        </p>
                    </div>
                </div>

                <div className="rounded-full bg-rose-500/10 px-2 py-1">
                    <span className="text-xs font-bold text-rose-400">{items.length}</span>
                </div>
            </div>

            {/* Items List */}
            <div className="space-y-2">
                {items.map((item) => (
                    <div
                        key={item.id}
                        className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-300">
                                        {item.sheet_name}
                                    </span>
                                    <span className="text-[10px] text-slate-500">
                                        Row {item.row_number}
                                    </span>
                                </div>
                                <div className="text-xs text-rose-300">{item.reason}</div>
                                <div className="mt-1 text-[10px] text-slate-500">
                                    {new Date(item.created_at).toLocaleDateString()}
                                </div>
                            </div>

                            {onRetry && (
                                <button
                                    onClick={() => onRetry(item.id)}
                                    className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white"
                                    title="Retry"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
