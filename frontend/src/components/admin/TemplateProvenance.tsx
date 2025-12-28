"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileCheck, AlertCircle, ExternalLink } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface TemplateWithMeta {
    id: string;
    slug: string;
    title: string;
    is_public: boolean;
    graph_data: {
        meta?: {
            guide_sources?: string[];
            evidence_refs?: string[];
            pattern_version?: string;
        };
    };
}

interface TemplateProvenanceProps {
    className?: string;
}

export default function TemplateProvenance({
    className = "",
}: TemplateProvenanceProps) {
    const { t } = useLanguage();
    const [templates, setTemplates] = useState<TemplateWithMeta[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchTemplates() {
            try {
                setIsLoading(true);
                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100"}/api/v1/templates?public_only=false`,
                    { headers: { "X-Admin-Mode": "true" } }
                );
                if (!response.ok) throw new Error("Failed to fetch");
                const data = await response.json();
                setTemplates(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load");
            } finally {
                setIsLoading(false);
            }
        }
        fetchTemplates();
    }, []);


    const publicTemplates = templates.filter((t) => t.is_public);
    const missingProvenance = publicTemplates.filter((t) => {
        const meta = t.graph_data?.meta;
        const hasGuide = meta?.guide_sources && meta.guide_sources.length > 0;
        const hasEvidence = meta?.evidence_refs && meta.evidence_refs.length > 0;
        return !hasGuide && !hasEvidence;
    });

    if (isLoading) {
        return (
            <div className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}>
                <div className="flex items-center gap-2 text-slate-400">
                    <FileCheck className="h-4 w-4 animate-pulse" />
                    <span className="text-sm">Loading templates...</span>
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

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl border border-white/10 bg-slate-900/50 p-4 ${className}`}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10">
                        <FileCheck className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-slate-100">
                            {t("templateProvenance" as any) || "Template Provenance"}
                        </h3>
                        <p className="text-xs text-slate-500">
                            {t("publicTemplatesCount" as any) || `${publicTemplates.length} public templates`}
                        </p>
                    </div>
                </div>

                {missingProvenance.length > 0 && (
                    <div className="flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-1">
                        <AlertCircle className="h-3 w-3 text-amber-400" />
                        <span className="text-xs font-medium text-amber-400">
                            {missingProvenance.length} missing
                        </span>
                    </div>
                )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="rounded-lg bg-slate-950/50 p-3 text-center">
                    <div className="text-lg font-bold text-slate-100">{templates.length}</div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">Total</div>
                </div>
                <div className="rounded-lg bg-slate-950/50 p-3 text-center">
                    <div className="text-lg font-bold text-emerald-400">{publicTemplates.length}</div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">Public</div>
                </div>
                <div className="rounded-lg bg-slate-950/50 p-3 text-center">
                    <div className="text-lg font-bold text-amber-400">{missingProvenance.length}</div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">No Refs</div>
                </div>
            </div>

            {/* Missing Provenance List */}
            {missingProvenance.length > 0 && (
                <div className="space-y-2">
                    <div className="text-xs uppercase tracking-widest text-slate-500 mb-2">
                        Missing Provenance
                    </div>
                    {missingProvenance.slice(0, 5).map((template) => (
                        <div
                            key={template.id}
                            className="flex items-center justify-between rounded-lg border border-amber-500/20 bg-amber-500/5 p-3"
                        >
                            <div>
                                <div className="text-sm font-medium text-slate-200">{template.title}</div>
                                <div className="text-xs text-slate-500 font-mono">{template.slug}</div>
                            </div>
                            <a
                                href={`/templates/${template.id}`}
                                className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white"
                            >
                                <ExternalLink className="h-4 w-4" />
                            </a>
                        </div>
                    ))}
                    {missingProvenance.length > 5 && (
                        <div className="text-xs text-center text-slate-500">
                            +{missingProvenance.length - 5} more
                        </div>
                    )}
                </div>
            )}

            {/* All Good State */}
            {missingProvenance.length === 0 && publicTemplates.length > 0 && (
                <div className="flex items-center justify-center gap-2 py-4 text-emerald-400">
                    <FileCheck className="h-5 w-5" />
                    <span className="text-sm font-medium">All templates have provenance</span>
                </div>
            )}
        </motion.div>
    );
}
