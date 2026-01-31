"use client";

/**
 * DNALabQuickStart - V7 Cinematic Quick Start Entry Point
 *
 * Stitch AI V7 디자인 적용:
 * - Aurora Neon Red 배경
 * - Rotating gradient border 마스터 프로필 카드
 * - Neon Red CTA 버튼
 * - 3-Step 인디케이터
 *
 * UX 하드닝 적용:
 * - H1: Loading State 스켈레톤
 * - H2: 마이크로 인터랙션 (motion)
 * - H3: Error State 디자인
 * - H4: 키보드 접근성 (Enter)
 * - H5: 반응형 개선
 *
 * URL: /dna-lab?master=xxx&mode=quick
 */

import { useState, useEffect } from "react";
import { Play } from "lucide-react";
import { motion } from "framer-motion";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";
import { cn } from "@/lib/utils";

interface DNALabQuickStartProps {
  masterKey: string;
  onStart: (options: { videoUrl?: string }) => void;
  isLoading?: boolean;
  error?: string | null;
}

/**
 * H1: Loading State 스켈레톤
 */
function QuickStartSkeleton() {
  return (
    <div className="animate-pulse flex flex-col items-center">
      <div className="w-32 h-32 sm:w-48 sm:h-48 rounded-full bg-white/10" />
      <div className="h-8 w-48 bg-white/10 rounded-lg mt-6" />
      <div className="h-4 w-32 bg-white/10 rounded mt-2" />
      <div className="h-12 w-full max-w-md bg-white/5 rounded-xl mt-8" />
      <div className="h-14 w-64 bg-[var(--stitch-primary)]/20 rounded-xl mt-6" />
    </div>
  );
}

export function DNALabQuickStart({
  masterKey,
  onStart,
  isLoading = false,
  error = null,
}: DNALabQuickStartProps) {
  const [videoUrl, setVideoUrl] = useState("");
  const master = MASTER_AUTEURS.find((m) => m.key === masterKey);

  // H4: 키보드 접근성 - Enter 키 지원
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey && !isLoading) {
        onStart({ videoUrl: videoUrl || undefined });
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [videoUrl, onStart, isLoading]);

  return (
    <div className="min-h-screen bg-stitch-dark flex flex-col">
      {/* Aurora Background - Neon Red */}
      <div className="aurora-neon fixed inset-0 pointer-events-none" />

      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4">
        {isLoading ? (
          <QuickStartSkeleton />
        ) : (
          <>
            {/* Master Profile Card with rotating border + H2 hover effect */}
            <MasterProfileCard master={master} />

            {/* Master Name & Title */}
            <h1 className="text-2xl sm:text-3xl font-bold text-white mt-6 text-center">
              {master?.name || masterKey}
            </h1>
            <p className="text-white/60 text-sm mt-2 text-center">
              {master?.nameEn || "마스터 스타일 분석"}
            </p>

            {/* H3: Error State */}
            {error && (
              <div className="error-neon rounded-xl px-4 py-3 mt-4 text-sm text-white/80 max-w-md text-center">
                <span className="text-[var(--stitch-primary)] font-medium">
                  오류:{" "}
                </span>
                {error}
              </div>
            )}

            {/* Optional Video URL Input */}
            <div className="mt-8 w-full max-w-md">
              <input
                type="url"
                placeholder="YouTube/Vimeo URL (선택)"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10
                           text-white placeholder:text-white/40 focus:outline-none
                           focus:border-[var(--stitch-primary)]/50"
              />
            </div>

            {/* Neon Red CTA + H2 motion + H5 반응형 */}
            <motion.button
              whileTap={{ scale: 0.98 }}
              className="btn-neon-red flex items-center gap-3 mt-6 w-full sm:w-auto justify-center"
              onClick={() => onStart({ videoUrl: videoUrl || undefined })}
              disabled={isLoading}
            >
              <Play className="w-5 h-5" />
              <span>통합분석 시작하기</span>
              <span className="bg-black/20 px-2 py-0.5 rounded text-sm">
                50 credits
              </span>
            </motion.button>
          </>
        )}
      </main>

      {/* 3-Step Indicator */}
      <MinimalStepper currentStep={0} />
    </div>
  );
}

/**
 * Master Profile Card with V7 rotating gradient border
 * H2: motion whileHover 적용
 * H5: 반응형 크기 (w-32 sm:w-48)
 */
function MasterProfileCard({
  master,
}: {
  master: (typeof MASTER_AUTEURS)[number] | undefined;
}) {
  return (
    <motion.div
      className="relative"
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      {/* Rotating gradient border */}
      <div className="absolute inset-0 -m-2 rounded-full border border-[var(--stitch-primary)]/20 animate-[spin_10s_linear_infinite]" />
      <div className="absolute inset-0 -m-4 rounded-full border border-dashed border-white/5 animate-[spin_20s_linear_infinite_reverse]" />

      {/* Avatar - H5 반응형 */}
      <div className="w-32 h-32 sm:w-48 sm:h-48 rounded-full p-[3px] bg-gradient-to-b from-[var(--stitch-primary)] via-purple-500 to-transparent">
        <div className="w-full h-full rounded-full overflow-hidden border-4 border-[var(--stitch-card-dark)]">
          {master?.thumbnail ? (
            <img
              src={master.thumbnail}
              alt={master.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-white/10 flex items-center justify-center text-4xl">
              🎬
            </div>
          )}
        </div>
      </div>

      {/* Ready badge */}
      <div className="absolute bottom-2 right-2 bg-[var(--stitch-card-dark)] text-[var(--stitch-primary)] text-xs px-3 py-1 rounded-full border border-white/10">
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse inline-block mr-1" />
        READY
      </div>
    </motion.div>
  );
}

/**
 * Minimal 3-Step Stepper
 * H5: 반응형 - 모바일에서 세로 배치
 */
function MinimalStepper({ currentStep }: { currentStep: number }) {
  const steps = ["영상분석", "창작DNA", "품질검증"];

  return (
    <div className="pb-8 flex flex-col sm:flex-row justify-center gap-4 sm:gap-8">
      {steps.map((label, idx) => (
        <div key={label} className="flex items-center gap-2 justify-center">
          <div
            className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
              idx === currentStep
                ? "bg-[var(--stitch-primary)] text-white shadow-neon"
                : "bg-white/10 text-white/40"
            )}
          >
            {idx + 1}
          </div>
          <span
            className={cn(
              "text-sm",
              idx === currentStep ? "text-white" : "text-white/40"
            )}
          >
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}
