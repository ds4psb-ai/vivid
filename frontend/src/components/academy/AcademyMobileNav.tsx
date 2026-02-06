"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import type { TabKey } from "@/app/academy/constants";
import { SIDEBAR_NAV_ITEMS } from "@/config/sidebar-nav";
import { ModeToggle } from "@/components/mode-toggle";
import { useSessionContext } from "@/contexts/SessionContext";
import { isAdminModeEnabled } from "@/lib/admin";
import { extractAcademyTabFromHref, isAcademyTabActive } from "./nav-utils";

interface AcademyMobileNavProps {
  currentTab: TabKey;
  onTabChange?: (tab: TabKey) => void;
}

export function AcademyMobileNav({
  currentTab,
  onTabChange,
}: AcademyMobileNavProps) {
  const router = useRouter();
  const { session } = useSessionContext();
  const isAdmin = isAdminModeEnabled(session?.user?.role);

  const items = useMemo(
    () => SIDEBAR_NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin),
    [isAdmin]
  );

  const navigateToTab = (href: string) => {
    const tab = extractAcademyTabFromHref(href);
    if (onTabChange) {
      onTabChange(tab);
      return;
    }
    router.push(href);
  };

  return (
    <div className="border-b border-[var(--border-muted)] bg-[var(--bg-0)]">
      <div className="flex items-start gap-2 px-3 py-2">
        <div className="flex-1 overflow-x-auto">
          <div className="flex min-w-max items-center gap-2 pr-2">
            {items.map((item) => {
              const Icon = item.icon;
              const active = isAcademyTabActive(currentTab, item.href);

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => navigateToTab(item.href)}
                  className={`inline-flex min-h-11 items-center gap-2 rounded-xl border px-3 text-sm font-medium transition-colors ${
                    active
                      ? "border-[var(--color-brand-primary)]/50 bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]"
                      : "border-[var(--border-muted)] bg-[var(--surface-1)] text-[var(--fg-muted)]"
                  }`}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className="h-4 w-4" />
                  <span className="whitespace-nowrap">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
        <ModeToggle />
      </div>
    </div>
  );
}
