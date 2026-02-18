import type {
  FoundryRightsEvaluationRequest,
  FoundryPatternExtractionRequest,
  FoundryRecommendationRequest,
  FoundryRightsEvaluationResponse,
  FoundryPatternExtractionResponse,
  FoundryRecommendationResponse,
  FoundryExperimentSummaryResponse,
  FoundryKPISnapshotResponse,
} from "@/lib/api";

// Demo request payloads (for calling APIs)
export const DEMO_RIGHTS_REQUEST: FoundryRightsEvaluationRequest = {
  action: "remix",
  requested_elements: ["composition", "color_palette", "camera_angle"],
  assets: [
    { asset_id: "asset_kubrick_001", source_license: "FAIR_USE", derivative_allowed: true, allowed_actions: ["remix", "reference"] },
    { asset_id: "asset_bong_001", source_license: "CC_BY", derivative_allowed: true, allowed_actions: ["remix", "reference", "commercial"] },
  ],
  evidence_refs: ["db:foundry:rights_eval:demo"],
};

export const DEMO_PATTERN_REQUEST: FoundryPatternExtractionRequest = {
  project_id: "demo-project",
  scene_id: "scene_01",
  shots: [
    { shot_id: "shot_001", shot_size: "wide", camera_angle: "low_angle", camera_movement: "dolly", emotion_tone: "tension", transition_to_next: "match_cut", location: "hotel_corridor", characters: ["jack"], duration_sec: 8 },
    { shot_id: "shot_002", shot_size: "close_up", camera_angle: "eye_level", camera_movement: "static", emotion_tone: "fear", transition_to_next: "cut", location: "hotel_corridor", characters: ["jack", "wendy"], duration_sec: 4 },
    { shot_id: "shot_003", shot_size: "medium", camera_angle: "dutch_angle", camera_movement: "handheld", emotion_tone: "tension", transition_to_next: "dissolve", location: "hotel_bathroom", characters: ["jack"], duration_sec: 6 },
  ],
};

export const DEMO_RECOMMENDATION_REQUEST: FoundryRecommendationRequest = {
  scene_context: {
    project_id: "demo-project",
    scene_id: "scene_02",
    previous_scene_id: "scene_01",
    target_emotion: "tension",
    location: "hotel_corridor",
    characters: ["jack", "wendy"],
    desired_camera_rhythm: "dynamic",
    intent_tags: ["tension", "pursuit", "isolation"],
  },
  candidates: [
    {
      candidate_id: "cand_001",
      title: "Steadicam Pursuit",
      shots: [{ shot_id: "c1_shot1", shot_size: "medium", camera_angle: "eye_level", camera_movement: "steadicam", emotion_tone: "tension", location: "hotel_corridor", characters: ["jack"] }],
      rights_assets: [{ asset_id: "a1", source_license: "CC0" }],
      mise_en_scene_score: 0.85,
      story_intent_fit: 0.9,
      director_style_fit: 0.8,
      execution_feasibility: 0.95,
      pattern_tags: ["tension", "tracking", "corridor"],
    },
    {
      candidate_id: "cand_002",
      title: "Static Confrontation",
      shots: [{ shot_id: "c2_shot1", shot_size: "close_up", camera_angle: "low_angle", camera_movement: "static", emotion_tone: "power", location: "hotel_lobby", characters: ["jack"] }],
      rights_assets: [{ asset_id: "a2", source_license: "FAIR_USE" }],
      mise_en_scene_score: 0.7,
      story_intent_fit: 0.6,
      director_style_fit: 0.75,
      execution_feasibility: 0.9,
      pattern_tags: ["power", "confrontation"],
    },
  ],
  rights_action: "remix",
  continuity_floor: 0.6,
};

// Demo RESPONSE payloads (fallback when API is disabled)
export const DEMO_RIGHTS_RESPONSE: FoundryRightsEvaluationResponse = {
  decision: "allow",
  reason_codes: ["ALL_ASSETS_CLEAR"],
  per_asset: [
    { asset_id: "asset_kubrick_001", decision: "review", reason_codes: ["FAIR_USE_REQUIRES_REVIEW"] },
    { asset_id: "asset_bong_001", decision: "allow", reason_codes: [] },
  ],
  evidence_refs: ["db:foundry:rights_eval:demo"],
};

export const DEMO_PATTERN_RESPONSE: FoundryPatternExtractionResponse = {
  project_id: "demo-project",
  scene_id: "scene_01",
  pattern_atoms: [
    { atom_id: "low_angle::dolly::wide::tension::match_cut", camera_angle: "low_angle", camera_movement: "dolly", shot_size: "wide", emotion_tone: "tension", transition: "match_cut", frequency: 1, confidence: 0.75 },
    { atom_id: "eye_level::static::close_up::fear::cut", camera_angle: "eye_level", camera_movement: "static", shot_size: "close_up", emotion_tone: "fear", transition: "cut", frequency: 1, confidence: 0.75 },
    { atom_id: "dutch_angle::handheld::medium::tension::dissolve", camera_angle: "dutch_angle", camera_movement: "handheld", shot_size: "medium", emotion_tone: "tension", transition: "dissolve", frequency: 1, confidence: 0.75 },
  ],
  transition_rules: [
    { rule: "wide->close_up:match_cut", frequency: 1 },
    { rule: "close_up->medium:cut", frequency: 1 },
  ],
  total_shots: 3,
};

export const DEMO_RECOMMENDATION_RESPONSE: FoundryRecommendationResponse = {
  scene_id: "scene_02",
  continuity_gate: 0.6,
  ranked: [
    {
      candidate_id: "cand_001",
      title: "Steadicam Pursuit",
      decision: "allow",
      final_score: 0.8542,
      continuity_score: 0.82,
      reason_codes: [],
      recommendation_rationale: ["Continuity score 0.82를 기준으로 후보를 평가했습니다.", "Pattern affinity 0.33를 반영했습니다.", "Rights decision은 allow입니다."],
      rights_decision: "allow",
      recommended_shots: [{ shot_id: "c1_shot1", shot_size: "medium", camera_angle: "eye_level", camera_movement: "steadicam", emotion_tone: "tension", location: "hotel_corridor", characters: ["jack"] }],
    },
    {
      candidate_id: "cand_002",
      title: "Static Confrontation",
      decision: "hold",
      final_score: 0.6231,
      continuity_score: 0.48,
      reason_codes: ["CONTINUITY_BELOW_GATE", "QUALITY_GATE_REVIEW"],
      recommendation_rationale: ["Continuity score 0.48를 기준으로 후보를 평가했습니다.", "Pattern affinity 0.00를 반영했습니다.", "Rights decision은 review입니다."],
      rights_decision: "review",
      recommended_shots: [{ shot_id: "c2_shot1", shot_size: "close_up", camera_angle: "low_angle", camera_movement: "static", emotion_tone: "power", location: "hotel_lobby", characters: ["jack"] }],
    },
  ],
};

export const DEMO_EXPERIMENT_RESPONSE: FoundryExperimentSummaryResponse = {
  experiment_key: "default",
  total_events: 47,
  variants: {
    A: { total: 25, accepted: 15, edited: 7, rejected: 3, avg_completion_seconds: 12.4, accept_rate: 0.6, edit_rate: 0.28, reject_rate: 0.12 },
    B: { total: 22, accepted: 10, edited: 8, rejected: 4, avg_completion_seconds: 18.2, accept_rate: 0.4545, edit_rate: 0.3636, reject_rate: 0.1818 },
  },
};

export const DEMO_KPI_RESPONSE: FoundryKPISnapshotResponse = {
  p95_latency_ms: 1850,
  p50_latency_ms: 420,
  pattern_reuse_rate: 0.65,
  mean_continuity: 0.72,
  continuity_uplift: 0.22,
  sample_counts: { latency: 150, continuity: 80, pattern_queries: 45 },
};
