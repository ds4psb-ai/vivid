"use client";

import { useState, useRef, useCallback } from "react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TrainWorkflowView, TrainWorkflowHandle } from "@/components/train/TrainWorkflowView";
import { AgentChatAccordion } from "@/components/AgentChatAccordion";
import { useLanguage } from "@/contexts/LanguageContext";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Copy, Check, Sparkles, LayoutGrid, Image as ImageIcon, Film, X } from "lucide-react";

// Tool ID to dimension info mapping
const TOOL_TO_DIMENSION: Record<string, { displayName: string; icon: string; color: string; dimension: string }> = {
    "generate_veo_prompt": { displayName: "Veo 프롬프트 생성기", icon: "sparkles", color: "violet", dimension: "1D" },
    "create_storyboard": { displayName: "스토리보드 생성기", icon: "layout-grid", color: "emerald", dimension: "2D" },
    "generate_image_prompt": { displayName: "이미지 프롬프트 생성기", icon: "image", color: "amber", dimension: "3D" },
    "analyze_reference": { displayName: "레퍼런스 분석기", icon: "film", color: "cyan", dimension: "4D" },
};

// Icon components
const ICON_COMPONENTS: Record<string, React.ReactNode> = {
    sparkles: <Sparkles className="h-5 w-5" />,
    "layout-grid": <LayoutGrid className="h-5 w-5" />,
    image: <ImageIcon className="h-5 w-5" />,
    film: <Film className="h-5 w-5" />,
};

// Workflow result type
interface WorkflowResult {
    dimension: string;
    dimensionName: string;
    toolName: string;
    output: Record<string, unknown>;
    creditCost?: number;
}

// Safe JSON stringify to handle circular references and large objects
function safeStringify(value: unknown, maxLength = 5000): string {
    const seen = new WeakSet();
    try {
        const result = JSON.stringify(value, (key, val) => {
            // Handle circular references
            if (typeof val === 'object' && val !== null) {
                if (seen.has(val)) {
                    return '[Circular]';
                }
                seen.add(val);
            }
            // Truncate very long strings
            if (typeof val === 'string' && val.length > 1000) {
                return val.slice(0, 1000) + '...';
            }
            return val;
        }, 2);

        // Truncate overall result if too long
        if (result && result.length > maxLength) {
            return result.slice(0, maxLength) + '\n...(truncated)';
        }
        return result || '(empty)';
    } catch {
        return '(serialization error)';
    }
}

export default function FlowPage() {
    const [isExecuting, setIsExecuting] = useState(false);
    const [workflowResults, setWorkflowResults] = useState<WorkflowResult[]>([]);
    const [showResults, setShowResults] = useState(false);
    const [expandedResult, setExpandedResult] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);
    const workflowRef = useRef<TrainWorkflowHandle>(null);
    const { language } = useLanguage();

    // Track agent-created cars for updating status
    const carIdMapRef = useRef<Map<number, string>>(new Map());

    const labels = {
        badge: language === "ko" ? "디멘션 플로우" : "Dimension Flow",
        initialMessage: language === "ko"
            ? "안녕하세요! 차원 흐름을 함께 설계해드릴게요. 어떤 콘텐츠를 만들고 싶으신가요?"
            : "Hello! I'll help you design dimension flows. What content would you like to create?",
        results: language === "ko" ? "워크플로우 결과물" : "Workflow Results",
        copySuccess: language === "ko" ? "복사됨!" : "Copied!",
    };

    const handleExecuteAll = async () => {
        setIsExecuting(true);
        if (workflowRef.current) {
            await workflowRef.current.executeAll();
        }
        setIsExecuting(false);
    };

    // Copy to clipboard with error handling
    const copyToClipboard = async (text: string, fieldId: string) => {
        try {
            if (!text || typeof text !== 'string') return;
            await navigator.clipboard.writeText(text);
            setCopiedField(fieldId);
            setTimeout(() => setCopiedField(null), 2000);
        } catch (err) {
            console.error('[Flow] Clipboard copy failed:', err);
            // Fallback: try execCommand (legacy)
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                setCopiedField(fieldId);
                setTimeout(() => setCopiedField(null), 2000);
            } catch {
                // Silent fail
            }
        }
    };

    // === Agent Workflow Event Handlers ===

    const handleWorkflowStart = useCallback((data: { topic: string; dimensions: string[]; total_steps: number }) => {
        console.log("[Flow] Workflow started:", data);

        // Defensive: validate data
        if (!data || typeof data !== 'object') {
            console.warn('[Flow] Invalid workflow start data');
            return;
        }

        // Clear existing cars and results
        try {
            if (workflowRef.current) {
                workflowRef.current.clearCars();
            }
            carIdMapRef.current.clear();
            setWorkflowResults([]);
            setShowResults(false);
            setIsExecuting(true);
            setExpandedResult(null);
        } catch (err) {
            console.error('[Flow] Error clearing workflow state:', err);
        }
    }, []);

    const handleWorkflowStep = useCallback((event: {
        step: number;
        dimension: string;
        dimension_name: string;
        tool_name: string;
        status?: "start" | "complete" | "error";
        output_preview?: string;
        credit_cost?: number;
    }) => {
        console.log("[Flow] Workflow step:", event);

        if (!workflowRef.current) return;

        const toolInfo = TOOL_TO_DIMENSION[event.tool_name] || {
            displayName: event.dimension_name,
            icon: "zap",
            color: "zinc",
            dimension: event.dimension,
        };

        if (event.status === "start") {
            // Add new car with executing status
            const carId = workflowRef.current.addCar({
                toolId: event.tool_name,
                displayName: toolInfo.displayName,
                icon: toolInfo.icon,
                color: toolInfo.color,
                status: "executing",
                inputs: {},
            });
            // Track car ID by step number
            carIdMapRef.current.set(event.step, carId);
        } else if (event.status === "complete") {
            // Update existing car to completed
            const carId = carIdMapRef.current.get(event.step);
            if (carId) {
                workflowRef.current.updateCarStatus(carId, "completed", {
                    preview: event.output_preview,
                    credit_cost: event.credit_cost,
                });
            }
        } else if (event.status === "error") {
            // Update existing car to failed
            const carId = carIdMapRef.current.get(event.step);
            if (carId) {
                workflowRef.current.updateCarStatus(carId, "failed");
            }
        }
    }, []);

    const handleWorkflowComplete = useCallback((data: { total_credits: number; success_count: number }) => {
        console.log("[Flow] Workflow completed:", data);
        setIsExecuting(false);
        // Show results panel if there are results
        if (data.success_count > 0) {
            setShowResults(true);
        }
    }, []);

    // Handle tool result from agent
    const handleToolResult = useCallback((result: {
        name: string;
        status: string;
        output: Record<string, unknown>;
    }) => {
        console.log("[Flow] Tool result:", result);

        // Defensive: validate result
        if (!result || typeof result !== 'object') {
            console.warn('[Flow] Invalid tool result');
            return;
        }

        const { name, status, output } = result;

        // Only process workflow tool results
        if (!name || typeof name !== 'string') return;
        if (!TOOL_TO_DIMENSION[name]) return;

        // Accept both 'completed' and 'success' status (case-insensitive)
        const normalizedStatus = (status || '').toLowerCase();
        if (normalizedStatus !== 'completed' && normalizedStatus !== 'success') return;

        // Ensure output is a valid object
        const safeOutput = (output && typeof output === 'object' && !Array.isArray(output))
            ? output
            : {};

        const toolInfo = TOOL_TO_DIMENSION[name];

        setWorkflowResults(prev => {
            try {
                // Avoid duplicates
                if (prev.some(r => r.toolName === name)) {
                    return prev.map(r => r.toolName === name
                        ? { ...r, output: safeOutput }
                        : r
                    );
                }
                return [...prev, {
                    dimension: toolInfo.dimension,
                    dimensionName: toolInfo.displayName,
                    toolName: name,
                    output: safeOutput,
                }];
            } catch (err) {
                console.error('[Flow] Error updating workflow results:', err);
                return prev;
            }
        });
    }, []);

    // Render output value based on type with error handling
    const renderOutputValue = (key: string, value: unknown, resultId: string) => {
        const fieldId = `${resultId}-${key}`;

        // Handle null/undefined
        if (value === null || value === undefined) {
            return <span className="text-xs text-[var(--fg-muted)] italic">(없음)</span>;
        }

        if (typeof value === "string") {
            const displayValue = value.trim() || '(빈 문자열)';
            return (
                <div className="relative group">
                    <div className="p-3 rounded-lg bg-black/30 border border-white/5 text-sm text-[var(--fg-0)] whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {displayValue}
                    </div>
                    {value.trim() && (
                        <button
                            onClick={() => copyToClipboard(value, fieldId)}
                            className="absolute top-2 right-2 p-1.5 rounded-md bg-white/5 opacity-0 group-hover:opacity-100 hover:bg-white/10 transition-all"
                        >
                            {copiedField === fieldId ? (
                                <Check className="h-3.5 w-3.5 text-emerald-400" />
                            ) : (
                                <Copy className="h-3.5 w-3.5 text-[var(--fg-muted)]" />
                            )}
                        </button>
                    )}
                </div>
            );
        }

        if (typeof value === "number" || typeof value === "boolean") {
            return <span className="text-sm text-[var(--fg-0)]">{String(value)}</span>;
        }

        if (Array.isArray(value)) {
            if (value.length === 0) {
                return <span className="text-xs text-[var(--fg-muted)] italic">(빈 배열)</span>;
            }
            return (
                <div className="space-y-2">
                    {value.slice(0, 20).map((item, i) => (
                        <div key={i} className="p-2 rounded-lg bg-black/20 border border-white/5 text-xs text-[var(--fg-muted)] overflow-x-auto">
                            {safeStringify(item)}
                        </div>
                    ))}
                    {value.length > 20 && (
                        <div className="text-xs text-[var(--fg-muted)] italic">...외 {value.length - 20}개 항목</div>
                    )}
                </div>
            );
        }

        if (typeof value === "object" && value !== null) {
            const stringified = safeStringify(value);
            return (
                <div className="p-3 rounded-lg bg-black/30 border border-white/5 text-xs text-[var(--fg-muted)] font-mono whitespace-pre overflow-x-auto max-h-64">
                    {stringified}
                </div>
            );
        }

        return <span className="text-sm text-[var(--fg-0)]">{String(value)}</span>;
    };

    return (
        <AppShell showTopBar={false} showChokki={false}>
            <div className="relative min-h-screen pb-20">
                {/* Aurora Background */}
                <AuroraBackground />

                {/* Content Container */}
                <div className="relative z-10 min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                    <div className="mx-auto max-w-7xl">

                        {/* Minimal Header */}
                        <div className="flex flex-col items-center mb-12">
                            {/* Subtle Badge */}
                            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-sm mb-4">
                                <span className="text-lg">🌊</span>
                                <span className="text-sm font-medium text-[var(--fg-muted)]">
                                    {labels.badge}
                                </span>
                            </div>
                        </div>

                        {/* Main Workflow View */}
                        <div className="card-glass p-1">
                            <div className="overflow-hidden p-6 sm:p-8">
                                <TrainWorkflowView
                                    ref={workflowRef}
                                    onComplete={(results) => {
                                        console.log("Workflow completed:", results);
                                    }}
                                />
                            </div>
                        </div>

                        {/* Workflow Results Panel */}
                        <AnimatePresence>
                            {showResults && workflowResults.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 20 }}
                                    transition={{ duration: 0.3 }}
                                    className="mt-8"
                                >
                                    <div className="card-glass p-1">
                                        <div className="p-6">
                                            {/* Results Header */}
                                            <div className="flex items-center justify-between mb-6">
                                                <h3 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
                                                    <Sparkles className="h-5 w-5 text-violet-400" />
                                                    {labels.results}
                                                    <span className="ml-2 px-2 py-0.5 rounded-full bg-emerald-500/20 text-xs text-emerald-400">
                                                        {workflowResults.length}개 완료
                                                    </span>
                                                </h3>
                                                <button
                                                    onClick={() => setShowResults(false)}
                                                    className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                                                >
                                                    <X className="h-4 w-4 text-[var(--fg-muted)]" />
                                                </button>
                                            </div>

                                            {/* Results List */}
                                            <div className="space-y-4">
                                                {workflowResults.map((result, index) => {
                                                    const isExpanded = expandedResult === result.toolName;
                                                    const toolInfo = TOOL_TO_DIMENSION[result.toolName];
                                                    const Icon = ICON_COMPONENTS[toolInfo?.icon || "sparkles"];

                                                    return (
                                                        <div
                                                            key={result.toolName}
                                                            className="rounded-xl border border-white/5 bg-black/20 overflow-hidden"
                                                        >
                                                            {/* Result Header */}
                                                            <button
                                                                onClick={() => setExpandedResult(isExpanded ? null : result.toolName)}
                                                                className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors"
                                                            >
                                                                <div className="flex items-center gap-3">
                                                                    <div className={`
                                                                        h-10 w-10 rounded-xl flex items-center justify-center
                                                                        ${toolInfo?.color === "violet" ? "bg-violet-500/20 text-violet-400" : ""}
                                                                        ${toolInfo?.color === "emerald" ? "bg-emerald-500/20 text-emerald-400" : ""}
                                                                        ${toolInfo?.color === "amber" ? "bg-amber-500/20 text-amber-400" : ""}
                                                                        ${toolInfo?.color === "cyan" ? "bg-cyan-500/20 text-cyan-400" : ""}
                                                                    `}>
                                                                        {Icon}
                                                                    </div>
                                                                    <div className="text-left">
                                                                        <div className="flex items-center gap-2">
                                                                            <span className="text-xs font-bold text-violet-400">
                                                                                {result.dimension}
                                                                            </span>
                                                                            <span className="text-sm font-medium text-[var(--fg-0)]">
                                                                                {result.dimensionName}
                                                                            </span>
                                                                        </div>
                                                                        <p className="text-xs text-[var(--fg-muted)]">
                                                                            {Object.keys(result.output).length}개 필드 생성됨
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <ChevronDown
                                                                    className={`h-5 w-5 text-[var(--fg-muted)] transition-transform ${isExpanded ? "rotate-180" : ""
                                                                        }`}
                                                                />
                                                            </button>

                                                            {/* Result Content */}
                                                            <AnimatePresence>
                                                                {isExpanded && (
                                                                    <motion.div
                                                                        initial={{ height: 0, opacity: 0 }}
                                                                        animate={{ height: "auto", opacity: 1 }}
                                                                        exit={{ height: 0, opacity: 0 }}
                                                                        transition={{ duration: 0.2 }}
                                                                        className="overflow-hidden"
                                                                    >
                                                                        <div className="p-4 pt-0 space-y-4 border-t border-white/5">
                                                                            {Object.entries(result.output).map(([key, value]) => (
                                                                                <div key={key}>
                                                                                    <label className="text-xs font-medium text-[var(--fg-muted)] uppercase tracking-wider mb-2 block">
                                                                                        {key.replace(/_/g, " ")}
                                                                                    </label>
                                                                                    {renderOutputValue(key, value, result.toolName)}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* Flow-specific Chokki Agent with workflow callbacks */}
                <AgentChatAccordion
                    initialMessage={labels.initialMessage}
                    onWorkflowStart={handleWorkflowStart}
                    onWorkflowStep={handleWorkflowStep}
                    onWorkflowComplete={handleWorkflowComplete}
                    onToolResult={handleToolResult}
                />
            </div>
        </AppShell>
    );
}
