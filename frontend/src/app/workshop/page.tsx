"use client";

import Link from "next/link";
import { Sparkles, Film, LayoutGrid, Image as ImageIcon, Zap } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/lib/translations";

const DIMENSION_ITEMS: {
    href: string;
    icon: typeof Sparkles;
    titleKey: keyof typeof translations.ko;
    descKey: keyof typeof translations.ko;
    gradient: string;
    portalColor: string;
}[] = [
        {
            href: "/workshop/prompt",
            icon: Sparkles,
            titleKey: "workshopPromptTitle",
            descKey: "workshopPromptDesc",
            gradient: "from-violet-500/20 via-transparent to-purple-500/20",
            portalColor: "border-violet-500/50 shadow-violet-500/20",
        },
        {
            href: "/workshop/shot-catch",
            icon: Film,
            titleKey: "workshopShotCatchTitle",
            descKey: "workshopShotCatchDesc",
            gradient: "from-cyan-500/20 via-transparent to-blue-500/20",
            portalColor: "border-cyan-500/50 shadow-cyan-500/20",
        },
        {
            href: "/workshop/storyboard",
            icon: LayoutGrid,
            titleKey: "workshopStoryboardTitle",
            descKey: "workshopStoryboardDesc",
            gradient: "from-emerald-500/20 via-transparent to-teal-500/20",
            portalColor: "border-emerald-500/50 shadow-emerald-500/20",
        },
        {
            href: "/workshop/image-tool",
            icon: ImageIcon,
            titleKey: "workshopImageToolTitle",
            descKey: "workshopImageToolDesc",
            gradient: "from-amber-500/20 via-transparent to-orange-500/20",
            portalColor: "border-amber-500/50 shadow-amber-500/20",
        },
    ];

export default function WorkshopHubPage() {
    const { t } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-5xl">
                    {/* Header with Chokki concept */}
                    <header className="mb-10 text-center">
                        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-gradient-to-r from-violet-500/10 to-purple-500/10 px-4 py-1.5 text-sm font-semibold text-violet-300">
                            {t("workshopHubBadge")}
                        </div>
                        <h1 className="mt-4 text-3xl font-bold tracking-tight text-[var(--fg-0)] sm:text-4xl">
                            {t("workshopHubTitle")}
                        </h1>
                        <p className="mx-auto mt-3 max-w-xl text-base text-[var(--fg-muted)] sm:text-lg">
                            {t("workshopHubSubtitle")}
                        </p>
                    </header>

                    {/* Dimension Portal Grid */}
                    <div className="grid gap-5 sm:grid-cols-2">
                        {DIMENSION_ITEMS.map((dimension) => (
                            <Link
                                key={dimension.href}
                                href={dimension.href}
                                className={`group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${dimension.gradient} p-6 transition-all duration-300 hover:-translate-y-1 hover:border-white/20 hover:shadow-xl`}
                            >
                                {/* Portal Ring Effect */}
                                <div className={`absolute -right-8 -top-8 h-32 w-32 rounded-full border-2 ${dimension.portalColor} opacity-20 blur-sm transition-all duration-500 group-hover:opacity-40 group-hover:scale-110`} />

                                <div className="relative flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
                                                <dimension.icon className="h-5 w-5 text-white" aria-hidden="true" />
                                            </div>
                                            <h2 className="text-lg font-bold text-[var(--fg-0)]">
                                                {t(dimension.titleKey)}
                                            </h2>
                                        </div>
                                        <p className="mt-3 text-sm leading-relaxed text-[var(--fg-muted)]">
                                            {t(dimension.descKey)}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-1 rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-white/80 transition-colors group-hover:bg-white/20 group-hover:text-white">
                                        <Zap className="h-3 w-3" aria-hidden="true" />
                                        {t("workshopHubOpen")}
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>

                    {/* Coming Soon Dimensions */}
                    <div className="mt-8 rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-center">
                        <p className="text-sm text-[var(--fg-muted)]">
                            🔮 더 많은 차원이 곧 열립니다...
                        </p>
                        <p className="mt-1 text-xs text-white/40">
                            영상 일관성 차원 • 거장 스타일 차원 • 운명 차원
                        </p>
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
