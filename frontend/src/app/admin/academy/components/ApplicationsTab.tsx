"use client";

import { useState, useEffect, useCallback } from "react";
import { api, type AcademyApplication, type AcademyDeactivateResponse } from "@/lib/api";

type StatusFilter = "all" | "pending" | "paid" | "cancelled" | "refunded";

// =============================================================================
// Types
// =============================================================================

interface ApplicationsTabProps {
    onDataUpdate?: (data: { paid: number; unlinked: number; total: number }) => void;
}

// =============================================================================
// Sub Components
// =============================================================================

function StatCard({
    label,
    value,
    icon,
    color,
}: {
    label: string;
    value: number;
    icon: string;
    color: "blue" | "green" | "orange";
}) {
    const colorMap = {
        blue: "from-blue-500/20 to-indigo-500/20 border-blue-500/30 text-blue-400",
        green: "from-green-500/20 to-emerald-500/20 border-green-500/30 text-green-400",
        orange: "from-orange-500/20 to-amber-500/20 border-orange-500/30 text-orange-400",
    };

    return (
        <div className={`p-4 rounded-xl bg-gradient-to-br ${colorMap[color]} border`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-xs text-gray-400 mb-1">{label}</p>
                    <p className="text-2xl font-bold text-white">{value}</p>
                </div>
                <span className="material-symbols-outlined text-2xl opacity-50">{icon}</span>
            </div>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const statusMap: Record<string, { label: string; color: string }> = {
        paid: { label: "결제완료", color: "bg-green-500/20 text-green-300" },
        pending: { label: "대기중", color: "bg-yellow-500/20 text-yellow-300" },
        cancelled: { label: "취소", color: "bg-gray-500/20 text-gray-300" },
        refunded: { label: "환불", color: "bg-red-500/20 text-red-300" },
    };

    const { label, color } = statusMap[status] || {
        label: status,
        color: "bg-gray-500/20 text-gray-300",
    };

    return (
        <span className={`px-2 py-1 rounded-md text-xs font-medium ${color}`}>
            {label}
        </span>
    );
}

// =============================================================================
// Main Component
// =============================================================================

export function ApplicationsTab({ onDataUpdate }: ApplicationsTabProps) {
    const [applications, setApplications] = useState<AcademyApplication[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("paid");
    const [searchTerm, setSearchTerm] = useState("");
    const [total, setTotal] = useState(0);

    // Link Modal state
    const [linkModalOpen, setLinkModalOpen] = useState(false);
    const [selectedApp, setSelectedApp] = useState<AcademyApplication | null>(null);
    const [linkEmail, setLinkEmail] = useState("");
    const [linking, setLinking] = useState(false);
    const [linkError, setLinkError] = useState<string | null>(null);
    const [linkSuccess, setLinkSuccess] = useState<string | null>(null);

    // Deactivate Modal state
    const [deactivateModalOpen, setDeactivateModalOpen] = useState(false);
    const [deactivateApp, setDeactivateApp] = useState<AcademyApplication | null>(null);
    const [deactivating, setDeactivating] = useState(false);
    const [deactivateError, setDeactivateError] = useState<string | null>(null);
    const [deactivateSuccess, setDeactivateSuccess] = useState<string | null>(null);

    // Fetch applications
    const fetchApplications = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const statusParam = statusFilter === "all" ? undefined : statusFilter;
            const response = await api.getAcademyApplications(statusParam);
            setApplications(response.applications);
            setTotal(response.total);

            // Update parent with stats
            const paidCount = response.applications.filter((a) => a.status === "paid").length;
            const unlinkedCount = response.applications.filter(
                (a) => a.status === "paid" && !a.owner_id
            ).length;
            onDataUpdate?.({ paid: paidCount, unlinked: unlinkedCount, total: response.total });
        } catch (err) {
            setError(err instanceof Error ? err.message : "데이터를 불러오는 중 오류가 발생했습니다.");
        } finally {
            setLoading(false);
        }
    }, [statusFilter, onDataUpdate]);

    useEffect(() => {
        fetchApplications();
    }, [fetchApplications]);

    // Open link modal
    const openLinkModal = (app: AcademyApplication) => {
        setSelectedApp(app);
        setLinkEmail("");
        setLinkError(null);
        setLinkSuccess(null);
        setLinkModalOpen(true);
    };

    // Handle link account
    const handleLinkAccount = async () => {
        if (!selectedApp || !linkEmail.trim()) return;

        setLinking(true);
        setLinkError(null);
        setLinkSuccess(null);

        try {
            const response = await api.linkAcademyAccount(selectedApp.name, linkEmail.trim());

            if (response.success) {
                setLinkSuccess(response.message);
                setTimeout(() => {
                    setLinkModalOpen(false);
                    fetchApplications();
                }, 1500);
            } else {
                setLinkError(response.message);
            }
        } catch (err) {
            setLinkError(err instanceof Error ? err.message : "연결 중 오류가 발생했습니다.");
        } finally {
            setLinking(false);
        }
    };

    // Open deactivate modal
    const openDeactivateModal = (app: AcademyApplication) => {
        setDeactivateApp(app);
        setDeactivateError(null);
        setDeactivateSuccess(null);
        setDeactivateModalOpen(true);
    };

    // Handle deactivate
    const handleDeactivate = async () => {
        if (!deactivateApp) return;

        setDeactivating(true);
        setDeactivateError(null);
        setDeactivateSuccess(null);

        try {
            const response = await api.deactivateAcademyStudent(deactivateApp.email);

            if (response.success) {
                setDeactivateSuccess(response.message);
                setTimeout(() => {
                    setDeactivateModalOpen(false);
                    fetchApplications();
                }, 1500);
            } else {
                setDeactivateError(response.message);
            }
        } catch (err) {
            setDeactivateError(err instanceof Error ? err.message : "비활성화 중 오류가 발생했습니다.");
        } finally {
            setDeactivating(false);
        }
    };

    // Filter by search term
    const filteredApps = applications.filter((app) => {
        if (!searchTerm) return true;
        const term = searchTerm.toLowerCase();
        return (
            app.name.toLowerCase().includes(term) ||
            app.email.toLowerCase().includes(term) ||
            app.phone.includes(term)
        );
    });

    // Stats
    const paidCount = applications.filter((a) => a.status === "paid").length;
    const unlinkedCount = applications.filter((a) => a.status === "paid" && !a.owner_id).length;

    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-3 gap-4">
                <StatCard label="전체 신청" value={total} icon="people" color="blue" />
                <StatCard label="결제 완료" value={paidCount} icon="check_circle" color="green" />
                <StatCard label="미연결" value={unlinkedCount} icon="link_off" color="orange" />
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
                <div className="flex-1">
                    <div className="relative">
                        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xl">
                            search
                        </span>
                        <input
                            type="text"
                            placeholder="이름, 이메일, 전화번호 검색..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-white/10 border border-white/10 rounded-lg py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
                        />
                    </div>
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                    className="bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500/50"
                >
                    <option value="all">전체 상태</option>
                    <option value="paid">결제 완료</option>
                    <option value="pending">대기 중</option>
                    <option value="cancelled">취소</option>
                    <option value="refunded">환불</option>
                </select>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-red-400">error</span>
                        <span className="text-red-300">{error}</span>
                    </div>
                    <button
                        onClick={fetchApplications}
                        className="px-4 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition-colors text-sm font-medium"
                    >
                        재시도
                    </button>
                </div>
            )}

            {/* Success Banner */}
            {linkSuccess && !linkModalOpen && (
                <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30 flex items-center gap-3">
                    <span className="material-symbols-outlined text-green-400">check_circle</span>
                    <span className="text-green-300">{linkSuccess}</span>
                </div>
            )}

            {/* Table */}
            <div className="bg-[#0f0f11] border border-white/10 rounded-2xl overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center">
                        <div className="w-8 h-8 mx-auto rounded-full bg-gradient-to-tr from-purple-500 to-purple-400 animate-pulse" />
                        <p className="mt-4 text-gray-400">불러오는 중...</p>
                    </div>
                ) : filteredApps.length === 0 ? (
                    <div className="p-8 text-center">
                        <span className="material-symbols-outlined text-gray-500 text-4xl mb-2">inbox</span>
                        <p className="text-gray-400">표시할 데이터가 없습니다.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-left px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        이름
                                    </th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        이메일
                                    </th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        전화번호
                                    </th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        트랙
                                    </th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        상태
                                    </th>
                                    <th className="text-left px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        연결
                                    </th>
                                    <th className="text-right px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                        액션
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredApps.map((app) => (
                                    <tr
                                        key={app.id}
                                        className="border-b border-white/5 hover:bg-white/5 transition-colors"
                                    >
                                        <td className="px-6 py-4 text-sm text-white font-medium">{app.name}</td>
                                        <td className="px-6 py-4 text-sm text-gray-300">{app.email}</td>
                                        <td className="px-6 py-4 text-sm text-gray-300">{app.phone}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 py-1 rounded-md bg-purple-500/20 text-purple-300 text-xs font-medium">
                                                {app.track}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <StatusBadge status={app.status} />
                                        </td>
                                        <td className="px-6 py-4">
                                            {app.owner_id ? (
                                                <span className="flex items-center gap-1.5 text-green-400 text-sm">
                                                    <span className="material-symbols-outlined text-lg">link</span>
                                                    연결됨
                                                </span>
                                            ) : (
                                                <span className="flex items-center gap-1.5 text-gray-500 text-sm">
                                                    <span className="material-symbols-outlined text-lg">link_off</span>
                                                    미연결
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                {app.status === "paid" && !app.owner_id && (
                                                    <button
                                                        onClick={() => openLinkModal(app)}
                                                        className="px-3 py-1.5 rounded-lg bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors text-sm font-medium"
                                                    >
                                                        연결
                                                    </button>
                                                )}
                                                {app.status === "paid" && (
                                                    <button
                                                        onClick={() => openDeactivateModal(app)}
                                                        className="px-3 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition-colors text-sm font-medium"
                                                    >
                                                        비활성화
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Link Modal */}
            {linkModalOpen && selectedApp && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#0f0f11] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-white/10">
                            <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-purple-400">link</span>
                                <h3 className="text-lg font-bold text-white">계정 연결</h3>
                            </div>
                            <button
                                onClick={() => setLinkModalOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">수강생</label>
                                <div className="px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white">
                                    {selectedApp.name}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Google 이메일</label>
                                <input
                                    type="email"
                                    value={linkEmail}
                                    onChange={(e) => setLinkEmail(e.target.value)}
                                    placeholder="example@gmail.com"
                                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
                                />
                            </div>

                            {/* Warning */}
                            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                <div className="flex items-start gap-2">
                                    <span className="material-symbols-outlined text-amber-400 text-lg mt-0.5">
                                        warning
                                    </span>
                                    <p className="text-sm text-amber-300">
                                        수강생이 먼저 prompty.co.kr에서 Google 로그인해야 합니다.
                                    </p>
                                </div>
                            </div>

                            {/* Error */}
                            {linkError && (
                                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                    <div className="flex items-start gap-2">
                                        <span className="material-symbols-outlined text-red-400 text-lg mt-0.5">
                                            error
                                        </span>
                                        <p className="text-sm text-red-300">{linkError}</p>
                                    </div>
                                </div>
                            )}

                            {/* Success */}
                            {linkSuccess && (
                                <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                                    <div className="flex items-start gap-2">
                                        <span className="material-symbols-outlined text-green-400 text-lg mt-0.5">
                                            check_circle
                                        </span>
                                        <p className="text-sm text-green-300">{linkSuccess}</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-end gap-3 p-6 border-t border-white/10">
                            <button
                                onClick={() => setLinkModalOpen(false)}
                                className="px-4 py-2 rounded-lg bg-white/5 text-gray-300 hover:bg-white/10 transition-colors font-medium"
                            >
                                취소
                            </button>
                            <button
                                onClick={handleLinkAccount}
                                disabled={!linkEmail.trim() || linking}
                                className="px-4 py-2 rounded-lg bg-purple-500 text-white hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
                            >
                                {linking ? (
                                    <>
                                        <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                                        연결 중...
                                    </>
                                ) : (
                                    "연결"
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Deactivate Modal */}
            {deactivateModalOpen && deactivateApp && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#0f0f11] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-white/10">
                            <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-red-400">person_off</span>
                                <h3 className="text-lg font-bold text-white">수강생 비활성화</h3>
                            </div>
                            <button
                                onClick={() => setDeactivateModalOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">수강생</label>
                                <div className="px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white">
                                    {deactivateApp.name} ({deactivateApp.email})
                                </div>
                            </div>

                            {/* Warning */}
                            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                <div className="flex items-start gap-2">
                                    <span className="material-symbols-outlined text-red-400 text-lg mt-0.5">
                                        warning
                                    </span>
                                    <p className="text-sm text-red-300">
                                        이 수강생의 Academy 접근 권한이 취소됩니다. 계속하시겠습니까?
                                    </p>
                                </div>
                            </div>

                            {/* Error */}
                            {deactivateError && (
                                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                    <div className="flex items-start gap-2">
                                        <span className="material-symbols-outlined text-red-400 text-lg mt-0.5">
                                            error
                                        </span>
                                        <p className="text-sm text-red-300">{deactivateError}</p>
                                    </div>
                                </div>
                            )}

                            {/* Success */}
                            {deactivateSuccess && (
                                <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                                    <div className="flex items-start gap-2">
                                        <span className="material-symbols-outlined text-green-400 text-lg mt-0.5">
                                            check_circle
                                        </span>
                                        <p className="text-sm text-green-300">{deactivateSuccess}</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-end gap-3 p-6 border-t border-white/10">
                            <button
                                onClick={() => setDeactivateModalOpen(false)}
                                className="px-4 py-2 rounded-lg bg-white/5 text-gray-300 hover:bg-white/10 transition-colors font-medium"
                            >
                                취소
                            </button>
                            <button
                                onClick={handleDeactivate}
                                disabled={deactivating}
                                className="px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
                            >
                                {deactivating ? (
                                    <>
                                        <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                                        처리 중...
                                    </>
                                ) : (
                                    "비활성화"
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
