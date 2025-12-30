'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import {
    Plus, Trash2, GripVertical, Clock, Zap, ChevronDown, ChevronUp,
    Film, Play, Pause, SkipForward, Edit2, Check, X, Copy,
    Sparkles, AlertTriangle
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export interface Sequence {
    sequence_id: string;
    name: string;
    t_start: number;
    t_end: number;
    phase: 'hook' | 'setup' | 'build' | 'turn' | 'payoff' | 'climax' | 'resolution' | 'transition';
    hook_recommended: boolean;
    hook_intensity: 'soft' | 'medium' | 'strong';
}

export interface SequenceEditorProps {
    sequences: Sequence[];
    totalDuration: number;
    onSequencesChange: (sequences: Sequence[]) => void;
    onTotalDurationChange?: (duration: number) => void;
    disabled?: boolean;
    className?: string;
}

// =============================================================================
// Constants
// =============================================================================

const PHASE_CONFIG: Record<string, { label: string; color: string; bgColor: string; description: string }> = {
    hook: { label: '훅', color: 'text-red-400', bgColor: 'bg-red-500', description: '관객의 시선을 사로잡는 시작' },
    setup: { label: '설정', color: 'text-blue-400', bgColor: 'bg-blue-500', description: '상황과 캐릭터 소개' },
    build: { label: '상승', color: 'text-yellow-400', bgColor: 'bg-yellow-500', description: '긴장감 고조' },
    turn: { label: '전환', color: 'text-purple-400', bgColor: 'bg-purple-500', description: '반전 또는 예상치 못한 전개' },
    payoff: { label: '보상', color: 'text-emerald-400', bgColor: 'bg-emerald-500', description: '기대감 충족' },
    climax: { label: '클라이맥스', color: 'text-orange-400', bgColor: 'bg-orange-500', description: '가장 긴장되는 순간' },
    resolution: { label: '해결', color: 'text-cyan-400', bgColor: 'bg-cyan-500', description: '마무리와 해소' },
    transition: { label: '전환', color: 'text-gray-400', bgColor: 'bg-gray-500', description: '시퀀스 간 연결' },
};

const INTENSITY_CONFIG = {
    soft: { label: '부드럽게', color: 'text-gray-400', dotColor: 'bg-gray-400' },
    medium: { label: '보통', color: 'text-yellow-400', dotColor: 'bg-yellow-400' },
    strong: { label: '강하게', color: 'text-red-400', dotColor: 'bg-red-400' },
};

const PRESET_STRUCTURES = {
    '3-act': [
        { name: '1막: 설정', phase: 'setup', percentage: 25 },
        { name: '2막: 대결', phase: 'build', percentage: 50 },
        { name: '3막: 해결', phase: 'resolution', percentage: 25 },
    ],
    '5-act': [
        { name: '도입', phase: 'hook', percentage: 10 },
        { name: '상승', phase: 'build', percentage: 25 },
        { name: '클라이맥스', phase: 'climax', percentage: 20 },
        { name: '하강', phase: 'turn', percentage: 25 },
        { name: '대단원', phase: 'resolution', percentage: 20 },
    ],
    'hook-payoff': [
        { name: '훅', phase: 'hook', percentage: 15 },
        { name: '빌드', phase: 'build', percentage: 55 },
        { name: '페이오프', phase: 'payoff', percentage: 30 },
    ],
};

// =============================================================================
// Helper Functions
// =============================================================================

const generateId = () => `seq_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const parseTime = (timeStr: string): number => {
    const parts = timeStr.split(':');
    if (parts.length === 2) {
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }
    return parseInt(timeStr) || 0;
};

// =============================================================================
// Sequence Card Component
// =============================================================================

const SequenceCard: React.FC<{
    sequence: Sequence;
    index: number;
    totalDuration: number;
    onUpdate: (sequence: Sequence) => void;
    onDelete: () => void;
    onDuplicate: () => void;
    disabled?: boolean;
}> = ({ sequence, index, totalDuration, onUpdate, onDelete, onDuplicate, disabled }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState(sequence.name);

    const phaseConfig = PHASE_CONFIG[sequence.phase] || PHASE_CONFIG.setup;
    const intensityConfig = INTENSITY_CONFIG[sequence.hook_intensity];
    const duration = sequence.t_end - sequence.t_start;
    const widthPercent = totalDuration > 0 ? (duration / totalDuration) * 100 : 0;

    const handleSaveName = () => {
        onUpdate({ ...sequence, name: editName });
        setIsEditing(false);
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`bg-slate-900/60 rounded-xl border border-white/10 overflow-hidden ${disabled ? 'opacity-50' : ''
                }`}
        >
            {/* Header */}
            <div className="flex items-center gap-3 p-4">
                <div className="cursor-grab active:cursor-grabbing text-slate-600 hover:text-slate-400">
                    <GripVertical size={18} />
                </div>

                <div className={`w-8 h-8 rounded-lg ${phaseConfig.bgColor}/20 flex items-center justify-center`}>
                    <span className={`text-sm font-bold ${phaseConfig.color}`}>{index + 1}</span>
                </div>

                <div className="flex-1 min-w-0">
                    {isEditing ? (
                        <div className="flex items-center gap-2">
                            <input
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                className="flex-1 bg-white/5 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-purple-500"
                                autoFocus
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleSaveName();
                                    if (e.key === 'Escape') {
                                        setEditName(sequence.name);
                                        setIsEditing(false);
                                    }
                                }}
                            />
                            <button onClick={handleSaveName} className="p-1 text-emerald-400 hover:text-emerald-300">
                                <Check size={16} />
                            </button>
                            <button onClick={() => { setEditName(sequence.name); setIsEditing(false); }} className="p-1 text-slate-400 hover:text-slate-300">
                                <X size={16} />
                            </button>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2">
                            <span className="font-semibold text-white truncate">{sequence.name}</span>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="p-1 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                                disabled={disabled}
                            >
                                <Edit2 size={12} />
                            </button>
                        </div>
                    )}
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                        <span className={phaseConfig.color}>{phaseConfig.label}</span>
                        <span>•</span>
                        <span>{formatTime(sequence.t_start)} - {formatTime(sequence.t_end)}</span>
                        <span>•</span>
                        <span>{formatTime(duration)}</span>
                    </div>
                </div>

                {sequence.hook_recommended && (
                    <div className="flex items-center gap-1.5 px-2 py-1 bg-red-500/20 rounded-full">
                        <Zap size={12} className="text-red-400" />
                        <span className="text-xs text-red-400">훅</span>
                        <div className={`w-1.5 h-1.5 rounded-full ${intensityConfig.dotColor}`} />
                    </div>
                )}

                <div className="flex items-center gap-1">
                    <button
                        onClick={onDuplicate}
                        disabled={disabled}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-colors"
                    >
                        <Copy size={14} />
                    </button>
                    <button
                        onClick={onDelete}
                        disabled={disabled}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                    >
                        <Trash2 size={14} />
                    </button>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-colors"
                    >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                </div>
            </div>

            {/* Timeline Bar */}
            <div className="px-4 pb-3">
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${phaseConfig.bgColor} rounded-full`}
                        style={{ width: `${widthPercent}%` }}
                    />
                </div>
            </div>

            {/* Expanded Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-white/5 overflow-hidden"
                    >
                        <div className="p-4 space-y-4">
                            {/* Phase Selector */}
                            <div>
                                <label className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">서사 단계</label>
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(PHASE_CONFIG).map(([key, config]) => (
                                        <button
                                            key={key}
                                            onClick={() => onUpdate({ ...sequence, phase: key as any })}
                                            disabled={disabled}
                                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${sequence.phase === key
                                                    ? `${config.bgColor}/30 ${config.color} ring-1 ring-current`
                                                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                                }`}
                                        >
                                            {config.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Time Range */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">시작 시간</label>
                                    <input
                                        type="text"
                                        value={formatTime(sequence.t_start)}
                                        onChange={(e) => onUpdate({ ...sequence, t_start: parseTime(e.target.value) })}
                                        disabled={disabled}
                                        className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                                        placeholder="0:00"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">종료 시간</label>
                                    <input
                                        type="text"
                                        value={formatTime(sequence.t_end)}
                                        onChange={(e) => onUpdate({ ...sequence, t_end: parseTime(e.target.value) })}
                                        disabled={disabled}
                                        className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                                        placeholder="1:00"
                                    />
                                </div>
                            </div>

                            {/* Hook Settings */}
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <label className="text-xs text-slate-500 uppercase tracking-wider">훅 추천</label>
                                    <button
                                        onClick={() => onUpdate({ ...sequence, hook_recommended: !sequence.hook_recommended })}
                                        disabled={disabled}
                                        className={`relative w-10 h-5 rounded-full transition-colors ${sequence.hook_recommended ? 'bg-red-500' : 'bg-slate-700'
                                            }`}
                                    >
                                        <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${sequence.hook_recommended ? 'translate-x-5' : ''
                                            }`} />
                                    </button>
                                </div>

                                {sequence.hook_recommended && (
                                    <div className="flex gap-2">
                                        {(['soft', 'medium', 'strong'] as const).map(intensity => (
                                            <button
                                                key={intensity}
                                                onClick={() => onUpdate({ ...sequence, hook_intensity: intensity })}
                                                disabled={disabled}
                                                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${sequence.hook_intensity === intensity
                                                        ? `${INTENSITY_CONFIG[intensity].color} bg-white/10 ring-1 ring-current`
                                                        : 'text-slate-500 hover:text-slate-300'
                                                    }`}
                                            >
                                                {INTENSITY_CONFIG[intensity].label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// =============================================================================
// Main Component
// =============================================================================

export const SequenceEditor: React.FC<SequenceEditorProps> = ({
    sequences,
    totalDuration,
    onSequencesChange,
    onTotalDurationChange,
    disabled = false,
    className = '',
}) => {
    const [showPresets, setShowPresets] = useState(false);

    // Calculate total time coverage
    const coverage = useMemo(() => {
        if (sequences.length === 0 || totalDuration === 0) return 0;
        const covered = sequences.reduce((acc, seq) => acc + (seq.t_end - seq.t_start), 0);
        return Math.min(100, (covered / totalDuration) * 100);
    }, [sequences, totalDuration]);

    const handleAddSequence = useCallback(() => {
        const lastSeq = sequences[sequences.length - 1];
        const newStart = lastSeq ? lastSeq.t_end : 0;
        const newEnd = Math.min(newStart + 30, totalDuration);

        const newSequence: Sequence = {
            sequence_id: generateId(),
            name: `시퀀스 ${sequences.length + 1}`,
            t_start: newStart,
            t_end: newEnd,
            phase: 'setup',
            hook_recommended: sequences.length === 0, // First sequence gets hook
            hook_intensity: 'medium',
        };

        onSequencesChange([...sequences, newSequence]);
    }, [sequences, totalDuration, onSequencesChange]);

    const handleUpdateSequence = useCallback((index: number, updated: Sequence) => {
        const newSequences = [...sequences];
        newSequences[index] = updated;
        onSequencesChange(newSequences);
    }, [sequences, onSequencesChange]);

    const handleDeleteSequence = useCallback((index: number) => {
        onSequencesChange(sequences.filter((_, i) => i !== index));
    }, [sequences, onSequencesChange]);

    const handleDuplicateSequence = useCallback((index: number) => {
        const seq = sequences[index];
        const duplicated: Sequence = {
            ...seq,
            sequence_id: generateId(),
            name: `${seq.name} (복사본)`,
            t_start: seq.t_end,
            t_end: Math.min(seq.t_end + (seq.t_end - seq.t_start), totalDuration),
        };
        const newSequences = [...sequences];
        newSequences.splice(index + 1, 0, duplicated);
        onSequencesChange(newSequences);
    }, [sequences, totalDuration, onSequencesChange]);

    const handleApplyPreset = useCallback((presetKey: keyof typeof PRESET_STRUCTURES) => {
        const preset = PRESET_STRUCTURES[presetKey];
        let currentTime = 0;

        const newSequences: Sequence[] = preset.map((item, idx) => {
            const duration = (totalDuration * item.percentage) / 100;
            const seq: Sequence = {
                sequence_id: generateId(),
                name: item.name,
                t_start: currentTime,
                t_end: currentTime + duration,
                phase: item.phase as any,
                hook_recommended: idx === 0,
                hook_intensity: 'medium',
            };
            currentTime += duration;
            return seq;
        });

        onSequencesChange(newSequences);
        setShowPresets(false);
    }, [totalDuration, onSequencesChange]);

    const handleReorder = useCallback((newSequences: Sequence[]) => {
        onSequencesChange(newSequences);
    }, [onSequencesChange]);

    return (
        <div className={`bg-slate-900/40 rounded-xl border border-white/10 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-purple-500/20">
                        <Film size={18} className="text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-white">시퀀스 에디터</h3>
                        <p className="text-xs text-slate-500">장편 콘텐츠의 구조를 설계하세요</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* Total Duration */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg">
                        <Clock size={14} className="text-slate-500" />
                        <input
                            type="text"
                            value={formatTime(totalDuration)}
                            onChange={(e) => onTotalDurationChange?.(parseTime(e.target.value))}
                            disabled={disabled || !onTotalDurationChange}
                            className="w-16 bg-transparent text-sm text-white focus:outline-none text-center"
                            placeholder="5:00"
                        />
                    </div>

                    {/* Preset Button */}
                    <div className="relative">
                        <button
                            onClick={() => setShowPresets(!showPresets)}
                            disabled={disabled}
                            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                            <Sparkles size={14} />
                            프리셋
                        </button>

                        <AnimatePresence>
                            {showPresets && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 10 }}
                                    className="absolute right-0 top-full mt-2 w-48 bg-slate-800 rounded-xl border border-white/10 shadow-xl z-10 overflow-hidden"
                                >
                                    {Object.entries(PRESET_STRUCTURES).map(([key, preset]) => (
                                        <button
                                            key={key}
                                            onClick={() => handleApplyPreset(key as any)}
                                            className="w-full px-4 py-3 text-left text-sm hover:bg-white/5 transition-colors border-b border-white/5 last:border-0"
                                        >
                                            <span className="font-medium text-white">
                                                {key === '3-act' ? '3막 구조' : key === '5-act' ? '5막 구조' : '훅-페이오프'}
                                            </span>
                                            <p className="text-xs text-slate-500 mt-0.5">
                                                {preset.length}개 시퀀스
                                            </p>
                                        </button>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>

            {/* Coverage Bar */}
            <div className="px-4 py-3 border-b border-white/5">
                <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-slate-500">시간 커버리지</span>
                    <span className={`text-xs font-medium ${coverage >= 90 ? 'text-emerald-400' : coverage >= 50 ? 'text-yellow-400' : 'text-rose-400'}`}>
                        {coverage.toFixed(0)}%
                    </span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                        className={`h-full rounded-full ${coverage >= 90 ? 'bg-emerald-500' : coverage >= 50 ? 'bg-yellow-500' : 'bg-rose-500'}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${coverage}%` }}
                    />
                </div>
            </div>

            {/* Sequence List */}
            <div className="p-4 space-y-3">
                {sequences.length === 0 ? (
                    <div className="text-center py-12">
                        <Film className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                        <h4 className="text-slate-400 font-medium mb-1">시퀀스가 없습니다</h4>
                        <p className="text-xs text-slate-500 mb-4">프리셋을 선택하거나 직접 추가하세요</p>
                        <button
                            onClick={handleAddSequence}
                            disabled={disabled}
                            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                            <Plus size={16} className="inline mr-1" />
                            시퀀스 추가
                        </button>
                    </div>
                ) : (
                    <>
                        <Reorder.Group
                            values={sequences}
                            onReorder={handleReorder}
                            className="space-y-3"
                        >
                            {sequences.map((sequence, index) => (
                                <Reorder.Item key={sequence.sequence_id} value={sequence}>
                                    <SequenceCard
                                        sequence={sequence}
                                        index={index}
                                        totalDuration={totalDuration}
                                        onUpdate={(updated) => handleUpdateSequence(index, updated)}
                                        onDelete={() => handleDeleteSequence(index)}
                                        onDuplicate={() => handleDuplicateSequence(index)}
                                        disabled={disabled}
                                    />
                                </Reorder.Item>
                            ))}
                        </Reorder.Group>

                        {/* Add Button */}
                        <button
                            onClick={handleAddSequence}
                            disabled={disabled}
                            className="w-full py-3 rounded-xl border-2 border-dashed border-slate-700 hover:border-purple-500/50 text-slate-500 hover:text-purple-400 transition-colors flex items-center justify-center gap-2"
                        >
                            <Plus size={18} />
                            시퀀스 추가
                        </button>
                    </>
                )}
            </div>

            {/* Warning */}
            {coverage < 90 && sequences.length > 0 && (
                <div className="mx-4 mb-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-2">
                    <AlertTriangle size={16} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-yellow-300">
                        총 길이의 {(100 - coverage).toFixed(0)}%가 시퀀스에 할당되지 않았습니다.
                    </p>
                </div>
            )}
        </div>
    );
};

export default SequenceEditor;
