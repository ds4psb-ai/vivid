"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Search,
    BookOpen,
    FolderOpen,
    Layers,
    Activity,
    Palette,
    LayoutGrid,
    CreditCard,
    Gift,
    Settings,
    User,
    TrendingUp,
    Receipt,
    ChevronDown,
    ChevronRight,
    Sparkles,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { isAdminModeEnabled } from "@/lib/admin";

interface NavItem {
    labelKey: string;
    labelFallback: string;
    href: string;
    icon: React.ElementType;
    badgeKey?: string;
    badgeFallback?: string;
}

interface NavGroup {
    id: string;
    labelKey: string;
    labelFallback: string;
    icon: React.ElementType;
    items: NavItem[];
    defaultOpen?: boolean;
}

const NAV_GROUPS: NavGroup[] = [
    {
        id: "research",
        labelKey: "navResearch",
        labelFallback: "Research",
        icon: Search,
        items: [
            { labelKey: "navKnowledge", labelFallback: "Knowledge Center", href: "/knowledge", icon: BookOpen },
            { labelKey: "navCollections", labelFallback: "Collections", href: "/collections", icon: FolderOpen },
            { labelKey: "navPatterns", labelFallback: "Pattern Library", href: "/patterns", icon: Layers },
            { labelKey: "navPipeline", labelFallback: "Pipeline Ops", href: "/pipeline", icon: Activity },
        ],
    },
    {
        id: "creator-hub",
        labelKey: "navCreatorHub",
        labelFallback: "Creator Hub",
        icon: Palette,
        defaultOpen: true,
        items: [
            { labelKey: "navCanvas", labelFallback: "Canvas", href: "/canvas", icon: LayoutGrid, badgeKey: "badgeNew", badgeFallback: "New" },
            { labelKey: "navTemplates", labelFallback: "Templates", href: "/", icon: Sparkles },
        ],
    },
    {
        id: "accounts",
        labelKey: "navAccounts",
        labelFallback: "Accounts",
        icon: User,
        items: [
            { labelKey: "navUsage", labelFallback: "Usage", href: "/usage", icon: TrendingUp },
            { labelKey: "navBilling", labelFallback: "Billing", href: "/billing", icon: Receipt },
            { labelKey: "navSettings", labelFallback: "Settings", href: "/settings", icon: Settings },
        ],
    },
];

const BOTTOM_NAV: NavItem[] = [
    { labelKey: "navAffiliate", labelFallback: "Affiliate", href: "/affiliate", icon: Gift },
];

const ADMIN_ONLY_ROUTES = new Set(["/knowledge", "/patterns", "/pipeline"]);

interface SidebarProps {
    creditBalance?: number;
    onMobileClose?: () => void;
}

export default function Sidebar({ creditBalance = 0, onMobileClose }: SidebarProps) {
    const pathname = usePathname();
    const { t } = useLanguage();
    const adminModeEnabled = isAdminModeEnabled();
    const [openGroups, setOpenGroups] = useState<Set<string>>(
        new Set(NAV_GROUPS.filter((g) => g.defaultOpen).map((g) => g.id))
    );

    const toggleGroup = useCallback((id: string) => {
        setOpenGroups((prev) => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    }, []);

    const isActive = useCallback((href: string) => {
        if (href === "/") return pathname === "/";
        return pathname.startsWith(href);
    }, [pathname]);

    const getLabel = useCallback((labelKey: string, fallback: string) => {
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const translated = t(labelKey as any);
            return translated !== labelKey ? translated : fallback;
        } catch {
            return fallback;
        }
    }, [t]);

    const handleNavClick = useCallback(() => {
        // Close mobile sidebar when navigating
        onMobileClose?.();
    }, [onMobileClose]);

    return (
        <aside
            className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-white/10 bg-[var(--bg-1)]/95 backdrop-blur-xl"
            role="navigation"
            aria-label="Main navigation"
        >
            {/* Logo */}
            <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
                <Link
                    href="/"
                    className="flex items-center gap-3"
                    aria-label="Vivid Home"
                    onClick={handleNavClick}
                >
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-amber-400">
                        <Sparkles className="h-5 w-5 text-white" aria-hidden="true" />
                    </div>
                    <span className="text-lg font-semibold tracking-tight">Vivid</span>
                </Link>
            </div>

            {/* Navigation Groups */}
            <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Primary navigation">
                {NAV_GROUPS.map((group) => (
                    <div key={group.id} className="mb-2">
                        <button
                            onClick={() => toggleGroup(group.id)}
                            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--fg-muted)] transition-colors hover:bg-white/5 hover:text-[var(--fg-0)]"
                            aria-expanded={openGroups.has(group.id)}
                            aria-controls={`nav-group-${group.id}`}
                        >
                            <group.icon className="h-4 w-4" aria-hidden="true" />
                            <span className="flex-1 text-left">{getLabel(group.labelKey, group.labelFallback)}</span>
                            {openGroups.has(group.id) ? (
                                <ChevronDown className="h-4 w-4" aria-hidden="true" />
                            ) : (
                                <ChevronRight className="h-4 w-4" aria-hidden="true" />
                            )}
                        </button>

                        <AnimatePresence initial={false}>
                            {openGroups.has(group.id) && (
                                <motion.div
                                    id={`nav-group-${group.id}`}
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="overflow-hidden"
                                >
                                    <div className="ml-2 mt-1 space-y-1 border-l border-white/10 pl-4">
                                        {group.items
                                            .filter((item) => adminModeEnabled || !ADMIN_ONLY_ROUTES.has(item.href))
                                            .map((item) => (
                                            <Link
                                                key={item.href}
                                                href={item.href}
                                                onClick={handleNavClick}
                                                className={`group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all duration-200 ${isActive(item.href)
                                                    ? "bg-sky-500/10 text-sky-400 font-medium shadow-[inset_3px_0_0_0_#38bdf8]"
                                                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200 hover:pl-4"
                                                    }`}
                                                aria-current={isActive(item.href) ? "page" : undefined}
                                            >
                                                <item.icon className="h-4 w-4" aria-hidden="true" />
                                                <span className="flex-1">{getLabel(item.labelKey, item.labelFallback)}</span>
                                                {item.badgeKey && (
                                                    <span className="rounded-full bg-gradient-to-r from-sky-400 to-amber-400 px-2 py-0.5 text-[10px] font-semibold text-white">
                                                        {getLabel(item.badgeKey, item.badgeFallback || "")}
                                                    </span>
                                                )}
                                            </Link>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                ))}
            </nav>

            {/* Credits Section */}
            <div className="border-t border-white/10 px-3 py-4">
                <Link
                    href="/credits"
                    onClick={handleNavClick}
                    className="flex items-center gap-3 rounded-lg bg-gradient-to-r from-sky-500/10 to-amber-500/10 px-4 py-3 transition-all hover:from-sky-500/20 hover:to-amber-500/20"
                    aria-label={`Credits: ${creditBalance.toLocaleString()} available`}
                >
                    <CreditCard className="h-5 w-5 text-[var(--accent)]" aria-hidden="true" />
                    <div className="flex-1">
                        <div className="text-xs text-[var(--fg-muted)]">{getLabel("navCredits", "Credits")}</div>
                        <div className="text-lg font-semibold text-[var(--fg-0)]">
                            {creditBalance.toLocaleString()}
                        </div>
                    </div>
                </Link>
            </div>

            {/* Bottom Navigation */}
            <div className="border-t border-white/10 px-3 py-3">
                {BOTTOM_NAV.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        onClick={handleNavClick}
                        className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${isActive(item.href)
                            ? "bg-[var(--accent)]/15 text-[var(--accent)] font-medium"
                            : "text-[var(--fg-muted)] hover:bg-white/5 hover:text-[var(--fg-0)]"
                            }`}
                        aria-current={isActive(item.href) ? "page" : undefined}
                    >
                        <item.icon className="h-4 w-4" aria-hidden="true" />
                        <span>{getLabel(item.labelKey, item.labelFallback)}</span>
                    </Link>
                ))}
            </div>
        </aside>
    );
}
