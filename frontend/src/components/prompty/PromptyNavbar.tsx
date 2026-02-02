"use client";

/**
 * PromptyNavbar - Prompty 전용 네비게이션 바
 *
 * Features:
 * - Fixed top navigation with glass morphism
 * - 4개 탭: 대시보드, 템플릿, 프로젝트, 커뮤니티
 * - Responsive design (hamburger on mobile)
 * - Dark/Light mode toggle
 */

import React, { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";

// =============================================================================
// CONSTANTS
// =============================================================================

const PROMPTY_TABS = [
  { href: "/prompty", label: "대시보드", exact: true },
  { href: "/prompty/templates", label: "템플릿", exact: false },
  { href: "/prompty/projects", label: "프로젝트", exact: false },
  { href: "/prompty/community", label: "커뮤니티", exact: false },
] as const;

// =============================================================================
// MOBILE MENU
// =============================================================================

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  const pathname = usePathname();

  const isActive = (href: string, exact: boolean) => {
    if (exact) return pathname === href;
    return pathname === href || pathname.startsWith(href + "/");
  };

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
                       bg-background
                       border-l border-border
                       p-6 flex flex-col"
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 rounded-lg
                       hover:bg-accent transition-colors"
              aria-label="메뉴 닫기"
            >
              <X className="w-5 h-5 text-muted-foreground" />
            </button>

            {/* Logo */}
            <Link href="/prompty" className="flex items-center gap-3 mb-8" onClick={onClose}>
              <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center rounded-xl text-white font-bold text-lg">
                P
              </div>
              <span className="font-bold text-xl">
                Prompty
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex-1 space-y-2">
              {PROMPTY_TABS.map((item) => {
                const active = isActive(item.href, item.exact);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    className={`block px-4 py-3 rounded-xl text-base font-medium transition-all
                      ${
                        active
                          ? "bg-violet-500/10 text-violet-600 dark:text-violet-400"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground"
                      }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* Bottom Section */}
            <div className="pt-4 border-t border-border">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">테마</span>
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
// NAV LINK COMPONENT
// =============================================================================

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  exact?: boolean;
}

function NavLink({ href, children, exact = false }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = exact ? pathname === href : pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={`
        text-sm font-medium px-3 py-2 rounded-lg transition-all duration-200
        ${
          isActive
            ? "text-violet-600 dark:text-violet-400 bg-violet-500/10"
            : "text-muted-foreground hover:text-foreground hover:bg-accent"
        }
      `}
    >
      {children}
    </Link>
  );
}

// =============================================================================
// MAIN NAVBAR COMPONENT
// =============================================================================

interface PromptyNavbarProps {
  /** Show spacer div below navbar (default: true) */
  showSpacer?: boolean;
}

export function PromptyNavbar({ showSpacer = true }: PromptyNavbarProps = {}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleCloseMobileMenu = useCallback(() => {
    setIsMobileMenuOpen(false);
  }, []);

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50">
        {/* Glass Background */}
        <div className="absolute inset-0 backdrop-blur-xl bg-background/80 border-b border-border" />

        {/* Content */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          {/* Left: Logo */}
          <Link href="/prompty" className="flex items-center gap-3 shrink-0">
            <div className="w-9 h-9 bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center rounded-xl text-white font-bold text-base shadow-sm">
              P
            </div>
            <span className="font-bold text-lg tracking-tight hidden sm:block">
              Prompty
            </span>
          </Link>

          {/* Center: Main Navigation (Desktop) */}
          <div className="hidden md:flex items-center gap-1 flex-1 justify-center">
            {PROMPTY_TABS.map((tab) => (
              <NavLink key={tab.href} href={tab.href} exact={tab.exact}>
                {tab.label}
              </NavLink>
            ))}
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            {/* Mode Toggle */}
            <ModeToggle />

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg hover:bg-accent transition-colors"
              aria-label="메뉴 열기"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <MobileMenu isOpen={isMobileMenuOpen} onClose={handleCloseMobileMenu} />

      {/* Spacer to prevent content from going under fixed navbar */}
      {showSpacer && <div className="h-14" />}
    </>
  );
}

export default PromptyNavbar;
