"use client";

/**
 * Home Page - Clean & Simple
 *
 * Content-first layout:
 * 1. Category tabs for quick navigation
 * 2. Shortform Web Drama (9:16)
 * 3. Animation MV (16:9)
 * 4. Dimension tools
 */

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Play, Layers, Search, LogIn } from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { IPRailCard } from "@/components/home/IPRailCard";
import { DimensionAppRail } from "@/components/home/DimensionAppRail";
import { useLanguage } from "@/contexts/LanguageContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  VERTICAL_SHORTFORM_IPS,
  HORIZONTAL_ANIME_MV_IPS,
} from "@/lib/demo-ip-overrides";

type TabKey = "all" | "shortform" | "anime" | "tools";

function HomePageContent() {
  const { language } = useLanguage();
  const ko = language === "ko";
  const [activeTab, setActiveTab] = useState<TabKey>("all");

  const tabs: { key: TabKey; label: string; labelEn: string }[] = [
    { key: "all", label: "전체", labelEn: "All" },
    { key: "shortform", label: "숏폼", labelEn: "Shortform" },
    { key: "anime", label: "애니 MV", labelEn: "Anime MV" },
    { key: "tools", label: "도구", labelEn: "Tools" },
  ];

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background */}
      <AuroraBackground />

      <div className="relative z-10 min-h-screen aurora-bg">
        {/* Glass Header */}
        <header className="sticky top-0 z-50 glass-header">
          <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-violet-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold text-[var(--fg-0)]">Vivid AI</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative flex items-center">
                <Search className="absolute left-3 w-4 h-4 text-[var(--fg-muted)]" />
                <input
                  type="text"
                  placeholder={ko ? "검색..." : "Search..."}
                  className="pl-9 pr-4 py-2 text-sm glass-card rounded-xl text-[var(--fg-0)] placeholder:text-[var(--fg-muted)] focus:outline-none focus:ring-2 focus:ring-violet-500/50 w-40 md:w-56"
                />
              </div>
              <Link href="/login">
                <Button variant="ghost" size="sm" className="gap-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)]">
                  <LogIn className="w-4 h-4" />
                  {ko ? "로그인" : "Login"}
                </Button>
              </Link>
            </div>
          </div>
        </header>

        {/* Category Tabs */}
        <div className="sticky top-16 z-40 glass-header border-b border-white/5">
          <div className="mx-auto max-w-6xl px-6">
            <div className="flex gap-1 py-2 overflow-x-auto scrollbar-hide">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    activeTab === tab.key
                      ? "bg-violet-500/20 text-violet-300"
                      : "text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-white/5"
                  }`}
                >
                  {ko ? tab.label : tab.labelEn}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="px-6 py-6 pb-20">
          <div className="mx-auto max-w-6xl space-y-8">

            {/* Rail 1: 세로 숏폼 웹드라마 */}
            {(activeTab === "all" || activeTab === "shortform") && VERTICAL_SHORTFORM_IPS.length > 0 && (
              <motion.section
                key="shortform"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Play className="w-5 h-5 text-violet-500" />
                    <h2 className="text-xl font-semibold text-[var(--fg-0)]">
                      {ko ? "숏폼 웹드라마" : "Shortform Web Drama"}
                    </h2>
                  </div>
                  <Badge variant="outline" className="border-violet-500/50 text-violet-400">
                    9:16
                  </Badge>
                </div>
                <div className="content-rail">
                  {VERTICAL_SHORTFORM_IPS.map((ip) => (
                    <Link key={ip.slug} href={`/ip/${ip.slug}`} className="min-w-[168px] sm:min-w-[190px] md:min-w-0">
                      <IPRailCard
                        title={ko ? ip.titleKo : ip.titleEn}
                        subtitle={ip.genre}
                        licenseStatus="allowed"
                        genres={[ip.genre]}
                        thumbnailUrl={ip.thumbnailUrl}
                        previewVideoUrl={ip.previewVideoUrl}
                        viewCount={ip.viewCount}
                        isHot={ip.isHot}
                        isNew={ip.isNew}
                        aspectRatio="9:16"
                      />
                    </Link>
                  ))}
                </div>
              </motion.section>
            )}

            {/* Rail 2: 가로 애니 뮤비 */}
            {(activeTab === "all" || activeTab === "anime") && HORIZONTAL_ANIME_MV_IPS.length > 0 && (
              <motion.section
                key="anime"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-emerald-500" />
                    <h2 className="text-xl font-semibold text-[var(--fg-0)]">
                      {ko ? "애니메이션 MV" : "Animation MV"}
                    </h2>
                  </div>
                  <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
                    16:9
                  </Badge>
                </div>
                <div className="content-rail">
                  {HORIZONTAL_ANIME_MV_IPS.map((ip) => (
                    <Link key={ip.slug} href={`/ip/${ip.slug}`} className="min-w-[280px] sm:min-w-[320px] md:min-w-0">
                      <IPRailCard
                        title={ko ? ip.titleKo : ip.titleEn}
                        subtitle={ip.genre}
                        licenseStatus="allowed"
                        genres={[ip.genre]}
                        thumbnailUrl={ip.thumbnailUrl}
                        previewVideoUrl={ip.previewVideoUrl}
                        viewCount={ip.viewCount}
                        isHot={ip.isHot}
                        isNew={ip.isNew}
                        aspectRatio="16:9"
                      />
                    </Link>
                  ))}
                </div>
              </motion.section>
            )}

            {/* Dimension App Rail */}
            {(activeTab === "all" || activeTab === "tools") && (
              <motion.section
                key="tools"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
              >
                <DimensionAppRail compact={true} showCore={true} />
              </motion.section>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg-0)]">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
