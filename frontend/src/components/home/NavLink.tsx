"use client";

/**
 * NavLink - Header Navigation Link Component
 *
 * Styled link for the CrebitNavbar with:
 * - Active state indication
 * - Hover effects
 * - Glass morphism styling
 */

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

export function NavLink({ href, children, className = "" }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={`
        relative text-sm font-medium px-3 py-2 rounded-lg
        transition-all duration-200
        ${
          isActive
            ? "text-[var(--fg-0)] dark:text-white bg-black/5 dark:bg-white/10"
            : "text-[var(--fg-muted)] hover:text-[var(--fg-0)] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5"
        }
        ${className}
      `}
    >
      {children}
      {isActive && (
        <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 bg-[var(--color-brand-primary)] rounded-full" />
      )}
    </Link>
  );
}

export default NavLink;
