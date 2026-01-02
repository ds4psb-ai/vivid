"use client";

/**
 * Attribution Score Indicator
 * Shows fork originality score and estimated revenue share
 */

import { TrendingUp } from "lucide-react";

interface AttributionIndicatorProps {
    score: number;
    isTrivial: boolean;
}

export function AttributionIndicator({ score, isTrivial }: AttributionIndicatorProps) {
    const getScoreColor = () => {
        if (score >= 75) return "text-green-400";
        if (score >= 50) return "text-blue-400";
        if (score >= 25) return "text-yellow-400";
        return "text-red-400";
    };

    const getShareRate = () => {
        if (score >= 75) return "75%";
        if (score >= 50) return "50%";
        if (score >= 25) return "25%";
        return "10%";
    };

    return (
        <div className={`p-4 rounded-lg border ${isTrivial ? "bg-red-500/10 border-red-500/30" : "bg-gray-800/50 border-gray-700"}`}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-purple-400" />
                    <span className="text-sm text-gray-400">Attribution Score</span>
                </div>
                {isTrivial && (
                    <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">⚠️ Sybil</span>
                )}
            </div>
            <div className="flex items-center gap-4">
                <div className={`text-3xl font-bold ${getScoreColor()}`}>{score}</div>
                <div className="flex-1">
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-300 ${isTrivial ? "bg-red-500" : "bg-gradient-to-r from-purple-500 to-blue-500"}`}
                            style={{ width: `${Math.min(100, score)}%` }}
                        />
                    </div>
                </div>
                <div className="text-right">
                    <div className={`text-xl font-bold ${getScoreColor()}`}>{getShareRate()}</div>
                    <div className="text-xs text-gray-500">Revenue Share</div>
                </div>
            </div>
        </div>
    );
}
