"use client";

/**
 * WorkflowCanvas - React Flow 기반 시각적 DAG 빌더
 *
 * 거장 RAG + 페르소나 → 차원 조합 → 세계관 컨텐츠 생성을 시각화
 *
 * Features:
 * - 노드: 각 Dimension 앱 (4D, Story, 1D, 2D, 3D, VEO, QC, AD, Sound)
 * - 엣지: 데이터 흐름 (chainData)
 * - 자동 레이아웃: dagre 알고리즘
 * - 실시간 상태: XState 연동
 */

import { useCallback, useMemo, useEffect } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  Handle,
  Position,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion } from "framer-motion";
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
  type LucideIcon,
} from "lucide-react";
import { getLayoutedElements } from "@/lib/layout";
import { DIMENSION_CONNECTIONS } from "@/lib/dimension-theme";
import { FLOW_START_OPTIONS } from "@/lib/dimension-data";
import type { WorkflowPhase, ChainDataEntry } from "@/machines/workflowMachine";

// =============================================================================
// TYPES
// =============================================================================

export interface WorkflowNodeData extends Record<string, unknown> {
  label: string;
  labelEn: string;
  phase: WorkflowPhase;
  status: "pending" | "active" | "completed" | "error";
  icon: LucideIcon;
  color: string;
  chainData?: ChainDataEntry | null;
}

export type WorkflowNode = Node<WorkflowNodeData>;

interface WorkflowCanvasProps {
  /** 현재 활성화된 단계 */
  activePhase?: WorkflowPhase | null;
  /** 각 단계의 체인 데이터 */
  chainData?: Record<WorkflowPhase, ChainDataEntry | null>;
  /** 노드 클릭 핸들러 */
  onNodeClick?: (phase: WorkflowPhase) => void;
  /** 시작점 선택 핸들러 */
  onStartSelect?: (phase: WorkflowPhase) => void;
  /** 읽기 전용 모드 */
  readOnly?: boolean;
  /** 최소화 모드 */
  compact?: boolean;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const PHASE_TO_KEY: Record<WorkflowPhase, string> = {
  "4D": "reference-decoder",
  Story: "story-architect",
  AD: "aesthetic-director",
  "1D": "prompt-alchemy",
  "2D": "storyboard-sketch",
  Sound: "sound-crafter",
  "3D": "visual-realizer",
  VEO: "video-maker",
  QC: "quality-director",
};

const PHASE_ICONS: Record<WorkflowPhase, LucideIcon> = {
  "4D": Search,
  Story: Layers,
  AD: Palette,
  "1D": Wand2,
  "2D": LayoutGrid,
  Sound: Music,
  "3D": ImageIcon,
  VEO: Video,
  QC: CheckCircle,
};

const PHASE_COLORS: Record<WorkflowPhase, string> = {
  "4D": "emerald",
  Story: "violet",
  AD: "rose",
  "1D": "amber",
  "2D": "cyan",
  Sound: "fuchsia",
  "3D": "sky",
  VEO: "indigo",
  QC: "emerald",
};

const PHASE_LABELS: Record<WorkflowPhase, { ko: string; en: string }> = {
  "4D": { ko: "레퍼런스 해석기", en: "Reference Decoder" },
  Story: { ko: "시나리오 생성기", en: "Story Architect" },
  AD: { ko: "미학디렉터", en: "Aesthetic Director" },
  "1D": { ko: "프롬프트 연금술", en: "Prompt Alchemy" },
  "2D": { ko: "스토리보드 스케치", en: "Storyboard Sketch" },
  Sound: { ko: "사운드 크래프터", en: "Sound Crafter" },
  "3D": { ko: "비주얼 리얼라이저", en: "Visual Realizer" },
  VEO: { ko: "비디오 메이커", en: "Video Maker" },
  QC: { ko: "퀄리티 디렉터", en: "Quality Director" },
};

// =============================================================================
// CUSTOM NODE COMPONENT
// =============================================================================

function WorkflowNodeComponent({ data, selected }: NodeProps<WorkflowNode>) {
  const Icon = data.icon;
  const colorClass = `bg-${data.color}-500`;
  const borderColorClass = `border-${data.color}-500`;

  const statusClasses = {
    pending: "opacity-50",
    active: "ring-2 ring-offset-2 ring-offset-[var(--surface-0)]",
    completed: "",
    error: "ring-2 ring-red-500",
  };

  const statusBadge = {
    pending: null,
    active: (
      <span className="absolute -top-1 -right-1 w-3 h-3 bg-amber-500 rounded-full animate-pulse" />
    ),
    completed: (
      <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center">
        <CheckCircle className="w-3 h-3 text-white" />
      </span>
    ),
    error: (
      <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
    ),
  };

  return (
    <>
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className={`w-3 h-3 ${colorClass} border-2 border-[var(--surface-0)]`}
      />

      {/* Node Content */}
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`
          relative px-4 py-3 rounded-xl border-2 ${borderColorClass}/30
          bg-[var(--surface-1)] backdrop-blur-sm
          shadow-lg cursor-pointer transition-all
          ${statusClasses[data.status]}
          ${selected ? `ring-2 ring-${data.color}-400` : ""}
        `}
      >
        {statusBadge[data.status]}

        <div className="flex items-center gap-3">
          <div
            className={`
            w-10 h-10 rounded-lg ${colorClass}/20
            flex items-center justify-center
          `}
          >
            <Icon className={`w-5 h-5 text-${data.color}-400`} />
          </div>

          <div>
            <div className={`text-xs font-bold text-${data.color}-400`}>
              {data.phase}
            </div>
            <div className="text-sm font-medium text-[var(--fg-0)]">
              {data.label}
            </div>
          </div>
        </div>

        {/* Chain data preview */}
        {data.chainData && (
          <div className="mt-2 pt-2 border-t border-[var(--border-subtle)]">
            <div className="text-[10px] text-[var(--fg-muted)] truncate">
              {Object.keys(data.chainData.output).length}개 필드 생성됨
            </div>
          </div>
        )}
      </motion.div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className={`w-3 h-3 ${colorClass} border-2 border-[var(--surface-0)]`}
      />
    </>
  );
}

const nodeTypes = {
  workflowNode: WorkflowNodeComponent,
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function WorkflowCanvas({
  activePhase,
  chainData,
  onNodeClick,
  onStartSelect,
  readOnly = false,
  compact = false,
}: WorkflowCanvasProps) {
  // Generate initial nodes and edges from DIMENSION_CONNECTIONS
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const phases: WorkflowPhase[] = [
      "4D",
      "Story",
      "AD",
      "1D",
      "2D",
      "Sound",
      "3D",
      "VEO",
      "QC",
    ];

    const nodes: WorkflowNode[] = phases.map((phase) => {
      const isActive = activePhase === phase;
      const hasData = chainData?.[phase] !== null && chainData?.[phase] !== undefined;

      return {
        id: phase,
        type: "workflowNode",
        position: { x: 0, y: 0 }, // Will be calculated by dagre
        data: {
          label: PHASE_LABELS[phase].ko,
          labelEn: PHASE_LABELS[phase].en,
          phase,
          status: isActive ? "active" : hasData ? "completed" : "pending",
          icon: PHASE_ICONS[phase],
          color: PHASE_COLORS[phase],
          chainData: chainData?.[phase],
        },
      };
    });

    // Generate edges from DIMENSION_CONNECTIONS
    const edges: Edge[] = [];
    Object.entries(DIMENSION_CONNECTIONS).forEach(([sourceKey, targets]) => {
      // Map dimension key to phase
      const sourcePhase = Object.entries(PHASE_TO_KEY).find(
        ([, key]) => key === sourceKey
      )?.[0] as WorkflowPhase | undefined;

      if (!sourcePhase) return;

      targets.forEach((targetKey) => {
        const targetPhase = Object.entries(PHASE_TO_KEY).find(
          ([, key]) => key === targetKey
        )?.[0] as WorkflowPhase | undefined;

        if (!targetPhase) return;

        const sourceColor = PHASE_COLORS[sourcePhase];

        edges.push({
          id: `${sourcePhase}-${targetPhase}`,
          source: sourcePhase,
          target: targetPhase,
          type: "smoothstep",
          animated: activePhase === sourcePhase,
          style: {
            stroke: `var(--${sourceColor}-400, #8b8b8b)`,
            strokeWidth: 2,
          },
        });
      });
    });

    // Apply dagre layout
    return getLayoutedElements(nodes, edges, { direction: "LR" });
  }, [activePhase, chainData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when chainData or activePhase changes
  useEffect(() => {
    const { nodes: layoutedNodes } = getLayoutedElements(
      initialNodes as Node[],
      initialEdges,
      { direction: "LR" }
    );
    setNodes(layoutedNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (readOnly) return;
      const phase = node.id as WorkflowPhase;
      onNodeClick?.(phase);
    },
    [readOnly, onNodeClick]
  );

  return (
    <div
      className={`w-full ${compact ? "h-64" : "h-[500px]"} rounded-xl overflow-hidden border border-[var(--border-subtle)] bg-[var(--surface-0)]`}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={!readOnly}
        nodesConnectable={false}
        elementsSelectable={!readOnly}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={16}
          size={1}
          color="var(--border-subtle)"
        />
        {!compact && <Controls className="bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-lg" />}
        {!compact && (
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as WorkflowNodeData;
              return `var(--${data.color}-500)`;
            }}
            maskColor="rgba(0, 0, 0, 0.5)"
            className="bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-lg"
          />
        )}
      </ReactFlow>

      {/* Start Options Overlay (when no active phase) */}
      {!activePhase && !readOnly && (
        <div className="absolute inset-0 flex items-center justify-center bg-[var(--surface-0)]/80 backdrop-blur-sm">
          <div className="text-center">
            <h3 className="text-lg font-bold text-[var(--fg-0)] mb-4">
              워크플로우 시작점 선택
            </h3>
            <div className="flex gap-4">
              {FLOW_START_OPTIONS.map((option) => {
                const phase = Object.entries(PHASE_TO_KEY).find(
                  ([, key]) => key === option.key
                )?.[0] as WorkflowPhase | undefined;

                if (!phase) return null;

                const Icon = PHASE_ICONS[phase];
                const color = PHASE_COLORS[phase];

                return (
                  <button
                    key={option.key}
                    onClick={() => onStartSelect?.(phase)}
                    className={`
                      px-6 py-4 rounded-xl border-2 border-${color}-500/30
                      bg-${color}-500/10 hover:bg-${color}-500/20
                      transition-all hover:scale-105
                    `}
                  >
                    <Icon className={`w-8 h-8 mx-auto mb-2 text-${color}-400`} />
                    <div className={`text-sm font-bold text-${color}-400`}>
                      {option.dimension}
                    </div>
                    <div className="text-sm text-[var(--fg-0)]">
                      {option.name}
                    </div>
                    <div className="text-xs text-[var(--fg-muted)] mt-1">
                      {option.description}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowCanvas;
