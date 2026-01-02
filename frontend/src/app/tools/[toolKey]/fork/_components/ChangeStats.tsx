"use client";

/**
 * Change Statistics Panel
 * Shows diff stats: lines added, removed, modified, similarity
 */

import { Info } from "lucide-react";

interface DiffStats {
    lines_added: number;
    lines_removed: number;
    lines_modified: number;
    similarity_ratio: number;
    diff_score: number;
    is_trivial: boolean;
}

interface ChangeStatsProps {
    stats: DiffStats;
}

export function ChangeStats({ stats }: ChangeStatsProps) {
    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Info className="w-4 h-4 text-gray-400" />
                Change Statistics
            </h4>
            <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                    <span className="text-gray-400">Lines Added</span>
                    <span className="text-green-400 font-mono">+{stats.lines_added}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-400">Lines Removed</span>
                    <span className="text-red-400 font-mono">-{stats.lines_removed}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-400">Lines Modified</span>
                    <span className="text-yellow-400 font-mono">~{stats.lines_modified}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-gray-700 mt-2">
                    <span className="text-gray-400">Similarity</span>
                    <span className="text-purple-400 font-mono">
                        {(stats.similarity_ratio * 100).toFixed(1)}%
                    </span>
                </div>
            </div>
        </div>
    );
}
