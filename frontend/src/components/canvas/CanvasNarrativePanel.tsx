'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BookOpen, ChevronDown, ChevronUp, Sparkles,
    Zap, Target, TrendingUp, Shuffle, RefreshCw,
    Plus, X, Check
} from 'lucide-react';
import HookVariantSelector, {
    HookVariant,
    DEFAULT_HOOK_VARIANTS
} from '@/components/HookVariantSelector';

// =============================================================================
// Types
// =============================================================================

interface NarrativeArc {
    arc_type: string;
    emotion_start: string;
    emotion_peak: string;
    emotion_end: string;
    dissonance_type?: string;
    familiar_element?: string;
    unexpected_element?: string;
}

interface CanvasNarrativePanelProps {
    isEnabled: boolean;
    arc: NarrativeArc | null;
    selectedHookVariant: HookVariant | null;
    onToggleEnabled: () => void;
    onSetDissonance: (familiar: string, unexpected: string, type: string) => void;
    onSetEmotionCurve: (start: string, peak: string, end: string) => void;
    onSelectHookVariant: (variant: HookVariant) => void;
    onRunABTest?: (variants: HookVariant[]) => void;
    className?: string;
}

// =============================================================================
// Presets
// =============================================================================

const EMOTION_PRESETS = [
    { label: '보통', value: 'neutral' },
    { label: '호기심', value: 'curious' },
    { label: '놀람', value: 'shocked' },
    { label: '긴장', value: 'tense' },
    { label: '기쁨', value: 'joyful' },
    { label: '슬픔', value: 'sad' },
    { label: '만족', value: 'satisfied' },
];

const ARC_TYPE_PRESETS = [
    { label: 'Hook-Payoff', value: 'hook-payoff', desc: '훅 → 페이오프' },
    { label: '3막 구조', value: '3-act', desc: '설정 → 대립 → 해결' },
    { label: '순환', value: 'circular', desc: '시작 = 끝' },
];

const DISSONANCE_TYPE_PRESETS = [
    { label: '캐릭터 모순', value: 'character_contradiction', example: 'NBA→치킨집' },
    { label: '계급 대비', value: 'class_contrast', example: '부자↔가난' },
    { label: '상황 역설', value: 'situation_paradox', example: '일상→재난' },
    { label: '톤 전환', value: 'tone_shift', example: '코미디→심각' },
];

// =============================================================================
// Component
// =============================================================================

export const CanvasNarrativePanel: React.FC<CanvasNarrativePanelProps> = ({
    isEnabled,
    arc,
    selectedHookVariant,
    onToggleEnabled,
    onSetDissonance,
    onSetEmotionCurve,
    onSelectHookVariant,
    onRunABTest,
    className = '',
}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [activeTab, setActiveTab] = useState<'dissonance' | 'emotion' | 'hook'>('dissonance');

    // Local state for editing
    const [familiarInput, setFamiliarInput] = useState(arc?.familiar_element || '');
    const [unexpectedInput, setUnexpectedInput] = useState(arc?.unexpected_element || '');
    const [dissonanceType, setDissonanceType] = useState(arc?.dissonance_type || 'character_contradiction');
    const [emotionStart, setEmotionStart] = useState(arc?.emotion_start || 'neutral');
    const [emotionPeak, setEmotionPeak] = useState(arc?.emotion_peak || 'shocked');
    const [emotionEnd, setEmotionEnd] = useState(arc?.emotion_end || 'satisfied');

    const handleApplyDissonance = () => {
        onSetDissonance(familiarInput, unexpectedInput, dissonanceType);
    };

    const handleApplyEmotion = () => {
        onSetEmotionCurve(emotionStart, emotionPeak, emotionEnd);
    };

    return (
        <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${isEnabled ? 'bg-purple-500/20' : 'bg-gray-800'}`}>
                        <BookOpen size={18} className={isEnabled ? 'text-purple-400' : 'text-gray-500'} />
                    </div>
                    <div className="text-left">
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-white text-sm">Story-First</span>
                            {isEnabled && (
                                <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">
                                    활성
                                </span>
                            )}
                        </div>
                        <p className="text-xs text-gray-500">
                            {arc?.dissonance_type
                                ? `부조화: ${arc.familiar_element} ↔ ${arc.unexpected_element}`
                                : '서사 구조 + 훅 스타일'
                            }
                        </p>
                    </div>
                </div>
                {isExpanded ? (
                    <ChevronUp size={18} className="text-gray-400" />
                ) : (
                    <ChevronDown size={18} className="text-gray-400" />
                )}
            </button>

            {/* Expanded Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 space-y-4">
                            {/* Enable Toggle */}
                            <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                <span className="text-sm text-gray-300">Story-First 생성</span>
                                <button
                                    onClick={onToggleEnabled}
                                    className={`
                                        relative w-12 h-6 rounded-full transition-colors
                                        ${isEnabled ? 'bg-purple-600' : 'bg-gray-700'}
                                    `}
                                >
                                    <motion.div
                                        animate={{ x: isEnabled ? 24 : 4 }}
                                        className="absolute top-1 w-4 h-4 bg-white rounded-full"
                                    />
                                </button>
                            </div>

                            {/* Tabs */}
                            <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
                                {[
                                    { id: 'dissonance', label: '부조화', icon: Shuffle },
                                    { id: 'emotion', label: '감정', icon: TrendingUp },
                                    { id: 'hook', label: '훅 스타일', icon: Zap },
                                ].map(tab => {
                                    const Icon = tab.icon;
                                    const isActive = activeTab === tab.id;
                                    return (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                            className={`
                                                flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-medium transition-colors
                                                ${isActive
                                                    ? 'bg-gray-700 text-white'
                                                    : 'text-gray-400 hover:text-gray-300'
                                                }
                                            `}
                                        >
                                            <Icon size={14} />
                                            {tab.label}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Tab Content */}
                            <div className="min-h-[200px]">
                                {/* Dissonance Tab */}
                                {activeTab === 'dissonance' && (
                                    <div className="space-y-3">
                                        <p className="text-xs text-gray-400">
                                            🎭 익숙한 요소 + 낯선 요소 = 바이럴 핵심!
                                        </p>

                                        {/* Dissonance Type */}
                                        <div>
                                            <label className="text-xs text-gray-500 mb-1 block">부조화 유형</label>
                                            <div className="grid grid-cols-2 gap-2">
                                                {DISSONANCE_TYPE_PRESETS.map(preset => (
                                                    <button
                                                        key={preset.value}
                                                        onClick={() => setDissonanceType(preset.value)}
                                                        className={`
                                                            p-2 rounded-lg text-left text-xs transition-colors
                                                            ${dissonanceType === preset.value
                                                                ? 'bg-yellow-500/20 text-yellow-400 ring-1 ring-yellow-500/50'
                                                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                            }
                                                        `}
                                                    >
                                                        <div className="font-medium">{preset.label}</div>
                                                        <div className="text-gray-500 text-[10px]">{preset.example}</div>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Familiar Element */}
                                        <div>
                                            <label className="text-xs text-gray-500 mb-1 block">익숙한 요소</label>
                                            <input
                                                type="text"
                                                value={familiarInput}
                                                onChange={e => setFamiliarInput(e.target.value)}
                                                placeholder="예: NBA 스타, 평범한 아침"
                                                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                            />
                                        </div>

                                        {/* Unexpected Element */}
                                        <div>
                                            <label className="text-xs text-gray-500 mb-1 block">낯선 요소</label>
                                            <input
                                                type="text"
                                                value={unexpectedInput}
                                                onChange={e => setUnexpectedInput(e.target.value)}
                                                placeholder="예: 치킨집 사장, 갑자기 좀비"
                                                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                            />
                                        </div>

                                        {/* Apply Button */}
                                        <button
                                            onClick={handleApplyDissonance}
                                            disabled={!familiarInput || !unexpectedInput}
                                            className={`
                                                w-full py-2 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors
                                                ${familiarInput && unexpectedInput
                                                    ? 'bg-yellow-600 hover:bg-yellow-500 text-white'
                                                    : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                                                }
                                            `}
                                        >
                                            <Check size={16} />
                                            부조화 설정 적용
                                        </button>
                                    </div>
                                )}

                                {/* Emotion Tab */}
                                {activeTab === 'emotion' && (
                                    <div className="space-y-3">
                                        <p className="text-xs text-gray-400">
                                            📈 감정 곡선: 시작 → 피크 → 마무리
                                        </p>

                                        {/* Emotion Start */}
                                        <div>
                                            <label className="text-xs text-gray-500 mb-1 block">시작 감정</label>
                                            <div className="flex flex-wrap gap-1.5">
                                                {EMOTION_PRESETS.map(e => (
                                                    <button
                                                        key={e.value}
                                                        onClick={() => setEmotionStart(e.value)}
                                                        className={`
                                                            px-2.5 py-1 rounded-full text-xs transition-colors
                                                            ${emotionStart === e.value
                                                                ? 'bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/50'
                                                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                            }
                                                        `}
                                                    >
                                                        {e.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Emotion Peak */}
                                        <div>
                                            <label className="text-xs text-gray-500 mb-1 block">피크 감정</label>
                                            <div className="flex flex-wrap gap-1.5">
                                                {EMOTION_PRESETS.map(e => (
                                                    <button
                                                        key={e.value}
                                                        onClick={() => setEmotionPeak(e.value)}
                                                        className={`
                                                            px-2.5 py-1 rounded-full text-xs transition-colors
                                                            ${emotionPeak === e.value
                                                                ? 'bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/50'
                                                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                            }
                                                        `}
                                                    >
                                                        {e.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Emotion End */}
                                        <div>
                                            <label className="text-xs text-gray-500 mb-1 block">마무리 감정</label>
                                            <div className="flex flex-wrap gap-1.5">
                                                {EMOTION_PRESETS.map(e => (
                                                    <button
                                                        key={e.value}
                                                        onClick={() => setEmotionEnd(e.value)}
                                                        className={`
                                                            px-2.5 py-1 rounded-full text-xs transition-colors
                                                            ${emotionEnd === e.value
                                                                ? 'bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/50'
                                                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                            }
                                                        `}
                                                    >
                                                        {e.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Apply Button */}
                                        <button
                                            onClick={handleApplyEmotion}
                                            className="w-full py-2 rounded-lg font-medium text-sm flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                                        >
                                            <Check size={16} />
                                            감정 곡선 적용
                                        </button>
                                    </div>
                                )}

                                {/* Hook Tab */}
                                {activeTab === 'hook' && (
                                    <HookVariantSelector
                                        variants={DEFAULT_HOOK_VARIANTS}
                                        selectedVariantId={selectedHookVariant?.variantId || 'curiosity_1'}
                                        onSelect={onSelectHookVariant}
                                        onRunABTest={onRunABTest}
                                        showABTestButton={!!onRunABTest}
                                    />
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default CanvasNarrativePanel;
