"use client";

import { useState } from "react";
import { api } from "@/lib/api";

// =============================================================================
// Main Component
// =============================================================================

interface QuickActivateTabProps {
    onActivated?: () => void;
}

export function QuickActivateTab({ onActivated }: QuickActivateTabProps) {
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
                setTimeout(() => onActivated?.(), 1000);
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

            if (response.success_count > 0) {
                setTimeout(() => onActivated?.(), 1000);
            }
        } catch (err) {
            setBulkResults([{
                email: "error",
                success: false,
                message: err instanceof Error ? err.message : "벌크 활성화 실패",
            }]);
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
                            onClick={() => { setBulkMode(false); setBulkResults(null); }}
                            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${!bulkMode ? "bg-purple-500 text-white" : "text-gray-400 hover:text-white"}`}
                        >
                            단일
                        </button>
                        <button
                            onClick={() => { setBulkMode(true); setActivateResult(null); }}
                            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${bulkMode ? "bg-purple-500 text-white" : "text-gray-400 hover:text-white"}`}
                        >
                            벌크
                        </button>
                    </div>
                </div>
                <p className="text-sm text-gray-400 mb-4">
                    {bulkMode
                        ? "여러 Gmail을 줄바꿈으로 구분해서 입력하세요 (최대 20개)"
                        : "카톡방에서 받은 Gmail 주소를 입력하면 즉시 수강생으로 활성화됩니다."
                    }
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
                                className={`mt-4 p-3 rounded-lg ${activateResult.success
                                    ? "bg-green-500/10 border border-green-500/20"
                                    : "bg-red-500/10 border border-red-500/20"
                                }`}
                            >
                                <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-2 flex-1">
                                        <span
                                            className={`material-symbols-outlined text-lg ${activateResult.success ? "text-green-400" : "text-red-400"}`}
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
                                        className={`p-2 rounded-lg text-xs flex items-center gap-2 ${r.success
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
            <div className="p-6 rounded-2xl bg-[var(--surface-1)]/70 border border-white/5">
                <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                    <span className="material-symbols-outlined text-lg text-blue-400">help</span>
                    사용 가이드
                </h4>
                <div className="space-y-3 text-sm text-gray-400">
                    <div className="flex items-start gap-2">
                        <span className="text-purple-400">1.</span>
                        <p>수강생이 <span className="text-white">prompty.co.kr</span>에서 Google 로그인</p>
                    </div>
                    <div className="flex items-start gap-2">
                        <span className="text-purple-400">2.</span>
                        <p>수강생의 Gmail 주소를 카톡에서 받음</p>
                    </div>
                    <div className="flex items-start gap-2">
                        <span className="text-purple-400">3.</span>
                        <p>위 입력창에 Gmail 입력 후 <span className="text-purple-300">활성화</span> 버튼 클릭</p>
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
