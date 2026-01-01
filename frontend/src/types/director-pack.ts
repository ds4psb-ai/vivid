/**
 * DirectorPack TypeScript Types
 * 
 * Matches backend/app/schemas/director_pack.py
 * Used for type-safe DirectorPack handling in frontend
 */

// =============================================================================
// Enums
// =============================================================================

export type RulePriority = 'critical' | 'high' | 'medium' | 'low';

export type InvariantType =
    | 'timing'
    | 'composition'
    | 'engagement'
    | 'audio'
    | 'narrative'
    | 'technical';

export type SlotType =
    | 'style'
    | 'tone'
    | 'pacing'
    | 'color'
    | 'music'
    | 'text';

export type Severity = 'critical' | 'major' | 'minor';

// =============================================================================
// Source Reference & Evidence
// =============================================================================

export interface SourceRef {
    source_type: 'vdg' | 'metric' | 'entity' | 'frame';
    source_id: string;
    timestamp?: number;
    confidence: number;
}

// =============================================================================
// Rule Components
// =============================================================================

export interface RuleSpec {
    operator: 'eq' | 'gt' | 'lt' | 'gte' | 'lte' | '<=' | '>=' | 'between' | 'in' | 'exists';
    value: unknown;
    tolerance?: number;
    unit?: string;
    aggregation?: 'mean' | 'median' | 'max' | 'min';
    required_inputs?: string[];
}

export interface TimeScope {
    t_start: number;
    t_end: number;
    relative?: boolean;
}

// =============================================================================
// DNA Invariants (What to KEEP)
// =============================================================================

export interface DNAInvariant {
    rule_id: string;
    rule_type: InvariantType;
    name: string;
    description?: string;

    // Rule specification
    condition: string;
    spec: RuleSpec;

    // Scope & Priority
    time_scope?: TimeScope;
    priority: RulePriority;

    // Evidence
    source_refs?: SourceRef[];
    confidence: number;

    // Coaching
    coach_line?: string;
    coach_line_ko?: string;

    // Additional
    weight?: number;
    tolerance?: 'tight' | 'normal' | 'loose';
    fallback?: string;
    evidence_refs?: string[];
}

// =============================================================================
// Mutation Slots (What CAN change)
// =============================================================================

export interface MutationSlot {
    slot_id: string;
    slot_type: SlotType;
    name: string;
    description?: string;

    // Allowed values
    allowed_values?: unknown[];
    allowed_range?: [number, number];
    default_value?: unknown;

    // Persona binding
    persona_presets?: Record<string, unknown>;

    // Evidence
    source_refs?: SourceRef[];

    // Coaching templates per option
    coach_line_templates?: Record<string, string>;
}

// =============================================================================
// Forbidden Mutations (What to NEVER do)
// =============================================================================

export interface ForbiddenMutation {
    mutation_id: string;
    name: string;
    description: string;

    // What's forbidden
    forbidden_condition: string;
    severity: Severity;

    // When it applies
    time_scope?: TimeScope;

    // Coaching
    coach_line?: string;
    coach_line_ko?: string;

    // Evidence
    source_refs?: SourceRef[];
    evidence_refs?: string[];
}

// =============================================================================
// Checkpoints (Time-based rule activation)
// =============================================================================

export interface Checkpoint {
    checkpoint_id: string;
    t: number;

    // What to check - can be either format
    check_rule_ids?: string[];
    active_rules?: string[];
    t_window?: [number, number];

    // Coaching
    coach_prompt?: string;
    coach_prompt_ko?: string;
    note?: string;
}

// =============================================================================
// Policy & Runtime Contract
// =============================================================================

export interface Policy {
    interrupt_on_violation: boolean;
    suggest_on_medium: boolean;
    log_all_checks?: boolean;
    language: 'ko' | 'en';
    one_command_only?: boolean;
    cooldown_sec?: number;
    barge_in_handling?: 'stop_and_ack' | 'ignore' | 'queue';
    uncertainty_policy?: 'ask_user' | 'skip' | 'default';
}

export interface RuntimeContract {
    max_session_sec: number;
    checkpoint_interval_sec: number;
    enable_realtime_feedback: boolean;
    enable_audio_coach: boolean;
    input_modalities_expected?: string[];
    verification_granularity?: 'frame' | 'window' | 'scene';
    max_instruction_words?: number;
    cooldown_sec_default?: number;
}

// =============================================================================
// Coach Line Templates
// =============================================================================

export interface CoachLineTemplates {
    violation_critical: string;
    violation_major: string;
    violation_minor: string;
    encouragement: string;
    checkpoint_reminder: string;
}

// =============================================================================
// Scoring
// =============================================================================

export interface Scoring {
    weights?: Record<string, number>;
    dna_weights?: Record<string, number>;
    total_possible: number;
    pass_threshold: number;
    risk_penalty_rules?: Array<{
        trigger: string;
        penalty: number;
    }>;
}

// =============================================================================
// Pack Metadata
// =============================================================================

export interface PackMeta {
    pack_id: string;
    pattern_id: string;
    version: string;

    // Source
    source_vdg_id?: string;
    source_quality_tier?: 'gold' | 'silver' | 'bronze' | 'reject';

    // Compilation
    compiled_at: string;
    compiled_by?: string;
    generated_at?: string;
    compiler_version?: string;
    source_refs?: Array<{
        vdg_content_id: string;
        vdg_version: string;
    }>;

    // Stats
    invariant_count: number;
    slot_count: number;
    forbidden_count: number;
    checkpoint_count: number;
}

// =============================================================================
// Director Pack (Main Type)
// =============================================================================

export interface DirectorPack {
    // Metadata
    meta: PackMeta;

    // Version info (alternative formats)
    pack_version?: string;
    pattern_id?: string;
    goal?: string;
    pack_meta?: PackMeta;

    // Core Rules
    dna_invariants: DNAInvariant[];
    mutation_slots: MutationSlot[];
    forbidden_mutations: ForbiddenMutation[];
    checkpoints: Checkpoint[];

    // Policy & Config
    policy: Policy;
    runtime_contract: RuntimeContract;

    // Templates & Scoring
    coach_templates?: CoachLineTemplates;
    scoring?: Scoring;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface DirectorPackResponse {
    success: boolean;
    data?: DirectorPack;
    error?: string;
}

export interface DirectorPackListResponse {
    success: boolean;
    data?: DirectorPack[];
    total?: number;
    error?: string;
}

// =============================================================================
// UI State Types
// =============================================================================

export interface DirectorPackViewerState {
    expandedSections: {
        dna: boolean;
        slots: boolean;
        forbidden: boolean;
        timeline: boolean;
    };
    selectedInvariant?: DNAInvariant;
    selectedSlot?: MutationSlot;
    filterPriority?: RulePriority;
}

// =============================================================================
// Utility Types
// =============================================================================

export type DNAInvariantWithStatus = DNAInvariant & {
    status: 'passed' | 'violated' | 'pending' | 'skipped';
    lastCheckedAt?: string;
    violationCount?: number;
};

export type CheckpointWithProgress = Checkpoint & {
    reached: boolean;
    passedRules: string[];
    failedRules: string[];
};
