'use client';

import React, { useState } from 'react';
import { formatDateTime } from '@/lib/formatters';

// =============================================================================
// Types (matching backend/app/schemas/director_pack.py)
// =============================================================================

interface TimeScope {
    t_start: number;
    t_end: number;
    relative?: boolean;
}

interface RuleSpec {
    operator: string;
    value: unknown;
    tolerance?: number;
}

interface DNAInvariant {
    rule_id: string;
    rule_type: 'timing' | 'composition' | 'engagement' | 'audio' | 'narrative' | 'technical';
    name: string;
    description?: string;
    condition: string;
    spec: RuleSpec;
    time_scope?: TimeScope;
    priority: 'critical' | 'high' | 'medium' | 'low';
    confidence: number;
    coach_line?: string;
    coach_line_ko?: string;
}

interface MutationSlot {
    slot_id: string;
    slot_type: 'style' | 'tone' | 'pacing' | 'color' | 'music' | 'text';
    name: string;
    description?: string;
    allowed_values?: unknown[];
    allowed_range?: [number, number];
    default_value?: unknown;
    persona_presets?: Record<string, unknown>;
}

interface ForbiddenMutation {
    mutation_id: string;
    name: string;
    description: string;
    forbidden_condition: string;
    severity: 'critical' | 'major' | 'minor';
    time_scope?: TimeScope;
    coach_line?: string;
    coach_line_ko?: string;
}

interface Checkpoint {
    checkpoint_id: string;
    t: number;
    check_rule_ids: string[];
    coach_prompt?: string;
    coach_prompt_ko?: string;
}

interface PackMeta {
    pack_id: string;
    pattern_id: string;
    version: string;
    source_vdg_id?: string;
    source_quality_tier?: string;
    compiled_at: string;
    invariant_count: number;
    slot_count: number;
    forbidden_count: number;
    checkpoint_count: number;
}

interface Policy {
    interrupt_on_violation: boolean;
    suggest_on_medium: boolean;
    language: string;
}

interface DirectorPack {
    meta: PackMeta;
    dna_invariants: DNAInvariant[];
    mutation_slots: MutationSlot[];
    forbidden_mutations: ForbiddenMutation[];
    checkpoints: Checkpoint[];
    policy: Policy;
}

// =============================================================================
// Sub-components
// =============================================================================

const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
    const colors: Record<string, string> = {
        critical: 'bg-red-500/20 text-red-400 border-red-500/30',
        high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
        medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        low: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    };

    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${colors[priority] || colors.medium}`}>
            {priority.toUpperCase()}
        </span>
    );
};

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
    const colors: Record<string, string> = {
        critical: 'bg-red-600/20 text-red-400',
        major: 'bg-orange-600/20 text-orange-400',
        minor: 'bg-gray-600/20 text-gray-400',
    };

    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${colors[severity] || colors.major}`}>
            ⛔ {severity}
        </span>
    );
};

const TypeIcon: React.FC<{ type: string }> = ({ type }) => {
    const icons: Record<string, string> = {
        timing: '⏱️',
        composition: '🎬',
        engagement: '🎯',
        audio: '🔊',
        narrative: '📖',
        technical: '⚙️',
        style: '🎨',
        tone: '🎭',
        pacing: '⚡',
        color: '🌈',
        music: '🎵',
        text: '📝',
    };

    return <span className="text-lg">{icons[type] || '📌'}</span>;
};

const ConfidenceBar: React.FC<{ value: number }> = ({ value }) => {
    const percentage = Math.round(value * 100);
    const color = value >= 0.8 ? 'bg-green-500' : value >= 0.5 ? 'bg-yellow-500' : 'bg-red-500';

    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div className={`h-full ${color} transition-all`} style={{ width: `${percentage}%` }} />
            </div>
            <span className="text-xs text-gray-400">{percentage}%</span>
        </div>
    );
};

const TimelineBar: React.FC<{ checkpoints: Checkpoint[]; duration?: number }> = ({ checkpoints, duration = 60 }) => {
    return (
        <div className="relative h-8 bg-gray-800 rounded-lg overflow-hidden">
            {/* Timeline track */}
            <div className="absolute inset-0 flex items-center px-2">
                <div className="w-full h-0.5 bg-gray-600" />
            </div>

            {/* Checkpoint markers */}
            {checkpoints.map((cp) => {
                const position = (cp.t / duration) * 100;
                return (
                    <div
                        key={cp.checkpoint_id}
                        className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-blue-500 rounded-full border-2 border-blue-300 cursor-pointer hover:scale-125 transition-transform"
                        style={{ left: `${Math.min(position, 97)}%` }}
                        title={`${cp.t}s: ${cp.coach_prompt_ko || cp.coach_prompt || 'Checkpoint'}`}
                    />
                );
            })}

            {/* Time labels */}
            <div className="absolute bottom-0 left-2 text-[10px] text-gray-500">0s</div>
            <div className="absolute bottom-0 right-2 text-[10px] text-gray-500">{duration}s</div>
        </div>
    );
};

// =============================================================================
// Section Components
// =============================================================================

const DNAInvariantsSection: React.FC<{ invariants: DNAInvariant[]; expanded: boolean }> = ({ invariants, expanded }) => {
    const [showAll, setShowAll] = useState(false);
    const displayItems = showAll ? invariants : invariants.slice(0, 5);

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                    🧬 DNA Invariants
                    <span className="text-xs text-gray-500 font-normal">유지해야 할 규칙</span>
                </h3>
                <span className="text-xs text-gray-500">{invariants.length}개</span>
            </div>

            {expanded && (
                <div className="space-y-2">
                    {displayItems.map((inv) => (
                        <div
                            key={inv.rule_id}
                            className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-emerald-500/30 transition-colors"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <div className="flex items-center gap-2">
                                    <TypeIcon type={inv.rule_type} />
                                    <div>
                                        <div className="font-medium text-sm text-white">{inv.name}</div>
                                        {inv.description && (
                                            <div className="text-xs text-gray-400 mt-0.5">{inv.description}</div>
                                        )}
                                    </div>
                                </div>
                                <PriorityBadge priority={inv.priority} />
                            </div>

                            <div className="mt-2 flex items-center gap-4 text-xs">
                                <span className="text-gray-500">
                                    조건: <code className="text-emerald-300">{inv.condition} {inv.spec.operator} {JSON.stringify(inv.spec.value)}</code>
                                </span>
                                {inv.time_scope && (
                                    <span className="text-gray-500">
                                        구간: {inv.time_scope.t_start}s ~ {inv.time_scope.t_end}s
                                    </span>
                                )}
                            </div>

                            {inv.coach_line_ko && (
                                <div className="mt-2 p-2 bg-gray-900/50 rounded text-xs text-amber-300/80 italic">
                                    💬 &quot;{inv.coach_line_ko}&quot;
                                </div>
                            )}

                            <div className="mt-2">
                                <ConfidenceBar value={inv.confidence} />
                            </div>
                        </div>
                    ))}

                    {invariants.length > 5 && (
                        <button
                            onClick={() => setShowAll(!showAll)}
                            className="w-full py-2 text-xs text-gray-400 hover:text-white transition-colors"
                        >
                            {showAll ? '접기' : `+${invariants.length - 5}개 더 보기`}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

const MutationSlotsSection: React.FC<{ slots: MutationSlot[]; expanded: boolean }> = ({ slots, expanded }) => {
    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-blue-400 flex items-center gap-2">
                    🎨 Mutation Slots
                    <span className="text-xs text-gray-500 font-normal">변경 가능한 요소</span>
                </h3>
                <span className="text-xs text-gray-500">{slots.length}개</span>
            </div>

            {expanded && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {slots.map((slot) => (
                        <div
                            key={slot.slot_id}
                            className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-blue-500/30 transition-colors"
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <TypeIcon type={slot.slot_type} />
                                <span className="font-medium text-sm text-white">{slot.name}</span>
                            </div>

                            {slot.allowed_values && (
                                <div className="flex flex-wrap gap-1">
                                    {slot.allowed_values.map((val, idx) => (
                                        <span
                                            key={idx}
                                            className={`px-2 py-0.5 text-xs rounded-full ${val === slot.default_value
                                                    ? 'bg-blue-500/30 text-blue-300 border border-blue-500/50'
                                                    : 'bg-gray-700 text-gray-300'
                                                }`}
                                        >
                                            {String(val)}
                                        </span>
                                    ))}
                                </div>
                            )}

                            {slot.allowed_range && (
                                <div className="text-xs text-gray-400">
                                    범위: {slot.allowed_range[0]} ~ {slot.allowed_range[1]}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const ForbiddenSection: React.FC<{ mutations: ForbiddenMutation[]; expanded: boolean }> = ({ mutations, expanded }) => {
    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-red-400 flex items-center gap-2">
                    ⛔ Forbidden Mutations
                    <span className="text-xs text-gray-500 font-normal">금지 규칙</span>
                </h3>
                <span className="text-xs text-gray-500">{mutations.length}개</span>
            </div>

            {expanded && (
                <div className="space-y-2">
                    {mutations.map((mut) => (
                        <div
                            key={mut.mutation_id}
                            className="p-3 bg-red-950/20 rounded-lg border border-red-900/30"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <div>
                                    <div className="font-medium text-sm text-white">{mut.name}</div>
                                    <div className="text-xs text-gray-400 mt-0.5">{mut.description}</div>
                                </div>
                                <SeverityBadge severity={mut.severity} />
                            </div>

                            {mut.coach_line_ko && (
                                <div className="mt-2 text-xs text-red-300/80">
                                    ⚠️ {mut.coach_line_ko}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// =============================================================================
// Main Component
// =============================================================================

interface DirectorPackViewerProps {
    pack: DirectorPack;
    onEditInvariant?: (invariant: DNAInvariant) => void;
    onEditSlot?: (slot: MutationSlot) => void;
    className?: string;
}

export const DirectorPackViewer: React.FC<DirectorPackViewerProps> = ({
    pack,
    className = '',
}) => {
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        dna: true,
        slots: true,
        forbidden: true,
        timeline: true,
    });
    const compiledAt = formatDateTime(pack.meta.compiled_at, 'ko-KR');

    const toggleSection = (section: string) => {
        setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
    };

    const criticalCount = pack.dna_invariants.filter((i) => i.priority === 'critical').length;
    const highCount = pack.dna_invariants.filter((i) => i.priority === 'high').length;

    return (
        <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-800">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-bold text-white flex items-center gap-2">
                            🎬 Director Pack
                            <span className="text-xs font-normal text-gray-400">v{pack.meta.version}</span>
                        </h2>
                        <p className="text-xs text-gray-500 mt-0.5">
                            Pattern: {pack.meta.pattern_id} •
                            Quality: <span className="text-emerald-400">{pack.meta.source_quality_tier || 'N/A'}</span>
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="text-center">
                            <div className="text-xl font-bold text-emerald-400">{pack.meta.invariant_count}</div>
                            <div className="text-[10px] text-gray-500">DNA</div>
                        </div>
                        <div className="text-center">
                            <div className="text-xl font-bold text-blue-400">{pack.meta.slot_count}</div>
                            <div className="text-[10px] text-gray-500">Slots</div>
                        </div>
                        <div className="text-center">
                            <div className="text-xl font-bold text-red-400">{pack.meta.forbidden_count}</div>
                            <div className="text-[10px] text-gray-500">Forbidden</div>
                        </div>
                    </div>
                </div>

                {/* Priority summary */}
                <div className="flex items-center gap-2 mt-3">
                    {criticalCount > 0 && (
                        <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                            🔴 {criticalCount} Critical
                        </span>
                    )}
                    {highCount > 0 && (
                        <span className="px-2 py-0.5 text-xs bg-orange-500/20 text-orange-400 rounded-full">
                            🟠 {highCount} High
                        </span>
                    )}
                </div>
            </div>

            {/* Timeline */}
            <div className="p-4 border-b border-gray-800">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-purple-400">
                        ⏱️ Checkpoints Timeline
                    </h3>
                    <span className="text-xs text-gray-500">{pack.checkpoints.length}개</span>
                </div>
                <TimelineBar checkpoints={pack.checkpoints} duration={60} />
            </div>

            {/* Content sections */}
            <div className="p-4 space-y-6">
                {/* DNA Invariants */}
                <div>
                    <button
                        onClick={() => toggleSection('dna')}
                        className="w-full text-left mb-2"
                    >
                        <DNAInvariantsSection invariants={pack.dna_invariants} expanded={expandedSections.dna} />
                    </button>
                </div>

                {/* Mutation Slots */}
                <div>
                    <button
                        onClick={() => toggleSection('slots')}
                        className="w-full text-left mb-2"
                    >
                        <MutationSlotsSection slots={pack.mutation_slots} expanded={expandedSections.slots} />
                    </button>
                </div>

                {/* Forbidden Mutations */}
                {pack.forbidden_mutations.length > 0 && (
                    <div>
                        <button
                            onClick={() => toggleSection('forbidden')}
                            className="w-full text-left mb-2"
                        >
                            <ForbiddenSection mutations={pack.forbidden_mutations} expanded={expandedSections.forbidden} />
                        </button>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-gray-800/50 border-t border-gray-800 flex items-center justify-between">
                <div className="text-xs text-gray-500">
                    Compiled: {compiledAt ?? '-'}
                </div>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${pack.policy.interrupt_on_violation ? 'bg-green-500' : 'bg-gray-500'}`} />
                    <span className="text-xs text-gray-400">
                        {pack.policy.language === 'ko' ? '한국어' : 'English'} Coach
                    </span>
                </div>
            </div>
        </div>
    );
};

// =============================================================================
// Compact Card Version
// =============================================================================

export const DirectorPackCard: React.FC<{ pack: DirectorPack; onClick?: () => void }> = ({ pack, onClick }) => {
    return (
        <div
            onClick={onClick}
            className="p-4 bg-gray-900 rounded-lg border border-gray-800 hover:border-emerald-500/30 cursor-pointer transition-all hover:shadow-lg hover:shadow-emerald-500/5"
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-2xl">🎬</span>
                    <div>
                        <div className="font-semibold text-white">{pack.meta.pattern_id}</div>
                        <div className="text-xs text-gray-500">v{pack.meta.version}</div>
                    </div>
                </div>
                {pack.meta.source_quality_tier && (
                    <span className={`px-2 py-0.5 text-xs rounded-full ${pack.meta.source_quality_tier === 'gold' ? 'bg-yellow-500/20 text-yellow-400' :
                            pack.meta.source_quality_tier === 'silver' ? 'bg-gray-500/20 text-gray-300' :
                                'bg-amber-900/20 text-amber-600'
                        }`}>
                        {pack.meta.source_quality_tier}
                    </span>
                )}
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 bg-emerald-500/10 rounded">
                    <div className="text-lg font-bold text-emerald-400">{pack.meta.invariant_count}</div>
                    <div className="text-[10px] text-gray-500">DNA</div>
                </div>
                <div className="p-2 bg-blue-500/10 rounded">
                    <div className="text-lg font-bold text-blue-400">{pack.meta.slot_count}</div>
                    <div className="text-[10px] text-gray-500">Slots</div>
                </div>
                <div className="p-2 bg-red-500/10 rounded">
                    <div className="text-lg font-bold text-red-400">{pack.meta.forbidden_count}</div>
                    <div className="text-[10px] text-gray-500">Forbidden</div>
                </div>
            </div>
        </div>
    );
};

export default DirectorPackViewer;
