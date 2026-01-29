"use client";

/**
 * My Assignments Page
 * 
 * View and manage assignments for creators.
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    Briefcase,
    RefreshCw,
    AlertTriangle,
    ChevronRight,
    Clock,
    DollarSign,
    Filter,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { api } from "@/lib/api";
import {
    getAssignmentStatus,
    getStatusLabel,
    ASSIGNMENT_STATUS_FILTERS,
} from "@/lib/status-config";
import { CARD_MOTION_PROPS } from "@/hooks/useCardMotion";

interface Assignment {
    id: string;
    request_id: string;
    request_title?: string;
    creator_id: string;
    status: string;
    agreed_credits: number;
    agreed_deadline?: string;
    created_at: string;
}

function AssignmentCard({ assignment, onClick, language }: { assignment: Assignment; onClick: () => void; language: string }) {
    const config = getAssignmentStatus(assignment.status);
    const StatusIcon = config.icon;
    const now = useMemo(() => new Date(), []);
    const daysLeft = assignment.agreed_deadline
        ? Math.ceil((new Date(assignment.agreed_deadline).getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
        : null;

    return (
        <motion.div
            onClick={onClick}
            {...CARD_MOTION_PROPS}
            className="group card-glass card-glass-hover p-5 cursor-pointer"
        >
            <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-[var(--fg-0)] group-hover:text-violet-300 transition-colors line-clamp-1 pr-4">
                    {assignment.request_title || "Request"}
                </h3>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full whitespace-nowrap ${config.bgColor} ${config.color}`}>
                    <StatusIcon className="w-3 h-3" />
                    {getStatusLabel(config, language)}
                </span>
            </div>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                        <DollarSign className="w-4 h-4" />
                        {assignment.agreed_credits}
                    </span>
                    {daysLeft !== null && (
                        <span className={`flex items-center gap-1 text-sm ${daysLeft > 3 ? "text-slate-500" : daysLeft > 0 ? "text-yellow-400" : "text-red-400"}`}>
                            <Clock className="w-3.5 h-3.5" />
                            {daysLeft > 0 ? `${daysLeft}d left` : "Overdue"}
                        </span>
                    )}
                </div>
                <span className="text-xs text-slate-500">
                    {new Date(assignment.created_at).toLocaleDateString()}
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
                <div className="h-6 w-20 bg-slate-700 rounded-full"></div>
            </div>
            <div className="flex justify-between">
                <div className="h-5 w-24 bg-slate-700/50 rounded"></div>
                <div className="h-4 w-20 bg-slate-700/50 rounded"></div>
            </div>
        </div>
    );
}

export default function AssignmentsPage() {
    const router = useRouter();
    const { language } = useLanguage();

    const [assignments, setAssignments] = useState<Assignment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState("");

    const labels = {
        title: language === "ko" ? "내 과제" : "My Assignments",
        back: language === "ko" ? "Human Cloud" : "Human Cloud",
        noAssignments: language === "ko" ? "배정된 과제가 없습니다" : "No assignments yet",
        browseRequests: language === "ko" ? "의뢰 찾아보기" : "Browse Requests",
        count: (n: number) => language === "ko" ? `${n}개 과제` : `${n} assignment${n !== 1 ? "s" : ""}`,
    };

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.append("status", statusFilter);
            const url = `/api/v1/humancloud/my-assignments${params.toString() ? `?${params}` : ""}`;
            const data = await api.get<Assignment[]>(url);
            setAssignments(data || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }, [statusFilter]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return (
        <AppShell showTopBar={false}>
            <AuroraBackground />
            <div className="min-h-screen relative px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-4xl">
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
                                <Briefcase className="w-6 h-6 text-purple-400" />
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

                    {/* Status Filter */}
                    <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
                        <Filter className="w-4 h-4 text-slate-500 flex-shrink-0" />
                        {ASSIGNMENT_STATUS_FILTERS.map((f) => (
                            <button
                                key={f.value}
                                onClick={() => setStatusFilter(f.value)}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors
                                    ${statusFilter === f.value
                                        ? "bg-violet-600 text-white"
                                        : "bg-slate-800 text-[var(--fg-muted)] hover:bg-slate-700"
                                    }`}
                            >
                                {language === "ko" ? f.labelKo : f.label}
                            </button>
                        ))}
                    </div>

                    {/* Count */}
                    <div className="text-sm text-[var(--fg-muted)] mb-4">
                        {labels.count(assignments.length)}
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
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => <CardSkeleton key={i} />)}
                        </div>
                    )}

                    {/* Empty */}
                    {!loading && !error && assignments.length === 0 && (
                        <div className="text-center py-12">
                            <Briefcase className="w-12 h-12 mx-auto text-slate-600 mb-4" />
                            <p className="text-[var(--fg-muted)] mb-4">{labels.noAssignments}</p>
                            <button
                                onClick={() => router.push("/humancloud/requests")}
                                className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg"
                            >
                                {labels.browseRequests}
                            </button>
                        </div>
                    )}

                    {/* List */}
                    {!loading && !error && assignments.length > 0 && (
                        <div className="space-y-4">
                            {assignments.map((a) => (
                                <AssignmentCard
                                    key={a.id}
                                    assignment={a}
                                    language={language}
                                    onClick={() => router.push(`/humancloud/requests/${a.request_id}`)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
