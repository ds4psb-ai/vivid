export type AgentMessageRole = "user" | "assistant" | "tool";

export interface AgentToolCall {
  id: string;
  name: string;
  arguments?: Record<string, unknown>;
}

export interface AgentChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: "streaming" | "complete";
  toolCalls?: AgentToolCall[];
  createdAt?: string;
  attachments?: Record<string, unknown>[];
}

export interface AgentToolMessage {
  id: string;
  role: "tool";
  name: string;
  status?: string;
  output?: Record<string, unknown>;
  error?: string;
  taskId?: string;
  toolCallId?: string;
  raw?: string;
  createdAt?: string;
}

export type AgentMessage = AgentChatMessage | AgentToolMessage;

export interface AgentArtifactItem {
  id: string;
  artifactType: string;
  payload: Record<string, unknown>;
  version?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface AgentSessionState {
  sessionId: string;
  status: string;
  title?: string | null;
  agentModel?: string | null;
  metadata?: Record<string, unknown>;
}

export interface SceneSnapshot {
  sceneId: string;
  title?: string;
  summary?: string;
  style?: Record<string, unknown>;
  updatedAt?: string;
  status?: string;
  source?: string;
}

// === Workflow Event Types (shared across components) ===

/** Node in a workflow structure */
export interface WorkflowNode {
  id: string;
  dimension: string;
  dimension_name: string;
  tool_name: string;
  status: string;
}

/** Workflow start event from execute_workflow */
export interface WorkflowStartEvent {
  topic: string;
  dimensions: string[];
  total_steps: number;
}

/** Workflow step event from agent */
export interface WorkflowStepEvent {
  step: number;
  total_steps: number;
  dimension: string;
  dimension_name: string;
  tool_name: string;
  status?: "start" | "complete" | "error";
  output_preview?: string;
  credit_cost?: number;
}

/** Tool result event from agent */
export interface ToolResultEvent {
  name: string;
  status: string;
  output: Record<string, unknown>;
  arguments?: Record<string, unknown>;
  error?: string;
}

/** Workflow created event from create_workflow (structure only) */
export interface WorkflowCreatedEvent {
  workflow_id: string;
  topic: string;
  dimensions: string[];
  nodes: WorkflowNode[];
}

/** Workflow complete event */
export interface WorkflowCompleteEvent {
  total_credits: number;
  success_count: number;
}
