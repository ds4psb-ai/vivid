import { AgentToolCall } from "@/types/agent";

export type AgentStreamEnvelope = {
  event_id: string;
  session_id: string;
  type: string;
  seq: number;
  ts: string;
  payload: Record<string, unknown>;
};

export const parseSseEvent = (block: string): AgentStreamEnvelope | null => {
  const lines = block.split("\n");
  let data = "";
  for (const line of lines) {
    if (line.startsWith("data:")) {
      const chunk = line.slice(5).trim();
      data = data ? `${data}\n${chunk}` : chunk;
    }
  }
  if (!data) return null;
  try {
    return JSON.parse(data) as AgentStreamEnvelope;
  } catch {
    return null;
  }
};

export const mergeToolCalls = (
  current: AgentToolCall[] | undefined,
  next: AgentToolCall[] | undefined,
): AgentToolCall[] => {
  if (!next || next.length === 0) return current || [];
  if (!current || current.length === 0) return next;
  const seen = new Set(current.map((call) => call.id));
  const merged = [...current];
  next.forEach((call) => {
    if (!seen.has(call.id)) {
      merged.push(call);
      seen.add(call.id);
    }
  });
  return merged;
};
