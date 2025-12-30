'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap, HelpCircle, Heart, MessageCircle,
    Shuffle, Play, Eye, Wind,
    ChevronDown, Check, Sparkles, FlaskConical
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

const STYLE_CONFIG: Record<HookStyle, {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    labelKo: string;
    color: string;
    bgColor: string;
    description: string;
}> = {
    shock: {
        icon: Zap,
        label: 'Shock',
        labelKo: '충격형',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        description: '강렬한 시각적 충격으로 시작',
    },
    curiosity: {
        icon: HelpCircle,
        label: 'Curiosity',
        labelKo: '호기심형',
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/20',
        description: '미스터리와 궁금증 유발',
    },
    emotion: {
        icon: Heart,
        label: 'Emotion',
        labelKo: '감정형',
        color: 'text-pink-400',
        bgColor: 'bg-pink-500/20',
        description: '감정적 연결로 시작',
    },
    question: {
        icon: MessageCircle,
        label: 'Question',
        labelKo: '의문형',
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        description: '직접적 질문으로 시작',
    },
    paradox: {
        icon: Shuffle,
        label: 'Paradox',
        labelKo: '역설형',
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/20',
        description: '예상을 뒤집는 부조화',
    },
    tease: {
        icon: Eye,
        label: 'Tease',
        labelKo: '티저형',
        color: 'text-cyan-400',
        bgColor: 'bg-cyan-500/20',
        description: '결과를 먼저 보여주기',
    },
    action: {
        icon: Play,
        label: 'Action',
        labelKo: '액션형',
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/20',
        description: '바로 액션으로 돌입',
    },
    calm: {
        icon: Wind,
        label: 'Calm',
        labelKo: '차분형',
        color: 'text-emerald-400',
        bgColor: 'bg-emerald-500/20',
        description: '여유로운 분위기 조성',
    },
};

const INTENSITY_LABELS = {
    soft: { label: '부드럽게', color: 'text-gray-400' },
    medium: { label: '보통', color: 'text-yellow-400' },
    strong: { label: '강하게', color: 'text-orange-400' },
    explosive: { label: '폭발적', color: 'text-red-400' },
};

// =============================================================================
// Variant Card
// =============================================================================

const VariantCard: React.FC<{
    variant: HookVariant;
    isSelected: boolean;
    onClick: () => void;
    disabled?: boolean;
}> = ({ variant, isSelected, onClick, disabled }) => {
    const config = STYLE_CONFIG[variant.style];
    const Icon = config.icon;
    const intensity = INTENSITY_LABELS[variant.intensity];

    return (
        <motion.button
            onClick={onClick}
            disabled={disabled}
            whileHover={{ scale: disabled ? 1 : 1.02 }}
            whileTap={{ scale: disabled ? 1 : 0.98 }}
            className={`
                relative p-4 rounded-xl border transition-all w-full text-left
                ${isSelected
                    ? `${config.bgColor} border-${config.color.replace('text-', '')} ring-2 ring-${config.color.replace('text-', '')}/50`
                    : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
        >
            {/* Control Badge */}
            {variant.isControl && (
                <span className="absolute top-2 right-2 px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded-full">
                    대조군
                </span>
            )}

            {/* Selected Check */}
            {isSelected && (
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute top-2 left-2 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center"
                >
                    <Check size={12} className="text-white" />
                </motion.div>
            )}

            {/* Header */}
            <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${config.bgColor}`}>
                    <Icon size={20} className={config.color} />
                </div>
                <div>
                    <div className={`font-bold ${config.color}`}>{config.labelKo}</div>
                    <div className="text-xs text-gray-500">{config.label}</div>
                </div>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-400 mb-2">{config.description}</p>

            {/* Intensity */}
            <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500">강도:</span>
                <span className={intensity.color}>{intensity.label}</span>
            </div>

            {/* Coach Tip */}
            {variant.coachTipKo && (
                <div className="mt-2 p-2 bg-gray-900/50 rounded-lg">
                    <span className="text-xs text-gray-500">💡 </span>
                    <span className="text-xs text-gray-300">{variant.coachTipKo}</span>
                </div>
            )}
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
    showABTestButton = true,
    disabled = false,
    className = '',
}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [abTestVariants, setAbTestVariants] = useState<Set<string>>(new Set());

    const selectedVariant = variants.find(v => v.variantId === selectedVariantId) || variants[0];

    const toggleABTestVariant = useCallback((variantId: string) => {
        setAbTestVariants(prev => {
            const next = new Set(prev);
            if (next.has(variantId)) {
                next.delete(variantId);
            } else {
                if (next.size < 4) { // Max 4 variants in A/B test
                    next.add(variantId);
                }
            }
            return next;
        });
    }, []);

    const handleRunABTest = useCallback(() => {
        if (onRunABTest && abTestVariants.size >= 2) {
            const selectedForTest = variants.filter(v => abTestVariants.has(v.variantId));
            onRunABTest(selectedForTest);
        }
    }, [onRunABTest, abTestVariants, variants]);

    if (!selectedVariant) return null;

    const selectedConfig = STYLE_CONFIG[selectedVariant.style];
    const SelectedIcon = selectedConfig.icon;

    return (
        <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${selectedConfig.bgColor}`}>
                        <SelectedIcon size={20} className={selectedConfig.color} />
                    </div>
                    <div className="text-left">
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-white">훅 스타일</span>
                            <span className={`text-sm ${selectedConfig.color}`}>
                                {selectedConfig.labelKo}
                            </span>
                        </div>
                        <p className="text-xs text-gray-500">
                            {selectedConfig.description}
                        </p>
                    </div>
                </div>
                <ChevronDown
                    size={20}
                    className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                />
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
                        <div className="p-4 pt-0 space-y-4">
                            {/* Variant Grid */}
                            <div className="grid grid-cols-2 gap-3">
                                {variants.map(variant => (
                                    <VariantCard
                                        key={variant.variantId}
                                        variant={variant}
                                        isSelected={variant.variantId === selectedVariantId}
                                        onClick={() => onSelect(variant)}
                                        disabled={disabled}
                                    />
                                ))}
                            </div>

                            {/* A/B Test Section */}
                            {showABTestButton && onRunABTest && (
                                <div className="pt-4 border-t border-gray-800">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <FlaskConical size={16} className="text-purple-400" />
                                            <span className="text-sm font-semibold text-white">A/B 테스트</span>
                                        </div>
                                        <span className="text-xs text-gray-500">
                                            {abTestVariants.size}/4 선택
                                        </span>
                                    </div>

                                    {/* A/B Test Variant Selection */}
                                    <div className="flex flex-wrap gap-2 mb-3">
                                        {variants.map(variant => {
                                            const config = STYLE_CONFIG[variant.style];
                                            const isInTest = abTestVariants.has(variant.variantId);
                                            return (
                                                <button
                                                    key={variant.variantId}
                                                    onClick={() => toggleABTestVariant(variant.variantId)}
                                                    className={`
                                                        px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                                                        ${isInTest
                                                            ? `${config.bgColor} ${config.color} ring-1 ring-current`
                                                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                        }
                                                    `}
                                                >
                                                    {config.labelKo}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    {/* Run Test Button */}
                                    <button
                                        onClick={handleRunABTest}
                                        disabled={abTestVariants.size < 2}
                                        className={`
                                            w-full py-2.5 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition-colors
                                            ${abTestVariants.size >= 2
                                                ? 'bg-purple-600 hover:bg-purple-500 text-white'
                                                : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                                            }
                                        `}
                                    >
                                        <Sparkles size={16} />
                                        {abTestVariants.size >= 2
                                            ? `${abTestVariants.size}개 변형으로 테스트 시작`
                                            : '2개 이상 선택하세요'
                                        }
                                    </button>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// =============================================================================
// Preset Variants (re-exported from unified types)
// =============================================================================

export { DEFAULT_HOOK_VARIANTS } from '@/types/storyFirst';

export default HookVariantSelector;

