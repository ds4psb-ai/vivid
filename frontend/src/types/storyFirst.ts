/**
 * Story-First Types
 * 
 * Centralized type definitions for Story-First features:
 * - NarrativeArc, Sequence, NarrativePhase
 * - HookVariant, HookStyle
 * - Compliance reports
 */

// =============================================================================
// Hook Types
// =============================================================================

export type HookStyle =
    | 'shock'
    | 'curiosity'
    | 'emotion'
    | 'question'
    | 'paradox'
    | 'tease'
    | 'action'
    | 'calm';

export interface HookVariant {
    variantId: string;
    style: HookStyle;
    intensity: 'soft' | 'medium' | 'strong' | 'explosive';
    promptPrefix: string;
    promptKeywords: string[];
    visualDirection: string;
    coachTipKo: string;
    isControl?: boolean;
}

// =============================================================================
// Narrative Types
// =============================================================================

export type NarrativePhaseType = 'hook' | 'setup' | 'build' | 'turn' | 'payoff' | 'climax' | 'resolution' | 'transition';

export interface NarrativePhase {
    phase: NarrativePhaseType;
    hook_required?: boolean;
    target_emotion?: string;
    expectation_created?: string;
}

export interface Sequence {
    sequence_id: string;
    name: string;
    t_start: number;
    t_end: number;
    phase: NarrativePhaseType;
    hook_recommended: boolean;
    hook_intensity: 'soft' | 'medium' | 'strong';
}

export type ArcType = 'hook-payoff' | '3-act' | '5-act' | 'circular' | 'parallel';

export interface NarrativeArc {
    arc_id: string;
    arc_type: ArcType;
    duration_sec: number;
    is_longform: boolean;
    emotion_start: string;
    emotion_peak: string;
    emotion_end: string;
    dissonance_type?: string;
    familiar_element?: string;
    unexpected_element?: string;
    sequences: Sequence[];
    shot_roles: NarrativePhase[];
}

// =============================================================================
// State Types
// =============================================================================

export interface NarrativeArcState {
    arc: NarrativeArc | null;
    isEnabled: boolean;
    selectedHookVariant: HookVariant | null;
    abTestVariants: HookVariant[];
}

// =============================================================================
// API Payload Types
// =============================================================================

export interface StoryFirstApiPayload {
    narrative_arc: {
        arc_type: ArcType;
        emotion_curve: {
            start: string;
            peak: string;
            end: string;
        };
        dissonance?: {
            type: string;
            familiar: string;
            unexpected: string;
        };
        is_longform: boolean;
        sequences?: Sequence[];
    } | null;
    hook_variant: {
        style: HookStyle;
        intensity: string;
        prompt_prefix: string;
    } | null;
}

// =============================================================================
// Compliance Types
// =============================================================================

export interface RuleResult {
    rule_id: string;
    rule_name: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    level: 'compliant' | 'partial' | 'violation' | 'unknown';
    confidence: number;
    message: string;
    expected?: string | number | null;
    actual?: string | number | null;
}

export interface ShotComplianceReport {
    shot_id: string;
    badge?: string;
    overall_level: 'compliant' | 'partial' | 'violation' | 'unknown';
    overall_confidence: number;
    rule_results: RuleResult[];
    critical_violations: number;
    high_violations: number;
    suggestions: string[];
}

export interface BatchComplianceReport {
    total_shots: number;
    compliant_shots: number;
    partial_shots: number;
    violation_shots: number;
    overall_compliance_rate: number;
    summary: string;
    shot_reports: ShotComplianceReport[];
}

// =============================================================================
// Preset Variants
// =============================================================================

export const DEFAULT_HOOK_VARIANTS: HookVariant[] = [
    {
        variantId: 'shock_1',
        style: 'shock',
        intensity: 'explosive',
        promptPrefix: 'Shocking, unexpected opening.',
        promptKeywords: ['explosion', 'sudden', 'dramatic'],
        visualDirection: '극적인 클로즈업, 빠른 줌',
        coachTipKo: '가장 충격적인 순간으로 시작하세요',
        isControl: true,
    },
    {
        variantId: 'curiosity_1',
        style: 'curiosity',
        intensity: 'medium',
        promptPrefix: 'Mysterious, intriguing opening.',
        promptKeywords: ['mysterious', 'hidden', 'reveal'],
        visualDirection: '부분만 보여주기, 미스터리한 조명',
        coachTipKo: '전체가 아닌 일부만 보여주세요',
    },
    {
        variantId: 'paradox_1',
        style: 'paradox',
        intensity: 'strong',
        promptPrefix: 'Contradictory juxtaposition opening.',
        promptKeywords: ['contrast', 'unexpected', 'paradox'],
        visualDirection: '대비되는 요소 병치',
        coachTipKo: '익숙함과 낯섦을 조합하세요',
    },
    {
        variantId: 'tease_1',
        style: 'tease',
        intensity: 'strong',
        promptPrefix: 'Shows the climax first.',
        promptKeywords: ['result', 'climax', 'flash forward'],
        visualDirection: '결과 장면 → 어떻게 여기까지?',
        coachTipKo: '결과를 먼저 보여주고 궁금하게 만드세요',
    },
];
