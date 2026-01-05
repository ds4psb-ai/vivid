"use client";

import { useState, useRef, useCallback } from "react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TrainWorkflowView, TrainWorkflowHandle } from "@/components/train/TrainWorkflowView";
import { AgentChatAccordion } from "@/components/AgentChatAccordion";
import { useLanguage } from "@/contexts/LanguageContext";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Copy, Check, Sparkles, LayoutGrid, Image as ImageIcon, Film, X, Download, Save, CheckCircle, Palette, Moon, Video } from "lucide-react";
import { api } from "@/lib/api";

// Tool ID to dimension info mapping
const TOOL_TO_DIMENSION: Record<string, { displayName: string; icon: string; color: string; dimension: string }> = {
    "generate_veo_prompt": { displayName: "Veo 프롬프트 생성기", icon: "sparkles", color: "violet", dimension: "1D" },
    "create_storyboard": { displayName: "스토리보드 생성기", icon: "layout-grid", color: "emerald", dimension: "2D" },
    "generate_image_prompt": { displayName: "이미지 프롬프트 생성기", icon: "image", color: "amber", dimension: "3D" },
    "analyze_reference": { displayName: "레퍼런스 분석기", icon: "film", color: "cyan", dimension: "4D" },
    // Extended Dimension Capsules
    "quality_check": { displayName: "퀄리티 검수기", icon: "check-circle", color: "rose", dimension: "QC" },
    "aesthetic_direct": { displayName: "미학디렉터", icon: "palette", color: "fuchsia", dimension: "AD" },
    "persona_analyze": { displayName: "심연해석기", icon: "moon", color: "indigo", dimension: "AI" },
    "veo_generate": { displayName: "Veo 3.1 비디오", icon: "video", color: "sky", dimension: "VEO" },
};

// Icon components
const ICON_COMPONENTS: Record<string, React.ReactNode> = {
    sparkles: <Sparkles className="h-5 w-5" />,
    "layout-grid": <LayoutGrid className="h-5 w-5" />,
    image: <ImageIcon className="h-5 w-5" />,
    film: <Film className="h-5 w-5" />,
    // Extended Dimension Capsules
    "check-circle": <CheckCircle className="h-5 w-5" />,
    palette: <Palette className="h-5 w-5" />,
    moon: <Moon className="h-5 w-5" />,
    video: <Video className="h-5 w-5" />,
};

// Workflow result type
interface WorkflowResult {
    dimension: string;
    dimensionName: string;
    toolName: string;
    inputs: Record<string, unknown>;  // 🆕 Added: input prompts/options
    output: Record<string, unknown>;
    creditCost?: number;
    executedAt: Date;  // 🆕 Added: execution timestamp
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

// 🆕 Download utility functions
function downloadFile(content: string, filename: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadResultAsJSON(result: WorkflowResult) {
    const data = {
        dimension: result.dimension,
        dimensionName: result.dimensionName,
        toolName: result.toolName,
        inputs: result.inputs,
        output: result.output,
        executedAt: result.executedAt?.toISOString(),
    };
    downloadFile(
        JSON.stringify(data, null, 2),
        `${result.dimension}-${result.toolName}.json`,
        'application/json'
    );
}

function downloadResultAsMarkdown(result: WorkflowResult) {
    let md = `# ${result.dimension} - ${result.dimensionName}\n\n`;
    md += `**도구**: ${result.toolName}\n`;
    md += `**실행 시간**: ${result.executedAt?.toLocaleString('ko-KR')}\n\n`;

    if (Object.keys(result.inputs).length > 0) {
        md += `## 입력\n\n`;
        Object.entries(result.inputs).forEach(([key, value]) => {
            md += `### ${key.replace(/_/g, ' ')}\n${typeof value === 'string' ? value : JSON.stringify(value, null, 2)}\n\n`;
        });
    }

    md += `## 출력\n\n`;
    Object.entries(result.output).forEach(([key, value]) => {
        md += `### ${key.replace(/_/g, ' ')}\n`;
        if (typeof value === 'string') {
            md += `${value}\n\n`;
        } else {
            md += `\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\`\n\n`;
        }
    });

    downloadFile(md, `${result.dimension}-${result.toolName}.md`, 'text/markdown');
}

export default function FlowPage() {
    const [workflowResults, setWorkflowResults] = useState<WorkflowResult[]>([]);
    const [showResults, setShowResults] = useState(false);
    const [expandedResult, setExpandedResult] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);

    // 🆕 Template save modal state
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [templateTitle, setTemplateTitle] = useState("");
    const [templateDescription, setTemplateDescription] = useState("");
    const [templateTags, setTemplateTags] = useState("");
    const [isSavingTemplate, setIsSavingTemplate] = useState(false);
    const [templateSaveSuccess, setTemplateSaveSuccess] = useState(false);
    const [savedTemplateId, setSavedTemplateId] = useState<string | null>(null);  // 🆕 For singularity link
    const [templateSaveError, setTemplateSaveError] = useState<string | null>(null);  // 🆕 Inline error

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

    // 🆕 Save workflow results as template
    const handleSaveAsTemplate = async () => {
        if (workflowResults.length === 0 || !templateTitle.trim()) return;

        setIsSavingTemplate(true);
        try {
            // Merge all inputs and outputs from workflow results
            const mergedInputs: Record<string, unknown> = {};
            const mergedOutputs: Record<string, unknown> = {};

            workflowResults.forEach(result => {
                Object.entries(result.inputs).forEach(([k, v]) => { mergedInputs[k] = v; });
                Object.entries(result.output).forEach(([k, v]) => { mergedOutputs[k] = v; });
            });

            const response = await api.createSingularityTemplate({
                title: templateTitle.trim(),
                description: templateDescription.trim() || `${workflowResults.length}개 차원 워크플로우 템플릿`,
                dimension_source: workflowResults[0]?.dimension || "1D",
                tool_sequence: workflowResults.map(r => r.toolName),
                input_preset: mergedInputs,
                output_example: mergedOutputs,
                tags: templateTags.split(",").map(t => t.trim()).filter(Boolean),
                category: "user_created",
            });

            console.log("[Flow] Template saved:", response);
            setSavedTemplateId(response.id);  // 🆕 Store for singularity link
            setTemplateSaveSuccess(true);
            setTemplateSaveError(null);
            // Auto-close after 5 seconds (longer for user to see link)
            setTimeout(() => {
                setShowTemplateModal(false);
                setTemplateSaveSuccess(false);
                setSavedTemplateId(null);
                setTemplateTitle("");
                setTemplateDescription("");
                setTemplateTags("");
            }, 5000);
        } catch (err) {
            console.error("[Flow] Template save failed:", err);
            setTemplateSaveError(err instanceof Error ? err.message : "템플릿 저장에 실패했습니다. 다시 시도해주세요.");
        } finally {
            setIsSavingTemplate(false);
        }
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
                dimension: (toolInfo.dimension || event.dimension) as "1D" | "2D" | "3D" | "4D",
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
        arguments?: Record<string, unknown>;  // 🔧 Fixed: matches AgentChatAccordion
    }) => {
        console.log("[Flow] Tool result:", result);

        // Defensive: validate result
        if (!result || typeof result !== 'object') {
            console.warn('[Flow] Invalid tool result');
            return;
        }

        const { name, status, output, arguments: toolArguments } = result;

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

        // Extract inputs (from 'arguments' field sent by backend)
        const safeInputs = (toolArguments && typeof toolArguments === 'object' && !Array.isArray(toolArguments))
            ? toolArguments
            : {};

        const toolInfo = TOOL_TO_DIMENSION[name];

        setWorkflowResults(prev => {
            try {
                // Avoid duplicates
                if (prev.some(r => r.toolName === name)) {
                    return prev.map(r => r.toolName === name
                        ? { ...r, output: safeOutput, inputs: safeInputs }
                        : r
                    );
                }
                return [...prev, {
                    dimension: toolInfo.dimension,
                    dimensionName: toolInfo.displayName,
                    toolName: name,
                    inputs: safeInputs,
                    output: safeOutput,
                    executedAt: new Date(),
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
                                                <div className="flex items-center gap-2">
                                                    {/* 🆕 Save as Template Button */}
                                                    <button
                                                        onClick={() => setShowTemplateModal(true)}
                                                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 text-xs font-medium transition-colors"
                                                    >
                                                        <Save className="h-3.5 w-3.5" />
                                                        템플릿 저장
                                                    </button>
                                                    <button
                                                        onClick={() => setShowResults(false)}
                                                        className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                                                    >
                                                        <X className="h-4 w-4 text-[var(--fg-muted)]" />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Results List */}
                                            <div className="space-y-4">
                                                {workflowResults.map((result) => {
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
                                                                        ${toolInfo?.color === "rose" ? "bg-rose-500/20 text-rose-400" : ""}
                                                                        ${toolInfo?.color === "fuchsia" ? "bg-fuchsia-500/20 text-fuchsia-400" : ""}
                                                                        ${toolInfo?.color === "indigo" ? "bg-indigo-500/20 text-indigo-400" : ""}
                                                                        ${toolInfo?.color === "sky" ? "bg-sky-500/20 text-sky-400" : ""}
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
                                                                <div className="flex items-center gap-2">
                                                                    {/* 🆕 Download Buttons */}
                                                                    <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                                                                        <button
                                                                            onClick={() => downloadResultAsJSON(result)}
                                                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                                                                            title="JSON으로 다운로드"
                                                                        >
                                                                            <Download className="h-3.5 w-3.5 text-zinc-400" />
                                                                        </button>
                                                                        <button
                                                                            onClick={() => downloadResultAsMarkdown(result)}
                                                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                                                                            title="Markdown으로 다운로드"
                                                                        >
                                                                            <span className="text-[10px] font-bold text-zinc-400">MD</span>
                                                                        </button>
                                                                    </div>
                                                                    <ChevronDown
                                                                        className={`h-5 w-5 text-[var(--fg-muted)] transition-transform ${isExpanded ? "rotate-180" : ""}`}
                                                                    />
                                                                </div>
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
                                                                            {/* 🆕 Inputs Section */}
                                                                            {result.inputs && Object.keys(result.inputs).length > 0 && (
                                                                                <details className="group">
                                                                                    <summary className="text-xs font-medium text-violet-400 cursor-pointer hover:text-violet-300 transition-colors flex items-center gap-1.5">
                                                                                        <span>📝 입력 프롬프트</span>
                                                                                        <ChevronDown className="h-3 w-3 group-open:rotate-180 transition-transform" />
                                                                                    </summary>
                                                                                    <div className="mt-2 p-3 bg-violet-500/5 border border-violet-500/20 rounded-lg space-y-2">
                                                                                        {Object.entries(result.inputs).map(([key, value]) => (
                                                                                            <div key={key}>
                                                                                                <span className="text-[10px] text-violet-300/70 uppercase tracking-wider">{key.replace(/_/g, " ")}</span>
                                                                                                <p className="text-xs text-[var(--fg-0)]">
                                                                                                    {typeof value === "string" ? value : JSON.stringify(value)}
                                                                                                </p>
                                                                                            </div>
                                                                                        ))}
                                                                                    </div>
                                                                                </details>
                                                                            )}

                                                                            {/* Outputs Section */}
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

                {/* 🆕 Template Save Modal */}
                <AnimatePresence>
                    {showTemplateModal && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                            onClick={() => setShowTemplateModal(false)}
                        >
                            <motion.div
                                initial={{ scale: 0.95, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.95, opacity: 0 }}
                                onClick={e => e.stopPropagation()}
                                className="w-full max-w-md mx-4 bg-black/60 backdrop-blur-xl border border-white/10 rounded-[1.5rem] shadow-2xl overflow-hidden"
                            >
                                {/* Modal Header */}
                                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
                                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                        <Save className="h-5 w-5 text-violet-400" />
                                        싱귤래리티 템플릿 저장
                                    </h3>
                                    <button
                                        onClick={() => setShowTemplateModal(false)}
                                        className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                                    >
                                        <X className="h-4 w-4 text-zinc-400" />
                                    </button>
                                </div>

                                {/* Modal Body */}
                                <div className="p-6 space-y-4">
                                    {templateSaveSuccess ? (
                                        <div className="text-center py-8">
                                            <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                                                <Check className="h-8 w-8 text-emerald-400" />
                                            </div>
                                            <p className="text-lg font-medium text-white">템플릿 저장 완료!</p>
                                            <p className="text-sm text-zinc-400 mt-1 mb-4">싱귤래리티에서 확인하세요</p>

                                            {/* Singularity & Constellation Links */}
                                            <div className="flex flex-col gap-2">
                                                <a
                                                    href="/singularity"
                                                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
                                                >
                                                    <Sparkles className="h-4 w-4" />
                                                    싱귤래리티로 이동
                                                </a>
                                                {savedTemplateId && (
                                                    <a
                                                        href={`/constellation?new=true&singularity=${savedTemplateId}`}
                                                        className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium transition-colors"
                                                    >
                                                        <Sparkles className="h-4 w-4" />
                                                        별자리로 확장하기
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <div>
                                                <label className="text-xs font-medium text-zinc-400 mb-1.5 block">
                                                    템플릿 제목 *
                                                </label>
                                                <input
                                                    type="text"
                                                    value={templateTitle}
                                                    onChange={e => setTemplateTitle(e.target.value)}
                                                    placeholder="예: 시네마틱 프롬프트 워크플로우"
                                                    className="w-full px-4 py-2.5 rounded-lg bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-medium text-zinc-400 mb-1.5 block">
                                                    설명
                                                </label>
                                                <textarea
                                                    value={templateDescription}
                                                    onChange={e => setTemplateDescription(e.target.value)}
                                                    placeholder="워크플로우 템플릿에 대한 설명을 입력하세요"
                                                    rows={3}
                                                    className="w-full px-4 py-2.5 rounded-lg bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50 resize-none"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-medium text-zinc-400 mb-1.5 block">
                                                    태그 (쉼표로 구분)
                                                </label>
                                                <input
                                                    type="text"
                                                    value={templateTags}
                                                    onChange={e => setTemplateTags(e.target.value)}
                                                    placeholder="예: cinematic, veo, prompt"
                                                    className="w-full px-4 py-2.5 rounded-lg bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50"
                                                />
                                            </div>

                                            {/* Workflow Summary */}
                                            <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
                                                <p className="text-xs text-violet-300 font-medium mb-1">포함된 도구</p>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {workflowResults.map(r => (
                                                        <span key={r.toolName} className="px-2 py-0.5 rounded-md bg-violet-500/20 text-xs text-violet-200">
                                                            {r.dimension}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Modal Footer */}
                                {!templateSaveSuccess && (
                                    <div className="px-6 py-4 border-t border-white/5 space-y-3">
                                        {/* 🆕 Inline Error Display */}
                                        {templateSaveError && (
                                            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                                                <span className="text-red-400 text-xs">⚠️</span>
                                                <span className="text-xs text-red-300 flex-1">{templateSaveError}</span>
                                                <button
                                                    onClick={() => setTemplateSaveError(null)}
                                                    className="text-red-400 hover:text-red-300 text-xs"
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                        )}
                                        <div className="flex justify-end gap-3">
                                            <button
                                                onClick={() => setShowTemplateModal(false)}
                                                className="px-4 py-2 rounded-lg text-sm text-zinc-400 hover:bg-white/5 transition-colors"
                                            >
                                                취소
                                            </button>
                                            <button
                                                onClick={handleSaveAsTemplate}
                                                disabled={!templateTitle.trim() || isSavingTemplate}
                                                className="px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm font-medium transition-colors flex items-center gap-2"
                                            >
                                                {isSavingTemplate ? (
                                                    <>
                                                        <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                        저장 중...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Save className="h-4 w-4" />
                                                        저장
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </AppShell>
    );
}
