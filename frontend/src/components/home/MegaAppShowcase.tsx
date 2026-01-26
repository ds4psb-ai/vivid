"use client";

/**
 * MegaAppShowcase Section - 3 Mega App Workflow Cards
 *
 * DNA Lab → Story Engine → Production Bridge
 * Glass morphism cards with Oklch theme colors
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Dna, BookOpen, Clapperboard, ChevronRight, ArrowRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MegaApp {
  id: string;
  name: string;
  subtitle: string;
  icon: LucideIcon;
  hue: number;
  features: string[];
  href: string;
  step: number;
}

const MEGA_APPS: MegaApp[] = [
  {
    id: "dna-lab",
    name: "DNA Lab",
    subtitle: "거장 DNA 분석 및 오케스트레이션",
    icon: Dna,
    hue: 148,
    features: ["Video Parsing", "Aesthetic Director", "Abyss Mirror", "Quality Check"],
    href: "/dna-lab",
    step: 1,
  },
  {
    id: "story-engine",
    name: "Story Engine",
    subtitle: "스토리 구성 및 System Prompt 생성",
    icon: BookOpen,
    hue: 45,
    features: ["Story Architect", "Prompt Alchemy", "System Prompt"],
    href: "/story-engine",
    step: 2,
  },
  {
    id: "production",
    name: "Production Bridge",
    subtitle: "통합 미디어 생성 플랫폼",
    icon: Clapperboard,
    hue: 228,
    features: ["VEO 3.1", "Kling 2.6", "Suno AI"],
    href: "/production",
    step: 3,
  },
];

interface MegaAppShowcaseProps {
  className?: string;
}

export function MegaAppShowcase({ className }: MegaAppShowcaseProps) {
  return (
    <section className={cn("relative z-20 px-6 md:px-16 py-20 bg-[var(--bg-base)]", className)}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4 tracking-tight text-white">
            당신의 창작 <span className="text-[var(--fg-primary)]">워크플로우</span>
          </h2>
          <p className="text-gray-400 max-w-lg font-light break-keep">
            DNA 분석부터 최종 제작까지, 세 단계로 완성하세요.
          </p>
        </motion.div>
      </div>

      {/* Desktop Workflow Progress Bar */}
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="hidden md:flex items-center justify-center gap-6 mb-10"
        >
          {MEGA_APPS.map((app, index) => (
            <React.Fragment key={`progress-${app.id}`}>
              <Link href={app.href} className="flex items-center gap-2 group">
                <div
                  className="w-3 h-3 rounded-full transition-transform group-hover:scale-125"
                  style={{
                    backgroundColor: `oklch(0.64 0.18 ${app.hue})`,
                    boxShadow: `0 0 8px oklch(0.64 0.18 ${app.hue} / 0.5)`,
                  }}
                />
                <span className="text-sm text-white/60 group-hover:text-white transition-colors">
                  {app.name}
                </span>
              </Link>
              {index < MEGA_APPS.length - 1 && (
                <div className="w-16 h-px bg-gradient-to-r from-white/20 via-white/10 to-white/20" />
              )}
            </React.Fragment>
          ))}
        </motion.div>
      </div>

      {/* 3-Column Grid */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          {/* Workflow Connection Line (Desktop only) */}
          <div className="hidden md:block absolute top-1/2 left-0 right-0 -translate-y-1/2 z-0 px-12">
            <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          </div>

          {MEGA_APPS.map((app, index) => {
            const Icon = app.icon;
            const isLast = index === MEGA_APPS.length - 1;

            return (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15, duration: 0.5 }}
                className="relative z-10"
              >
                <Link href={app.href} className="block h-full">
                  <div
                    className={cn(
                      "relative rounded-2xl overflow-hidden",
                      "bg-black/40 backdrop-blur-xl",
                      "border border-white/5",
                      "p-6 h-full min-h-[320px]",
                      "transition-all duration-300",
                      "hover:-translate-y-2",
                      "group cursor-pointer"
                    )}
                    style={{
                      borderTopColor: `oklch(0.64 0.18 ${app.hue} / 0.5)`,
                      borderTopWidth: "2px",
                    }}
                  >
                    {/* Step Number */}
                    <div className="absolute top-4 right-4">
                      <span
                        className="text-xs font-bold px-2 py-1 rounded-full"
                        style={{
                          backgroundColor: `oklch(0.64 0.18 ${app.hue} / 0.15)`,
                          color: `oklch(0.74 0.18 ${app.hue})`,
                        }}
                      >
                        STEP {app.step}
                      </span>
                    </div>

                    {/* Icon with Glow */}
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center mb-5 transition-all duration-300 group-hover:scale-110"
                      style={{
                        backgroundColor: `oklch(0.64 0.18 ${app.hue} / 0.15)`,
                        boxShadow: `0 0 20px oklch(0.64 0.18 ${app.hue} / 0.2)`,
                      }}
                    >
                      <Icon
                        className="w-6 h-6"
                        style={{ color: `oklch(0.74 0.18 ${app.hue})` }}
                      />
                    </div>

                    {/* Title & Subtitle */}
                    <h3 className="text-xl font-bold text-white mb-2">{app.name}</h3>
                    <p className="text-sm text-gray-400 mb-6 break-keep">{app.subtitle}</p>

                    {/* Feature Badges */}
                    <div className="flex flex-wrap gap-2 mb-6">
                      {app.features.map((feature) => (
                        <span
                          key={feature}
                          className="px-2 py-1 rounded-full bg-white/5 text-xs text-white/60 transition-colors group-hover:bg-white/10"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>

                    {/* CTA Button */}
                    <div className="absolute bottom-6 left-6 right-6">
                      <div
                        className={cn(
                          "flex items-center justify-between",
                          "text-sm font-medium transition-colors"
                        )}
                        style={{ color: `oklch(0.74 0.18 ${app.hue})` }}
                      >
                        <span className="group-hover:underline">시작하기</span>
                        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                      </div>
                    </div>

                    {/* Hover Glow Effect */}
                    <div
                      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                      style={{
                        background: `radial-gradient(circle at 50% 0%, oklch(0.64 0.18 ${app.hue} / 0.1), transparent 70%)`,
                      }}
                    />
                  </div>
                </Link>

                {/* Workflow Arrow (between cards, desktop only) */}
                {!isLast && (
                  <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-20">
                    <div className="w-6 h-6 rounded-full bg-[var(--bg-base)] border border-white/10 flex items-center justify-center">
                      <ChevronRight className="w-4 h-4 text-white/40" />
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Mobile Workflow Indicator */}
        <div className="flex md:hidden justify-center mt-8 gap-2">
          {MEGA_APPS.map((app, index) => (
            <React.Fragment key={app.id}>
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                style={{
                  backgroundColor: `oklch(0.64 0.18 ${app.hue} / 0.2)`,
                  color: `oklch(0.74 0.18 ${app.hue})`,
                }}
              >
                {app.step}
              </div>
              {index < MEGA_APPS.length - 1 && (
                <ChevronRight className="w-5 h-5 text-white/30 self-center" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}

export default MegaAppShowcase;
