"use client";

/**
 * Crebit Navbar - Stitch V2 Design
 *
 * Minimal floating navigation with glass morphism
 * Fixed position, transparent with blur
 * Includes ModeToggle and Tools link
 */

import React from "react";
import Link from "next/link";
import { Layers } from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";

export function CrebitNavbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-6 flex justify-between items-center pointer-events-none">
      {/* Logo */}
      <Link
        href="/"
        className="flex items-center gap-3 pointer-events-auto"
      >
        <div className="w-10 h-10 bg-white flex items-center justify-center rounded-sm p-1.5">
          <img
            src="/assets/characters/crebit-logo.png"
            alt="Crebit"
            className="w-full h-full object-contain"
          />
        </div>
        <span className="font-display font-bold text-xl tracking-tighter uppercase text-white mix-blend-difference">
          Crebit
        </span>
      </Link>

      {/* Right Section */}
      <div className="flex items-center gap-3 pointer-events-auto">
        {/* Dimension Tools Link */}
        <Link
          href="/dimension"
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/10 text-white text-sm font-medium hover:bg-white/20 transition-all duration-300 group"
        >
          <Layers className="w-4 h-4 group-hover:scale-110 transition-transform" />
          <span className="hidden sm:inline">도구</span>
        </Link>

        {/* Mode Toggle */}
        <ModeToggle iconClassName="text-white" />
      </div>
    </nav>
  );
}

export default CrebitNavbar;
