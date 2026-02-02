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
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, LogOut, User } from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import { api, type AuthSession } from "@/lib/api";
import { useSessionContext } from "@/contexts/SessionContext";

// =============================================================================
// CONSTANTS
// =============================================================================

const PROMPTY_TABS = [
  { href: "/", label: "대시보드", exact: true },
  { href: "/templates", label: "템플릿", exact: false },
  { href: "/projects", label: "프로젝트", exact: false },
  { href: "/community", label: "커뮤니티", exact: false },
] as const;

// =============================================================================
// MOBILE MENU
// =============================================================================

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  session: AuthSession | null;
  onLogout: () => void;
}

function MobileMenu({ isOpen, onClose, session, onLogout }: MobileMenuProps) {
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
            role="dialog"
            aria-modal="true"
            aria-label="모바일 메뉴"
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
            <Link href="/" className="flex items-center gap-3 mb-8" onClick={onClose}>
              <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center rounded-xl text-white font-bold text-lg">
                P
              </div>
              <span className="font-bold text-xl">
                Prompty
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex-1 space-y-2" aria-label="모바일 네비게이션">
              {PROMPTY_TABS.map((item) => {
                const active = isActive(item.href, item.exact);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    aria-current={active ? "page" : undefined}
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
            <div className="pt-4 border-t border-border space-y-4">
              {/* Theme Toggle */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">테마</span>
                <ModeToggle />
              </div>

              {/* Auth Section */}
              {session?.authenticated ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 px-2">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground truncate">
                      {session.user?.name || session.user?.email || "사용자"}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      onLogout();
                      onClose();
                    }}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
                             text-sm font-medium text-red-600 dark:text-red-400
                             bg-red-500/10 hover:bg-red-500/20 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    로그아웃
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  onClick={onClose}
                  className="block w-full text-center px-4 py-2.5 rounded-xl
                           text-sm font-medium text-white
                           bg-gradient-to-r from-violet-500 to-purple-600
                           hover:from-violet-600 hover:to-purple-700 transition-all"
                >
                  로그인
                </Link>
              )}
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
      role="menuitem"
      aria-current={isActive ? "page" : undefined}
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
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { session, isLoading, refresh } = useSessionContext();

  const handleLogout = useCallback(async () => {
    try {
      await api.logout();
      await refresh(); // Update SessionContext
      router.refresh();
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }, [router, refresh]);

  const handleCloseMobileMenu = useCallback(() => {
    setIsMobileMenuOpen(false);
  }, []);

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50"
        role="navigation"
        aria-label="메인 네비게이션"
      >
        {/* Glass Background */}
        <div className="absolute inset-0 backdrop-blur-xl bg-background/80 border-b border-border" aria-hidden="true" />

        {/* Content */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          {/* Left: Logo */}
          <Link href="/" className="flex items-center gap-3 shrink-0" aria-label="Prompty 홈">
            <div className="w-9 h-9 bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center rounded-xl text-white font-bold text-base shadow-sm">
              P
            </div>
            <span className="font-bold text-lg tracking-tight hidden sm:block">
              Prompty
            </span>
          </Link>

          {/* Center: Main Navigation (Desktop) */}
          <div className="hidden md:flex items-center gap-1 flex-1 justify-center" role="menubar">
            {PROMPTY_TABS.map((tab) => (
              <NavLink key={tab.href} href={tab.href} exact={tab.exact}>
                {tab.label}
              </NavLink>
            ))}
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            {/* Auth UI (Desktop) */}
            <div className="hidden md:flex items-center gap-2">
              {isLoading ? (
                <div className="w-20 h-8 bg-muted animate-pulse rounded-lg" />
              ) : session?.authenticated ? (
                <>
                  <span className="text-sm text-muted-foreground max-w-32 truncate">
                    {session.user?.name || session.user?.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                             text-muted-foreground hover:text-red-600 dark:hover:text-red-400
                             hover:bg-red-500/10 transition-colors"
                    title="로그아웃"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden lg:inline">로그아웃</span>
                  </button>
                </>
              ) : (
                <Link
                  href="/login"
                  className="px-4 py-1.5 rounded-lg text-sm font-medium text-white
                           bg-gradient-to-r from-violet-500 to-purple-600
                           hover:from-violet-600 hover:to-purple-700 transition-all"
                >
                  로그인
                </Link>
              )}
            </div>

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
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={handleCloseMobileMenu}
        session={session}
        onLogout={handleLogout}
      />

      {/* Spacer to prevent content from going under fixed navbar */}
      {showSpacer && <div className="h-14" />}
    </>
  );
}

export default PromptyNavbar;
