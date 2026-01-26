"use client";

/**
 * MegaAppShowcase Section - Stitch V2 Light Theme (Dark Mode Adapted)
 *
 * DNA Lab → Story Engine → Production Bridge
 * Premium card design with step numbers and feature badges
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Dna, BookOpen, Clapperboard, ArrowRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MegaApp {
  id: string;
  name: string;
  subtitle: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
  hoverBgColor: string;
  features: string[];
  href: string;
  step: string;
}

const MEGA_APPS: MegaApp[] = [
  {
    id: "dna-lab",
    name: "DNA Lab",
    subtitle: "거장 DNA 분석 및 오케스트레이션",
    icon: Dna,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    hoverBgColor: "group-hover:text-green-50/50",
    features: ["Video Parsing", "Aesthetic Director", "Quality Check"],
    href: "/dna-lab",
    step: "01",
  },
  {
    id: "story-engine",
    name: "Story Engine",
    subtitle: "스토리 구성 및 System Prompt 생성",
    icon: BookOpen,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    hoverBgColor: "group-hover:text-orange-50/50",
    features: ["Story Architect", "Prompt Alchemy"],
    href: "/story-engine",
    step: "02",
  },
  {
    id: "production",
    name: "Production Bridge",
    subtitle: "통합 미디어 생성 플랫폼",
    icon: Clapperboard,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    hoverBgColor: "group-hover:text-blue-50/50",
    features: ["VEO 3.1", "Kling 2.6", "Suno AI"],
    href: "/production",
    step: "03",
  },
];

interface MegaAppShowcaseProps {
  className?: string;
}

export function MegaAppShowcase({ className }: MegaAppShowcaseProps) {
  return (
    <section className={cn("relative z-20 py-20 bg-[var(--bg-subtle)]", className)}>
      <div className="max-w-7xl mx-auto px-6 md:px-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-3 tracking-tight text-white">
            당신의 창작 <span className="text-[var(--fg-primary)]">워크플로우</span>
          </h2>
          <p className="text-gray-400 max-w-lg font-light break-keep">
            DNA 분석부터 최종 제작까지, 세 단계로 완성하세요.
          </p>

          {/* Workflow Indicators */}
          <div className="flex items-center gap-6 mt-6 text-sm font-medium">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-gray-300">DNA Lab</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              <span className="text-gray-300">Story Engine</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-gray-300">Production Bridge</span>
            </div>
          </div>
        </motion.div>

        {/* Cards Container */}
        <div className="relative">
          {/* Dashed connection line (desktop) */}
          <div className="hidden lg:block absolute top-1/2 left-0 w-full h-px border-t border-dashed border-gray-700 -z-10" />

          {/* 3-Column Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {MEGA_APPS.map((app, index) => {
              const Icon = app.icon;

              return (
                <motion.div
                  key={app.id}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.15, duration: 0.5 }}
                  className="relative z-10"
                >
                  <Link href={app.href} className="block h-full group">
                    <div
                      className={cn(
                        "relative rounded-3xl overflow-hidden",
                        "bg-[var(--bg-base)] border border-gray-800",
                        "p-8 h-full min-h-[280px]",
                        "transition-all duration-300",
                        "hover:border-gray-600",
                        "hover:-translate-y-1"
                      )}
                    >
                      {/* Step Number (Background) */}
                      <div className="absolute top-0 right-0 p-4 opacity-50">
                        <span
                          className={cn(
                            "text-6xl font-black text-gray-800/80",
                            app.hoverBgColor,
                            "transition-colors"
                          )}
                        >
                          {app.step}
                        </span>
                      </div>

                      {/* Icon */}
                      <div
                        className={cn(
                          "w-10 h-10 rounded-full flex items-center justify-center mb-6",
                          app.bgColor
                        )}
                      >
                        <Icon className={cn("w-5 h-5", app.color)} />
                      </div>

                      {/* Title */}
                      <h3 className="text-xl font-bold text-white mb-4">
                        {app.name}
                      </h3>

                      {/* Feature Badges */}
                      <div className="flex flex-wrap gap-2">
                        {app.features.map((feature) => (
                          <span
                            key={feature}
                            className="px-3 py-1 rounded-full bg-gray-800 text-xs font-medium text-gray-300 border border-gray-700"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>

                      {/* Arrow Button */}
                      <div className="mt-8 flex justify-end">
                        <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-gray-400 group-hover:bg-gray-700 group-hover:text-white transition-colors">
                          <ArrowRight className="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

export default MegaAppShowcase;
