/**
 * EnrollmentRequired - 미등록 사용자 안내 컴포넌트
 * Academy 접근 권한이 없는 사용자에게 수강 신청 안내를 보여줍니다.
 */

"use client";

import { useState, useEffect } from "react";

interface EnrollmentRequiredProps {
  isLoggedIn?: boolean;
}

type RequestStatus = "idle" | "loading" | "pending" | "approved" | "rejected" | "error";

// CSRF 토큰을 쿠키에서 가져오는 헬퍼
function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

export function EnrollmentRequired({ isLoggedIn = false }: EnrollmentRequiredProps) {
  const [requestStatus, setRequestStatus] = useState<RequestStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Check existing request status on mount (only if logged in)
  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;

    const loadRequestStatus = async () => {
      try {
        const csrfToken = getCsrfToken();
        const response = await fetch("/api/v1/access-request/status", {
          credentials: "include",
          headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
        });
        if (!response.ok || cancelled) return;
        const data = await response.json();
        if (!cancelled && data.has_request) {
          setRequestStatus(data.status as RequestStatus);
        }
      } catch (err) {
        console.error("Failed to check request status:", err);
      }
    };

    void loadRequestStatus();
    return () => {
      cancelled = true;
    };
  }, [isLoggedIn]);

  const handleAccessRequest = async () => {
    setRequestStatus("loading");
    setErrorMessage("");

    try {
      const csrfToken = getCsrfToken();
      const response = await fetch("/api/v1/access-request", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        credentials: "include",
        body: JSON.stringify({}),
      });

      if (response.ok || response.status === 201) {
        const data = await response.json();
        setRequestStatus(data.status as RequestStatus);
      } else {
        const error = await response.json();
        setErrorMessage(error.detail || "요청 처리 중 오류가 발생했습니다.");
        setRequestStatus("error");
      }
    } catch {
      setErrorMessage("네트워크 오류가 발생했습니다.");
      setRequestStatus("error");
    }
  };

  const getStatusUI = () => {
    switch (requestStatus) {
      case "loading":
        return (
          <div className="flex items-center gap-2 text-purple-400">
            <span className="material-symbols-outlined animate-spin text-xl">progress_activity</span>
            <span>요청 처리 중...</span>
          </div>
        );
      case "pending":
        return (
          <div className="px-6 py-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-2xl text-amber-400">schedule</span>
              <div>
                <p className="font-bold text-amber-300">접근 요청 대기 중</p>
                <p className="text-sm text-gray-400">확인 후 연락드리겠습니다.</p>
              </div>
            </div>
          </div>
        );
      case "approved":
        return (
          <div className="px-6 py-4 bg-green-500/10 border border-green-500/30 rounded-2xl">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-2xl text-green-400">check_circle</span>
              <div>
                <p className="font-bold text-green-300">접근이 승인되었습니다</p>
                <p className="text-sm text-gray-400">페이지를 새로고침 해주세요.</p>
              </div>
            </div>
          </div>
        );
      case "rejected":
        return (
          <div className="px-6 py-4 bg-red-500/10 border border-red-500/30 rounded-2xl">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-2xl text-red-400">cancel</span>
              <div>
                <p className="font-bold text-red-300">요청이 거절되었습니다</p>
                <p className="text-sm text-gray-400">문의가 필요하시면 연락주세요.</p>
              </div>
            </div>
          </div>
        );
      case "error":
        return (
          <div className="px-6 py-4 bg-red-500/10 border border-red-500/30 rounded-2xl">
            <p className="text-red-400">{errorMessage}</p>
            <button
              onClick={handleAccessRequest}
              className="mt-2 text-sm text-purple-400 hover:text-purple-300 underline"
            >
              다시 시도
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-0)] flex items-center justify-center p-6">
      <div className="w-full max-w-lg rounded-3xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-8 text-center shadow-xl">
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-brand-primary)]/30 bg-[var(--color-brand-primary)]/10 px-3 py-1 text-[10px] font-bold tracking-widest text-[var(--color-brand-primary)] uppercase mb-6">
          Members Only
        </div>

        <h1 className="text-2xl font-black text-[var(--fg-0)] mb-3">수강생 전용 페이지</h1>
        <p className="text-[var(--fg-muted)] mb-6 leading-relaxed">
          AI Academy 콘텐츠 이용을 위해
          <br />
          수강 신청 및 승인 절차가 필요합니다.
        </p>

        {!isLoggedIn && (
          <a
            href="/api/v1/auth/google/start"
            className="inline-flex items-center gap-3 px-6 py-3 bg-[var(--fg-0)] text-[var(--bg-0)] font-bold rounded-xl hover:opacity-90 transition-all mb-4"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Google 로그인
          </a>
        )}

        {isLoggedIn && requestStatus === "idle" && (
          <button
            onClick={handleAccessRequest}
            className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--color-brand-primary)] text-white font-bold rounded-xl hover:opacity-90 transition-all mb-4"
          >
            <span className="material-symbols-outlined text-lg">send</span>
            접근 요청하기
          </button>
        )}

        {isLoggedIn && requestStatus !== "idle" && <div className="mb-4">{getStatusUI()}</div>}

        {(requestStatus === "idle" || requestStatus === "error" || !isLoggedIn) && (
          <a
            href="https://cafe.naver.com/antacademy1/5150"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 border border-[var(--color-brand-primary)]/40 text-[var(--color-brand-primary)] font-bold rounded-xl hover:bg-[var(--color-brand-primary)]/10 transition-all"
          >
            <span className="material-symbols-outlined text-lg">arrow_forward</span>
            수강 신청하기
          </a>
        )}

        <p className="text-sm text-[var(--fg-muted)] mt-6">
          이미 결제하셨나요?{" "}
          <a
            href="mailto:ted.taeeun.kim@gmail.com"
            className="text-[var(--color-brand-primary)] hover:underline"
          >
            문의하기
          </a>
        </p>
      </div>
    </div>
  );
}
