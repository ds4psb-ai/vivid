"use client";

/**
 * Crebit Footer
 *
 * Minimal footer with:
 * - Logo
 * - Copyright
 * - Social links
 */

import React from "react";
import Link from "next/link";
import { Twitter, Github, Youtube } from "lucide-react";

export function CrebitFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 py-12 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-400 flex items-center justify-center text-white text-xs font-bold">
            C
          </div>
          <span className="font-bold text-gray-900 dark:text-white">
            Crebit
          </span>
        </Link>

        {/* Copyright */}
        <div className="text-sm text-gray-500 dark:text-gray-400">
          &copy; {currentYear} Crebit AI Inc. All rights reserved.
        </div>

        {/* Social Links */}
        <div className="flex gap-6">
          <a
            href="https://twitter.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-violet-500 transition-colors"
            aria-label="Twitter"
          >
            <Twitter className="w-5 h-5" />
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-violet-500 transition-colors"
            aria-label="GitHub"
          >
            <Github className="w-5 h-5" />
          </a>
          <a
            href="https://youtube.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-violet-500 transition-colors"
            aria-label="YouTube"
          >
            <Youtube className="w-5 h-5" />
          </a>
        </div>
      </div>
    </footer>
  );
}

export default CrebitFooter;
