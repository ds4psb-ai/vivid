/**
 * Stat Card Component
 * 
 * Display statistic with icon, title, and value.
 */

import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color?: "purple" | "blue" | "green" | "yellow" | "red" | "gray";
    subtitle?: string;
    loading?: boolean;
    trend?: {
        value: number;
        direction: "up" | "down";
    };
}

const COLOR_MAP: Record<string, { icon: string; bg: string }> = {
    purple: { icon: "text-purple-400", bg: "bg-purple-500/10" },
    blue: { icon: "text-blue-400", bg: "bg-blue-500/10" },
    green: { icon: "text-green-400", bg: "bg-green-500/10" },
    yellow: { icon: "text-yellow-400", bg: "bg-yellow-500/10" },
    red: { icon: "text-red-400", bg: "bg-red-500/10" },
    gray: { icon: "text-gray-400", bg: "bg-gray-500/10" },
};

export function StatCard({
    title,
    value,
    icon: Icon,
    color = "purple",
    subtitle,
    loading = false,
    trend,
}: StatCardProps) {
    const colors = COLOR_MAP[color];

    return (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 hover:border-gray-600 transition-colors">
            <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-400">{title}</span>
                <div className={`p-2 ${colors.bg} rounded-lg`}>
                    <Icon className={`w-4 h-4 ${colors.icon}`} />
                </div>
            </div>

            {loading ? (
                <div className="h-8 bg-gray-700 rounded animate-pulse w-20" />
            ) : (
                <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold text-white">{value}</span>
                    {trend && (
                        <span className={`text-sm ${trend.direction === "up" ? "text-green-400" : "text-red-400"}`}>
                            {trend.direction === "up" ? "↑" : "↓"} {trend.value}%
                        </span>
                    )}
                </div>
            )}

            {subtitle && (
                <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
        </div>
    );
}

export default StatCard;
