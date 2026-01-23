/**
 * Admin/Ops API Types
 * 
 * Types for admin operations, pipeline status, pattern management, and ops actions.
 */

import type { StageSummary } from "./types";

// Re-export common type
export type PipelineStageSummary = StageSummary;

export interface PipelineStatus {
    raw_assets: PipelineStageSummary;
    raw_restricted: number;
    video_segments: PipelineStageSummary;
    notebook_library: PipelineStageSummary;
    notebook_assets: PipelineStageSummary;
    evidence_records: PipelineStageSummary;
    evidence_missing_source_pack?: number;
    evidence_ops_only?: number;
    pattern_candidates: PipelineStageSummary;
    pattern_candidate_status: Record<string, number>;
    patterns: PipelineStageSummary;
    pattern_status: Record<string, number>;
    pattern_trace: PipelineStageSummary;
    pattern_version?: string | null;
    pattern_version_at?: string | null;
    pattern_versions?: PatternVersion[];
    capsule_specs: PipelineStageSummary;
    templates: PipelineStageSummary;
    templates_public: number;
    templates_missing_provenance?: number;
    template_versions: PipelineStageSummary;
    canvases: PipelineStageSummary;
    capsule_runs: PipelineStageSummary;
    capsule_run_status: Record<string, number>;
    generation_runs: PipelineStageSummary;
    generation_run_status: Record<string, number>;
    quarantine_total?: number;
    quarantine_by_sheet?: Record<string, number>;
    quarantine_by_reason?: Record<string, number>;
    quarantine_items?: Array<{ sheet: string; reason: string; count: number }>;
    quarantine_sample?: Array<{ sheet: string; reason: string; row: string; created_at: string }>;
}

export interface PatternPromotionRequest {
    derive_from_evidence?: boolean;
    min_confidence?: number;
    min_sources?: number;
    min_fitness_score?: number;
    allow_empty_evidence?: boolean;
    allow_missing_raw?: boolean;
    note?: string;
    dry_run?: boolean;
}

export interface PatternPromotionResponse {
    changed: boolean;
    stats: Record<string, number>;
    derived_candidates?: number;
    pattern_version?: string | null;
    note?: string | null;
}

export interface CapsuleRefreshRequest {
    pattern_version?: string;
    dry_run?: boolean;
    only_active?: boolean;
}

export interface CapsuleRefreshResponse {
    pattern_version: string;
    updated: number;
    dry_run: boolean;
    only_active: boolean;
}

export interface SheetsSyncResponse {
    status: string;
    duration_ms: number;
    quarantine_total: number;
    quarantine_by_sheet: Record<string, number>;
    quarantine_by_reason: Record<string, number>;
}

export interface OpsActionLog {
    id: string;
    action_type: string;
    status: string;
    note?: string | null;
    payload: Record<string, unknown>;
    stats: Record<string, unknown>;
    duration_ms?: number | null;
    actor_id?: string | null;
    created_at: string;
}

export interface RunTraceSummaryItem {
    date: string;
    run_count: number;
    avg_latency_ms: number | null;
    avg_cost_usd: number | null;
    total_cost_usd: number | null;
    status_breakdown: Record<string, number>;
}

export interface RunTraceSummary {
    items: RunTraceSummaryItem[];
    total_runs: number;
    period_start: string;
    period_end: string;
    overall_avg_latency_ms: number | null;
    overall_avg_cost_usd: number | null;
    overall_total_cost_usd: number | null;
}

export interface EvidenceCoverageByType {
    claim_type: string;
    total_claims: number;
    claims_with_evidence: number;
    coverage_rate: number;
}

export interface EvidenceCoverage {
    total_claims: number;
    claims_with_evidence: number;
    claims_without_evidence: number;
    coverage_rate: number;
    avg_evidence_per_claim: number;
    min_evidence_count: number;
    max_evidence_count: number;
    coverage_by_type: EvidenceCoverageByType[];
    calculated_at: string;
}

export interface PatternVersion {
    id: string;
    version: string;
    note?: string | null;
    created_at: string;
}

export interface PatternItem {
    id: string;
    name: string;
    pattern_type: string;
    description?: string | null;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface PatternTraceItem {
    id: string;
    source_id: string;
    pattern_id: string;
    pattern_name?: string | null;
    pattern_type?: string | null;
    weight?: number | null;
    evidence_ref?: string | null;
    created_at: string;
    updated_at: string;
}

// Affiliate types
export interface AffiliateProfile {
    user_id: string;
    affiliate_code: string;
    referral_link?: string | null;
    total_referrals: number;
    total_earned: number;
    pending_count: number;
}

export interface AffiliateReferral {
    id: string;
    referee_label?: string | null;
    status: string;
    reward_status: string;
    reward_amount: number;
    referee_reward_amount: number;
    created_at: string;
}

export interface AffiliateTrackRequest {
    affiliate_code: string;
    referee_label?: string;
}

export interface AffiliateRewardRequest {
    referral_id: string;
    referrer_reward?: number;
    referee_reward?: number;
    note?: string;
}

export interface AffiliateRewardResponse {
    referral_id: string;
    status: string;
    reward_status: string;
    referrer_reward: number;
    referee_reward: number;
    reward_ledger_id?: string | null;
    referee_reward_ledger_id?: string | null;
}

// Notebook/Raw Asset types
export interface NotebookLibraryItem {
    id: string;
    notebook_id: string;
    title: string;
    notebook_ref: string;
    owner_id?: string | null;
    cluster_id?: string | null;
    cluster_label?: string | null;
    cluster_tags: string[];
    guide_scope?: string | null;
    curator_notes?: string | null;
    source_ids: string[];
    source_count?: number | null;
    created_at: string;
    updated_at: string;
}

export interface NotebookAssetItem {
    id: string;
    notebook_id: string;
    asset_id: string;
    asset_type: string;
    asset_ref?: string | null;
    title?: string | null;
    tags: string[];
    notes?: string | null;
    created_at: string;
    updated_at: string;
}

export interface DerivedInsight {
    id: string;
    source_id: string;
    summary: string;
    guide_type?: string | null;
    story_beats?: Record<string, unknown>[] | null;
    storyboard_cards?: Record<string, unknown>[] | null;
    labels: string[];
    signature_motifs: string[];
    output_type: string;
    output_language: string;
    notebook_id?: string | null;
    generated_at?: string | null;
    created_at: string;
    updated_at: string;
}

export interface RawAsset {
    id: string;
    source_id: string;
    source_url: string;
    source_type: string;
    title?: string | null;
    director?: string | null;
    year?: number | null;
    duration_sec?: number | null;
    language?: string | null;
    tags: string[];
    scene_ranges?: string | null;
    notes?: string | null;
    rights_status?: string | null;
    created_by?: string | null;
    created_at: string;
    updated_at: string;
}
