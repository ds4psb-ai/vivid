/**
 * RAGSuggestionCard - P1.6: RAG 기반 추천 카드 컴포넌트
 * 
 * 2025-2026 UX Best Practices:
 * - 자동 적용 없음 - 사용자가 명시적으로 "적용" 클릭
 * - 신뢰도 배지 (색상 코드: 녹색/노랑/빨강)
 * - 원숫자 대신 라벨 ("높음", "보통", "낮음")
 * - 근거(evidence) 미리보기
 * - Prompt chips로 빠른 삽입
 */
'use client';

import React, { useState } from 'react';

// Types
interface EvidenceRef {
    ref_id: string;
    source: string;
    content_preview: string;
    dataset_id: string;
    dataset_label: string;
    score: number;
}

interface PromptChip {
    label: string;
    insert_text: string;
    chip_type: string;
}

interface RAGSuggestion {
    has_suggestion: boolean;
    confidence: number;
    confidence_level: 'high' | 'medium' | 'low';
    evidence_refs: EvidenceRef[];
    prompt_chips: PromptChip[];
    suggested_context: string;
    datasets_used: string[];
    total_results: number;
}

interface RAGSuggestionCardProps {
    suggestion: RAGSuggestion | null;
    onApply?: (context: string) => void;
    onDismiss?: () => void;
    onChipClick?: (insertText: string) => void;
    isLoading?: boolean;
}

// Confidence Level 배지 설정
const CONFIDENCE_CONFIG = {
    high: {
        label: '높음',
        labelEn: 'High',
        color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
        borderColor: 'border-green-300 dark:border-green-700',
        icon: '✓',
    },
    medium: {
        label: '보통',
        labelEn: 'Medium',
        color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
        borderColor: 'border-yellow-300 dark:border-yellow-700',
        icon: '~',
    },
    low: {
        label: '낮음',
        labelEn: 'Low',
        color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
        borderColor: 'border-red-300 dark:border-red-700',
        icon: '?',
    },
};

export function RAGSuggestionCard({
    suggestion,
    onApply,
    onDismiss,
    onChipClick,
    isLoading = false,
}: RAGSuggestionCardProps) {
    const [expandedEvidence, setExpandedEvidence] = useState(false);

    // 로딩 중
    if (isLoading) {
        return (
            <div className="animate-pulse rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
            </div>
        );
    }

    // 추천 없음
    if (!suggestion || !suggestion.has_suggestion) {
        return null;
    }

    const config = CONFIDENCE_CONFIG[suggestion.confidence_level];

    return (
        <div
            className={`rounded-lg border-2 ${config.borderColor} bg-white dark:bg-gray-900 shadow-sm overflow-hidden`}
        >
            {/* 헤더: 신뢰도 배지 + 제목 */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800">
                <div className="flex items-center gap-2">
                    <span className="text-lg">💡</span>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                        RAG 추천
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                        ({suggestion.total_results}개 결과)
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    {/* 신뢰도 배지 */}
                    <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
                    >
                        <span>{config.icon}</span>
                        {config.label}
                    </span>
                    {/* 닫기 버튼 */}
                    {onDismiss && (
                        <button
                            onClick={onDismiss}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                            aria-label="닫기"
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>

            {/* Prompt Chips */}
            {suggestion.prompt_chips.length > 0 && (
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                        빠른 삽입
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {suggestion.prompt_chips.map((chip, idx) => (
                            <button
                                key={idx}
                                onClick={() => onChipClick?.(chip.insert_text)}
                                className={`px-3 py-1.5 rounded-full text-sm border transition-all hover:scale-105 ${chip.chip_type === 'context'
                                        ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
                                        : 'bg-gray-50 border-gray-200 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300'
                                    }`}
                            >
                                {chip.label}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Evidence 미리보기 */}
            {suggestion.evidence_refs.length > 0 && (
                <div className="px-4 py-3">
                    <button
                        onClick={() => setExpandedEvidence(!expandedEvidence)}
                        className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-2"
                    >
                        <span>{expandedEvidence ? '▼' : '▶'}</span>
                        <span>왜 추천? ({suggestion.evidence_refs.length}개 근거)</span>
                    </button>

                    {expandedEvidence && (
                        <div className="space-y-2 ml-3">
                            {suggestion.evidence_refs.slice(0, 3).map((evidence, idx) => (
                                <div
                                    key={idx}
                                    className="text-sm p-2 rounded bg-gray-50 dark:bg-gray-800"
                                >
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                                            {evidence.dataset_label}
                                        </span>
                                        <span className="text-xs text-gray-400">
                                            score: {(evidence.score * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <p className="text-gray-700 dark:text-gray-300 line-clamp-2">
                                        {evidence.content_preview}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* 액션 버튼 */}
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-100 dark:border-gray-700 flex justify-end gap-2">
                {onDismiss && (
                    <button
                        onClick={onDismiss}
                        className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                    >
                        무시
                    </button>
                )}
                {onApply && suggestion.suggested_context && (
                    <button
                        onClick={() => onApply(suggestion.suggested_context)}
                        className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                    >
                        적용하기
                    </button>
                )}
            </div>
        </div>
    );
}

export default RAGSuggestionCard;
