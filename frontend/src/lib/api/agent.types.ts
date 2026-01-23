/**
 * Agent API Types
 * 
 * Types for AI agent sessions, chat, and tool execution.
 */

// Inline to avoid path resolution issues
export interface AgentToolCall {
    id: string;
    name: string;
    arguments?: Record<string, unknown>;
}


export interface AgentMessageRecord {
    message_id: string;
    role: string;
    content: string;
    tool_calls: AgentToolCall[];
    tool_call_id?: string | null;
    name?: string | null;
    created_at: string;
}

export interface AgentArtifactRecord {
    artifact_id: string;
    artifact_type: string;
    payload: Record<string, unknown>;
    version: number;
    created_at: string;
    updated_at: string;
}

export interface AgentSessionResponse {
    session_id: string;
    status: string;
    title?: string | null;
    agent_model?: string | null;
    metadata: Record<string, unknown>;
    created_at: string;
    updated_at: string;
    messages: AgentMessageRecord[];
    artifacts: AgentArtifactRecord[];
}

export interface AgentSessionStatusResponse {
    session_id: string;
    status: string;
    metadata: Record<string, unknown>;
    updated_at: string;
}

export interface AgentChatRequest {
    session_id?: string | null;
    message: string;
    metadata?: Record<string, unknown>;
    model?: string | null;
    attachments?: Record<string, unknown>[];
    page_context?: string | null;
}

export interface AgentDecisionRequest {
    note?: string | null;
    metadata?: Record<string, unknown>;
}
