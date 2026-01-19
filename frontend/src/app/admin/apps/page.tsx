/**
 * App List Page
 * 
 * 등록된 앱 목록 조회 및 관리
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
    Package, Plus, Search,
    CheckCircle, Clock, AlertCircle, XCircle, Loader2,
    Eye, Trash2, Play, Pause
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { listApps, updateAppStatus, deleteApp, buildApp, type RegisteredApp } from "@/lib/admin-api";

// Status badge colors
const STATUS_STYLES: Record<string, { bg: string; text: string; icon: typeof CheckCircle }> = {
    active: { bg: "bg-green-500/20", text: "text-green-400", icon: CheckCircle },
    pending: { bg: "bg-yellow-500/20", text: "text-yellow-400", icon: Clock },
    building: { bg: "bg-blue-500/20", text: "text-blue-400", icon: Loader2 },
    reviewing: { bg: "bg-purple-500/20", text: "text-purple-400", icon: Clock },
    inactive: { bg: "bg-zinc-500/20", text: "text-zinc-400", icon: Pause },
    rejected: { bg: "bg-red-500/20", text: "text-red-400", icon: XCircle },
    failed: { bg: "bg-red-500/20", text: "text-red-400", icon: AlertCircle },
};

function StatusBadge({ status }: { status: string }) {
    const style = STATUS_STYLES[status] || STATUS_STYLES.pending;
    const Icon = style.icon;

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
            <Icon className={`w-3 h-3 ${status === "building" ? "animate-spin" : ""}`} />
            {status}
        </span>
    );
}

export default function AdminAppsPage() {
    const [apps, setApps] = useState<RegisteredApp[]>([]);
    const [total, setTotal] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("");
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    // Fetch apps
    const fetchApps = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await listApps({
                status: statusFilter || undefined,
                limit: 50,
            });
            setApps(response.apps);
            setTotal(response.total);
        } catch (err) {
            console.error(err);
            setError("앱 목록을 불러올 수 없습니다");
        } finally {
            setIsLoading(false);
        }
    }, [statusFilter]);

    useEffect(() => {
        fetchApps();
    }, [fetchApps]);

    // Filter by search
    const filteredApps = apps.filter(app =>
        app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.appId.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Handle build
    const handleBuild = async (appId: string) => {
        setActionLoading(appId);
        try {
            const result = await buildApp(appId);
            if (result.success) {
                await fetchApps();
            } else {
                alert(`빌드 실패: ${result.error}`);
            }
        } finally {
            setActionLoading(null);
        }
    };

    // Handle toggle status
    const handleToggleStatus = async (appId: string, currentStatus: string) => {
        const newStatus = currentStatus === "active" ? "inactive" : "active";
        setActionLoading(appId);
        try {
            const result = await updateAppStatus(appId, newStatus);
            if (result.success) {
                await fetchApps();
            }
        } finally {
            setActionLoading(null);
        }
    };

    // Handle delete
    const handleDelete = async (appId: string) => {
        if (!confirm("정말 삭제하시겠습니까?")) return;

        setActionLoading(appId);
        try {
            const result = await deleteApp(appId);
            if (result.success) {
                await fetchApps();
            }
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <AppShell>
            <div className="min-h-screen bg-[#0a0a0b] text-white p-8">
                <div className="max-w-6xl mx-auto">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h1 className="text-2xl font-bold mb-2">등록된 앱</h1>
                            <p className="text-zinc-400 text-sm">
                                {total}개의 앱이 등록되어 있습니다
                            </p>
                        </div>
                        <Link
                            href="/admin/migration"
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-lime-500 hover:bg-lime-400 text-black font-bold transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            새 앱 등록
                        </Link>
                    </div>

                    {/* Filters */}
                    <div className="flex gap-4 mb-6">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="앱 이름 또는 ID로 검색..."
                                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 focus:border-lime-500/50 focus:outline-none transition-colors"
                            />
                        </div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-4 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 focus:border-lime-500/50 focus:outline-none transition-colors"
                        >
                            <option value="">모든 상태</option>
                            <option value="active">Active</option>
                            <option value="pending">Pending</option>
                            <option value="building">Building</option>
                            <option value="inactive">Inactive</option>
                            <option value="failed">Failed</option>
                        </select>
                    </div>

                    {/* Loading */}
                    {isLoading && (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 text-lime-400 animate-spin" />
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-center">
                            {error}
                        </div>
                    )}

                    {/* App List */}
                    {!isLoading && !error && (
                        <div className="space-y-3">
                            {filteredApps.length === 0 ? (
                                <div className="text-center py-20 text-zinc-500">
                                    <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>등록된 앱이 없습니다</p>
                                </div>
                            ) : (
                                filteredApps.map((app, index) => (
                                    <motion.div
                                        key={app.appId}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.05 }}
                                        className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-colors"
                                    >
                                        <div className="flex items-center gap-4">
                                            {/* Icon */}
                                            <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center shrink-0">
                                                <Package className="w-6 h-6 text-zinc-500" />
                                            </div>

                                            {/* Info */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-3 mb-1">
                                                    <h3 className="font-bold truncate">{app.name}</h3>
                                                    <StatusBadge status={app.status} />
                                                </div>
                                                <div className="flex items-center gap-4 text-xs text-zinc-500">
                                                    <span>v{app.version}</span>
                                                    <span className="font-mono">{app.appId}</span>
                                                    <span>{new Date(app.createdAt).toLocaleDateString()}</span>
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div className="flex items-center gap-2">
                                                {actionLoading === app.appId ? (
                                                    <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
                                                ) : (
                                                    <>
                                                        {app.status === "pending" && (
                                                            <button
                                                                onClick={() => handleBuild(app.appId)}
                                                                className="p-2 rounded-lg hover:bg-lime-500/20 text-lime-400 transition-colors"
                                                                title="빌드"
                                                            >
                                                                <Play className="w-4 h-4" />
                                                            </button>
                                                        )}
                                                        {(app.status === "active" || app.status === "inactive") && (
                                                            <button
                                                                onClick={() => handleToggleStatus(app.appId, app.status)}
                                                                className={`p-2 rounded-lg transition-colors ${app.status === "active"
                                                                    ? "hover:bg-yellow-500/20 text-yellow-400"
                                                                    : "hover:bg-green-500/20 text-green-400"
                                                                    }`}
                                                                title={app.status === "active" ? "비활성화" : "활성화"}
                                                            >
                                                                {app.status === "active" ? (
                                                                    <Pause className="w-4 h-4" />
                                                                ) : (
                                                                    <Play className="w-4 h-4" />
                                                                )}
                                                            </button>
                                                        )}
                                                        <Link
                                                            href={`/sandbox/${app.appId}`}
                                                            className="p-2 rounded-lg hover:bg-white/10 text-zinc-400 transition-colors"
                                                            title="미리보기"
                                                        >
                                                            <Eye className="w-4 h-4" />
                                                        </Link>
                                                        <button
                                                            onClick={() => handleDelete(app.appId)}
                                                            className="p-2 rounded-lg hover:bg-red-500/20 text-red-400 transition-colors"
                                                            title="삭제"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
