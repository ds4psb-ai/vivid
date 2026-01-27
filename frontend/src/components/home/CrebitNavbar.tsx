"use client";

/**
 * CrebitNavbar - Netflix 2026 Style Header Navigation
 *
 * Features:
 * - Fixed top navigation with glass morphism
 * - Mega menu dropdown for tools
 * - Responsive design (hamburger on mobile)
 * - Dark/Light mode toggle
 *
 * Structure:
 * ┌──────────────────────────────────────────────────────────────────────┐
 * │ [Logo]   [홈]  [만들기 ▼]  [스튜디오]  [캐릭터]     [검색] [테마]   │
 * └──────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Menu, X, Search } from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import { MegaMenu } from "./MegaMenu";
import { NavLink } from "./NavLink";

// =============================================================================
// MOBILE MENU
// =============================================================================

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "홈" },
    { href: "/dimension", label: "만들기" },
    { href: "/studio", label: "스튜디오" },
    { href: "/characters", label: "캐릭터" },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Menu Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 bottom-0 w-72 z-50
                       bg-[var(--surface-1)] dark:bg-[#1a1a1c]
                       border-l border-[var(--glass-border)]
                       p-6 flex flex-col"
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 rounded-lg
                       hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              aria-label="메뉴 닫기"
            >
              <X className="w-5 h-5 text-[var(--fg-muted)]" />
            </button>

            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 mb-8" onClick={onClose}>
              <div className="w-10 h-10 bg-white dark:bg-slate-900 flex items-center justify-center rounded-lg p-1.5 border border-[var(--glass-border)]">
                <img
                  src="/assets/characters/crebit-logo.png"
                  alt="Crebit"
                  className="w-full h-full object-contain dark:invert"
                />
              </div>
              <span className="font-display font-bold text-xl text-[var(--fg-0)] dark:text-white">
                Crebit
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex-1 space-y-2">
              {navItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    className={`block px-4 py-3 rounded-xl text-base font-medium transition-all
                      ${
                        isActive
                          ? "bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]"
                          : "text-[var(--fg-muted)] hover:bg-black/5 dark:hover:bg-white/5 hover:text-[var(--fg-0)] dark:hover:text-white"
                      }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* Bottom Section */}
            <div className="pt-4 border-t border-[var(--glass-border)]">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--fg-muted)]">테마</span>
                <ModeToggle />
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// =============================================================================
// MAIN NAVBAR COMPONENT
// =============================================================================

interface CrebitNavbarProps {
  /** Show spacer div below navbar (default: true) */
  showSpacer?: boolean;
  /** Transparent background mode for hero overlays */
  transparent?: boolean;
}

export function CrebitNavbar({
  showSpacer = true,
  transparent = false,
}: CrebitNavbarProps = {}) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  // Close mega menu when clicking outside or navigating
  const handleCloseMegaMenu = useCallback(() => {
    setIsMenuOpen(false);
  }, []);

  // Check if tools dropdown should be active
  const isToolsActive =
    pathname.startsWith("/dimension") ||
    pathname.startsWith("/dna-lab") ||
    pathname.startsWith("/story-engine") ||
    pathname.startsWith("/production");

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50">
        {/* Glass Background */}
        <div
          className={`absolute inset-0 backdrop-blur-xl border-b transition-colors duration-300 ${
            transparent
              ? "bg-transparent border-transparent"
              : "bg-[var(--surface-1)] dark:bg-[rgba(10,10,12,0.8)] border-[var(--glass-border)]"
          }`}
        />

        {/* Content */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          {/* Left: Logo */}
          <Link href="/" className="flex items-center gap-3 shrink-0">
            <div className="w-9 h-9 bg-white dark:bg-slate-900 flex items-center justify-center rounded-lg p-1.5 border border-[var(--glass-border)] shadow-sm">
              <img
                src="/assets/characters/crebit-logo.png"
                alt="Crebit"
                className="w-full h-full object-contain dark:invert"
              />
            </div>
            <span className="font-display font-bold text-lg tracking-tight text-[var(--fg-0)] dark:text-white hidden sm:block">
              Crebit
            </span>
          </Link>

          {/* Center: Main Navigation (Desktop) */}
          <div className="hidden md:flex items-center gap-1 flex-1 justify-center">
            <NavLink href="/">홈</NavLink>

            {/* Tools Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setIsMenuOpen(true)}
              onMouseLeave={() => setIsMenuOpen(false)}
            >
              <button
                className={`
                  flex items-center gap-1 text-sm font-medium px-3 py-2 rounded-lg
                  transition-all duration-200
                  ${
                    isToolsActive || isMenuOpen
                      ? "text-[var(--fg-0)] dark:text-white bg-black/5 dark:bg-white/10"
                      : "text-[var(--fg-muted)] hover:text-[var(--fg-0)] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5"
                  }
                `}
                aria-expanded={isMenuOpen}
                aria-haspopup="true"
              >
                <span>만들기</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform duration-200 ${
                    isMenuOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              {/* Mega Menu */}
              <MegaMenu isOpen={isMenuOpen} onClose={handleCloseMegaMenu} />
            </div>

            <NavLink href="/studio">스튜디오</NavLink>
            <NavLink href="/characters">캐릭터</NavLink>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            {/* Search Button (Desktop) */}
            <button
              className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg
                       text-[var(--fg-muted)] hover:text-[var(--fg-0)] dark:hover:text-white
                       hover:bg-black/5 dark:hover:bg-white/5 transition-all"
              aria-label="검색"
            >
              <Search className="w-4 h-4" />
              <span className="text-sm hidden lg:inline">검색</span>
              <kbd className="hidden lg:inline text-[10px] px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/10 text-[var(--fg-muted)]">
                ⌘K
              </kbd>
            </button>

            {/* Mode Toggle */}
            <ModeToggle />

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              aria-label="메뉴 열기"
            >
              <Menu className="w-5 h-5 text-[var(--fg-0)] dark:text-white" />
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      {/* Spacer to prevent content from going under fixed navbar */}
      {showSpacer && <div className="h-14" />}
    </>
  );
}

export default CrebitNavbar;
