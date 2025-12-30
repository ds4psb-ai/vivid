/**
 * DirectorPack API Hook
 * 
 * Provides hooks for loading DirectorPack data and applying scene overrides
 * to the capsule execution pipeline for multi-scene consistency.
 */

import { useState, useCallback } from 'react';
import type { DirectorPack } from '@/types/director-pack';
import type { SceneOverride } from '@/components/SceneDNAEditor';

// =============================================================================
// Types
// =============================================================================

export interface UseDirectorPackOptions {
    capsuleId?: string;
    patternId?: string;
}

export interface UseDirectorPackReturn {
    pack: DirectorPack | null;
    isLoading: boolean;
    error: Error | null;
    loadPack: (packId: string) => Promise<void>;
    createFromCapsule: (capsuleId: string) => Promise<DirectorPack>;
    applyToGeneration: (overrides?: Record<string, SceneOverride>) => DirectorPackPayload;
}

export interface DirectorPackPayload {
    director_pack: DirectorPack;
    scene_overrides?: Record<string, SceneOverride>;
}

// =============================================================================
// Default DirectorPack for Testing
// =============================================================================

export const DEFAULT_BONG_PACK: Partial<DirectorPack> = {
    meta: {
        pack_id: 'dp_bong_default',
        pattern_id: 'auteur.bong-joon-ho',
        version: '1.0.0',
        compiled_at: new Date().toISOString(),
        invariant_count: 5,
        slot_count: 4,
        forbidden_count: 3,
        checkpoint_count: 6,
    },
    dna_invariants: [
        {
            rule_id: 'hook_timing_2s',
            rule_type: 'timing',
            name: '훅 타이밍 2초',
            description: '시청자 관심을 2초 이내에 사로잡기',
            condition: 'hook_punch_time',
            spec: { operator: '<=', value: 2.0 },
            priority: 'critical',
            confidence: 0.95,
            coach_line_ko: '훅이 너무 늦어요! 시작하자마자 치고 나가세요.',
        },
        {
            rule_id: 'center_composition',
            rule_type: 'composition',
            name: '중앙 구도',
            description: '주요 피사체 중앙 배치',
            condition: 'center_offset',
            spec: { operator: '<=', value: 0.3 },
            priority: 'high',
            confidence: 0.88,
            coach_line_ko: '피사체를 중앙으로 모아주세요!',
        },
        {
            rule_id: 'vertical_blocking',
            rule_type: 'composition',
            name: '수직 블로킹',
            description: '봉준호 스타일의 수직적 공간 활용',
            condition: 'vertical_depth',
            spec: { operator: '>=', value: 0.6 },
            priority: 'high',
            confidence: 0.82,
            coach_line_ko: '위아래 공간을 더 활용하세요!',
        },
        {
            rule_id: 'cut_frequency',
            rule_type: 'timing',
            name: '컷 빈도',
            description: '적절한 컷 전환 속도 유지',
            condition: 'cuts_per_second',
            spec: { operator: '<=', value: 0.5 },
            priority: 'medium',
            confidence: 0.75,
            coach_line_ko: '컷이 너무 빨라요. 좀 더 여유를 가지세요.',
        },
        {
            rule_id: 'audio_clarity',
            rule_type: 'audio',
            name: '음성 명료도',
            description: '대사가 명확하게 들리도록',
            condition: 'speech_clarity',
            spec: { operator: '>=', value: 0.8 },
            priority: 'high',
            confidence: 0.9,
            coach_line_ko: '목소리가 잘 안 들려요! 마이크 확인!',
        },
    ],
    mutation_slots: [
        {
            slot_id: 'opening_tone',
            slot_type: 'tone',
            name: '오프닝 톤',
            description: '씬 시작 분위기',
            allowed_values: ['활기찬', '시니컬', '진지한', '친근한'],
            default_value: '활기찬',
        },
        {
            slot_id: 'camera_style',
            slot_type: 'style',
            name: '카메라 스타일',
            allowed_values: ['클로즈업', '미디엄', '와이드', '극단적 와이드'],
            default_value: '미디엄',
        },
        {
            slot_id: 'color_grade',
            slot_type: 'color',
            name: '컬러 그레이딩',
            allowed_values: ['자연스러운', '영화적', '빈티지', '고대비'],
            default_value: '영화적',
        },
        {
            slot_id: 'pacing_speed',
            slot_type: 'pacing',
            name: '편집 속도',
            allowed_range: [0.5, 2.0],
            default_value: 1.0,
        },
    ],
    forbidden_mutations: [
        {
            mutation_id: 'jump_cut_abuse',
            name: '점프컷 남용',
            description: '불필요한 점프컷 사용 금지',
            forbidden_condition: 'jump_cuts > 3 per minute',
            severity: 'major',
            coach_line_ko: '점프컷이 너무 많아요!',
        },
        {
            mutation_id: 'dutch_angle',
            name: '더치 앵글 금지',
            description: '기울어진 카메라 앵글 사용 금지',
            forbidden_condition: 'camera_tilt > 15deg',
            severity: 'major',
            coach_line_ko: '카메라를 똑바로!',
        },
        {
            mutation_id: 'fast_zoom',
            name: '빠른 줌 금지',
            description: '급격한 줌 인/아웃 금지',
            forbidden_condition: 'zoom_speed > 2x',
            severity: 'minor',
            coach_line_ko: '줌이 너무 빨라요!',
        },
    ],
    checkpoints: [
        { checkpoint_id: 'cp_hook', t: 2, active_rules: ['hook_timing_2s'], coach_prompt_ko: '훅 체크' },
        { checkpoint_id: 'cp_10s', t: 10, active_rules: ['center_composition'], coach_prompt_ko: '10초 체크' },
        { checkpoint_id: 'cp_30s', t: 30, active_rules: ['vertical_blocking'], coach_prompt_ko: '30초 체크' },
        { checkpoint_id: 'cp_60s', t: 60, active_rules: ['cut_frequency'], coach_prompt_ko: '1분 체크' },
        { checkpoint_id: 'cp_90s', t: 90, active_rules: ['audio_clarity'], coach_prompt_ko: '1분 30초 체크' },
        { checkpoint_id: 'cp_end', t: 120, active_rules: ['center_composition', 'audio_clarity'], coach_prompt_ko: '마무리 체크' },
    ],
    policy: {
        interrupt_on_violation: false,
        suggest_on_medium: true,
        language: 'ko',
    },
    runtime_contract: {
        max_session_sec: 180,
        checkpoint_interval_sec: 30,
        enable_realtime_feedback: false,
        enable_audio_coach: false,
    },
};

// =============================================================================
// Hook Implementation
// =============================================================================

export function useDirectorPack(options: UseDirectorPackOptions = {}): UseDirectorPackReturn {
    const [pack, setPack] = useState<DirectorPack | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const loadPack = useCallback(async (packId: string) => {
        setIsLoading(true);
        setError(null);

        try {
            // TODO: Replace with actual API call when backend endpoint is ready
            // const response = await fetch(`/api/v1/director-packs/${packId}`);
            // const data = await response.json();

            // For now, use default pack
            if (packId.includes('bong') || options.capsuleId?.includes('bong')) {
                setPack(DEFAULT_BONG_PACK as DirectorPack);
            } else {
                throw new Error(`DirectorPack not found: ${packId}`);
            }
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to load DirectorPack'));
        } finally {
            setIsLoading(false);
        }
    }, [options.capsuleId]);

    const createFromCapsule = useCallback(async (capsuleId: string): Promise<DirectorPack> => {
        // TODO: Call backend to compile DirectorPack from capsule
        // const response = await fetch(`/api/v1/capsules/${capsuleId}/compile-pack`, { method: 'POST' });
        // return await response.json();

        if (capsuleId.includes('bong')) {
            return DEFAULT_BONG_PACK as DirectorPack;
        }

        throw new Error(`Cannot create DirectorPack for capsule: ${capsuleId}`);
    }, []);

    const applyToGeneration = useCallback((
        overrides?: Record<string, SceneOverride>
    ): DirectorPackPayload => {
        if (!pack) {
            throw new Error('No DirectorPack loaded');
        }

        return {
            director_pack: pack,
            scene_overrides: overrides,
        };
    }, [pack]);

    return {
        pack,
        isLoading,
        error,
        loadPack,
        createFromCapsule,
        applyToGeneration,
    };
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Convert DirectorPack to a format suitable for API request
 */
export function serializeDirectorPack(pack: DirectorPack): Record<string, unknown> {
    return {
        meta: pack.meta,
        dna_invariants: pack.dna_invariants,
        mutation_slots: pack.mutation_slots,
        forbidden_mutations: pack.forbidden_mutations,
        checkpoints: pack.checkpoints,
        policy: pack.policy,
        runtime_contract: pack.runtime_contract,
    };
}

/**
 * Merge scene overrides with base DirectorPack
 */
export function applySceneOverrides(
    pack: DirectorPack,
    overrides: Record<string, SceneOverride>
): DirectorPack {
    // Create a copy
    const merged = { ...pack };

    // Apply overrides to DNA invariants
    Object.entries(overrides).forEach(([sceneId, override]) => {
        if (!override.enabled) return;

        Object.entries(override.overridden_invariants).forEach(([ruleId, newSpec]) => {
            const idx = merged.dna_invariants.findIndex(inv => inv.rule_id === ruleId);
            if (idx >= 0 && newSpec) {
                merged.dna_invariants[idx] = {
                    ...merged.dna_invariants[idx],
                    ...newSpec,
                };
            }
        });
    });

    return merged;
}

export default useDirectorPack;
