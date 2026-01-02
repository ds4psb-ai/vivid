"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, Send, Square, Terminal, User, Paperclip, X, Image, FileText, Film } from "lucide-react";
import { AgentMessage, AgentToolCall, AgentToolMessage } from "@/types/agent";
import StreamingText from "./StreamingText";
import AgentThinkingIndicator from "./AgentThinkingIndicator";
import ArtifactPreview, { ArtifactPayload } from "./ArtifactPreview";
import { useLanguage } from "@/contexts/LanguageContext";
import { getText } from "@/lib/agentUtils";

interface ChatPanelProps {
  messages: AgentMessage[];
  isStreaming: boolean;
  onSend: (message: string, files?: File[]) => void;
  onStop: () => void;
  className?: string;
  placeholder?: string;
  showTools?: boolean;
  isMinimized?: boolean;
}

const formatJson = (value: unknown) => {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return null;
  }
};

const ToolCallList = ({ toolCalls, label }: { toolCalls: AgentToolCall[]; label: string }) => {
  if (!toolCalls.length) return null;
  return (
    <div className="mt-3 rounded-xl border border-white/10 bg-black/20 p-3">
      <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">{label}</div>
      <div className="mt-2 space-y-2">
        {toolCalls.map((call) => {
          const args = call.arguments && Object.keys(call.arguments).length > 0 ? formatJson(call.arguments) : null;
          return (
            <div key={call.id} className="rounded-lg border border-white/10 bg-white/5 p-2 text-xs text-slate-200">
              <div className="flex items-center gap-2 text-[11px] font-semibold text-slate-100">
                <Terminal className="h-3 w-3 text-sky-300" aria-hidden="true" />
                {call.name}
              </div>
              {args && (
                <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-slate-950/70 p-2 text-[11px] text-slate-300">
                  <code>{args}</code>
                </pre>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const KNOWN_ARTIFACT_TYPES = new Set([
  "storyboard",
  "shot_list",
  "data_table",
  "scene_card",
  "video_summary",
  "audio_overview",
]);

const getArtifactPayload = (output?: Record<string, unknown>): ArtifactPayload | null => {
  if (!output) return null;
  const artifactType = getText(output.artifact_type);
  if (!artifactType || !KNOWN_ARTIFACT_TYPES.has(artifactType)) return null;
  return output as ArtifactPayload;
};

const ToolResultCard = ({
  message,
  artifactPayload,
}: {
  message: AgentToolMessage;
  artifactPayload?: ArtifactPayload | null;
}) => {
  const resolvedArtifact = artifactPayload ?? getArtifactPayload(message.output);
  const output = resolvedArtifact ? null : message.output ? formatJson(message.output) : message.raw || null;
  const hasOutput = output && output.trim().length > 0;
  const isError =
    Boolean(message.error) ||
    message.status === "failed" ||
    message.status === "error" ||
    message.status === "rejected";

  return (
    <div
      className={`rounded-2xl border px-4 py-3 ${isError ? "border-rose-500/40 bg-rose-500/10" : "border-white/10 bg-white/5"
        }`}
    >
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-300">
        <Terminal className="h-4 w-4 text-amber-300" aria-hidden="true" />
        <span className="font-semibold text-slate-100">{message.name}</span>
        {message.status && (
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-[0.2em]">
            {message.status}
          </span>
        )}
        {message.taskId && <span className="text-[11px] text-slate-400">task {message.taskId}</span>}
      </div>
      {message.error && <div className="mt-2 text-xs text-rose-200">{message.error}</div>}
      {resolvedArtifact && (
        <div className="mt-3">
          <ArtifactPreview artifact={resolvedArtifact} />
        </div>
      )}
      {hasOutput && (
        <pre className="mt-3 max-h-72 overflow-auto rounded-xl border border-white/10 bg-slate-950/70 p-3 text-[11px] text-slate-200">
          <code>{output}</code>
        </pre>
      )}
    </div>
  );
};

export default function ChatPanel({
  messages,
  isStreaming,
  onSend,
  onStop,
  className,
  placeholder = "Describe what you want to build or ask for a scene.",
  showTools = true,
  isMinimized = false,
}: ChatPanelProps) {
  const { t } = useLanguage();
  const [draft, setDraft] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const toolErrorFallback = t("studioChatToolError");

  const hasStreamingMessage = useMemo(
    () => messages.some((message) => message.role === "assistant" && message.status === "streaming"),
    [messages]
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: isStreaming ? "auto" : "smooth", block: "end" });
  }, [messages, isStreaming]);

  const handleSend = () => {
    const value = draft.trim();
    if (!value || isStreaming) return;
    onSend(value, attachedFiles.length > 0 ? attachedFiles : undefined);
    setDraft("");
    setAttachedFiles([]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachedFiles(prev => [...prev, ...files].slice(0, 5)); // Max 5 files
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <Image className="w-3.5 h-3.5" />;
    if (file.type.startsWith('video/')) return <Film className="w-3.5 h-3.5" />;
    return <FileText className="w-3.5 h-3.5" />;
  };

  const canSend = draft.trim().length > 0 && !isStreaming;

  return (
    <div className={`flex h-full flex-col rounded-3xl border border-white/10 bg-white/5 ${className ?? ""}`}>
      {/* Header - hidden when minimized */}
      {!isMinimized && (
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div>
            <div className="text-sm font-semibold text-slate-100">{t("studioChatTitle")}</div>
            <div className="text-xs text-slate-400">{t("studioChatSubtitle")}</div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Bot className="h-4 w-4 text-sky-300" aria-hidden="true" />
            {t("studioChatLive")}
          </div>
        </div>
      )}

      {/* Messages - hidden when minimized */}
      {!isMinimized && (
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          {messages.length === 0 && (
            <div className="rounded-2xl border border-dashed border-white/10 bg-slate-900/30 p-6 text-sm text-slate-400">
              {t("studioChatEmpty")}
            </div>
          )}

          {messages.map((message) => {
            if (message.role === "tool") {
              const artifactPayload = getArtifactPayload(message.output);
              if (!showTools) {
                if (artifactPayload) {
                  return (
                    <div key={message.id} className="flex justify-start">
                      <div className="max-w-[90%]">
                        <ArtifactPreview artifact={artifactPayload} />
                      </div>
                    </div>
                  );
                }
                const errorMessage =
                  message.error ||
                  (message.status && ["failed", "error", "rejected"].includes(message.status)
                    ? toolErrorFallback
                    : "");
                if (!errorMessage) return null;
                return (
                  <div key={message.id} className="flex justify-start">
                    <div className="max-w-[90%] rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-xs text-rose-100">
                      {errorMessage}
                    </div>
                  </div>
                );
              }
              return (
                <div key={message.id} className="flex justify-start">
                  <div className="max-w-[90%]">
                    <ToolResultCard message={message} artifactPayload={artifactPayload} />
                  </div>
                </div>
              );
            }

            const isUser = message.role === "user";
            const alignClass = isUser ? "justify-end" : "justify-start";
            const bubbleClass = isUser
              ? "border-sky-500/40 bg-sky-500/10 text-slate-100"
              : "border-white/10 bg-white/5 text-slate-100";

            return (
              <div key={message.id} className={`flex ${alignClass} gap-3`}>
                {!isUser && (
                  <div className="mt-1 h-8 w-8 rounded-full border border-white/10 bg-white/5 p-1 text-sky-300">
                    <Bot className="h-6 w-6" aria-hidden="true" />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-2xl border px-4 py-3 ${bubbleClass}`}>
                  <div className="text-xs uppercase tracking-[0.25em] text-slate-400">
                    {isUser ? t("studioChatYou") : t("studioChatAgent")}
                  </div>
                  <div className="mt-2 text-sm text-slate-100">
                    {message.content ? (
                      isUser ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      ) : (
                        <StreamingText content={message.content} />
                      )
                    ) : message.status === "streaming" ? (
                      <AgentThinkingIndicator className="mt-2" label={t("studioChatThinking")} />
                    ) : null}
                  </div>
                  {showTools && message.role === "assistant" && message.toolCalls && message.toolCalls.length > 0 && (
                    <ToolCallList toolCalls={message.toolCalls} label={t("studioChatToolCalls")} />
                  )}
                  {message.role === "assistant" && message.status === "streaming" && message.content && (
                    <div className="mt-3">
                      <AgentThinkingIndicator label={t("studioChatThinking")} />
                    </div>
                  )}
                </div>
                {isUser && (
                  <div className="mt-1 h-8 w-8 rounded-full border border-white/10 bg-white/5 p-1 text-slate-300">
                    <User className="h-6 w-6" aria-hidden="true" />
                  </div>
                )}
              </div>
            );
          })}

          {isStreaming && !hasStreamingMessage && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <AgentThinkingIndicator label={t("studioChatThinking")} />
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>
      )}

      <div className="border-t border-white/10 px-5 py-3">
        {/* File preview chips */}
        {attachedFiles.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachedFiles.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300"
              >
                {getFileIcon(file)}
                <span className="max-w-[100px] truncate">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="ml-1 text-slate-500 hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3">
          <div className="flex items-start gap-2">
            {/* File attachment button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="shrink-0 rounded-lg border border-white/10 bg-white/5 p-2 text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              title="파일 첨부 (이미지, 문서, 영상)"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,video/*,.pdf,.doc,.docx,.txt,.md"
              onChange={handleFileSelect}
              className="hidden"
            />

            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder={placeholder}
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none min-h-[24px] max-h-[120px]"
            />

            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="shrink-0 inline-flex items-center gap-1.5 rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-100 transition hover:border-rose-500/70 hover:bg-rose-500/20"
              >
                <Square className="h-3.5 w-3.5" aria-hidden="true" />
                {t("studioChatStop")}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                disabled={!canSend}
                className={`shrink-0 inline-flex items-center gap-1.5 rounded-full border border-sky-500/40 bg-sky-500/10 px-3 py-1.5 text-xs font-semibold text-sky-100 transition hover:border-sky-500/70 hover:bg-sky-500/20 ${!canSend ? "cursor-not-allowed opacity-40" : ""
                  }`}
              >
                <Send className="h-3.5 w-3.5" aria-hidden="true" />
                {t("studioChatSend")}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
