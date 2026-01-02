'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BookOpen, ChevronDown, Sparkles,
    Zap, TrendingUp, Shuffle,
    Check
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
    defaultExpanded?: boolean;
}

// =============================================================================
// Presets
// =============================================================================

const EMOTION_PRESETS = [
    { label: '🙂 보통', value: 'neutral', color: 'bg-gray-500/20 text-gray-300 border-gray-500/30' },
    { label: '🧐 호기심', value: 'curious', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
    { label: '😱 놀람', value: 'shocked', color: 'bg-red-500/20 text-red-300 border-red-500/30' },
    { label: '😰 긴장', value: 'tense', color: 'bg-orange-500/20 text-orange-300 border-orange-500/30' },
    { label: '😆 기쁨', value: 'joyful', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' },
    { label: '😢 슬픔', value: 'sad', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
    { label: '😌 만족', value: 'satisfied', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
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
    defaultExpanded = true,
}) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);
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
        <motion.div
            initial={false}
            animate={{
                borderColor: isExpanded ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.05)',
                backgroundColor: isExpanded ? 'rgba(10, 10, 12, 0.95)' : 'rgba(10, 10, 12, 0.6)'
            }}
            className={`
                rounded-xl border backdrop-blur-xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300
                ${className}
            `}
        >
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-5 py-4 flex items-center justify-between group"
            >
                <div className="flex items-center gap-4">
                    <div className={`
                        p-2.5 rounded-xl transition-all duration-300
                        ${isEnabled
                            ? 'bg-purple-500/20 text-purple-400 shadow-[0_0_15px_-3px_rgba(168,85,247,0.3)]'
                            : 'bg-white/5 text-gray-500 group-hover:bg-white/10'
                        }
                    `}>
                        <BookOpen size={20} />
                    </div>
                    <div className="text-left">
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-white text-[15px] tracking-tight">Story-First DNA</span>
                            {isEnabled && (
                                <span className="flex h-2 w-2 relative">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                                </span>
                            )}
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5 group-hover:text-gray-400 transition-colors">
                            {arc?.dissonance_type
                                ? `${arc.familiar_element} ↔ ${arc.unexpected_element}`
                                : '내러티브 구조 및 훅 설계'
                            }
                        </p>
                    </div>
                </div>
                <div className={`
                    p-1.5 rounded-lg text-gray-500 transition-all duration-300
                    ${isExpanded ? 'bg-white/10 rotate-180 text-white' : 'group-hover:bg-white/5 group-hover:text-gray-300'}
                `}>
                    <ChevronDown size={18} />
                </div>
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
                        <div className="px-5 pb-5 space-y-6">
                            {/* Divider with Enable Toggle */}
                            <div className="h-px bg-white/5 flex items-center justify-center gap-4 my-2">
                                <div className="bg-[#0A0A0C] px-3 flex items-center justify-between w-full max-w-sm rounded-full border border-white/5 py-1.5">
                                    <span className="text-xs font-medium text-gray-400">Story-First 모드</span>
                                    <button
                                        onClick={onToggleEnabled}
                                        className={`
                                            relative w-10 h-5 rounded-full transition-all duration-300
                                            ${isEnabled ? 'bg-purple-600 shadow-[0_0_10px_rgba(147,51,234,0.4)]' : 'bg-gray-700'}
                                        `}
                                    >
                                        <motion.div
                                            animate={{ x: isEnabled ? 20 : 2 }}
                                            className="absolute top-[2px] w-4 h-4 bg-white rounded-full shadow-sm"
                                        />
                                    </button>
                                </div>
                            </div>

                            {/* Tabs */}
                            <div className="flex gap-1 p-1 bg-black/40 rounded-xl border border-white/5">
                                {[
                                    { id: 'dissonance', label: '부조화 설계', icon: Shuffle },
                                    { id: 'emotion', label: '감정 곡선', icon: TrendingUp },
                                    { id: 'hook', label: '훅 스타일', icon: Zap },
                                ].map(tab => {
                                    const Icon = tab.icon;
                                    const isActive = activeTab === tab.id;
                                    return (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                            className={`
                                                relative flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 z-10
                                                ${isActive ? 'text-white' : 'text-gray-500 hover:text-gray-300'}
                                            `}
                                        >
                                            {isActive && (
                                                <motion.div
                                                    layoutId="activeTabBg"
                                                    className="absolute inset-0 bg-white/10 rounded-lg shadow-sm border border-white/5"
                                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                                />
                                            )}
                                            <Icon size={14} className="relative z-10" />
                                            <span className="relative z-10">{tab.label}</span>
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Tab Content */}
                            <motion.div
                                key={activeTab}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3 }}
                                className="min-h-[200px]"
                            >
                                {/* Dissonance Tab */}
                                {activeTab === 'dissonance' && (
                                    <div className="space-y-4">
                                        <div className="bg-yellow-500/5 border border-yellow-500/10 rounded-xl p-3 flex gap-3">
                                            <div className="p-2 bg-yellow-500/10 rounded-full h-fit">
                                                <Sparkles size={14} className="text-yellow-400" />
                                            </div>
                                            <div>
                                                <h4 className="text-xs font-bold text-yellow-500 mb-0.5">바이럴 법칙 #1: 인지적 부조화</h4>
                                                <p className="text-[11px] text-yellow-200/60 leading-relaxed">
                                                    뇌는 예측 불가능한 정보에 더 강하게 반응합니다. 익숙한 상황에 낯선 요소를 충돌시키세요.
                                                </p>
                                            </div>
                                        </div>

                                        {/* Dissonance Type Chips */}
                                        <div className="grid grid-cols-2 gap-2">
                                            {DISSONANCE_TYPE_PRESETS.map(preset => (
                                                <button
                                                    key={preset.value}
                                                    onClick={() => setDissonanceType(preset.value)}
                                                    className={`
                                                        p-3 rounded-xl text-left transition-all duration-200 border
                                                        ${dissonanceType === preset.value
                                                            ? 'bg-white/10 border-white/20 ring-1 ring-white/20'
                                                            : 'bg-white/5 border-transparent hover:bg-white/10 hover:border-white/5'
                                                        }
                                                    `}
                                                >
                                                    <div className="text-xs font-medium text-white mb-1">{preset.label}</div>
                                                    <div className="text-[10px] text-gray-500">{preset.example}</div>
                                                </button>
                                            ))}
                                        </div>

                                        <div className="grid gap-4 pt-2">
                                            {/* Familiar Element */}
                                            <div className="space-y-1.5">
                                                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider ml-1">익숙한 요소 (The Anchor)</label>
                                                <input
                                                    type="text"
                                                    value={familiarInput}
                                                    onChange={e => setFamiliarInput(e.target.value)}
                                                    placeholder="예: 평범한 지하철, 조용한 도서관"
                                                    className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all font-light"
                                                />
                                            </div>

                                            {/* Unexpected Element */}
                                            <div className="space-y-1.5">
                                                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider ml-1">낯선 요소 (The Twist)</label>
                                                <input
                                                    type="text"
                                                    value={unexpectedInput}
                                                    onChange={e => setUnexpectedInput(e.target.value)}
                                                    placeholder="예: 갑자기 춤추는 승객, 록밴드 공연"
                                                    className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-sm text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all font-light"
                                                />
                                            </div>
                                        </div>

                                        {/* Apply Button */}
                                        <button
                                            onClick={handleApplyDissonance}
                                            disabled={!familiarInput || !unexpectedInput}
                                            className={`
                                                w-full py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all mt-2
                                                ${familiarInput && unexpectedInput
                                                    ? 'bg-gradient-to-r from-yellow-600 to-orange-600 text-white shadow-lg shadow-orange-900/40 hover:scale-[1.02]'
                                                    : 'bg-white/5 text-gray-500 cursor-not-allowed'
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
                                    <div className="space-y-6">
                                        <div className="bg-blue-500/5 border border-blue-500/10 rounded-xl p-3 flex gap-3">
                                            <div className="p-2 bg-blue-500/10 rounded-full h-fit">
                                                <TrendingUp size={14} className="text-blue-400" />
                                            </div>
                                            <div>
                                                <h4 className="text-xs font-bold text-blue-500 mb-0.5">바이럴 법칙 #2: 감정의 롤러코스터</h4>
                                                <p className="text-[11px] text-blue-200/60 leading-relaxed">
                                                    단조로운 감정선은 이탈을 부릅니다. 감정의 높낮이를 극적으로 설계하세요.
                                                </p>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            {/* Emotion Start */}
                                            <div>
                                                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 block ml-1">시작 (Start)</label>
                                                <div className="flex flex-wrap gap-2">
                                                    {EMOTION_PRESETS.map(e => (
                                                        <button
                                                            key={e.value}
                                                            onClick={() => setEmotionStart(e.value)}
                                                            className={`
                                                                px-3 py-1.5 rounded-lg text-xs transition-all border
                                                                ${emotionStart === e.value
                                                                    ? `${e.color} shadow-sm ring-1 ring-white/10`
                                                                    : 'bg-white/5 text-gray-500 border-transparent hover:bg-white/10'
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
                                                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 block ml-1">절정 (Peak)</label>
                                                <div className="flex flex-wrap gap-2">
                                                    {EMOTION_PRESETS.map(e => (
                                                        <button
                                                            key={e.value}
                                                            onClick={() => setEmotionPeak(e.value)}
                                                            className={`
                                                                px-3 py-1.5 rounded-lg text-xs transition-all border
                                                                ${emotionPeak === e.value
                                                                    ? `${e.color} shadow-sm ring-1 ring-white/10`
                                                                    : 'bg-white/5 text-gray-500 border-transparent hover:bg-white/10'
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
                                                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 block ml-1">결말 (End)</label>
                                                <div className="flex flex-wrap gap-2">
                                                    {EMOTION_PRESETS.map(e => (
                                                        <button
                                                            key={e.value}
                                                            onClick={() => setEmotionEnd(e.value)}
                                                            className={`
                                                                px-3 py-1.5 rounded-lg text-xs transition-all border
                                                                ${emotionEnd === e.value
                                                                    ? `${e.color} shadow-sm ring-1 ring-white/10`
                                                                    : 'bg-white/5 text-gray-500 border-transparent hover:bg-white/10'
                                                                }
                                                            `}
                                                        >
                                                            {e.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Apply Button */}
                                        <button
                                            onClick={handleApplyEmotion}
                                            className="w-full py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:scale-[1.02] text-white shadow-lg shadow-blue-900/40 transition-all mt-2"
                                        >
                                            <Check size={16} />
                                            감정 곡선 적용
                                        </button>
                                    </div>
                                )}

                                {/* Hook Tab */}
                                {activeTab === 'hook' && (
                                    <div className="space-y-4">
                                        <div className="bg-purple-500/5 border border-purple-500/10 rounded-xl p-3 flex gap-3 mb-2">
                                            <div className="p-2 bg-purple-500/10 rounded-full h-fit">
                                                <Zap size={14} className="text-purple-400" />
                                            </div>
                                            <div>
                                                <h4 className="text-xs font-bold text-purple-500 mb-0.5">바이럴 법칙 #3: 3초 훅</h4>
                                                <p className="text-[11px] text-purple-200/60 leading-relaxed">
                                                    시청자의 60%는 3초 안에 이탈합니다. 가장 강력한 훅 스타일을 선택하거나 A/B 테스트하세요.
                                                </p>
                                            </div>
                                        </div>

                                        <HookVariantSelector
                                            variants={DEFAULT_HOOK_VARIANTS}
                                            selectedVariantId={selectedHookVariant?.variantId || 'curiosity_1'}
                                            onSelect={onSelectHookVariant}
                                            onRunABTest={onRunABTest}
                                            showABTestButton={!!onRunABTest}
                                        />
                                    </div>
                                )}
                            </motion.div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default CanvasNarrativePanel;
