"use client";

/**
 * DNA Lab - Simplified Design
 *
 * 4단계 워크플로우를 심플하게 표현
 * 홈페이지 MegaAppShowcase 스타일 적용
 */

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Video, Palette, Brain, CheckCircle, ArrowUpRight, ArrowLeft, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import AppShell from "@/components/AppShell";

// Import existing panels
import VPEPanel from "@/components/dimension/VPEPanel";
import AestheticDirectorPanel from "@/components/dimension/AestheticDirectorPanel";
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";
import QualityDirectorPanel from "@/components/dimension/QualityDirectorPanel";

// Step definitions
const STEPS = [
  {
    id: "vpe",
    name: "영상 분석",
    subtitle: "Logic Vector를 추출합니다",
    icon: Video,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  {
    id: "ad",
    name: "미학 적용",
    subtitle: "거장의 스타일을 적용합니다",
    icon: Palette,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
  },
  {
    id: "mirror",
    name: "창작 DNA",
    subtitle: "페르소나 DNA를 분석합니다",
    icon: Brain,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
  },
  {
    id: "qc",
    name: "품질 검증",
    subtitle: "최종 품질을 검수합니다",
    icon: CheckCircle,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
  },
];

export default function DNALabPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <DNALabContent />
    </Suspense>
  );
}

function LoadingFallback() {
  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen flex items-center justify-center bg-black">
        <Loader2 className="w-8 h-8 animate-spin text-white/40" />
      </div>
    </AppShell>
  );
}

function DNALabContent() {
  const searchParams = useSearchParams();
  const step = searchParams?.get("step");

  // If step is selected, show the step panel
  if (step) {
    return <StepView stepId={step} />;
  }

  // Otherwise show overview
  return <OverviewView />;
}

/**
 * Overview - 4개 스텝 카드 그리드
 */
function OverviewView() {
  return (
    <AppShell showTopBar={false}>
      <section className="min-h-screen bg-[var(--bg-base)] px-6 md:px-16 py-16">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-12"
          >
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors mb-6"
            >
              <ArrowLeft className="w-4 h-4" />
              홈으로
            </Link>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight text-white">
              DNA <span className="text-[var(--fg-primary)]">분석</span>
            </h1>
            <p className="text-gray-400 max-w-lg font-light">
              영상을 분석하고 거장의 스타일을 추출하세요.
            </p>
          </motion.div>

          {/* Step Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                >
                  <Link href={`/dna-lab?step=${step.id}`} className="block group">
                    <div
                      className={cn(
                        "relative rounded-2xl overflow-hidden",
                        "bg-[var(--bg-subtle)] border border-white/10",
                        "p-8 h-full min-h-[180px]",
                        "transition-all duration-300",
                        "hover:border-[var(--border-primary)]/50",
                        "hover:-translate-y-1"
                      )}
                    >
                      {/* Step number */}
                      <div className="absolute top-4 right-4 text-5xl font-black text-white/5">
                        {String(index + 1).padStart(2, "0")}
                      </div>

                      {/* Icon */}
                      <div
                        className={cn(
                          "w-12 h-12 rounded-xl flex items-center justify-center mb-5",
                          step.bgColor
                        )}
                      >
                        <Icon className={cn("w-6 h-6", step.color)} />
                      </div>

                      {/* Title */}
                      <h3 className="text-xl font-bold text-white mb-2">
                        {step.name}
                      </h3>

                      {/* Subtitle */}
                      <p className="text-sm text-gray-500 mb-6">
                        {step.subtitle}
                      </p>

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
    </AppShell>
  );
}

/**
 * Step View - 개별 스텝 패널
 */
function StepView({ stepId }: { stepId: string }) {
  const router = useRouter();
  const step = STEPS.find((s) => s.id === stepId);

  if (!step) {
    return (
      <AppShell showTopBar={false}>
        <div className="min-h-screen flex items-center justify-center bg-black text-white">
          알 수 없는 단계입니다
        </div>
      </AppShell>
    );
  }

  const Icon = step.icon;
  const currentIndex = STEPS.findIndex((s) => s.id === stepId);
  const nextStep = STEPS[currentIndex + 1];
  const prevStep = STEPS[currentIndex - 1];

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen bg-[var(--bg-base)]">
        {/* Simple Header */}
        <div className="border-b border-white/5 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push("/dna-lab")}
                className="p-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-400" />
              </button>
              <div className="flex items-center gap-3">
                <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", step.bgColor)}>
                  <Icon className={cn("w-5 h-5", step.color)} />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-white">{step.name}</h1>
                  <p className="text-xs text-gray-500">{step.subtitle}</p>
                </div>
              </div>
            </div>

            {/* Step navigation */}
            <div className="flex items-center gap-2">
              {STEPS.map((s, i) => (
                <button
                  key={s.id}
                  onClick={() => router.push(`/dna-lab?step=${s.id}`)}
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold transition-all",
                    s.id === stepId
                      ? "bg-[var(--bg-primary)] text-white"
                      : "bg-white/5 text-gray-500 hover:bg-white/10"
                  )}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Panel Content */}
        <div className="max-w-5xl mx-auto px-6 py-8">
          {stepId === "vpe" && <VPEPanel />}
          {stepId === "ad" && <AestheticDirectorPanel />}
          {stepId === "mirror" && <AbyssMirrorPanel />}
          {stepId === "qc" && <QualityDirectorPanel />}
        </div>

        {/* Bottom Navigation */}
        <div className="fixed bottom-0 left-0 right-0 border-t border-white/5 bg-black/80 backdrop-blur-sm">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            {prevStep ? (
              <button
                onClick={() => router.push(`/dna-lab?step=${prevStep.id}`)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/5 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                {prevStep.name}
              </button>
            ) : (
              <div />
            )}

            {nextStep ? (
              <button
                onClick={() => router.push(`/dna-lab?step=${nextStep.id}`)}
                className="flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium bg-[var(--bg-primary)] text-white hover:opacity-90 transition-all"
              >
                {nextStep.name}
                <ArrowUpRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => router.push("/dna-lab")}
                className="flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium bg-emerald-500 text-white hover:opacity-90 transition-all"
              >
                완료
                <CheckCircle className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
