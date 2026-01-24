"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
    Bot,
    Send,
    Wand2,
    Eye,
    Undo2,
    AlertCircle,
    CheckCircle,
    Loader2,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface NodeChange {
    property: string;
    oldValue: unknown;
    newValue: unknown;
    isNew?: boolean;
}

interface STPFEvaluation {
    score: number;
    grade: string;
    action: "auto_apply" | "apply_with_log" | "confirm_required" | "reject" | "suggest_alternative";
    actionReason: string;
    kellyRecommendation?: string;
}

interface ChatMessage {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: Date;
    preview?: {
        nodeId: string;
        changes: NodeChange[];
        stpf: STPFEvaluation;
    };
    applied?: boolean;
    changeId?: string;
}

interface NodeChatPanelProps {
    nodeId: string;
    nodeType: string;
    currentProperties: Record<string, unknown>;
    onApplyChanges: (changes: Record<string, unknown>) => Promise<void>;
    onUndo: (changeId: string) => Promise<void>;
    className?: string;
}

// ============================================================================
// Helpers
// ============================================================================

const getGradeColor = (grade: string): string => {
    if (grade.includes("Unicorn")) return "text-purple-400";
    if (grade.includes("High")) return "text-emerald-400";
    if (grade.includes("Red")) return "text-amber-400";
    return "text-rose-400";
};

const getActionIcon = (action: string) => {
    switch (action) {
        case "auto_apply":
            return <CheckCircle className="h-4 w-4 text-emerald-400" />;
        case "apply_with_log":
            return <CheckCircle className="h-4 w-4 text-sky-400" />;
        case "confirm_required":
            return <Eye className="h-4 w-4 text-amber-400" />;
        default:
            return <AlertCircle className="h-4 w-4 text-rose-400" />;
    }
};

// ============================================================================
// Subcomponents
// ============================================================================

const ChangePreviewCard = ({
    preview,
    onApply,
    onCancel,
    isApplying,
}: {
    preview: ChatMessage["preview"];
    onApply: () => void;
    onCancel: () => void;
    isApplying: boolean;
}) => {
    if (!preview) return null;

    return (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/20 p-4">
            {/* STPF Badge */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {getActionIcon(preview.stpf.action)}
                    <span className={`text-sm font-semibold ${getGradeColor(preview.stpf.grade)}`}>
                        {preview.stpf.grade}
                    </span>
                    <span className="text-xs text-slate-400">
                        Score: {preview.stpf.score.toFixed(0)}
                    </span>
                </div>
                {preview.stpf.kellyRecommendation && (
                    <span className="text-xs text-slate-500">
                        {preview.stpf.kellyRecommendation}
                    </span>
                )}
            </div>

            {/* Changes List */}
            <div className="mt-3 space-y-2">
                {preview.changes.map((change, idx) => (
                    <div
                        key={idx}
                        className="flex items-center justify-between rounded-lg border border-white/5 bg-white/5 px-3 py-2 text-xs"
                    >
                        <span className="font-medium text-slate-200">{change.property}</span>
                        <div className="flex items-center gap-2">
                            {!change.isNew && (
                                <>
                                    <span className="text-slate-500 line-through">
                                        {String(change.oldValue)}
                                    </span>
                                    <span className="text-slate-400">→</span>
                                </>
                            )}
                            <span className="text-sky-300">{String(change.newValue)}</span>
                            {change.isNew && (
                                <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] text-emerald-300">
                                    NEW
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Action Reason */}
            <div className="mt-3 text-xs text-slate-400">{preview.stpf.actionReason}</div>

            {/* Action Buttons */}
            {preview.stpf.action !== "reject" && (
                <div className="mt-4 flex items-center gap-2">
                    <button
                        type="button"
                        onClick={onApply}
                        disabled={isApplying}
                        className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-100 transition hover:border-emerald-500/70 hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {isApplying ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Wand2 className="h-3.5 w-3.5" />
                        )}
                        적용하기
                    </button>
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={isApplying}
                        className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300 transition hover:border-white/20 hover:bg-white/10"
                    >
                        취소
                    </button>
                </div>
            )}
        </div>
    );
};

const UndoButton = ({
    changeId,
    onUndo,
    isUndoing,
}: {
    changeId: string;
    onUndo: (id: string) => void;
    isUndoing: boolean;
}) => (
    <button
        type="button"
        onClick={() => onUndo(changeId)}
        disabled={isUndoing}
        className="mt-2 inline-flex items-center gap-1 text-xs text-slate-400 transition hover:text-slate-200"
    >
        {isUndoing ? (
            <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
            <Undo2 className="h-3 w-3" />
        )}
        되돌리기
    </button>
);

// ============================================================================
// Quick Commands
// ============================================================================

const QUICK_COMMANDS = [
    { label: "밝게", command: "밝게 해줘" },
    { label: "어둡게", command: "어둡게 해줘" },
    { label: "극적으로", command: "더 극적으로" },
    { label: "부드럽게", command: "부드럽게 해줘" },
    { label: "줌인", command: "카메라 줌인" },
    { label: "빠르게", command: "더 빠르게" },
];

// ============================================================================
// Main Component
// ============================================================================

export default function NodeChatPanel({
    nodeId,
    nodeType,
    currentProperties,
    onApplyChanges,
    onUndo,
    className,
}: NodeChatPanelProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [draft, setDraft] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isApplying, setIsApplying] = useState(false);
    const [isUndoing, setIsUndoing] = useState(false);
    const endRef = useRef<HTMLDivElement | null>(null);

    // Auto-scroll
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }, [messages]);

    // Parse intent and get preview
    const parseIntent = useCallback(
        async (userInput: string): Promise<ChatMessage["preview"] | null> => {
            try {
                const response = await fetch("/api/v1/intent/parse", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_input: userInput,
                        node_id: nodeId,
                        node_type: nodeType,
                        current_properties: currentProperties,
                        include_stpf: true,
                    }),
                });

                if (!response.ok) return null;

                const data = await response.json();

                if (!data.success) return null;

                // Transform to preview format
                const changes: NodeChange[] = Object.entries(
                    data.intent?.simple_changes || {}
                ).map(([key, value]) => ({
                    property: key,
                    oldValue: currentProperties[key],
                    newValue: value,
                    isNew: !(key in currentProperties),
                }));

                return {
                    nodeId,
                    changes,
                    stpf: {
                        score: data.stpf_score || 500,
                        grade: data.stpf_grade || "Unknown",
                        action: data.kelly_recommendation?.includes("적극")
                            ? "auto_apply"
                            : data.stpf_score > 500
                                ? "apply_with_log"
                                : data.stpf_score > 250
                                    ? "confirm_required"
                                    : "reject",
                        actionReason: `STPF ${data.stpf_score?.toFixed(0) || 0}점`,
                        kellyRecommendation: data.kelly_recommendation,
                    },
                };
            } catch (error) {
                console.error("Intent parse error:", error);
                return null;
            }
        },
        [nodeId, nodeType, currentProperties]
    );

    // Send message
    const handleSend = useCallback(async () => {
        const value = draft.trim();
        if (!value || isLoading) return;

        setDraft("");
        setIsLoading(true);

        // Add user message
        const userMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: value,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        // Parse and create preview
        const preview = await parseIntent(value);

        // Add assistant message with preview
        const assistantMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: preview
                ? `"${value}" 요청을 분석했습니다. 아래 변경 사항을 확인해주세요.`
                : `죄송합니다. "${value}"을(를) 이해하지 못했습니다. 다시 시도해주세요.`,
            timestamp: new Date(),
            preview: preview || undefined,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        setIsLoading(false);
    }, [draft, isLoading, parseIntent]);

    // Apply changes
    const handleApply = useCallback(
        async (messageId: string) => {
            const message = messages.find((m) => m.id === messageId);
            if (!message?.preview) return;

            setIsApplying(true);

            try {
                const changes: Record<string, unknown> = {};
                message.preview.changes.forEach((c) => {
                    changes[c.property] = c.newValue;
                });

                await onApplyChanges(changes);

                // Update message as applied
                setMessages((prev) =>
                    prev.map((m) =>
                        m.id === messageId
                            ? { ...m, applied: true, changeId: crypto.randomUUID() }
                            : m
                    )
                );

                // Add confirmation message
                setMessages((prev) => [
                    ...prev,
                    {
                        id: crypto.randomUUID(),
                        role: "system",
                        content: `✅ 변경이 적용되었습니다. (${message.preview?.changes.length}개 속성)`,
                        timestamp: new Date(),
                    },
                ]);
            } catch (error) {
                console.error("Apply error:", error);
                setMessages((prev) => [
                    ...prev,
                    {
                        id: crypto.randomUUID(),
                        role: "system",
                        content: `❌ 변경 적용 실패: ${error}`,
                        timestamp: new Date(),
                    },
                ]);
            }

            setIsApplying(false);
        },
        [messages, onApplyChanges]
    );

    // Undo
    const handleUndo = useCallback(
        async (changeId: string) => {
            setIsUndoing(true);

            try {
                await onUndo(changeId);
                setMessages((prev) => [
                    ...prev,
                    {
                        id: crypto.randomUUID(),
                        role: "system",
                        content: "↩️ 변경이 되돌려졌습니다.",
                        timestamp: new Date(),
                    },
                ]);
            } catch (error) {
                console.error("Undo error:", error);
            }

            setIsUndoing(false);
        },
        [onUndo]
    );

    // Quick command
    const handleQuickCommand = (command: string) => {
        setDraft(command);
    };

    const canSend = draft.trim().length > 0 && !isLoading;

    return (
        <div
            className={`flex h-full flex-col rounded-3xl border border-white/10 bg-white/5 ${className ?? ""}`}
        >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <div>
                    <div className="text-sm font-semibold text-slate-100">노드 채팅</div>
                    <div className="text-xs text-slate-400">
                        {nodeId} · {nodeType}
                    </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Bot className="h-4 w-4 text-purple-300" />
                    AI 편집
                </div>
            </div>

            {/* Quick Commands */}
            <div className="flex flex-wrap gap-2 border-b border-white/10 px-5 py-3">
                {QUICK_COMMANDS.map((cmd) => (
                    <button
                        key={cmd.label}
                        type="button"
                        onClick={() => handleQuickCommand(cmd.command)}
                        className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300 transition hover:border-purple-500/40 hover:bg-purple-500/10 hover:text-purple-200"
                    >
                        {cmd.label}
                    </button>
                ))}
            </div>

            {/* Messages */}
            <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
                {messages.length === 0 && (
                    <div className="rounded-2xl border border-dashed border-white/10 bg-slate-900/30 p-6 text-center text-sm text-slate-400">
                        노드를 어떻게 변경할지 말씀해주세요.
                        <br />
                        <span className="text-xs text-slate-500">
                            예: &quot;더 밝게&quot;, &quot;극적으로 바꿔줘&quot;, &quot;카메라 줌인&quot;
                        </span>
                    </div>
                )}

                {messages.map((message) => {
                    if (message.role === "system") {
                        return (
                            <div key={message.id} className="text-center text-xs text-slate-400">
                                {message.content}
                            </div>
                        );
                    }

                    const isUser = message.role === "user";
                    const alignClass = isUser ? "justify-end" : "justify-start";
                    const bubbleClass = isUser
                        ? "border-purple-500/40 bg-purple-500/10 text-slate-100"
                        : "border-white/10 bg-white/5 text-slate-100";

                    return (
                        <div key={message.id} className={`flex ${alignClass} gap-3`}>
                            <div className={`max-w-[var(--layout-bubble-max)] rounded-2xl border px-4 py-3 ${bubbleClass}`}>
                                <div className="text-sm text-slate-100">{message.content}</div>

                                {message.preview && !message.applied && (
                                    <ChangePreviewCard
                                        preview={message.preview}
                                        onApply={() => handleApply(message.id)}
                                        onCancel={() => { }}
                                        isApplying={isApplying}
                                    />
                                )}

                                {message.applied && message.changeId && (
                                    <UndoButton
                                        changeId={message.changeId}
                                        onUndo={handleUndo}
                                        isUndoing={isUndoing}
                                    />
                                )}
                            </div>
                        </div>
                    );
                })}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                분석 중...
                            </div>
                        </div>
                    </div>
                )}

                <div ref={endRef} />
            </div>

            {/* Input */}
            <div className="border-t border-white/10 px-5 py-4">
                <div className="glass-card rounded-2xl p-3">
                    <textarea
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="노드 변경 요청을 입력하세요..."
                        rows={2}
                        className="w-full resize-none bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
                    />
                    <div className="mt-3 flex items-center justify-between">
                        <div className="text-xs text-slate-500">Shift+Enter로 줄바꿈</div>
                        <button
                            type="button"
                            onClick={handleSend}
                            disabled={!canSend}
                            className={`inline-flex items-center gap-2 rounded-full border border-purple-500/40 bg-purple-500/10 px-4 py-2 text-xs font-semibold text-purple-100 transition hover:border-purple-500/70 hover:bg-purple-500/20 ${!canSend ? "cursor-not-allowed opacity-40" : ""
                                }`}
                        >
                            <Send className="h-3.5 w-3.5" />
                            분석
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
