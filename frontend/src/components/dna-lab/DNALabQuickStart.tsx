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
 * URL: /dna-lab?master=xxx&mode=quick
 */

import { useState } from "react";
import { Play } from "lucide-react";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";
import { cn } from "@/lib/utils";

interface DNALabQuickStartProps {
  masterKey: string;
  onStart: (options: { videoUrl?: string }) => void;
}

export function DNALabQuickStart({ masterKey, onStart }: DNALabQuickStartProps) {
  const [videoUrl, setVideoUrl] = useState("");
  const master = MASTER_AUTEURS.find((m) => m.key === masterKey);

  return (
    <div className="min-h-screen bg-stitch-dark flex flex-col">
      {/* Aurora Background - Neon Red */}
      <div className="aurora-neon fixed inset-0 pointer-events-none" />

      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4">
        {/* Master Profile Card with rotating border */}
        <MasterProfileCard master={master} />

        {/* Master Name & Title */}
        <h1 className="text-3xl font-bold text-white mt-6">
          {master?.name || masterKey}
        </h1>
        <p className="text-white/60 text-sm mt-2">
          {master?.nameEn || "마스터 스타일 분석"}
        </p>

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

        {/* Neon Red CTA */}
        <button
          className="btn-neon-red flex items-center gap-3 mt-6"
          onClick={() => onStart({ videoUrl: videoUrl || undefined })}
        >
          <Play className="w-5 h-5" />
          <span>통합분석 시작하기</span>
          <span className="bg-black/20 px-2 py-0.5 rounded text-sm">50 credits</span>
        </button>
      </main>

      {/* 3-Step Indicator */}
      <MinimalStepper currentStep={0} />
    </div>
  );
}

/**
 * Master Profile Card with V7 rotating gradient border
 */
function MasterProfileCard({
  master,
}: {
  master: (typeof MASTER_AUTEURS)[number] | undefined;
}) {
  return (
    <div className="relative">
      {/* Rotating gradient border */}
      <div className="absolute inset-0 -m-2 rounded-full border border-[var(--stitch-primary)]/20 animate-[spin_10s_linear_infinite]" />
      <div className="absolute inset-0 -m-4 rounded-full border border-dashed border-white/5 animate-[spin_20s_linear_infinite_reverse]" />

      {/* Avatar */}
      <div className="w-48 h-48 rounded-full p-[3px] bg-gradient-to-b from-[var(--stitch-primary)] via-purple-500 to-transparent">
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
    </div>
  );
}

/**
 * Minimal 3-Step Stepper
 */
function MinimalStepper({ currentStep }: { currentStep: number }) {
  const steps = ["영상분석", "창작DNA", "품질검증"];

  return (
    <div className="pb-8 flex justify-center gap-8">
      {steps.map((label, idx) => (
        <div key={label} className="flex items-center gap-2">
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
