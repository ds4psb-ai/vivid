"use client";

/**
 * NextDimensionNav - Navigation component for workflow chaining
 *
 * Shows available next dimensions based on output_dimensions
 * and allows navigation with chain data.
 */

import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { THEME_COLOR_CLASSES, type ThemeColor } from "@/lib/dimension-theme";
import { ArrowRight, Link2, CheckCircle } from "lucide-react";

interface NextDimensionNavProps {
    /** Current dimension's route key */
    currentDimension: string;
    /** Whether to show the component (typically after successful generation) */
    show: boolean;
    /** Optional theme color for styling */
    themeColor?: ThemeColor;
}

export default function NextDimensionNav({
    currentDimension,
    show,
    themeColor = "emerald",
}: NextDimensionNavProps) {
    const chainContext = useDimensionChainOptional();
    const colors = THEME_COLOR_CLASSES[themeColor];

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
