"use client";

/**
 * Home Page - Unified Home
 * 
 * Combines TemplateRail, DimensionGrid, and WorkflowCTA
 * into a single cohesive landing page.
 */

import React, { Suspense, useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BarChart3,
  CreditCard,
  FlaskConical,
  Clock,
  LayoutDashboard,
  MessageSquareText,
  Settings,
  ShieldCheck,
  Sparkles,
  Wallet,
  Wand2,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TemplateRail, DimensionGrid, WorkflowCTA } from "@/components/home";
import HomeRailSection from "@/components/home/HomeRailSection";
import { IPRailCard } from "@/components/home/IPRailCard";
import { WorkRailCard } from "@/components/home/WorkRailCard";
import { useSessionContext } from "@/contexts/SessionContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface RailItem {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  thumbnail_url: string | null;
  license_status: string;
  preset_count: number;
}

interface RailSection {
  section_id: string;
  title_ko: string;
  title_en: string;
  items: RailItem[];
  has_more: boolean;
}

function HomePageContent() {
  const router = useRouter();
  const { language } = useLanguage();
  const { isLoading: isSessionLoading } = useSessionContext();
  const [ipRails, setIpRails] = useState<RailSection[]>([]);

  // Fetch IP rails
  useEffect(() => {
    async function fetchIPRails() {
      try {
        const response = await fetch("/api/v1/ip/home/rails");
        if (response.ok) {
          const data = await response.json();
          setIpRails(data.sections || []);
        }
      } catch (err) {
        console.error("Failed to fetch IP rails:", err);
      }
    }
    fetchIPRails();
  }, []);

  const copy = useMemo(() => {
    const ko = language === "ko";
    return {
      heroTitle: ko ? "Crebit Studio 홈" : "Crebit Studio Home",
      heroSubtitle: ko
        ? "IP-First 워크플로우와 HITL 운영을 빠르게 시작하세요."
        : "Kickstart IP-first workflows and HITL operations.",
      heroSummaryTitle: ko ? "운영 스냅샷" : "Ops Snapshot",
      heroSummaryDesc: ko
        ? "승인 대기와 추천 작업을 빠르게 확인하세요."
        : "Review pending approvals and suggested tasks instantly.",
      heroCtaPrimary: ko ? "크리에이터 허브" : "Creator Hub",
      quickStart: ko ? "빠른 시작" : "Quick Start",
      creatorOps: ko ? "크리에이터 운영" : "Creator Operations",
      seeAll: ko ? "전체 보기" : "View all",
      studioCta: ko ? "작업실로 이동" : "Go to Studio",
      browseIp: ko ? "IP 갤러리 보기" : "Browse IP Gallery",
      recentWork: ko ? "최근 작업" : "Recent Work",
      recentWorkDesc: ko ? "진행 중인 작업을 이어서 진행하세요." : "Resume in-progress creations.",
      recommendedIp: ko ? "추천 IP" : "Recommended IP",
      recommendedIpDesc: ko
        ? "IP 하이라이트와 권리 상태를 한눈에 확인하세요."
        : "Preview IP highlights with rights status.",
      ipHighlight: ko ? "IP 하이라이트" : "IP Highlights",
      ipHighlightDesc: ko
        ? "추천 IP를 카드로 먼저 살펴보세요."
        : "Preview recommended IPs at a glance.",
      accountTools: ko ? "계정 & 크레딧" : "Account & Credits",
    };
  }, [language]);

  const quickLinks = [
    {
      titleKo: "IP 갤러리",
      titleEn: "IP Gallery",
      descKo: "IP 카탈로그와 프리셋을 탐색합니다.",
      descEn: "Browse IP catalog and presets.",
      href: "/ip",
      icon: Sparkles,
      badge: "IP",
    },
    {
      titleKo: "내 작업실",
      titleEn: "Studio",
      descKo: "진행 중 프로젝트를 이어서 작업합니다.",
      descEn: "Continue in-progress projects.",
      href: "/studio",
      icon: LayoutDashboard,
      badge: "WORK",
    },
    {
      titleKo: "템플릿",
      titleEn: "Templates",
      descKo: "싱귤래리티 템플릿을 시작점으로 사용합니다.",
      descEn: "Launch with curated templates.",
      href: "/singularity",
      icon: Wand2,
      badge: "NEW",
    },
  ];

  const creatorOps = [
    {
      titleKo: "승인 게이트",
      titleEn: "Approval Gate",
      descKo: "HITL 승인 큐를 관리합니다.",
      descEn: "Manage HITL approval queues.",
      href: "/creator/approvals",
      icon: ShieldCheck,
      badge: "HITL",
    },
    {
      titleKo: "피드백 루프",
      titleEn: "Feedback Loop",
      descKo: "피드백 → 학습 파이프라인을 추적합니다.",
      descEn: "Track feedback-to-learning flow.",
      href: "/creator/feedback",
      icon: MessageSquareText,
      badge: "NEW",
    },
    {
      titleKo: "A/B 실험",
      titleEn: "A/B Experiments",
      descKo: "실험 변형 성과를 비교합니다.",
      descEn: "Compare variant performance.",
      href: "/creator/experiments",
      icon: FlaskConical,
      badge: "BETA",
    },
    {
      titleKo: "분석 대시보드",
      titleEn: "Analytics",
      descKo: "성과·리스크를 통합 분석합니다.",
      descEn: "Unified performance insights.",
      href: "/creator/analytics",
      icon: BarChart3,
      badge: "INSIGHT",
    },
    {
      titleKo: "정산",
      titleEn: "Settlements",
      descKo: "수익 정산과 지급 내역을 확인합니다.",
      descEn: "Track payouts and settlements.",
      href: "/settlements",
      icon: Wallet,
      badge: "FIN",
    },
  ];

  const accountLinks = [
    {
      titleKo: "크레딧",
      titleEn: "Credits",
      descKo: "크레딧 충전 및 사용 현황을 확인합니다.",
      descEn: "Manage credit balance and usage.",
      href: "/credits",
      icon: CreditCard,
      badge: "CREDITS",
    },
    {
      titleKo: "설정",
      titleEn: "Settings",
      descKo: "계정, BYOK, 알림을 설정합니다.",
      descEn: "Configure account, BYOK, and notifications.",
      href: "/settings",
      icon: Settings,
      badge: "SETUP",
    },
  ];

  const mockIpCards = [
    {
      titleKo: "네오 서울",
      titleEn: "Neo Seoul",
      subtitleKo: "사이버펑크 도시",
      subtitleEn: "Cyberpunk city",
      license: "allowed" as const,
      genres: ["SF", "Action"],
      thumbnailUrl: "/images/ip_cards/neo_seoul.svg",
    },
    {
      titleKo: "달빛 정원",
      titleEn: "Moonlit Garden",
      subtitleKo: "판타지 왕국",
      subtitleEn: "Fantasy realm",
      license: "restricted" as const,
      genres: ["Fantasy", "Drama"],
      thumbnailUrl: "/images/ip_cards/moonlight_garden.svg",
    },
    {
      titleKo: "서울 2099",
      titleEn: "Seoul 2099",
      subtitleKo: "미래 추격전",
      subtitleEn: "Future chase",
      license: "allowed" as const,
      genres: ["Thriller", "Sci-Fi"],
      thumbnailUrl: "/images/ip_cards/seoul_2099.svg",
    },
    {
      titleKo: "금빛 극장",
      titleEn: "Golden Theatre",
      subtitleKo: "뮤지컬 무대",
      subtitleEn: "Musical stage",
      license: "prohibited" as const,
      genres: ["Musical", "Romance"],
      thumbnailUrl: "/images/ip_cards/golden_theater.svg",
    },
  ];

  const recentWorks = [
    {
      titleKo: "네오 서울 - 스토리 아크",
      titleEn: "Neo Seoul - Story Arc",
      subtitleKo: "스토리 아키텍트 • 2단계 진행 중",
      subtitleEn: "Story Architect • Phase 2 in progress",
      status: "in_progress" as const,
      updatedAt: "10분 전",
    },
    {
      titleKo: "달빛 정원 - 캐릭터 셋업",
      titleEn: "Moonlit Garden - Character Setup",
      subtitleKo: "캐릭터 디자인 • 초안",
      subtitleEn: "Character Design • Draft",
      status: "draft" as const,
      updatedAt: "1시간 전",
    },
    {
      titleKo: "서울 2099 - 레퍼런스 분석",
      titleEn: "Seoul 2099 - Reference Review",
      subtitleKo: "Aesthetic Director • 완료",
      subtitleEn: "Aesthetic Director • Completed",
      status: "complete" as const,
      updatedAt: "어제",
    },
  ];

  const recommendedCards = ipRails.length > 0
    ? ipRails[0].items.slice(0, 4).map((item) => ({
      title: language === "ko" ? item.name_ko : item.name_en,
      subtitle: `${item.preset_count} presets`,
      slug: item.slug,
      thumbnailUrl: item.thumbnail_url || undefined,
      license: item.license_status === "restricted"
        ? ("restricted" as const)
        : item.license_status === "prohibited"
          ? ("prohibited" as const)
          : ("allowed" as const),
    }))
    : mockIpCards.map((item) => ({
      title: language === "ko" ? item.titleKo : item.titleEn,
      subtitle: language === "ko" ? item.subtitleKo : item.subtitleEn,
      slug: "",
      thumbnailUrl: item.thumbnailUrl,
      license: item.license,
      genres: item.genres,
    }));


  const handleIPItemClick = (item: { slug: string }) => {
    router.push("/ip/" + item.slug);
  };

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background */}
      <AuroraBackground />

      <div className="relative z-10 min-h-screen">
        {/* Hero Section */}
        <section className="pt-10 pb-6 px-6">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <Badge variant="secondary">IP-FIRST</Badge>
                  <Badge variant="outline">HITL READY</Badge>
                </div>
                <h1 className="mt-3 text-2xl md:text-3xl font-semibold text-[var(--fg-0)]">
                  {copy.heroTitle}
                </h1>
                <p className="mt-2 text-sm text-[var(--fg-muted)] max-w-2xl">{copy.heroSubtitle}</p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Button
                    onClick={() => router.push("/studio")}
                    className="gap-2"
                    disabled={isSessionLoading}
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    {copy.studioCta}
                  </Button>
                  <Button variant="outline" onClick={() => router.push("/ip")} className="gap-2">
                    <Sparkles className="h-4 w-4" />
                    {copy.browseIp}
                  </Button>
                </div>
              </div>
              <Card className="border border-white/5 bg-[var(--surface-1)]/70 overflow-hidden">
                <div className="h-1 w-full bg-gradient-to-r from-violet-500/70 via-sky-500/50 to-emerald-500/50" />
                <CardContent className="p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[var(--fg-muted)]">{copy.heroSummaryTitle}</p>
                      <p className="text-base font-semibold text-[var(--fg-0)]">{copy.heroSummaryDesc}</p>
                    </div>
                    <Badge variant="secondary" className="text-[10px]">
                      LIVE
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between rounded-xl border border-white/5 bg-[var(--surface-2)] px-3 py-2 text-xs text-[var(--fg-muted)]">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-violet-400" />
                        승인 대기 SLA
                      </div>
                      <span className="text-[var(--fg-0)] font-semibold">24h</span>
                    </div>
                    <div className="flex items-center justify-between rounded-xl border border-white/5 bg-[var(--surface-2)] px-3 py-2 text-xs text-[var(--fg-muted)]">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="h-4 w-4 text-emerald-400" />
                        승인 처리율
                      </div>
                      <span className="text-[var(--fg-0)] font-semibold">92%</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" className="gap-2" onClick={() => router.push("/creator")}>
                      {copy.heroCtaPrimary}
                      <ArrowUpRight className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="outline" className="gap-2" onClick={() => router.push("/creator/approvals")}>
                      승인 게이트
                      <ArrowUpRight className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Main Content */}
        <div className="px-6 pb-20 space-y-12">
          <div className="mx-auto max-w-7xl space-y-12">
            {/* Recent work + Recommended IP */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
            >
              <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-[var(--fg-0)]">{copy.recentWork}</h2>
                      <p className="text-xs text-[var(--fg-muted)]">{copy.recentWorkDesc}</p>
                    </div>
                    <Button variant="ghost" onClick={() => router.push("/studio")} className="text-[var(--fg-subtle)]">
                      {copy.seeAll}
                      <ArrowUpRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {recentWorks.map((work) => (
                      <WorkRailCard
                        key={work.titleEn}
                        title={language === "ko" ? work.titleKo : work.titleEn}
                        subtitle={language === "ko" ? work.subtitleKo : work.subtitleEn}
                        status={work.status}
                        updatedAt={work.updatedAt}
                      />
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-[var(--fg-0)]">{copy.recommendedIp}</h2>
                      <p className="text-xs text-[var(--fg-muted)]">{copy.recommendedIpDesc}</p>
                    </div>
                    <Button variant="ghost" onClick={() => router.push("/ip")} className="text-[var(--fg-subtle)]">
                      {copy.seeAll}
                      <ArrowUpRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {recommendedCards.map((item, idx) => (
                      <Link key={`${item.title}-${idx}`} href={item.slug ? `/ip/${item.slug}` : "/ip"}>
                        <IPRailCard
                          title={item.title}
                          subtitle={item.subtitle}
                          licenseStatus={item.license}
                          genres={"genres" in item ? item.genres : undefined}
                          thumbnailUrl={item.thumbnailUrl}
                        />
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </motion.section>

            {/* IP Rails - IP-First UX */}
            {ipRails.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="space-y-8">
                  {ipRails.slice(0, 2).map((section) => (
                    <HomeRailSection
                      key={section.section_id}
                      sectionId={section.section_id}
                      titleKo={section.title_ko}
                      titleEn={section.title_en}
                      items={section.items}
                      hasMore={section.has_more}
                      onSeeMore={() => router.push("/ip")}
                      onItemClick={handleIPItemClick}
                    />
                  ))}
                </div>
              </motion.section>
            )}

            {ipRails.length === 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--fg-0)]">{copy.ipHighlight}</h2>
                    <p className="text-xs text-[var(--fg-muted)]">{copy.ipHighlightDesc}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => router.push("/ip")}>
                    {copy.seeAll}
                    <ArrowUpRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {mockIpCards.map((item) => (
                    <IPRailCard
                      key={item.titleEn}
                      title={language === "ko" ? item.titleKo : item.titleEn}
                      subtitle={language === "ko" ? item.subtitleKo : item.subtitleEn}
                      licenseStatus={item.license}
                      genres={item.genres}
                      thumbnailUrl={item.thumbnailUrl}
                    />
                  ))}
                </div>
              </motion.section>
            )}

            {/* Quick Start */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-[var(--fg-0)]">{copy.quickStart}</h2>
                <Button variant="ghost" className="text-[var(--fg-subtle)]">
                  {copy.seeAll}
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                {quickLinks.map((item) => (
                  <Link key={item.href} href={item.href} className="group">
                    <Card className="border border-white/5 bg-[var(--surface-1)]/70 transition-all group-hover:border-violet-500/30 group-hover:-translate-y-0.5">
                      <CardContent className="p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-3">
                            <div className="h-10 w-10 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center">
                              <item.icon className="h-5 w-5" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <div className="text-sm font-semibold text-[var(--fg-0)]">
                                  {language === "ko" ? item.titleKo : item.titleEn}
                                </div>
                                <Badge variant="secondary" className="text-[10px]">
                                  {item.badge}
                                </Badge>
                              </div>
                              <p className="mt-2 text-xs text-[var(--fg-muted)]">
                                {language === "ko" ? item.descKo : item.descEn}
                              </p>
                            </div>
                          </div>
                          <ArrowUpRight className="h-4 w-4 text-violet-400 opacity-0 transition group-hover:opacity-100" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </motion.section>

            {/* Creator Operations */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-[var(--fg-0)]">{copy.creatorOps}</h2>
                <Button variant="ghost" onClick={() => router.push("/creator")} className="text-[var(--fg-subtle)]">
                  {copy.seeAll}
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                {creatorOps.map((item) => (
                  <Link key={item.href} href={item.href} className="group">
                    <Card className="border border-white/5 bg-[var(--surface-1)]/70 transition-all group-hover:border-violet-500/30 group-hover:-translate-y-0.5">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="h-9 w-9 rounded-lg bg-violet-500/10 text-violet-400 flex items-center justify-center">
                            <item.icon className="h-4 w-4" />
                          </div>
                          <Badge variant="secondary" className="text-[10px]">
                            {item.badge}
                          </Badge>
                        </div>
                        <div className="mt-3 text-sm font-semibold text-[var(--fg-0)]">
                          {language === "ko" ? item.titleKo : item.titleEn}
                        </div>
                        <p className="mt-2 text-xs text-[var(--fg-muted)]">
                          {language === "ko" ? item.descKo : item.descEn}
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </motion.section>

            {/* Account & Credits */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-[var(--fg-0)]">{copy.accountTools}</h2>
                <Button variant="ghost" className="text-[var(--fg-subtle)]">
                  {copy.seeAll}
                  <ArrowUpRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {accountLinks.map((item) => (
                  <Link key={item.href} href={item.href} className="group">
                    <Card className="border border-white/5 bg-[var(--surface-1)]/70 transition-all group-hover:border-violet-500/30 group-hover:-translate-y-0.5">
                      <CardContent className="p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-3">
                            <div className="h-10 w-10 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center">
                              <item.icon className="h-5 w-5" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <div className="text-sm font-semibold text-[var(--fg-0)]">
                                  {language === "ko" ? item.titleKo : item.titleEn}
                                </div>
                                <Badge variant="secondary" className="text-[10px]">
                                  {item.badge}
                                </Badge>
                              </div>
                              <p className="mt-2 text-xs text-[var(--fg-muted)]">
                                {language === "ko" ? item.descKo : item.descEn}
                              </p>
                            </div>
                          </div>
                          <ArrowUpRight className="h-4 w-4 text-violet-400 opacity-0 transition group-hover:opacity-100" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </motion.section>

            {/* Template Rail */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <TemplateRail maxItems={6} />
            </motion.section>

            {/* Dimension Grid */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <DimensionGrid showTitle={true} showFilters={true} />
            </motion.section>

            {/* Workflow CTA */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <WorkflowCTA />
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
