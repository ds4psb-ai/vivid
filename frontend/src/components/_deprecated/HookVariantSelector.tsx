'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap, HelpCircle, Heart, MessageCircle,
    Shuffle, Play, Eye, Wind,
    ChevronDown, FlaskConical,
    Info
} from 'lucide-react';
import type { HookStyle, HookVariant } from '@/types/storyFirst';

// Re-export for backwards compatibility
export type { HookStyle, HookVariant } from '@/types/storyFirst';

// =============================================================================
// Props
// =============================================================================

export interface HookVariantSelectorProps {
    variants: HookVariant[];
    selectedVariantId: string;
    onSelect: (variant: HookVariant) => void;
    onRunABTest?: (variants: HookVariant[]) => void;
    showABTestButton?: boolean;
    disabled?: boolean;
    className?: string;
}

// =============================================================================
// Style Config
// =============================================================================

// Safe full class names for Tailwind JIT
const STYLE_CONFIG: Record<HookStyle, {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    labelKo: string;
    // Colors
    text: string;
    bg: string;
    border: string;
    borderSelected: string;
    ring: string;
    iconBg: string;
    shadow: string; // Custom shadow color
    description: string;
}> = {
    shock: {
        icon: Zap,
        label: 'Shock',
        labelKo: '충격형',
        text: 'text-red-400',
        bg: 'bg-red-500/5',
        border: 'border-red-500/20',
        borderSelected: 'border-red-500',
        ring: 'focus:ring-red-500',
        iconBg: 'bg-red-500/20',
        shadow: 'shadow-red-500/20',
        description: '강렬한 시각적 충격으로 시작',
    },
    curiosity: {
        icon: HelpCircle,
        label: 'Curiosity',
        labelKo: '호기심형',
        text: 'text-purple-400',
        bg: 'bg-purple-500/5',
        border: 'border-purple-500/20',
        borderSelected: 'border-purple-500',
        ring: 'focus:ring-purple-500',
        iconBg: 'bg-purple-500/20',
        shadow: 'shadow-purple-500/20',
        description: '미스터리와 궁금증 유발',
    },
    emotion: {
        icon: Heart,
        label: 'Emotion',
        labelKo: '감정형',
        text: 'text-pink-400',
        bg: 'bg-pink-500/5',
        border: 'border-pink-500/20',
        borderSelected: 'border-pink-500',
        ring: 'focus:ring-pink-500',
        iconBg: 'bg-pink-500/20',
        shadow: 'shadow-pink-500/20',
        description: '감정적 연결로 시작',
    },
    question: {
        icon: MessageCircle,
        label: 'Question',
        labelKo: '의문형',
        text: 'text-blue-400',
        bg: 'bg-blue-500/5',
        border: 'border-blue-500/20',
        borderSelected: 'border-blue-500',
        ring: 'focus:ring-blue-500',
        iconBg: 'bg-blue-500/20',
        shadow: 'shadow-blue-500/20',
        description: '직접적 질문으로 시작',
    },
    paradox: {
        icon: Shuffle,
        label: 'Paradox',
        labelKo: '역설형',
        text: 'text-yellow-400',
        bg: 'bg-yellow-500/5',
        border: 'border-yellow-500/20',
        borderSelected: 'border-yellow-500',
        ring: 'focus:ring-yellow-500',
        iconBg: 'bg-yellow-500/20',
        shadow: 'shadow-yellow-500/20',
        description: '예상을 뒤집는 부조화',
    },
    tease: {
        icon: Eye,
        label: 'Tease',
        labelKo: '티저형',
        text: 'text-cyan-400',
        bg: 'bg-cyan-500/5',
        border: 'border-cyan-500/20',
        borderSelected: 'border-cyan-500',
        ring: 'focus:ring-cyan-500',
        iconBg: 'bg-cyan-500/20',
        shadow: 'shadow-cyan-500/20',
        description: '결과를 먼저 보여주기',
    },
    action: {
        icon: Play,
        label: 'Action',
        labelKo: '액션형',
        text: 'text-orange-400',
        bg: 'bg-orange-500/5',
        border: 'border-orange-500/20',
        borderSelected: 'border-orange-500',
        ring: 'focus:ring-orange-500',
        iconBg: 'bg-orange-500/20',
        shadow: 'shadow-orange-500/20',
        description: '바로 액션으로 돌입',
    },
    calm: {
        icon: Wind,
        label: 'Calm',
        labelKo: '차분형',
        text: 'text-emerald-400',
        bg: 'bg-emerald-500/5',
        border: 'border-emerald-500/20',
        borderSelected: 'border-emerald-500',
        ring: 'focus:ring-emerald-500',
        iconBg: 'bg-emerald-500/20',
        shadow: 'shadow-emerald-500/20',
        description: '여유로운 분위기 조성',
    },
};

const INTENSITY_LABELS = {
    soft: { label: '부드럽게', color: 'text-gray-400', bg: 'bg-gray-500/20' },
    medium: { label: '보통', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    strong: { label: '강하게', color: 'text-orange-400', bg: 'bg-orange-500/20' },
    explosive: { label: '폭발적', color: 'text-red-400', bg: 'bg-red-500/20' },
};

// =============================================================================
// Variant Card
// =============================================================================

const VariantCard: React.FC<{
    variant: HookVariant;
    isSelected: boolean;
    onClick: () => void;
    disabled?: boolean;
    isInABTest?: boolean;
}> = ({ variant, isSelected, onClick, disabled, isInABTest }) => {
    const config = STYLE_CONFIG[variant.style];
    const Icon = config.icon;
    const intensity = INTENSITY_LABELS[variant.intensity];

    return (
        <motion.button
            onClick={onClick}
            disabled={disabled}
            whileHover={disabled ? undefined : { scale: 1.02, y: -2 }}
            whileTap={disabled ? undefined : { scale: 0.98 }}
            className={`
                relative p-4 rounded-xl border transition-all duration-200 w-full text-left
                ${isSelected
                    ? `${config.bg} ${config.borderSelected} ring-1 ring-offset-0 ${config.shadow} shadow-lg z-10`
                    : `bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/20 hover:shadow-md`
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${isInABTest ? 'ring-2 ring-blue-500 border-blue-500' : ''}
            `}
        >
            {/* Control Badge */}
            {variant.isControl && (
                <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-full tracking-wide">
                    대조군
                </span>
            )}

            {/* A/B Test Badge */}
            {isInABTest && !variant.isControl && (
                <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-full tracking-wide flex items-center gap-1">
                    <FlaskConical size={10} />
                    TEST
                </span>
            )}

            <div className="flex flex-col gap-3">
                {/* Header: Icon & Title */}
                <div className="flex items-start gap-3">
                    <div className={`
                        p-2.5 rounded-lg transition-colors
                        ${isSelected ? config.iconBg : 'bg-white/5'}
                    `}>
                        <Icon size={20} className={isSelected ? config.text : 'text-gray-400'} />
                    </div>
                    <div>
                        <div className={`font-bold text-sm flex items-center gap-2 ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                            {config.labelKo}
                            <span className="text-[10px] font-normal text-gray-500 uppercase tracking-wider">
                                {config.label}
                            </span>
                        </div>
                        <div className={`text-xs mt-0.5 ${isSelected ? config.text : 'text-gray-500'}`}>
                            {config.description}
                        </div>
                    </div>
                </div>

                {/* Additional Info: Intensity */}
                <div className="flex items-center gap-2 mt-1">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${intensity.color} bg-white/5`}>
                        {intensity.label}
                    </span>
                    {variant.duration && variant.duration > 0 && (
                        <span className="px-2 py-0.5 rounded text-[10px] text-gray-400 bg-white/5">
                            {variant.duration}초
                        </span>
                    )}
                </div>
            </div>

            {/* Selection/Hover Indicator */}
            <div className={`
                absolute bottom-0 left-0 w-full h-1 rounded-b-xl overflow-hidden transition-all duration-300
                ${isSelected ? 'opacity-100' : 'opacity-0'}
            `}>
                <div className={`w-full h-full bg-gradient-to-r from-transparent via-${config.text.split('-')[1]}-500 to-transparent opacity-50`} />
            </div>
        </motion.button>
    );
};

// =============================================================================
// Main Component
// =============================================================================

export const HookVariantSelector: React.FC<HookVariantSelectorProps> = ({
    variants,
    selectedVariantId,
    onSelect,
    onRunABTest,
    showABTestButton = false,
    disabled = false,
    className = '',
}) => {
    // Local state for A/B testing
    const [isABTestMode, setIsABTestMode] = useState(false);
    const [selectedForAB, setSelectedForAB] = useState<Set<string>>(new Set());

    // Toggle variant for A/B test
    const toggleABSelection = useCallback((variantId: string) => {
        const newSet = new Set(selectedForAB);
        if (newSet.has(variantId)) {
            newSet.delete(variantId);
        } else {
            if (newSet.size >= 4) return; // Max 4 variants
            newSet.add(variantId);
        }
        setSelectedForAB(newSet);
    }, [selectedForAB]);

    // Handle card click
    const handleCardClick = (variant: HookVariant) => {
        if (isABTestMode) {
            toggleABSelection(variant.variantId);
        } else {
            onSelect(variant);
        }
    };

    // Run A/B Test
    const handleRunTest = () => {
        if (onRunABTest && selectedForAB.size >= 2) {
            const selectedVariants = variants.filter(v => selectedForAB.has(v.variantId));
            onRunABTest(selectedVariants);
            setIsABTestMode(false);
            setSelectedForAB(new Set());
        }
    };

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Header / Controls */}
            {showABTestButton && (
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        훅 스타일 선택
                    </h3>

                    {!isABTestMode ? (
                        <button
                            onClick={() => setIsABTestMode(true)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-400 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 hover:border-purple-500/40 rounded-lg transition-all"
                        >
                            <FlaskConical size={14} />
                            A/B 테스트 모드
                        </button>
                    ) : (
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-400">
                                {selectedForAB.size}개 선택됨
                            </span>
                            <button
                                onClick={handleRunTest}
                                disabled={selectedForAB.size < 2}
                                className={`
                                    flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all
                                    ${selectedForAB.size >= 2
                                        ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-900/40'
                                        : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                                    }
                                `}
                            >
                                <Play size={14} className={selectedForAB.size >= 2 ? 'fill-current' : ''} />
                                테스트 시작
                            </button>
                            <button
                                onClick={() => {
                                    setIsABTestMode(false);
                                    setSelectedForAB(new Set());
                                }}
                                className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                            >
                                <ChevronDown size={16} />
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* A/B Test Instructions */}
            <AnimatePresence>
                {isABTestMode && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                    >
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 mb-4 flex gap-3 text-xs text-blue-200">
                            <Info size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
                            <p>
                                테스트하고 싶은 변형을 2개 이상 선택하세요. (최대 4개)<br />
                                <span className="text-blue-400/70">가장 효과적인 훅을 자동으로 찾아냅니다.</span>
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Grid display */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {variants.map((variant) => (
                    <VariantCard
                        key={variant.variantId}
                        variant={variant}
                        isSelected={isABTestMode ? selectedForAB.has(variant.variantId) : selectedVariantId === variant.variantId}
                        onClick={() => handleCardClick(variant)}
                        disabled={disabled}
                        isInABTest={isABTestMode && selectedForAB.has(variant.variantId)}
                    />
                ))}
            </div>
        </div>
    );
};

export default HookVariantSelector;

export const DEFAULT_HOOK_VARIANTS: HookVariant[] = [
    {
        variantId: 'shock_1',
        style: 'shock',
        intensity: 'explosive',
        duration: 3,
        description: '화면 깨지는 효과와 경고음',
        isControl: false,
        promptPrefix: 'Shocking opening sequence',
        promptKeywords: ['shock', 'break', 'alarm']
    },
    {
        variantId: 'curiosity_1',
        style: 'curiosity',
        intensity: 'medium',
        duration: 4,
        description: '블러 처리된 물체 서서히 공개',
        isControl: true,
        promptPrefix: 'Mysterious blurred object reveal',
        promptKeywords: ['blur', 'reveal', 'mystery']
    },
    {
        variantId: 'paradox_1',
        style: 'paradox',
        intensity: 'strong',
        duration: 4,
        description: '우아한 음악 + 혼돈스러운 영상',
        isControl: false,
        promptPrefix: 'Contrasting elegant music with chaos',
        promptKeywords: ['contrast', 'chaos', 'elegant']
    },
    {
        variantId: 'emotion_1',
        style: 'emotion',
        intensity: 'soft',
        duration: 5,
        description: '주인공의 클로즈업 눈물',
        isControl: false,
        promptPrefix: 'Emotional closeup shot',
        promptKeywords: ['tears', 'closeup', 'sadness']
    },
    {
        variantId: 'question_1',
        style: 'question',
        intensity: 'medium',
        duration: 3,
        description: '텍스트: "이것을 믿으시겠습니까?"',
        isControl: false,
        promptPrefix: 'Text overlay question',
        promptKeywords: ['text', 'question', 'believe']
    },
    {
        variantId: 'tease_result',
        style: 'tease',
        intensity: 'strong',
        duration: 2,
        description: '결과물 퀵 플래시',
        isControl: false,
        promptPrefix: 'Quick flash of end result',
        promptKeywords: ['flash', 'result', 'end']
    },
    {
        variantId: 'action_start',
        style: 'action',
        intensity: 'explosive',
        duration: 3,
        description: '추격전 중간부터 시작',
        isControl: false,
        promptPrefix: 'In media res chase sequence',
        promptKeywords: ['chase', 'action', 'run']
    },
    {
        variantId: 'calm_contrast',
        style: 'calm',
        intensity: 'soft',
        duration: 5,
        description: '고요한 풍경 (폭풍 전야)',
        isControl: false,
        promptPrefix: 'Calm landscape before storm',
        promptKeywords: ['landscape', 'calm', 'peaceful']
    },
];
