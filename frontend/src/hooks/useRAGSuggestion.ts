/**
 * useRAGSuggestion - P1.6: RAG 추천 API 호출 훅
 */
'use client';

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8100';

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

    const fetchSuggestion = useCallback(async (
        query: string,
        historyContext?: string,
    ) => {
        if (!query.trim()) {
            setSuggestion(null);
            return;
        }

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

    const dismissSuggestion = useCallback(() => {
        setSuggestion(null);
    }, []);

    const clearError = useCallback(() => {
        setError(null);
    }, []);

    return {
        suggestion,
        isLoading,
        error,
        fetchSuggestion,
        dismissSuggestion,
        clearError,
    };
}

export default useRAGSuggestion;
