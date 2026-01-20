"use client";

/**
 * Home Page - Investor Demo Version
 *
 * Simplified layout focusing on:
 * 1. Shortform Web Drama (9:16)
 * 2. Animation MV (16:9)
 * 3. Dimension Flow CTA
 */

import React, { Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Play, Layers, ArrowRight } from "lucide-react";
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

function HomePageContent() {
  const router = useRouter();
  const { language } = useLanguage();
  const ko = language === "ko";

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background */}
      <AuroraBackground />

      <div className="relative z-10 min-h-screen">
        {/* Hero Section - 간결한 타이틀 */}
        <section className="pt-12 pb-8 px-6">
          <div className="mx-auto max-w-6xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="text-3xl md:text-4xl font-bold text-[var(--fg-0)] mb-3">
                {ko ? "IP-First 콘텐츠 생성" : "IP-First Content Creation"}
              </h1>
              <p className="text-base text-[var(--fg-muted)] max-w-xl mx-auto">
                {ko
                  ? "레퍼런스 영상을 분석하고, AI로 새로운 변주를 생성하세요"
                  : "Analyze reference videos and generate new variations with AI"}
              </p>
            </motion.div>
          </div>
        </section>

        {/* Main Content */}
        <div className="px-6 pb-20">
          <div className="mx-auto max-w-6xl space-y-12">
            {/* Rail 1: 세로 숏폼 웹드라마 */}
            {VERTICAL_SHORTFORM_IPS.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <div className="flex items-center gap-3 mb-6">
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
                <p className="text-sm text-[var(--fg-muted)] mb-6">
                  {ko
                    ? "세로 영상을 분석하고 캐릭터/스토리 변주를 생성합니다"
                    : "Analyze vertical videos and generate character/story variations"}
                </p>
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
                        aspectRatio="9:16"
                      />
                    </Link>
                  ))}
                </div>
              </motion.section>
            )}

            {/* Rail 2: 가로 애니 뮤비 */}
            {HORIZONTAL_ANIME_MV_IPS.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-emerald-500" />
                    <h2 className="text-xl font-semibold text-[var(--fg-0)]">
                      {ko ? "애니메이션 MV" : "Animation MV"}
                    </h2>
                  </div>
                  <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
                    16:9
                  </Badge>
                  <Badge variant="secondary" className="text-[10px]">
                    {ko ? "씬 일관성" : "Scene Consistency"}
                  </Badge>
                </div>
                <p className="text-sm text-[var(--fg-muted)] mb-6">
                  {ko
                    ? "가로 영상의 씬을 분석하고 캐릭터 일관성을 유지하며 새로운 씬을 생성합니다"
                    : "Analyze horizontal video scenes and generate new scenes with character consistency"}
                </p>
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
                        aspectRatio="16:9"
                      />
                    </Link>
                  ))}
                </div>
              </motion.section>
            )}

            {/* Dimension Flow CTA */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-violet-500/10 via-transparent to-emerald-500/10 p-8">
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-xl bg-violet-500/20">
                      <Sparkles className="w-6 h-6 text-violet-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-[var(--fg-0)]">
                      {ko ? "차원 플로우 시작하기" : "Start Dimension Flow"}
                    </h2>
                  </div>
                  <p className="text-sm text-[var(--fg-muted)] mb-6 max-w-xl">
                    {ko
                      ? "여러 차원 도구를 직접 조합하여 나만의 AI 파이프라인을 구축하세요. Reference Decoder → Abyss Mirror → Video Maker"
                      : "Build your own AI pipeline by combining dimension tools. Reference Decoder → Abyss Mirror → Video Maker"}
                  </p>
                  <Button
                    onClick={() => router.push("/flow")}
                    className="gap-2"
                  >
                    {ko ? "차원 플로우" : "Dimension Flow"}
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </div>
                {/* Background decoration */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-violet-500/20 to-transparent rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-emerald-500/20 to-transparent rounded-full blur-3xl" />
              </div>
            </motion.section>

            {/* Dimension App Rail */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <DimensionAppRail compact={true} showCore={true} />
            </motion.section>
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
