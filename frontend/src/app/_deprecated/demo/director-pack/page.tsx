'use client';

import React from 'react';
import { DirectorPackViewer, DirectorPackCard } from '@/components/DirectorPackViewer';

// Sample DirectorPack data for demonstration
const samplePack = {
    meta: {
        pack_id: 'dp-bong-parasite-001',
        pattern_id: 'bong-2019-parasite',
        version: '1.0.2',
        source_vdg_id: 'vdg-parasite-full',
        source_quality_tier: 'gold',
        compiled_at: new Date().toISOString(),
        compiled_by: 'DirectorCompiler',
        invariant_count: 6,
        slot_count: 4,
        forbidden_count: 3,
        checkpoint_count: 5,
    },
    dna_invariants: [
        {
            rule_id: 'hook_timing_2s',
            rule_type: 'timing' as const,
            name: '훅 타이밍 2초 규칙',
            description: '시청자의 관심을 2초 이내에 사로잡아야 함',
            condition: 'hook_punch_time',
            spec: { operator: '<=', value: 2.0, tolerance: 0.5 },
            time_scope: { t_start: 0, t_end: 3 },
            priority: 'critical' as const,
            confidence: 0.95,
            coach_line: 'Hook needs to hit within 2 seconds!',
            coach_line_ko: '너무 늦어요! 시작하자마자 치고 나가세요.',
        },
        {
            rule_id: 'center_composition',
            rule_type: 'composition' as const,
            name: '중앙 구도 유지',
            description: '주요 피사체를 화면 중앙에 배치',
            condition: 'center_offset_xy',
            spec: { operator: '<=', value: 0.3 },
            time_scope: { t_start: 0, t_end: 10 },
            priority: 'high' as const,
            confidence: 0.88,
            coach_line_ko: '피사체를 중앙에 고정하세요!',
        },
        {
            rule_id: 'vertical_blocking',
            rule_type: 'composition' as const,
            name: '수직 블로킹',
            description: '봉준호 감독 특유의 수직적 공간 활용',
            condition: 'vertical_depth_ratio',
            spec: { operator: '>=', value: 0.6 },
            priority: 'high' as const,
            confidence: 0.82,
            coach_line_ko: '위아래 공간을 더 활용하세요!',
        },
        {
            rule_id: 'lighting_brightness',
            rule_type: 'technical' as const,
            name: '조명 밝기',
            description: '적절한 노출 유지',
            condition: 'brightness_ratio',
            spec: { operator: '>=', value: 0.7 },
            priority: 'medium' as const,
            confidence: 0.75,
            coach_line_ko: '살짝 더 밝게 해볼까요?',
        },
        {
            rule_id: 'audio_clarity',
            rule_type: 'audio' as const,
            name: '음성 명료도',
            description: '대사가 명확하게 들려야 함',
            condition: 'speech_clarity',
            spec: { operator: '>=', value: 0.8 },
            priority: 'high' as const,
            confidence: 0.9,
            coach_line_ko: '목소리가 잘 안 들려요! 마이크 확인!',
        },
        {
            rule_id: 'scene_stability',
            rule_type: 'technical' as const,
            name: '장면 안정성',
            description: '카메라 흔들림 최소화',
            condition: 'stability_score',
            spec: { operator: '>=', value: 0.7 },
            priority: 'medium' as const,
            confidence: 0.7,
            coach_line_ko: '흔들리지 마세요! 안정적으로!',
        },
    ],
    mutation_slots: [
        {
            slot_id: 'opening_tone',
            slot_type: 'tone' as const,
            name: '오프닝 톤',
            description: '시작 톤을 자신의 스타일에 맞게 조절',
            allowed_values: ['활기찬', '시니컬', '진지한 전문가', '친구 같은'],
            default_value: '활기찬',
            persona_presets: {
                energetic: '활기찬',
                professional: '진지한 전문가',
            },
        },
        {
            slot_id: 'camera_distance',
            slot_type: 'style' as const,
            name: '카메라 거리',
            description: '카메라와 피사체 간 거리 조절',
            allowed_values: ['클로즈업', '미디엄', '와이드'],
            default_value: '미디엄',
        },
        {
            slot_id: 'pacing_speed',
            slot_type: 'pacing' as const,
            name: '편집 속도',
            description: '컷 전환 빈도 조절',
            allowed_range: [0.5, 2.0] as [number, number],
            default_value: 1.0,
        },
        {
            slot_id: 'color_grade',
            slot_type: 'color' as const,
            name: '컬러 그레이딩',
            description: '전체적인 색감 톤',
            allowed_values: ['자연스러운', '영화적', '빈티지', '고대비'],
            default_value: '영화적',
        },
    ],
    forbidden_mutations: [
        {
            mutation_id: 'forbid_vertical_video',
            name: '세로 영상 금지',
            description: '시네마틱 장면에서 9:16 세로 비율 사용 금지',
            forbidden_condition: 'aspect_ratio == 9:16',
            severity: 'critical' as const,
            coach_line_ko: '세로 영상은 이 스타일에 맞지 않아요!',
        },
        {
            mutation_id: 'forbid_shaky_cam',
            name: '과도한 흔들림 금지',
            description: '안정적인 샷이 필요한 장면에서 핸드헬드 흔들림 금지',
            forbidden_condition: 'stability_score < 0.3',
            severity: 'major' as const,
            coach_line_ko: '너무 흔들려요! 삼각대를 사용하세요.',
        },
        {
            mutation_id: 'forbid_overexposure',
            name: '과노출 금지',
            description: '화면이 너무 밝아 디테일이 사라지는 것 금지',
            forbidden_condition: 'brightness > 0.95',
            severity: 'major' as const,
            coach_line_ko: '화면이 너무 밝아서 하얗게 날아가고 있어요!',
        },
    ],
    checkpoints: [
        {
            checkpoint_id: 'hook_punch',
            t: 2.0,
            check_rule_ids: ['hook_timing_2s', 'center_composition'],
            coach_prompt_ko: '훅 펀치 확인! 관심을 잡았나요?',
        },
        {
            checkpoint_id: 'scene_1_end',
            t: 10.0,
            check_rule_ids: ['vertical_blocking', 'lighting_brightness'],
            coach_prompt_ko: '첫 번째 장면 종료. 구도와 조명 체크!',
        },
        {
            checkpoint_id: 'mid_video',
            t: 30.0,
            check_rule_ids: ['audio_clarity', 'scene_stability'],
            coach_prompt_ko: '중반부 체크포인트. 오디오와 안정성 확인!',
        },
        {
            checkpoint_id: 'climax_prep',
            t: 45.0,
            check_rule_ids: ['center_composition', 'vertical_blocking'],
            coach_prompt_ko: '클라이맥스 준비! 구도 다시 점검!',
        },
        {
            checkpoint_id: 'outro',
            t: 55.0,
            check_rule_ids: ['hook_timing_2s', 'audio_clarity'],
            coach_prompt_ko: '마무리 단계. 강렬한 엔딩 준비!',
        },
    ],
    policy: {
        interrupt_on_violation: true,
        suggest_on_medium: true,
        log_all_checks: false,
        language: 'ko',
    },
    runtime_contract: {
        max_session_sec: 300,
        checkpoint_interval_sec: 5.0,
        enable_realtime_feedback: true,
        enable_audio_coach: true,
    },
    coach_templates: {
        violation_critical: '⚠️ 중요: {rule_name} 위반. {coach_line}',
        violation_major: '💡 개선점: {rule_name}. {coach_line}',
        violation_minor: '참고: {coach_line}',
        encouragement: '✅ 좋아요! {positive_note}',
        checkpoint_reminder: '⏱️ {t}초 체크포인트: {coach_prompt}',
    },
    scoring: {
        weights: {
            hook_timing_2s: 1.0,
            center_composition: 0.9,
            vertical_blocking: 0.8,
            audio_clarity: 0.85,
        },
        total_possible: 100,
        pass_threshold: 70,
    },
};

export default function DirectorPackDemoPage() {
    return (
        <div className="min-h-screen bg-gray-950 text-white p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                        DirectorPack Viewer Demo
                    </h1>
                    <p className="text-gray-400 mt-2">
                        VDG 2-Pass Pipeline에서 생성된 DirectorPack을 시각화하는 컴포넌트
                    </p>
                </div>

                {/* Compact Card Preview */}
                <div className="mb-8">
                    <h2 className="text-lg font-semibold text-gray-300 mb-4">📦 Compact Card View</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <DirectorPackCard pack={samplePack} onClick={() => alert('Card clicked!')} />
                        <DirectorPackCard
                            pack={{
                                ...samplePack,
                                meta: {
                                    ...samplePack.meta,
                                    pack_id: 'dp-bong-memories-001',
                                    pattern_id: 'bong-2003-memories-of-murder',
                                    source_quality_tier: 'silver',
                                    invariant_count: 4,
                                    slot_count: 3,
                                    forbidden_count: 2,
                                },
                            }}
                        />
                        <DirectorPackCard
                            pack={{
                                ...samplePack,
                                meta: {
                                    ...samplePack.meta,
                                    pack_id: 'dp-bong-host-001',
                                    pattern_id: 'bong-2006-the-host',
                                    source_quality_tier: 'bronze',
                                    invariant_count: 3,
                                    slot_count: 2,
                                    forbidden_count: 1,
                                },
                            }}
                        />
                    </div>
                </div>

                {/* Full Viewer */}
                <div>
                    <h2 className="text-lg font-semibold text-gray-300 mb-4">📋 Full DirectorPack Viewer</h2>
                    <DirectorPackViewer pack={samplePack} />
                </div>

                {/* Usage Instructions */}
                <div className="mt-12 p-6 bg-gray-900/50 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-semibold text-white mb-4">사용법</h3>
                    <pre className="text-sm text-gray-300 overflow-x-auto">
                        {`import { DirectorPackViewer, DirectorPackCard } from '@/components/DirectorPackViewer';

// Full viewer
<DirectorPackViewer 
  pack={directorPack} 
  onEditInvariant={(inv) => console.log('Edit:', inv)}
/>

// Compact card
<DirectorPackCard 
  pack={directorPack} 
  onClick={() => setSelectedPack(pack)}
/>`}
                    </pre>
                </div>
            </div>
        </div>
    );
}
