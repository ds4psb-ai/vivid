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
import { Sparkles, Play, Layers, ArrowRight, Search, LogIn, Zap, Compass } from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { IPRailCard } from "@/components/home/IPRailCard";
import { DimensionAppRail } from "@/components/home/DimensionAppRail";
import { SparkleParticles } from "@/components/ui/SparkleParticles";
import { GlowButton } from "@/components/ui/GlowButton";
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

      <div className="relative z-10 min-h-screen aurora-bg">
        {/* Glass Header - Stitch AI Generated Style */}
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
                  placeholder={ko ? "차원 검색..." : "Search Dimensions..."}
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

        {/* Main Content - IP First */}
        <div className="px-6 py-8 pb-20">
          <div className="mx-auto max-w-6xl space-y-8">
            {/* Hero - Urgent UX upgrade (clear value prop + CTA hierarchy) */}
            <motion.section
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
            >
              <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-black/60 p-8 md:p-12 lg:p-14">
                <div className="absolute inset-0 bg-gradient-to-br from-violet-600/20 via-transparent to-emerald-500/20 animate-gradient-xy" />
                <div className="absolute -top-20 right-0 h-64 w-64 rounded-full bg-violet-500/20 blur-3xl animate-float" />
                <div
                  className="absolute bottom-0 left-0 h-72 w-72 rounded-full bg-emerald-500/20 blur-3xl animate-float"
                  style={{ animationDelay: "-6s" }}
                />

                <div className="relative z-10 grid gap-10 md:grid-cols-[1.2fr_0.8fr] md:items-center">
                  <div className="space-y-5 md:space-y-6 text-center md:text-left">
                    <div className="flex flex-wrap items-center justify-center gap-2 md:justify-start">
                      <Badge variant="outline" className="border-violet-500/50 text-violet-300">
                        {ko ? "AI 콘텐츠 스튜디오" : "AI Content Studio"}
                      </Badge>
                      <Badge variant="secondary" className="text-[10px] uppercase tracking-widest">
                        {ko ? "차원 플로우" : "Dimension Flow"}
                      </Badge>
                    </div>
                    <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold uppercase gradient-text-hero leading-[1.02] tracking-[-0.02em] max-w-[720px] mx-auto md:mx-0">
                      {ko ? "차원을 펼쳐라" : "Unleash your"}
                      <span className="block">{ko ? "Vivid 플로우" : "dimension"}</span>
                    </h1>
                    <p className="text-[15px] md:text-lg leading-relaxed text-[var(--fg-muted)] max-w-xl mx-auto md:mx-0">
                      {ko
                        ? "AI 기반 스토리텔링을 생각의 속도로. 레퍼런스 분석부터 영상 생성까지 한 번에 연결하세요."
                        : "AI-driven storytelling at the speed of thought. Connect reference decoding to video generation in one flow."}
                    </p>
                    <div className="flex flex-wrap gap-3 justify-center md:justify-start">
                      <GlowButton onClick={() => router.push("/flow")} glowColor="emerald" size="lg" className="w-full sm:w-auto">
                        {ko ? "차원 플로우 시작" : "Start Dimension Flow"}
                        <Zap className="w-4 h-4" />
                      </GlowButton>
                      <Button
                        variant="outline"
                        size="lg"
                        className="rounded-full border-white/20 text-[var(--fg-0)] hover:border-white/40 hover:bg-white/5 glass-card w-full sm:w-auto"
                        onClick={() => router.push("/ip")}
                      >
                        {ko ? "IP 둘러보기" : "Browse IP"}
                        <Compass className="w-4 h-4" />
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2 justify-center md:justify-start text-xs text-[var(--fg-muted)]">
                      <Badge variant="secondary">{ko ? "숏폼 9:16" : "Shortform 9:16"}</Badge>
                      <Badge variant="secondary">{ko ? "애니 MV 16:9" : "Animation MV 16:9"}</Badge>
                      <Badge variant="secondary">{ko ? "실시간 프리뷰" : "Realtime previews"}</Badge>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center md:text-left">
                      <div className="glass-card rounded-xl px-3 py-2">
                        <p className="text-lg font-bold text-[var(--fg-0)]">3</p>
                        <p className="text-[10px] text-[var(--fg-muted)] uppercase tracking-widest">
                          {ko ? "플로우 단계" : "Flow steps"}
                        </p>
                      </div>
                      <div className="glass-card rounded-xl px-3 py-2">
                        <p className="text-lg font-bold text-[var(--fg-0)]">2</p>
                        <p className="text-[10px] text-[var(--fg-muted)] uppercase tracking-widest">
                          {ko ? "콘텐츠 포맷" : "Formats"}
                        </p>
                      </div>
                      <div className="glass-card rounded-xl px-3 py-2">
                        <p className="text-lg font-bold text-[var(--fg-0)]">Live</p>
                        <p className="text-[10px] text-[var(--fg-muted)] uppercase tracking-widest">
                          {ko ? "프리뷰" : "Preview"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="hidden md:block">
                    <div className="glass-card rounded-2xl p-6 space-y-4">
                      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[var(--fg-muted)]">
                        <Sparkles className="h-4 w-4 text-violet-400" />
                        {ko ? "빠른 시작" : "Quick start"}
                      </div>
                      <div className="space-y-3 text-sm">
                        <div className="flex items-center gap-3 text-[var(--fg-0)]">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-500/20 text-violet-300">
                            1
                          </div>
                          {ko ? "레퍼런스 디코더" : "Reference Decoder"}
                        </div>
                        <div className="flex items-center gap-3 text-[var(--fg-0)]">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-300">
                            2
                          </div>
                          {ko ? "어비스 미러" : "Abyss Mirror"}
                        </div>
                        <div className="flex items-center gap-3 text-[var(--fg-0)]">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-500/20 text-violet-300">
                            3
                          </div>
                          {ko ? "비디오 메이커" : "Video Maker"}
                        </div>
                      </div>
                      <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-[var(--fg-muted)]">
                        {ko
                          ? "가장 빠른 경로로 결과를 확인하세요."
                          : "See results faster with the guided flow."}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.section>

            {/* Rail 1: 세로 숏폼 웹드라마 */}
            {VERTICAL_SHORTFORM_IPS.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
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
            {HORIZONTAL_ANIME_MV_IPS.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
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
                  <Badge variant="secondary" className="text-[10px]">
                    {ko ? "씬 일관성" : "Scene Consistency"}
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

            {/* Dimension Flow CTA - Upgraded with Stitch-inspired design */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="relative group">
                <div className="dimension-border">
                  <div className="dimension-content relative overflow-hidden p-8">
                  {/* Sparkle particles */}
                  <SparkleParticles count={20} />

                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 rounded-xl bg-violet-500/20 group-hover:bg-violet-500/30 transition-colors">
                        <Sparkles className="w-6 h-6 text-violet-400 group-hover:text-violet-300 transition-colors" />
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
                    <GlowButton
                      onClick={() => router.push("/flow")}
                      glowColor="violet"
                    >
                      {ko ? "차원 플로우" : "Dimension Flow"}
                      <ArrowRight className="w-4 h-4" />
                    </GlowButton>
                  </div>

                  {/* Background orbs with float animation */}
                  <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-violet-500/20 to-transparent rounded-full blur-3xl animate-float" />
                  <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-emerald-500/20 to-transparent rounded-full blur-3xl animate-float" style={{ animationDelay: '-5s' }} />
                </div>
                </div>
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
