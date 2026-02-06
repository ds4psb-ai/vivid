"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  ChevronsLeft,
  ChevronsRight,
  LogOut,
} from "lucide-react";
import { SIDEBAR_NAV_ITEMS } from "@/config/sidebar-nav";
import { SidebarIcon } from "./SidebarIcon";
import { FloatingTooltip } from "./FloatingTooltip";
import { ModeToggle } from "@/components/mode-toggle";
import { useSessionContext } from "@/contexts/SessionContext";
import { isAdminModeEnabled } from "@/lib/admin";
import { api } from "@/lib/api";

const LS_KEY = "crebit-sidebar-collapsed";

export function CrebitSidebar() {
  return (
    <Suspense fallback={null}>
      <CrebitSidebarInner />
    </Suspense>
  );
}

function CrebitSidebarInner() {
  const [collapsed, setCollapsed] = useState(true);
  const [tooltip, setTooltip] = useState<{
    label: string;
    rect: DOMRect;
  } | null>(null);

  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentTab = searchParams.get("tab");
  const { session } = useSessionContext();
  const isAdmin = isAdminModeEnabled(session?.user?.role);

  // Restore collapsed state from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LS_KEY);
      if (saved !== null) setCollapsed(saved === "true");
    } catch {
      /* SSR or privacy mode */
    }
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(LS_KEY, String(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await api.logout();
      router.push("/");
      router.refresh();
    } catch {
      /* ignore */
    }
  }, [router]);

  // Tooltip handlers for collapsed mode
  const showTooltip = useCallback(
    (label: string, e: React.MouseEvent<HTMLElement>) => {
      if (!collapsed) return;
      const rect = e.currentTarget.getBoundingClientRect();
      setTooltip({ label, rect });
    },
    [collapsed]
  );
  const hideTooltip = useCallback(() => setTooltip(null), []);

  // Sync CSS variable for main content margin + hide tooltip when expanding
  useEffect(() => {
    const val = collapsed
      ? "var(--sidebar-collapsed)"
      : "var(--sidebar-expanded)";
    document.documentElement.style.setProperty("--sidebar-current", val);
    if (!collapsed) setTooltip(null);
  }, [collapsed]);

  const isActive = (href: string) => {
    // Home: "/" with no tab param
    if (href === "/") {
      return pathname === "/" && (!currentTab || currentTab === "home");
    }
    // Non-root paths (fallback for future)
    if (pathname !== "/") {
      return pathname.startsWith(href);
    }
    // /?tab=xxx matching
    try {
      const url = new URL(href, "http://x");
      return url.searchParams.get("tab") === currentTab;
    } catch {
      return false;
    }
  };

  const filteredItems = SIDEBAR_NAV_ITEMS.filter(
    (item) => !item.adminOnly || isAdmin
  );

  return (
    <>
      <aside
        className="fixed top-0 left-0 bottom-0 z-[var(--z-fixed)]
                   flex flex-col
                   bg-[var(--surface-1)] dark:bg-[rgba(10,10,12,0.92)]
                   backdrop-blur-xl
                   border-r border-[var(--glass-border)]
                   transition-[width] duration-300 ease-out
                   hidden md:flex"
        style={{
          width: collapsed
            ? "var(--sidebar-collapsed)"
            : "var(--sidebar-expanded)",
        }}
      >
        {/* ── Header: Logo + Toggle ── */}
        <div className="flex items-center h-14 px-3 shrink-0">
          <Link
            href="/"
            className="flex items-center gap-3 shrink-0"
            onMouseEnter={(e) => showTooltip("홈", e)}
            onMouseLeave={hideTooltip}
          >
            <div
              className="w-9 h-9 bg-white dark:bg-slate-900 flex items-center justify-center
                           rounded-lg p-1.5 border border-[var(--glass-border)] shadow-sm shrink-0"
            >
              <img
                src="/assets/characters/crebit-logo.png"
                alt="Crebit"
                className="w-full h-full object-contain dark:invert"
              />
            </div>
          </Link>

          {!collapsed && (
            <span className="ml-3 font-display font-bold text-lg tracking-tight text-[var(--fg-0)] dark:text-white truncate">
              Crebit
            </span>
          )}

          {/* Toggle button – pushed to right */}
          <button
            onClick={toggle}
            className={`p-1.5 rounded-lg
                       hover:bg-black/5 dark:hover:bg-white/5
                       text-[var(--fg-muted)] hover:text-[var(--fg-0)] dark:hover:text-white
                       transition-colors ${collapsed ? "mx-auto mt-2" : "ml-auto"}`}
            aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
          >
            {collapsed ? (
              <ChevronsRight className="w-4 h-4" />
            ) : (
              <ChevronsLeft className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* ── Navigation Items ── */}
        <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
          {filteredItems.map((item) => {
            const active = isActive(item.href);
            return (
              <div key={item.id}>
                {item.dividerBefore && (
                  <div className="my-2 mx-2 border-t border-[var(--glass-border)]" />
                )}
                <Link
                  href={item.href}
                  onMouseEnter={(e) => showTooltip(item.label, e)}
                  onMouseLeave={hideTooltip}
                  className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl
                             transition-all duration-200 group
                             ${
                               active
                                 ? "bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]"
                                 : "text-[var(--fg-muted)] hover:bg-black/5 dark:hover:bg-white/5 hover:text-[var(--fg-0)] dark:hover:text-white"
                             }
                             ${collapsed ? "justify-center" : ""}`}
                >
                  {/* Active left bar indicator */}
                  {active && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-[var(--color-brand-primary)]" />
                  )}

                  <SidebarIcon icon={item.icon} active={active} />

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

        {/* ── Bottom Section ── */}
        <div className="shrink-0 border-t border-[var(--glass-border)] px-2 py-2 space-y-0.5">
          {/* Logout */}
          <button
            onClick={handleLogout}
            onMouseEnter={(e) => showTooltip("로그아웃", e)}
            onMouseLeave={hideTooltip}
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

          {/* Theme Toggle */}
          <div
            className={`flex items-center px-3 py-2 ${collapsed ? "justify-center" : "gap-3"}`}
            onMouseEnter={(e) => showTooltip("테마 변경", e)}
            onMouseLeave={hideTooltip}
          >
            <ModeToggle />
            {!collapsed && (
              <span className="text-sm text-[var(--fg-muted)]">테마</span>
            )}
          </div>
        </div>
      </aside>

      {/* Portal Tooltip */}
      <FloatingTooltip
        label={tooltip?.label ?? ""}
        anchorRect={tooltip?.rect ?? null}
        visible={!!tooltip}
      />
    </>
  );
}
