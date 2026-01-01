'use client';

import React, { useState } from 'react';
import SceneDNAEditor, { Scene, SceneOverride } from '@/components/SceneDNAEditor';
import type { DNAInvariant, MutationSlot } from '@/types/director-pack';

// =============================================================================
// Sample Data - Parasite Movie Scenes
// =============================================================================

const sampleScenes: Scene[] = [
    {
        scene_id: 'scene_hook',
        scene_type: 'hook',
        t_start: 0,
        t_end: 3,
        title: 'HOOK: 반지하 창문',
        description: '기우의 시점에서 반지하 창문을 통해 보이는 세상',
    },
    {
        scene_id: 'scene_build_1',
        scene_type: 'build',
        t_start: 3,
        t_end: 15,
        title: 'BUILD: 잠입 시작',
        description: '기우가 박 사장 집에 처음 방문하는 장면',
    },
    {
        scene_id: 'scene_build_2',
        scene_type: 'build',
        t_start: 15,
        t_end: 30,
        title: 'BUILD: 가족 잠입',
        description: '기정, 기택, 충숙이 차례로 잠입하는 과정',
    },
    {
        scene_id: 'scene_turn',
        scene_type: 'turn',
        t_start: 30,
        t_end: 40,
        title: 'TURN: 지하 벙커 발견',
        description: '문광이 숨겨진 지하 벙커를 보여주는 반전',
    },
    {
        scene_id: 'scene_payoff',
        scene_type: 'payoff',
        t_start: 40,
        t_end: 50,
        title: 'PAYOFF: 폭우 하강',
        description: '비가 쏟아지며 계층을 가르는 하강 시퀀스',
    },
    {
        scene_id: 'scene_climax',
        scene_type: 'climax',
        t_start: 50,
        t_end: 58,
        title: 'CLIMAX: 가든 파티 참극',
        description: '긴장이 폭발하는 생일 파티 클라이맥스',
    },
    {
        scene_id: 'scene_outro',
        scene_type: 'outro',
        t_start: 58,
        t_end: 65,
        title: 'OUTRO: 기우의 계획',
        description: '기우가 편지를 쓰며 희망을 품는 결말',
    },
];

const sampleInvariants: DNAInvariant[] = [
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
];

const sampleSlots: MutationSlot[] = [
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
];

// =============================================================================
// Demo Page
// =============================================================================

export default function SceneDNAEditorDemoPage() {
    const [overrides, setOverrides] = useState<Record<string, SceneOverride>>(() => {
        // Initialize with default overrides for each scene
        const initial: Record<string, SceneOverride> = {};
        sampleScenes.forEach(scene => {
            initial[scene.scene_id] = {
                scene_id: scene.scene_id,
                overridden_invariants: {},
                overridden_slots: {},
                enabled: true,
            };
        });
        return initial;
    });

    const handleOverrideChange = (sceneId: string, override: SceneOverride) => {
        setOverrides(prev => ({
            ...prev,
            [sceneId]: override,
        }));
    };

    return (
        <div className="min-h-screen bg-gray-950 text-white p-8">
            <div className="max-w-5xl mx-auto space-y-8">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-emerald-400 bg-clip-text text-transparent">
                        씬별 DNA 오버라이드 에디터
                    </h1>
                    <p className="text-gray-400 mt-2">
                        Human-in-the-Loop: 각 씬마다 다른 DNA 규칙을 적용하여 다중 씬 품질 일관성 유지
                    </p>
                </div>

                {/* Info Banner */}
                <div className="p-4 bg-blue-950/30 border border-blue-500/30 rounded-xl">
                    <h3 className="font-semibold text-blue-400 mb-2">💡 사용 방법</h3>
                    <ul className="text-sm text-gray-300 space-y-1">
                        <li>• <strong>DNA 규칙 탭</strong>: 각 씬에서 유지해야 할 규칙 값을 조정합니다</li>
                        <li>• <strong>변수 탭</strong>: 톤, 카메라 스타일, 컬러 등을 씬별로 커스텀합니다</li>
                        <li>• <strong>프롬프트 탭</strong>: AI 코치에게 추가 지시를 제공합니다</li>
                        <li>• 수정된 규칙은 <span className="text-amber-400">노란색 뱃지</span>로 표시됩니다</li>
                    </ul>
                </div>

                {/* Main Editor */}
                <SceneDNAEditor
                    scenes={sampleScenes}
                    baseInvariants={sampleInvariants}
                    baseSlots={sampleSlots}
                    overrides={overrides}
                    onOverrideChange={handleOverrideChange}
                />

                {/* Export Preview */}
                <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <h3 className="text-sm font-semibold text-gray-300 mb-3">📤 Export Preview (JSON)</h3>
                    <pre className="text-xs text-gray-400 overflow-x-auto max-h-48 overflow-y-auto bg-gray-800/50 p-3 rounded-lg">
                        {JSON.stringify(overrides, null, 2)}
                    </pre>
                </div>

                {/* Usage Code */}
                <div className="p-4 bg-gray-900/50 rounded-xl border border-gray-800">
                    <h3 className="text-lg font-semibold text-white mb-4">사용법</h3>
                    <pre className="text-sm text-gray-300 overflow-x-auto">
                        {`import SceneDNAEditor from '@/components/SceneDNAEditor';

<SceneDNAEditor
  scenes={videoScenes}
  baseInvariants={directorPack.dna_invariants}
  baseSlots={directorPack.mutation_slots}
  overrides={sceneOverrides}
  onOverrideChange={(sceneId, override) => {
    // Update override state
    setOverrides(prev => ({ ...prev, [sceneId]: override }));
  }}
/>

// 최종 시스템 프롬프트 생성
function buildSystemPrompt(sceneId: string) {
  const override = overrides[sceneId];
  const basePrompt = generateBasePrompt(directorPack);
  
  // Apply overrides
  let prompt = basePrompt;
  Object.entries(override.overridden_invariants).forEach(([ruleId, value]) => {
    prompt += \`\\n[OVERRIDE] \${ruleId}: \${JSON.stringify(value.spec)}\`;
  });
  
  if (override.custom_prompt) {
    prompt += \`\\n[USER CUSTOM] \${override.custom_prompt}\`;
  }
  
  return prompt;
}`}
                    </pre>
                </div>
            </div>
        </div>
    );
}
