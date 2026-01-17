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
import {
  Brain,
  Search,
  Layers,
  Music,
  LayoutGrid,
  Wand2,
  Image as ImageIcon,
  Video,
  CheckCircle,
  Palette,
  FlaskConical,
} from "lucide-react";

// =============================================================================
// TYPES
// =============================================================================

export interface DimensionItemData {
  id: string;
  href: string;
  iconName: DimensionIconName;
  stage: DimensionStage;
  stageOrder: number;
  titleKo: string;
  titleEn: string;
  descKo: string;
  descEn: string;
  portalColor: string;
  borderColor: string;
  glowClass: string;
  activeBg: string;
  activeText: string;
  textColor: string;
  gradient?: string;
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
  | "layout-grid"
  | "wand"
  | "image"
  | "video"
  | "check"
  | "palette"
  | "flask";

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
  "layout-grid": LayoutGrid,
  wand: Wand2,
  image: ImageIcon,
  video: Video,
  check: CheckCircle,
  palette: Palette,
  flask: FlaskConical,
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
    stage: "planning",
    stageOrder: 1,
    titleKo: "심연의 거울",
    titleEn: "Abyss Mirror",
    descKo: "나만의 취향과 창작 DNA 분석",
    descEn: "Analyze your creative DNA",
    portalColor: "border-indigo-500/50",
    borderColor: "border-indigo-500",
    glowClass: "glow-breathe glow-breathe-indigo",
    activeBg: "bg-indigo-500",
    activeText: "text-indigo-100",
    textColor: "text-indigo-400",
    gradient: "from-indigo-500 via-violet-500 to-blue-500",
  },
  {
    id: "reference-decoder",
    href: "/dimension/reference-decoder",
    iconName: "search",
    stage: "planning",
    stageOrder: 2,
    titleKo: "레퍼런스 해석기",
    titleEn: "Reference Decoder",
    descKo: "조명, 색감, 연출의 전문가적 분석",
    descEn: "Expert analysis of lighting, color, direction",
    portalColor: "border-amber-500/50",
    borderColor: "border-amber-500",
    glowClass: "glow-breathe glow-breathe-amber",
    activeBg: "bg-amber-500",
    activeText: "text-amber-950",
    textColor: "text-amber-400",
    gradient: "from-amber-500 via-orange-500 to-red-500",
  },
  {
    id: "story-architect",
    href: "/dimension/story-architect",
    iconName: "layers",
    stage: "planning",
    stageOrder: 3,
    titleKo: "시나리오 생성기",
    titleEn: "Story Architect",
    descKo: "DNA와 스타일을 결합한 시나리오 작성",
    descEn: "Write scenarios combining DNA and style",
    portalColor: "border-emerald-500/50",
    borderColor: "border-emerald-500",
    glowClass: "glow-breathe glow-breathe-emerald",
    activeBg: "bg-emerald-500",
    activeText: "text-emerald-950",
    textColor: "text-emerald-400",
    gradient: "from-emerald-500 via-green-500 to-lime-500",
    isNew: true,
  },

  // ========== Stage 2: 사전 제작 (Pre-production) ==========
  {
    id: "sound-crafter",
    href: "/dimension/sound-crafter",
    iconName: "music",
    stage: "pre_production",
    stageOrder: 1,
    titleKo: "사운드 크래프터",
    titleEn: "Sound Crafter",
    descKo: "BGM 및 성우 내레이션 생성 (Suno, Udio)",
    descEn: "Generate BGM and narration (Suno, Udio)",
    portalColor: "border-pink-500/50",
    borderColor: "border-pink-500",
    glowClass: "glow-breathe glow-breathe-pink",
    activeBg: "bg-pink-500",
    activeText: "text-pink-100",
    textColor: "text-pink-400",
    gradient: "from-pink-500 via-rose-500 to-red-500",
    isNew: true,
  },
  {
    id: "storyboard-sketch",
    href: "/dimension/storyboard",
    iconName: "layout-grid",
    stage: "pre_production",
    stageOrder: 2,
    titleKo: "스토리보드 스케치",
    titleEn: "Storyboard Sketch",
    descKo: "글을 시각적 컷으로 스케치",
    descEn: "Sketch text into visual cuts",
    portalColor: "border-cyan-500/50",
    borderColor: "border-cyan-500",
    glowClass: "glow-breathe glow-breathe-cyan",
    activeBg: "bg-cyan-500",
    activeText: "text-cyan-950",
    textColor: "text-cyan-400",
    gradient: "from-cyan-500 via-teal-500 to-emerald-500",
  },
  {
    id: "prompt-alchemy",
    href: "/dimension/prompt",
    iconName: "wand",
    stage: "pre_production",
    stageOrder: 3,
    titleKo: "프롬프트 연금술",
    titleEn: "Prompt Alchemy",
    descKo: "AI가 이해하는 전문 언어로 번역",
    descEn: "Translate to AI-native language",
    portalColor: "border-violet-500/50",
    borderColor: "border-violet-500",
    glowClass: "glow-breathe glow-breathe-violet",
    activeBg: "bg-violet-500",
    activeText: "text-violet-100",
    textColor: "text-violet-400",
    gradient: "from-violet-500 via-purple-500 to-indigo-500",
  },
  {
    id: "platform-translator",
    href: "/dimension/prompt-alchemy",
    iconName: "flask",
    stage: "pre_production",
    stageOrder: 4,
    titleKo: "플랫폼 번역기",
    titleEn: "Platform Translator",
    descKo: "Veo, Kling, Sora 최적화 프롬프트",
    descEn: "Optimized prompts for Veo, Kling, Sora",
    portalColor: "border-purple-500/50",
    borderColor: "border-purple-500",
    glowClass: "glow-breathe glow-breathe-purple",
    activeBg: "bg-purple-500",
    activeText: "text-purple-100",
    textColor: "text-purple-400",
    gradient: "from-purple-500 via-violet-500 to-fuchsia-500",
    isNew: true,
  },

  // ========== Stage 3: 제작 (Production) ==========
  {
    id: "visual-realizer",
    href: "/dimension/visual-realizer",
    iconName: "image",
    stage: "production",
    stageOrder: 1,
    titleKo: "비주얼 리얼라이저",
    titleEn: "Visual Realizer",
    descKo: "Key Frame 고품질 생성 (Midjourney)",
    descEn: "Generate high-quality keyframes",
    portalColor: "border-orange-500/50",
    borderColor: "border-orange-500",
    glowClass: "glow-breathe glow-breathe-orange",
    activeBg: "bg-orange-500",
    activeText: "text-orange-950",
    textColor: "text-orange-400",
    gradient: "from-orange-500 via-amber-500 to-yellow-500",
  },
  {
    id: "video-maker",
    href: "/dimension/video-maker",
    iconName: "video",
    stage: "production",
    stageOrder: 2,
    titleKo: "비디오 메이커",
    titleEn: "Video Maker",
    descKo: "영상 변환 및 모션 제어 (Veo 3.1, Kling)",
    descEn: "Video conversion & motion control",
    portalColor: "border-sky-500/50",
    borderColor: "border-sky-500",
    glowClass: "glow-breathe glow-breathe-sky",
    activeBg: "bg-sky-500",
    activeText: "text-sky-100",
    textColor: "text-sky-400",
    gradient: "from-sky-500 via-blue-500 to-indigo-500",
  },

  // ========== Stage 4: 완성 (Finishing) ==========
  {
    id: "quality-director",
    href: "/dimension/quality-check",
    iconName: "check",
    stage: "finishing",
    stageOrder: 1,
    titleKo: "퀄리티 디렉터",
    titleEn: "Quality Director",
    descKo: "시각적 일관성 및 동작 자연스러움 검수",
    descEn: "Check visual consistency & motion smoothness",
    portalColor: "border-rose-500/50",
    borderColor: "border-rose-500",
    glowClass: "glow-breathe glow-breathe-rose",
    activeBg: "bg-rose-500",
    activeText: "text-rose-100",
    textColor: "text-rose-400",
    gradient: "from-rose-500 via-pink-500 to-red-500",
  },

  // ========== Extended Tools ==========
  {
    id: "aesthetic-director",
    href: "/dimension/aesthetic",
    iconName: "palette",
    stage: "extended",
    stageOrder: 1,
    titleKo: "미학디렉터",
    titleEn: "Aesthetic Director",
    descKo: "거장들의 미학을 적용합니다",
    descEn: "Apply masters' aesthetics",
    portalColor: "border-fuchsia-500/50",
    borderColor: "border-fuchsia-500",
    glowClass: "glow-breathe glow-breathe-fuchsia",
    activeBg: "bg-fuchsia-500",
    activeText: "text-fuchsia-100",
    textColor: "text-fuchsia-400",
    gradient: "from-fuchsia-500 via-purple-500 to-pink-500",
  },
];

// =============================================================================
// ROUTE KEY MAPPING
// =============================================================================

export const ROUTE_KEYS: Record<string, string> = {
  "/dimension/abyss": "abyss-mirror",
  "/dimension/reference-decoder": "reference-decoder",
  "/dimension/story-architect": "story-architect",
  "/dimension/sound-crafter": "sound-crafter",
  "/dimension/storyboard": "storyboard-sketch",
  "/dimension/prompt": "prompt-alchemy",
  "/dimension/prompt-alchemy": "platform-translator",
  "/dimension/visual-realizer": "visual-realizer",
  "/dimension/video-maker": "video-maker",
  "/dimension/quality-check": "quality-director",
  "/dimension/aesthetic": "aesthetic-director",
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
