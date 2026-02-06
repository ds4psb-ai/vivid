"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Boxes,
  ChevronsLeft,
  ChevronsRight,
  Clapperboard,
  Compass,
  CreditCard,
  LogOut,
  Settings,
  Shield,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import { SidebarIcon } from "./SidebarIcon";
import { useSessionContext } from "@/contexts/SessionContext";
import { isAdminModeEnabled } from "@/lib/admin";
import { api } from "@/lib/api";

const LS_KEY = "studio-sidebar-collapsed";

interface StudioNavItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  adminOnly?: boolean;
  dividerBefore?: boolean;
}

const STUDIO_NAV_ITEMS: StudioNavItem[] = [
  { id: "academy", label: "아카데미", href: "/", icon: Compass },
  { id: "dimension", label: "디멘션", href: "/dimension", icon: Boxes },
  { id: "flow", label: "플로우", href: "/flow", icon: Workflow },
  { id: "tools", label: "도구 허브", href: "/tools", icon: Bot },
  { id: "studio", label: "스튜디오", href: "/studio", icon: Clapperboard, dividerBefore: true },
  { id: "credits", label: "크레딧", href: "/credits", icon: CreditCard },
  { id: "settings", label: "설정", href: "/settings", icon: Settings },
  { id: "admin", label: "관리자", href: "/admin/apps", icon: Shield, dividerBefore: true, adminOnly: true },
];

export function StudioSidebar() {
  const pathname = usePathname();
  const { session } = useSessionContext();
  const isAdmin = isAdminModeEnabled(session?.user?.role);
  const [collapsed, setCollapsed] = useState(true);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(LS_KEY);
      if (saved !== null) {
        setCollapsed(saved === "true");
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const width = collapsed
      ? "var(--sidebar-collapsed)"
      : "var(--sidebar-expanded)";
    document.documentElement.style.setProperty("--sidebar-current", width);
  }, [collapsed]);

  const toggle = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(LS_KEY, String(next));
      } catch {
        // ignore
      }
      return next;
    });
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    }
    window.location.href = "/";
  }, []);

  const navItems = useMemo(
    () => STUDIO_NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin),
    [isAdmin]
  );

  const isActive = useCallback(
    (href: string) => {
      if (href === "/") {
        return pathname === "/";
      }
      return pathname.startsWith(href);
    },
    [pathname]
  );

  return (
    <aside
      className="fixed top-0 left-0 bottom-0 z-[var(--z-fixed)]
                 hidden md:flex flex-col
                 bg-[var(--surface-1)] backdrop-blur-xl
                 border-r border-[var(--glass-border)]
                 transition-[width] duration-300 ease-out"
      style={{
        width: collapsed
          ? "var(--sidebar-collapsed)"
          : "var(--sidebar-expanded)",
      }}
    >
      <div className="flex items-center h-14 px-3 shrink-0">
        <Link href="/" className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 bg-white dark:bg-slate-900 flex items-center justify-center rounded-lg p-1.5 border border-[var(--glass-border)] shadow-sm shrink-0">
            <img
              src="/assets/characters/crebit-logo.png"
              alt="Crebit"
              className="w-full h-full object-contain dark:invert"
            />
          </div>
        </Link>

        {!collapsed && (
          <span className="ml-3 font-display font-bold text-lg tracking-tight text-[var(--fg-0)] truncate">
            Crebit
          </span>
        )}

        <button
          onClick={toggle}
          className={`p-1.5 rounded-lg hover:bg-black/5 text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors ${
            collapsed ? "mx-auto mt-2" : "ml-auto"
          }`}
          aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          {collapsed ? (
            <ChevronsRight className="w-4 h-4" />
          ) : (
            <ChevronsLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <div key={item.id}>
              {item.dividerBefore && (
                <div className="my-2 mx-2 border-t border-[var(--glass-border)]" />
              )}
              <Link
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl
                           transition-all duration-200 group
                           ${
                             active
                               ? "bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]"
                               : "text-[var(--fg-muted)] hover:bg-black/5 hover:text-[var(--fg-0)]"
                           }
                           ${collapsed ? "justify-center" : ""}`}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-[var(--color-brand-primary)]" />
                )}

                <SidebarIcon icon={Icon} active={active} />

                {!collapsed && (
                  <span className="text-sm font-medium truncate">
                    {item.label}
                  </span>
                )}
              </Link>
            </div>
          );
        })}
      </nav>

      <div className="shrink-0 border-t border-[var(--glass-border)] px-2 py-2 space-y-0.5">
        <button
          onClick={handleLogout}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl w-full
                     transition-all duration-200
                     text-[var(--fg-muted)] hover:bg-red-500/10 hover:text-red-500
                     ${collapsed ? "justify-center" : ""}`}
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!collapsed && (
            <span className="text-sm font-medium truncate">로그아웃</span>
          )}
        </button>

        <div
          className={`flex items-center px-3 py-2 ${
            collapsed ? "justify-center" : "gap-3"
          }`}
        >
          <ModeToggle />
          {!collapsed && (
            <span className="text-sm text-[var(--fg-muted)]">테마</span>
          )}
        </div>
      </div>
    </aside>
  );
}
