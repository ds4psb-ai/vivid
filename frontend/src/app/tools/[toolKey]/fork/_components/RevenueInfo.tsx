"use client";

/**
 * Revenue Sharing Info Panel
 */

import { TrendingUp } from "lucide-react";

export function RevenueInfo() {
    return (
        <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-xl p-5">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-purple-400" />
                Revenue Sharing
            </h4>
            <p className="text-sm text-gray-300 mb-3">
                When users run your fork, you earn based on your attribution score:
            </p>
            <ul className="text-sm text-gray-400 space-y-1">
                <li>• <span className="text-green-400">75+</span>: You get 75% of creator pool</li>
                <li>• <span className="text-blue-400">50-74</span>: You get 50%</li>
                <li>• <span className="text-yellow-400">25-49</span>: You get 25%</li>
                <li>• <span className="text-red-400">&lt;25</span>: Only 10% (Sybil flag)</li>
            </ul>
        </div>
    );
}
