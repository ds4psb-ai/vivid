"use client";

import { useState, useEffect, useCallback } from "react";
import { api, type AcademyApplication, type AcademyDeactivateResponse } from "@/lib/api";

type StatusFilter = "all" | "pending" | "paid" | "cancelled" | "refunded";
type AdminTab = "students" | "requests" | "activate";

// =============================================================================
// Types
// =============================================================================

interface AccessRequestItem {
  id: string;
  user_id: string;
  email: string;
  name: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface AccessRequestListResponse {
  requests: AccessRequestItem[];
  total: number;
  pending_count: number;
}

// =============================================================================
// AdminContent Component
// =============================================================================

export function AdminContent() {
  const [activeTab, setActiveTab] = useState<AdminTab>("students");

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">수강생 관리</h2>
        <p className="text-gray-400">수강 신청, 접근 요청, 빠른 활성화를 한 곳에서 관리</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 mb-6 p-1 bg-white/5 rounded-xl w-fit">
        <TabButton
          active={activeTab === "students"}
          onClick={() => setActiveTab("students")}
          icon="people"
          label="수강생"
        />
        <TabButton
          active={activeTab === "requests"}
          onClick={() => setActiveTab("requests")}
          icon="how_to_reg"
          label="접근 요청"
        />
        <TabButton
          active={activeTab === "activate"}
          onClick={() => setActiveTab("activate")}
          icon="bolt"
          label="빠른 활성화"
        />
      </div>

      {/* Tab Content */}
      {activeTab === "students" && <StudentsTab />}
      {activeTab === "requests" && <AccessRequestsTab />}
      {activeTab === "activate" && <QuickActivateTab />}
    </div>
  );
}

// =============================================================================
// Tab Button
// =============================================================================

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: string;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        active
          ? "bg-purple-500/20 text-purple-300"
          : "text-gray-400 hover:text-white hover:bg-white/5"
      }`}
    >
      <span className="material-symbols-outlined text-lg">{icon}</span>
      {label}
    </button>
  );
}

// =============================================================================
// Students Tab (수강 신청 관리 + 비활성화)
// =============================================================================

function StudentsTab() {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터를 불러오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

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
        <Modal onClose={() => setLinkModalOpen(false)}>
          <div className="flex items-center gap-3 mb-6">
            <span className="material-symbols-outlined text-purple-400">link</span>
            <h3 className="text-lg font-bold text-white">계정 연결</h3>
          </div>

          <div className="space-y-4">
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

            <AlertBox type="warning">
              수강생이 먼저 prompty.co.kr에서 Google 로그인해야 합니다.
            </AlertBox>

            {linkError && <AlertBox type="error">{linkError}</AlertBox>}
            {linkSuccess && <AlertBox type="success">{linkSuccess}</AlertBox>}
          </div>

          <div className="flex items-center justify-end gap-3 mt-6">
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
        </Modal>
      )}

      {/* Deactivate Modal */}
      {deactivateModalOpen && deactivateApp && (
        <Modal onClose={() => setDeactivateModalOpen(false)}>
          <div className="flex items-center gap-3 mb-6">
            <span className="material-symbols-outlined text-red-400">person_off</span>
            <h3 className="text-lg font-bold text-white">수강생 비활성화</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">수강생</label>
              <div className="px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white">
                {deactivateApp.name} ({deactivateApp.email})
              </div>
            </div>

            <AlertBox type="error">
              이 수강생의 Academy 접근 권한이 취소됩니다. 계속하시겠습니까?
            </AlertBox>

            {deactivateError && <AlertBox type="error">{deactivateError}</AlertBox>}
            {deactivateSuccess && <AlertBox type="success">{deactivateSuccess}</AlertBox>}
          </div>

          <div className="flex items-center justify-end gap-3 mt-6">
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
        </Modal>
      )}
    </div>
  );
}

// =============================================================================
// Access Requests Tab (접근 요청 관리)
// =============================================================================

function AccessRequestsTab() {
  const [data, setData] = useState<AccessRequestListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("pending");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusParam = filter === "all" ? "" : `?status=${filter}`;
      const response = await api.get<AccessRequestListResponse>(
        `/api/v1/access-request/admin/list${statusParam}`
      );
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터를 불러오지 못했습니다");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApprove = async (id: string) => {
    setProcessingId(id);
    try {
      await api.patch(`/api/v1/access-request/admin/${id}/approve`, {});
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "승인 처리 실패");
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: string) => {
    setProcessingId(id);
    try {
      await api.patch(`/api/v1/access-request/admin/${id}/reject`, {});
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "거절 처리 실패");
    } finally {
      setProcessingId(null);
    }
  };

  const handleRevoke = async (id: string) => {
    setProcessingId(id);
    try {
      await api.revokeAccessRequest(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "승인 취소 실패");
    } finally {
      setProcessingId(null);
    }
  };

  const statusColors: Record<string, string> = {
    pending: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    approved: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    rejected: "bg-red-500/20 text-red-300 border-red-500/30",
  };

  const statusLabels: Record<string, string> = {
    pending: "대기 중",
    approved: "승인됨",
    rejected: "거절됨",
  };

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      <div className="flex gap-2">
        {[
          { key: "pending", label: "대기 중" },
          { key: "approved", label: "승인됨" },
          { key: "rejected", label: "거절됨" },
          { key: "all", label: "전체" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              filter === tab.key
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                : "text-gray-400 hover:bg-white/5"
            }`}
          >
            {tab.label}
            {tab.key === "pending" && data && data.pending_count > 0 && (
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-amber-500/30 text-amber-300 rounded-full">
                {data.pending_count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
          <span className="material-symbols-outlined text-red-400">error</span>
          <p className="text-red-300">{error}</p>
          <button
            onClick={fetchData}
            className="ml-auto px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm"
          >
            재시도
          </button>
        </div>
      )}

      {/* Request List */}
      <div className="border border-white/10 bg-[#0f0f11] rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="material-symbols-outlined text-purple-400">mail</span>
          <h3 className="text-base font-medium text-white">접근 요청 목록</h3>
          <span className="px-2 py-0.5 text-xs bg-white/10 text-gray-400 rounded-full">
            {data?.requests.length ?? 0}개
          </span>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="rounded-xl border border-white/5 bg-white/5 p-4 animate-pulse"
              >
                <div className="h-4 w-48 bg-white/10 rounded mb-2" />
                <div className="h-3 w-32 bg-white/10 rounded" />
              </div>
            ))}
          </div>
        ) : data?.requests.length === 0 ? (
          <div className="text-center py-8">
            <span className="material-symbols-outlined text-gray-500 text-4xl mb-2">check_circle</span>
            <p className="text-gray-400">
              {filter === "pending" ? "대기 중인 접근 요청이 없습니다." : "해당 상태의 요청이 없습니다."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {data?.requests.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-white/5 bg-white/5 p-4 transition-colors hover:border-purple-500/30"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="material-symbols-outlined text-purple-400 text-lg">mail</span>
                      <span className="text-white font-medium truncate">{item.email}</span>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full border ${
                          statusColors[item.status] || statusColors.pending
                        }`}
                      >
                        {statusLabels[item.status] || item.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      {item.name && <span>{item.name}</span>}
                      {item.name && <span>•</span>}
                      <span>{new Date(item.created_at).toLocaleString("ko-KR")}</span>
                    </div>
                  </div>

                  {item.status === "pending" && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleApprove(item.id)}
                        disabled={processingId === item.id}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 transition-colors text-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <span className="material-symbols-outlined text-lg">check_circle</span>
                        승인
                      </button>
                      <button
                        onClick={() => handleReject(item.id)}
                        disabled={processingId === item.id}
                        className="px-3 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition-colors text-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <span className="material-symbols-outlined text-lg">cancel</span>
                        거절
                      </button>
                    </div>
                  )}

                  {item.status === "approved" && (
                    <button
                      onClick={() => handleRevoke(item.id)}
                      disabled={processingId === item.id}
                      className="px-3 py-1.5 rounded-lg bg-orange-500/20 text-orange-300 hover:bg-orange-500/30 transition-colors text-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-lg">undo</span>
                      승인 취소
                    </button>
                  )}

                  {item.status === "rejected" && (
                    <button
                      onClick={() => handleApprove(item.id)}
                      disabled={processingId === item.id}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 transition-colors text-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-lg">check_circle</span>
                      재승인
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Quick Activate Tab (빠른 활성화)
// =============================================================================

function QuickActivateTab() {
  // Single activate state
  const [activateEmail, setActivateEmail] = useState("");
  const [activateName, setActivateName] = useState("");
  const [activating, setActivating] = useState(false);
  const [activateResult, setActivateResult] = useState<{ success: boolean; message: string } | null>(null);

  // Bulk activate state
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkEmails, setBulkEmails] = useState("");
  const [bulkResults, setBulkResults] = useState<{ email: string; success: boolean; message: string }[] | null>(null);

  // Single activate handler
  const handleQuickActivate = async () => {
    if (!activateEmail.trim()) return;

    setActivating(true);
    setActivateResult(null);

    try {
      const response = await api.activateAcademyStudent(activateEmail.trim(), activateName.trim());
      setActivateResult({ success: response.success, message: response.message });

      if (response.success) {
        setActivateEmail("");
        setActivateName("");
      }
    } catch (err) {
      setActivateResult({
        success: false,
        message: err instanceof Error ? err.message : "활성화 중 오류가 발생했습니다.",
      });
    } finally {
      setActivating(false);
    }
  };

  // Bulk activate handler
  const handleBulkActivate = async () => {
    const emails = bulkEmails
      .split("\n")
      .map((e) => e.trim())
      .filter((e) => e.includes("@"));

    if (emails.length === 0) return;

    setActivating(true);
    setBulkResults(null);

    try {
      const response = await api.post<{
        total: number;
        success_count: number;
        fail_count: number;
        results: { email: string; success: boolean; message: string }[];
      }>("/api/v1/admin/academy/activate-bulk", { emails, cohort: "1기" });

      setBulkResults(response.results);
    } catch (err) {
      setBulkResults([
        {
          email: "error",
          success: false,
          message: err instanceof Error ? err.message : "벌크 활성화 실패",
        },
      ]);
    } finally {
      setActivating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick Activate Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-500/30">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-purple-400 text-2xl">bolt</span>
            <h3 className="text-lg font-bold text-white">빠른 활성화</h3>
          </div>
          {/* Single/Bulk toggle */}
          <div className="flex items-center gap-2 bg-white/5 rounded-lg p-1">
            <button
              onClick={() => {
                setBulkMode(false);
                setBulkResults(null);
              }}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                !bulkMode ? "bg-purple-500 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              단일
            </button>
            <button
              onClick={() => {
                setBulkMode(true);
                setActivateResult(null);
              }}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                bulkMode ? "bg-purple-500 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              벌크
            </button>
          </div>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          {bulkMode
            ? "여러 Gmail을 줄바꿈으로 구분해서 입력하세요 (최대 20개)"
            : "카톡방에서 받은 Gmail 주소를 입력하면 즉시 수강생으로 활성화됩니다."}
          <br />
          <span className="text-amber-400">※ 수강생이 먼저 prompty.co.kr에서 Google 로그인해야 합니다.</span>
        </p>

        {/* Single mode UI */}
        {!bulkMode && (
          <>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="이름 (선택)"
                value={activateName}
                onChange={(e) => setActivateName(e.target.value)}
                className="w-40 bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
              />
              <input
                type="email"
                placeholder="Gmail 주소 입력"
                value={activateEmail}
                onChange={(e) => setActivateEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleQuickActivate()}
                className="flex-1 bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
              />
              <button
                onClick={handleQuickActivate}
                disabled={!activateEmail.trim() || activating}
                className="px-6 py-2.5 rounded-lg bg-purple-500 text-white font-medium hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {activating ? (
                  <>
                    <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                    처리 중
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-lg">person_add</span>
                    활성화
                  </>
                )}
              </button>
            </div>
            {activateResult && (
              <div
                className={`mt-4 p-3 rounded-lg ${
                  activateResult.success
                    ? "bg-green-500/10 border border-green-500/20"
                    : "bg-red-500/10 border border-red-500/20"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1">
                    <span
                      className={`material-symbols-outlined text-lg ${
                        activateResult.success ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {activateResult.success ? "check_circle" : "error"}
                    </span>
                    <p className={`text-sm ${activateResult.success ? "text-green-300" : "text-red-300"}`}>
                      {activateResult.message}
                    </p>
                  </div>
                  {!activateResult.success && activateResult.message.includes("로그인") && (
                    <button
                      onClick={() => {
                        const msg = `[수강생님] prompty.co.kr 접속 후 Google 로그인 먼저 해주세요! 로그인 완료되면 다시 말씀해주세요 ✅`;
                        navigator.clipboard.writeText(msg);
                        setActivateResult({
                          success: false,
                          message: "📋 카톡 메시지 복사됨! 수강생에게 보내세요",
                        });
                      }}
                      className="px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors text-xs font-medium flex items-center gap-1.5 whitespace-nowrap"
                    >
                      <span className="material-symbols-outlined text-sm">content_copy</span>
                      카톡 복붙
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {/* Bulk mode UI */}
        {bulkMode && (
          <>
            <div className="flex gap-3">
              <textarea
                placeholder={"user1@gmail.com\nuser2@gmail.com\nuser3@gmail.com"}
                value={bulkEmails}
                onChange={(e) => setBulkEmails(e.target.value)}
                rows={4}
                className="flex-1 bg-white/10 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 resize-none font-mono"
              />
              <button
                onClick={handleBulkActivate}
                disabled={!bulkEmails.trim() || activating}
                className="px-6 py-2.5 rounded-lg bg-purple-500 text-white font-medium hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 self-end"
              >
                {activating ? (
                  <>
                    <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                    처리 중
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-lg">group_add</span>
                    일괄 활성화
                  </>
                )}
              </button>
            </div>
            {bulkResults && (
              <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
                {bulkResults.map((r, i) => (
                  <div
                    key={i}
                    className={`p-2 rounded-lg text-xs flex items-center gap-2 ${
                      r.success
                        ? "bg-green-500/10 border border-green-500/20 text-green-300"
                        : "bg-red-500/10 border border-red-500/20 text-red-300"
                    }`}
                  >
                    <span className="material-symbols-outlined text-sm">
                      {r.success ? "check_circle" : "error"}
                    </span>
                    <span className="font-mono">{r.email}</span>
                    <span className="text-gray-400">→</span>
                    <span>{r.message}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Usage Guide */}
      <div className="p-6 rounded-2xl bg-[#0f0f11] border border-white/10">
        <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
          <span className="material-symbols-outlined text-lg text-blue-400">help</span>
          사용 가이드
        </h4>
        <div className="space-y-3 text-sm text-gray-400">
          <div className="flex items-start gap-2">
            <span className="text-purple-400">1.</span>
            <p>
              수강생이 <span className="text-white">prompty.co.kr</span>에서 Google 로그인
            </p>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-purple-400">2.</span>
            <p>수강생의 Gmail 주소를 카톡에서 받음</p>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-purple-400">3.</span>
            <p>
              위 입력창에 Gmail 입력 후 <span className="text-purple-300">활성화</span> 버튼 클릭
            </p>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-purple-400">4.</span>
            <p>수강생이 Academy 접근 가능!</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Shared Components
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
    <div className={`p-6 rounded-2xl bg-gradient-to-br ${colorMap[color]} border`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <span className="material-symbols-outlined text-3xl opacity-50">{icon}</span>
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

  return <span className={`px-2 py-1 rounded-md text-xs font-medium ${color}`}>{label}</span>;
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0f0f11] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl p-6">
        {children}
      </div>
    </div>
  );
}

function AlertBox({
  type,
  children,
}: {
  type: "warning" | "error" | "success";
  children: React.ReactNode;
}) {
  const styles = {
    warning: "bg-amber-500/10 border-amber-500/20 text-amber-300",
    error: "bg-red-500/10 border-red-500/20 text-red-300",
    success: "bg-green-500/10 border-green-500/20 text-green-300",
  };

  const icons = {
    warning: "warning",
    error: "error",
    success: "check_circle",
  };

  const iconColors = {
    warning: "text-amber-400",
    error: "text-red-400",
    success: "text-green-400",
  };

  return (
    <div className={`p-3 rounded-lg border ${styles[type]}`}>
      <div className="flex items-start gap-2">
        <span className={`material-symbols-outlined text-lg mt-0.5 ${iconColors[type]}`}>
          {icons[type]}
        </span>
        <p className="text-sm">{children}</p>
      </div>
    </div>
  );
}
