"use client";

/**
 * NextDimensionNav - Navigation component for workflow chaining
 *
 * Shows available next dimensions based on output_dimensions
 * and allows navigation with chain data.
 */

import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { ArrowRight, Link2, CheckCircle } from "lucide-react";

// Align with DimensionPanelLayout ThemeColor
type ThemeColor = "violet" | "cyan" | "emerald" | "amber" | "rose" | "fuchsia" | "indigo" | "sky";

interface NextDimensionNavProps {
    /** Current dimension's route key */
    currentDimension: string;
    /** Whether to show the component (typically after successful generation) */
    show: boolean;
    /** Optional theme color for styling */
    themeColor?: ThemeColor;
}

const colorClasses: Record<ThemeColor, { bg: string; border: string; text: string; button: string; buttonActive: string }> = {
    emerald: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
        text: "text-emerald-400",
        button: "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400",
        buttonActive: "bg-emerald-500 text-black",
    },
    violet: {
        bg: "bg-violet-500/10",
        border: "border-violet-500/20",
        text: "text-violet-400",
        button: "bg-violet-500/20 hover:bg-violet-500/30 text-violet-400",
        buttonActive: "bg-violet-500 text-black",
    },
    amber: {
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
        text: "text-amber-400",
        button: "bg-amber-500/20 hover:bg-amber-500/30 text-amber-400",
        buttonActive: "bg-amber-500 text-black",
    },
    cyan: {
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/20",
        text: "text-cyan-400",
        button: "bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400",
        buttonActive: "bg-cyan-500 text-black",
    },
    rose: {
        bg: "bg-rose-500/10",
        border: "border-rose-500/20",
        text: "text-rose-400",
        button: "bg-rose-500/20 hover:bg-rose-500/30 text-rose-400",
        buttonActive: "bg-rose-500 text-black",
    },
    fuchsia: {
        bg: "bg-fuchsia-500/10",
        border: "border-fuchsia-500/20",
        text: "text-fuchsia-400",
        button: "bg-fuchsia-500/20 hover:bg-fuchsia-500/30 text-fuchsia-400",
        buttonActive: "bg-fuchsia-500 text-black",
    },
    indigo: {
        bg: "bg-indigo-500/10",
        border: "border-indigo-500/20",
        text: "text-indigo-400",
        button: "bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400",
        buttonActive: "bg-indigo-500 text-black",
    },
    sky: {
        bg: "bg-sky-500/10",
        border: "border-sky-500/20",
        text: "text-sky-400",
        button: "bg-sky-500/20 hover:bg-sky-500/30 text-sky-400",
        buttonActive: "bg-sky-500 text-black",
    },
};

export default function NextDimensionNav({
    currentDimension,
    show,
    themeColor = "emerald",
}: NextDimensionNavProps) {
    const chainContext = useDimensionChainOptional();
    const colors = colorClasses[themeColor];

    if (!show || !chainContext) return null;

    const nextDimensions = chainContext.getNextDimensions(currentDimension);

    if (nextDimensions.length === 0) {
        return (
            <div className={`p-4 rounded-xl ${colors.bg} border ${colors.border}`}>
                <div className="flex items-center gap-2">
                    <CheckCircle className={`w-5 h-5 ${colors.text}`} />
                    <span className={`${colors.text} font-medium`}>
                        워크플로우 완료
                    </span>
                </div>
                <p className="text-white/60 text-sm mt-2">
                    모든 단계가 완료되었습니다. 결과물을 확인하세요.
                </p>
            </div>
        );
    }

    return (
        <div className={`p-4 rounded-xl ${colors.bg} border ${colors.border} space-y-3`}>
            <div className="flex items-center gap-2">
                <Link2 className={`w-4 h-4 ${colors.text}`} />
                <span className={`${colors.text} font-medium text-sm`}>
                    다음 차원으로 이동
                </span>
            </div>

            <div className="flex flex-wrap gap-2">
                {nextDimensions.map((dim) => (
                    <button
                        key={dim.key}
                        onClick={() => chainContext.navigateToDimension(dim.key)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all
                                  ${dim.hasData ? colors.buttonActive : colors.button}`}
                    >
                        {dim.name}
                        <ArrowRight className="w-4 h-4" />
                        {dim.hasData && (
                            <span className="text-xs opacity-70">(데이터 있음)</span>
                        )}
                    </button>
                ))}
            </div>

            <p className="text-white/40 text-xs">
                생성된 결과가 다음 차원의 입력으로 자동 연결됩니다.
            </p>
        </div>
    );
}
