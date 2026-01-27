"use client";

/**
 * ChainDataInput - Display and use input data from previous dimensions
 *
 * Shows available chain data from input_dimensions and allows
 * users to apply it to the current dimension.
 */

import { useDimensionChainOptional, type ChainData } from "@/contexts/DimensionChainContext";
import { safeValidateChainDataRecord } from "@/lib/schemas/chain.schema";
import { THEME_COLOR_CLASSES, type ThemeColor } from "@/lib/dimension-theme";
import { Database, ChevronDown, ChevronUp, Check, AlertCircle } from "lucide-react";
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
    const [applied, setApplied] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isExpanded, setIsExpanded] = useState(true);
    const colors = THEME_COLOR_CLASSES[themeColor];

    const inputData = chainContext?.getInputData(currentDimension) ?? {};
    const availableInputs = Object.entries(inputData);

    // Early returns after all hooks
    if (!chainContext) return null;
    if (availableInputs.length === 0) return null;

    const handleApply = () => {
        if (!onApplyData) return;

        // Clear previous error
        setError(null);

        try {
            // Validate chain data before applying
            const validated = safeValidateChainDataRecord(inputData);
            if (!validated) {
                setError("데이터 형식이 올바르지 않습니다.");
                return;
            }

            onApplyData(inputData);
            setApplied(true);
            setTimeout(() => setApplied(false), 2000);
        } catch (err) {
            console.error("[ChainDataInput] Apply error:", err);
            setError("데이터 적용 중 오류가 발생했습니다.");
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

                    {/* Error message */}
                    {error && (
                        <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/30">
                            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                            <span className="text-red-400 text-xs">{error}</span>
                        </div>
                    )}

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
