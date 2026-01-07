"use client";

/**
 * ChainDataInput - Display and use input data from previous dimensions
 *
 * Shows available chain data from input_dimensions and allows
 * users to apply it to the current dimension.
 */

import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import { Database, ChevronDown, ChevronUp, Check } from "lucide-react";
import { useState } from "react";

// Align with DimensionPanelLayout ThemeColor
type ThemeColor = "violet" | "cyan" | "emerald" | "amber" | "rose" | "fuchsia" | "indigo" | "sky";

interface ChainDataInputProps {
    /** Current dimension's route key */
    currentDimension: string;
    /** Callback when user selects data to apply */
    onApplyData?: (data: Record<string, ChainData>) => void;
    /** Theme color for styling */
    themeColor?: ThemeColor;
}

const colorClasses: Record<ThemeColor, { bg: string; border: string; text: string; button: string }> = {
    emerald: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
        text: "text-emerald-400",
        button: "bg-emerald-500/20 hover:bg-emerald-500/30",
    },
    violet: {
        bg: "bg-violet-500/10",
        border: "border-violet-500/20",
        text: "text-violet-400",
        button: "bg-violet-500/20 hover:bg-violet-500/30",
    },
    amber: {
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
        text: "text-amber-400",
        button: "bg-amber-500/20 hover:bg-amber-500/30",
    },
    cyan: {
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/20",
        text: "text-cyan-400",
        button: "bg-cyan-500/20 hover:bg-cyan-500/30",
    },
    rose: {
        bg: "bg-rose-500/10",
        border: "border-rose-500/20",
        text: "text-rose-400",
        button: "bg-rose-500/20 hover:bg-rose-500/30",
    },
    fuchsia: {
        bg: "bg-fuchsia-500/10",
        border: "border-fuchsia-500/20",
        text: "text-fuchsia-400",
        button: "bg-fuchsia-500/20 hover:bg-fuchsia-500/30",
    },
    indigo: {
        bg: "bg-indigo-500/10",
        border: "border-indigo-500/20",
        text: "text-indigo-400",
        button: "bg-indigo-500/20 hover:bg-indigo-500/30",
    },
    sky: {
        bg: "bg-sky-500/10",
        border: "border-sky-500/20",
        text: "text-sky-400",
        button: "bg-sky-500/20 hover:bg-sky-500/30",
    },
};

export default function ChainDataInput({
    currentDimension,
    onApplyData,
    themeColor = "emerald",
}: ChainDataInputProps) {
    const chainContext = useDimensionChainOptional();
    const [isExpanded, setIsExpanded] = useState(false);
    const [applied, setApplied] = useState(false);
    const colors = colorClasses[themeColor];

    if (!chainContext) return null;

    const inputData = chainContext.getInputData(currentDimension);
    const availableInputs = Object.entries(inputData);

    if (availableInputs.length === 0) return null;

    const handleApply = () => {
        if (onApplyData) {
            onApplyData(inputData);
            setApplied(true);
            setTimeout(() => setApplied(false), 2000);
        }
    };

    const formatTime = (timestamp: number) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
    };

    return (
        <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <Database className={`w-4 h-4 ${colors.text}`} />
                    <span className="text-white/80 text-sm font-medium">
                        이전 차원 데이터 ({availableInputs.length})
                    </span>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-white/40" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-white/40" />
                )}
            </button>

            {/* Expanded content */}
            {isExpanded && (
                <div className="px-4 pb-4 space-y-3">
                    {availableInputs.map(([key, data]) => (
                        <div
                            key={key}
                            className="p-3 rounded-lg bg-white/5 border border-white/10"
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className={`${colors.text} text-sm font-medium`}>
                                    {chainContext.getDimensionName(key)}
                                </span>
                                <span className="text-white/40 text-xs">
                                    {formatTime(data.timestamp)}
                                </span>
                            </div>
                            {data.summary && (
                                <p className="text-white/60 text-xs line-clamp-2">
                                    {data.summary}
                                </p>
                            )}
                        </div>
                    ))}

                    {/* Apply button */}
                    {onApplyData && (
                        <button
                            onClick={handleApply}
                            disabled={applied}
                            className={`w-full py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-all
                                      ${applied
                                    ? "bg-green-500/20 text-green-400"
                                    : `${colors.button} ${colors.text}`
                                }`}
                        >
                            {applied ? (
                                <>
                                    <Check className="w-4 h-4" />
                                    적용됨
                                </>
                            ) : (
                                "데이터 적용하기"
                            )}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
