"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import type { TabKey } from "@/app/academy/constants";
import { SIDEBAR_NAV_ITEMS } from "@/config/sidebar-nav";
import { ModeToggle } from "@/components/mode-toggle";
import { useSessionContext } from "@/contexts/SessionContext";
import { isAdminModeEnabled } from "@/lib/admin";
import {
  extractAcademyTabFromHref,
  isAcademyTabActive,
} from "./nav-utils";

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
    <div className="border-b border-[var(--glass-border)] bg-[var(--surface-1)]/90 backdrop-blur-xl">
      <div className="flex items-center gap-2 px-3 py-2">
        <div className="flex-1 overflow-x-auto">
          <div className="flex items-center gap-1 min-w-max pr-2">
            {items.map((item) => {
              const Icon = item.icon;
              const tab = extractAcademyTabFromHref(item.href);
              const active = isAcademyTabActive(currentTab, item.href);

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => navigateToTab(item.href)}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors
                    ${
                      active
                        ? "bg-[var(--color-brand-primary)]/12 text-[var(--color-brand-primary)]"
                        : "text-[var(--fg-muted)] hover:bg-black/5 hover:text-[var(--fg-0)]"
                    }`}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className="h-3.5 w-3.5" />
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
