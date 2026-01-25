"use client";

/**
 * Crebit Navbar - Stitch V2 Design
 *
 * Minimal floating navigation with glass morphism
 * Fixed position, transparent with blur
 */

import React from "react";
import Link from "next/link";
import { Menu } from "lucide-react";

export function CrebitNavbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-6 flex justify-between items-center pointer-events-none">
      {/* Logo */}
      <Link
        href="/"
        className="flex items-center gap-3 pointer-events-auto"
      >
        <div className="w-10 h-10 bg-white text-[#030014] font-display font-bold text-xl flex items-center justify-center rounded-sm">
          C
        </div>
        <span className="font-display font-bold text-xl tracking-tighter uppercase text-white mix-blend-difference">
          Crebit
        </span>
      </Link>

      {/* Menu Button */}
      <div className="pointer-events-auto">
        <button className="w-12 h-12 rounded-full glass-panel flex items-center justify-center hover:bg-white/10 transition-colors group">
          <Menu className="w-5 h-5 text-white group-hover:rotate-90 transition-transform duration-300" />
        </button>
      </div>
    </nav>
  );
}

export default CrebitNavbar;
