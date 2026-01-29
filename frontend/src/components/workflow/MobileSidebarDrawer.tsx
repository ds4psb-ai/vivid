"use client";

/**
 * MobileSidebarDrawer - Mobile access to chain sidebar
 *
 * Provides a floating action button and drawer for accessing
 * the chain sidebar on mobile devices (lg: and below).
 *
 * 2026 UX Pattern: Cross-platform responsive design
 */

import { PanelRight, ChevronLeft } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useState } from "react";
import { RESPONSIVE_CONFIG } from "./workflow-configs";

export interface MobileSidebarDrawerProps {
  /** Sidebar content to render in drawer */
  children: React.ReactNode;
  /** Title for the drawer header */
  title?: string;
  /** Custom trigger button label */
  triggerLabel?: string;
}

/**
 * MobileSidebarDrawer - FAB + Sheet for mobile sidebar access
 *
 * @example
 * ```tsx
 * <MobileSidebarDrawer title="체인 요약">
 *   <UnifiedChainSidebar {...props} />
 * </MobileSidebarDrawer>
 * ```
 */
export function MobileSidebarDrawer({
  children,
  title = "체인 데이터",
  triggerLabel = "요약",
}: MobileSidebarDrawerProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Floating Action Button - Only visible on mobile (< md breakpoint) */}
      <button
        onClick={() => setOpen(true)}
        className={`
          fixed bottom-6 right-6 z-40
          ${RESPONSIVE_CONFIG.breakpoints.showMobileFab}
          flex items-center gap-2
          min-h-[48px] min-w-[48px]
          px-4 py-3
          bg-[var(--surface-1)]
          border border-[var(--border-subtle)]
          rounded-full
          shadow-lg shadow-black/20
          hover:bg-[var(--surface-2)]
          active:scale-95
          transition-all duration-200
        `}
        aria-label={`${title} 열기`}
      >
        <PanelRight className="w-5 h-5 text-[var(--fg-subtle)]" />
        <span className="text-sm font-medium text-[var(--fg-0)]">
          {triggerLabel}
        </span>
      </button>

      {/* Sheet Drawer */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          side="right"
          className={`${RESPONSIVE_CONFIG.sidebar.mobile.width} ${RESPONSIVE_CONFIG.sidebar.mobile.maxWidth} p-0 flex flex-col`}
          onClose={() => setOpen(false)}
        >
          {/* Header */}
          <SheetHeader className="p-4 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setOpen(false)}
                className="p-1 -ml-1 rounded-lg hover:bg-white/10 transition-colors"
                aria-label="닫기"
              >
                <ChevronLeft className="w-5 h-5 text-[var(--fg-subtle)]" />
              </button>
              <SheetTitle>{title}</SheetTitle>
            </div>
          </SheetHeader>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-auto">
            {children}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}

/**
 * MobileSidebarTrigger - Standalone trigger button (if not using FAB)
 *
 * Use this for custom placement of the trigger.
 */
export function MobileSidebarTrigger({
  onClick,
  className = "",
}: {
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        ${RESPONSIVE_CONFIG.breakpoints.showMobileFab}
        flex items-center gap-2
        min-h-[44px] min-w-[44px]
        px-3 py-2
        text-sm text-[var(--fg-subtle)]
        hover:text-[var(--fg-0)]
        hover:bg-white/5
        rounded-lg
        transition-colors
        ${className}
      `}
      aria-label="사이드바 열기"
    >
      <PanelRight className="w-4 h-4" />
      <span className="hidden sm:inline">요약</span>
    </button>
  );
}
