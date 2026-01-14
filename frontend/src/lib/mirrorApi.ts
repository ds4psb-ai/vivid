/**
 * mirrorApi - 심연의 거울 API 호출 래퍼
 * 
 * Phase 2: Implementation Plan v2
 * - fetch 패턴 (Server Actions 없음)
 * - SSE EventSource 스트리밍
 * - 기존 BYOK 헤더 지원
 */

import { getBYOKHeaders } from '@/hooks/useBYOK';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8100';

// ============================================================================
// Types
// ============================================================================

export interface MirrorInitRequest {
    mbti?: string;
    blood_type?: string;
    birth_year: number;
    birth_month: number;
    birth_day: number;
    birth_hour?: number;
    gender?: string;
    model?: string;
    // Workflow support
    session_id?: string;
    seed_preset?: Record<string, unknown>;
    prior_outputs?: object[];
}

export interface MirrorChatRequest {
    session_id: string;
    user_message: string;
    persona_data: Record<string, unknown>;
    chat_history: Array<{ role: string; content: string }>;
    current_stage: string;
    model?: string;
}

export interface EvidenceRef {
    ref_id: string;
    source: string;
    content_preview: string;
    dataset_id: string;
    dataset_label: string;
    score: number;
}

export interface MirrorInitResponse {
    success: boolean;
    session_id: string;
    saju: Record<string, string>;
    initial_message: string;
    persona_data: Record<string, unknown>;
    completion_rate: number;
}

export interface MirrorChatResponse {
    success: boolean;
    ai_response: string;
    persona_data: Record<string, unknown>;
    completion_rate: number;
    current_stage: string;
    is_complete: boolean;
    // RAG Protocol
    trace_id: string;
    evidence_refs: EvidenceRef[];
    confidence: number;
    error?: string;
}

export interface MirrorExportResponse {
    success: boolean;
    preset_json: string;
    download_filename: string;
}

// ============================================================================
// API Functions
// ============================================================================

export async function initMirror(
    request: MirrorInitRequest,
    byokKey?: string | null
): Promise<MirrorInitResponse> {
    const response = await fetch(`${API_BASE}/api/dimension/mirror/init`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getBYOKHeaders(byokKey ?? null),
        },
        body: JSON.stringify({
            mbti: request.mbti ?? '',
            blood_type: request.blood_type ?? '',
            birth_year: request.birth_year,
            birth_month: request.birth_month,
            birth_day: request.birth_day,
            birth_hour: request.birth_hour ?? 12,
            gender: request.gender ?? '',
            model: request.model ?? 'gemini-3-flash-preview',
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

export async function chatMirror(
    request: MirrorChatRequest,
    byokKey?: string | null,
    runToken?: string | null  // P3.5: Run-Token 추가
): Promise<MirrorChatResponse> {
    const response = await fetch(`${API_BASE}/api/dimension/mirror/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(runToken ? { Authorization: `Bearer ${runToken}` } : {}),  // P3.5
            ...getBYOKHeaders(byokKey ?? null),
        },
        body: JSON.stringify({
            session_id: request.session_id,
            user_message: request.user_message,
            persona_data: request.persona_data,
            chat_history: request.chat_history,
            current_stage: request.current_stage,
            model: request.model ?? 'gemini-3-flash-preview',
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

export async function exportMirrorPreset(
    personaData: Record<string, unknown>,
    byokKey?: string | null
): Promise<MirrorExportResponse> {
    const response = await fetch(`${API_BASE}/api/dimension/mirror/export`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getBYOKHeaders(byokKey ?? null),
        },
        body: JSON.stringify(personaData),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

/**
 * SSE Streaming chat
 */
export function chatMirrorStream(
    request: MirrorChatRequest,
    byokKey?: string | null,
    runToken?: string | null,  // P3.5: Run-Token 추가
    onMessage?: (data: MirrorChatResponse) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
): () => void {
    const controller = new AbortController();

    (async () => {
        try {
            const response = await fetch(`${API_BASE}/api/dimension/mirror/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(runToken ? { Authorization: `Bearer ${runToken}` } : {}),  // P3.5
                    ...getBYOKHeaders(byokKey ?? null),
                },
                body: JSON.stringify({
                    session_id: request.session_id,
                    user_message: request.user_message,
                    persona_data: request.persona_data,
                    chat_history: request.chat_history,
                    current_stage: request.current_stage,
                    model: request.model ?? 'gemini-3-flash-preview',
                }),
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('No response body');
            }

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            onMessage(data);
                        } catch {
                            // Skip invalid JSON
                        }
                    }
                }
            }

            onComplete();
        } catch (err) {
            if (err instanceof Error && err.name !== 'AbortError') {
                onError(err);
            }
        }
    })();

    return () => controller.abort();
}

// Export default object for convenience
export const mirrorApi = {
    init: initMirror,
    chat: chatMirror,
    export: exportMirrorPreset,
    chatStream: chatMirrorStream,
};

export default mirrorApi;
