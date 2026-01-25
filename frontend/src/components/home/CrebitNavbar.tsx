"use client";

/**
 * Crebit Navbar
 *
 * Netflix-style fixed navigation bar
 * - Logo + brand name
 * - Discover, My Studio, Community links
 * - Search, notifications, user avatar
 * - Glass morphism effect
 */

import React from "react";
import Link from "next/link";
import { Search, Bell, Menu } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface CrebitNavbarProps {
  transparent?: boolean;
}

export function CrebitNavbar({ transparent = false }: CrebitNavbarProps) {
  const { language } = useLanguage();
  const ko = language === "ko";

  const navLinks = [
    { href: "/", labelKo: "탐색", labelEn: "Discover" },
    { href: "/studio", labelKo: "내 스튜디오", labelEn: "My Studio" },
    { href: "/community", labelKo: "커뮤니티", labelEn: "Community" },
  ];

  return (
    <>
      <nav
        className={`fixed top-0 w-full z-50 transition-colors duration-300 ${
          transparent
            ? "bg-transparent"
            : "bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-400 flex items-center justify-center text-white font-bold text-lg">
                C
              </div>
              <span className="font-bold text-xl tracking-tight text-gray-900 dark:text-white">
                Crebit
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-gray-600 dark:text-gray-300 hover:text-violet-500 dark:hover:text-violet-400 font-medium transition-colors"
                >
                  {ko ? link.labelKo : link.labelEn}
                </Link>
              ))}
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-4">
              {/* Search */}
              <div className="relative hidden sm:block">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="w-4 h-4 text-gray-400" />
                </span>
                <input
                  type="text"
                  placeholder={ko ? "IP 검색..." : "Search IP..."}
                  className="block w-full pl-10 pr-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-full leading-5 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-violet-500 focus:border-violet-500 sm:text-sm transition-colors"
                />
              </div>

              {/* Notifications */}
              <button className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <Bell className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </button>

              {/* User Avatar */}
              <Link
                href="/login"
                className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-400 to-pink-400 flex items-center justify-center text-white text-sm font-semibold overflow-hidden hover:ring-2 hover:ring-violet-500 hover:ring-offset-2 dark:hover:ring-offset-gray-900 transition-all"
              >
                <span>U</span>
              </Link>

              {/* Mobile Menu Button */}
              <button className="md:hidden p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile FAB Menu */}
      <div className="fixed bottom-6 right-6 z-40 md:hidden">
        <button className="bg-violet-500 text-white p-4 rounded-full shadow-lg shadow-violet-500/40 hover:bg-violet-600 transition-colors">
          <Menu className="w-5 h-5" />
        </button>
      </div>
    </>
  );
}

export default CrebitNavbar;
