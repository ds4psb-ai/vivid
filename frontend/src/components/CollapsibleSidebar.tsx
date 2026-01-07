"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useLanguage } from "@/contexts/LanguageContext";
import {
    Rabbit,
    Home,
    Search,
    BookOpen,
    FolderOpen,
    Layers,
    Activity,
    LayoutGrid,
    User,
    TrendingUp,
    Receipt,
    Settings,
    Sparkles,
    Zap,
    Film,
    Image as ImageIcon,
    GraduationCap,
    Gift,
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    MessageCircle,
    Moon,
    DollarSign,
    Orbit,
    Waypoints,
    CircleDashed,
} from "lucide-react";
import { CreditDisplay, ProfileSettingsPanel } from "@/components/CreditDisplay";

// Moved inside component to use translations
// const NAV_ITEMS ... 
// const NAV_GROUPS ...
// const ACADEMY_ITEM ...
// const BOTTOM_ITEM ...

// ============================================================================
// FLYOUT PANEL COMPONENT & CONFIGURATION
// ============================================================================

// Moved inside component used t()

interface FlyoutPanelProps {
    /** Unique group identifier for hover state */
    groupId: string;
    /** Title displayed at top of flyout */
    title: string;
    /** Content to render inside flyout */
    children: React.ReactNode;
    /** Width class (default: w-48) */
    width?: string;
}

/**
 * Reusable flyout panel component for sidebar hover menus.
 * Uses CSS group-hover for visibility toggling.
 */
function FlyoutPanel({ groupId, title, children, width = "w-48" }: FlyoutPanelProps) {
    return (
        <div
            className={`absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 ${width} 
                       bg-[#1a1a1c] border border-white/10 rounded-xl shadow-xl 
                       opacity-0 invisible transform -translate-x-2 
                       group-hover/${groupId}:opacity-100 group-hover/${groupId}:visible group-hover/${groupId}:translate-x-0 
                       transition-all duration-200 z-[60] p-3 
                       pointer-events-none group-hover/${groupId}:pointer-events-auto
                       before:absolute before:inset-y-0 before:-left-4 before:w-4 before:content-['']`}
        >
            <div className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
                {title}
            </div>
            {children}
        </div>
    );
}

interface NavItemProps {
    icon: React.ElementType;
    label: string;
    href: string;
    isExpanded: boolean;
    isActive: boolean;
    badge?: string;
}

function NavItem({ icon: Icon, label, href, isExpanded, isActive, badge }: NavItemProps) {
    return (
        <div className="relative group/navitem">
            <Link
                href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 relative group/item
                ${isActive
                        ? label === "차원문"
                            ? 'bg-gradient-to-r from-violet-500/20 via-violet-500/5 to-transparent text-white border-l-2 border-violet-500 shadow-[0_0_20px_rgba(139,92,246,0.15)]'
                            : 'bg-gradient-to-r from-[#4200FF]/20 via-[#4200FF]/5 to-transparent text-white border-l-2 border-[#4200FF]'
                        : 'text-slate-400 hover:bg-white/5 hover:text-white border-l-2 border-transparent hover:border-white/20'
                    }
            `}
            >
                <Icon className="w-5 h-5 shrink-0" />
                <AnimatePresence>
                    {isExpanded && (
                        <motion.span
                            initial={{ opacity: 0, width: 0 }}
                            animate={{ opacity: 1, width: "auto" }}
                            exit={{ opacity: 0, width: 0 }}
                            className="text-sm font-medium whitespace-nowrap overflow-hidden"
                        >
                            {label}
                        </motion.span>
                    )}
                </AnimatePresence>
                {badge && isExpanded && (
                    <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded ${badge === 'Hot' ? 'bg-[#FF0045] text-white' : 'bg-[#00E0FF] text-white'}`}>
                        {badge}
                    </span>
                )}
                {/* Collapsed badge indicator dot */}
                {badge && !isExpanded && (
                    <span className={`absolute top-2.5 right-3 w-2 h-2 rounded-full ring-2 ring-[#0a0a0c] ${badge === 'Hot'
                        ? 'bg-[#FF0045] shadow-[0_0_8px_rgba(255,0,69,0.8)]'
                        : 'bg-[#00E0FF]'
                        }`} />
                )}
            </Link>

            {/* Custom Tooltip for Collapsed State */}
            {!isExpanded && (
                <div className="absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 z-[60]
                              opacity-0 invisible transform -translate-x-2 group-hover/navitem:opacity-100 group-hover/navitem:visible group-hover/navitem:translate-x-0 
                              transition-all duration-200 pointer-events-none">
                    <div className="bg-[#1a1a1c] border border-white/10 text-white text-sm font-medium px-3 py-1.5 rounded-lg shadow-xl whitespace-nowrap">
                        {label}
                    </div>
                </div>
            )}
        </div>
    );
}

interface NavGroupProps {
    id: string;
    label: string;
    icon: React.ElementType;
    items: { label: string; href: string; icon: React.ElementType }[];
    isExpanded: boolean;
    pathname: string;
}

function NavGroup({ label, icon: Icon, items, isExpanded, pathname }: NavGroupProps) {
    const [isOpen, setIsOpen] = useState(false);
    const isGroupActive = items.some(item => pathname === item.href);

    return (
        <div className="relative group/navgroup">
            <button
                onClick={() => isExpanded && setIsOpen(!isOpen)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 border-l-2
                    ${isGroupActive
                        ? 'bg-gradient-to-r from-white/10 to-transparent text-white border-white/40'
                        : 'text-slate-400 hover:bg-white/5 hover:text-white border-transparent hover:border-white/20'}
                `}
            >
                <Icon className="w-5 h-5 shrink-0" />
                <AnimatePresence>
                    {isExpanded && (
                        <>
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="text-sm font-medium whitespace-nowrap flex-1 text-left"
                            >
                                {label}
                            </motion.span>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1, rotate: isOpen ? 180 : 0 }}
                                exit={{ opacity: 0 }}
                            >
                                <ChevronDown className="w-4 h-4" />
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>
            </button>
            <AnimatePresence>
                {isOpen && isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden ml-4 border-l border-white/5 pl-2"
                    >
                        {items.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors
                                    ${pathname === item.href ? 'text-white bg-white/5' : 'text-slate-500 hover:text-white'}
                                `}
                            >
                                <item.icon className="w-4 h-4" />
                                {item.label}
                            </Link>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Flyout Menu for Collapsed State */}
            {!isExpanded && (
                <div className="absolute left-[calc(100%+8px)] top-0 w-48 bg-[#1a1a1c] border border-white/10 rounded-xl shadow-xl 
                              opacity-0 invisible transform -translate-x-2 group-hover/navgroup:opacity-100 group-hover/navgroup:visible group-hover/navgroup:translate-x-0 
                              transition-all duration-200 z-[60] p-3 pointer-events-none group-hover/navgroup:pointer-events-auto
                              before:absolute before:inset-y-0 before:-left-4 before:w-4 before:content-['']">
                    <div className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">{label}</div>
                    <div className="space-y-1">
                        {items.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                            >
                                <item.icon className="w-4 h-4" />
                                {item.label}
                            </Link>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

interface CollapsibleSidebarProps {
    defaultExpanded?: boolean;
}

export default function CollapsibleSidebar({ defaultExpanded = false }: CollapsibleSidebarProps) {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);
    const pathname = usePathname();
    const [isLogoHovered, setIsLogoHovered] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const { t } = useLanguage();

    // 핵심 네비게이션 - 단일 링크 아이템
    const NAV_ITEMS: { label: string; href: string; icon: React.ElementType; badge?: string }[] = [
        { label: "차원문", href: "/dimension", icon: Orbit },
        { label: "차원 흐름", href: "/flow", icon: Waypoints },
        { label: "특이점", href: "/singularity", icon: CircleDashed },
        { label: "별자리", href: "/constellation", icon: Sparkles, badge: "New" },
    ];

    const NAV_GROUPS = [
        {
            id: "credits",
            label: "크레딧",
            icon: TrendingUp,
            items: [
                { label: "사용량", href: "/credits", icon: Activity },
                { label: "설정", href: "/settings", icon: Settings },
            ],
        },
        {
            id: "earnings",
            label: "수익",
            icon: DollarSign,
            items: [
                { label: "내 정산", href: "/settlements", icon: TrendingUp },
            ],
        },
    ];

    const ACADEMY_ITEM = { label: "Crebit ATC 1기", href: "/crebit", icon: Moon, badge: "Hot" };
    const BOTTOM_ITEM = null; // 제휴 프로그램 제거

    const FLYOUT_CONTENT = {
        affiliate: {
            title: t("partnership"),
            items: [
                { label: t("commission"), value: t("safe"), highlight: true },
                { label: t("settlement"), value: t("monthly") },
            ],
        },
        kakao: {
            title: t("supportCenter"),
            items: [
                { label: t("operatingHours"), value: "10:00 - 19:00 (KST)" },
                { label: t("responseTime"), value: "Within 10 mins" },
            ],
        },
    };

    return (
        <>
            <motion.aside
                initial={false}
                animate={{ width: isExpanded ? 220 : 56 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="fixed left-0 top-0 h-screen bg-black/40 backdrop-blur-2xl z-50 
                       border-r border-white/10 flex flex-col shadow-[10px_0_30px_rgba(0,0,0,0.5)]"
            >
                {/* Logo Toggle Button */}
                {/* Logo Toggle Button */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    onMouseEnter={() => setIsLogoHovered(true)}
                    onMouseLeave={() => setIsLogoHovered(false)}
                    className="flex items-center gap-3 px-3 py-4 hover:bg-white/5 transition-colors group"
                    aria-label={isExpanded ? "사이드바 축소" : "사이드바 확장"}
                    aria-expanded={isExpanded}
                >
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4200FF] to-[#8F00FF] 
                                flex items-center justify-center shrink-0 shadow-lg shadow-[#4200FF]/20 relative overflow-hidden">
                        <AnimatePresence mode="wait">
                            {isLogoHovered ? (
                                <motion.div
                                    key="moon"
                                    initial={{ opacity: 0, scale: 0.5, rotate: -30 }}
                                    animate={{ opacity: 1, scale: 1, rotate: 0 }}
                                    exit={{ opacity: 0, scale: 0.5, rotate: 30 }}
                                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                >
                                    <Moon className="w-5 h-5 text-yellow-300" />
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="rabbit"
                                    initial={{ opacity: 0, scale: 0.5, rotate: 30 }}
                                    animate={{ opacity: 1, scale: 1, rotate: 0 }}
                                    exit={{ opacity: 0, scale: 0.5, rotate: -30 }}
                                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                    className="w-full h-full flex items-center justify-center bg-black"
                                >
                                    <Image
                                        src="/assets/characters/chokki.png"
                                        alt="Chokki"
                                        width={32}
                                        height={32}
                                        className="object-cover w-full h-full"
                                        unoptimized
                                    />
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                    <AnimatePresence>
                        {isExpanded && (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -10 }}
                                className="flex items-center gap-2"
                            >
                                <span className="text-lg font-bold text-white">Crebit</span>
                                <ChevronLeft className="w-4 h-4 text-slate-400" />
                            </motion.div>
                        )}
                    </AnimatePresence>
                    {!isExpanded && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="absolute left-14 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <ChevronRight className="w-4 h-4 text-slate-400" />
                        </motion.div>
                    )}
                </button>

                {/* Divider */}
                <div className="mx-3 border-t border-white/5" />

                {/* Main Navigation */}
                <nav className={`flex-1 p-2 space-y-1 scrollbar-none ${isExpanded ? 'overflow-y-auto' : 'overflow-visible'}`}>
                    {/* Quick Access */}
                    {NAV_ITEMS.map((item) => (
                        <NavItem
                            key={item.href + item.label}
                            icon={item.icon}
                            label={item.label}
                            href={item.href}
                            isExpanded={isExpanded}
                            isActive={pathname === item.href}
                            badge={item.badge}
                        />
                    ))}

                    {/* Divider */}
                    <div className="my-2 mx-1 border-t border-white/5" />

                    {/* Nav Groups */}
                    {NAV_GROUPS.map((group) => (
                        <NavGroup
                            key={group.id}
                            {...group}
                            isExpanded={isExpanded}
                            pathname={pathname}
                        />
                    ))}

                    {/* Divider */}
                    <div className="my-2 mx-1 border-t border-white/5" />

                    {/* Academy (Crebit) */}
                    <div className="pt-1">
                        {isExpanded && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="px-3 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider"
                            >
                                아카데미
                            </motion.div>
                        )}
                        <NavItem
                            icon={ACADEMY_ITEM.icon}
                            label={ACADEMY_ITEM.label}
                            href={ACADEMY_ITEM.href}
                            isExpanded={isExpanded}
                            isActive={pathname === ACADEMY_ITEM.href}
                            badge={ACADEMY_ITEM.badge}
                        />
                    </div>
                </nav>

                {/* Bottom Section with Credits */}
                <div className="p-2 border-t border-white/5 space-y-1">
                    {/* Credit Display */}
                    <CreditDisplay
                        isExpanded={isExpanded}
                        onOpenSettings={() => setIsSettingsOpen(true)}
                    />

                    {/* KakaoTalk 1:1 Inquiry with Flyout */}
                    <div className="relative group/kakao">
                        <a
                            href="http://pf.kakao.com/_YxhVvj"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 text-slate-400 hover:text-[#FAE100] hover:bg-white/5"
                        >
                            <MessageCircle className="h-5 w-5 flex-shrink-0" />
                            {isExpanded && (
                                <motion.span
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                    className="whitespace-nowrap"
                                >
                                    카카오톡 1:1 상담
                                </motion.span>
                            )}
                        </a>
                        <FlyoutPanel groupId="kakao" title={FLYOUT_CONTENT.kakao.title} width="w-52">
                            <div className="space-y-2">
                                {FLYOUT_CONTENT.kakao.items.map((item) => (
                                    <div key={item.label} className="text-sm text-white">
                                        <span className="block text-slate-400 text-xs mb-1">{item.label}</span>
                                        {item.value}
                                    </div>
                                ))}
                            </div>
                        </FlyoutPanel>
                    </div>
                </div>

                {/* Bottom Branding */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="p-3 border-t border-white/5"
                        >
                            <p className="text-[10px] text-slate-500 text-center">
                                © 2025 Crebit
                            </p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.aside>

            {/* Profile Settings Panel */}
            <ProfileSettingsPanel
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />
        </>
    );
}
