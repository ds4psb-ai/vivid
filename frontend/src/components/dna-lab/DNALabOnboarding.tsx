"use client";

/**
 * DNALabOnboarding - Smart Entry Point for DNA Lab
 *
 * 2026 UX Enhancement:
 * - 3 entry options instead of direct VPE start
 * - "Value Before Step" pattern
 * - Intent-driven workflow selection
 *
 * Options:
 * 1. Select existing IP (메인페이지 IP 선택)
 * 2. Enter video URL (YouTube 직접 분석)
 * 3. Quick start with master style (거장 스타일 자동 선택)
 * 4. Manual start (수동 VPE 시작)
 */

import { useState } from "react";
import { Film, Link2, Sparkles, ChevronRight, Dna, Search, X } from "lucide-react";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";
import { cn } from "@/lib/utils";

interface DNALabOnboardingProps {
  /** Called when user selects an existing IP */
  onSelectIP: (ipSlug: string) => void;
  /** Called when user enters a video URL */
  onEnterURL: (url: string) => void;
  /** Called when user picks quick start with a master style */
  onQuickStart: (master: string) => void;
  /** Called when user wants to start manually */
  onManualStart: () => void;
}

type OnboardingMode = "main" | "url-input" | "master-select";

export function DNALabOnboarding({
  onSelectIP,
  onEnterURL,
  onQuickStart,
  onManualStart,
}: DNALabOnboardingProps) {
  const [mode, setMode] = useState<OnboardingMode>("main");
  const [urlInput, setUrlInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  // Filter masters by search query
  const filteredMasters = MASTER_AUTEURS.filter(
    (m) =>
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.nameEn.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.key.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleURLSubmit = () => {
    if (urlInput.trim()) {
      onEnterURL(urlInput.trim());
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Aurora Background - Neon Red + Violet 점진적 전환 */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-[var(--stitch-primary)]/20 rounded-full blur-[128px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-600/15 rounded-full blur-[100px] animate-pulse delay-1000" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-white/10 mb-6">
            <Dna className="w-8 h-8 text-white/80" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
            DNA Lab
          </h1>
          <p className="text-white/60 text-lg max-w-md mx-auto">
            무엇을 분석할까요?
          </p>
        </div>

        {/* Main Options */}
        {mode === "main" && (
          <div className="w-full max-w-3xl">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              {/* Option 1: Existing IP */}
              <OnboardingCard
                icon={Film}
                title="기존 IP"
                description="메인페이지에서 IP 선택"
                hue={148}
                onClick={() => onSelectIP("")}
              />

              {/* Option 2: Video URL */}
              <OnboardingCard
                icon={Link2}
                title="영상 URL"
                description="YouTube 직접 분석"
                hue={220}
                onClick={() => setMode("url-input")}
              />

              {/* Option 3: Quick Start */}
              <OnboardingCard
                icon={Sparkles}
                title="빠른 시작"
                description="거장 스타일 자동 선택"
                hue={45}
                onClick={() => setMode("master-select")}
              />
            </div>

            {/* Manual Start Link */}
            <div className="text-center">
              <button
                onClick={onManualStart}
                className="inline-flex items-center gap-2 text-white/40 hover:text-white/60 transition-colors text-sm"
              >
                <span>수동으로 분석하기</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* URL Input Mode */}
        {mode === "url-input" && (
          <div className="w-full max-w-lg">
            <button
              onClick={() => setMode("main")}
              className="mb-6 flex items-center gap-2 text-white/40 hover:text-white/60 transition-colors text-sm"
            >
              <ChevronRight className="w-4 h-4 rotate-180" />
              <span>뒤로</span>
            </button>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <h2 className="text-xl font-semibold text-white mb-2">
                영상 URL 입력
              </h2>
              <p className="text-white/50 text-sm mb-6">
                YouTube, Vimeo 등 영상 URL을 입력하면 AI가 분석합니다
              </p>

              <div className="flex gap-3">
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..."
                  className="flex-1 px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 transition-colors"
                  onKeyDown={(e) => e.key === "Enter" && handleURLSubmit()}
                  autoFocus
                />
                <button
                  onClick={handleURLSubmit}
                  disabled={!urlInput.trim()}
                  className={cn(
                    "px-6 py-3 rounded-xl font-medium transition-all",
                    urlInput.trim()
                      ? "bg-cyan-500 text-white hover:bg-cyan-400"
                      : "bg-white/10 text-white/30 cursor-not-allowed"
                  )}
                >
                  분석
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Master Select Mode */}
        {mode === "master-select" && (
          <div className="w-full max-w-2xl">
            <button
              onClick={() => setMode("main")}
              className="mb-6 flex items-center gap-2 text-white/40 hover:text-white/60 transition-colors text-sm"
            >
              <ChevronRight className="w-4 h-4 rotate-180" />
              <span>뒤로</span>
            </button>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <h2 className="text-xl font-semibold text-white mb-2">
                거장 스타일 선택
              </h2>
              <p className="text-white/50 text-sm mb-6">
                AI 거장의 스타일로 빠르게 시작하세요
              </p>

              {/* Search */}
              <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="거장 검색..."
                  className="w-full pl-10 pr-10 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-amber-500/50 transition-colors text-sm"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Masters Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-80 overflow-y-auto pr-1">
                {filteredMasters.map((master) => (
                  <button
                    key={master.key}
                    onClick={() => onQuickStart(master.key)}
                    className="flex items-center gap-3 p-3 bg-black/30 hover:bg-white/10 border border-white/10 hover:border-amber-500/30 rounded-xl transition-all group text-left"
                  >
                    {/* Thumbnail */}
                    <div className="w-10 h-10 rounded-lg bg-white/5 overflow-hidden flex-shrink-0">
                      {master.thumbnail ? (
                        <img
                          src={master.thumbnail}
                          alt={master.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-white/20 text-xs">
                          {master.name.charAt(0)}
                        </div>
                      )}
                    </div>
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate group-hover:text-amber-400 transition-colors">
                        {master.name}
                      </div>
                      <div className="text-xs text-white/40 truncate">
                        {master.nameEn}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {filteredMasters.length === 0 && (
                <div className="py-8 text-center text-white/40 text-sm">
                  검색 결과가 없습니다
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Onboarding Card Component
 */
interface OnboardingCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  hue: number;
  onClick: () => void;
}

function OnboardingCard({
  icon: Icon,
  title,
  description,
  hue,
  onClick,
}: OnboardingCardProps) {
  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col items-center p-6 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-2xl transition-all duration-300 text-center overflow-hidden hover:shadow-[0_0_30px_rgba(255,0,60,0.15)]"
      style={{
        ["--card-hue" as string]: hue,
      }}
    >
      {/* Hover Glow */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 50% 100%, hsl(${hue}, 70%, 50%, 0.15), transparent 70%)`,
        }}
      />

      {/* Icon */}
      <div
        className="w-14 h-14 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110 duration-300"
        style={{
          background: `linear-gradient(135deg, hsl(${hue}, 70%, 50%, 0.2), hsl(${hue}, 70%, 50%, 0.1))`,
          borderColor: `hsl(${hue}, 70%, 50%, 0.3)`,
          borderWidth: 1,
        }}
      >
        <span style={{ color: `hsl(${hue}, 70%, 60%)` }}>
          <Icon className="w-6 h-6 transition-colors" />
        </span>
      </div>

      {/* Text */}
      <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-white/90">
        {title}
      </h3>
      <p className="text-sm text-white/50 group-hover:text-white/60 transition-colors">
        {description}
      </p>

      {/* Arrow indicator */}
      <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/0 group-hover:text-white/40 transition-all duration-300 translate-x-2 group-hover:translate-x-0" />
    </button>
  );
}
