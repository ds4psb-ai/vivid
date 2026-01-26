"use client";

/**
 * Crebit Footer - Stitch V2 Neon Red Design
 *
 * Minimal footer with deep charcoal theme
 * Logo, version info, and navigation links
 */

import React from "react";
import Link from "next/link";

export function CrebitFooter() {
  return (
    <footer className="mt-0 border-t border-white/10 py-8 px-6 md:px-16 bg-[var(--bg-base)]">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center text-xs text-gray-500 font-bold tracking-wider uppercase">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-4 md:mb-0">
          <div className="h-6 w-6 bg-white text-black font-bold flex items-center justify-center rounded text-xs">
            C
          </div>
          <span>Crebit AI</span>
        </div>

        {/* Version Info */}
        <div>Neural Architecture v1.0 // 2023년 설립</div>

        {/* Navigation Links */}
        <div className="flex gap-6 mt-4 md:mt-0">
          <Link href="/manifesto" className="hover:text-[var(--fg-primary)] transition-colors">
            선언문
          </Link>
          <Link href="/legal" className="hover:text-[var(--fg-primary)] transition-colors">
            법적 고지
          </Link>
          <Link href="/connect" className="hover:text-[var(--fg-primary)] transition-colors">
            연결
          </Link>
        </div>
      </div>
    </footer>
  );
}

export default CrebitFooter;
