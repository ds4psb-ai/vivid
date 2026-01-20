"use client";

/**
 * Shortform Category Page
 *
 * 세로 숏폼 웹드라마 (9:16) IP 목록을 표시합니다.
 * 투자자 데모용 카테고리 페이지입니다.
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Play, ArrowLeft, Sparkles } from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { IPRailCard } from "@/components/home/IPRailCard";
import { useLanguage } from "@/contexts/LanguageContext";
import { Badge } from "@/components/ui/badge";
import { VERTICAL_SHORTFORM_IPS } from "@/lib/demo-ip-overrides";

export default function ShortformPage() {
  const { language } = useLanguage();
  const ko = language === "ko";

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background */}
      <AuroraBackground />

      <div className="relative z-10 min-h-screen">
        {/* Hero Section */}
        <section className="pt-12 pb-8 px-6">
          <div className="mx-auto max-w-6xl">
            {/* Back button */}
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 mb-6 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">{ko ? "홈으로" : "Back to Home"}</span>
            </Link>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center"
            >
              {/* Badge */}
              <div className="flex items-center justify-center gap-3 mb-4">
                <Badge
                  variant="outline"
                  className="border-violet-500/50 text-violet-400 text-lg px-4 py-1"
                >
                  9:16
                </Badge>
                <Badge
                  variant="secondary"
                  className="bg-violet-500/20 text-violet-400"
                >
                  {ko ? "세로 영상" : "Vertical Video"}
                </Badge>
              </div>

              {/* Title */}
              <div className="flex items-center justify-center gap-3 mb-4">
                <Play className="w-8 h-8 text-violet-500" />
                <h1 className="text-3xl md:text-4xl font-bold text-[var(--fg-0)]">
                  {ko ? "숏폼 웹드라마" : "Shortform Web Drama"}
                </h1>
              </div>

              {/* Description */}
              <p className="text-base text-[var(--fg-muted)] max-w-xl mx-auto mb-2">
                {ko
                  ? "세로 영상을 분석하고 캐릭터/스토리 변주를 생성합니다"
                  : "Analyze vertical videos and generate character/story variations"}
              </p>
              <p className="text-sm text-violet-500/80">
                {ko
                  ? "레퍼런스 분석 → 페르소나 변주 → 스토리 생성 → 숏폼 제작"
                  : "Reference Analysis → Persona Remix → Story Generation → Shortform Production"}
              </p>
            </motion.div>
          </div>
        </section>

        {/* IP Grid */}
        <div className="px-6 pb-20">
          <div className="mx-auto max-w-6xl">
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              {/* Section Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-violet-500" />
                  <h2 className="text-lg font-semibold text-[var(--fg-0)]">
                    {ko ? "이 IP로 시작하기" : "Start with these IPs"}
                  </h2>
                </div>
                <span className="text-sm text-[var(--fg-muted)]">
                  {VERTICAL_SHORTFORM_IPS.length} {ko ? "개 IP" : "IPs"}
                </span>
              </div>

              {/* IP Cards Grid */}
              {VERTICAL_SHORTFORM_IPS.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {VERTICAL_SHORTFORM_IPS.map((ip) => (
                    <Link key={ip.slug} href={`/ip/${ip.slug}`}>
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
                      />
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-[var(--fg-muted)]">
                    {ko
                      ? "숏폼 IP가 곧 추가됩니다"
                      : "Shortform IPs coming soon"}
                  </p>
                </div>
              )}
            </motion.section>

            {/* Workflow Hint */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-12 p-6 rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-transparent"
            >
              <h3 className="text-lg font-semibold text-[var(--fg-0)] mb-3">
                {ko ? "워크플로우 가이드" : "Workflow Guide"}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { step: 1, label: ko ? "레퍼런스 분석" : "Reference Decode", badge: "4D" },
                  { step: 2, label: ko ? "페르소나 변주" : "Persona Remix", badge: "AI" },
                  { step: 3, label: ko ? "스토리 변주" : "Story Variation", badge: "2D" },
                  { step: 4, label: ko ? "숏폼 생성" : "Generate Shortform", badge: "VEO" },
                ].map((item) => (
                  <div
                    key={item.step}
                    className="flex items-center gap-3 p-3 rounded-xl bg-white/50 dark:bg-slate-800/50"
                  >
                    <div className="w-8 h-8 rounded-full bg-violet-500 text-white text-sm font-bold flex items-center justify-center">
                      {item.step}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[var(--fg-0)]">
                        {item.label}
                      </p>
                      <span className="text-[10px] text-violet-500 font-medium">
                        {item.badge}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
