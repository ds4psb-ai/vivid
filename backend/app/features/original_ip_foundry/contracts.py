"""Typed contracts for Original-IP Foundry runtime APIs."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FoundryRightsAsset(BaseModel):
    asset_id: str = Field(..., min_length=1, max_length=160)
    source_license: str = Field("", max_length=200)
    derivative_allowed: bool = True
    allowed_actions: List[str] = Field(default_factory=list)
    blocked_elements: List[str] = Field(default_factory=list)


class FoundryRightsEvaluationRequest(BaseModel):
    action: str = Field("reference", min_length=1, max_length=64)
    requested_elements: List[str] = Field(default_factory=list)
    assets: List[FoundryRightsAsset] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="rights")


class FoundryRightsAssetDecision(BaseModel):
    asset_id: str
    decision: Literal["allow", "review", "block"]
    reason_codes: List[str] = Field(default_factory=list)


class FoundryRightsEvaluationResponse(BaseModel):
    decision: Literal["allow", "review", "block"]
    reason_codes: List[str] = Field(default_factory=list)
    per_asset: List[FoundryRightsAssetDecision] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)


class FoundryShotInput(BaseModel):
    shot_id: str = Field(..., min_length=1, max_length=80)
    shot_size: str = Field("medium", max_length=32)
    camera_angle: str = Field("eye_level", max_length=32)
    camera_movement: str = Field("static", max_length=32)
    emotion_tone: str = Field("neutral", max_length=48)
    transition_to_next: str = Field("cut", max_length=32)
    location: Optional[str] = Field(default=None, max_length=120)
    characters: List[str] = Field(default_factory=list)
    duration_sec: float = Field(default=6.0, ge=0.5, le=120.0)


class FoundryPatternExtractionRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    scene_id: str = Field(..., min_length=1, max_length=120)
    reference_id: Optional[str] = Field(default=None, max_length=120)
    shots: List[FoundryShotInput] = Field(default_factory=list)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="video")


class FoundryPatternAtom(BaseModel):
    atom_id: str
    camera_angle: str
    camera_movement: str
    shot_size: str
    emotion_tone: str
    transition: str
    frequency: int
    confidence: float


class FoundryPatternExtractionResponse(BaseModel):
    project_id: str
    scene_id: str
    pattern_atoms: List[FoundryPatternAtom] = Field(default_factory=list)
    transition_rules: List[dict] = Field(default_factory=list)
    total_shots: int = 0


class FoundrySceneContext(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    scene_id: str = Field(..., min_length=1, max_length=120)
    previous_scene_id: Optional[str] = Field(default=None, max_length=120)
    target_emotion: str = Field("neutral", max_length=48)
    location: str = Field("unknown", max_length=120)
    characters: List[str] = Field(default_factory=list)
    desired_camera_rhythm: str = Field("balanced", max_length=32)
    intent_tags: List[str] = Field(default_factory=list)


class FoundryCandidateInput(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=80)
    title: str = Field("", max_length=160)
    shots: List[FoundryShotInput] = Field(default_factory=list)
    rights_assets: List[FoundryRightsAsset] = Field(default_factory=list)
    mise_en_scene_score: float = Field(0.5, ge=0.0, le=1.0)
    story_intent_fit: float = Field(0.5, ge=0.0, le=1.0)
    director_style_fit: float = Field(0.5, ge=0.0, le=1.0)
    execution_feasibility: float = Field(0.5, ge=0.0, le=1.0)
    clone_risk: float = Field(0.0, ge=0.0, le=1.0)
    pattern_tags: List[str] = Field(default_factory=list)


class FoundryRecommendationRequest(BaseModel):
    scene_context: FoundrySceneContext
    candidates: List[FoundryCandidateInput] = Field(default_factory=list)
    rights_action: str = Field("remix", min_length=1, max_length=64)
    continuity_floor: float = Field(0.6, ge=0.0, le=1.0)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="recommendation")


class FoundryCandidateResult(BaseModel):
    candidate_id: str
    title: str
    decision: Literal["allow", "review", "hold", "block"]
    final_score: float
    continuity_score: float
    reason_codes: List[str] = Field(default_factory=list)
    recommendation_rationale: List[str] = Field(default_factory=list)
    rights_decision: Literal["allow", "review", "block"]
    recommended_shots: List[FoundryShotInput] = Field(default_factory=list)


class FoundryRecommendationResponse(BaseModel):
    scene_id: str
    ranked: List[FoundryCandidateResult] = Field(default_factory=list)
    continuity_gate: float


class FoundryExperimentAssignRequest(BaseModel):
    tenant_id: str = Field(default="default", min_length=1, max_length=120)
    experiment_key: str = Field(..., min_length=1, max_length=120)
    user_key: str = Field(..., min_length=1, max_length=120)
    scene_id: Optional[str] = Field(default=None, max_length=120)
    variants: List[str] = Field(default_factory=lambda: ["A", "B", "AB_A", "AB_B"])
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="experiment")


class FoundryExperimentAssignResponse(BaseModel):
    tenant_id: str = "default"
    experiment_key: str
    assigned_variant: str
    hash_slot: int


class FoundryExperimentFeedbackRequest(BaseModel):
    tenant_id: str = Field(default="default", min_length=1, max_length=120)
    experiment_key: str = Field(..., min_length=1, max_length=120)
    user_key: str = Field(..., min_length=1, max_length=120)
    variant: str = Field(..., min_length=1, max_length=60)
    outcome: Literal["accepted", "edited", "rejected"]
    completion_seconds: Optional[int] = Field(default=None, ge=0, le=86400)
    edit_distance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="experiment_feedback")


class FoundryMemoryNormalizeRequest(BaseModel):
    tenant_id: str = Field(default="default", min_length=1, max_length=120)
    project_id: str = Field(..., min_length=1, max_length=120)
    scene_id: Optional[str] = Field(default=None, max_length=120)
    source_channel: Literal["telegram", "web", "notion", "other"] = "other"
    note: str = Field(..., min_length=1, max_length=10000)
    attachments: List[str] = Field(default_factory=list)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="memory")


class FoundryRetrievalRequest(BaseModel):
    tenant_id: str = Field(default="default", min_length=1, max_length=120)
    project_id: str = Field(..., min_length=1, max_length=120)
    query_type: Literal["director_context", "shot_reference", "payload_filter", "transition_rerank"]
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(5, ge=1, le=30)
    filters: Optional[dict] = Field(default=None)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="retrieval")


class FoundryC2PAAction(BaseModel):
    action: str = Field(..., min_length=1, max_length=80)
    parameters: dict = Field(default_factory=dict)


class FoundryC2PAIngredient(BaseModel):
    asset_id: str = Field(..., min_length=1, max_length=160)
    relationship: str = Field(default="componentOf", max_length=40)
    title: Optional[str] = Field(default=None, max_length=200)
    source_license: Optional[str] = Field(default=None, max_length=200)


class FoundryC2PAExportRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    scene_id: str = Field(..., min_length=1, max_length=120)
    asset_id: str = Field(..., min_length=1, max_length=160)
    title: str = Field(..., min_length=1, max_length=200)
    generator_model: str = Field(..., min_length=1, max_length=120)
    source_license: Optional[str] = Field(default=None, max_length=200)
    actions: List[FoundryC2PAAction] = Field(default_factory=list)
    provenance_trace: List[FoundryC2PAIngredient] = Field(default_factory=list)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="provenance")


class FoundryC2PAExportResponse(BaseModel):
    spec_version: str
    manifest: dict
    compliance: dict
    warnings: List[str] = Field(default_factory=list)


class FoundryWorkerDispatchRequest(BaseModel):
    tenant_id: str = Field(default="default", min_length=1, max_length=120)
    project_id: str = Field(..., min_length=1, max_length=120)
    job_type: str = Field(..., min_length=1, max_length=120)
    payload: dict = Field(default_factory=dict)
    provider: Optional[Literal["agent0", "taskiq", "temporal"]] = None
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="worker_dispatch")


class FoundryWorkerDispatchResponse(BaseModel):
    provider: str
    status: str
    job_id: str
    job_type: str
    tenant_id: str
    project_id: str
    payload: dict = Field(default_factory=dict)


class FoundryWorkerStatusResponse(BaseModel):
    provider: str
    job_id: str
    status: str
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    job_type: Optional[str] = None
    updated_at: Optional[str] = None
    message: Optional[str] = None


class FoundryEnginePromptResult(BaseModel):
    engine: str
    prompt_text: str
    negative_prompt: str = ""
    metadata: dict = Field(default_factory=dict)


class FoundryPromptCompileRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    scene_id: str = Field(..., min_length=1, max_length=120)
    shots: List[FoundryShotInput] = Field(default_factory=list)
    engines: Optional[List[str]] = Field(default=None)
    model: Optional[str] = Field(default=None, max_length=80)
    input_type: Optional[str] = Field(default="prompt_compile")


class FoundryCompiledShot(BaseModel):
    shot_id: str
    engines: dict[str, FoundryEnginePromptResult] = Field(default_factory=dict)


class FoundryPromptCompileResponse(BaseModel):
    project_id: str
    scene_id: str
    compiled_shots: List[FoundryCompiledShot] = Field(default_factory=list)


class ChannelWebhookPayload(BaseModel):
    event_id: Optional[str] = Field(default=None, max_length=120)
    user_id: str = Field(..., min_length=1, max_length=120)
    text: str = Field(default="", max_length=10000)
    tenant_id: str = Field(default="default", max_length=120)
    project_id: Optional[str] = Field(default=None, max_length=120)
    attachments: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ChannelReplyRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=120)
    text: str = Field(..., min_length=1, max_length=10000)
    attachments: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ChannelUploadRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=120)
    media_url: str = Field(..., min_length=1, max_length=2000)
    media_type: str = Field(default="image", max_length=20)
    caption: str = Field(default="", max_length=500)
    metadata: dict = Field(default_factory=dict)
