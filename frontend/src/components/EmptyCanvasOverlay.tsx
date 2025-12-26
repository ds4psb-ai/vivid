"use client";

import { motion } from "framer-motion";
import {
    Sparkles,
    LayoutGrid,
    Video,
    FileText,
    ArrowRight,
    Plus,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface SeedOption {
    id: string;
    title: string;
    description: string;
    icon: React.ElementType;
    gradient: string;
}

interface EmptyCanvasOverlayProps {
    onSelectSeed: (seedId: string) => void;
    onNavigateToTemplates: () => void;
}

export default function EmptyCanvasOverlay({
    onSelectSeed,
    onNavigateToTemplates,
}: EmptyCanvasOverlayProps) {
    const { t } = useLanguage();
    const seedOptions: SeedOption[] = [
        {
            id: "auteur",
            title: t("seedOptionAuteurTitle"),
            description: t("seedOptionAuteurDesc"),
            icon: Sparkles,
            gradient: "from-sky-400 to-blue-600",
        },
        {
            id: "youtube",
            title: t("seedOptionYoutubeTitle"),
            description: t("seedOptionYoutubeDesc"),
            icon: Video,
            gradient: "from-emerald-400 to-teal-600",
        },
        {
            id: "document",
            title: t("seedOptionDocumentTitle"),
            description: t("seedOptionDocumentDesc"),
            icon: FileText,
            gradient: "from-amber-400 to-orange-600",
        },
        {
            id: "blank",
            title: t("seedOptionBlankTitle"),
            description: t("seedOptionBlankDesc"),
            icon: LayoutGrid,
            gradient: "from-slate-400 to-zinc-600",
        },
    ];
    return (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-[var(--bg-0)]/90 backdrop-blur-sm">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-2xl px-6"
            >
                {/* Header */}
                <div className="text-center mb-8">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/10 px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-sky-400 mb-4 shadow-[0_0_10px_-4px_rgba(14,165,233,0.5)]"
                    >
                        <Plus className="h-3 w-3" />
                        {t("emptyCanvasBadge")}
                    </motion.div>
                    <motion.h2
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-2xl font-bold text-[var(--fg-0)]"
                    >
                        {t("emptyCanvasTitle")}
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="mt-2 text-[var(--fg-muted)]"
                    >
                        {t("emptyCanvasSubtitle")}
                    </motion.p>
                </div>

                {/* Seed Options Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="grid grid-cols-2 gap-4"
                >
                    {seedOptions.map((option, index) => (
                        <motion.button
                            key={option.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 + index * 0.1 }}
                            whileHover={{ scale: 1.03, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => {
                                if (option.id === "auteur") {
                                    onNavigateToTemplates();
                                } else {
                                    onSelectSeed(option.id);
                                }
                            }}
                            className="group relative flex flex-col items-start rounded-xl border border-white/10 bg-slate-950/60 p-5 text-left backdrop-blur-xl transition-all hover:border-white/20"
                        >
                            {/* Gradient Accent */}
                            <div
                                className={`absolute inset-0 rounded-xl bg-gradient-to-br ${option.gradient} opacity-0 group-hover:opacity-10 transition-opacity`}
                            />

                            {/* Icon */}
                            <div
                                className={`inline-flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${option.gradient} mb-3`}
                            >
                                <option.icon className="h-5 w-5 text-white" />
                            </div>

                            {/* Content */}
                            <div className="relative z-10">
                                <h3 className="font-semibold text-[var(--fg-0)] group-hover:text-white transition-colors">
                                    {option.title}
                                </h3>
                                <p className="mt-1 text-sm text-[var(--fg-muted)] group-hover:text-slate-300 transition-colors">
                                    {option.description}
                                </p>
                            </div>

                            {/* Arrow on hover */}
                            <div className="absolute bottom-5 right-5 opacity-0 transform translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                                <ArrowRight className="h-4 w-4 text-[var(--accent)]" />
                            </div>
                        </motion.button>
                    ))}
                </motion.div>

                {/* Seed Graph Preview */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="mt-8 rounded-xl border border-white/10 bg-slate-950/40 p-6 backdrop-blur-sm"
                >
                    <div className="text-xs uppercase tracking-widest text-[var(--fg-muted)] mb-4 font-semibold text-center">
                        {t("seedGraphPreviewTitle")}
                    </div>
                    <div className="flex items-center justify-center gap-4">
                        {/* Input Node */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.8 }}
                            className="flex h-12 items-center rounded-lg border border-sky-500/30 bg-sky-500/10 px-4 shadow-[0_0_15px_-3px_rgba(14,165,233,0.15)]"
                        >
                            <span className="text-sm font-medium text-sky-400">{t("seedInput")}</span>
                        </motion.div>
                        {/* Arrow */}
                        <motion.div
                            initial={{ opacity: 0, width: 0 }}
                            animate={{ opacity: 1, width: 32 }}
                            transition={{ delay: 0.9 }}
                            className="h-[1px] border-t border-dashed border-white/20"
                        />
                        {/* Capsule Node */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 1.0 }}
                            className="flex h-12 items-center rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 shadow-[0_0_15px_-3px_rgba(245,158,11,0.15)]"
                        >
                            <Sparkles className="h-4 w-4 text-amber-400 mr-2" />
                            <span className="text-sm font-medium text-amber-400">{t("seedCapsule")}</span>
                        </motion.div>
                        {/* Arrow */}
                        <motion.div
                            initial={{ opacity: 0, width: 0 }}
                            animate={{ opacity: 1, width: 32 }}
                            transition={{ delay: 1.1 }}
                            className="h-[1px] border-t border-dashed border-white/20"
                        />
                        {/* Output Node */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 1.2 }}
                            className="flex h-12 items-center rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 shadow-[0_0_15px_-3px_rgba(16,185,129,0.15)]"
                        >
                            <span className="text-sm font-medium text-emerald-400">{t("seedOutput")}</span>
                        </motion.div>
                    </div>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 1.4 }}
                        className="mt-4 text-center text-xs text-[var(--fg-muted)]"
                    >
                        {t("seedGraphPreviewDesc")}
                    </motion.div>
                </motion.div>
            </motion.div>
        </div>
    );
}
