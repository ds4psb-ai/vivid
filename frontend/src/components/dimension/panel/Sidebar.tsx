"use client";

/**
 * Sidebar - DimensionPanel.Sidebar compound component
 *
 * Container for input controls (Input, Textarea, Select, GenerateButton).
 * Includes BYOK settings footer.
 */

import { useState, type ReactNode } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { useBYOK } from "@/hooks/useBYOK";
import BYOKSettingsModal from "../BYOKSettingsModal";

export interface SidebarProps {
  /** Child input components */
  children: ReactNode;
  /** Width (default: layout sidebar token) */
  width?: string;
  /** Additional className */
  className?: string;
  /** Show BYOK settings footer (default: true) */
  showBYOKFooter?: boolean;
}

export function Sidebar({
  children,
  width = "w-[var(--layout-sidebar-width)]",
  className = "",
  showBYOKFooter = true,
}: SidebarProps) {
  const { classes } = useDimensionPanel();
  const { isBYOKEnabled } = useBYOK();
  const [showBYOKModal, setShowBYOKModal] = useState(false);

  return (
    <div
      className={`${width} flex-shrink-0 flex flex-col border-r border-slate-200 dark:border-white/10 bg-slate-50/80 dark:bg-slate-900/60 backdrop-blur-xl relative z-20 ${className}`}
    >
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
        <div className="space-y-6">{children}</div>
      </div>

      {/* BYOK Settings Footer */}
      {showBYOKFooter && (
        <div className="border-t border-slate-200 dark:border-white/5 p-4 bg-transparent">
          <button
            onClick={() => setShowBYOKModal(true)}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 transition-all group border border-transparent hover:border-slate-200 dark:hover:border-white/5"
          >
            <div className="flex items-center gap-3">
              <div
                className={`p-2 rounded-lg ${
                  isBYOKEnabled
                    ? "bg-violet-100 dark:bg-violet-500/20 text-violet-600 dark:text-violet-400"
                    : "bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-zinc-400"
                }`}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                  />
                </svg>
              </div>
              <div className="flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-600 dark:text-zinc-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">
                  API Key
                </span>
                <span
                  className={`text-[10px] ${
                    isBYOKEnabled
                      ? "text-violet-600 dark:text-violet-400"
                      : "text-slate-400 dark:text-zinc-600"
                  } group-hover:text-slate-500 dark:group-hover:text-zinc-400`}
                >
                  {isBYOKEnabled ? "✓ 내 키 사용 중" : "클릭하여 등록하기"}
                </span>
              </div>
            </div>
            <svg
              className="w-4 h-4 text-slate-400 dark:text-zinc-600 group-hover:text-slate-600 dark:group-hover:text-zinc-400 transition-transform group-hover:translate-x-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>

          {/* BYOK Settings Modal */}
          <BYOKSettingsModal
            isOpen={showBYOKModal}
            onClose={() => setShowBYOKModal(false)}
          />
        </div>
      )}
    </div>
  );
}

Sidebar.displayName = "DimensionPanel.Sidebar";
