"use client";

/**
 * @deprecated This sidebar component is deprecated in favor of the new
 * top header mega menu navigation (CrebitNavbar + MegaMenu).
 *
 * Migration:
 * - Use CrebitNavbar from "@/components/home/CrebitNavbar" for main navigation
 * - Use DimensionTabs from "@/components/dimension/DimensionTabs" for in-page navigation
 *
 * This file will be removed in a future version.
 * Last updated: 2026-01-27
 */

import React, { useState, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Home,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  MessageCircle,
  Orbit,
  Waypoints,
  Globe,
  Sparkles,
  FlaskConical,
  Pin,
  PinOff,
} from "lucide-react";
import { CreditDisplay, ProfileSettingsPanel } from "@/components/CreditDisplay";
import { ModeToggle } from "@/components/mode-toggle";

// ============================================================================
// TYPES
// ============================================================================

interface NavItemConfig {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

interface NavGroupConfig {
  id: string;
  sectionLabel: string;
  label: string;
  icon: React.ElementType;
  items: NavItemConfig[];
}

interface FlyoutContentItem {
  label: string;
  value: string;
  highlight?: boolean;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const NAV_ITEMS: NavItemConfig[] = [
  { label: "홈", href: "/", icon: Home },
  { label: "숏폼", href: "/shortform", icon: Sparkles, badge: "9:16" },
  { label: "애니 MV", href: "/anime-mv", icon: Orbit, badge: "16:9" },
  { label: "차원 플로우", href: "/flow", icon: Waypoints },
  { label: "크레빗 아카데미", href: "/crebit", icon: FlaskConical, badge: "Hot" },
];

const QUICK_ACTIONS: NavItemConfig[] = [];
const NAV_GROUPS: NavGroupConfig[] = [];

// Reusable style constants
const FLYOUT_BASE_STYLES = `
  absolute left-[calc(100%+8px)] bg-white dark:bg-[#1a1a1c]
  border border-black/10 dark:border-white/10 rounded-xl shadow-xl
  opacity-0 invisible transform -translate-x-2 transition-all duration-200 z-[60]
  pointer-events-none before:absolute before:inset-y-0 before:-left-4 before:w-4 before:content-['']
`;

const TOOLTIP_STYLES = `
  bg-white dark:bg-[#1a1a1c] border border-black/10 dark:border-white/10
  text-black dark:text-white text-sm font-medium px-3 py-1.5 rounded-lg shadow-xl whitespace-nowrap
`;

const NAV_ACTIVE_STYLES = {
  dimension: "bg-gradient-to-r from-violet-500/20 via-violet-500/5 to-transparent text-black dark:text-white border-l-2 border-violet-500 shadow-[0_0_20px_rgba(139,92,246,0.15)]",
  default: "bg-gradient-to-r from-[#4200FF]/20 via-[#4200FF]/5 to-transparent text-black dark:text-white border-l-2 border-[#4200FF]",
  inactive: "text-slate-600 dark:text-slate-400 hover:bg-black/5 dark:hover:bg-white/5 hover:text-black dark:hover:text-white border-l-2 border-transparent hover:border-black/20 dark:hover:border-white/20",
};

// ============================================================================
// HOOKS
// ============================================================================

function useSidebarState(defaultExpanded: boolean) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isPinned, setIsPinned] = useState(false);

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => {
      if (prev) setIsPinned(false);
      return !prev;
    });
  }, []);

  const togglePinned = useCallback(() => {
    setIsPinned((prev) => {
      if (!prev) setIsExpanded(true);
      return !prev;
    });
  }, []);

  return { isExpanded, isPinned, toggleExpanded, togglePinned };
}

// ============================================================================
// SUBCOMPONENTS
// ============================================================================

interface TooltipProps {
  label: string;
  groupId: string;
}

function Tooltip({ label, groupId }: TooltipProps) {
  return (
    <div
      className={`${FLYOUT_BASE_STYLES} top-1/2 -translate-y-1/2
        group-hover/${groupId}:opacity-100 group-hover/${groupId}:visible
        group-hover/${groupId}:translate-x-0 group-hover/${groupId}:pointer-events-auto`}
    >
      <div className={TOOLTIP_STYLES}>{label}</div>
    </div>
  );
}

interface FlyoutPanelProps {
  groupId: string;
  title: string;
  children: React.ReactNode;
  width?: string;
}

function FlyoutPanel({ groupId, title, children, width = "w-48" }: FlyoutPanelProps) {
  return (
    <div
      className={`${FLYOUT_BASE_STYLES} top-1/2 -translate-y-1/2 ${width} p-3
        group-hover/${groupId}:opacity-100 group-hover/${groupId}:visible
        group-hover/${groupId}:translate-x-0 group-hover/${groupId}:pointer-events-auto`}
    >
      <div className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">
        {title}
      </div>
      {children}
    </div>
  );
}

interface FlyoutContentProps {
  items: FlyoutContentItem[];
}

function FlyoutContent({ items }: FlyoutContentProps) {
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.label} className="text-sm text-black dark:text-white">
          <span className="block text-slate-500 dark:text-slate-400 text-xs mb-1">
            {item.label}
          </span>
          {item.value}
        </div>
      ))}
    </div>
  );
}

interface BadgeProps {
  badge: string;
  isExpanded: boolean;
}

function Badge({ badge, isExpanded }: BadgeProps) {
  const isHot = badge === "Hot";

  if (isExpanded) {
    return (
      <span
        className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded ${
          isHot ? "bg-[#FF0045] text-white" : "bg-[#00E0FF] text-white"
        }`}
      >
        {badge}
      </span>
    );
  }

  return (
    <span
      className={`absolute top-2.5 right-3 w-2 h-2 rounded-full ring-2 ring-[#0a0a0c] ${
        isHot ? "bg-[#FF0045] shadow-[0_0_8px_rgba(255,0,69,0.8)]" : "bg-[#00E0FF]"
      }`}
    />
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
  const activeStyle = isActive
    ? label === "차원문"
      ? NAV_ACTIVE_STYLES.dimension
      : NAV_ACTIVE_STYLES.default
    : NAV_ACTIVE_STYLES.inactive;

  return (
    <div className="relative group/navitem">
      <Link
        href={href}
        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 relative ${activeStyle}`}
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
        {badge && <Badge badge={badge} isExpanded={isExpanded} />}
      </Link>
      {!isExpanded && <Tooltip label={label} groupId="navitem" />}
    </div>
  );
}

interface NavGroupProps {
  id: string;
  label: string;
  icon: React.ElementType;
  items: NavItemConfig[];
  isExpanded: boolean;
  pathname: string;
}

function NavGroup({ label, icon: Icon, items, isExpanded, pathname }: NavGroupProps) {
  const [isOpen, setIsOpen] = useState(false);
  const isGroupActive = items.some((item) => pathname === item.href);

  const groupStyle = isGroupActive
    ? "bg-gradient-to-r from-black/10 dark:from-white/10 to-transparent text-black dark:text-white border-black/40 dark:border-white/40"
    : "text-gray-600 dark:text-slate-400 hover:bg-black/5 dark:hover:bg-white/5 hover:text-black dark:hover:text-white border-transparent hover:border-black/20 dark:hover:border-white/20";

  return (
    <div className="relative group/navgroup">
      <button
        onClick={() => isExpanded && setIsOpen(!isOpen)}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 border-l-2 ${groupStyle}`}
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

      {/* Expanded submenu */}
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
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  pathname === item.href
                    ? "text-black dark:text-white bg-black/5 dark:bg-white/5"
                    : "text-slate-600 dark:text-slate-500 hover:text-black dark:hover:text-white"
                }`}
              >
                <item.icon className="w-4 h-4" />
                <span className="flex-1">{item.label}</span>
                {item.badge && (
                  <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-slate-200/70 dark:bg-slate-700/60 text-slate-600 dark:text-slate-200">
                    {item.badge}
                  </span>
                )}
              </Link>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Collapsed flyout menu */}
      {!isExpanded && (
        <div
          className={`${FLYOUT_BASE_STYLES} top-0 w-48 p-3
            group-hover/navgroup:opacity-100 group-hover/navgroup:visible
            group-hover/navgroup:translate-x-0 group-hover/navgroup:pointer-events-auto`}
        >
          <div className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wider">
            {label}
          </div>
          <div className="space-y-1">
            {items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:text-black dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              >
                <item.icon className="w-4 h-4" />
                <span className="flex-1">{item.label}</span>
                {item.badge && (
                  <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-slate-200/70 dark:bg-slate-700/60 text-slate-600 dark:text-slate-200">
                    {item.badge}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

interface CollapsibleSidebarProps {
  defaultExpanded?: boolean;
}

export default function CollapsibleSidebar({ defaultExpanded = false }: CollapsibleSidebarProps) {
  const { isExpanded, isPinned, toggleExpanded, togglePinned } = useSidebarState(defaultExpanded);
  const [isLogoHovered, setIsLogoHovered] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const pathname = usePathname();
  const { t, language, setLanguage } = useLanguage();

  const flyoutContent = {
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
        className="fixed left-0 top-0 h-screen bg-white/80 dark:bg-black/40 backdrop-blur-2xl z-50 border-r border-black/10 dark:border-white/10 flex flex-col shadow-[10px_0_30px_rgba(0,0,0,0.1)] dark:shadow-[10px_0_30px_rgba(0,0,0,0.5)]"
      >
        {/* Logo Toggle + Pin */}
        <div className="flex items-center justify-between gap-2 px-3 py-4">
          <button
            onClick={toggleExpanded}
            onMouseEnter={() => setIsLogoHovered(true)}
            onMouseLeave={() => setIsLogoHovered(false)}
            className="flex flex-1 items-center gap-3 hover:bg-white/5 transition-colors group rounded-xl px-1 py-1.5"
            aria-label={isExpanded ? "사이드바 축소" : "사이드바 확장"}
            aria-expanded={isExpanded}
          >
            <div className="w-8 h-8 rounded-lg bg-white dark:bg-slate-900 flex items-center justify-center shrink-0 shadow-lg shadow-black/10 dark:shadow-white/5 relative overflow-hidden border border-black/10 dark:border-white/10">
              <motion.div
                animate={{ scale: isLogoHovered ? 1.2 : 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="w-full h-full flex items-center justify-center"
              >
                <Image
                  src="/assets/characters/crebit-logo.png"
                  alt="Crebit"
                  width={24}
                  height={24}
                  className="object-contain dark:invert"
                  unoptimized
                />
              </motion.div>
            </div>
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="flex items-center gap-2"
                >
                  <span className="text-lg font-bold text-black dark:text-white">Crebit</span>
                  <ChevronLeft className="w-4 h-4 text-slate-500 dark:text-slate-400" />
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
          {isExpanded && (
            <button
              onClick={togglePinned}
              className="h-8 w-8 rounded-lg border border-black/10 dark:border-white/10 bg-white/70 dark:bg-white/5 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors flex items-center justify-center"
              aria-pressed={isPinned}
              aria-label={isPinned ? "사이드바 고정 해제" : "사이드바 고정"}
              title={isPinned ? "고정 해제" : "고정"}
            >
              {isPinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
            </button>
          )}
        </div>

        {/* Divider */}
        <div className="mx-3 border-t border-white/5" />

        {/* Main Navigation */}
        <nav
          className={`flex-1 p-2 space-y-2 scrollbar-none ${
            isExpanded ? "overflow-y-auto" : "overflow-visible"
          }`}
        >
          {/* Quick Actions */}
          {QUICK_ACTIONS.length > 0 && (
            <div className="space-y-2">
              {isExpanded && (
                <div className="px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
                  퀵 액션
                </div>
              )}
              <div className="grid gap-2">
                {QUICK_ACTIONS.map((action) => (
                  <div key={action.href} className="relative group/quickaction">
                    <Link
                      href={action.href}
                      className={`btn btn-secondary ${
                        isExpanded
                          ? "btn-size-sm w-full justify-start px-3"
                          : "btn-size-icon w-full justify-center"
                      } gap-2`}
                      aria-label={action.label}
                    >
                      <action.icon className="h-4 w-4" />
                      {isExpanded && <span className="text-sm">{action.label}</span>}
                    </Link>
                    {!isExpanded && <Tooltip label={action.label} groupId="quickaction" />}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Items */}
          {isExpanded && (
            <div className="px-3 pt-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              탐색
            </div>
          )}
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

          {/* Nav Groups */}
          {NAV_GROUPS.length > 0 && (
            <>
              <div className="my-2 mx-1 border-t border-white/5" />
              {NAV_GROUPS.map((group) => (
                <div key={group.id} className="space-y-2">
                  {isExpanded && group.sectionLabel && (
                    <div className="px-3 pt-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
                      {group.sectionLabel}
                    </div>
                  )}
                  <NavGroup
                    id={group.id}
                    label={group.label}
                    icon={group.icon}
                    items={group.items}
                    isExpanded={isExpanded}
                    pathname={pathname}
                  />
                </div>
              ))}
            </>
          )}
        </nav>

        {/* Bottom Section with Credits */}
        <div className="p-2 border-t border-slate-200 dark:border-white/5 space-y-1">
          {/* Theme Toggle */}
          <div
            className={`flex w-full items-center py-2.5 ${
              isExpanded ? "gap-3 px-3 justify-start" : "px-0 justify-center"
            }`}
          >
            <ModeToggle />
            <AnimatePresence>
              {isExpanded && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="text-sm text-slate-600 dark:text-slate-400 font-medium whitespace-nowrap"
                >
                  테마 변경
                </motion.span>
              )}
            </AnimatePresence>
          </div>

          {/* Language Toggle */}
          <button
            onClick={() => setLanguage(language === "ko" ? "en" : "ko")}
            className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 text-slate-500 dark:text-slate-400 hover:text-violet-500 hover:bg-black/5 dark:hover:bg-white/5 w-full"
          >
            <Globe className="h-5 w-5 flex-shrink-0" />
            <AnimatePresence>
              {isExpanded && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="whitespace-nowrap"
                >
                  {language === "ko" ? "English" : "한국어"}
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          {/* Credit Display */}
          <CreditDisplay isExpanded={isExpanded} onOpenSettings={() => setIsSettingsOpen(true)} />

          {/* KakaoTalk 1:1 Inquiry with Flyout */}
          <div className="relative group/kakao">
            <a
              href="http://pf.kakao.com/_YxhVvj"
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 text-slate-500 dark:text-slate-400 hover:text-[#FAE100] hover:bg-black/5 dark:hover:bg-white/5"
            >
              <MessageCircle className="h-5 w-5 flex-shrink-0" />
              <AnimatePresence>
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
              </AnimatePresence>
            </a>
            <FlyoutPanel groupId="kakao" title={flyoutContent.kakao.title} width="w-52">
              <FlyoutContent items={flyoutContent.kakao.items} />
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
              className="p-3 border-t border-slate-200 dark:border-white/5"
            >
              <p className="text-[10px] text-slate-600 text-center">© 2026 Crebit</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.aside>

      {/* Profile Settings Panel */}
      <ProfileSettingsPanel isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </>
  );
}
