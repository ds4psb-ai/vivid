'use client';

import React, { useState } from 'react';
import Image from "next/image";
import type { DNAInvariant, MutationSlot } from '@/types/director-pack';
import { formatTime } from '@/lib/formatters';

// =============================================================================
// Types
// =============================================================================

export interface Scene {
    scene_id: string;
    scene_type: 'hook' | 'build' | 'turn' | 'payoff' | 'climax' | 'outro';
    t_start: number;
    t_end: number;
    title: string;
    description?: string;
    thumbnail_url?: string;
}

export interface SceneOverride {
    scene_id: string;
    overridden_invariants: Record<string, Partial<DNAInvariant>>;
    overridden_slots: Record<string, unknown>;
    custom_prompt?: string;
    notes?: string;
    enabled: boolean;
}

export interface SceneDNAEditorProps {
    scenes: Scene[];
    baseInvariants: DNAInvariant[];
    baseSlots: MutationSlot[];
    overrides: Record<string, SceneOverride>;
    onOverrideChange: (sceneId: string, override: SceneOverride) => void;
    className?: string;
}

type SceneTab = 'dna' | 'slots' | 'prompt';

// =============================================================================
// Helper Components
// =============================================================================

const SceneTypeBadge: React.FC<{ type: Scene['scene_type'] }> = ({ type }) => {
    const colors: Record<string, string> = {
        hook: 'bg-red-500/20 text-red-400 border-red-500/30',
        build: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        turn: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
        payoff: 'bg-green-500/20 text-green-400 border-green-500/30',
        climax: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
        outro: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    };

    const icons: Record<string, string> = {
        hook: '🎣',
        build: '📈',
        turn: '🔄',
        payoff: '💰',
        climax: '🔥',
        outro: '🎬',
    };

    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${colors[type] || colors.build}`}>
            {icons[type]} {type.toUpperCase()}
        </span>
    );
};

const InvariantOverrideRow: React.FC<{
    invariant: DNAInvariant;
    override?: Partial<DNAInvariant>;
    onOverride: (value: Partial<DNAInvariant> | null) => void;
}> = ({ invariant, override, onOverride }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [localValue, setLocalValue] = useState<string>(
        override?.spec?.value !== undefined
            ? String(override.spec.value)
            : String(invariant.spec.value)
    );

    const isOverridden = override !== undefined;
    const displayValue = override?.spec?.value ?? invariant.spec.value;

    const handleSave = () => {
        const numValue = parseFloat(localValue);
        if (!isNaN(numValue)) {
            onOverride({
                ...override,
                spec: {
                    ...invariant.spec,
                    value: numValue,
                },
            });
        }
        setIsEditing(false);
    };

    const handleReset = () => {
        onOverride(null);
        setLocalValue(String(invariant.spec.value));
    };

    return (
        <div className={`p-3 rounded-lg border transition-all ${isOverridden
                ? 'bg-amber-950/20 border-amber-500/30'
                : 'bg-gray-800/30 border-gray-700/30'
            }`}>
            <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white truncate">{invariant.name}</span>
                        {isOverridden && (
                            <span className="px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded">
                                수정됨
                            </span>
                        )}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                        {invariant.condition} {invariant.spec.operator}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {isEditing ? (
                        <>
                            <input
                                type="number"
                                value={localValue}
                                onChange={(e) => setLocalValue(e.target.value)}
                                className="w-20 px-2 py-1 text-sm bg-gray-900 border border-gray-600 rounded text-white focus:border-amber-500 focus:outline-none"
                                step="0.1"
                            />
                            <button
                                onClick={handleSave}
                                className="px-2 py-1 text-xs bg-amber-500 text-black rounded hover:bg-amber-400"
                            >
                                저장
                            </button>
                            <button
                                onClick={() => setIsEditing(false)}
                                className="px-2 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-500"
                            >
                                취소
                            </button>
                        </>
                    ) : (
                        <>
                            <span className={`px-2 py-1 text-sm rounded ${isOverridden ? 'bg-amber-500/20 text-amber-300' : 'bg-gray-700 text-gray-300'
                                }`}>
                                {displayValue}
                            </span>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="p-1 text-gray-400 hover:text-white transition-colors"
                                title="수정"
                            >
                                ✏️
                            </button>
                            {isOverridden && (
                                <button
                                    onClick={handleReset}
                                    className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                                    title="원래 값으로 복원"
                                >
                                    ↩️
                                </button>
                            )}
                        </>
                    )}
                </div>
            </div>

            {invariant.coach_line_ko && (
                <div className="mt-2 text-xs text-gray-400 italic">
                    💬 {invariant.coach_line_ko}
                </div>
            )}
        </div>
    );
};

const SlotOverrideRow: React.FC<{
    slot: MutationSlot;
    override?: unknown;
    onOverride: (value: unknown | null) => void;
}> = ({ slot, override, onOverride }) => {
    const currentValue = override ?? slot.default_value;
    const isOverridden = override !== undefined;

    return (
        <div className={`p-3 rounded-lg border transition-all ${isOverridden
                ? 'bg-blue-950/20 border-blue-500/30'
                : 'bg-gray-800/30 border-gray-700/30'
            }`}>
            <div className="flex items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{slot.name}</span>
                    {isOverridden && (
                        <span className="px-1.5 py-0.5 text-[10px] bg-blue-500/20 text-blue-400 rounded">
                            커스텀
                        </span>
                    )}
                </div>
                {isOverridden && (
                    <button
                        onClick={() => onOverride(null)}
                        className="text-xs text-gray-400 hover:text-red-400"
                    >
                        기본값으로
                    </button>
                )}
            </div>

            {slot.allowed_values && (
                <div className="flex flex-wrap gap-1.5">
                    {slot.allowed_values.map((val, idx) => (
                        <button
                            key={idx}
                            onClick={() => onOverride(val === slot.default_value && !isOverridden ? undefined : val)}
                            className={`px-2.5 py-1 text-xs rounded-full transition-all ${currentValue === val
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            {String(val)}
                        </button>
                    ))}
                </div>
            )}

            {slot.allowed_range && (
                <div className="flex items-center gap-3">
                    <input
                        type="range"
                        min={slot.allowed_range[0]}
                        max={slot.allowed_range[1]}
                        step={0.1}
                        value={currentValue}
                        onChange={(e) => onOverride(parseFloat(e.target.value))}
                        className="flex-1 accent-blue-500"
                    />
                    <span className="text-sm text-blue-400 w-12 text-right">{currentValue}</span>
                </div>
            )}
        </div>
    );
};

// =============================================================================
// Scene Card Component
// =============================================================================

const SceneCard: React.FC<{
    scene: Scene;
    baseInvariants: DNAInvariant[];
    baseSlots: MutationSlot[];
    override: SceneOverride;
    onOverrideChange: (override: SceneOverride) => void;
    isExpanded: boolean;
    onToggle: () => void;
}> = ({ scene, baseInvariants, baseSlots, override, onOverrideChange, isExpanded, onToggle }) => {
    const [activeTab, setActiveTab] = useState<SceneTab>('dna');

    const handleInvariantOverride = (invariantId: string, value: Partial<DNAInvariant> | null) => {
        const newOverrides = { ...override.overridden_invariants };
        if (value === null) {
            delete newOverrides[invariantId];
        } else {
            newOverrides[invariantId] = value;
        }
        onOverrideChange({
            ...override,
            overridden_invariants: newOverrides,
        });
    };

    const handleSlotOverride = (slotId: string, value: unknown | null) => {
        const newOverrides = { ...override.overridden_slots };
        if (value === null || value === undefined) {
            delete newOverrides[slotId];
        } else {
            newOverrides[slotId] = value;
        }
        onOverrideChange({
            ...override,
            overridden_slots: newOverrides,
        });
    };

    const handlePromptChange = (prompt: string) => {
        onOverrideChange({
            ...override,
            custom_prompt: prompt || undefined,
        });
    };

    const overrideCount =
        Object.keys(override.overridden_invariants).length +
        Object.keys(override.overridden_slots).length +
        (override.custom_prompt ? 1 : 0);

    return (
        <div className={`rounded-xl border overflow-hidden transition-all ${override.enabled
                ? 'border-emerald-500/30 bg-gray-900/50'
                : 'border-gray-800 bg-gray-900/30 opacity-60'
            }`}>
            {/* Header */}
            <div
                className="p-4 cursor-pointer hover:bg-gray-800/30 transition-colors"
                onClick={onToggle}
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        {/* Thumbnail */}
                        <div className="w-16 h-10 bg-gray-800 rounded overflow-hidden flex-shrink-0">
                            {scene.thumbnail_url ? (
                                <Image
                                    src={scene.thumbnail_url}
                                    alt=""
                                    width={64}
                                    height={40}
                                    className="h-full w-full object-cover"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-gray-600">
                                    🎬
                                </div>
                            )}
                        </div>

                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-semibold text-white">{scene.title}</span>
                                <SceneTypeBadge type={scene.scene_type} />
                                {overrideCount > 0 && (
                                    <span className="px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded-full">
                                        {overrideCount} 수정
                                    </span>
                                )}
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">
                                {formatTime(scene.t_start)} - {formatTime(scene.t_end)}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Enable/Disable toggle */}
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onOverrideChange({ ...override, enabled: !override.enabled });
                            }}
                            className={`w-10 h-5 rounded-full transition-colors relative ${override.enabled ? 'bg-emerald-500' : 'bg-gray-600'
                                }`}
                        >
                            <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${override.enabled ? 'translate-x-5' : 'translate-x-0.5'
                                }`} />
                        </button>

                        {/* Expand arrow */}
                        <span className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                            ▼
                        </span>
                    </div>
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && override.enabled && (
                <div className="border-t border-gray-800">
                    {/* Tabs */}
                    <div className="flex border-b border-gray-800">
                        {([
                            { id: 'dna', label: '🧬 DNA 규칙', count: Object.keys(override.overridden_invariants).length },
                            { id: 'slots', label: '🎨 변수', count: Object.keys(override.overridden_slots).length },
                            { id: 'prompt', label: '📝 프롬프트', count: override.custom_prompt ? 1 : 0 },
                        ] as Array<{ id: SceneTab; label: string; count: number }>).map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${activeTab === tab.id
                                        ? 'text-white border-b-2 border-emerald-500 bg-gray-800/30'
                                        : 'text-gray-400 hover:text-gray-200'
                                    }`}
                            >
                                {tab.label}
                                {tab.count > 0 && (
                                    <span className="ml-1.5 px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded-full">
                                        {tab.count}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                        {activeTab === 'dna' && (
                            <>
                                <p className="text-xs text-gray-500 mb-3">
                                    이 씬에서 적용될 DNA 규칙을 수정합니다. 수정하지 않으면 기본값이 적용됩니다.
                                </p>
                                {baseInvariants.map((inv) => (
                                    <InvariantOverrideRow
                                        key={inv.rule_id}
                                        invariant={inv}
                                        override={override.overridden_invariants[inv.rule_id]}
                                        onOverride={(value) => handleInvariantOverride(inv.rule_id, value)}
                                    />
                                ))}
                            </>
                        )}

                        {activeTab === 'slots' && (
                            <>
                                <p className="text-xs text-gray-500 mb-3">
                                    이 씬에서 사용할 스타일 변수를 선택합니다.
                                </p>
                                {baseSlots.map((slot) => (
                                    <SlotOverrideRow
                                        key={slot.slot_id}
                                        slot={slot}
                                        override={override.overridden_slots[slot.slot_id]}
                                        onOverride={(value) => handleSlotOverride(slot.slot_id, value)}
                                    />
                                ))}
                            </>
                        )}

                        {activeTab === 'prompt' && (
                            <>
                                <p className="text-xs text-gray-500 mb-3">
                                    이 씬에만 적용될 커스텀 프롬프트를 입력합니다. 시스템 프롬프트 뒤에 추가됩니다.
                                </p>
                                <textarea
                                    value={override.custom_prompt || ''}
                                    onChange={(e) => handlePromptChange(e.target.value)}
                                    placeholder="예: 이 씬은 더 극적으로 연출해주세요. 조명을 낮추고 긴장감을 높여주세요."
                                    className="w-full h-32 p-3 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 resize-none focus:border-emerald-500 focus:outline-none"
                                />
                                {override.custom_prompt && (
                                    <button
                                        onClick={() => handlePromptChange('')}
                                        className="text-xs text-gray-400 hover:text-red-400"
                                    >
                                        프롬프트 삭제
                                    </button>
                                )}
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

// =============================================================================
// Main Component
// =============================================================================

export const SceneDNAEditor: React.FC<SceneDNAEditorProps> = ({
    scenes,
    baseInvariants,
    baseSlots,
    overrides,
    onOverrideChange,
    className = '',
}) => {
    const [expandedScene, setExpandedScene] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    const totalOverrides = Object.values(overrides).reduce((sum, o) =>
        sum + Object.keys(o.overridden_invariants).length + Object.keys(o.overridden_slots).length + (o.custom_prompt ? 1 : 0)
        , 0);

    const enabledScenes = Object.values(overrides).filter(o => o.enabled).length;

    const handleToggle = (sceneId: string) => {
        setExpandedScene(expandedScene === sceneId ? null : sceneId);
    };

    const handleResetAll = () => {
        scenes.forEach(scene => {
            onOverrideChange(scene.scene_id, {
                scene_id: scene.scene_id,
                overridden_invariants: {},
                overridden_slots: {},
                enabled: true,
            });
        });
    };

    return (
        <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-800">
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <h2 className="text-lg font-bold text-white flex items-center gap-2">
                            🎬 씬별 DNA 오버라이드
                        </h2>
                        <p className="text-xs text-gray-500 mt-0.5">
                            각 씬마다 다른 DNA 규칙을 적용할 수 있습니다
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="text-center">
                            <div className="text-xl font-bold text-emerald-400">{enabledScenes}</div>
                            <div className="text-[10px] text-gray-500">활성 씬</div>
                        </div>
                        <div className="text-center">
                            <div className="text-xl font-bold text-amber-400">{totalOverrides}</div>
                            <div className="text-[10px] text-gray-500">수정됨</div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="씬 검색..."
                        className="flex-1 px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none"
                    />
                    <button
                        onClick={handleResetAll}
                        className="px-3 py-1.5 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
                    >
                        모두 초기화
                    </button>
                </div>
            </div>

            {/* Scene List */}
            <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
                {scenes
                    .filter(s => !searchQuery || s.title.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map((scene) => (
                        <SceneCard
                            key={scene.scene_id}
                            scene={scene}
                            baseInvariants={baseInvariants}
                            baseSlots={baseSlots}
                            override={overrides[scene.scene_id] || {
                                scene_id: scene.scene_id,
                                overridden_invariants: {},
                                overridden_slots: {},
                                enabled: true,
                            }}
                            onOverrideChange={(override) => onOverrideChange(scene.scene_id, override)}
                            isExpanded={expandedScene === scene.scene_id}
                            onToggle={() => handleToggle(scene.scene_id)}
                        />
                    ))}
            </div>

            {/* Footer Summary */}
            <div className="px-4 py-3 bg-gray-800/50 border-t border-gray-800">
                <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>
                        {scenes.length}개 씬 중 {enabledScenes}개 활성화, {totalOverrides}개 규칙 수정됨
                    </span>
                    <button
                        className="px-3 py-1 bg-emerald-500 text-black font-medium rounded hover:bg-emerald-400 transition-colors"
                    >
                        적용하기
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SceneDNAEditor;
