"use client";

/**
 * Crebit Footer - Stitch V2 Design
 *
 * Minimal footer with dark theme
 * Logo, version info, and navigation links
 */

import React from "react";
import Link from "next/link";

export function CrebitFooter() {
  return (
    <footer className="border-t border-white/5 bg-[#030014] py-12 px-6 sm:px-12 lg:px-20">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-6 h-6 bg-white text-[#030014] font-display font-bold text-xs flex items-center justify-center rounded-sm">
            C
          </div>
          <span className="font-display font-bold text-white tracking-tight">
            Crebit AI
          </span>
        </Link>

        {/* Version Info */}
        <div className="text-xs text-gray-600 font-mono">
          NEURAL ARCHITECTURE V1.0 // EST. 2023
        </div>

        {/* Navigation Links */}
        <div className="flex gap-6">
          <Link
            href="/manifesto"
            className="text-gray-500 hover:text-white transition-colors text-sm"
          >
            Manifesto
          </Link>
          <Link
            href="/legal"
            className="text-gray-500 hover:text-white transition-colors text-sm"
          >
            Legal
          </Link>
          <Link
            href="/connect"
            className="text-gray-500 hover:text-white transition-colors text-sm"
          >
            Connect
          </Link>
        </div>
      </div>
    </footer>
  );
}

export default CrebitFooter;
