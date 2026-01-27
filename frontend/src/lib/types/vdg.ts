// frontend/src/lib/types/vdg.ts
/**
 * VDG (Video Data Graph) Type Definitions - Single Source of Truth
 *
 * This file is the SSoT for all VDG-related TypeScript types.
 * Other files should import from here instead of defining their own types.
 *
 * @see backend/app/schemas/vdg_base.py (Python SSoT)
 * @see docs/contracts/vdg_time_format.md (Time Format Contract)
 */

// ─────────────────────────────────────────────────────────────
// Time Window Types
// ─────────────────────────────────────────────────────────────

/**
 * Time window in milliseconds (matches backend TimeWindowMs)
 */
export interface TimeWindowMs {
  start_ms: number;
  end_ms: number;
}

// ─────────────────────────────────────────────────────────────
// Microbeat Types
// ─────────────────────────────────────────────────────────────

export type MicrobeatRole =
  | "start"
  | "setup"
  | "build"
  | "hook"
  | "punch"
  | "reveal"
  | "demo"
  | "payoff"
  | "cta"
  | "loop"
  | "end";

export type MicrobeatCue = "visual" | "audio" | "text" | "action";

/**
 * Microbeat - Hook 내 세부 비트
 *
 * Time Format:
 * - t: 초 단위 (frontend display format)
 * - t_ms: 밀리초 단위 (API 응답 호환)
 * - t_start_ms, t_end_ms: 밀리초 범위 (backend format)
 */
export interface Microbeat {
  /** Time in seconds (frontend format, optional for API compat) */
  t?: number;
  /** Time in milliseconds (API response format) */
  t_ms?: number;
  /** Time range start in milliseconds (backend format) */
  t_start_ms?: number;
  /** Time range end in milliseconds (backend format) */
  t_end_ms?: number;
  /** Microbeat role */
  role: string;
  /** Cue type */
  cue?: string;
  /** Description/note */
  note?: string;
  /** Alternative description field */
  description?: string;
  /** Camera shot type */
  shot_type?: string;
}

/**
 * MicrobeatsLegacy - v3 레거시 포맷 (간단한 텍스트 기반)
 */
export interface MicrobeatsLegacy {
  start?: string;
  build?: string;
  punch?: string;
}

// ─────────────────────────────────────────────────────────────
// Hook Genome Types
// ─────────────────────────────────────────────────────────────

/**
 * HookGenome - 바이럴 DNA 핵심
 */
export interface HookGenome {
  pattern?: string;
  delivery?: string;
  strength?: number;
  hook_summary?: string;
  /** Legacy: seconds */
  start_sec?: number;
  /** Legacy: seconds */
  end_sec?: number;
  /** Milliseconds (preferred) */
  hook_start_ms?: number;
  /** Milliseconds (preferred) */
  hook_end_ms?: number;
  /** Microbeats (v4 array or v3 legacy object) */
  microbeats?: Microbeat[] | MicrobeatsLegacy;
  /** Virality analysis metadata */
  virality_analysis?: Record<string, string>;
}

// ─────────────────────────────────────────────────────────────
// Intent Layer Types
// ─────────────────────────────────────────────────────────────

/**
 * DopamineRadar - 바이럴 자극 레이더 (0-10)
 */
export interface DopamineRadar {
  visual_spectacle?: number;
  audio_stimulation?: number;
  narrative_intrigue?: number;
  emotional_resonance?: number;
  comedy_shock?: number;
}

/**
 * IronyAnalysis - 반전 분석 (기대 vs 현실)
 */
export interface IronyAnalysis {
  setup?: string;
  twist?: string;
  gap_type?: string;
}

/**
 * IntentLayer - 심리적 의도 분석
 */
export interface IntentLayer {
  dopamine_radar?: DopamineRadar;
  irony_analysis?: IronyAnalysis;
  intent_summary?: string;
  target_emotion?: string;
  call_to_action?: string;
  hook_trigger?: string;
  hook_trigger_reason?: string;
  retention_strategy?: string;
  creator_intent?: string;
  audience_trigger?: string[];
  novelty?: string;
  clarity?: string;
}

// ─────────────────────────────────────────────────────────────
// Scene Types
// ─────────────────────────────────────────────────────────────

/**
 * Scene - 씬 정보
 */
export interface Scene {
  scene_id?: string;
  label?: string;
  /** Milliseconds (preferred) */
  t_start_ms?: number;
  /** Milliseconds (preferred) */
  t_end_ms?: number;
  /** Legacy: seconds */
  time_start?: number;
  /** Legacy: seconds */
  time_end?: number;
  description?: string;
  summary?: string;
  narrative_role?: string;
  visual_detail?: SceneVisualDetail;
}

/**
 * SceneVisualDetail - Veo/Sora 프롬프트용 시각 정보
 */
export interface SceneVisualDetail {
  background?: string;
  foreground_props?: string[];
  text_overlays?: string[];
  subject_description?: string;
  subject_action?: string;
}

// ─────────────────────────────────────────────────────────────
// Mise-en-Scene Types
// ─────────────────────────────────────────────────────────────

export type MiseEnSceneElement =
  | "outfit_color"
  | "background"
  | "lighting"
  | "props"
  | "makeup"
  | "setting";

export type MiseEnSceneSentiment = "positive" | "negative" | "neutral";

/**
 * MiseEnSceneSignal - v4 format (comment-based visual signals)
 */
export interface MiseEnSceneSignal {
  element: string;
  value: string;
  sentiment?: MiseEnSceneSentiment;
  source_comment?: string;
  likes?: number;
  evidence_refs?: string[];
  /** Confidence score for the signal (0-1) */
  confidence?: number;
}

/**
 * MiseEnSceneSignalLLM - v3/LLM format (different structure)
 */
export interface MiseEnSceneSignalLLM {
  type?: string;
  description?: string;
  why_it_matters?: string;
  anchor_ms?: number;
}

// ─────────────────────────────────────────────────────────────
// Viral Kick Types
// ─────────────────────────────────────────────────────────────

export type KeyframeRole = "start" | "peak" | "end";

/**
 * ViralKickKeyframe - 키프레임 증거
 */
export interface ViralKickKeyframe {
  t_ms: number;
  role: KeyframeRole;
  what_to_see?: string;
}

/**
 * ViralKick - 바이럴 킥 구간
 */
export interface ViralKick {
  kick_index: number;
  kick_id?: string;
  start_ms: number;
  end_ms: number;
  peak_ms?: number;
  title?: string;
  mechanism?: string;
  keyframes: ViralKickKeyframe[];
  confidence?: number;
  creator_instruction?: string;
  /** Comment ranks referenced as evidence */
  evidence_comment_ranks?: number[];
  proof_ready?: boolean;
  status?: string;
}

// ─────────────────────────────────────────────────────────────
// Capsule Brief Types
// ─────────────────────────────────────────────────────────────

/**
 * ProductionConstraints - 촬영 제약 조건
 */
export interface ProductionConstraints {
  min_actors?: number;
  locations?: string[];
  props?: string[];
  difficulty?: string;
  primary_challenge?: string;
}

/**
 * ShotlistItem - 샷 리스트 항목
 */
export interface ShotlistItem {
  seq?: number;
  duration?: number;
  action?: string;
  shot?: string;
}

/**
 * CapsuleBrief - 크리에이터 실행 가이드
 */
export interface CapsuleBrief {
  hook_script?: string;
  shotlist?: ShotlistItem[];
  constraints?: ProductionConstraints;
  do_not?: string[];
}

// ─────────────────────────────────────────────────────────────
// Causal Reasoning Types
// ─────────────────────────────────────────────────────────────

/**
 * CausalReasoning - 인과 추론 (왜 바이럴인가)
 */
export interface CausalReasoning {
  why_viral?: string;
  why_viral_one_liner?: string;
  causal_chain?: string[];
  /** Can be array (v4) or string (legacy v3) */
  replication_recipe?: string[] | string;
  risks_or_unknowns?: string[];
}

// ─────────────────────────────────────────────────────────────
// Normalized VDG (Output of normalizeVDG)
// ─────────────────────────────────────────────────────────────

/**
 * NormalizedVDG - normalizeVDG() 함수의 출력 타입
 *
 * 모든 VDG 버전(v3, v4)을 일관된 구조로 정규화한 결과
 */
export interface NormalizedVDG {
  hook_genome: HookGenome;
  intent_layer: IntentLayer;
  scenes: Scene[];
  mise_en_scene_signals: MiseEnSceneSignal[];
  capsule_brief?: CapsuleBrief;
  provenance?: Record<string, unknown>;
  contract_candidates?: Array<{
    type?: string;
    prompt?: string;
    description?: string;
  }>;
  viral_kicks: ViralKick[];
  duration_ms?: number;
  invariant?: string[];
  variable?: string[];
  do_not?: string[];
  causal_reasoning?: CausalReasoning;
}

// ─────────────────────────────────────────────────────────────
// Raw VDG Types (for API responses)
// ─────────────────────────────────────────────────────────────

/**
 * VDGAudioEvent - 오디오 이벤트
 */
export interface VDGAudioEvent {
  label: string;
  label_en: string;
  intensity: string;
}

/**
 * VDGCameraInfo - 카메라 정보
 */
export interface VDGCameraInfo {
  shot: string;
  shot_en: string;
  move: string;
  move_en: string;
  angle: string;
  angle_en: string;
}

/**
 * VDGSceneData - Raw VDG 씬 데이터 (v3 format)
 */
export interface VDGSceneData {
  scene_id: string;
  scene_number: number;
  time_start: number;
  time_end: number;
  duration_sec: number;
  time_label: string;
  role: string;
  role_en: string;
  summary: string;
  summary_ko: string;
  dialogue: string;
  comedic_device: string[];
  camera: VDGCameraInfo;
  location: string;
  lighting: string;
  lighting_en: string;
  edit_pace: string;
  edit_pace_en: string;
  audio_events: VDGAudioEvent[];
  music: string;
  ambient: string;
}

/**
 * RawVDG - Raw VDG 데이터 (v3 format, from API)
 */
export interface RawVDG {
  title: string;
  title_ko: string;
  total_duration: number;
  scene_count: number;
  scenes: VDGSceneData[];
}

/**
 * OutlierVDGAnalysis - Outlier용 VDG 분석 결과
 */
export interface OutlierVDGAnalysis {
  title?: string;
  title_ko?: string;
  total_duration?: number;
  scene_count?: number;
  scenes?: VDGSceneData[];
  hook_genome?: {
    pattern?: string;
    strength?: number;
    hook_summary?: string;
  };
  intent_layer?: unknown;
  capsule_brief?: unknown;
}

// ─────────────────────────────────────────────────────────────
// CANONICAL_FIELDS - VDG 정규화 필드 목록
// ─────────────────────────────────────────────────────────────

/**
 * CANONICAL_FIELDS - VDG 정규화 필드 목록 (백엔드와 동기화)
 *
 * SSoT: backend/app/schemas/vdg_base.py
 * Total: 22 fields (2026-01-27)
 */
export const CANONICAL_FIELDS = [
  // Core Analysis
  "hook_genome",
  "intent_layer",
  "scenes",
  "mise_en_scene_signals",
  "capsule_brief",
  "viral_kicks",

  // Evidence & Reasoning
  "causal_reasoning",
  "comment_evidence_top5",
  "audience_reaction",

  // Metadata
  "provenance",
  "duration_ms",

  // Rules & Constraints
  "invariant",
  "variable",
  "do_not",
  "contract_candidates",

  // Technical
  "analysis_plan",
  "implementation_layer",
  "entity_hints",

  // Legacy/Additional
  "asr_transcript",
  "ocr_content",
  "commerce",
  "remix_suggestions",
] as const;

export type CanonicalField = (typeof CANONICAL_FIELDS)[number];
