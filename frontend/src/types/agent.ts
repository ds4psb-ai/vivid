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
