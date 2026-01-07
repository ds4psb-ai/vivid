"use client";

/**
 * ChainDataInput - Display and use input data from previous dimensions
 *
 * Shows available chain data from input_dimensions and allows
 * users to apply it to the current dimension.
 */

import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import { THEME_COLOR_CLASSES, type ThemeColor } from "@/lib/dimension-theme";
import { Database, ChevronDown, ChevronUp, Check } from "lucide-react";
import { useState } from "react";

interface ChainDataInputProps {
    /** Current dimension's route key */
    currentDimension: string;
    /** Callback when user selects data to apply */
    onApplyData?: (data: Record<string, ChainData>) => void;
    /** Theme color for styling */
    themeColor?: ThemeColor;
}

export default function ChainDataInput({
    currentDimension,
    onApplyData,
    themeColor = "emerald",
}: ChainDataInputProps) {
    const chainContext = useDimensionChainOptional();
    const [isExpanded, setIsExpanded] = useState(false);
    const [applied, setApplied] = useState(false);
    const colors = THEME_COLOR_CLASSES[themeColor];

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
