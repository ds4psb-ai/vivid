"use client";

/**
 * TeachingCapsuleNode
 * 
 * Agent가 생성한 Teaching 캡슐 노드 컴포넌트.
 * Canvas에서 렌더링되며, 입력 파라미터 수정 및 재실행이 가능합니다.
 */

import { memo, useState, useCallback } from "react";
import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
    Wand2,
    Film,
    Image,
    Search,
    Play,
    RefreshCw,
    Edit3,
    Check,
    X,
    Loader2,
    Coins,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: (string | undefined | null | boolean)[]) {
    return twMerge(clsx(inputs));
}

// ============================================================================
// Types
// ============================================================================

export interface TeachingCapsuleNodeData extends Record<string, unknown> {
    capsule_key: string;
    display_name: string;
    category: "teaching";

    // Input/Output schemas from capsule spec
    input_schema: Record<string, {
        type: string;
        required?: boolean;
        default?: unknown;
        description?: string;
    }>;
    output_schema: Record<string, {
        type: string;
        description?: string;
    }>;
    params_schema?: Record<string, {
        type: string;
        default?: unknown;
        options?: string[];
    }>;

    // Current values
    inputs: Record<string, unknown>;
    locked_inputs: string[];  // Inputs filled by chat
    output: Record<string, unknown>;

    // Execution state
    editable: boolean;
    executed: boolean;
    credit_cost: number;

    // Status
    status?: "idle" | "loading" | "complete" | "error";
    error?: string;

    // Callbacks for React Flow state updates
    onExecuteComplete?: (nodeId: string, output: Record<string, unknown>) => void;
    onInputsChange?: (nodeId: string, inputs: Record<string, unknown>) => void;
}

// ============================================================================
// Icon mapping
// ============================================================================

const CAPSULE_ICONS: Record<string, React.ElementType> = {
    "teaching.prompt.generate": Wand2,
    "teaching.storyboard.create": Film,
    "teaching.image.generate": Image,
    "teaching.reference.analyze": Search,
};

const CAPSULE_COLORS: Record<string, {
    gradient: string;
    border: string;
    text: string;
}> = {
    "teaching.prompt.generate": {
        gradient: "from-violet-500 to-purple-600",
        border: "border-violet-400/50",
        text: "text-violet-100",
    },
    "teaching.storyboard.create": {
        gradient: "from-amber-500 to-orange-600",
        border: "border-amber-400/50",
        text: "text-amber-100",
    },
    "teaching.image.generate": {
        gradient: "from-cyan-500 to-blue-600",
        border: "border-cyan-400/50",
        text: "text-cyan-100",
    },
    "teaching.reference.analyze": {
        gradient: "from-emerald-500 to-teal-600",
        border: "border-emerald-400/50",
        text: "text-emerald-100",
    },
};

// ============================================================================
// Component
// ============================================================================

function TeachingCapsuleNodeBase({
    id,
    data,
    selected
}: NodeProps<Node<TeachingCapsuleNodeData>>) {
    const [isEditing, setIsEditing] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [localInputs, setLocalInputs] = useState<Record<string, unknown>>(
        data.inputs || {}
    );
    const [isExecuting, setIsExecuting] = useState(false);

    const capsuleKey = data.capsule_key || "teaching.prompt.generate";
    const Icon = CAPSULE_ICONS[capsuleKey] || Wand2;
    const colors = CAPSULE_COLORS[capsuleKey] || CAPSULE_COLORS["teaching.prompt.generate"];

    const status = data.status || (data.executed ? "complete" : "idle");
    const creditCost = data.credit_cost || 0;

    // Handle input change
    const handleInputChange = useCallback((key: string, value: unknown) => {
        setLocalInputs(prev => ({ ...prev, [key]: value }));
    }, []);

    // Toggle edit mode and save changes
    const handleToggleEdit = useCallback(() => {
        if (isEditing) {
            // Save changes to React Flow state
            if (data.onInputsChange) {
                data.onInputsChange(id, localInputs);
            }
            setIsEditing(false);
        } else {
            setIsEditing(true);
        }
    }, [isEditing, id, localInputs, data]);

    // Cancel edit
    const handleCancelEdit = useCallback(() => {
        setLocalInputs(data.inputs || {});
        setIsEditing(false);
    }, [data.inputs]);

    // Execute node - calls Teaching API with current inputs
    const handleExecute = useCallback(async () => {
        setIsExecuting(true);
        try {
            // Map capsule_key to endpoint
            const endpointMap: Record<string, string> = {
                "teaching.prompt.generate": "/api/v1/teaching/prompt/generate",
                "teaching.storyboard.create": "/api/v1/teaching/storyboard/create",
                "teaching.image.generate": "/api/v1/teaching/image/generate",
                "teaching.reference.analyze": "/api/v1/teaching/reference/analyze",
            };

            const endpoint = endpointMap[capsuleKey];
            if (!endpoint) {
                console.error(`[TeachingCapsuleNode] Unknown capsule key: ${capsuleKey}`);
                return;
            }

            // Get BYOK key from localStorage if available
            const byokKey = typeof window !== "undefined"
                ? localStorage.getItem("vivid.byok.gemini")
                : null;

            const headers: Record<string, string> = {
                "Content-Type": "application/json",
            };
            if (byokKey) {
                headers["X-Gemini-API-Key"] = byokKey;
            }

            console.log(`[TeachingCapsuleNode] Executing ${capsuleKey}:`, localInputs);

            const response = await fetch(endpoint, {
                method: "POST",
                headers,
                body: JSON.stringify(localInputs),
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[TeachingCapsuleNode] Execution failed:`, errorText);
                return;
            }

            const result = await response.json();
            console.log(`[TeachingCapsuleNode] Execution result:`, result);

            // Update React Flow node state with new output
            if (data.onExecuteComplete) {
                data.onExecuteComplete(id, result.output || result);
            }
        } catch (error) {
            console.error(`[TeachingCapsuleNode] Execution error:`, error);
        } finally {
            setIsExecuting(false);
        }
    }, [capsuleKey, localInputs]);

    // Render input field based on type
    const renderInputField = (
        key: string,
        schema: { type: string; default?: unknown; description?: string },
        value: unknown,
        isLocked: boolean,
    ) => {
        const disabled = !isEditing || isLocked;

        if (schema.type === "integer" || schema.type === "number") {
            return (
                <input
                    type="number"
                    value={String(value ?? schema.default ?? "")}
                    onChange={(e) => handleInputChange(key, Number(e.target.value))}
                    disabled={disabled}
                    className={cn(
                        "w-full px-2 py-1 rounded text-xs bg-white/5 border border-white/10",
                        "text-white placeholder-white/40",
                        disabled ? "opacity-50 cursor-not-allowed" : "hover:border-white/20",
                    )}
                />
            );
        }

        if (schema.type === "array") {
            return (
                <input
                    type="text"
                    value={Array.isArray(value) ? value.join(", ") : String(value ?? "")}
                    onChange={(e) => handleInputChange(key, e.target.value.split(",").map(s => s.trim()))}
                    disabled={disabled}
                    placeholder="comma separated values"
                    className={cn(
                        "w-full px-2 py-1 rounded text-xs bg-white/5 border border-white/10",
                        "text-white placeholder-white/40",
                        disabled ? "opacity-50 cursor-not-allowed" : "hover:border-white/20",
                    )}
                />
            );
        }

        // Default: string
        const strValue = String(value ?? schema.default ?? "");
        const isLongText = strValue.length > 50;

        if (isLongText) {
            return (
                <textarea
                    value={strValue}
                    onChange={(e) => handleInputChange(key, e.target.value)}
                    disabled={disabled}
                    rows={2}
                    className={cn(
                        "w-full px-2 py-1 rounded text-xs bg-white/5 border border-white/10",
                        "text-white placeholder-white/40 resize-none",
                        disabled ? "opacity-50 cursor-not-allowed" : "hover:border-white/20",
                    )}
                />
            );
        }

        return (
            <input
                type="text"
                value={strValue}
                onChange={(e) => handleInputChange(key, e.target.value)}
                disabled={disabled}
                className={cn(
                    "w-full px-2 py-1 rounded text-xs bg-white/5 border border-white/10",
                    "text-white placeholder-white/40",
                    disabled ? "opacity-50 cursor-not-allowed" : "hover:border-white/20",
                )}
            />
        );
    };

    return (
        <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={cn(
                "relative min-w-[280px] max-w-[320px] rounded-xl overflow-hidden",
                "bg-gradient-to-br from-[#1a1a2e] to-[#16162a]",
                "border-2",
                colors.border,
                selected && "ring-2 ring-white/30",
                "shadow-xl shadow-black/30",
            )}
        >
            {/* Input Handle */}
            <Handle
                type="target"
                position={Position.Left}
                className="!w-3 !h-3 !bg-white/80 !border-2 !border-white/40"
            />

            {/* Output Handle */}
            <Handle
                type="source"
                position={Position.Right}
                className="!w-3 !h-3 !bg-white/80 !border-2 !border-white/40"
            />

            {/* Header */}
            <div className={cn(
                "px-3 py-2 bg-gradient-to-r",
                colors.gradient,
            )}>
                <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-white" />
                    <span className="text-sm font-medium text-white truncate flex-1">
                        {data.display_name || "Teaching Capsule"}
                    </span>

                    {/* Status indicator */}
                    {status === "loading" && (
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                    )}
                    {status === "complete" && (
                        <Check className="w-4 h-4 text-white" />
                    )}

                    {/* Credit cost badge */}
                    {creditCost > 0 && (
                        <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-black/20 text-xs text-white/80">
                            <Coins className="w-3 h-3" />
                            {creditCost}
                        </div>
                    )}
                </div>
            </div>

            {/* Body */}
            <div className="p-3 space-y-3">
                {/* Inputs summary (collapsed) */}
                {!isExpanded && (
                    <div className="space-y-1">
                        {Object.entries(data.input_schema || {}).slice(0, 2).map(([key, schema]) => {
                            const value = localInputs[key];
                            const isLocked = (data.locked_inputs || []).includes(key);
                            return (
                                <div key={key} className="flex items-center gap-2 text-xs">
                                    <span className="text-white/50 min-w-[60px] truncate">{key}:</span>
                                    <span className={cn(
                                        "text-white/80 truncate flex-1",
                                        isLocked && "text-yellow-300/80",
                                    )}>
                                        {String(value ?? schema.default ?? "-").slice(0, 30)}
                                        {isLocked && " 🔒"}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Toggle expand button */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center justify-center w-full py-1 text-xs text-white/50 hover:text-white/80 transition-colors"
                >
                    {isExpanded ? (
                        <>
                            <ChevronUp className="w-4 h-4 mr-1" />
                            접기
                        </>
                    ) : (
                        <>
                            <ChevronDown className="w-4 h-4 mr-1" />
                            펼치기
                        </>
                    )}
                </button>

                {/* Expanded inputs */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="space-y-2 overflow-hidden"
                        >
                            {Object.entries(data.input_schema || {}).map(([key, schema]) => {
                                const value = localInputs[key];
                                const isLocked = (data.locked_inputs || []).includes(key);
                                return (
                                    <div key={key} className="space-y-1">
                                        <label className="flex items-center gap-1 text-xs text-white/60">
                                            {key}
                                            {schema.required && <span className="text-red-400">*</span>}
                                            {isLocked && <span className="text-yellow-400">🔒</span>}
                                        </label>
                                        {renderInputField(key, schema, value, isLocked)}
                                    </div>
                                );
                            })}

                            {/* Output preview */}
                            {data.executed && Object.keys(data.output || {}).length > 0 && (
                                <div className="mt-3 pt-3 border-t border-white/10">
                                    <div className="text-xs text-white/50 mb-2">출력:</div>
                                    <div className="p-2 rounded bg-white/5 text-xs text-white/70 max-h-24 overflow-y-auto">
                                        <pre className="whitespace-pre-wrap">
                                            {JSON.stringify(data.output, null, 2).slice(0, 200)}
                                            {JSON.stringify(data.output).length > 200 && "..."}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2 border-t border-white/10">
                    {isEditing ? (
                        <>
                            <button
                                onClick={handleToggleEdit}
                                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded bg-green-500/20 text-green-300 text-xs hover:bg-green-500/30 transition-colors"
                            >
                                <Check className="w-3 h-3" />
                                저장
                            </button>
                            <button
                                onClick={handleCancelEdit}
                                className="flex items-center justify-center px-2 py-1.5 rounded bg-white/5 text-white/60 text-xs hover:bg-white/10 transition-colors"
                            >
                                <X className="w-3 h-3" />
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={handleToggleEdit}
                                disabled={!data.editable}
                                className={cn(
                                    "flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors",
                                    data.editable
                                        ? "bg-white/5 text-white/70 hover:bg-white/10"
                                        : "bg-white/5 text-white/30 cursor-not-allowed",
                                )}
                            >
                                <Edit3 className="w-3 h-3" />
                                수정
                            </button>
                            <button
                                onClick={handleExecute}
                                disabled={isExecuting}
                                className={cn(
                                    "flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors",
                                    "bg-gradient-to-r",
                                    colors.gradient,
                                    "text-white hover:opacity-90",
                                    isExecuting && "opacity-50 cursor-not-allowed",
                                )}
                            >
                                {isExecuting ? (
                                    <>
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                        실행 중...
                                    </>
                                ) : (
                                    <>
                                        <RefreshCw className="w-3 h-3" />
                                        재실행
                                    </>
                                )}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

export const TeachingCapsuleNode = memo(TeachingCapsuleNodeBase);
export default TeachingCapsuleNode;
