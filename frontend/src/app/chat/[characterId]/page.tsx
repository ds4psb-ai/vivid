"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Send, ArrowLeft, Settings, RefreshCw, MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";

// Types
interface IPCharacter {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  thumbnail_url: string | null;
  chat_enabled: boolean;
  chat_model_default: string;
}

interface ChatSession {
  id: string;
  ip_id: string;
  ip_name: string;
  ip_thumbnail: string | null;
  title: string | null;
  scenario_branch: string | null;
  model_preference: string;
  total_messages: number;
  total_credits_spent: number;
  created_at: string;
  last_message_at: string | null;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  media_urls: string[];
  tokens_used: number;
  credits_charged: number;
  model_used: string | null;
  latency_ms: number;
  is_regenerated: boolean;
  created_at: string;
}

interface Scenario {
  scenario_key: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  character_mood: string;
  is_default: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const characterId = params.characterId as string;
  const sessionIdParam = searchParams.get("session");

  // State
  const [character, setCharacter] = useState<IPCharacter | null>(null);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [modelPreference, setModelPreference] = useState("flash");

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Fetch character info
  useEffect(() => {
    async function fetchCharacter() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/chat/ips/${characterId}`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error("Failed to fetch character");
        const data = await res.json();
        setCharacter(data);
        setModelPreference(data.chat_model_default || "flash");
      } catch (err) {
        setError("캐릭터 정보를 불러오지 못했습니다");
      }
    }

    if (characterId) {
      fetchCharacter();
    }
  }, [characterId]);

  // Fetch or create session
  useEffect(() => {
    async function initSession() {
      try {
        if (sessionIdParam) {
          // Fetch existing session
          const res = await fetch(`${API_BASE}/api/v1/chat/sessions/${sessionIdParam}`, {
            credentials: "include",
          });
          if (res.ok) {
            const data = await res.json();
            setSession(data);
            setModelPreference(data.model_preference);
            await fetchMessages(data.id);
            return;
          }
        }

        // Create new session
        const res = await fetch(`${API_BASE}/api/v1/chat/sessions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            ip_id: characterId,
            model_preference: modelPreference,
          }),
        });

        if (!res.ok) throw new Error("Failed to create session");

        const data = await res.json();
        setSession(data);

        // Update URL with session ID
        router.replace(`/chat/${characterId}?session=${data.id}`);

        // Fetch initial messages (opening message)
        await fetchMessages(data.id);
      } catch (err) {
        setError("채팅 세션을 시작하지 못했습니다");
      }
    }

    if (characterId && character) {
      initSession();
    }
  }, [characterId, character, sessionIdParam]);

  // Fetch scenarios
  useEffect(() => {
    async function fetchScenarios() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/chat/ips/${characterId}/scenarios`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setScenarios(data);
        }
      } catch (err) {
        console.error("Failed to fetch scenarios", err);
      }
    }

    if (characterId) {
      fetchScenarios();
    }
  }, [characterId]);

  // Fetch messages
  async function fetchMessages(sessionId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/chat/sessions/${sessionId}/messages`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
      }
    } catch (err) {
      console.error("Failed to fetch messages", err);
    }
  }

  // Send message with streaming
  async function handleSendMessage() {
    if (!inputValue.trim() || !session || isStreaming) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setIsStreaming(true);
    setStreamingContent("");

    // Add user message immediately
    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: userMessage,
      media_urls: [],
      tokens_used: 0,
      credits_charged: 0,
      model_used: null,
      latency_ms: 0,
      is_regenerated: false,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const url = `${API_BASE}/api/v1/chat/sessions/${session.id}/stream?content=${encodeURIComponent(userMessage)}`;
      const eventSource = new EventSource(url, { withCredentials: true });

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "message.chunk") {
            setStreamingContent((prev) => prev + data.chunk);
          } else if (data.type === "message.completed") {
            // Add the completed assistant message
            const assistantMessage: ChatMessage = {
              id: `msg-${Date.now()}`,
              role: "assistant",
              content: data.full_content,
              media_urls: [],
              tokens_used: 0,
              credits_charged: 0,
              model_used: modelPreference,
              latency_ms: 0,
              is_regenerated: false,
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setStreamingContent("");
            setIsStreaming(false);
            eventSource.close();
          } else if (data.type === "error") {
            setError(data.message);
            setIsStreaming(false);
            eventSource.close();
          }
        } catch (err) {
          console.error("Failed to parse SSE data", err);
        }
      };

      eventSource.onerror = () => {
        setError("연결이 끊어졌습니다");
        setIsStreaming(false);
        eventSource.close();
      };
    } catch (err) {
      setError("메시지 전송에 실패했습니다");
      setIsStreaming(false);
    }
  }

  // Regenerate last message
  async function handleRegenerate() {
    if (!session || isStreaming) return;

    const lastAssistantMessage = [...messages].reverse().find((m) => m.role === "assistant");
    if (!lastAssistantMessage) return;

    setIsLoading(true);

    try {
      const res = await fetch(
        `${API_BASE}/api/v1/chat/sessions/${session.id}/messages/${lastAssistantMessage.id}/regenerate`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (res.ok) {
        const newMessage = await res.json();
        setMessages((prev) => {
          const filtered = prev.filter((m) => m.id !== lastAssistantMessage.id);
          return [...filtered, newMessage];
        });
      }
    } catch (err) {
      setError("재생성에 실패했습니다");
    } finally {
      setIsLoading(false);
    }
  }

  // Handle keyboard shortcut
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }

  // Model badge color
  function getModelBadgeColor(model: string) {
    switch (model) {
      case "flash":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "pro":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "opus":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
    }
  }

  if (error && !character) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            뒤로 가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          {character?.thumbnail_url && (
            <img
              src={character.thumbnail_url}
              alt={character.name_ko}
              className="w-10 h-10 rounded-full object-cover"
            />
          )}

          <div>
            <h1 className="font-semibold text-gray-900 dark:text-white">
              {character?.name_ko || "Loading..."}
            </h1>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "text-xs px-2 py-0.5 rounded-full",
                  getModelBadgeColor(modelPreference)
                )}
              >
                {modelPreference.toUpperCase()}
              </span>
              {session?.scenario_branch && (
                <span className="text-xs text-gray-500">
                  {scenarios.find((s) => s.scenario_key === session.scenario_branch)?.name_ko}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRegenerate}
            disabled={isStreaming || messages.length === 0}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
            title="재생성"
          >
            <RefreshCw className={cn("w-5 h-5", isLoading && "animate-spin")} />
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              모델:
            </label>
            <select
              value={modelPreference}
              onChange={(e) => setModelPreference(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            >
              <option value="flash">Flash (1 크레딧/메시지)</option>
              <option value="pro">Pro (3 크레딧/메시지)</option>
              <option value="opus">Opus (5 크레딧/메시지)</option>
            </select>
          </div>

          {scenarios.length > 0 && (
            <div className="flex items-center gap-4 mt-3">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                시나리오:
              </label>
              <select
                value={session?.scenario_branch || ""}
                onChange={async (e) => {
                  if (!session) return;
                  const res = await fetch(
                    `${API_BASE}/api/v1/chat/sessions/${session.id}/scenario`,
                    {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      credentials: "include",
                      body: JSON.stringify({ scenario_key: e.target.value }),
                    }
                  );
                  if (res.ok) {
                    await fetchMessages(session.id);
                    setSession((prev) =>
                      prev ? { ...prev, scenario_branch: e.target.value } : null
                    );
                  }
                }}
                className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                {scenarios.map((s) => (
                  <option key={s.scenario_key} value={s.scenario_key}>
                    {s.name_ko}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} character={character} />
        ))}

        {/* Streaming indicator */}
        {isStreaming && streamingContent && (
          <div className="flex gap-3">
            {character?.thumbnail_url && (
              <img
                src={character.thumbnail_url}
                alt={character.name_ko}
                className="w-8 h-8 rounded-full object-cover flex-shrink-0"
              />
            )}
            <div className="max-w-[80%] px-4 py-3 rounded-2xl bg-white dark:bg-gray-800 shadow-sm">
              <p className="text-gray-900 dark:text-white whitespace-pre-wrap">
                {streamingContent}
                <span className="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse" />
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="text-center py-4">
            <p className="text-red-500 text-sm">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-sm text-blue-500 hover:underline mt-1"
            >
              닫기
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            disabled={isStreaming}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            rows={1}
            style={{
              minHeight: "44px",
              maxHeight: "120px",
            }}
          />

          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isStreaming}
            className={cn(
              "p-3 rounded-xl transition-colors",
              inputValue.trim() && !isStreaming
                ? "bg-blue-500 hover:bg-blue-600 text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-400"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center mt-2">
          {session?.total_credits_spent || 0} 크레딧 사용됨
        </p>
      </div>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({
  message,
  character,
}: {
  message: ChatMessage;
  character: IPCharacter | null;
}) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {!isUser && character?.thumbnail_url && (
        <img
          src={character.thumbnail_url}
          alt={character.name_ko}
          className="w-8 h-8 rounded-full object-cover flex-shrink-0"
        />
      )}

      <div
        className={cn(
          "max-w-[80%] px-4 py-3 rounded-2xl",
          isUser
            ? "bg-blue-500 text-white"
            : "bg-white dark:bg-gray-800 shadow-sm text-gray-900 dark:text-white"
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {/* Media attachments */}
        {message.media_urls.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.media_urls.map((url, i) => (
              <img
                key={i}
                src={url}
                alt={`attachment-${i}`}
                className="max-w-[200px] rounded-lg"
              />
            ))}
          </div>
        )}

        {/* Metadata */}
        {!isUser && message.latency_ms > 0 && (
          <p className="text-xs text-gray-400 mt-1">
            {message.latency_ms}ms
            {message.is_regenerated && " (재생성됨)"}
          </p>
        )}
      </div>
    </div>
  );
}
