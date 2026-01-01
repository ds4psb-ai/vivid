'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Sparkles, Film, Palette, Music, Zap, Heart,
    ArrowRight, X, Wand2, Eye, MessageSquare,
    Clapperboard, Lightbulb, Target
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export interface VibePreset {
    id: string;
    title: string;
    subtitle: string;
    tone: string[];
    visualStyle: string;
    emotionalArc: string;
    referenceWorks: string[];
    icon: React.ReactNode;
    gradient: string;
}

export interface VibeBoardProps {
    isOpen: boolean;
    onClose: () => void;
    onVibeSelected: (vibe: VibeInput) => void;
    isProcessing?: boolean;
}

export interface VibeInput {
    type: 'preset' | 'custom';
    presetId?: string;
    customDescription?: string;
    outputType: 'short_drama' | 'ad' | 'animation' | 'music_video';
    targetLengthSec: number;
}

// =============================================================================
// Preset Data
// =============================================================================

const VIBE_PRESETS: VibePreset[] = [
    {
        id: 'noir_seoul',
        title: '80년대 서울 누아르',
        subtitle: '어둡고 축축한 뒷골목의 고독',
        tone: ['어둡고', '축축한', '고독한', '속은 뜨거운'],
        visualStyle: '필름 누아르, 네온 조명, 빗물에 반사되는 불빛',
        emotionalArc: '냉소 → 갈등 → 희망',
        referenceWorks: ['올드보이', '아저씨', '범죄와의 전쟁'],
        icon: <Film size={24} />,
        gradient: 'from-slate-900 via-blue-950 to-slate-800',
    },
    {
        id: 'vibrant_kpop',
        title: 'K-POP 뮤직비디오',
        subtitle: '화려하고 에너지 넘치는 퍼포먼스',
        tone: ['역동적', '화려한', '트렌디한', '중독성 있는'],
        visualStyle: '네온 컬러, 빠른 컷, 댄스 브레이크, LED 무대',
        emotionalArc: '임팩트 → 빌드업 → 폭발',
        referenceWorks: ['NewJeans MV', 'aespa MV', 'BLACKPINK MV'],
        icon: <Music size={24} />,
        gradient: 'from-pink-500 via-purple-500 to-indigo-500',
    },
    {
        id: 'emotional_drama',
        title: '감성 멜로드라마',
        subtitle: '잔잔하지만 깊은 울림의 서사',
        tone: ['서정적', '따뜻한', '쓸쓸한', '희망적'],
        visualStyle: '소프트 라이팅, 파스텔 톤, 긴 테이크, 클로즈업',
        emotionalArc: '일상 → 상실 → 치유 → 성장',
        referenceWorks: ['이별의 정석', '봄날', '디어 마이 프렌즈'],
        icon: <Heart size={24} />,
        gradient: 'from-rose-400 via-orange-300 to-amber-200',
    },
    {
        id: 'comedy_viral',
        title: '바이럴 코미디',
        subtitle: '똑소니 같은 유쾌한 반전',
        tone: ['유쾌한', '위트있는', '예상치 못한', '공감가는'],
        visualStyle: '밝은 조명, 빠른 편집, 리액션 컷, 자막 효과',
        emotionalArc: '설정 → 빌드업 → 반전 → 펀치라인',
        referenceWorks: ['SNL 코리아', '개그콘서트', '코미디빅리그'],
        icon: <Zap size={24} />,
        gradient: 'from-yellow-400 via-orange-400 to-red-400',
    },
    {
        id: 'cinematic_ad',
        title: '시네마틱 광고',
        subtitle: '영화 같은 몰입감의 브랜드 스토리',
        tone: ['프리미엄', '감각적', '스토리텔링', '브랜드 메시지'],
        visualStyle: '와이드 앵글, 슬로모션, 색보정, 드라마틱 조명',
        emotionalArc: '호기심 → 공감 → 감동 → 액션',
        referenceWorks: ['Apple 광고', 'Nike 광고', '삼성 광고'],
        icon: <Clapperboard size={24} />,
        gradient: 'from-gray-800 via-gray-700 to-gray-600',
    },
    {
        id: 'anime_style',
        title: '일본 애니메이션 스타일',
        subtitle: '감정선이 살아있는 2D 세계',
        tone: ['드라마틱', '감성적', '액션', '판타지'],
        visualStyle: '셀 애니메이션, 큰 눈, 스피드 라인, 배경 아트',
        emotionalArc: '평화 → 위기 → 각성 → 승리',
        referenceWorks: ['신카이 마코토', '지브리', '귀멸의 칼날'],
        icon: <Palette size={24} />,
        gradient: 'from-cyan-400 via-blue-500 to-purple-600',
    },
];

const OUTPUT_TYPES = [
    { id: 'short_drama', label: '숏드라마', duration: '60-180초' },
    { id: 'ad', label: '광고', duration: '15-60초' },
    { id: 'animation', label: '애니메이션', duration: '30-120초' },
    { id: 'music_video', label: '뮤직비디오', duration: '60-240초' },
];

// =============================================================================
// Main Component
// =============================================================================

export default function VibeBoard({
    isOpen,
    onClose,
    onVibeSelected,
    isProcessing = false,
}: VibeBoardProps) {
    const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
    const [customVibe, setCustomVibe] = useState('');
    const [isCustomMode, setIsCustomMode] = useState(false);
    const [outputType, setOutputType] = useState<VibeInput['outputType']>('short_drama');
    const [targetLength, setTargetLength] = useState(60);

    const handlePresetSelect = useCallback((presetId: string) => {
        setSelectedPreset(presetId);
        setIsCustomMode(false);
    }, []);

    const handleSubmit = useCallback(() => {
        const vibeInput: VibeInput = isCustomMode
            ? {
                type: 'custom',
                customDescription: customVibe,
                outputType,
                targetLengthSec: targetLength,
            }
            : {
                type: 'preset',
                presetId: selectedPreset!,
                outputType,
                targetLengthSec: targetLength,
            };
        onVibeSelected(vibeInput);
    }, [isCustomMode, customVibe, selectedPreset, outputType, targetLength, onVibeSelected]);

    const canSubmit = isCustomMode ? customVibe.trim().length > 10 : selectedPreset !== null;

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="relative w-full max-w-5xl max-h-[90vh] overflow-hidden rounded-3xl bg-gray-900 border border-white/10 shadow-2xl"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-white/5">
                        <div className="flex items-center gap-3">
                            <div className="p-3 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500">
                                <Wand2 size={24} className="text-white" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white">바이브 코딩</h2>
                                <p className="text-gray-400 text-sm">원하는 분위기를 선택하면 AI 감독이 워크플로우를 설계합니다</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-xl hover:bg-white/10 transition-colors"
                        >
                            <X size={24} className="text-gray-400" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
                        {/* Mode Toggle */}
                        <div className="flex gap-3 mb-6">
                            <button
                                onClick={() => setIsCustomMode(false)}
                                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${!isCustomMode
                                        ? 'bg-purple-600 text-white'
                                        : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                    }`}
                            >
                                <Eye size={18} className="inline mr-2" />
                                프리셋 선택
                            </button>
                            <button
                                onClick={() => setIsCustomMode(true)}
                                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${isCustomMode
                                        ? 'bg-purple-600 text-white'
                                        : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                    }`}
                            >
                                <MessageSquare size={18} className="inline mr-2" />
                                자연어 입력
                            </button>
                        </div>

                        {/* Preset Grid */}
                        {!isCustomMode && (
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                                {VIBE_PRESETS.map((preset) => (
                                    <motion.button
                                        key={preset.id}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => handlePresetSelect(preset.id)}
                                        className={`relative overflow-hidden rounded-2xl p-5 text-left transition-all ${selectedPreset === preset.id
                                                ? 'ring-2 ring-purple-500 ring-offset-2 ring-offset-gray-900'
                                                : 'hover:ring-1 hover:ring-white/20'
                                            }`}
                                    >
                                        <div className={`absolute inset-0 bg-gradient-to-br ${preset.gradient} opacity-80`} />
                                        <div className="relative z-10">
                                            <div className="flex items-center gap-2 mb-3">
                                                <div className="p-2 rounded-xl bg-white/20">
                                                    {preset.icon}
                                                </div>
                                            </div>
                                            <h3 className="text-lg font-bold text-white mb-1">{preset.title}</h3>
                                            <p className="text-sm text-white/70 mb-3">{preset.subtitle}</p>
                                            <div className="flex flex-wrap gap-1">
                                                {preset.tone.slice(0, 3).map((t) => (
                                                    <span
                                                        key={t}
                                                        className="px-2 py-0.5 text-xs rounded-full bg-white/20 text-white"
                                                    >
                                                        {t}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </motion.button>
                                ))}
                            </div>
                        )}

                        {/* Custom Input */}
                        {isCustomMode && (
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    원하는 분위기를 자유롭게 설명해주세요
                                </label>
                                <textarea
                                    value={customVibe}
                                    onChange={(e) => setCustomVibe(e.target.value)}
                                    placeholder="예: 전체적으로 어둡고 축축한 80년대 서울 뒷골목 느낌, 주인공은 고독하지만 속은 뜨거운, 그런 누아르 분위기로 가죠..."
                                    className="w-full h-32 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                                />
                                <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                                    <Lightbulb size={14} />
                                    <span>구체적인 레퍼런스 작품, 톤, 시각적 스타일을 포함하면 더 정확한 결과를 얻을 수 있어요</span>
                                </div>
                            </div>
                        )}

                        {/* Output Type Selection */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-400 mb-3">
                                <Target size={14} className="inline mr-1" />
                                결과물 유형
                            </label>
                            <div className="flex gap-3">
                                {OUTPUT_TYPES.map((type) => (
                                    <button
                                        key={type.id}
                                        onClick={() => setOutputType(type.id as VibeInput['outputType'])}
                                        className={`flex-1 py-3 px-4 rounded-xl text-center transition-all ${outputType === type.id
                                                ? 'bg-purple-600/30 text-purple-300 border border-purple-500/50'
                                                : 'bg-white/5 text-gray-400 border border-transparent hover:bg-white/10'
                                            }`}
                                    >
                                        <div className="font-medium">{type.label}</div>
                                        <div className="text-xs opacity-60">{type.duration}</div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Duration Slider */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-400 mb-3">
                                목표 길이: <span className="text-white font-bold">{targetLength}초</span>
                            </label>
                            <input
                                type="range"
                                min={15}
                                max={240}
                                step={15}
                                value={targetLength}
                                onChange={(e) => setTargetLength(Number(e.target.value))}
                                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-purple-500"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>15초</span>
                                <span>240초</span>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between p-6 border-t border-white/5 bg-gray-900/50">
                        <div className="text-sm text-gray-500">
                            {selectedPreset && !isCustomMode && (
                                <span>
                                    선택됨: <span className="text-purple-400 font-medium">
                                        {VIBE_PRESETS.find(p => p.id === selectedPreset)?.title}
                                    </span>
                                </span>
                            )}
                            {isCustomMode && customVibe.length > 0 && (
                                <span className="text-purple-400">{customVibe.length}자 입력됨</span>
                            )}
                        </div>
                        <button
                            onClick={handleSubmit}
                            disabled={!canSubmit || isProcessing}
                            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${canSubmit && !isProcessing
                                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500'
                                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                }`}
                        >
                            {isProcessing ? (
                                <>
                                    <Sparkles size={18} className="animate-spin" />
                                    AI 감독이 설계 중...
                                </>
                            ) : (
                                <>
                                    <Sparkles size={18} />
                                    워크플로우 생성
                                    <ArrowRight size={18} />
                                </>
                            )}
                        </button>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
