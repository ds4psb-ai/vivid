/**
 * useRAGSuggestion - P1.6/P1.7: RAG 추천 API 호출 훅
 * 
 * P1.7 Features:
 * - MIN_QUERY_LENGTH: 30자 미만 쿼리는 API 호출 건너뛰기
 * - appliedContext: 적용된 컨텍스트 추적
 * - isOverridden: 적용 후 편집 시 override 상태
 * - restoreSuggestion: override 상태에서 복원
 */
'use client';

import { useState, useCallback, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8100';

// P1.7: 30자 미만 쿼리는 추천 건너뛰기
const MIN_QUERY_LENGTH = 30;

// Types (mirror backend response)
export interface EvidenceRef {
    ref_id: string;
    source: string;
    content_preview: string;
    dataset_id: string;
    dataset_label: string;
    score: number;
}

export interface PromptChip {
    label: string;
    insert_text: string;
    chip_type: string;
}

export interface RAGSuggestion {
    has_suggestion: boolean;
    confidence: number;
    confidence_level: 'high' | 'medium' | 'low';
    evidence_refs: EvidenceRef[];
    prompt_chips: PromptChip[];
    suggested_context: string;
    datasets_used: string[];
    total_results: number;
}

interface UseRAGSuggestionOptions {
    appKey: string;
}

export function useRAGSuggestion({ appKey }: UseRAGSuggestionOptions) {
    const [suggestion, setSuggestion] = useState<RAGSuggestion | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // P1.7: Override 상태 관리
    const [appliedContext, setAppliedContext] = useState<string | null>(null);
    const [isOverridden, setIsOverridden] = useState(false);
    const lastQueryRef = useRef<string>('');

    const fetchSuggestion = useCallback(async (
        query: string,
        historyContext?: string,
    ) => {
        // P1.7: 새 쿼리 시 override 상태 초기화
        setIsOverridden(false);
        setAppliedContext(null);

        // P1.7: 30자 미만 쿼리는 건너뛰기
        if (query.trim().length < MIN_QUERY_LENGTH) {
            setSuggestion(null);
            return;
        }

        lastQueryRef.current = query;
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/api/rag/suggest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    app_key: appKey,
                    query: query.trim(),
                    history_context: historyContext,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json() as RAGSuggestion;
            setSuggestion(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'RAG 추천 조회 실패');
            setSuggestion(null);
        } finally {
            setIsLoading(false);
        }
    }, [appKey]);

    // P1.7: dismiss는 현재 suggestion만 숨김 (override와 분리)
    const dismissSuggestion = useCallback(() => {
        setSuggestion(null);
        // override 상태는 변경하지 않음 - 새 입력 시 다시 추천 허용
    }, []);

    // P1.7: 컨텍스트 적용
    const applyContext = useCallback((context: string) => {
        setAppliedContext(context);
        dismissSuggestion();
    }, [dismissSuggestion]);

    // P1.7: 적용 후 편집 감지 → override 설정
    const markAsOverridden = useCallback(() => {
        if (appliedContext) {
            setIsOverridden(true);
        }
    }, [appliedContext]);

    // P1.7: override 상태에서 복원
    const restoreSuggestion = useCallback(async () => {
        setIsOverridden(false);
        setAppliedContext(null);
        // 마지막 쿼리로 다시 fetch
        if (lastQueryRef.current) {
            await fetchSuggestion(lastQueryRef.current);
        }
    }, [fetchSuggestion]);

    const clearError = useCallback(() => {
        setError(null);
    }, []);

    return {
        suggestion,
        isLoading,
        error,
        // P1.7: 확장된 상태
        appliedContext,
        isOverridden,
        // 기존 함수
        fetchSuggestion,
        dismissSuggestion,
        clearError,
        // P1.7: 새 함수
        applyContext,
        markAsOverridden,
        restoreSuggestion,
    };
}

export default useRAGSuggestion;

