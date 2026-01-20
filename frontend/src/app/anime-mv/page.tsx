"use client";

/**
 * Anime MV Category Page
 *
 * 가로 애니메이션 MV (16:9) IP 목록을 표시합니다.
 * 씬 일관성 워크플로우를 강조한 투자자 데모용 카테고리 페이지입니다.
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Layers, ArrowLeft, Sparkles, Users, Palette, Music, Video } from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { IPRailCard } from "@/components/home/IPRailCard";
import { useLanguage } from "@/contexts/LanguageContext";
import { Badge } from "@/components/ui/badge";
import { HORIZONTAL_ANIME_MV_IPS } from "@/lib/demo-ip-overrides";

export default function AnimeMVPage() {
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
                  className="border-emerald-500/50 text-emerald-400 text-lg px-4 py-1"
                >
                  16:9
                </Badge>
                <Badge
                  variant="secondary"
                  className="bg-emerald-500/20 text-emerald-400"
                >
                  {ko ? "씬 일관성" : "Scene Consistency"}
                </Badge>
              </div>

              {/* Title */}
              <div className="flex items-center justify-center gap-3 mb-4">
                <Layers className="w-8 h-8 text-emerald-500" />
                <h1 className="text-3xl md:text-4xl font-bold text-[var(--fg-0)]">
                  {ko ? "애니메이션 MV" : "Animation MV"}
                </h1>
              </div>

              {/* Description */}
              <p className="text-base text-[var(--fg-muted)] max-w-xl mx-auto mb-2">
                {ko
                  ? "가로 영상의 씬을 분석하고 캐릭터 일관성을 유지하며 새로운 씬을 생성합니다"
                  : "Analyze horizontal video scenes and generate new scenes with character consistency"}
              </p>
              <p className="text-sm text-emerald-500/80">
                {ko
                  ? "씬 분석 → 캐릭터 DNA → 스타일 가이드 → 캐릭터 일관성 → BGM → 씬 생성"
                  : "Scene Analysis → Character DNA → Style Guide → Character Consistency → BGM → Scene Generation"}
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
                  <Sparkles className="w-5 h-5 text-emerald-500" />
                  <h2 className="text-lg font-semibold text-[var(--fg-0)]">
                    {ko ? "이 IP로 시작하기" : "Start with these IPs"}
                  </h2>
                </div>
                <span className="text-sm text-[var(--fg-muted)]">
                  {HORIZONTAL_ANIME_MV_IPS.length} {ko ? "개 IP" : "IPs"}
                </span>
              </div>

              {/* IP Cards Grid */}
              {HORIZONTAL_ANIME_MV_IPS.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {HORIZONTAL_ANIME_MV_IPS.map((ip) => (
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
                      ? "애니메이션 MV IP가 곧 추가됩니다"
                      : "Animation MV IPs coming soon"}
                  </p>
                </div>
              )}
            </motion.section>

            {/* Complex Workflow Guide */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-12 p-6 rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-transparent"
            >
              <h3 className="text-lg font-semibold text-[var(--fg-0)] mb-3 flex items-center gap-2">
                {ko ? "복합 워크플로우" : "Complex Workflow"}
                <Badge variant="secondary" className="text-[10px]">
                  {ko ? "6단계" : "6 Steps"}
                </Badge>
              </h3>
              <p className="text-sm text-[var(--fg-muted)] mb-4">
                {ko
                  ? "애니메이션 MV는 캐릭터 일관성 유지를 위해 복합 워크플로우가 필요합니다."
                  : "Animation MV requires a complex workflow to maintain character consistency."}
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {[
                  { step: 1, label: ko ? "씬 분석" : "Scene Analysis", icon: Sparkles, badge: "필수" },
                  { step: 2, label: ko ? "캐릭터 DNA" : "Character DNA", icon: Users, badge: "필수" },
                  { step: 3, label: ko ? "스타일 가이드" : "Style Guide", icon: Palette, badge: "스타일" },
                  { step: 4, label: ko ? "캐릭터 일관성" : "Consistency", icon: Users, badge: "일관성" },
                  { step: 5, label: ko ? "BGM 생성" : "BGM", icon: Music, badge: "BGM" },
                  { step: 6, label: ko ? "씬 생성" : "Scene Gen", icon: Video, badge: "씬생성" },
                ].map((item) => (
                  <div
                    key={item.step}
                    className="flex flex-col items-center gap-2 p-3 rounded-xl bg-white/50 dark:bg-slate-800/50"
                  >
                    <div className="relative">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-blue-500 text-white flex items-center justify-center shadow-lg shadow-emerald-500/20">
                        <item.icon className="w-5 h-5" />
                      </div>
                      <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-[10px] font-bold flex items-center justify-center">
                        {item.step}
                      </div>
                    </div>
                    <div className="text-center">
                      <p className="text-xs font-medium text-[var(--fg-0)]">
                        {item.label}
                      </p>
                      <span className="text-[9px] text-emerald-500 font-medium">
                        {item.badge}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Key Features */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4"
            >
              {[
                {
                  icon: Users,
                  title: ko ? "캐릭터 일관성" : "Character Consistency",
                  desc: ko ? "StoryMem + Veo Ingredients로 캐릭터 유지" : "Maintain characters with StoryMem + Veo Ingredients",
                },
                {
                  icon: Palette,
                  title: ko ? "오뜨르 블렌딩" : "Auteur Blending",
                  desc: ko ? "거장 스타일을 혼합한 고유 미학" : "Unique aesthetics blending master styles",
                },
                {
                  icon: Music,
                  title: ko ? "BGM 동기화" : "BGM Sync",
                  desc: ko ? "Suno V5로 영상에 맞는 음악 생성" : "Generate music matching video with Suno V5",
                },
              ].map((feature) => (
                <div
                  key={feature.title}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/30"
                >
                  <feature.icon className="w-6 h-6 text-emerald-500 mb-2" />
                  <h4 className="font-semibold text-[var(--fg-0)] mb-1">
                    {feature.title}
                  </h4>
                  <p className="text-sm text-[var(--fg-muted)]">{feature.desc}</p>
                </div>
              ))}
            </motion.div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
