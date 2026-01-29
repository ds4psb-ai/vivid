"use client";

/**
 * MegaAppShowcase Section - Stitch V2 Neon Red Design
 *
 * 분석 → 구성 → 제작
 * Minimal card design with Korean labels
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Dna, BookOpen, Clapperboard, ArrowUpRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MegaApp {
  id: string;
  name: string;
  subtitle: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
  features: string[];
  href: string;
}

const MEGA_APPS: MegaApp[] = [
  {
    id: "dna-lab",
    name: "분석",
    subtitle: "거장의 스타일을 해체하세요",
    icon: Dna,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    features: ["영상 파싱", "스타일 추출"],
    href: "/dna-lab",
  },
  {
    id: "story-engine",
    name: "구성",
    subtitle: "당신만의 이야기를 설계하세요",
    icon: BookOpen,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    features: ["스토리 설계", "프롬프트 연금술"],
    href: "/story-engine",
  },
  {
    id: "production",
    name: "제작",
    subtitle: "아이디어를 현실로 만드세요",
    icon: Clapperboard,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    features: ["영상 생성", "사운드 합성"],
    href: "/production",
  },
];

interface MegaAppShowcaseProps {
  className?: string;
}

export function MegaAppShowcase({ className }: MegaAppShowcaseProps) {
  return (
    <section className={cn("relative z-20 px-6 md:px-16 py-24 bg-[var(--bg-subtle)]", className)}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight text-white">
            창작 <span className="text-[var(--fg-primary)]">파이프라인</span>
          </h2>
          <p className="text-gray-400 max-w-lg font-light break-keep">
            세 단계로 아이디어를 완성하세요.
          </p>
        </motion.div>

        {/* 3-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {MEGA_APPS.map((app, index) => {
            const Icon = app.icon;

            return (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Link href={app.href} className="block h-full group">
                  <div
                    className={cn(
                      "relative rounded-2xl overflow-hidden",
                      "bg-[var(--bg-base)] border border-white/10",
                      "p-8 h-full min-h-[240px]",
                      "transition-all duration-300",
                      "hover:border-[var(--border-primary)]/50",
                      "hover:-translate-y-1"
                    )}
                  >
                    {/* Icon */}
                    <div
                      className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center mb-6",
                        app.bgColor
                      )}
                    >
                      <Icon className={cn("w-6 h-6", app.color)} />
                    </div>

                    {/* Title */}
                    <h3 className="text-2xl font-bold text-white mb-2">
                      {app.name}
                    </h3>

                    {/* Subtitle */}
                    <p className="text-gray-400 text-sm mb-6 break-keep">
                      {app.subtitle}
                    </p>

                    {/* Feature Tags */}
                    <div className="flex flex-wrap gap-2 mb-6">
                      {app.features.map((feature) => (
                        <span
                          key={feature}
                          className="text-xs text-gray-500"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>

                    {/* CTA */}
                    <div className="flex items-center text-xs font-bold tracking-widest text-[var(--fg-primary)] group-hover:text-white transition-colors uppercase">
                      시작하기 <ArrowUpRight className="w-4 h-4 ml-1" />
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default MegaAppShowcase;
