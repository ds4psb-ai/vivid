"use client";

/**
 * MegaMenu - Netflix 2026 Style Mega Menu
 *
 * Shows 3 Mega Apps as simple cards:
 * - DNA Lab (DNA 연구실)
 * - Story Engine (스토리 엔진)
 * - Production Bridge (프로덕션 브릿지)
 */

import React from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { MEGA_APPS } from "@/lib/dimension-data";

// =============================================================================
// TYPES
// =============================================================================

interface MegaMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

// =============================================================================
// MEGA APP CARD
// =============================================================================

interface MegaAppCardProps {
  appKey: "dna-lab" | "story-engine" | "production";
  title: string;
  icon: string;
  description: string;
  href: string;
}

function MegaAppCard({ appKey, title, icon, description, href }: MegaAppCardProps) {
  const getColorClass = () => {
    switch (appKey) {
      case "dna-lab":
        return "text-emerald-400 group-hover:text-emerald-300";
      case "story-engine":
        return "text-amber-400 group-hover:text-amber-300";
      case "production":
        return "text-blue-400 group-hover:text-blue-300";
    }
  };

  const getBorderClass = () => {
    switch (appKey) {
      case "dna-lab":
        return "hover:border-emerald-500/30";
      case "story-engine":
        return "hover:border-amber-500/30";
      case "production":
        return "hover:border-blue-500/30";
    }
  };

  return (
    <Link
      href={href}
      className={`group flex items-center gap-4 p-4 rounded-xl
                  bg-[var(--surface-2)] dark:bg-white/[0.03]
                  border border-transparent ${getBorderClass()}
                  hover:bg-[var(--surface-3)] dark:hover:bg-white/[0.06]
                  transition-all duration-200`}
    >
      <span className="text-3xl">{icon}</span>
      <div className="flex-1 min-w-0">
        <h3 className={`text-base font-semibold ${getColorClass()} transition-colors`}>
          {title}
        </h3>
        <p className="text-sm text-[var(--fg-muted)] mt-0.5">
          {description}
        </p>
      </div>
      <ChevronRight className="w-5 h-5 text-[var(--fg-muted)] group-hover:translate-x-0.5 transition-transform" />
    </Link>
  );
}

// =============================================================================
// MEGA MENU MAIN COMPONENT
// =============================================================================

export function MegaMenu({ isOpen, onClose }: MegaMenuProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/20 dark:bg-black/40 z-40"
            onClick={onClose}
          />

          {/* Menu Panel */}
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed top-14 left-4 right-4 z-50
                       bg-[var(--surface-1)] dark:bg-[rgba(22,22,24,0.95)]
                       backdrop-blur-xl
                       border border-[var(--glass-border)]
                       rounded-2xl shadow-2xl
                       p-5 max-w-3xl mx-auto"
            role="menu"
            aria-label="도구 메뉴"
          >
            {/* 3 Mega App Cards */}
            <div className="grid grid-cols-1 gap-3">
              <MegaAppCard
                appKey="dna-lab"
                title={MEGA_APPS["dna-lab"].nameKo}
                icon={MEGA_APPS["dna-lab"].icon}
                description={MEGA_APPS["dna-lab"].descriptionKo}
                href={MEGA_APPS["dna-lab"].href}
              />
              <MegaAppCard
                appKey="story-engine"
                title={MEGA_APPS["story-engine"].nameKo}
                icon={MEGA_APPS["story-engine"].icon}
                description={MEGA_APPS["story-engine"].descriptionKo}
                href={MEGA_APPS["story-engine"].href}
              />
              <MegaAppCard
                appKey="production"
                title={MEGA_APPS["production"].nameKo}
                icon={MEGA_APPS["production"].icon}
                description={MEGA_APPS["production"].descriptionKo}
                href={MEGA_APPS["production"].href}
              />
            </div>

            {/* Quick Link to All Tools */}
            <div className="mt-4 pt-3 border-t border-[var(--glass-border)] flex justify-end">
              <Link
                href="/dimension"
                className="text-xs text-[var(--fg-muted)] hover:text-[var(--color-brand-primary)]
                         transition-colors flex items-center gap-1"
              >
                모든 도구 보기
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default MegaMenu;
