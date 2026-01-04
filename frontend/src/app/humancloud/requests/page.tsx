"use client";

/**
 * Requests List Page
 * 
 * Browse all open creative requests.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    Briefcase,
    Search,
    Filter,
    RefreshCw,
    AlertTriangle,
    ChevronRight,
    Clock,
    DollarSign,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

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

const STATUS_CONFIG: Record<string, { color: string; bgColor: string; label: string; labelKo: string }> = {
    draft: { color: "text-slate-400", bgColor: "bg-slate-500/10", label: "Draft", labelKo: "초안" },
    open: { color: "text-emerald-400", bgColor: "bg-emerald-500/10", label: "Open", labelKo: "공개" },
    assigned: { color: "text-blue-400", bgColor: "bg-blue-500/10", label: "Assigned", labelKo: "배정됨" },
    in_progress: { color: "text-purple-400", bgColor: "bg-purple-500/10", label: "In Progress", labelKo: "진행중" },
    delivered: { color: "text-yellow-400", bgColor: "bg-yellow-500/10", label: "Delivered", labelKo: "납품됨" },
    completed: { color: "text-emerald-400", bgColor: "bg-emerald-500/10", label: "Completed", labelKo: "완료" },
};

const CATEGORIES = [
    { value: "", label: "All", labelKo: "전체" },
    { value: "video_creative", label: "Video", labelKo: "영상" },
    { value: "image_design", label: "Image", labelKo: "이미지" },
    { value: "motion_graphics", label: "Motion", labelKo: "모션" },
    { value: "short_form", label: "Short-form", labelKo: "숏폼" },
    { value: "brand_content", label: "Brand", labelKo: "브랜드" },
];

function RequestCard({ request, onClick, language }: { request: CreativeRequest; onClick: () => void; language: string }) {
    const config = STATUS_CONFIG[request.status] || STATUS_CONFIG.draft;
    const daysLeft = request.deadline
        ? Math.ceil((new Date(request.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
        : null;

    return (
        <motion.div
            onClick={onClick}
            whileHover={{ y: -3, scale: 1.01 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="group card-glass card-glass-hover p-5 cursor-pointer"
        >
            <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-[var(--fg-0)] group-hover:text-violet-300 transition-colors line-clamp-1 pr-4">
                    {request.title}
                </h3>
                <span className={`px-2.5 py-0.5 text-xs rounded-full whitespace-nowrap ${config.bgColor} ${config.color}`}>
                    {language === "ko" ? config.labelKo : config.label}
                </span>
            </div>

            <p className="text-sm text-[var(--fg-muted)] line-clamp-2 mb-4">
                {request.description}
            </p>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1 text-emerald-400 font-medium">
                        <DollarSign className="w-4 h-4" />
                        {request.budget_credits}
                    </span>
                    {daysLeft !== null && daysLeft > 0 && (
                        <span className="flex items-center gap-1 text-slate-500 text-sm">
                            <Clock className="w-3.5 h-3.5" />
                            {daysLeft}d
                        </span>
                    )}
                </div>
                <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
                    {request.category.replace(/_/g, " ")}
                </span>
            </div>

            <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 
                opacity-0 group-hover:opacity-100 group-hover:text-violet-400 transition-all" />
        </motion.div>
    );
}

function CardSkeleton() {
    return (
        <div className="card-glass p-5 animate-pulse">
            <div className="flex justify-between mb-3">
                <div className="h-5 w-3/4 bg-slate-700 rounded"></div>
                <div className="h-5 w-16 bg-slate-700 rounded-full"></div>
            </div>
            <div className="h-10 bg-slate-700/50 rounded mb-4"></div>
            <div className="flex justify-between">
                <div className="h-5 w-20 bg-slate-700/50 rounded"></div>
                <div className="h-5 w-24 bg-slate-800 rounded"></div>
            </div>
        </div>
    );
}

export default function RequestsListPage() {
    const router = useRouter();
    const { language } = useLanguage();

    const [requests, setRequests] = useState<CreativeRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("");

    const labels = {
        title: language === "ko" ? "의뢰 목록" : "Browse Requests",
        back: language === "ko" ? "Human Cloud" : "Human Cloud",
        searchPlaceholder: language === "ko" ? "의뢰 검색..." : "Search requests...",
        noResults: language === "ko" ? "조건에 맞는 의뢰가 없습니다" : "No requests found",
        count: (n: number) => language === "ko" ? `${n}개 의뢰` : `${n} request${n !== 1 ? "s" : ""}`,
    };

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams();
            if (category) params.append("category", category);
            const url = `/api/v1/humancloud/requests${params.toString() ? `?${params}` : ""}`;
            const data = await fetchWithAuth(url) as CreativeRequest[];
            setRequests(data || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [category]);

    const filteredRequests = requests.filter((r) =>
        !search || r.title.toLowerCase().includes(search.toLowerCase()) ||
        r.description.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <AppShell showTopBar={false}>
            <AuroraBackground />
            <div className="min-h-screen relative px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-5xl">
                    {/* Header */}
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
                        <button
                            onClick={() => router.push("/humancloud")}
                            className="flex items-center gap-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] mb-4 transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            {labels.back}
                        </button>
                        <div className="flex items-center justify-between">
                            <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl flex items-center gap-2">
                                <Briefcase className="w-6 h-6 text-emerald-400" />
                                {labels.title}
                            </h1>
                            <button
                                onClick={fetchData}
                                disabled={loading}
                                className="p-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-slate-800 rounded-lg"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                            </button>
                        </div>
                    </motion.div>

                    {/* Filters */}
                    <div className="flex flex-wrap gap-3 mb-6">
                        <div className="flex-1 min-w-[200px] relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder={labels.searchPlaceholder}
                                className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg 
                                    text-white placeholder-slate-500 focus:border-violet-500"
                            />
                        </div>
                        <div className="flex gap-2 flex-wrap">
                            {CATEGORIES.map((cat) => (
                                <button
                                    key={cat.value}
                                    onClick={() => setCategory(cat.value)}
                                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors
                                        ${category === cat.value
                                            ? "bg-violet-600 text-white"
                                            : "bg-slate-800 text-[var(--fg-muted)] hover:bg-slate-700"
                                        }`}
                                >
                                    {language === "ko" ? cat.labelKo : cat.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Count */}
                    <div className="text-sm text-[var(--fg-muted)] mb-4">
                        {labels.count(filteredRequests.length)}
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-400" />
                            <p className="text-red-300 flex-1">{error}</p>
                        </div>
                    )}

                    {/* Loading */}
                    {loading && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {[1, 2, 3, 4].map((i) => <CardSkeleton key={i} />)}
                        </div>
                    )}

                    {/* Empty */}
                    {!loading && !error && filteredRequests.length === 0 && (
                        <div className="text-center py-12 text-[var(--fg-muted)]">
                            {labels.noResults}
                        </div>
                    )}

                    {/* List */}
                    {!loading && !error && filteredRequests.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {filteredRequests.map((req) => (
                                <RequestCard
                                    key={req.id}
                                    request={req}
                                    language={language}
                                    onClick={() => router.push(`/humancloud/requests/${req.id}`)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
