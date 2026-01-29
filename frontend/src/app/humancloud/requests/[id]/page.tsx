"use client";

/**
 * Request Detail Page (Hardened)
 * 
 * Features:
 * - Evidence Loop Visualization (Timeline)
 * - State-Aware Action Console
 * - 75/25 Settlement Logic
 * - Role-Based Views (Client vs Creator)
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    FileText,
    DollarSign,
    Calendar,
    Clock,
    Shield,
    CheckCircle,
    AlertTriangle,
    Loader2,
    RefreshCw,
    Activity,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { api } from "@/lib/api";
import EvidenceTimeline, { EvidenceLog } from "@/components/humancloud/EvidenceTimeline";
import ActionConsole from "@/components/humancloud/ActionConsole";

// =============================================================================
// Types
// =============================================================================

interface RequestDetail {
    id: string;
    client_id: string;
    title: string;
    description: string;
    category: string;
    budget_credits: number;
    status: string;
    deadline?: string;
    created_at: string;
    // Expanded fields
    credits_escrowed?: number;
    credits_released?: number;
    assigned_creator_id?: string;
}

interface Assignment {
    id: string;
    creator_id: string;
    status: string;
    agreed_credits: number;
    created_at: string;
}

interface Delivery {
    id: string;
    assignment_id: string;
    version: number;
    files: string[];
    status: 'pending' | 'approved' | 'rejected';
    submitted_at: string;
}

interface UserProfile {
    id: string;
    email: string;
}

// =============================================================================
// Page Component
// =============================================================================

export default function RequestDetailPage() {
    const router = useRouter();
    const params = useParams();
    const requestId = params.id as string;
    const { language } = useLanguage();

    // Data State
    const [user, setUser] = useState<UserProfile | null>(null);
    const [request, setRequest] = useState<RequestDetail | null>(null);
    const [assignment, setAssignment] = useState<Assignment | null>(null);
    const [evidenceLogs, setEvidenceLogs] = useState<EvidenceLog[]>([]);

    // UI State
    const [loading, setLoading] = useState(true);
    const [msg, setMsg] = useState<{ type: 'error' | 'success', text: string } | null>(null);

    // Derived Role
    type UserRole = "client" | "creator" | "guest";
    const role: UserRole = user?.id === request?.client_id
        ? "client"
        : (user?.id === assignment?.creator_id ? "creator" : "guest");

    // Labels
    const labels = {
        back: language === "ko" ? "목록으로" : "Back",
        timeline: language === "ko" ? "증거 타임라인" : "Evidence Timeline",
        timelineDesc: language === "ko"
            ? "모든 계약, 작업, 자금 이동이 블록체인처럼 기록됩니다."
            : "Immutable record of contracts, work, and funds.",
        console: language === "ko" ? "액션 콘솔" : "Action Console",
    };

    // -------------------------------------------------------------------------
    // Data Fetching
    // -------------------------------------------------------------------------

    const fetchData = useCallback(async () => {
        setLoading(true);
        setMsg(null);
        try {
            // 1. Get User
            const userData = await api.get("/api/v1/users/me") as UserProfile;
            setUser(userData);

            // 2. Get Request
            const reqData = await api.get(`/api/v1/humancloud/requests/${requestId}`) as RequestDetail;
            setRequest(reqData);

            // 3. Get Assignment (if any)
            try {
                const assigns = await api.get(`/api/v1/humancloud/requests/${requestId}/assignments`) as Assignment[];
                // Find active assignment
                const activeAssign = Array.isArray(assigns) ? assigns[0] : null;
                setAssignment(activeAssign);
            } catch {
                setAssignment(null);
            }

            // 4. Get Evidence
            // Note: In a real app, assignments have IDs. Here we assume one active assignment for the request context
            // or fetch logs by request context if API supports it.
            // For MVP, we try to fetch evidence by assignment ID if it exists.
            if (reqData.status !== "draft" && reqData.status !== "open") {
                try {
                    // We need assignment ID for evidence. 
                    // If we found assignment above, use it.
                    // The API expects /assignments/{id}/evidence
                    const assigns = await api.get(`/api/v1/humancloud/requests/${requestId}/assignments`) as Assignment[];
                    if (assigns && assigns.length > 0) {
                        const logs = await api.get(`/api/v1/humancloud/assignments/${assigns[0].id}/evidence`) as EvidenceLog[];
                        setEvidenceLogs(logs || []);
                    }
                } catch {
                    setEvidenceLogs([]);
                }
            }

        } catch (err) {
            setMsg({ type: 'error', text: err instanceof Error ? err.message : "Failed to load data" });
        } finally {
            setLoading(false);
        }
    }, [requestId]);

    useEffect(() => {
        if (requestId) fetchData();
    }, [requestId, fetchData]);

    // -------------------------------------------------------------------------
    // Action Handlers
    // -------------------------------------------------------------------------

    const handleAction = async (action: string, data?: unknown) => {
        setMsg(null);
        try {
            if (action === "publish") {
                await api.post(`/api/v1/humancloud/requests/${requestId}/publish`);
                setMsg({ type: 'success', text: "Request published and credits escrowed." });
            }
            else if (action === "accept" && assignment) {
                await api.post(`/api/v1/humancloud/assignments/${assignment.id}/accept`);
                setMsg({ type: 'success', text: "Assignment accepted. Contract started." });
            }
            else if (action === "start" && assignment) {
                await api.post(`/api/v1/humancloud/assignments/${assignment.id}/start`);
                setMsg({ type: 'success', text: "Work started." });
            }
            else if (action === "deliver" && assignment) {
                await api.post(`/api/v1/humancloud/assignments/${assignment.id}/deliver`, data);
                setMsg({ type: 'success', text: "Delivery submitted for review." });
            }
            else if (action === "approve" && assignment) {
                // Fetch deliveries to find the latest one
                const deliveries = await api.get<Delivery[]>(`/api/v1/humancloud/assignments/${assignment.id}/deliveries`);

                // Find latest pending delivery
                const pendingDelivery = deliveries.find((d) => d.status === 'pending');

                if (!pendingDelivery) {
                    throw new Error("No pending delivery found to approve.");
                }

                await api.post(`/api/v1/humancloud/deliveries/${pendingDelivery.id}/approve`, data);

                setMsg({ type: 'success', text: "Delivery approved! Payment released." });
            }

            // Refresh data
            await fetchData();

        } catch (err) {
            setMsg({ type: 'error', text: err instanceof Error ? err.message : "Action failed" });
        }
    };

    // -------------------------------------------------------------------------
    // Render
    // -------------------------------------------------------------------------

    if (loading && !request) {
        return (
            <AppShell showTopBar={false}>
                <div className="min-h-screen flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                </div>
            </AppShell>
        );
    }

    if (!request) return null;

    return (
        <AppShell showTopBar={false}>
            {/* Aurora Background */}
            <AuroraBackground />

            <div className="min-h-screen relative px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* LEFT COLUMN: Request Info & Action Console */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* Header */}
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <button
                                onClick={() => router.push("/humancloud/requests")}
                                className="flex items-center gap-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] mb-4 transition-colors"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                {labels.back}
                            </button>

                            <div className="flex items-start justify-between mb-2">
                                <h1 className="text-2xl font-bold text-[var(--fg-0)]">{request.title}</h1>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium border
                                    ${request.status === 'open' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' :
                                        request.status === 'draft' ? 'border-slate-500/30 text-slate-400 bg-slate-500/10' :
                                            'border-blue-500/30 text-blue-400 bg-blue-500/10'}`}>
                                    {request.status.toUpperCase()}
                                </span>
                            </div>

                            <div className="flex flex-wrap gap-4 text-sm text-[var(--fg-muted)] mb-6">
                                <span className="flex items-center gap-1.5">
                                    <DollarSign className="w-4 h-4 text-emerald-500" />
                                    <span className="text-[var(--fg-0)] font-medium">{request.budget_credits}</span> CR
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <Calendar className="w-4 h-4 text-blue-400" />
                                    {request.deadline ? new Date(request.deadline).toLocaleDateString() : 'No deadline'}
                                </span>
                                <span className="flex items-center gap-1.5">
                                    <Clock className="w-4 h-4 text-slate-400" />
                                    {new Date(request.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        </motion.div>

                        {/* Error/Success Message */}
                        {msg && (
                            <div className={`p-4 rounded-xl flex items-center gap-3 border ${msg.type === 'error' ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                                }`}>
                                {msg.type === 'error' ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
                                {msg.text}
                            </div>
                        )}

                        {/* ACTION CONSOLE (The Brain) */}
                        <div className="card-glass">
                            <div className="p-4 border-b border-white/5 bg-slate-900/50 flex items-center justify-between">
                                <h2 className="font-semibold text-[var(--fg-0)] flex items-center gap-2">
                                    <Activity className="w-4 h-4 text-violet-400" />
                                    {labels.console}
                                </h2>
                                <span className="text-xs text-slate-500">Role: {role.toUpperCase()}</span>
                            </div>
                            <div className="p-6 bg-gradient-to-br from-slate-900/50 to-slate-800/20">
                                {request.status === 'draft' ? (
                                    role === 'client' ? (
                                        <button
                                            onClick={() => handleAction('publish')}
                                            disabled={loading}
                                            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium flex items-center justify-center gap-2"
                                        >
                                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                                            Publish & Escrow Credits
                                        </button>
                                    ) : (
                                        <div className="text-center text-slate-500">Draft mode - waiting for client publish</div>
                                    )
                                ) : (
                                    <ActionConsole
                                        status={assignment ? assignment.status : request.status}
                                        role={role}
                                        onAction={handleAction}
                                        assignmentId={assignment?.id}
                                        budget={request.budget_credits}
                                    />
                                )}
                            </div>
                        </div>

                        {/* Details */}
                        <div className="card-glass p-6">
                            <h3 className="font-semibold text-[var(--fg-0)] mb-3 flex items-center gap-2">
                                <FileText className="w-4 h-4 text-blue-400" />
                                Description
                            </h3>
                            <p className="text-[var(--fg-muted)] whitespace-pre-wrap leading-relaxed">
                                {request.description}
                            </p>
                        </div>
                    </div>

                    {/* RIGHT COLUMN: Evidence Timeline */}
                    <div className="lg:col-span-1">
                        <div className="card-glass h-full max-h-[var(--layout-app-viewport-lg)] flex flex-col">
                            <div className="p-4 border-b border-white/5 bg-slate-900/50">
                                <h2 className="font-semibold text-[var(--fg-0)] flex items-center gap-2">
                                    <Shield className="w-4 h-4 text-emerald-400" />
                                    {labels.timeline}
                                </h2>
                                <p className="text-xs text-slate-500 mt-1">{labels.timelineDesc}</p>
                            </div>

                            <div className="p-4 overflow-y-auto flex-1 custom-scrollbar">
                                <div className="flex items-center justify-between mb-4 text-xs text-slate-500">
                                    <span>LIVE UPDATES</span>
                                    <button onClick={fetchData} className="hover:text-violet-400 transition-colors">
                                        <RefreshCw className="w-3 h-3" />
                                    </button>
                                </div>
                                <EvidenceTimeline logs={evidenceLogs} />
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </AppShell>
    );
}
