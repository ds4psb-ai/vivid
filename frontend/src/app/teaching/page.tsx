"use client";

import Link from "next/link";
import { Film, Image as ImageIcon, LayoutGrid, Sparkles } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/lib/translations";

const TOOL_ITEMS: {
    href: string;
    icon: typeof Sparkles;
    titleKey: keyof typeof translations.ko;
    descKey: keyof typeof translations.ko;
}[] = [
    {
        href: "/teaching/prompt",
        icon: Sparkles,
        titleKey: "teachingPromptTitle",
        descKey: "teachingPromptDesc",
    },
    {
        href: "/teaching/shot-catch",
        icon: Film,
        titleKey: "teachingShotCatchTitle",
        descKey: "teachingShotCatchDesc",
    },
    {
        href: "/teaching/storyboard",
        icon: LayoutGrid,
        titleKey: "teachingStoryboardTitle",
        descKey: "teachingStoryboardDesc",
    },
    {
        href: "/teaching/image-tool",
        icon: ImageIcon,
        titleKey: "teachingImageToolTitle",
        descKey: "teachingImageToolDesc",
    },
];

export default function TeachingHubPage() {
    const { t } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-5xl">
                    <header className="mb-8">
                        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-[var(--fg-muted)]">
                            {t("teachingHubBadge")}
                        </div>
                        <h1 className="mt-3 text-2xl font-semibold text-[var(--fg-0)] sm:text-3xl">
                            {t("teachingHubTitle")}
                        </h1>
                        <p className="mt-2 text-sm text-[var(--fg-muted)] sm:text-base">
                            {t("teachingHubSubtitle")}
                        </p>
                    </header>

                    <div className="grid gap-4 sm:grid-cols-2">
                        {TOOL_ITEMS.map((tool) => (
                            <Link
                                key={tool.href}
                                href={tool.href}
                                className="group rounded-2xl border border-white/10 bg-white/5 p-5 transition-colors hover:bg-white/10"
                            >
                                <div className="flex items-start justify-between">
                                    <div>
                                        <div className="flex items-center gap-2 text-lg font-semibold text-[var(--fg-0)]">
                                            <tool.icon className="h-5 w-5 text-white/70" aria-hidden="true" />
                                            {t(tool.titleKey)}
                                        </div>
                                        <p className="mt-2 text-sm text-[var(--fg-muted)]">
                                            {t(tool.descKey)}
                                        </p>
                                    </div>
                                    <span className="text-xs text-white/50 group-hover:text-white/80">
                                        {t("teachingHubOpen")}
                                    </span>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
