"use client";

/**
 * DimensionHubClient - Interactive Client Component
 * =================================================
 *
 * Contains all interactive UI logic for the Dimension Hub:
 * - Stage filter toggle
 * - Chain context integration
 * - Animation effects
 *
 * Static data is imported from lib/dimension-data.ts
 */

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  CheckCircle,
  ChevronRight,
  Link2,
  Trash2,
} from "lucide-react";
import { AuroraBackground } from "@/components/AuroraBackground";
import { MiniAppSubmitModal } from "@/components/MiniAppSubmitModal";
import { useParallaxScroll } from "@/hooks/useLusionAnimations";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { getDimensionGradient, getDimensionGlow, getDimensionToken } from "@/lib/tokens";
import {
  type DimensionStage,
  type DimensionItemData,
  DIMENSION_ITEMS,
  DIMENSION_ICONS,
  WORKFLOW_STAGES,
  ROUTE_KEYS,
} from "@/lib/dimension-data";

// Stage color mappings for toggle buttons
const STAGE_COLORS: Record<string, { bg: string; text: string }> = {
  emerald: { bg: "bg-[var(--color-brand-secondary)]", text: "text-black" },
  violet: { bg: "bg-[var(--color-brand-primary)]", text: "text-white" },
  amber: { bg: "bg-[var(--color-brand-accent)]", text: "text-black" },
  cyan: { bg: "bg-[var(--info)]", text: "text-white" },
  fuchsia: { bg: "bg-[var(--color-brand-primary)]", text: "text-white" },
};

const SUCCESS_TONE = {
  bg: "bg-[var(--success)]/20",
  border: "border-[var(--success)]/30",
  text: "text-[var(--success)]",
};

function DimensionIcon({
  iconName,
  className,
}: {
  iconName: DimensionItemData["iconName"];
  className?: string;
}) {
  const Icon = DIMENSION_ICONS[iconName] ?? Link2;
  return <Icon className={className} aria-hidden="true" />;
}

export default function DimensionHubClient() {
  const { language } = useLanguage();
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [selectedStage, setSelectedStage] = useState<DimensionStage | null>(
    null
  );
  const [showChainPanel, setShowChainPanel] = useState(false);
  const chainCtx = useDimensionChainOptional();
  useParallaxScroll();

  const filteredItems = selectedStage
    ? DIMENSION_ITEMS.filter((d) => d.stage === selectedStage)
    : DIMENSION_ITEMS;

  const stageKeys = Object.keys(WORKFLOW_STAGES) as DimensionStage[];

  // Chain data summary
  const chainSummary = chainCtx?.getChainSummary() || [];
  const hasChainData = chainSummary.length > 0;

  // Check if a dimension has chain data
  const hasDimensionData = (href: string): boolean => {
    const routeKey = ROUTE_KEYS[href];
    return routeKey ? chainCtx?.hasChainData(routeKey) || false : false;
  };

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background (Fixed) */}
      <AuroraBackground />

      {/* Mini App Submit Modal */}
      <MiniAppSubmitModal
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
      />

      <div className="min-h-screen relative">
        {/* Minimalist Hero Section (Toggle Only) */}
        <section className="relative pt-32 pb-12 flex flex-col items-center justify-center overflow-hidden px-4">
          {/* 4-Stage Workflow Toggle */}
          <StageToggle
            stageKeys={stageKeys}
            selectedStage={selectedStage}
            onStageChange={setSelectedStage}
            language={language}
          />

          {/* Chain Status Bar */}
          <AnimatePresence>
            {hasChainData && (
              <ChainStatusBar
                chainSummary={chainSummary}
                showChainPanel={showChainPanel}
                onTogglePanel={() => setShowChainPanel(!showChainPanel)}
                onClearChain={() => chainCtx?.clearChain()}
                language={language}
              />
            )}
          </AnimatePresence>
        </section>

        {/* Content Section - Cards */}
        <section className="relative z-10 pb-40 px-4 sm:px-6">
          <div className="mx-auto max-w-7xl">
            <DimensionPortalGrid
              items={filteredItems}
              hasDimensionData={hasDimensionData}
              onOpenSubmitModal={() => setIsSubmitModalOpen(true)}
              language={language}
            />
          </div>
        </section>
      </div>
    </AppShell>
  );
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

interface StageToggleProps {
  stageKeys: DimensionStage[];
  selectedStage: DimensionStage | null;
  onStageChange: (stage: DimensionStage | null) => void;
  language: string;
}

function StageToggle({
  stageKeys,
  selectedStage,
  onStageChange,
  language,
}: StageToggleProps) {
  return (
    <div className="flex flex-wrap justify-center items-center gap-2 p-2 rounded-2xl backdrop-blur-sm bg-[var(--surface-1)]">
      <button
        onClick={() => onStageChange(null)}
        className={`px-5 py-2.5 rounded-xl text-xs font-bold tracking-widest uppercase transition-all duration-300 ${
          selectedStage === null
            ? "bg-[var(--fg-0)] text-[var(--bg-0)] shadow-lg scale-105"
            : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
        }`}
      >
        ALL
      </button>
      {stageKeys.map((stageKey) => {
        const stage = WORKFLOW_STAGES[stageKey];
        const isSelected = selectedStage === stageKey;
        const colors = STAGE_COLORS[stage.color] || STAGE_COLORS.emerald;

        return (
          <button
            key={stageKey}
            onClick={() => onStageChange(isSelected ? null : stageKey)}
            className={`px-4 py-2.5 rounded-xl text-xs font-bold tracking-wide transition-all duration-300 flex items-center gap-2 ${
              isSelected
                ? `${colors.bg} ${colors.text} shadow-lg scale-105`
                : "text-[var(--fg-muted)] hover:text-[var(--fg-0)] bg-[var(--surface-1)] hover:bg-[var(--surface-2)]"
            }`}
          >
            <span className="text-[10px] font-mono opacity-60">
              {stage.order}
            </span>
            <span>{language === "ko" ? stage.nameKo : stage.nameEn}</span>
          </button>
        );
      })}
    </div>
  );
}

interface ChainStatusBarProps {
  chainSummary: Array<{ key: string; name: string; summary?: string }>;
  showChainPanel: boolean;
  onTogglePanel: () => void;
  onClearChain: () => void;
  language: string;
}

function ChainStatusBar({
  chainSummary,
  showChainPanel,
  onTogglePanel,
  onClearChain,
  language,
}: ChainStatusBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="mt-4 w-full max-w-2xl"
    >
      <div className="relative p-3 rounded-xl backdrop-blur-md bg-gradient-to-r from-[var(--color-brand-secondary)]/10 via-[var(--color-brand-primary)]/10 to-[var(--color-brand-accent)]/10 border border-[var(--border-subtle)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link2 className="w-4 h-4 text-[var(--success)]" />
            <span className="text-sm font-medium text-[var(--fg-0)]">
              {language === "ko" ? "워크플로우 진행 중" : "Workflow in progress"}
            </span>
            <span className="text-xs text-[var(--fg-subtle)]">
              ({chainSummary.length}{" "}
              {language === "ko" ? "단계 완료" : "steps done"})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onTogglePanel}
              className="text-xs text-[var(--fg-muted)] hover:text-[var(--fg-0)] px-2 py-1 rounded-lg hover:bg-[var(--surface-2)] transition-colors"
            >
              {showChainPanel
                ? language === "ko"
                  ? "숨기기"
                  : "Hide"
                : language === "ko"
                  ? "상세보기"
                  : "Details"}
            </button>
            <button
              onClick={onClearChain}
              className="p-1 rounded-lg text-[var(--fg-subtle)] hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title={language === "ko" ? "초기화" : "Clear"}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Expanded Chain Details */}
        <AnimatePresence>
          {showChainPanel && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-3 mt-3 border-t border-[var(--border-subtle)] space-y-2">
                {chainSummary.map((item, idx) => (
                  <div key={item.key} className="flex items-center gap-2 text-sm">
                    <span className={`w-5 h-5 rounded-full ${SUCCESS_TONE.bg} ${SUCCESS_TONE.text} flex items-center justify-center text-xs font-bold`}>
                      {idx + 1}
                    </span>
                    <span className="text-[var(--fg-0)] font-medium">{item.name}</span>
                    {item.summary && (
                      <span className="text-[var(--fg-subtle)] text-xs truncate max-w-[var(--layout-max-width-xl)]">
                        - {item.summary}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

interface DimensionPortalGridProps {
  items: DimensionItemData[];
  hasDimensionData: (href: string) => boolean;
  onOpenSubmitModal: () => void;
  language: string;
}

function DimensionPortalGrid({
  items,
  hasDimensionData,
  onOpenSubmitModal,
  language,
}: DimensionPortalGridProps) {
  return (
    <div className="relative">
      {/* Background Atmosphere Spot */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[var(--layout-spotlight-size)] h-[var(--layout-spotlight-size)] bg-[var(--color-brand-primary)]/10 blur-[150px] rounded-full pointer-events-none z-0 mix-blend-screen" />

      <motion.div
        className={`grid gap-6 relative z-10 ${
          items.length === 1
            ? "grid-cols-1 max-w-2xl mx-auto"
            : "sm:grid-cols-2 lg:grid-cols-4"
        }`}
        layout
      >
        <AnimatePresence mode="popLayout">
          {items.map((dimension, idx) => (
            <DimensionCard
              key={dimension.href}
              dimension={dimension}
              index={idx}
              hasData={hasDimensionData(dimension.href)}
              language={language}
            />
          ))}
        </AnimatePresence>

        {/* Propose Button */}
        <ProposeButton onOpenSubmitModal={onOpenSubmitModal} language={language} />
      </motion.div>
    </div>
  );
}

interface DimensionCardProps {
  dimension: DimensionItemData;
  index: number;
  hasData: boolean;
  language: string;
}

function DimensionCard({
  dimension,
  index,
  hasData,
  language,
}: DimensionCardProps) {
  const stageInfo = WORKFLOW_STAGES[dimension.stage];
  const token = getDimensionToken(dimension.dimensionCode);
  const toneKey = token.tailwindKey;
  const textColor = `text-${toneKey}`;
  const borderColor = `border-${toneKey}`;
  const borderColorSoft = `border-${toneKey}/50`;
  const gradientStops = getDimensionGradient(dimension.dimensionCode).replace(
    "bg-gradient-to-r ",
    ""
  );
  const gradient = `bg-gradient-to-br ${gradientStops}`;
  const glowClass = getDimensionGlow(dimension.dimensionCode, "lg");

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="group relative"
    >
      <Link
        href={dimension.href}
        className="block relative overflow-hidden rounded-[2rem] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 backdrop-blur-2xl hover:bg-[var(--surface-2)] transition-all duration-700 hover:-translate-y-2 shadow-lg"
      >
        {/* NEW Badge */}
        {dimension.isNew && (
          <div className="absolute top-4 right-4 z-20 px-2 py-1 rounded-full bg-lime-500 text-black text-[10px] font-bold tracking-wider animate-pulse">
            NEW
          </div>
        )}

        {/* Chain Data Indicator */}
        {hasData && (
          <div className={`absolute top-4 left-4 z-20 flex items-center gap-1 px-2 py-1 rounded-full ${SUCCESS_TONE.bg} border ${SUCCESS_TONE.border}`}>
            <CheckCircle className={`w-3 h-3 ${SUCCESS_TONE.text}`} />
            <span className={`text-[10px] ${SUCCESS_TONE.text} font-medium`}>
              {language === "ko" ? "데이터" : "Data"}
            </span>
          </div>
        )}

        {/* Colored Border Reveal */}
        <div
          className={`absolute inset-0 rounded-[2rem] border-2 ${borderColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
        />

        {/* Gradient Background */}
        <div
          className={`absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-700 ${gradient}`}
        />

        {/* Portal Ring Effect */}
        <div
          className={`absolute -right-20 -top-20 h-64 w-64 rounded-full border-[1px] ${borderColorSoft} ${glowClass} blur-[60px] opacity-20 group-hover:opacity-40 transition-opacity duration-700`}
        />

        <div className="relative flex items-start justify-between h-full flex-col gap-4 min-h-[var(--layout-min-height-md)]">
          <div className="w-full flex items-start justify-between z-10">
            <div className="flex flex-col gap-1">
              {/* Stage Label */}
              <span
                className={`text-[10px] font-mono tracking-wider ${textColor} opacity-60`}
              >
                {stageInfo.order}.{dimension.stageOrder}
              </span>
              <h2 className="text-lg font-bold text-[var(--fg-0)] group-hover:text-[var(--color-brand-primary)] transition-colors duration-500">
                {language === "ko" ? dimension.titleKo : dimension.titleEn}
              </h2>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--surface-2)] border border-[var(--border-subtle)] backdrop-blur-md transition-all duration-500 group-hover:scale-110 group-hover:bg-[var(--surface-1)]">
              <DimensionIcon
                iconName={dimension.iconName}
                className={`h-4 w-4 ${textColor}`}
              />
            </div>
          </div>

          <div className="space-y-6 z-10 mt-auto">
            <div className="space-y-2">
              <p className="text-sm text-[var(--fg-muted)] leading-relaxed line-clamp-2">
                {language === "ko" ? dimension.descKo : dimension.descEn}
              </p>
            </div>
            {/* Arrow Action */}
            <div className="flex justify-end mt-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-full border border-[var(--border-subtle)] bg-[var(--surface-2)] backdrop-blur-sm text-[var(--fg-muted)] group-hover:text-[var(--fg-0)] group-hover:bg-[var(--surface-1)] transition-all duration-300 group-hover:scale-110">
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

interface ProposeButtonProps {
  onOpenSubmitModal: () => void;
  language: string;
}

function ProposeButton({ onOpenSubmitModal, language }: ProposeButtonProps) {
  return (
    <button
      onClick={onOpenSubmitModal}
      className="group relative overflow-hidden rounded-[2rem] border border-dashed border-[var(--border-subtle)] bg-transparent p-6 hover:bg-[var(--surface-1)] hover:border-[var(--border-strong)] transition-all duration-500 flex flex-col items-center justify-center gap-4 min-h-[var(--layout-min-height-md)]"
    >
      <div className="relative">
        <div className="absolute inset-0 bg-[var(--color-brand-accent)]/20 blur-[30px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-[var(--surface-1)] border border-[var(--border-subtle)] transition-all duration-500 group-hover:scale-110">
          <Plus className="h-6 w-6 text-[var(--fg-muted)] group-hover:text-[var(--fg-0)] transition-colors duration-300" />
        </div>
      </div>

      <div className="text-center space-y-2">
        <span className="text-xs font-bold tracking-[0.2em] text-[var(--fg-muted)] uppercase group-hover:text-[var(--color-brand-accent)] transition-colors">
          ∞D INFINITE
        </span>
        <p className="text-sm text-[var(--fg-subtle)] group-hover:text-[var(--fg-muted)] transition-colors max-w-[var(--layout-max-width-xl)]">
          {language === "ko" ? "새로운 차원을 제안하세요" : "Propose a new dimension"}
        </p>
      </div>
    </button>
  );
}
