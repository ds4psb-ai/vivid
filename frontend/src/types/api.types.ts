/**
 * Shared API Types
 * 
 * Common type definitions used across the application.
 */

// =============================================================================
// Settlement Types
// =============================================================================

export interface Settlement {
    id: string;
    tool_key: string;
    tool_run_id: string;
    status: SettlementStatus;
    total_credits: number;
    platform_fee: number;
    creator_pool: number;
    payer_user_id: string;
    created_at: string;
    processed_at: string | null;
    retry_count: number;
}

export type SettlementStatus =
    | "pending"
    | "processing"
    | "completed"
    | "failed"
    | "disputed"
    | "reversed";

export interface Payout {
    id: string;
    settlement_id: string;
    recipient_id: string;
    recipient_tool_key: string | null;
    amount: number;
    share_type: "creator" | "forker" | "platform";
    share_rate: number;
    lineage_position: number;
    status: "pending" | "credited" | "failed";
    credited_at: string | null;
    created_at: string;
}

export interface PayoutSummary {
    period_days: number;
    total_payouts: number;
    total_earned: number;
    avg_per_payout: number;
    pending_amount: number;
}

// =============================================================================
// Review Types
// =============================================================================

export interface Review {
    id: string;
    tool_id: string;
    version_id: string | null;
    review_type: ReviewType;
    status: ReviewStatus;
    priority: number;
    submitted_by: string;
    submission_notes: string | null;
    assigned_to: string | null;
    decision_by: string | null;
    decision_notes: string | null;
    rejection_reason: string | null;
    auto_checks_passed: boolean;
    auto_checks_score: number;
    created_at: string;
}

export type ReviewType =
    | "fork_submission"
    | "tier_promotion"
    | "code_update"
    | "safety_audit"
    | "quality_check";

export type ReviewStatus =
    | "pending"
    | "in_progress"
    | "approved"
    | "rejected"
    | "changes_requested";

export interface ReviewStats {
    pending_count: number;
    in_progress_count: number;
    decided_today: number;
    avg_auto_score: number;
}

export interface CheckResult {
    id: string;
    category: string;
    check_name: string;
    description: string | null;
    passed: boolean;
    score: number;
    details: Record<string, any>;
    error_message: string | null;
    is_automated: boolean;
}

// =============================================================================
// Tool Types
// =============================================================================

export interface Tool {
    id: string;
    tool_key: string;
    display_name: string;
    description: string;
    category: string;
    tier: ToolTier;
    credit_cost: number;
    input_schema: Record<string, any>;
    output_schema: Record<string, any>;
    usage_count: number;
    fork_count: number;
    quality_rating: number | null;
    safety_rating: number | null;
    created_by: string;
    parent_tool_id: string | null;
    created_at: string;
    // Optional fields from extended queries
    live_version?: ToolVersion;
}

export type ToolTier = "experimental" | "verified" | "certified";

export interface ToolVersion {
    id: string;
    tool_id: string;
    version: string;
    version_number: number;
    code_type: CodeType;
    code_content: string;
    system_prompt: string | null;
    status: VersionStatus;
    is_live: boolean;
    created_by: string;
    created_at: string;
}

export type CodeType =
    | "prompt_template"
    | "python_function"
    | "api_call"
    | "composite"
    | "static";

export type VersionStatus =
    | "draft"
    | "pending_review"
    | "approved"
    | "rejected"
    | "deprecated";

// =============================================================================
// Fork Types
// =============================================================================

export interface DiffStats {
    lines_added: number;
    lines_removed: number;
    lines_modified: number;
    similarity_ratio: number;
    diff_score: number;
    is_trivial: boolean;
}

export interface DiffPreview {
    diff_content: string;
    stats: DiffStats;
    semantic_changes: Record<string, any>;
    sybil_warning: string | null;
}

export interface ForkResult {
    tool_id: string;
    tool_key: string;
    version_id: string;
    fork_event_id: string;
    diff: DiffStats;
    needs_review: boolean;
    sybil_flagged: boolean;
}
