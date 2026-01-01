'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Lightbulb, AlertTriangle, Sparkles, X, ChevronRight,
    CheckCircle, XCircle, RefreshCw, Wand2
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export type SuggestionType = 'improvement' | 'warning' | 'opportunity' | 'dna_violation';

export interface ProactiveSuggestion {
    id: string;
    type: SuggestionType;
    title: string;
    message: string;
    targetNodeId?: string;
    suggestedAction?: {
        type: 'modify_node' | 'add_node' | 'connect_nodes' | 'fix_tone';
        params: Record<string, unknown>;
        label: string;
    };
    confidence: number; // 0-1
    dnaField?: string; // 위반된 DNA 필드
    timestamp: number;
}

export interface ProactiveAssistantProps {
    suggestions: ProactiveSuggestion[];
    onDismiss: (id: string) => void;
    onAccept: (suggestion: ProactiveSuggestion) => void;
    onDismissAll: () => void;
    isMinimized?: boolean;
    onToggleMinimize?: () => void;
}

// =============================================================================
// Helper Functions
// =============================================================================

const getTypeIcon = (type: SuggestionType) => {
    switch (type) {
        case 'improvement':
            return <Sparkles size={16} className="text-blue-400" />;
        case 'warning':
            return <AlertTriangle size={16} className="text-amber-400" />;
        case 'opportunity':
            return <Lightbulb size={16} className="text-emerald-400" />;
        case 'dna_violation':
            return <XCircle size={16} className="text-rose-400" />;
        default:
            return <Lightbulb size={16} className="text-gray-400" />;
    }
};

const getTypeBgColor = (type: SuggestionType) => {
    switch (type) {
        case 'improvement':
            return 'bg-blue-500/10 border-blue-500/20';
        case 'warning':
            return 'bg-amber-500/10 border-amber-500/20';
        case 'opportunity':
            return 'bg-emerald-500/10 border-emerald-500/20';
        case 'dna_violation':
            return 'bg-rose-500/10 border-rose-500/20';
        default:
            return 'bg-gray-500/10 border-gray-500/20';
    }
};

const getTypeLabel = (type: SuggestionType) => {
    switch (type) {
        case 'improvement':
            return '개선 제안';
        case 'warning':
            return '주의';
        case 'opportunity':
            return '기회 발견';
        case 'dna_violation':
            return 'DNA 위반';
        default:
            return '제안';
    }
};

// =============================================================================
// Main Component
// =============================================================================

export default function ProactiveAssistant({
    suggestions,
    onDismiss,
    onAccept,
    onDismissAll,
    isMinimized = false,
    onToggleMinimize,
}: ProactiveAssistantProps) {
    const [expandedId, setExpandedId] = useState<string | null>(() =>
        suggestions[0]?.id ?? null
    );

    // 초기 렌더에서 첫 제안을 확장하도록 기본값 설정

    if (suggestions.length === 0) {
        return null;
    }

    // 축소 모드
    if (isMinimized) {
        return (
            <motion.button
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                onClick={onToggleMinimize}
                className="fixed bottom-24 right-6 z-40 flex items-center gap-2 px-4 py-2 rounded-full bg-purple-600/90 backdrop-blur-sm border border-purple-500/30 shadow-lg hover:bg-purple-500/90 transition-colors"
            >
                <Wand2 size={18} className="text-white" />
                <span className="text-white font-medium">{suggestions.length}</span>
                <span className="text-white/70 text-sm">제안</span>
            </motion.button>
        );
    }

    return (
        <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            className="fixed bottom-24 right-6 z-40 w-80 max-h-[60vh] overflow-hidden rounded-2xl bg-gray-900/95 backdrop-blur-xl border border-white/10 shadow-2xl"
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-purple-500/20">
                        <Wand2 size={16} className="text-purple-400" />
                    </div>
                    <span className="text-white font-medium">AI 어시스턴트</span>
                    <span className="px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-xs font-medium">
                        {suggestions.length}
                    </span>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={onDismissAll}
                        className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                        title="모두 닫기"
                    >
                        <RefreshCw size={14} />
                    </button>
                    <button
                        onClick={onToggleMinimize}
                        className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                        title="최소화"
                    >
                        <X size={14} />
                    </button>
                </div>
            </div>

            {/* Suggestions List */}
            <div className="max-h-[50vh] overflow-y-auto p-2 space-y-2">
                <AnimatePresence mode="popLayout">
                    {suggestions.map((suggestion) => (
                        <motion.div
                            key={suggestion.id}
                            layout
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, x: 100 }}
                            className={`rounded-xl border ${getTypeBgColor(suggestion.type)} overflow-hidden`}
                        >
                            {/* Suggestion Header */}
                            <button
                                onClick={() => setExpandedId(expandedId === suggestion.id ? null : suggestion.id)}
                                className="w-full flex items-start gap-3 p-3 text-left hover:bg-white/5 transition-colors"
                            >
                                <div className="pt-0.5">
                                    {getTypeIcon(suggestion.type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-xs font-medium text-gray-400">
                                            {getTypeLabel(suggestion.type)}
                                        </span>
                                        {suggestion.confidence >= 0.8 && (
                                            <span className="text-xs text-emerald-400">높은 확신</span>
                                        )}
                                    </div>
                                    <p className="text-sm text-white font-medium line-clamp-2">
                                        {suggestion.title}
                                    </p>
                                </div>
                                <ChevronRight
                                    size={16}
                                    className={`text-gray-500 transition-transform ${expandedId === suggestion.id ? 'rotate-90' : ''
                                        }`}
                                />
                            </button>

                            {/* Expanded Content */}
                            <AnimatePresence>
                                {expandedId === suggestion.id && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="px-3 pb-3 space-y-3">
                                            <p className="text-sm text-gray-400 pl-7">
                                                {suggestion.message}
                                            </p>

                                            {suggestion.dnaField && (
                                                <div className="pl-7 text-xs text-rose-400">
                                                    DNA 필드: <code className="bg-rose-500/20 px-1 rounded">{suggestion.dnaField}</code>
                                                </div>
                                            )}

                                            <div className="flex items-center gap-2 pl-7">
                                                {suggestion.suggestedAction && (
                                                    <button
                                                        onClick={() => onAccept(suggestion)}
                                                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-colors"
                                                    >
                                                        <CheckCircle size={12} />
                                                        {suggestion.suggestedAction.label}
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => onDismiss(suggestion.id)}
                                                    className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 text-xs font-medium transition-colors"
                                                >
                                                    무시
                                                </button>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
