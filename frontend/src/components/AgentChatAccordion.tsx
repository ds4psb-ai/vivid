"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, MoreHorizontal, Play, CheckCircle2, ChevronDown, Paperclip, X, File as FileIcon, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import {
    SSEEventBuffer,
    SSEConnectionManager,
    parseSSEEvent,
    saveSession,
    loadSession,
    clearSession,
    type EventHandlers,
    type SSEConnectionState,
} from "@/lib/sse-utils";
import {
    createEventHandlers,
    type AgentEventContext,
    type Message,
} from "@/lib/agent-event-handlers";
import type {
    WorkflowStepEvent,
    ToolResultEvent,
    WorkflowCreatedEvent,
    WorkflowStartEvent,
    WorkflowCompleteEvent,
} from "@/types/agent";

// Message type imported from @/lib/agent-event-handlers

// Template context from Singularity
interface TemplateContext {
    id: string;
    title: string;
    description?: string;
    tool_sequence?: string[];
    input_preset?: Record<string, unknown>;
}

interface AgentChatAccordionProps {
    onExecuteAll?: () => void;
    onManualExecute?: () => void;
    isExecuting?: boolean;
    initialMessage?: string;
    // Workflow event callbacks for dimension integration
    onWorkflowStart?: (data: WorkflowStartEvent) => void;
    onWorkflowStep?: (event: WorkflowStepEvent) => void;
    onWorkflowComplete?: (data: WorkflowCompleteEvent) => void;
    // Workflow created event (structure only, for manual execution)
    onWorkflowCreated?: (event: WorkflowCreatedEvent) => void;
    // Tool result callback for capturing dimension outputs
    onToolResult?: (result: ToolResultEvent) => void;
    // Template context from Singularity gallery
    templateContext?: TemplateContext | null;
}

export function AgentChatAccordion({
    onExecuteAll,
    onManualExecute,
    isExecuting = false,
    initialMessage = "안녕하세요! 차원 흐름을 함께 설계해드릴게요. 어떤 콘텐츠를 만들고 싶으신가요?",
    onWorkflowStart,
    onWorkflowStep,
    onWorkflowComplete,
    onWorkflowCreated,
    onToolResult,
    templateContext,
}: AgentChatAccordionProps) {
    const pathname = usePathname();
    const router = useRouter();
    const [isOpen, setIsOpen] = useState(false);

    // Safely build template-aware initial message
    const computedInitialMessage = useMemo(() => {
        if (!templateContext?.title) return initialMessage;

        // Sanitize and truncate title (max 50 chars)
        const safeTitle = String(templateContext.title || "")
            .replace(/[<>]/g, "")
            .slice(0, 50);

        if (!safeTitle) return initialMessage;

        const parts = [`🎬 "${safeTitle}" 템플릿이 적용되었습니다!\n\n`];

        // Safely handle tool_sequence
        if (Array.isArray(templateContext.tool_sequence) && templateContext.tool_sequence.length > 0) {
            const safeSequence = templateContext.tool_sequence
                .filter((s): s is string => typeof s === "string")
                .slice(0, 10)  // Max 10 steps
                .map(s => s.slice(0, 20));  // Max 20 chars per step
            if (safeSequence.length > 0) {
                parts.push(`${safeSequence.join(" → ")} 워크플로우가 준비되어 있어요.\n\n`);
            }
        }

        parts.push(`입력값을 넣고 "전체 실행"을 누르거나, 제가 도와드릴 내용이 있으면 말씀해주세요!`);
        return parts.join("");
    }, [templateContext, initialMessage]);

    const [messages, setMessages] = useState<Message[]>([
        {
            id: "initial",
            role: "assistant",
            content: initialMessage,  // Start with default, update via effect
            timestamp: new Date(),
        },
    ]);

    // Update initial message when template context changes
    useEffect(() => {
        setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages[0]?.id === "initial") {
                newMessages[0] = {
                    ...newMessages[0],
                    content: computedInitialMessage,
                };
            }
            return newMessages;
        });
    }, [computedInitialMessage]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [showMenu, setShowMenu] = useState(false);

    // P2: SSE connection state and session restoration
    const [connectionState, setConnectionState] = useState<SSEConnectionState>("disconnected");
    const [hasRestorableSession, setHasRestorableSession] = useState(false);
    const [lastFailedInput, setLastFailedInput] = useState<string | null>(null);
    const connectionManagerRef = useRef<SSEConnectionManager | null>(null);

    // Initialize connection manager
    useEffect(() => {
        connectionManagerRef.current = new SSEConnectionManager({
            maxRetries: 3,
            baseDelay: 1000,
            onStateChange: setConnectionState,
        });
    }, []);

    // Check for restorable session on mount
    useEffect(() => {
        const stored = loadSession();
        if (stored && stored.messages.length > 0) {
            setHasRestorableSession(true);
        }
    }, []);

    // Session restoration handler
    const handleRestoreSession = useCallback(() => {
        const stored = loadSession();
        if (!stored) return;

        const restoredMessages: Message[] = stored.messages.map(m => ({
            id: m.id,
            role: m.role as "user" | "assistant" | "tool",
            content: m.content,
            timestamp: new Date(m.timestamp),
            toolName: m.toolName,
            toolStatus: m.toolStatus as "pending" | "complete" | "error" | undefined,
        }));

        setMessages(restoredMessages);
        setHasRestorableSession(false);
        clearSession();
    }, []);

    // Dismiss restoration banner
    const handleDismissRestore = useCallback(() => {
        setHasRestorableSession(false);
        clearSession();
    }, []);

    // Retry last failed request
    const handleRetry = useCallback(() => {
        if (lastFailedInput) {
            setInput(lastFailedInput);
            setLastFailedInput(null);
            // Remove the last error message
            setMessages(prev => prev.filter(m => !m.id.startsWith('error-')));
        }
    }, [lastFailedInput]);

    // Draggable FAB position state
    const [fabPosition, setFabPosition] = useState({ x: 0, y: 0 });
    const constraintsRef = useRef<HTMLDivElement>(null);
    const isDraggingRef = useRef(false);

    // Calculate chat panel position with viewport boundary clamping
    const chatPosition = useMemo(() => {
        const chatWidth = 380;
        const chatHeight = 600;
        const padding = 16; // minimum distance from edge

        // Get viewport dimensions (use default if SSR)
        const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 1024;
        const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 768;

        // Calculate ideal position (centered above FAB)
        const idealLeft = viewportWidth / 2 + fabPosition.x - chatWidth / 2;
        const idealBottom = 96 + (-fabPosition.y); // 6rem = 96px

        // Clamp to viewport boundaries
        const clampedLeft = Math.max(padding, Math.min(idealLeft, viewportWidth - chatWidth - padding));
        const clampedBottom = Math.max(padding, Math.min(idealBottom, viewportHeight - chatHeight - padding));

        return { left: clampedLeft, bottom: clampedBottom };
    }, [fabPosition.x, fabPosition.y]);

    // File upload state
    const [files, setFiles] = useState<File[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll
    useEffect(() => {
        if (isOpen && messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, isOpen]);

    // Focus input
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
        }
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleSend = async () => {
        if ((!input.trim() && files.length === 0) || isLoading || isUploading) return;

        let uploadedAttachments: { name: string; mime_type: string; file_uri: string }[] = [];

        // Upload files if any
        if (files.length > 0) {
            setIsUploading(true);
            try {
                const uploadPromises = files.map(file => api.uploadFile(file));
                const results = await Promise.all(uploadPromises);
                uploadedAttachments = results.map(r => ({
                    name: r.display_name, // Use original filename for display
                    mime_type: r.mime_type,
                    file_uri: r.file_uri
                }));
            } catch (error) {
                console.error("File upload failed", error);
                // Optionally show error to user
                setIsUploading(false);
                return;
            }
            setIsUploading(false);
            setFiles([]); // Clear files after upload logic
        }

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: "user",
            content: input.trim(),
            timestamp: new Date(),
            attachments: uploadedAttachments.length > 0 ? uploadedAttachments : undefined,
        };

        setMessages((prev) => [...prev, userMessage]);
        const userInput = input.trim();
        setInput("");
        setIsLoading(true);

        try {
            // Safely build template metadata (avoid circular refs, limit size)
            let safeMetadata: Record<string, unknown> | undefined;
            if (templateContext?.id && templateContext?.title) {
                try {
                    safeMetadata = {
                        template: {
                            id: String(templateContext.id).slice(0, 100),
                            title: String(templateContext.title).slice(0, 100),
                            description: templateContext.description
                                ? String(templateContext.description).slice(0, 500)
                                : undefined,
                            tool_sequence: Array.isArray(templateContext.tool_sequence)
                                ? templateContext.tool_sequence.slice(0, 10).map(s => String(s).slice(0, 20))
                                : undefined,
                            // Omit input_preset to avoid large payloads - backend can fetch if needed
                        },
                    };
                } catch {
                    console.warn("[AgentChat] Failed to build template metadata");
                }
            }

            // Call Backend API
            const response = await api.openAgentChatStream({
                message: userInput || (uploadedAttachments.length > 0 ? "File attached" : ""),
                attachments: uploadedAttachments.length > 0 ? uploadedAttachments : undefined,
                page_context: pathname,
                metadata: safeMetadata,
            });

            if (!response.ok || !response.body) {
                throw new Error("API call failed");
            }

            // Init Assistant Message
            const assistantMessage: Message = {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: "",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMessage]);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // P4: AG-UI 표준 매퍼 - SSEEventBuffer 통합
            const accumulatedContentRef = { current: "" };

            const eventContext: AgentEventContext = {
                setMessages,
                assistantMessageId: assistantMessage.id,
                accumulatedContentRef,
                onWorkflowStart,
                onWorkflowStep,
                onWorkflowComplete,
                onWorkflowCreated,
                onToolResult,
                router,
            };

            const handlers = createEventHandlers(eventContext);
            const eventBuffer = new SSEEventBuffer(handlers, { debug: false });

            connectionManagerRef.current?.setState("connected");

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    for (const line of chunk.split("\n")) {
                        if (line.startsWith("data: ")) {
                            const event = parseSSEEvent(line.slice(6));
                            if (event) {
                                eventBuffer.push(event);
                            }
                        }
                    }
                }
            } finally {
                connectionManagerRef.current?.setState("disconnected");
            }

            // 세션 저장 - 최신 messages 상태 사용
            setMessages(currentMessages => {
                saveSession("vivid-agent", currentMessages.map(m => ({
                    id: m.id,
                    role: m.role,
                    content: typeof m.content === 'string' ? m.content : accumulatedContentRef.current,
                    timestamp: m.timestamp,
                    toolName: m.toolName,
                    toolStatus: m.toolStatus,
                })));
                return currentMessages;
            });

        } catch (error) {
            console.error("Chat error:", error);

            // 에러 유형 분류
            const errorType = error instanceof TypeError ? "network"
                : (error as Error)?.message?.includes("timeout") ? "timeout"
                    : "server";

            const errorMessageContent = errorType === "network"
                ? "🌐 네트워크 연결을 확인해주세요."
                : errorType === "timeout"
                    ? "⏱️ 응답이 너무 오래 걸려요. 다시 시도해주세요."
                    : "앗, 차원 이동 중 문제가 생겼어요. 다시 시도해주세요! 🐰";

            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: "assistant",
                content: errorMessageContent,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);

            // 마지막 실패 요청 저장 (재시도용)
            setLastFailedInput(userInput);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Drag Constraints - Full Screen */}
            <div ref={constraintsRef} className="fixed inset-0 pointer-events-none z-40" />

            {/* Draggable Chokki FAB */}
            <motion.div
                drag
                dragConstraints={constraintsRef}
                dragElastic={0.05}
                dragMomentum={false}
                whileDrag={{ scale: 1.1 }}
                className="fixed bottom-8 left-1/2 z-[60] pointer-events-auto cursor-grab active:cursor-grabbing"
                style={{
                    x: fabPosition.x,
                    y: fabPosition.y,
                    translateX: "-50%"
                }}
                onDragStart={() => {
                    isDraggingRef.current = true;
                }}
                onDragEnd={(_, info) => {
                    // Only update position if actually moved
                    if (Math.abs(info.offset.x) > 5 || Math.abs(info.offset.y) > 5) {
                        setFabPosition(prev => ({
                            x: prev.x + info.offset.x,
                            y: prev.y + info.offset.y
                        }));
                    }
                    // Reset drag flag after animation frame to avoid race condition
                    requestAnimationFrame(() => {
                        isDraggingRef.current = false;
                    });
                }}
            >
                <button
                    onClick={(e) => {
                        // Prevent click if we were dragging
                        if (isDraggingRef.current) {
                            e.preventDefault();
                            e.stopPropagation();
                            return;
                        }
                        setIsOpen(!isOpen);
                    }}
                    className="relative group focus:outline-none"
                >
                    {/* Glow Effect */}
                    <div className={`absolute inset-0 rounded-full blur-xl transition-all duration-500 ${isOpen
                        ? 'bg-zinc-500/30'
                        : 'bg-violet-500/40 group-hover:bg-violet-400/50'
                        }`} />

                    {/* Chokki Image */}
                    <div className={`relative h-16 w-16 rounded-full overflow-hidden border-2 shadow-[0_10px_40px_rgba(0,0,0,0.5)] transition-all duration-300 ${isOpen
                        ? 'border-zinc-600 shadow-zinc-900/50'
                        : 'border-violet-400/50 shadow-violet-500/30 group-hover:border-violet-300/70 group-hover:shadow-violet-400/40'
                        }`}>
                        <Image
                            src="/assets/characters/chokki.png"
                            alt="Chokki"
                            width={64}
                            height={64}
                            className={`object-cover w-full h-full transition-all duration-300 pointer-events-none ${isOpen ? 'brightness-75' : 'group-hover:scale-110'
                                }`}
                            unoptimized
                            draggable={false}
                        />

                        {/* Close Overlay when Open */}
                        {isOpen && (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                                <ChevronDown className="h-6 w-6 text-white" />
                            </div>
                        )}
                    </div>

                    {/* Status Indicator */}
                    {!isOpen && (
                        <span className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-4 w-4 bg-lime-500 border-2 border-black"></span>
                        </span>
                    )}

                    {/* Executing Indicator */}
                    {isExecuting && !isOpen && (
                        <div className="absolute -top-1 -right-1 h-4 w-4">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-4 w-4 bg-amber-500 border-2 border-black"></span>
                        </div>
                    )}
                </button>
            </motion.div>

            {/* Chat Panel - follows FAB position */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed z-50 pointer-events-auto w-[380px] h-[600px] flex flex-col bg-black/90 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden"
                        style={{
                            left: chatPosition.left,
                            bottom: chatPosition.bottom,
                        }}
                    >
                        {/* Background Effect */}
                        <div className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-violet-500/10 to-transparent pointer-events-none" />

                        {/* Header */}
                        <div className="relatvie flex items-center justify-between px-5 py-4 border-b border-white/5 bg-white/[0.02]">
                            <div className="flex items-center gap-3">
                                <div className="relative group cursor-pointer">
                                    <div className="h-10 w-10 rounded-full bg-black/50 overflow-hidden border border-white/10 flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)] group-hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] transition-all">
                                        <Image
                                            src="/assets/characters/chokki.png"
                                            alt="Chokki"
                                            width={40}
                                            height={40}
                                            className="object-cover w-full h-full"
                                            unoptimized
                                        />
                                    </div>
                                    <span className="absolute -bottom-0.5 -right-0.5 flex h-3 w-3">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-lime-500 border-2 border-black"></span>
                                    </span>
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
                                        차원 안내자 초끼
                                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-white/10 text-zinc-300 font-medium border border-white/5">Beta</span>
                                    </h3>
                                    <p className="text-[11px] text-zinc-400 font-medium">Gemini 3.0 Flash</p>
                                </div>
                            </div>

                            {/* Menu */}
                            <div className="relative">
                                <button
                                    onClick={() => setShowMenu(!showMenu)}
                                    className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                                >
                                    <MoreHorizontal className="h-5 w-5" />
                                </button>

                                <AnimatePresence>
                                    {showMenu && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.9, y: 5 }}
                                            animate={{ opacity: 1, scale: 1, y: 0 }}
                                            exit={{ opacity: 0, scale: 0.9, y: 5 }}
                                            className="absolute right-0 top-full mt-2 w-48 bg-[#1a1a1c] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 p-1"
                                        >
                                            <button
                                                onClick={() => {
                                                    onExecuteAll?.();
                                                    setShowMenu(false);
                                                }}
                                                disabled={isExecuting}
                                                className="w-full px-3 py-2.5 text-left text-xs font-medium text-zinc-300 hover:bg-violet-600/20 hover:text-violet-300 flex items-center gap-2.5 transition-colors disabled:opacity-50 rounded-lg"
                                            >
                                                <Play className="h-3.5 w-3.5" />
                                                전체 워크플로우 실행
                                            </button>
                                            <button
                                                onClick={() => {
                                                    onManualExecute?.();
                                                    setShowMenu(false);
                                                }}
                                                className="w-full px-3 py-2.5 text-left text-xs font-medium text-zinc-300 hover:bg-lime-500/20 hover:text-lime-300 flex items-center gap-2.5 transition-colors rounded-lg"
                                            >
                                                <CheckCircle2 className="h-3.5 w-3.5" />
                                                수동 실행 모드 전환
                                            </button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* P2: Session Restoration Banner */}
                        {hasRestorableSession && (
                            <div className="mx-4 mt-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
                                <p className="text-xs text-amber-200 mb-2">
                                    💬 이전 대화를 복원할 수 있습니다.
                                </p>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleRestoreSession}
                                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-amber-500 text-black rounded-lg hover:bg-amber-400 transition-colors"
                                    >
                                        <RefreshCw className="h-3 w-3" />
                                        복원하기
                                    </button>
                                    <button
                                        onClick={handleDismissRestore}
                                        className="text-xs text-amber-300/70 hover:text-amber-300 underline transition-colors"
                                    >
                                        무시
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* P2: Connection Status Indicator */}
                        {connectionState === "connecting" && (
                            <div className="mx-4 mt-2 flex items-center gap-2 text-xs text-blue-400">
                                <span className="animate-pulse">●</span>
                                연결 중...
                            </div>
                        )}
                        {connectionState === "reconnecting" && (
                            <div className="mx-4 mt-2 flex items-center gap-2 text-xs text-yellow-400">
                                <RefreshCw className="h-3 w-3 animate-spin" />
                                재연결 중...
                            </div>
                        )}
                        {connectionState === "error" && (
                            <div className="mx-4 mt-2 text-xs text-red-400">
                                ⚠️ 연결 오류가 발생했습니다
                            </div>
                        )}

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-5 space-y-6 scrollbar-thin scrollbar-thumb-zinc-700/50 scrollbar-track-transparent">
                            {messages.map((message) => {
                                // Tool message - render as card
                                if (message.role === "tool") {
                                    const isPending = message.toolStatus === "pending";
                                    const isError = message.toolStatus === "error";
                                    const isComplete = message.toolStatus === "complete";

                                    // Dynamic card styling based on status
                                    const cardStyles = isPending
                                        ? "border-amber-500/30 bg-amber-500/10"
                                        : isError
                                            ? "border-red-500/30 bg-red-500/10"
                                            : "border-emerald-500/30 bg-emerald-500/10";

                                    const textColor = isPending
                                        ? "text-amber-400"
                                        : isError
                                            ? "text-red-400"
                                            : "text-emerald-400";

                                    const badgeStyles = isPending
                                        ? "bg-amber-500/20 text-amber-300"
                                        : isError
                                            ? "bg-red-500/20 text-red-300"
                                            : "bg-emerald-500/20 text-emerald-300";

                                    const statusText = isPending ? "실행 중" : isError ? "실패" : "완료";

                                    return (
                                        <div key={message.id} className="flex gap-3">
                                            {/* Icon with glass effect */}
                                            <div className={`h-8 w-8 rounded-xl backdrop-blur-sm ${isPending
                                                ? "bg-amber-500/10 border-amber-500/20"
                                                : isComplete
                                                    ? "bg-emerald-500/10 border-emerald-500/20"
                                                    : "bg-red-500/10 border-red-500/20"
                                                } border flex items-center justify-center shrink-0`}>
                                                {isPending ? (
                                                    <span className="h-4 w-4 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
                                                ) : isComplete ? (
                                                    <Bot className="h-4 w-4 text-emerald-400" />
                                                ) : (
                                                    <Bot className="h-4 w-4 text-red-400" />
                                                )}
                                            </div>
                                            {/* Card with glass morphism */}
                                            <div className={`flex-1 rounded-xl backdrop-blur-sm border ${cardStyles} p-3 transition-all duration-500`}>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className={`text-xs font-semibold ${textColor}`}>
                                                        🔧 {message.toolName}
                                                    </span>
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded flex items-center gap-1 ${badgeStyles}`}>
                                                        {isPending && (
                                                            <span className="h-2 w-2 border border-current border-t-transparent rounded-full animate-spin" />
                                                        )}
                                                        {statusText}
                                                    </span>
                                                </div>
                                                {isPending ? (
                                                    <div className="flex items-center gap-2 text-xs text-amber-300/70">
                                                        <span className="animate-pulse">도구를 실행하고 있습니다...</span>
                                                    </div>
                                                ) : message.toolError ? (
                                                    <p className="text-xs text-red-300">{message.toolError}</p>
                                                ) : message.toolOutput && Object.keys(message.toolOutput).length > 0 ? (
                                                    <div className="text-xs text-zinc-400 max-h-20 overflow-y-auto">
                                                        {Object.entries(message.toolOutput).slice(0, 3).map(([key, value]) => (
                                                            <div key={key} className="truncate">
                                                                <span className="text-zinc-500">{key}:</span>{" "}
                                                                <span className="text-zinc-300">
                                                                    {typeof value === "string" ? value.slice(0, 50) + (value.length > 50 ? "..." : "") : JSON.stringify(value).slice(0, 50)}
                                                                </span>
                                                            </div>
                                                        ))}
                                                        {Object.keys(message.toolOutput).length > 3 && (
                                                            <span className="text-zinc-500 text-[10px]">...외 {Object.keys(message.toolOutput).length - 3}개 필드</span>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <p className="text-xs text-zinc-500 italic">결과 없음</p>
                                                )}
                                            </div>
                                        </div>
                                    );
                                }

                                // User/Assistant message - original rendering
                                return (
                                    <div
                                        key={message.id}
                                        className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
                                    >
                                        {message.role === "assistant" && (
                                            <div className="h-8 w-8 rounded-full bg-black/50 overflow-hidden border border-white/10 flex items-center justify-center shrink-0 shadow-lg shadow-violet-500/20">
                                                <Image
                                                    src="/assets/characters/chokki.png"
                                                    alt="Chokki"
                                                    width={32}
                                                    height={32}
                                                    className="object-cover w-full h-full"
                                                    unoptimized
                                                />
                                            </div>
                                        )}

                                        <div className="flex flex-col gap-1 max-w-[85%]">
                                            <span className={`text-[10px] font-medium px-1 ${message.role === "assistant" ? "text-zinc-500" : "text-violet-300 text-right"}`}>
                                                {message.role === "assistant" ? "초끼" : "You"}
                                            </span>
                                            <div
                                                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${message.role === "assistant"
                                                    ? "bg-zinc-800/80 text-zinc-100 border border-white/5 rounded-tl-none"
                                                    : "bg-violet-600 text-white shadow-lg shadow-violet-600/20 rounded-tr-none"
                                                    }`}
                                            >
                                                {message.content}
                                                {message.attachments && message.attachments.length > 0 && (
                                                    <div className="mt-2 flex flex-wrap gap-2">
                                                        {message.attachments.map((file, i) => (
                                                            <div key={i} className="flex items-center gap-1.5 rounded-md bg-black/20 px-2 py-1.5 text-xs text-white/80">
                                                                <FileIcon className="h-3 w-3 opacity-70" />
                                                                <span className="max-w-[150px] truncate">{file.name}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}

                            {isLoading && (
                                <div className="flex gap-3">
                                    <div className="h-8 w-8 rounded-full bg-black/50 overflow-hidden border border-white/10 flex items-center justify-center shrink-0 shadow-lg shadow-violet-500/20">
                                        <Image
                                            src="/assets/characters/chokki.png"
                                            alt="Chokki"
                                            width={32}
                                            height={32}
                                            className="object-cover w-full h-full"
                                            unoptimized
                                        />
                                    </div>
                                    <div className="bg-zinc-800/80 rounded-2xl rounded-tl-none px-4 py-3 border border-white/5">
                                        <div className="flex gap-1.5 h-5 items-center">
                                            <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                                            <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                                            <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-4 bg-black/40 backdrop-blur-md border-t border-white/5 space-y-3">
                            {/* Retry Button - shown when last request failed */}
                            {lastFailedInput && (
                                <button
                                    onClick={handleRetry}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-xl hover:bg-amber-500/20 transition-colors"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                    다시 시도하기
                                </button>
                            )}

                            {/* File Preview */}
                            {files.length > 0 && (
                                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
                                    {files.map((file, i) => (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            key={i}
                                            className="relative flex items-center gap-2 rounded-lg bg-zinc-800/80 px-3 py-2 text-xs text-zinc-300 border border-white/10 shrink-0"
                                        >
                                            <span className="max-w-[100px] truncate">{file.name}</span>
                                            <button
                                                onClick={() => removeFile(i)}
                                                className="ml-1 rounded-full p-0.5 hover:bg-white/10 transition-colors"
                                            >
                                                <X className="h-3 w-3" />
                                            </button>
                                        </motion.div>
                                    ))}
                                </div>
                            )}

                            <div className="relative group">
                                <input
                                    type="file"
                                    multiple
                                    ref={fileInputRef}
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="absolute left-3 top-3 p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                                >
                                    <Paperclip className="h-4 w-4" />
                                </button>

                                <input
                                    ref={inputRef}
                                    role="textbox"
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="초끼에게 차원 여행 도움 요청하기..."
                                    className="w-full bg-zinc-900/50 border border-white/10 rounded-2xl pl-12 pr-12 py-3.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 focus:bg-zinc-900 transition-all focus:ring-1 focus:ring-violet-500/20"
                                />
                                <button
                                    onClick={handleSend}
                                    disabled={(!input.trim() && files.length === 0) || isLoading || isUploading}
                                    className="absolute right-2 top-2 h-9 w-9 rounded-xl flex items-center justify-center transition-all duration-200 disabled:opacity-0 disabled:scale-75 text-white bg-violet-600 hover:bg-violet-500 shadow-lg shadow-violet-500/25"
                                >
                                    {isUploading ? (
                                        <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    ) : (
                                        <Send className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}

