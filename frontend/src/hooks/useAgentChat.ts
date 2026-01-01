import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AgentArtifactRecord,
  AgentChatRequest,
  AgentMessageRecord,
  AgentSessionResponse,
  AgentSessionStatusResponse,
  api,
} from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";
import { extractScenesFromToolPayload } from "@/lib/agentScene";
import { mergeToolCalls, parseSseEvent } from "@/lib/agentStream";
import type { AgentStreamEnvelope } from "@/lib/agentStream";
import { asRecord, getText, parseJsonRecord } from "@/lib/agentUtils";
import {
  AgentArtifactItem,
  AgentMessage,
  AgentSessionState,
  AgentToolCall,
  AgentToolMessage,
  SceneSnapshot,
} from "@/types/agent";

export interface AgentToolResultEvent {
  name: string;
  output: Record<string, unknown>;
  status?: string;
  toolCallId?: string;
  payload: Record<string, unknown>;
  sessionId?: string;
}

export interface UseAgentChatOptions {
  sessionId?: string | null;
  onToolResult?: (event: AgentToolResultEvent) => void;
  maxMessages?: number;
  maxArtifacts?: number;
}

const toToolMessage = (record: AgentMessageRecord): AgentToolMessage => {
  const parsed = parseJsonRecord(record.content || "");
  const output = parsed ? asRecord(parsed.output) ?? undefined : undefined;
  return {
    id: record.message_id,
    role: "tool",
    name: record.name || "tool",
    status: getText(parsed?.status) || "complete",
    output,
    error: getText(parsed?.error),
    taskId: getText(parsed?.task_id),
    toolCallId: record.tool_call_id ?? undefined,
    raw: record.content || undefined,
    createdAt: record.created_at,
  };
};

const toChatMessage = (record: AgentMessageRecord): AgentMessage => {
  if (record.role === "tool") {
    return toToolMessage(record);
  }
  return {
    id: record.message_id,
    role: record.role === "assistant" ? "assistant" : "user",
    content: record.content || "",
    status: "complete",
    toolCalls: record.tool_calls || [],
    createdAt: record.created_at,
  };
};

const toArtifactItem = (record: AgentArtifactRecord): AgentArtifactItem => ({
  id: record.artifact_id,
  artifactType: record.artifact_type,
  payload: record.payload || {},
  version: record.version,
  createdAt: record.created_at,
  updatedAt: record.updated_at,
});

const toArtifactMessage = (record: AgentArtifactRecord): AgentToolMessage | null => {
  const payload = asRecord(record.payload) ?? {};
  const artifactType = getText(payload.artifact_type) || record.artifact_type;
  if (!artifactType) return null;
  const payloadWithType = payload.artifact_type ? payload : { ...payload, artifact_type: artifactType };
  return {
    id: `artifact-${record.artifact_id}`,
    role: "tool",
    name: artifactType,
    status: "complete",
    output: payloadWithType,
    createdAt: record.created_at,
  };
};

const toTimestamp = (value?: string): number => {
  if (!value) return 0;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
};

const mergeMessagesByTime = (messages: AgentMessage[], additions: AgentMessage[]): AgentMessage[] => {
  const map = new Map<string, AgentMessage>();
  messages.forEach((message) => {
    map.set(message.id, message);
  });
  additions.forEach((message) => {
    if (!map.has(message.id)) {
      map.set(message.id, message);
    }
  });
  return Array.from(map.values()).sort((a, b) => toTimestamp(a.createdAt) - toTimestamp(b.createdAt));
};

const appendMessage = (messages: AgentMessage[], next: AgentMessage): AgentMessage[] => {
  return [...messages, next];
};

const upsertMessageById = (
  messages: AgentMessage[],
  id: string,
  init: AgentMessage,
  update: (message: AgentMessage) => AgentMessage,
): AgentMessage[] => {
  const index = messages.findIndex((message) => message.id === id);
  if (index === -1) {
    return appendMessage(messages, init);
  }
  const next = messages.slice();
  next[index] = update(next[index]);
  return next;
};

const updateMessageById = (
  messages: AgentMessage[],
  id: string,
  update: (message: AgentMessage) => AgentMessage,
): AgentMessage[] => {
  const index = messages.findIndex((message) => message.id === id);
  if (index === -1) {
    return appendMessage(messages, update({
      id,
      role: "assistant",
      content: "",
      status: "streaming",
    }));
  }
  const next = messages.slice();
  next[index] = update(next[index]);
  return next;
};

const getNumber = (value: unknown): number | undefined => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return undefined;
};

const toSessionState = (session: AgentSessionResponse): AgentSessionState => ({
  sessionId: session.session_id,
  status: session.status,
  title: session.title,
  agentModel: session.agent_model,
  metadata: session.metadata,
});

const mergeSceneSnapshot = (
  existing: SceneSnapshot | undefined,
  incoming: SceneSnapshot,
): SceneSnapshot => {
  if (!existing) return incoming;
  const merged: SceneSnapshot = { ...existing };
  (Object.keys(incoming) as Array<keyof SceneSnapshot>).forEach((key) => {
    const value = incoming[key];
    if (value !== undefined) {
      merged[key] = value;
    }
  });
  return merged;
};

const mergeScenes = (artifacts: AgentArtifactItem[]): SceneSnapshot[] => {
  const map = new Map<string, SceneSnapshot>();
  artifacts.forEach((artifact) => {
    const scenes = extractScenesFromToolPayload(artifact.artifactType, artifact.payload);
    scenes.forEach((scene) => {
      const existing = map.get(scene.sceneId);
      map.set(scene.sceneId, mergeSceneSnapshot(existing, scene));
    });
  });
  return Array.from(map.values());
};

const SCENE_TOOL_NAMES = new Set([
  "create_scene",
  "modify_scene",
  "split_scene",
  "merge_scenes",
  "apply_style",
  "generate_video",
  "generate_image",
]);

export const useAgentChat = (options?: UseAgentChatOptions) => {
  const [session, setSession] = useState<AgentSessionState | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [artifacts, setArtifacts] = useState<AgentArtifactItem[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const streamIdRef = useRef(0);
  const artifactIdsRef = useRef<Set<string>>(new Set());
  const toolResultHandlerRef = useRef<UseAgentChatOptions["onToolResult"]>(options?.onToolResult);
  const messageLimit = Math.max(0, options?.maxMessages ?? 200);
  const artifactLimit = Math.max(0, options?.maxArtifacts ?? 200);

  const trimMessages = useCallback(
    (items: AgentMessage[]): AgentMessage[] => {
      if (!messageLimit || items.length <= messageLimit) return items;
      return items.slice(-messageLimit);
    },
    [messageLimit]
  );

  const trimArtifacts = useCallback(
    (items: AgentArtifactItem[]): AgentArtifactItem[] => {
      if (!artifactLimit || items.length <= artifactLimit) {
        artifactIdsRef.current = new Set(items.map((item) => item.id));
        return items;
      }
      const trimmed = items.slice(-artifactLimit);
      artifactIdsRef.current = new Set(trimmed.map((item) => item.id));
      return trimmed;
    },
    [artifactLimit]
  );

  const scenes = useMemo(() => mergeScenes(artifacts), [artifacts]);

  useEffect(() => {
    toolResultHandlerRef.current = options?.onToolResult;
  }, [options?.onToolResult]);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    stop();
    try {
      const data = await api.getAgentSession(sessionId);
      setSession(toSessionState(data));
      const baseMessages = data.messages.map(toChatMessage);
      const artifactMessages = data.artifacts
        .map(toArtifactMessage)
        .filter((message): message is AgentToolMessage => Boolean(message));
      setMessages(trimMessages(mergeMessagesByTime(baseMessages, artifactMessages)));
      const nextArtifacts = data.artifacts.map(toArtifactItem);
      setArtifacts(trimArtifacts(nextArtifacts));
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err, "Failed to load session"));
    }
  }, [stop, trimArtifacts, trimMessages]);

  useEffect(() => {
    if (options?.sessionId) {
      void loadSession(options.sessionId);
    }
  }, [loadSession, options?.sessionId]);

  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
    };
  }, []);

  const resetSession = useCallback(() => {
    stop();
    setSession(null);
    setMessages([]);
    setArtifacts([]);
    artifactIdsRef.current = new Set();
    setError(null);
  }, [stop]);

  const sendMessage = useCallback(async (content: string, extra?: Partial<AgentChatRequest>) => {
    const text = content.trim();
    if (!text) return;
    stop();
    setError(null);
    setIsStreaming(true);
    const streamId = streamIdRef.current + 1;
    streamIdRef.current = streamId;

    const userMessage: AgentMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      status: "complete",
    };
    setMessages((prev) => trimMessages(appendMessage(prev, userMessage)));

    const payload: AgentChatRequest = {
      session_id: extra?.session_id ?? session?.sessionId ?? undefined,
      message: text,
      metadata: extra?.metadata,
      model: extra?.model ?? session?.agentModel ?? undefined,
    };

    const controller = new AbortController();
    abortRef.current = controller;

    const handleStreamEvent = (event: AgentStreamEnvelope) => {
      const payloadData = event.payload || {};
      switch (event.type) {
        case "agent.session": {
          setSession((prev) => ({
            sessionId: event.session_id,
            status: getText(payloadData.status) || prev?.status || "active",
            title: getText(payloadData.title) || prev?.title,
            agentModel: getText(payloadData.agent_model) || prev?.agentModel,
            metadata: prev?.metadata || {},
          }));
          break;
        }
        case "agent.thinking": {
          const messageId = getText(payloadData.message_id);
          if (messageId) {
            setMessages((prev) =>
              trimMessages(
                updateMessageById(prev, messageId, (message) => ({
                  ...message,
                  role: "assistant",
                  content: message.role === "assistant" ? message.content : "",
                  status: "streaming",
                }))
              )
            );
          }
          break;
        }
        case "agent.delta": {
          const messageId = getText(payloadData.message_id);
          const delta = getText(payloadData.delta) || "";
          if (messageId && delta) {
            setMessages((prev) =>
              trimMessages(
                updateMessageById(prev, messageId, (message) => {
                  if (message.role !== "assistant") {
                    return {
                      id: messageId,
                      role: "assistant",
                      content: delta,
                      status: "streaming",
                    };
                  }
                  return {
                    ...message,
                    content: `${message.content}${delta}`,
                    status: "streaming",
                  };
                })
              )
            );
          }
          break;
        }
        case "agent.tool_calls": {
          const messageId = getText(payloadData.message_id);
          const toolCalls = Array.isArray(payloadData.tool_calls)
            ? (payloadData.tool_calls as AgentToolCall[])
            : [];
          if (messageId) {
            setMessages((prev) =>
              trimMessages(
                updateMessageById(prev, messageId, (message) => ({
                  ...message,
                  role: "assistant",
                  toolCalls: mergeToolCalls(
                    message.role === "assistant" ? message.toolCalls : undefined,
                    toolCalls,
                  ),
                }))
              )
            );
          }
          break;
        }
        case "agent.message": {
          const messageId = getText(payloadData.message_id);
          if (messageId) {
            const toolCalls = Array.isArray(payloadData.tool_calls)
              ? (payloadData.tool_calls as AgentToolCall[])
              : [];
            setMessages((prev) =>
              trimMessages(
                updateMessageById(prev, messageId, (message) => ({
                  ...message,
                  role: "assistant",
                  content: getText(payloadData.content) || message.content,
                  status: "complete",
                  toolCalls: mergeToolCalls(
                    message.role === "assistant" ? message.toolCalls : undefined,
                    toolCalls,
                  ),
                }))
              )
            );
          }
          break;
        }
        case "agent.tool_result": {
          const name = getText(payloadData.name) || "tool";
          const output = asRecord(payloadData.output) ?? {};
          const toolMessage: AgentToolMessage = {
            id: `tool-${event.event_id}`,
            role: "tool",
            name,
            status: getText(payloadData.status),
            output,
            error: getText(payloadData.error),
            taskId: getText(payloadData.task_id),
            toolCallId: getText(payloadData.tool_call_id),
          };
          setMessages((prev) => trimMessages(appendMessage(prev, toolMessage)));
          if (SCENE_TOOL_NAMES.has(name)) {
            const artifact: AgentArtifactItem = {
              id: `artifact-${event.event_id}`,
              artifactType: name,
              payload: payloadData,
            };
            setArtifacts((prev) => {
              if (artifactIdsRef.current.has(artifact.id)) {
                return prev;
              }
              const next = [...prev, artifact];
              return trimArtifacts(next);
            });
          }
          toolResultHandlerRef.current?.({
            name,
            output,
            status: getText(payloadData.status),
            toolCallId: getText(payloadData.tool_call_id),
            payload: payloadData,
            sessionId: event.session_id,
          });
          break;
        }
        case "agent.capsule_start":
        case "agent.capsule_progress":
        case "agent.capsule_complete": {
          const toolCallId = getText(payloadData.tool_call_id) || `tool-${event.event_id}`;
          const messageId = `tool-progress-${toolCallId}`;
          const name = getText(payloadData.tool_name) || "run_capsule";
          const status = event.type === "agent.capsule_complete" ? "complete" : "working";
          const progress = getNumber(payloadData.progress);
          const progressOutput: Record<string, unknown> = {};
          const note = getText(payloadData.message);
          if (note) progressOutput.message = note;
          if (progress !== undefined) progressOutput.progress = progress;
          setMessages((prev) =>
            trimMessages(
              upsertMessageById(
                prev,
                messageId,
                {
                  id: messageId,
                  role: "tool",
                  name,
                  status,
                  output: progressOutput,
                  toolCallId,
                },
                (message) => ({
                  ...message,
                  role: "tool",
                  name,
                  status,
                  output: progressOutput,
                  toolCallId,
                })
              )
            )
          );
          break;
        }
        case "agent.analysis_progress": {
          const toolCallId = getText(payloadData.tool_call_id) || `tool-${event.event_id}`;
          const messageId = `analysis-progress-${toolCallId}`;
          const stepName = getText(payloadData.name) || "analyzing";
          const progress = getNumber(payloadData.progress) ?? 0;
          const totalSteps = getNumber(payloadData.total_steps) ?? 5;
          const currentStep = getNumber(payloadData.step) ?? 1;
          const status = progress >= 100 ? "complete" : "working";
          const progressOutput: Record<string, unknown> = {
            step: currentStep,
            name: stepName,
            progress,
            total_steps: totalSteps,
            message: `Step ${currentStep}/${totalSteps}: ${stepName} (${progress}%)`,
          };
          setMessages((prev) =>
            trimMessages(
              upsertMessageById(
                prev,
                messageId,
                {
                  id: messageId,
                  role: "tool",
                  name: "analyze_sources",
                  status,
                  output: progressOutput,
                  toolCallId,
                },
                (message) => ({
                  ...message,
                  role: "tool",
                  name: "analyze_sources",
                  status,
                  output: progressOutput,
                  toolCallId,
                })
              )
            )
          );
          break;
        }
        case "agent.artifact_update": {
          const artifactId = getText(payloadData.artifact_id) || `artifact-${event.event_id}`;
          const payload = asRecord(payloadData.payload) ?? {};
          const artifactType = getText(payload.artifact_type) || getText(payloadData.artifact_type) || "artifact";
          const payloadWithType = payload.artifact_type ? payload : { ...payload, artifact_type: artifactType };
          const artifact: AgentArtifactItem = {
            id: artifactId,
            artifactType,
            payload: payloadWithType,
            version: getNumber(payloadData.version),
            createdAt: getText(payloadData.created_at),
            updatedAt: getText(payloadData.updated_at),
          };
          setArtifacts((prev) => {
            const index = prev.findIndex((item) => item.id === artifact.id);
            if (index === -1) {
              const next = [...prev, artifact];
              return trimArtifacts(next);
            }
            const next = prev.slice();
            next[index] = { ...next[index], ...artifact };
            return trimArtifacts(next);
          });
          const artifactMessage: AgentToolMessage = {
            id: `artifact-${artifactId}`,
            role: "tool",
            name: artifactType,
            status: "complete",
            output: payloadWithType,
            createdAt: artifact.createdAt,
          };
          setMessages((prev) =>
            trimMessages(
              upsertMessageById(prev, artifactMessage.id, artifactMessage, () => artifactMessage)
            )
          );
          break;
        }
        default:
          break;
      }
    };

    try {
      const response = await api.openAgentChatStream(payload, controller.signal);
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const message = (detail && typeof detail.detail === "string" && detail.detail.trim())
          ? detail.detail
          : `Chat request failed (${response.status})`;
        setError(message);
        return;
      }

      if (!response.body) {
        setError("Chat stream unavailable");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (value) {
          buffer += decoder.decode(value, { stream: true });
        }
        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          const event = parseSseEvent(block);
          if (event) {
            handleStreamEvent(event);
          }
          boundary = buffer.indexOf("\n\n");
        }
        if (done) break;
      }

      buffer += decoder.decode();
      const tailEvent = buffer.trim() ? parseSseEvent(buffer) : null;
      if (tailEvent) {
        handleStreamEvent(tailEvent);
      }
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setError(normalizeApiError(err, "Streaming failed"));
      }
    } finally {
      if (streamIdRef.current === streamId) {
        setIsStreaming(false);
        abortRef.current = null;
      }
    }
  }, [session?.sessionId, session?.agentModel, stop, trimArtifacts, trimMessages]);

  const approveSession = useCallback(
    async (sessionId: string, note?: string): Promise<AgentSessionStatusResponse | null> => {
      try {
        const result = await api.approveAgentSession(sessionId, note ? { note } : {});
        setSession((prev) => (prev ? { ...prev, status: result.status, metadata: result.metadata } : prev));
        return result;
      } catch (err) {
        setError(normalizeApiError(err, "Failed to approve session"));
        return null;
      }
    },
    []
  );

  const rejectSession = useCallback(
    async (sessionId: string, note?: string): Promise<AgentSessionStatusResponse | null> => {
      try {
        const result = await api.rejectAgentSession(sessionId, note ? { note } : {});
        setSession((prev) => (prev ? { ...prev, status: result.status, metadata: result.metadata } : prev));
        return result;
      } catch (err) {
        setError(normalizeApiError(err, "Failed to update session"));
        return null;
      }
    },
    []
  );

  return {
    session,
    messages,
    artifacts,
    scenes,
    isStreaming,
    error,
    loadSession,
    resetSession,
    sendMessage,
    stop,
    approveSession,
    rejectSession,
  };
};
