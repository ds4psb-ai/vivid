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
  FlaskConical,
  LayoutDashboard,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  Wallet,
  Wand2,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TemplateRail, DimensionGrid, WorkflowCTA } from "@/components/home";
import HomeRailSection from "@/components/home/HomeRailSection";
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
  const { isAuthenticated, isLoading: isSessionLoading } = useSessionContext();
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
      quickStart: ko ? "빠른 시작" : "Quick Start",
      creatorOps: ko ? "크리에이터 운영" : "Creator Operations",
      seeAll: ko ? "전체 보기" : "View all",
      studioCta: ko ? "작업실로 이동" : "Go to Studio",
      browseIp: ko ? "IP 갤러리 보기" : "Browse IP Gallery",
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

  const handleIPItemClick = (item: { slug: string }) => {
    router.push("/ip/" + item.slug);
  };

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background */}
      <AuroraBackground />

      <div className="relative z-10 min-h-screen">
        {/* Hero Section - Minimal */}
        <section className="pt-10 pb-6 px-6">
          <div className="mx-auto max-w-7xl">
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
        </section>

        {/* Main Content */}
        <div className="px-6 pb-20 space-y-12">
          <div className="mx-auto max-w-7xl space-y-12">
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
