"use client";

/**
 * Tool Dashboard Page
 * 
 * UX Hardening Features:
 * - Tier badge with color coding (experimental/verified/certified)
 * - Usage stats with sparklines
 * - Fork count with attribution score preview
 * - Quality rating with star display
 * - Revenue tracking
 * - Empty state with CTA
 * - Loading skeleton
 * - Error handling with retry
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
    Zap,
    GitFork,
    Star,
    TrendingUp,
    Plus,
    AlertTriangle,
    CheckCircle,
    Shield,
    Loader2,
    RefreshCw,
    ChevronRight,
    Beaker,
    Award,
    BadgeCheck,
} from "lucide-react";
import * as telemetryApi from "@/lib/telemetry-api";
import type { ToolManifest, ToolTier, DashboardOverview } from "@/lib/telemetry-api";

// =============================================================================
// Tier Badge Component
// =============================================================================

function TierBadge({ tier }: { tier: ToolTier }) {
    const config = {
        experimental: {
            icon: Beaker,
            label: "Experimental",
            className: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
        },
        verified: {
            icon: BadgeCheck,
            label: "Verified",
            className: "bg-blue-500/10 text-blue-400 border-blue-500/30",
        },
        certified: {
            icon: Award,
            label: "Certified",
            className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
        },
    };

    const { icon: Icon, label, className } = config[tier];

    return (
        <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full border ${className}`}
        >
            <Icon className="w-3.5 h-3.5" />
            {label}
        </span>
    );
}

// =============================================================================
// Star Rating Component
// =============================================================================

function StarRating({ rating, count }: { rating: number | null; count?: number }) {
    if (rating === null) {
        return <span className="text-gray-500 text-sm">No ratings yet</span>;
    }

    return (
        <div className="flex items-center gap-1.5">
            <div className="flex">
                {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                        key={star}
                        className={`w-4 h-4 ${star <= Math.round(rating)
                                ? "text-yellow-400 fill-yellow-400"
                                : "text-gray-600"
                            }`}
                    />
                ))}
            </div>
            <span className="text-sm text-gray-400">
                {rating.toFixed(1)}
                {count !== undefined && <span className="text-gray-500"> ({count})</span>}
            </span>
        </div>
    );
}

// =============================================================================
// Tool Card Component
// =============================================================================

function ToolCard({ tool, onClick }: { tool: ToolManifest; onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className="group relative bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 
                 hover:border-purple-500/50 hover:bg-gray-800/80 transition-all cursor-pointer"
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-purple-300 transition-colors">
                        {tool.display_name}
                    </h3>
                    <p className="text-sm text-gray-400 font-mono">{tool.tool_key}</p>
                </div>
                <TierBadge tier={tool.tier} />
            </div>

            {/* Description */}
            <p className="text-sm text-gray-400 line-clamp-2 mb-4">{tool.description}</p>

            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                    <div className="text-lg font-bold text-white">{tool.usage_count}</div>
                    <div className="text-xs text-gray-500">Uses</div>
                </div>
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                    <div className="text-lg font-bold text-white">{tool.fork_count}</div>
                    <div className="text-xs text-gray-500">Forks</div>
                </div>
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                    <div className="text-lg font-bold text-emerald-400">{tool.total_revenue}</div>
                    <div className="text-xs text-gray-500">Credits</div>
                </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between">
                <StarRating rating={tool.quality_rating} />
                <div className="flex items-center gap-1 text-sm text-gray-400">
                    <span className="px-2 py-0.5 bg-gray-700/50 rounded text-xs">
                        {tool.credit_cost} credits
                    </span>
                </div>
            </div>

            {/* Fork Indicator */}
            {tool.parent_tool_id && (
                <div className="absolute top-3 right-3 flex items-center gap-1 text-xs text-purple-400">
                    <GitFork className="w-3 h-3" />
                    <span>Fork</span>
                </div>
            )}

            {/* Hover Arrow */}
            <ChevronRight
                className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-600 
                   group-hover:text-purple-400 group-hover:translate-x-1 transition-all opacity-0 group-hover:opacity-100"
            />
        </div>
    );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function ToolCardSkeleton() {
    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 animate-pulse">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <div className="h-6 w-32 bg-gray-700 rounded mb-2"></div>
                    <div className="h-4 w-24 bg-gray-700/50 rounded"></div>
                </div>
                <div className="h-6 w-20 bg-gray-700 rounded-full"></div>
            </div>
            <div className="h-10 bg-gray-700/50 rounded mb-4"></div>
            <div className="grid grid-cols-3 gap-3 mb-4">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-14 bg-gray-900/50 rounded-lg"></div>
                ))}
            </div>
            <div className="h-4 w-24 bg-gray-700/50 rounded"></div>
        </div>
    );
}

// =============================================================================
// Empty State
// =============================================================================

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
    return (
        <div className="text-center py-16">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-purple-500/10 flex items-center justify-center">
                <Zap className="w-10 h-10 text-purple-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Tools Yet</h3>
            <p className="text-gray-400 mb-6 max-w-md mx-auto">
                Create your first AI tool to start building your ecosystem.
                Tools can be forked, shared, and earn credits.
            </p>
            <button
                onClick={onCreateClick}
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 
                   text-white font-medium rounded-lg transition-colors"
            >
                <Plus className="w-5 h-5" />
                Create Your First Tool
            </button>
        </div>
    );
}

// =============================================================================
// Dashboard Stats
// =============================================================================

function DashboardStats({ overview }: { overview: DashboardOverview | null }) {
    if (!overview) return null;

    const stats = [
        {
            label: "Total Tools",
            value: overview.tools.total,
            icon: Zap,
            color: "text-purple-400",
            bgColor: "bg-purple-500/10",
        },
        {
            label: "Total Runs",
            value: overview.runs.total,
            subValue: `${overview.runs.success_rate.toFixed(1)}% success`,
            icon: TrendingUp,
            color: "text-blue-400",
            bgColor: "bg-blue-500/10",
        },
        {
            label: "Total Forks",
            value: overview.forks.total,
            subValue: overview.forks.suspicious > 0 ? `${overview.forks.suspicious} flagged` : undefined,
            icon: GitFork,
            color: "text-emerald-400",
            bgColor: "bg-emerald-500/10",
        },
        {
            label: "Credits Earned",
            value: overview.runs.revenue_credits,
            icon: Star,
            color: "text-yellow-400",
            bgColor: "bg-yellow-500/10",
        },
    ];

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {stats.map((stat) => (
                <div
                    key={stat.label}
                    className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4"
                >
                    <div className="flex items-center gap-3 mb-2">
                        <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                            <stat.icon className={`w-5 h-5 ${stat.color}`} />
                        </div>
                        <span className="text-sm text-gray-400">{stat.label}</span>
                    </div>
                    <div className="text-2xl font-bold text-white">{stat.value.toLocaleString()}</div>
                    {stat.subValue && (
                        <div className="text-xs text-gray-500 mt-1">{stat.subValue}</div>
                    )}
                </div>
            ))}
        </div>
    );
}

// =============================================================================
// Tier Filter
// =============================================================================

function TierFilter({
    selected,
    onChange,
    counts,
}: {
    selected: ToolTier | "all";
    onChange: (tier: ToolTier | "all") => void;
    counts: Record<string, number>;
}) {
    const tiers: Array<{ key: ToolTier | "all"; label: string }> = [
        { key: "all", label: "All" },
        { key: "certified", label: "Certified" },
        { key: "verified", label: "Verified" },
        { key: "experimental", label: "Experimental" },
    ];

    return (
        <div className="flex gap-2 flex-wrap">
            {tiers.map(({ key, label }) => (
                <button
                    key={key}
                    onClick={() => onChange(key)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${selected === key
                            ? "bg-purple-600 text-white"
                            : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                        }`}
                >
                    {label}
                    {counts[key] !== undefined && (
                        <span className="ml-1.5 text-xs opacity-70">({counts[key] || 0})</span>
                    )}
                </button>
            ))}
        </div>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function ToolDashboardPage() {
    const router = useRouter();
    const [tools, setTools] = useState<ToolManifest[]>([]);
    const [overview, setOverview] = useState<DashboardOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [tierFilter, setTierFilter] = useState<ToolTier | "all">("all");

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [toolsData, overviewData] = await Promise.all([
                telemetryApi.listTools({ tier: tierFilter === "all" ? undefined : tierFilter }),
                telemetryApi.getDashboardOverview(30),
            ]);
            setTools(toolsData);
            setOverview(overviewData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [tierFilter]);

    const handleCreateClick = () => {
        router.push("/tools/create");
    };

    const handleToolClick = (tool: ToolManifest) => {
        router.push(`/tools/${tool.tool_key}`);
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold">Tool Dashboard</h1>
                            <p className="text-gray-400 text-sm">
                                Manage your AI tools, track usage, and monitor earnings
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={fetchData}
                                disabled={loading}
                                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </button>
                            <button
                                onClick={handleCreateClick}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 
                           text-white font-medium rounded-lg transition-colors"
                            >
                                <Plus className="w-5 h-5" />
                                Create Tool
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Stats */}
                <DashboardStats overview={overview} />

                {/* Filter */}
                <div className="flex items-center justify-between mb-6">
                    <TierFilter
                        selected={tierFilter}
                        onChange={setTierFilter}
                        counts={overview?.tools.by_tier || {}}
                    />
                    <div className="text-sm text-gray-400">
                        {tools.length} tool{tools.length !== 1 ? "s" : ""}
                    </div>
                </div>

                {/* Error State */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <div className="flex-1">
                            <p className="text-red-300">{error}</p>
                        </div>
                        <button
                            onClick={fetchData}
                            className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
                        >
                            Retry
                        </button>
                    </div>
                )}

                {/* Loading State */}
                {loading && !error && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <ToolCardSkeleton key={i} />
                        ))}
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && tools.length === 0 && (
                    <EmptyState onCreateClick={handleCreateClick} />
                )}

                {/* Tools Grid */}
                {!loading && !error && tools.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {tools.map((tool) => (
                            <ToolCard key={tool.id} tool={tool} onClick={() => handleToolClick(tool)} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
