"use client";

import { memo, useState, useCallback } from "react";
import { Node } from "@xyflow/react";
import { motion, AnimatePresence } from "framer-motion";
import {
    X,
    Play,
    Loader2,
    CheckCircle2,
    AlertTriangle,
    Upload,
    FileText,
    Wand2,
    Download,
    RefreshCcw,
    ShieldCheck,
    Layers,
    Settings,
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { CanvasNodeData } from "@/components/canvas/CustomNodes";

// Utility function for merging class names
function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Category-specific configurations
const CATEGORY_CONFIG = {
    input: {
        icon: Upload,
        color: "yellow",
        gradient: "from-yellow-400 to-amber-500",
    },
    generate: {
        icon: Wand2,
        color: "blue",
        gradient: "from-blue-400 to-blue-600",
    },
    refine: {
        icon: RefreshCcw,
        color: "amber",
        gradient: "from-amber-400 to-orange-500",
    },
    validate: {
        icon: ShieldCheck,
        color: "teal",
        gradient: "from-teal-400 to-cyan-500",
    },
    compose: {
        icon: Layers,
        color: "indigo",
        gradient: "from-indigo-400 to-purple-500",
    },
    output: {
        icon: Download,
        color: "emerald",
        gradient: "from-emerald-400 to-teal-500",
    },
} as const;

type NodeCategory = keyof typeof CATEGORY_CONFIG;

interface NodeDetailPanelProps {
    node: Node<CanvasNodeData> | null;
    onClose: () => void;
    onExecute?: (nodeId: string, inputData: Record<string, unknown>) => Promise<void>;
    isExecuting?: boolean;
}

function NodeDetailPanelBase({ node, onClose, onExecute, isExecuting = false }: NodeDetailPanelProps) {
    const [inputValue, setInputValue] = useState("");
    const [executionStatus, setExecutionStatus] = useState<"idle" | "loading" | "complete" | "error">("idle");

    const category = (node?.data?.category as NodeCategory) || "generate";
    const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.generate;
    const CategoryIcon = config.icon;

    const handleExecute = useCallback(async () => {
        if (!node || !onExecute) return;

        setExecutionStatus("loading");
        try {
            await onExecute(node.id, { text: inputValue });
            setExecutionStatus("complete");
        } catch {
            setExecutionStatus("error");
        }
    }, [node, onExecute, inputValue]);

    if (!node) return null;

    const { data } = node;
    const nodeLabel = data.label || "Node";
    const nodeDescription = data.description || "";

    return (
        <AnimatePresence>
            <motion.div
                initial={{ x: "100%", opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: "100%", opacity: 0 }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className="fixed right-0 top-0 h-full w-[var(--layout-detail-panel-width)] bg-[#0a0a0c]/95 backdrop-blur-2xl border-l border-white/10 z-50 overflow-hidden"
            >
                {/* Header */}
                <div className="p-6 border-b border-white/10">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div
                                className={cn(
                                    "flex h-10 w-10 items-center justify-center rounded-xl",
                                    `bg-gradient-to-br ${config.gradient}`
                                )}
                            >
                                <CategoryIcon className="h-5 w-5 text-white" strokeWidth={2} />
                            </div>
                            <div>
                                <div className={cn(
                                    "text-[10px] font-bold uppercase tracking-widest mb-0.5",
                                    `text-${config.color}-400`
                                )}>
                                    {category}
                                </div>
                                <h2 className="text-lg font-bold text-slate-100">{nodeLabel}</h2>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        >
                            <X className="h-5 w-5 text-slate-400" />
                        </button>
                    </div>

                    {nodeDescription && (
                        <p className="text-sm text-slate-400">{nodeDescription}</p>
                    )}
                </div>

                {/* Content based on category */}
                <div className="p-6 space-y-6 overflow-y-auto h-[calc(100%_-_var(--layout-rail-offset-lg))]">
                    {/* INPUT category - Show input form */}
                    {category === "input" && (
                        <div className="space-y-4">
                            <label className="block">
                                <span className="text-sm font-medium text-slate-300 mb-2 block">
                                    스토리 입력
                                </span>
                                <textarea
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder={(data.data as Record<string, unknown>)?.hint as string || "내용을 입력하세요..."}
                                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/20 resize-none"
                                />
                            </label>

                            <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
                                <Upload className="h-5 w-5 text-yellow-400" />
                                <span className="text-sm text-slate-300">파일 업로드</span>
                                <button className="ml-auto px-3 py-1.5 text-xs font-medium bg-yellow-500/20 text-yellow-300 rounded-lg hover:bg-yellow-500/30 transition-colors">
                                    찾아보기
                                </button>
                            </div>
                        </div>
                    )}

                    {/* GENERATE category - Show AI model info and parameters */}
                    {category === "generate" && (
                        <div className="space-y-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <div className="flex items-center gap-3 mb-3">
                                    <Wand2 className="h-5 w-5 text-blue-400" />
                                    <span className="text-sm font-medium text-slate-300">AI 모델</span>
                                </div>
                                <div className="text-lg font-bold text-blue-400">
                                    {data.ai_model || "gemini-3-flash-preview"}
                                </div>
                            </div>

                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <div className="flex items-center gap-3 mb-3">
                                    <Settings className="h-4 w-4 text-slate-400" />
                                    <span className="text-sm font-medium text-slate-300">파라미터</span>
                                </div>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Temperature</span>
                                        <span className="text-slate-300">0.8</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Max Tokens</span>
                                        <span className="text-slate-300">4000</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* VALIDATE category - Show validation rules */}
                    {category === "validate" && (
                        <div className="space-y-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <div className="flex items-center gap-3 mb-3">
                                    <ShieldCheck className="h-5 w-5 text-teal-400" />
                                    <span className="text-sm font-medium text-slate-300">검증 규칙</span>
                                </div>
                                <ul className="space-y-2 text-sm text-slate-400">
                                    <li className="flex items-center gap-2">
                                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                        서사 DNA 일관성 검증
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                        톤 & 무드 일치 확인
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                        금지 요소 필터링
                                    </li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* OUTPUT category - Show export options */}
                    {category === "output" && (
                        <div className="space-y-4">
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <div className="flex items-center gap-3 mb-3">
                                    <Download className="h-5 w-5 text-emerald-400" />
                                    <span className="text-sm font-medium text-slate-300">출력 형식</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                    <button className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-sm text-emerald-300 hover:bg-emerald-500/20 transition-colors">
                                        MP4 영상
                                    </button>
                                    <button className="p-3 bg-white/5 border border-white/10 rounded-lg text-sm text-slate-400 hover:bg-white/10 transition-colors">
                                        GIF
                                    </button>
                                    <button className="p-3 bg-white/5 border border-white/10 rounded-lg text-sm text-slate-400 hover:bg-white/10 transition-colors">
                                        이미지 시퀀스
                                    </button>
                                    <button className="p-3 bg-white/5 border border-white/10 rounded-lg text-sm text-slate-400 hover:bg-white/10 transition-colors">
                                        프리미어 XML
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Connection info */}
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                        <div className="flex items-center gap-3 mb-3">
                            <FileText className="h-4 w-4 text-slate-400" />
                            <span className="text-sm font-medium text-slate-300">연결 정보</span>
                        </div>
                        <div className="text-sm text-slate-500">
                            {data.input_handles?.length || 0}개 입력 • {data.output_handles?.length || 0}개 출력
                        </div>
                    </div>
                </div>

                {/* Footer with Execute button */}
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#0a0a0c] to-transparent">
                    <button
                        onClick={handleExecute}
                        disabled={isExecuting || executionStatus === "loading"}
                        className={cn(
                            "w-full py-4 rounded-xl font-bold text-white transition-all",
                            "flex items-center justify-center gap-2",
                            executionStatus === "loading"
                                ? "bg-blue-500/50 cursor-wait"
                                : executionStatus === "complete"
                                    ? "bg-emerald-500 hover:bg-emerald-600"
                                    : executionStatus === "error"
                                        ? "bg-red-500 hover:bg-red-600"
                                        : `bg-gradient-to-r ${config.gradient} hover:opacity-90`
                        )}
                    >
                        {executionStatus === "loading" ? (
                            <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                실행 중...
                            </>
                        ) : executionStatus === "complete" ? (
                            <>
                                <CheckCircle2 className="h-5 w-5" />
                                완료
                            </>
                        ) : executionStatus === "error" ? (
                            <>
                                <AlertTriangle className="h-5 w-5" />
                                오류 발생
                            </>
                        ) : (
                            <>
                                <Play className="h-5 w-5" />
                                노드 실행
                            </>
                        )}
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}

export const NodeDetailPanel = memo(NodeDetailPanelBase);
