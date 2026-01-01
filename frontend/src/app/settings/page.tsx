"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
    Globe,
    Bell,
    Palette,
    ChevronRight,
    Check,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { api } from "@/lib/api";
import PageStatus from "@/components/PageStatus";
import { isNetworkError, normalizeApiError } from "@/lib/errors";
import { useActiveUserId } from "@/hooks/useActiveUserId";
import { formatNumber } from "@/lib/formatters";

const LANGUAGES = [
    { code: "en", label: "English" },
    { code: "ko", label: "한국어" },
] as const;

const THEMES = [
    { id: "dark", label: "Dark", labelKo: "다크", preview: "bg-slate-900" },
    { id: "darker", label: "Darker", labelKo: "딥 다크", preview: "bg-slate-950" },
] as const;

interface SettingItem {
    label: string;
    value: string;
    action: string;
}

interface SettingSection {
    title: string;
    titleKo: string;
    icon: React.ElementType;
    items: SettingItem[];
}

export default function SettingsPage() {
    const { language, setLanguage } = useLanguage();
    const [theme, setTheme] = useState("dark");
    const [notifications, setNotifications] = useState(true);
    const [canvasCount, setCanvasCount] = useState<number | null>(null);
    const [creditBalance, setCreditBalance] = useState<number | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [isOffline, setIsOffline] = useState(false);
    const { userId } = useActiveUserId("demo-user");

    const labels = {
        title: language === "ko" ? "설정" : "Settings",
        subtitle: language === "ko" ? "계정 및 환경설정 관리" : "Manage your account and preferences",
        language: language === "ko" ? "언어" : "Language",
        theme: language === "ko" ? "테마" : "Theme",
        notifications: language === "ko" ? "알림" : "Notifications",
        configure: language === "ko" ? "설정" : "Configure",
        overview: language === "ko" ? "계정 요약" : "Account overview",
        overviewSubtitle:
            language === "ko"
                ? "캔버스와 크레딧 상태를 확인하세요."
                : "Monitor canvas count and credit balance.",
        canvasCount: language === "ko" ? "캔버스" : "Canvases",
        credits: language === "ko" ? "크레딧" : "Credits",
        loadError: language === "ko" ? "설정을 불러오지 못했습니다." : "Unable to load settings.",
    };

    useEffect(() => {
        let active = true;
        Promise.all([api.listCanvases(), api.getCreditsBalance(userId)])
            .then(([canvases, balance]) => {
                if (!active) return;
                setLoadError(null);
                setIsOffline(false);
                setCanvasCount(canvases.length);
                setCreditBalance(balance.balance);
            })
            .catch((err) => {
                if (!active) return;
                setLoadError(normalizeApiError(err, labels.loadError));
                setIsOffline(isNetworkError(err));
            });
        return () => {
            active = false;
        };
    }, [labels.loadError, userId]);

    const sections: SettingSection[] = [
        {
            title: "Preferences",
            titleKo: "환경설정",
            icon: Palette,
            items: [
                { label: labels.theme, value: theme === "dark" ? "Dark" : "Darker", action: "theme" },
                { label: labels.notifications, value: notifications ? "On" : "Off", action: "notifications" },
            ],
        },
    ];

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-2xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 sm:mb-8"
                    >
                        <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                        <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                    </motion.div>

                    {loadError && (
                        <PageStatus
                            variant="error"
                            title={labels.loadError}
                            message={loadError}
                            isOffline={isOffline}
                            className="mb-4"
                        />
                    )}

                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.05 }}
                        className="mb-4 rounded-lg border border-white/10 bg-slate-950/60 p-4 sm:mb-6 sm:rounded-xl sm:p-5"
                        aria-labelledby="overview-heading"
                    >
                        <div className="flex items-center gap-2 mb-3 sm:mb-4">
                            <Globe className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                            <span id="overview-heading" className="font-medium text-[var(--fg-0)]">{labels.overview}</span>
                        </div>
                        <p className="text-xs text-[var(--fg-muted)]">{labels.overviewSubtitle}</p>
                        <div className="mt-4 grid gap-3 sm:grid-cols-2">
                            <div className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2">
                                <div className="text-[9px] uppercase text-[var(--fg-muted)]">{labels.canvasCount}</div>
                                <div className="mt-1 text-sm font-semibold text-[var(--fg-0)]">
                                    {formatNumber(canvasCount, undefined, undefined, "-")}
                                </div>
                            </div>
                            <div className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2">
                                <div className="text-[9px] uppercase text-[var(--fg-muted)]">{labels.credits}</div>
                                <div className="mt-1 text-sm font-semibold text-[var(--fg-0)]">
                                    {formatNumber(creditBalance, undefined, undefined, "-")}
                                </div>
                            </div>
                        </div>
                    </motion.section>

                    {/* Language */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-4 rounded-lg border border-white/10 bg-slate-950/60 p-4 sm:mb-6 sm:rounded-xl sm:p-5"
                        aria-labelledby="language-heading"
                    >
                        <div className="flex items-center gap-2 mb-3 sm:mb-4">
                            <Globe className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                            <span id="language-heading" className="font-medium text-[var(--fg-0)]">{labels.language}</span>
                        </div>
                        <div className="flex flex-wrap gap-2" role="radiogroup" aria-labelledby="language-heading">
                            {LANGUAGES.map((lang) => (
                                <button
                                    key={lang.code}
                                    onClick={() => setLanguage(lang.code)}
                                    className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition-colors ${language === lang.code
                                        ? "bg-[var(--accent)]/15 text-[var(--accent)] font-medium"
                                        : "bg-white/5 text-[var(--fg-muted)] hover:bg-white/10"
                                        }`}
                                    role="radio"
                                    aria-checked={language === lang.code}
                                >
                                    {language === lang.code && <Check className="h-3 w-3" aria-hidden="true" />}
                                    {lang.label}
                                </button>
                            ))}
                        </div>
                    </motion.section>

                    {/* Theme */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="mb-4 rounded-lg border border-white/10 bg-slate-950/60 p-4 sm:mb-6 sm:rounded-xl sm:p-5"
                        aria-labelledby="theme-heading"
                    >
                        <div className="flex items-center gap-2 mb-3 sm:mb-4">
                            <Palette className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                            <span id="theme-heading" className="font-medium text-[var(--fg-0)]">{labels.theme}</span>
                        </div>
                        <div className="flex flex-wrap gap-2 sm:gap-3" role="radiogroup" aria-labelledby="theme-heading">
                            {THEMES.map((t) => (
                                <button
                                    key={t.id}
                                    onClick={() => setTheme(t.id)}
                                    className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors ${theme === t.id
                                        ? "border-[var(--accent)] bg-[var(--accent)]/10"
                                        : "border-white/10 bg-white/5 hover:bg-white/10"
                                        }`}
                                    role="radio"
                                    aria-checked={theme === t.id}
                                >
                                    <div className={`h-4 w-4 rounded ${t.preview}`} aria-hidden="true" />
                                    <span className="text-[var(--fg-0)]">
                                        {language === "ko" ? t.labelKo : t.label}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </motion.section>

                    {/* Notifications */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mb-4 rounded-lg border border-white/10 bg-slate-950/60 p-4 sm:mb-6 sm:rounded-xl sm:p-5"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Bell className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                                <span className="font-medium text-[var(--fg-0)]">{labels.notifications}</span>
                            </div>
                            <button
                                onClick={() => setNotifications(!notifications)}
                                className={`relative h-6 w-11 rounded-full transition-colors ${notifications ? "bg-[var(--accent)]" : "bg-white/20"
                                    }`}
                                role="switch"
                                aria-checked={notifications}
                                aria-label={labels.notifications}
                            >
                                <div
                                    className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${notifications ? "left-6" : "left-1"
                                        }`}
                                    aria-hidden="true"
                                />
                            </button>
                        </div>
                    </motion.section>

                    {/* Sections */}
                    {sections.map((section, sectionIndex) => (
                        <motion.section
                            key={section.title}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.25 + sectionIndex * 0.05 }}
                            className="mb-4 rounded-lg border border-white/10 bg-slate-950/60 overflow-hidden sm:mb-6 sm:rounded-xl"
                            aria-labelledby={`section-${section.title}`}
                        >
                            <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3 sm:px-5">
                                <section.icon className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                                <span id={`section-${section.title}`} className="font-medium text-[var(--fg-0)]">
                                    {language === "ko" ? section.titleKo : section.title}
                                </span>
                            </div>
                            <div className="divide-y divide-white/5">
                                {section.items.map((item) => (
                                    <button
                                        key={item.label}
                                        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/5 sm:px-5 sm:py-4"
                                        aria-label={`${item.label}: ${item.value || labels.configure}`}
                                    >
                                        <div>
                                            <div className="text-sm text-[var(--fg-0)]">{item.label}</div>
                                            {item.value && (
                                                <div className="text-xs text-[var(--fg-muted)]">{item.value}</div>
                                            )}
                                        </div>
                                        <ChevronRight className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                                    </button>
                                ))}
                            </div>
                        </motion.section>
                    ))}
                </div>
            </div>
        </AppShell>
    );
}
