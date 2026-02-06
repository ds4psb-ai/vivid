"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ChevronsLeft, ChevronsRight, LogOut } from "lucide-react";
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
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      const saved = localStorage.getItem(LS_KEY);
      return saved === null ? false : saved === "true";
    } catch {
      return false;
    }
  });
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
      router.push("/");
      router.refresh();
    } catch {
      // ignore
    }
  }, [router]);

  const showTooltip = useCallback(
    (label: string, e: React.MouseEvent<HTMLElement>) => {
      if (!collapsed) return;
      const rect = e.currentTarget.getBoundingClientRect();
      setTooltip({ label, rect });
    },
    [collapsed]
  );

  const hideTooltip = useCallback(() => setTooltip(null), []);

  useEffect(() => {
    const val = collapsed
      ? "var(--sidebar-collapsed)"
      : "var(--sidebar-expanded)";
    document.documentElement.style.setProperty("--sidebar-current", val);
  }, [collapsed]);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/" && (!currentTab || currentTab === "home");
    }
    if (pathname !== "/") {
      return pathname.startsWith(href);
    }
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
        className="fixed bottom-0 left-0 top-0 z-[var(--z-fixed)] hidden border-r border-[var(--border-muted)] bg-[var(--bg-0)] md:flex md:flex-col"
        style={{
          width: collapsed
            ? "var(--sidebar-collapsed)"
            : "var(--sidebar-expanded)",
        }}
      >
        <div className="flex h-14 items-center px-3">
          <Link
            href="/"
            className="flex items-center gap-2"
            onMouseEnter={(e) => showTooltip("홈", e)}
            onMouseLeave={hideTooltip}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border-muted)] bg-[var(--surface-1)] p-1.5">
              <img
                src="/assets/characters/crebit-logo.png"
                alt="Crebit"
                className="h-full w-full object-contain dark:invert"
              />
            </div>
          </Link>

          {!collapsed && (
            <span className="ml-2 truncate text-base font-semibold text-[var(--fg-0)]">
              Academy
            </span>
          )}

          <button
            type="button"
            onClick={toggle}
            className={`inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] text-[var(--fg-muted)] transition-colors hover:text-[var(--fg-0)] ${collapsed ? "mx-auto" : "ml-auto"}`}
            aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
          >
            {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-2">
          {filteredItems.map((item) => {
            const active = isActive(item.href);
            return (
              <div key={item.id}>
                {item.dividerBefore && (
                  <div className="my-2 border-t border-[var(--border-muted)]" />
                )}
                <Link
                  href={item.href}
                  onMouseEnter={(e) => showTooltip(item.label, e)}
                  onMouseLeave={hideTooltip}
                  className={`flex min-h-11 items-center gap-3 rounded-xl border px-3 text-sm font-medium transition-colors ${
                    active
                      ? "border-[var(--color-brand-primary)]/40 bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]"
                      : "border-transparent text-[var(--fg-muted)] hover:border-[var(--border-muted)] hover:bg-[var(--surface-1)] hover:text-[var(--fg-0)]"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  <SidebarIcon icon={item.icon} active={active} />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </Link>
              </div>
            );
          })}
        </nav>

        <div className="space-y-1 border-t border-[var(--border-muted)] px-2 py-2">
          <button
            type="button"
            onClick={handleLogout}
            onMouseEnter={(e) => showTooltip("로그아웃", e)}
            onMouseLeave={hideTooltip}
            className={`flex min-h-11 w-full items-center gap-3 rounded-xl border border-transparent px-3 text-sm font-medium text-[var(--fg-muted)] transition-colors hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-500 ${collapsed ? "justify-center" : ""}`}
          >
            <LogOut className="h-5 w-5 shrink-0" />
            {!collapsed && <span className="truncate">로그아웃</span>}
          </button>

          <div
            className={`flex min-h-11 items-center ${collapsed ? "justify-center" : "gap-3 px-1"}`}
            onMouseEnter={(e) => showTooltip("테마", e)}
            onMouseLeave={hideTooltip}
          >
            <ModeToggle />
            {!collapsed && <span className="text-sm text-[var(--fg-muted)]">테마</span>}
          </div>
        </div>
      </aside>

      <FloatingTooltip
        label={tooltip?.label ?? ""}
        anchorRect={tooltip?.rect ?? null}
        visible={collapsed && !!tooltip}
      />
    </>
  );
}
