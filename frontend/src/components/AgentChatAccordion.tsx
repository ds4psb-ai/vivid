"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, MoreHorizontal, Play, CheckCircle2, ChevronDown, Paperclip, X, File as FileIcon } from "lucide-react";
import { api } from "@/lib/api";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: React.ReactNode;
    timestamp: Date;
    attachments?: { name: string; mime_type: string; file_uri: string }[];
}

// Workflow step event from agent
interface WorkflowStepEvent {
    step: number;
    total_steps: number;
    dimension: string;
    dimension_name: string;
    tool_name: string;
    status?: "start" | "complete" | "error";
    output_preview?: string;
    credit_cost?: number;
}

// Tool result event from agent
interface ToolResultEvent {
    name: string;
    status: string;
    output: Record<string, unknown>;
    error?: string;
}

interface AgentChatAccordionProps {
    onExecuteAll?: () => void;
    onManualExecute?: () => void;
    isExecuting?: boolean;
    initialMessage?: string;
    // Workflow event callbacks for dimension integration
    onWorkflowStart?: (data: { topic: string; dimensions: string[]; total_steps: number }) => void;
    onWorkflowStep?: (event: WorkflowStepEvent) => void;
    onWorkflowComplete?: (data: { total_credits: number; success_count: number }) => void;
    // Tool result callback for capturing dimension outputs
    onToolResult?: (result: ToolResultEvent) => void;
}

export function AgentChatAccordion({
    onExecuteAll,
    onManualExecute,
    isExecuting = false,
    initialMessage = "안녕하세요! 차원 흐름을 함께 설계해드릴게요. 어떤 콘텐츠를 만들고 싶으신가요?",
    onWorkflowStart,
    onWorkflowStep,
    onWorkflowComplete,
    onToolResult,
}: AgentChatAccordionProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "initial",
            role: "assistant",
            content: initialMessage,
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [showMenu, setShowMenu] = useState(false);

    // Draggable FAB position state
    const [fabPosition, setFabPosition] = useState({ x: 0, y: 0 });
    const constraintsRef = useRef<HTMLDivElement>(null);

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
            // Call Backend API
            const response = await api.openAgentChatStream({
                message: userInput || (uploadedAttachments.length > 0 ? "File attached" : ""),
                attachments: uploadedAttachments.length > 0 ? uploadedAttachments : undefined,
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
            let accumulatedContent = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const rawData = line.slice(6);
                            if (!rawData || rawData === '[DONE]') continue;

                            const data = JSON.parse(rawData);
                            if (!data || typeof data !== 'object') continue;

                            const eventType = data.type;
                            const payload = data.payload;

                            // Handle streaming delta events
                            if (eventType === "agent.delta" && payload?.delta) {
                                accumulatedContent += String(payload.delta || '');
                                setMessages((prev) =>
                                    prev.map(m => m.id === assistantMessage.id
                                        ? { ...m, content: accumulatedContent }
                                        : m
                                    )
                                );
                            }
                            // Handle complete message events (fallback)
                            else if (eventType === "agent.message" && payload?.content) {
                                accumulatedContent = String(payload.content || '');
                                setMessages((prev) =>
                                    prev.map(m => m.id === assistantMessage.id
                                        ? { ...m, content: accumulatedContent }
                                        : m
                                    )
                                );
                            }
                            // === Workflow Events for Dimension Integration ===
                            else if (eventType === "agent.workflow_start" && payload) {
                                onWorkflowStart?.({
                                    topic: String(payload.topic || ''),
                                    dimensions: Array.isArray(payload.dimensions) ? payload.dimensions : [],
                                    total_steps: Number(payload.total_steps) || 0,
                                });
                            }
                            else if (eventType === "agent.workflow_step_start" && payload) {
                                onWorkflowStep?.({
                                    step: Number(payload.step) || 0,
                                    total_steps: Number(payload.total_steps) || 0,
                                    dimension: String(payload.dimension || ''),
                                    dimension_name: String(payload.dimension_name || ''),
                                    tool_name: String(payload.tool_name || ''),
                                    status: "start",
                                });
                            }
                            else if (eventType === "agent.workflow_step_complete" && payload) {
                                onWorkflowStep?.({
                                    step: Number(payload.step) || 0,
                                    total_steps: Number(payload.total_steps) || 0,
                                    dimension: String(payload.dimension || ''),
                                    dimension_name: String(payload.dimension_name || ''),
                                    tool_name: String(payload.tool_name || ''),
                                    status: "complete",
                                    output_preview: payload.output_preview ? String(payload.output_preview) : undefined,
                                    credit_cost: typeof payload.credit_cost === 'number' ? payload.credit_cost : undefined,
                                });
                            }
                            else if (eventType === "agent.workflow_step_error" && payload) {
                                onWorkflowStep?.({
                                    step: Number(payload.step) || 0,
                                    total_steps: Number(payload.total_steps) || 0,
                                    dimension: String(payload.dimension || ''),
                                    dimension_name: String(payload.dimension_name || ''),
                                    tool_name: String(payload.tool_name || ''),
                                    status: "error",
                                });
                            }
                            else if (eventType === "agent.workflow_complete" && payload) {
                                onWorkflowComplete?.({
                                    total_credits: typeof payload.total_credits === 'number' ? payload.total_credits : 0,
                                    success_count: typeof payload.success_count === 'number' ? payload.success_count : 0,
                                });
                            }
                            // Tool result event - capture dimension outputs
                            else if (eventType === "agent.tool_result" && payload) {
                                onToolResult?.({
                                    name: String(payload.name || ''),
                                    status: String(payload.status || ''),
                                    output: (payload.output && typeof payload.output === 'object') ? payload.output : {},
                                    error: payload.error ? String(payload.error) : undefined,
                                });
                            }
                            // Legacy format support
                            else if (eventType === "content" && data.delta) {
                                accumulatedContent += String(data.delta || '');
                                setMessages((prev) =>
                                    prev.map(m => m.id === assistantMessage.id
                                        ? { ...m, content: accumulatedContent }
                                        : m
                                    )
                                );
                            }
                        } catch (e) {
                            // JSON parse error - log but don't crash
                            console.debug('[AgentChat] SSE parse error:', e);
                        }
                    }
                }
            }

            // After stream, check for execution intents based on full content if needed
            // (Similar to previous "Interactive Execute Prompt" logic, but now based on actual response)
            // For now, removing the manual simple check or keeping logic simple.

        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: "assistant",
                content: "앗, 차원 이동 중 문제가 생겼어요. 다시 시도해주세요! 🐰",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
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
                whileDrag={{ scale: 1.1, cursor: "grabbing" }}
                className="fixed bottom-8 left-1/2 z-50 pointer-events-auto"
                style={{
                    x: fabPosition.x,
                    y: fabPosition.y,
                    translateX: "-50%"
                }}
                onDragStart={() => {
                    // Mark as dragging to prevent click
                    (window as unknown as { __chokkiDragging: boolean }).__chokkiDragging = true;
                }}
                onDragEnd={(_, info) => {
                    setFabPosition(prev => ({
                        x: prev.x + info.offset.x,
                        y: prev.y + info.offset.y
                    }));
                    // Reset drag flag after a short delay
                    setTimeout(() => {
                        (window as unknown as { __chokkiDragging: boolean }).__chokkiDragging = false;
                    }, 100);
                }}
            >
                <button
                    onClick={() => {
                        // Ignore click if we were just dragging
                        if ((window as unknown as { __chokkiDragging: boolean }).__chokkiDragging) return;
                        setIsOpen(!isOpen);
                    }}
                    className="relative group cursor-grab active:cursor-grabbing focus:outline-none"
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

            {/* Chat Panel */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 pointer-events-auto w-[380px] h-[600px] flex flex-col bg-black/90 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden"
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

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-5 space-y-6 scrollbar-thin scrollbar-thumb-zinc-700/50 scrollbar-track-transparent">
                            {messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""
                                        }`}
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
                                        <span className={`text-[10px] font-medium px-1 ${message.role === "assistant" ? "text-zinc-500" : "text-violet-300 text-right"
                                            }`}>
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
                            ))}

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

