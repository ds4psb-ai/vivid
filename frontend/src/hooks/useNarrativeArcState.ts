'use client';

import { useState, useCallback, useMemo } from 'react';
import {
    HookVariant,
    HookStyle,
    DEFAULT_HOOK_VARIANTS
} from '@/components/HookVariantSelector';

// =============================================================================
// Types
// =============================================================================

export interface NarrativePhase {
    phase: 'hook' | 'setup' | 'build' | 'turn' | 'payoff' | 'climax';
    hook_required?: boolean;
    target_emotion?: string;
    expectation_created?: string;
}

export interface Sequence {
    sequence_id: string;
    name: string;
    t_start: number;
    t_end: number;
    phase: string;
    hook_recommended: boolean;
    hook_intensity: 'soft' | 'medium' | 'strong';
}

export interface NarrativeArc {
    arc_id: string;
    arc_type: 'hook-payoff' | '3-act' | '5-act' | 'circular' | 'parallel';
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

export interface NarrativeArcState {
    arc: NarrativeArc | null;
    isEnabled: boolean;
    selectedHookVariant: HookVariant | null;
    abTestVariants: HookVariant[];
}

export interface NarrativeArcActions {
    setArc: (arc: NarrativeArc | null) => void;
    toggleEnabled: () => void;
    setHookVariant: (variant: HookVariant | null) => void;
    addABTestVariant: (variant: HookVariant) => void;
    removeABTestVariant: (variantId: string) => void;
    clearABTest: () => void;
    setDissonance: (familiar: string, unexpected: string, type: string) => void;
    setEmotionCurve: (start: string, peak: string, end: string) => void;
    addSequence: (sequence: Sequence) => void;
    removeSequence: (sequenceId: string) => void;
    getApiPayload: () => {
        narrative_arc: Record<string, unknown> | null;
        hook_variant: Record<string, unknown> | null;
    };
    reset: () => void;
}

// =============================================================================
// Default Values
// =============================================================================

const DEFAULT_ARC: NarrativeArc = {
    arc_id: 'default',
    arc_type: 'hook-payoff',
    duration_sec: 60,
    is_longform: false,
    emotion_start: 'neutral',
    emotion_peak: 'excited',
    emotion_end: 'satisfied',
    sequences: [],
    shot_roles: [],
};

// =============================================================================
// Hook
// =============================================================================

export function useNarrativeArcState(): NarrativeArcState & NarrativeArcActions {
    const [arc, setArcState] = useState<NarrativeArc | null>(null);
    const [isEnabled, setIsEnabled] = useState(false);
    const [selectedHookVariant, setSelectedHookVariant] = useState<HookVariant | null>(null);
    const [abTestVariants, setAbTestVariants] = useState<HookVariant[]>([]);

    // Actions
    const setArc = useCallback((newArc: NarrativeArc | null) => {
        setArcState(newArc);
        if (newArc) {
            setIsEnabled(true);
        }
    }, []);

    const toggleEnabled = useCallback(() => {
        setIsEnabled(prev => !prev);
    }, []);

    const setHookVariant = useCallback((variant: HookVariant | null) => {
        setSelectedHookVariant(variant);
    }, []);

    const addABTestVariant = useCallback((variant: HookVariant) => {
        setAbTestVariants(prev => {
            if (prev.length >= 4) return prev; // Max 4
            if (prev.some(v => v.variantId === variant.variantId)) return prev;
            return [...prev, variant];
        });
    }, []);

    const removeABTestVariant = useCallback((variantId: string) => {
        setAbTestVariants(prev => prev.filter(v => v.variantId !== variantId));
    }, []);

    const clearABTest = useCallback(() => {
        setAbTestVariants([]);
    }, []);

    const setDissonance = useCallback((familiar: string, unexpected: string, type: string) => {
        setArcState(prev => {
            if (!prev) {
                return {
                    ...DEFAULT_ARC,
                    familiar_element: familiar,
                    unexpected_element: unexpected,
                    dissonance_type: type,
                };
            }
            return {
                ...prev,
                familiar_element: familiar,
                unexpected_element: unexpected,
                dissonance_type: type,
            };
        });
    }, []);

    const setEmotionCurve = useCallback((start: string, peak: string, end: string) => {
        setArcState(prev => {
            if (!prev) {
                return {
                    ...DEFAULT_ARC,
                    emotion_start: start,
                    emotion_peak: peak,
                    emotion_end: end,
                };
            }
            return {
                ...prev,
                emotion_start: start,
                emotion_peak: peak,
                emotion_end: end,
            };
        });
    }, []);

    const addSequence = useCallback((sequence: Sequence) => {
        setArcState(prev => {
            if (!prev) {
                return {
                    ...DEFAULT_ARC,
                    is_longform: true,
                    sequences: [sequence],
                };
            }
            return {
                ...prev,
                is_longform: true,
                sequences: [...prev.sequences, sequence],
            };
        });
    }, []);

    const removeSequence = useCallback((sequenceId: string) => {
        setArcState(prev => {
            if (!prev) return null;
            const sequences = prev.sequences.filter(s => s.sequence_id !== sequenceId);
            return {
                ...prev,
                is_longform: sequences.length > 0,
                sequences,
            };
        });
    }, []);

    const getApiPayload = useCallback(() => {
        if (!isEnabled) {
            return { narrative_arc: null, hook_variant: null };
        }

        const narrativePayload = arc ? {
            arc_id: arc.arc_id,
            arc_type: arc.arc_type,
            duration_sec: arc.duration_sec,
            is_longform: arc.is_longform,
            emotion_start: arc.emotion_start,
            emotion_peak: arc.emotion_peak,
            emotion_end: arc.emotion_end,
            dissonance_type: arc.dissonance_type,
            familiar_element: arc.familiar_element,
            unexpected_element: arc.unexpected_element,
            sequences: arc.sequences,
            shot_roles: arc.shot_roles,
        } : null;

        const hookPayload = selectedHookVariant ? {
            variant_id: selectedHookVariant.variantId,
            style: selectedHookVariant.style,
            intensity: selectedHookVariant.intensity,
            prompt_prefix: selectedHookVariant.promptPrefix,
            prompt_keywords: selectedHookVariant.promptKeywords,
            visual_direction: selectedHookVariant.visualDirection,
            coach_tip_ko: selectedHookVariant.coachTipKo,
        } : null;

        return {
            narrative_arc: narrativePayload,
            hook_variant: hookPayload,
        };
    }, [isEnabled, arc, selectedHookVariant]);

    const reset = useCallback(() => {
        setArcState(null);
        setIsEnabled(false);
        setSelectedHookVariant(null);
        setAbTestVariants([]);
    }, []);

    return {
        // State
        arc,
        isEnabled,
        selectedHookVariant,
        abTestVariants,
        // Actions
        setArc,
        toggleEnabled,
        setHookVariant,
        addABTestVariant,
        removeABTestVariant,
        clearABTest,
        setDissonance,
        setEmotionCurve,
        addSequence,
        removeSequence,
        getApiPayload,
        reset,
    };
}

export default useNarrativeArcState;
