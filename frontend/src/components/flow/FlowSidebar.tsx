"use client";

/**
 * FlowSidebar - 2026 Spatial UI Workflow Sidebar
 *
 * Modern sidebar with glassmorphism, motion UI, and spatial depth.
 * Displays workflow phases, navigation, and status indicators.
 *
 * Features:
 * - Collapsible with smooth animations
 * - Phase navigation with visual status indicators
 * - Workflow progress visualization
 * - Standalone tools section
 * - 2026 design tokens integration
 */

import { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Search,
  Layers,
  Wand2,
  LayoutGrid,
  Image as ImageIcon,
  Video,
  CheckCircle,
  Palette,
  Music,
  Moon,
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  RotateCcw,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { STANDALONE_TOOLS } from "@/lib/dimension-data";
import type { WorkflowPhase, ChainDataEntry } from "@/machines/workflowMachine";

// =============================================================================
// TYPES
// =============================================================================

interface FlowSidebarProps {
  /** Current active workflow phase */
  activePhase: WorkflowPhase | null;
  /** Chain data for each phase */
  chainData: Record<WorkflowPhase, ChainDataEntry | null>;
  /** Workflow state (idle, running, completed, error) */
  workflowState: "idle" | "running" | "completed" | "error";
  /** Callback when a start option is selected */
  onStartSelect: (phase: WorkflowPhase) => void;
  /** Callback when a phase node is clicked */
  onPhaseClick: (phase: WorkflowPhase) => void;
  /** Callback for workflow control actions */
  onWorkflowControl?: (action: "play" | "pause" | "reset") => void;
  /** Language setting */
  language?: "ko" | "en";
  /** Whether sidebar is collapsed */
  collapsed?: boolean;
  /** Callback when collapse state changes */
  onCollapsedChange?: (collapsed: boolean) => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const PHASE_CONFIG: Record<WorkflowPhase, {
  icon: LucideIcon;
  color: string;
  label: { ko: string; en: string };
  description: { ko: string; en: string };
}> = {
  "4D": {
    icon: Search,
    color: "emerald",
    label: { ko: "레퍼런스 해석기", en: "Reference Decoder" },
    description: { ko: "거장의 작품 분석", en: "Master's work analysis" },
  },
  Story: {
    icon: Layers,
    color: "fuchsia",
    label: { ko: "시나리오 생성기", en: "Story Architect" },
    description: { ko: "스토리 구조 설계", en: "Story structure design" },
  },
  AD: {
    icon: Palette,
    color: "rose",
    label: { ko: "미학 디렉터", en: "Aesthetic Director" },
    description: { ko: "비주얼 스타일 가이드", en: "Visual style guide" },
  },
  "1D": {
    icon: Wand2,
    color: "violet",
    label: { ko: "프롬프트 연금술", en: "Prompt Alchemy" },
    description: { ko: "프롬프트 최적화", en: "Prompt optimization" },
  },
  "2D": {
    icon: LayoutGrid,
    color: "cyan",
    label: { ko: "스토리보드 스케치", en: "Storyboard Sketch" },
    description: { ko: "씬 시각화", en: "Scene visualization" },
  },
  Sound: {
    icon: Music,
    color: "cyan",
    label: { ko: "사운드 크래프터", en: "Sound Crafter" },
    description: { ko: "음악 & 사운드", en: "Music & sound design" },
  },
  "3D": {
    icon: ImageIcon,
    color: "emerald",
    label: { ko: "비주얼 리얼라이저", en: "Visual Realizer" },
    description: { ko: "이미지 생성", en: "Image generation" },
  },
  VEO: {
    icon: Video,
    color: "sky",
    label: { ko: "비디오 메이커", en: "Video Maker" },
    description: { ko: "영상 생성", en: "Video generation" },
  },
  QC: {
    icon: CheckCircle,
    color: "emerald",
    label: { ko: "퀄리티 디렉터", en: "Quality Director" },
    description: { ko: "품질 검증", en: "Quality verification" },
  },
};

const WORKFLOW_PHASES: WorkflowPhase[] = [
  "4D", "Story", "AD", "1D", "2D", "Sound", "3D", "VEO", "QC"
];

// =============================================================================
// COMPONENTS
// =============================================================================

function PhaseNode({
  phase,
  isActive,
  isCompleted,
  onClick,
  language = "ko",
  collapsed = false,
}: {
  phase: WorkflowPhase;
  isActive: boolean;
  isCompleted: boolean;
  onClick: () => void;
  language?: "ko" | "en";
  collapsed?: boolean;
}) {
  const config = PHASE_CONFIG[phase];
  const Icon = config.icon;

  const getStatusClasses = () => {
    if (isActive) {
      return `border-${config.color}-500 bg-${config.color}-500/20 ring-2 ring-${config.color}-500/30 ring-offset-2 ring-offset-[var(--surface-0)]`;
    }
    if (isCompleted) {
      return `border-${config.color}-500/50 bg-${config.color}-500/10`;
    }
    return "border-[var(--border-subtle)] bg-[var(--surface-1)] opacity-60";
  };

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        w-full flex items-center gap-3 p-3 rounded-xl border-2
        transition-all duration-200 text-left
        ${getStatusClasses()}
        hover:bg-[var(--surface-2)] hover:border-[var(--border-muted)]
      `}
    >
      {/* Icon */}
      <div className={`
        w-10 h-10 rounded-lg flex-shrink-0
        flex items-center justify-center
        ${isActive || isCompleted
          ? `bg-${config.color}-500/20`
          : "bg-[var(--surface-2)]"
        }
      `}>
        <Icon className={`
          w-5 h-5
          ${isActive || isCompleted
            ? `text-${config.color}-400`
            : "text-[var(--fg-muted)]"
          }
        `} />
      </div>

      {/* Labels - hidden when collapsed */}
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            className="flex-1 min-w-0 overflow-hidden"
          >
            <div className="flex items-center gap-2">
              <span className={`
                text-xs font-bold
                ${isActive || isCompleted
                  ? `text-${config.color}-400`
                  : "text-[var(--fg-muted)]"
                }
              `}>
                {phase}
              </span>
              {isCompleted && (
                <CheckCircle className="w-3 h-3 text-emerald-400" />
              )}
              {isActive && (
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              )}
            </div>
            <div className={`
              text-sm font-medium truncate
              ${isActive || isCompleted
                ? "text-[var(--fg-0)]"
                : "text-[var(--fg-muted)]"
              }
            `}>
              {config.label[language]}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}

function WorkflowProgress({
  chainData,
  collapsed,
}: {
  chainData: Record<WorkflowPhase, ChainDataEntry | null>;
  collapsed: boolean;
}) {
  const completedCount = WORKFLOW_PHASES.filter(p => chainData[p] !== null).length;
  const progress = (completedCount / WORKFLOW_PHASES.length) * 100;

  if (collapsed) {
    return (
      <div className="px-2 py-3">
        <div className="h-24 w-1.5 mx-auto bg-[var(--surface-2)] rounded-full overflow-hidden">
          <motion.div
            className="w-full bg-gradient-to-b from-violet-500 to-emerald-500 rounded-full"
            initial={{ height: 0 }}
            animate={{ height: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
        <div className="text-center mt-2 text-xs font-bold text-[var(--fg-muted)]">
          {completedCount}/{WORKFLOW_PHASES.length}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-3">
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="text-[var(--fg-muted)]">진행률</span>
        <span className="font-bold text-[var(--fg-0)]">{completedCount}/{WORKFLOW_PHASES.length}</span>
      </div>
      <div className="h-2 bg-[var(--surface-2)] rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-violet-500 via-cyan-500 to-emerald-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function FlowSidebar({
  activePhase,
  chainData,
  workflowState,
  onStartSelect: _onStartSelect,
  onPhaseClick,
  onWorkflowControl,
  language = "ko",
  collapsed = false,
  onCollapsedChange,
}: FlowSidebarProps) {
  const handleToggleCollapse = useCallback(() => {
    onCollapsedChange?.(!collapsed);
  }, [collapsed, onCollapsedChange]);

  const labels = {
    title: language === "ko" ? "워크플로우" : "Workflow",
    phases: language === "ko" ? "단계" : "Phases",
    startPoints: language === "ko" ? "시작점" : "Start Points",
    standaloneTools: language === "ko" ? "독립 도구" : "Standalone Tools",
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 320 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={`
        flex-shrink-0 h-full
        bg-[var(--surface-0)]/80 backdrop-blur-xl
        border-r border-[var(--border-subtle)]
        flex flex-col overflow-hidden
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border-subtle)]">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="flex items-center gap-2"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
                <Workflow className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-[var(--fg-0)]">{labels.title}</span>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          onClick={handleToggleCollapse}
          className={`
            p-2 rounded-lg
            bg-[var(--surface-1)] hover:bg-[var(--surface-2)]
            border border-[var(--border-subtle)]
            transition-colors
            ${collapsed ? "mx-auto" : ""}
          `}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4 text-[var(--fg-muted)]" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-[var(--fg-muted)]" />
          )}
        </button>
      </div>

      {/* Progress Indicator */}
      <WorkflowProgress chainData={chainData} collapsed={collapsed} />

      {/* Workflow Controls */}
      {workflowState !== "idle" && onWorkflowControl && (
        <div className={`
          flex items-center gap-2 px-4 py-2 border-b border-[var(--border-subtle)]
          ${collapsed ? "justify-center" : "justify-start"}
        `}>
          {workflowState === "running" ? (
            <button
              onClick={() => onWorkflowControl("pause")}
              className="p-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 transition-colors"
            >
              <Pause className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => onWorkflowControl("play")}
              className="p-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 transition-colors"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => onWorkflowControl("reset")}
            className="p-2 rounded-lg bg-[var(--surface-2)] hover:bg-[var(--surface-1)] text-[var(--fg-muted)] transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Phase List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {/* Section Title */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="px-1 py-2"
            >
              <span className="text-xs font-semibold text-[var(--fg-muted)] uppercase tracking-wider">
                {labels.phases}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Phase Nodes */}
        {WORKFLOW_PHASES.map((phase) => (
          <PhaseNode
            key={phase}
            phase={phase}
            isActive={activePhase === phase}
            isCompleted={chainData[phase] !== null}
            onClick={() => onPhaseClick(phase)}
            language={language}
            collapsed={collapsed}
          />
        ))}
      </div>

      {/* Standalone Tools Section */}
      <div className="p-3 border-t border-[var(--border-subtle)]">
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="px-1 py-2"
            >
              <span className="text-xs font-semibold text-[var(--fg-muted)] uppercase tracking-wider">
                {labels.standaloneTools}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {STANDALONE_TOOLS.map((tool) => (
          <Link
            key={tool.key}
            href="/dimension/abyss"
            className={`
              flex items-center gap-3 p-3 rounded-xl
              bg-[var(--surface-1)] hover:bg-[var(--surface-2)]
              border border-[var(--border-subtle)] hover:border-violet-500/30
              transition-all
              ${collapsed ? "justify-center" : ""}
            `}
          >
            <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center flex-shrink-0">
              <Moon className="w-4 h-4 text-violet-400" />
            </div>
            <AnimatePresence>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 min-w-0"
                >
                  <div className="text-sm font-medium text-[var(--fg-0)] truncate">
                    {language === "ko" ? tool.name : tool.nameEn}
                  </div>
                  <div className="text-xs text-[var(--fg-muted)]">{tool.dimension}</div>
                </motion.div>
              )}
            </AnimatePresence>
          </Link>
        ))}
      </div>
    </motion.aside>
  );
}

export default FlowSidebar;
