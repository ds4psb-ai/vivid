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
            A
          </div>
          <span>주식회사 아캐인</span>
        </div>

        {/* Company Info */}
        <div className="normal-case">Crebit by Arkain // AI 콘텐츠 스튜디오</div>

        {/* Navigation Links */}
        <div className="flex gap-6 mt-4 md:mt-0">
          <Link href="/terms" className="hover:text-[var(--fg-primary)] transition-colors">
            이용약관
          </Link>
          <Link href="/terms?tab=privacy" className="hover:text-[var(--fg-primary)] transition-colors">
            개인정보처리방침
          </Link>
          <a href="mailto:support@crebit.ai" className="hover:text-[var(--fg-primary)] transition-colors">
            문의
          </a>
        </div>
      </div>
    </footer>
  );
}

export default CrebitFooter;
