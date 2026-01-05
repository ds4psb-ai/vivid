"use client";

/**
 * Human Cloud Dashboard Page (Design v2)
 * 
 * Aligned with Dimension/Tools page design system:
 * - Aurora Background
 * - card-premium hover effects
 * - Consistent typography
 * - Lusion-style rounded corners
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    Users,
    FileText,
    Briefcase,
    Plus,
    DollarSign,
    CheckCircle,
    AlertTriangle,
    RefreshCw,
    ChevronRight,
    Star,
    UserPlus,
    Sparkles,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

// =============================================================================
// Types
// =============================================================================

interface MarketplaceStats {
    open_requests: number;
    active_creators: number;
    completed_requests: number;
    total_volume_credits: number;
}

interface CreativeRequest {
    id: string;
    client_id: string;
    title: string;
    description: string;
    category: string;
    budget_credits: number;
    status: string;
    deadline?: string;
    created_at: string;
}

interface CreatorProfile {
    id: string;
    user_id: string;
    display_name: string;
    bio?: string;
    categories: string[];
    skills: string[];
    completed_count: number;
    avg_rating?: number;
    is_available: boolean;
    is_verified: boolean;
}

// =============================================================================
// Stat Card Component (Lusion Style)
// =============================================================================

function StatCard({
    icon: Icon,
    label,
    value,
    color,
}: {
    icon: React.ElementType;
    label: string;
    value: string | number;
    color: string;
}) {
    return (
        <div className="card-glass p-5">
            {/* Subtle glow */}
            <div className={`absolute -right-8 -top-8 h-32 w-32 rounded-full ${color} opacity-10 blur-[50px]`} />

            <div className="relative flex items-center justify-between">
                <div>
                    <div className="text-3xl font-bold text-white mb-1">
                        {typeof value === "number" ? value.toLocaleString() : value}
                    </div>
                    <div className="text-sm text-[var(--fg-muted)]">{label}</div>
                </div>
                <div className={`p-3 rounded-xl bg-white/5 border border-white/10`}>
                    <Icon className={`w-5 h-5 ${color.replace('bg-', 'text-')}`} />
                </div>
            </div>
        </div>
    );
}

// =============================================================================
// Request Card Component (Card Premium Style)
// =============================================================================

function RequestCard({
    request,
    onClick,
}: {
    request: CreativeRequest;
    onClick: () => void;
}) {
    const statusConfig: Record<string, { color: string; borderColor: string; label: string }> = {
        draft: { color: "text-slate-400", borderColor: "border-slate-500/30", label: "Draft" },
        open: { color: "text-emerald-400", borderColor: "border-emerald-500/30", label: "Open" },
        assigned: { color: "text-blue-400", borderColor: "border-blue-500/30", label: "Assigned" },
        in_progress: { color: "text-purple-400", borderColor: "border-purple-500/30", label: "In Progress" },
        review: { color: "text-yellow-400", borderColor: "border-yellow-500/30", label: "Review" },
        completed: { color: "text-emerald-400", borderColor: "border-emerald-500/30", label: "Completed" },
    };

    const config = statusConfig[request.status] || statusConfig.draft;

    return (
        <motion.div
            onClick={onClick}
            whileHover={{ y: -4, scale: 1.01 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="group card-glass card-glass-hover p-5 cursor-pointer"
        >
            {/* Glow on hover */}
            <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-violet-500 opacity-0 
                group-hover:opacity-10 blur-[60px] transition-opacity duration-500" />

            <div className="relative">
                <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-semibold text-white group-hover:text-violet-200 transition-colors line-clamp-1 pr-4">
                        {request.title}
                    </h3>
                    <span className={`px-2.5 py-1 text-xs font-medium rounded-full border bg-black/20 ${config.borderColor} ${config.color}`}>
                        {config.label}
                    </span>
                </div>

                <p className="text-sm text-[var(--fg-muted)] line-clamp-2 mb-4 leading-relaxed">
                    {request.description}
                </p>

                <div className="flex items-center justify-between">
                    <span className="text-emerald-400 font-bold text-lg">
                        {request.budget_credits} <span className="text-xs font-normal text-[var(--fg-muted)]">CR</span>
                    </span>
                    <span className="text-xs text-[var(--fg-muted)] px-2 py-1 bg-white/5 rounded-lg">
                        {request.category.replace(/_/g, " ")}
                    </span>
                </div>
            </div>

            <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/20 
                opacity-0 group-hover:opacity-100 group-hover:text-violet-400 transition-all duration-300" />
        </motion.div>
    );
}

// =============================================================================
// Creator Card Component (Card Premium Style)
// =============================================================================

function CreatorCard({
    creator,
    onClick,
}: {
    creator: CreatorProfile;
    onClick: () => void;
}) {
    return (
        <motion.div
            onClick={onClick}
            whileHover={{ y: -4, scale: 1.01 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="group card-glass card-glass-hover p-5 cursor-pointer"
        >
            {/* Glow on hover */}
            <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-blue-500 opacity-0 
                group-hover:opacity-10 blur-[60px] transition-opacity duration-500" />

            <div className="relative">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 
                        flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-violet-500/20">
                        {creator.display_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h3 className="font-semibold text-white group-hover:text-blue-200 transition-colors">
                            {creator.display_name}
                        </h3>
                        <div className="flex items-center gap-2 text-xs">
                            {creator.is_verified && (
                                <span className="text-blue-400 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" /> Verified
                                </span>
                            )}
                            <span className={creator.is_available ? "text-emerald-400" : "text-[var(--fg-muted)]"}>
                                {creator.is_available ? "Available" : "Busy"}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4 text-sm mb-3">
                    {creator.avg_rating && (
                        <span className="flex items-center gap-1 text-yellow-400">
                            <Star className="w-4 h-4 fill-current" />
                            {creator.avg_rating.toFixed(1)}
                        </span>
                    )}
                    <span className="text-[var(--fg-muted)]">
                        {creator.completed_count} completed
                    </span>
                </div>

                <div className="flex flex-wrap gap-2">
                    {creator.categories.slice(0, 2).map((cat) => (
                        <span key={cat} className="px-2.5 py-1 text-xs bg-white/5 border border-white/10 text-[var(--fg-muted)] rounded-lg">
                            {cat.replace(/_/g, " ")}
                        </span>
                    ))}
                </div>
            </div>
        </motion.div>
    );
}

// =============================================================================
// Loading Skeleton (Lusion Style)
// =============================================================================

function CardSkeleton() {
    return (
        <div className="card-glass p-5 animate-pulse">
            <div className="h-6 w-3/4 bg-white/10 rounded-lg mb-3"></div>
            <div className="h-4 w-full bg-white/5 rounded mb-2"></div>
            <div className="h-4 w-2/3 bg-white/5 rounded mb-4"></div>
            <div className="flex justify-between">
                <div className="h-6 w-20 bg-white/10 rounded"></div>
                <div className="h-5 w-16 bg-white/5 rounded"></div>
            </div>
        </div>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function HumanCloudPage() {
    const router = useRouter();
    const { language } = useLanguage();

    const [stats, setStats] = useState<MarketplaceStats | null>(null);
    const [openRequests, setOpenRequests] = useState<CreativeRequest[]>([]);
    const [topCreators, setTopCreators] = useState<CreatorProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const labels = {
        title: "Human Cloud",
        subtitle: language === "ko"
            ? "크리에이터와 클라이언트를 연결하는 마켓플레이스"
            : "Marketplace connecting creators and clients",
        createRequest: language === "ko" ? "의뢰 등록" : "Create Request",
        becomeCreator: language === "ko" ? "크리에이터 등록" : "Become Creator",
        openRequests: language === "ko" ? "공개 의뢰" : "Open Requests",
        topCreators: language === "ko" ? "추천 크리에이터" : "Top Creators",
        viewAll: language === "ko" ? "전체 보기" : "View All",
    };

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [statsRes, requestsRes, creatorsRes] = await Promise.all([
                fetchWithAuth("/api/v1/humancloud/stats").catch(() => null),
                fetchWithAuth("/api/v1/humancloud/requests/open?limit=6"),
                fetchWithAuth("/api/v1/humancloud/creators?limit=6"),
            ]);

            if (statsRes) setStats(statsRes as MarketplaceStats);
            setOpenRequests((requestsRes as CreativeRequest[]) || []);
            setTopCreators((creatorsRes as CreatorProfile[]) || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <AppShell showTopBar={false}>
            {/* Aurora Background (Fixed) */}
            <AuroraBackground />

            <div className="min-h-screen relative">
                {/* Hero Section */}
                <section className="relative pt-24 pb-12 px-4 sm:px-6">
                    <div className="mx-auto max-w-7xl">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                            className="text-center mb-12"
                        >
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
                                <Sparkles className="w-4 h-4 text-violet-400" />
                                <span className="text-xs font-medium text-violet-300 tracking-wider uppercase">Creative Marketplace</span>
                            </div>
                            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                                {labels.title}
                            </h1>
                            <p className="text-lg text-[var(--fg-muted)] max-w-2xl mx-auto">
                                {labels.subtitle}
                            </p>
                        </motion.div>

                        {/* Action Buttons */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
                            className="flex flex-wrap justify-center gap-4 mb-16"
                        >
                            <button
                                onClick={() => router.push("/humancloud/requests/create")}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-black font-medium rounded-full 
                                    hover:bg-violet-300 transition-all duration-300 shadow-lg shadow-white/10"
                            >
                                <Plus className="w-5 h-5" />
                                {labels.createRequest}
                            </button>
                            <button
                                onClick={() => router.push("/humancloud/creator")}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 text-white 
                                    font-medium rounded-full hover:bg-white/10 transition-all duration-300"
                            >
                                <UserPlus className="w-4 h-4" />
                                {labels.becomeCreator}
                            </button>
                            <button
                                onClick={fetchData}
                                disabled={loading}
                                className="p-3 bg-white/5 border border-white/10 text-[var(--fg-muted)] 
                                    hover:text-white hover:bg-white/10 rounded-full transition-all"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </button>
                        </motion.div>

                        {/* Stats Grid */}
                        {stats && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                                className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-16"
                            >
                                <StatCard
                                    icon={FileText}
                                    label="Open Requests"
                                    value={stats.open_requests}
                                    color="bg-violet-500"
                                />
                                <StatCard
                                    icon={Users}
                                    label="Active Creators"
                                    value={stats.active_creators}
                                    color="bg-blue-500"
                                />
                                <StatCard
                                    icon={CheckCircle}
                                    label="Completed"
                                    value={stats.completed_requests}
                                    color="bg-emerald-500"
                                />
                                <StatCard
                                    icon={DollarSign}
                                    label="Credits Paid"
                                    value={stats.total_volume_credits}
                                    color="bg-yellow-500"
                                />
                            </motion.div>
                        )}
                    </div>
                </section>

                {/* Error State */}
                {error && (
                    <div className="mx-auto max-w-7xl px-4 sm:px-6 mb-8">
                        <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 flex items-center gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                            <p className="text-red-300 flex-1">{error}</p>
                            <button
                                onClick={fetchData}
                                className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                )}

                {/* Content Sections */}
                <section className="relative z-10 pb-24 px-4 sm:px-6">
                    <div className="mx-auto max-w-7xl space-y-16">

                        {/* Open Requests Section */}
                        <div>
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                                    <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                        <Briefcase className="w-5 h-5 text-emerald-400" />
                                    </div>
                                    {labels.openRequests}
                                </h2>
                                <button
                                    onClick={() => router.push("/humancloud/requests")}
                                    className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1 
                                        px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 transition-colors"
                                >
                                    {labels.viewAll} <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>

                            {loading ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {[1, 2, 3].map((i) => <CardSkeleton key={i} />)}
                                </div>
                            ) : openRequests.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {openRequests.map((req) => (
                                        <RequestCard
                                            key={req.id}
                                            request={req}
                                            onClick={() => router.push(`/humancloud/requests/${req.id}`)}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-16 text-[var(--fg-muted)] bg-white/[0.02] rounded-[2rem] border border-white/5">
                                    No open requests yet
                                </div>
                            )}
                        </div>

                        {/* Top Creators Section */}
                        <div>
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                                    <div className="p-2 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                                        <Star className="w-5 h-5 text-yellow-400" />
                                    </div>
                                    {labels.topCreators}
                                </h2>
                                <button
                                    onClick={() => router.push("/humancloud/creators")}
                                    className="text-sm text-violet-400 hover:text-violet-300 flex items-center gap-1 
                                        px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 transition-colors"
                                >
                                    {labels.viewAll} <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>

                            {loading ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {[1, 2, 3].map((i) => <CardSkeleton key={i} />)}
                                </div>
                            ) : topCreators.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {topCreators.map((creator) => (
                                        <CreatorCard
                                            key={creator.id}
                                            creator={creator}
                                            onClick={() => router.push(`/humancloud/creators/${creator.id}`)}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-16 text-[var(--fg-muted)] bg-white/[0.02] rounded-[2rem] border border-white/5">
                                    No creators yet. Be the first!
                                </div>
                            )}
                        </div>
                    </div>
                </section>
            </div>
        </AppShell>
    );
}
