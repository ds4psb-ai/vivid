/**
 * Dimension Static Data - Server Component Compatible
 * ===================================================
 *
 * Static dimension data that can be imported from both
 * Server and Client Components. No React hooks or browser APIs.
 *
 * 2026 Best Practice: Keep static data serializable for RSC.
 */

import type { LucideIcon } from "lucide-react";
import type { DimensionCode } from "@/lib/tokens";
import {
  Brain,
  Search,
  Layers,
  Music,
  Music2,
  LayoutGrid,
  Wand2,
  Image as ImageIcon,
  Video,
  Film,
  CheckCircle,
  Palette,
  FlaskConical,
  Users,
} from "lucide-react";

// =============================================================================
// TYPES
// =============================================================================

export interface DimensionItemData {
  id: string;
  href: string;
  iconName: DimensionIconName;
  dimensionCode: DimensionCode;
  stage: DimensionStage;
  stageOrder: number;
  titleKo: string;
  titleEn: string;
  descKo: string;
  descEn: string;
  isNew?: boolean;
}

export type DimensionStage =
  | "planning"
  | "pre_production"
  | "production"
  | "finishing"
  | "extended";

export interface WorkflowStageInfo {
  order: number;
  nameKo: string;
  nameEn: string;
  color: string;
}

export type DimensionIconName =
  | "brain"
  | "search"
  | "layers"
  | "music"
  | "music2"
  | "layout-grid"
  | "wand"
  | "image"
  | "video"
  | "film"
  | "check"
  | "palette"
  | "flask"
  | "users";

// =============================================================================
// WORKFLOW STAGES
// =============================================================================

export const WORKFLOW_STAGES: Record<DimensionStage, WorkflowStageInfo> = {
  planning: { order: 1, nameKo: "기획", nameEn: "Planning", color: "emerald" },
  pre_production: {
    order: 2,
    nameKo: "사전 제작",
    nameEn: "Pre-production",
    color: "violet",
  },
  production: { order: 3, nameKo: "제작", nameEn: "Production", color: "amber" },
  finishing: { order: 4, nameKo: "완성", nameEn: "Finishing", color: "cyan" },
  extended: { order: 5, nameKo: "확장", nameEn: "Extended", color: "fuchsia" },
};

// =============================================================================
// ICON MAPPING (for serialization)
// =============================================================================

export const DIMENSION_ICONS: Record<DimensionIconName, LucideIcon> = {
  brain: Brain,
  search: Search,
  layers: Layers,
  music: Music,
  music2: Music2,
  "layout-grid": LayoutGrid,
  wand: Wand2,
  image: ImageIcon,
  video: Video,
  film: Film,
  check: CheckCircle,
  palette: Palette,
  flask: FlaskConical,
  users: Users,
};

// =============================================================================
// DIMENSION ITEMS (Static, Serializable)
// =============================================================================

export const DIMENSION_ITEMS: DimensionItemData[] = [
  // ========== Stage 1: 기획 (Planning) ==========
  {
    id: "abyss-mirror",
    href: "/dimension/abyss",
    iconName: "brain",
    dimensionCode: "mirror",
    stage: "planning",
    stageOrder: 1,
    titleKo: "심연의 거울",
    titleEn: "Abyss Mirror",
    descKo: "나만의 취향과 창작 DNA 분석",
    descEn: "Analyze your creative DNA",
  },
  {
    id: "reference-decoder",
    href: "/dimension/reference-decoder",
    iconName: "search",
    dimensionCode: "4d",
    stage: "planning",
    stageOrder: 2,
    titleKo: "레퍼런스 해석기",
    titleEn: "Reference Decoder",
    descKo: "조명, 색감, 연출의 전문가적 분석",
    descEn: "Expert analysis of lighting, color, direction",
  },
  {
    id: "story-architect",
    href: "/dimension/story-architect",
    iconName: "layers",
    dimensionCode: "story",
    stage: "planning",
    stageOrder: 3,
    titleKo: "시나리오 생성기",
    titleEn: "Story Architect",
    descKo: "DNA와 스타일을 결합한 시나리오 작성",
    descEn: "Write scenarios combining DNA and style",
    isNew: true,
  },

  // ========== Stage 2: 사전 제작 (Pre-production) ==========
  {
    id: "sound-crafter",
    href: "/dimension/sound-crafter",
    iconName: "music",
    dimensionCode: "sound",
    stage: "pre_production",
    stageOrder: 1,
    titleKo: "사운드 크래프터",
    titleEn: "Sound Crafter",
    descKo: "BGM 및 성우 내레이션 생성 (Suno, Udio)",
    descEn: "Generate BGM and narration (Suno, Udio)",
    isNew: true,
  },
  {
    id: "storyboard-sketch",
    href: "/dimension/storyboard",
    iconName: "layout-grid",
    dimensionCode: "storyboard",
    stage: "pre_production",
    stageOrder: 2,
    titleKo: "스토리보드 스케치",
    titleEn: "Storyboard Sketch",
    descKo: "글을 시각적 컷으로 스케치",
    descEn: "Sketch text into visual cuts",
  },
  {
    id: "prompt-generator",
    href: "/dimension/prompt",
    iconName: "wand",
    dimensionCode: "prompt",
    stage: "pre_production",
    stageOrder: 3,
    titleKo: "프롬프트 생성기",
    titleEn: "Prompt Generator",
    descKo: "AI 비디오 프롬프트 생성",
    descEn: "Generate AI video prompts",
  },
  {
    id: "platform-translator",
    href: "/dimension/prompt-translator",
    iconName: "flask",
    dimensionCode: "prompt",
    stage: "pre_production",
    stageOrder: 4,
    titleKo: "플랫폼 번역기",
    titleEn: "Platform Translator",
    descKo: "Veo, Kling, Sora 플랫폼별 최적화",
    descEn: "Optimized prompts for Veo, Kling, Sora",
    isNew: true,
  },

  // ========== Stage 3: 제작 (Production) ==========
  {
    id: "visual-realizer",
    href: "/dimension/visual-realizer",
    iconName: "image",
    dimensionCode: "3d",
    stage: "production",
    stageOrder: 1,
    titleKo: "비주얼 리얼라이저",
    titleEn: "Visual Realizer",
    descKo: "Key Frame 고품질 생성 (Midjourney)",
    descEn: "Generate high-quality keyframes",
  },
  {
    id: "video-maker",
    href: "/dimension/video-maker",
    iconName: "video",
    dimensionCode: "veo",
    stage: "production",
    stageOrder: 2,
    titleKo: "비디오 메이커",
    titleEn: "Video Maker",
    descKo: "영상 변환 및 모션 제어 (Veo 3.1, Kling)",
    descEn: "Video conversion & motion control",
  },

  // ========== Stage 4: 완성 (Finishing) ==========
  {
    id: "quality-director",
    href: "/dimension/quality-check",
    iconName: "check",
    dimensionCode: "qc",
    stage: "finishing",
    stageOrder: 1,
    titleKo: "퀄리티 디렉터",
    titleEn: "Quality Director",
    descKo: "시각적 일관성 및 동작 자연스러움 검수",
    descEn: "Check visual consistency & motion smoothness",
  },
  {
    id: "creative-editor",
    href: "/dimension/creative-editor",
    iconName: "wand",
    dimensionCode: "qc",
    stage: "finishing",
    stageOrder: 2,
    titleKo: "크리에이티브 에디터",
    titleEn: "Creative Editor",
    descKo: "완성본 품질 검수 및 편집",
    descEn: "Final quality check and editing",
  },

  // ========== Extended Tools ==========
  {
    id: "aesthetic-director",
    href: "/dimension/aesthetic",
    iconName: "palette",
    dimensionCode: "ad",
    stage: "extended",
    stageOrder: 1,
    titleKo: "미학디렉터",
    titleEn: "Aesthetic Director",
    descKo: "거장들의 미학을 적용합니다",
    descEn: "Apply masters' aesthetics",
  },
  {
    id: "character-consistency",
    href: "/dimension/character-consistency",
    iconName: "users",
    dimensionCode: "character",
    stage: "extended",
    stageOrder: 2,
    titleKo: "캐릭터 일관성",
    titleEn: "Character Consistency",
    descKo: "StoryMem 캐릭터 라이브러리 관리",
    descEn: "StoryMem character library management",
    isNew: true,
  },
  {
    id: "suno-music",
    href: "/dimension/suno",
    iconName: "music2",
    dimensionCode: "suno",
    stage: "extended",
    stageOrder: 3,
    titleKo: "Suno 음악",
    titleEn: "Suno Music",
    descKo: "AI 음악 생성 (작사/작곡)",
    descEn: "AI music generation (lyrics/composition)",
    isNew: true,
  },
  {
    id: "kling-video",
    href: "/dimension/kling",
    iconName: "film",
    dimensionCode: "kling",
    stage: "extended",
    stageOrder: 4,
    titleKo: "Kling 2.6",
    titleEn: "Kling Video",
    descKo: "고품질 시네마틱 비디오 생성",
    descEn: "High-quality cinematic video generation",
    isNew: true,
  },
];

// =============================================================================
// WORKFLOW START OPTIONS - 거장 미학 입력 시작점 (3옵션)
// =============================================================================

/**
 * 워크플로우 시작 옵션
 *
 * 거장 RAG 기반 세계관 컨텐츠 생성의 3가지 진입점:
 * 1. 레퍼런스 해석기 (4D): 거장의 레퍼런스 분석부터 시작
 * 2. 시나리오 생성기 (Story): 스토리 구성부터 시작
 * 3. 프롬프트 연금술 (1D): 프롬프트 작성부터 시작
 */
export interface FlowStartOption {
  key: string;
  dimension: string;
  phase: "4D" | "Story" | "1D"; // WorkflowPhase 시작점
  name: string;
  nameEn: string;
  description: string;
  descriptionEn: string;
  iconName: DimensionIconName;
}

export const FLOW_START_OPTIONS: readonly FlowStartOption[] = [
  {
    key: "reference-decoder",
    dimension: "4D",
    phase: "4D",
    name: "레퍼런스 해석기",
    nameEn: "Reference Decoder",
    description: "거장의 레퍼런스 분석부터 시작",
    descriptionEn: "Start from master's reference analysis",
    iconName: "search",
  },
  {
    key: "story-architect",
    dimension: "STORY",
    phase: "Story",
    name: "시나리오 생성기",
    nameEn: "Story Architect",
    description: "스토리 구성부터 시작",
    descriptionEn: "Start from story composition",
    iconName: "layers",
  },
  {
    key: "prompt-generator",
    dimension: "1D",
    phase: "1D",
    name: "프롬프트 생성기",
    nameEn: "Prompt Generator",
    description: "프롬프트 작성부터 시작",
    descriptionEn: "Start from prompt writing",
    iconName: "wand",
  },
] as const;

// =============================================================================
// STANDALONE TOOLS - AI(Abyss Mirror)는 별도 섹션
// =============================================================================

/**
 * 독립 도구 목록
 *
 * 워크플로우 DAG에 포함되지 않고 별도로 사용:
 * - 심연의 거울 (AI): 페르소나 분석 후 다른 앱에 컨텍스트로 주입
 */
export interface StandaloneTool {
  key: string;
  dimension: string;
  name: string;
  nameEn: string;
  description: string;
  descriptionEn: string;
  iconName: DimensionIconName;
}

export const STANDALONE_TOOLS: readonly StandaloneTool[] = [
  {
    key: "abyss-mirror",
    dimension: "AI",
    name: "심연의 거울",
    nameEn: "Abyss Mirror",
    description: "나의 창작 DNA 분석 후 다른 앱에 적용",
    descriptionEn: "Analyze creative DNA and apply to other apps",
    iconName: "brain",
  },
] as const;

// =============================================================================
// ROUTE KEY MAPPING
// =============================================================================

export const ROUTE_KEYS: Record<string, string> = {
  "/dimension/abyss": "abyss-mirror",
  "/dimension/reference-decoder": "reference-decoder",
  "/dimension/story-architect": "story-architect",
  "/dimension/sound-crafter": "sound-crafter",
  "/dimension/storyboard": "storyboard-sketch",
  "/dimension/prompt": "prompt-generator",
  "/dimension/prompt-translator": "platform-translator",
  "/dimension/visual-realizer": "visual-realizer",
  "/dimension/video-maker": "video-maker",
  "/dimension/quality-check": "quality-director",
  "/dimension/creative-editor": "creative-editor",
  "/dimension/aesthetic": "aesthetic-director",
  "/dimension/character-consistency": "character-consistency",
  "/dimension/suno": "suno-music",
  "/dimension/kling": "kling-video",
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get dimension item by ID
 */
export function getDimensionById(id: string): DimensionItemData | undefined {
  return DIMENSION_ITEMS.find((d) => d.id === id);
}

/**
 * Get dimension items by stage
 */
export function getDimensionsByStage(
  stage: DimensionStage
): DimensionItemData[] {
  return DIMENSION_ITEMS.filter((d) => d.stage === stage);
}

/**
 * Get route key from href
 */
export function getRouteKey(href: string): string | undefined {
  return ROUTE_KEYS[href];
}

/**
 * Get icon component by name
 */
export function getDimensionIcon(iconName: DimensionIconName): LucideIcon {
  return DIMENSION_ICONS[iconName];
}

/**
 * Get stage info
 */
export function getStageInfo(stage: DimensionStage): WorkflowStageInfo {
  return WORKFLOW_STAGES[stage];
}

/**
 * Get all stage keys in order
 */
export function getOrderedStageKeys(): DimensionStage[] {
  return Object.entries(WORKFLOW_STAGES)
    .sort(([, a], [, b]) => a.order - b.order)
    .map(([key]) => key as DimensionStage);
}
