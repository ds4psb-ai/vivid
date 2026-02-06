/**
 * EnrollmentRequired
 * 접근 권한이 없는 사용자에게 워크플로우 프리뷰 + 전환 유도 랜딩을 제공합니다.
 */

"use client";

import { useState, useEffect } from "react";
import {
  ClipboardCopy,
  ScanSearch,
  Sparkles,
  Upload,
  Wrench,
} from "lucide-react";

interface EnrollmentRequiredProps {
  isLoggedIn?: boolean;
}

type RequestStatus = "idle" | "loading" | "pending" | "approved" | "rejected" | "error";

const SHOW_MEMBERSHIP = false;

const steps = [
  { num: 1, icon: Upload, label: "업로드", desc: "영상을 올리면" },
  { num: 2, icon: ScanSearch, label: "씬 감지", desc: "장면이 자동 추출되고" },
  { num: 3, icon: Sparkles, label: "프롬프터", desc: "AI가 4개 플랫폼 프롬프트 생성" },
  { num: 4, icon: ClipboardCopy, label: "파싱 + 복사", desc: "한 번에 복사해서" },
  { num: 5, icon: Wrench, label: "외부 툴", desc: "MJ, Kling, Veo에 붙여넣기" },
];

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
          <div className="inline-flex items-center gap-2 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-3 py-2 text-sm text-[var(--fg-muted)]">
            <span className="h-4 w-4 rounded-full border-2 border-[var(--border-muted)] border-t-[var(--color-brand-primary)] animate-spin" />
            요청 처리 중...
          </div>
        );
      case "pending":
        return (
          <div className="rounded-xl border border-amber-500/35 bg-amber-500/10 px-4 py-3">
            <p className="text-sm font-semibold text-amber-300">접근 요청 대기 중</p>
            <p className="mt-1 text-xs text-[var(--fg-muted)]">확인 후 승인됩니다.</p>
          </div>
        );
      case "approved":
        return (
          <div className="rounded-xl border border-green-500/35 bg-green-500/10 px-4 py-3">
            <p className="text-sm font-semibold text-green-300">접근 승인 완료</p>
            <p className="mt-1 text-xs text-[var(--fg-muted)]">새로고침 후 바로 이용할 수 있습니다.</p>
          </div>
        );
      case "rejected":
        return (
          <div className="rounded-xl border border-red-500/35 bg-red-500/10 px-4 py-3">
            <p className="text-sm font-semibold text-red-300">요청이 거절되었습니다</p>
            <p className="mt-1 text-xs text-[var(--fg-muted)]">문의 후 다시 요청해 주세요.</p>
          </div>
        );
      case "error":
        return (
          <div className="rounded-xl border border-red-500/35 bg-red-500/10 px-4 py-3">
            <p className="text-sm text-red-300">{errorMessage}</p>
            <button
              onClick={handleAccessRequest}
              className="mt-2 text-xs font-semibold text-[var(--color-brand-primary)] hover:opacity-80"
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
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-5">
        {/* 1. Hero 섹션 */}
        <section className="space-y-4 px-1">
          <div className="stagger-reveal inline-flex items-center rounded-full border border-[var(--color-brand-primary)]/35 bg-[var(--color-brand-primary)]/10 px-3 py-1 text-[10px] font-semibold tracking-widest text-[var(--color-brand-primary)] uppercase">
            Preview Access
          </div>

          <h1 className="stagger-reveal stagger-1 text-3xl font-semibold tracking-tight text-[var(--fg-0)] md:text-4xl">
            영상에서 프롬프트까지,<br className="hidden md:block" />
            5단계면 끝
          </h1>

          <p className="stagger-reveal stagger-2 max-w-2xl text-sm leading-relaxed text-[var(--fg-muted)] md:text-base">
            영상 업로드 → 자동 씬 감지 → AI 프롬프트 생성 → MJ·Kling·Veo에 바로 붙여넣기
          </p>
        </section>

        {/* 2. 워크플로우 프리뷰 (2:1 grid) */}
        <div className="grid gap-4 md:grid-cols-3">
          {/* 좌: 5단계 카드 리스트 */}
          <div className="stagger-reveal stagger-3 md:col-span-2 rounded-3xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-5 md:p-6">
            <div className="stagger-children space-y-3">
              {steps.map((step) => {
                const Icon = step.icon;
                return (
                  <div
                    key={step.num}
                    className="flex items-center gap-4 rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--color-brand-primary)]/15 text-sm font-bold text-[var(--color-brand-primary)]">
                      {step.num}
                    </div>
                    <Icon className="h-5 w-5 shrink-0 text-[var(--fg-muted)]" />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-[var(--fg-0)]">{step.label}</p>
                      <p className="text-xs text-[var(--fg-muted)]">{step.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 우: 실제 프롬프터 출력 예시 */}
          <div className="stagger-reveal stagger-4 relative overflow-hidden rounded-3xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-5 md:p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-[var(--color-brand-primary)]" />
              <p className="text-sm font-semibold text-[var(--fg-0)]">Scene 03 — 프롬프트 예시</p>
            </div>

            <div className="flex-1 space-y-3 text-xs leading-relaxed text-[var(--fg-muted)]">
              {/* MJ 프롬프트 예시 */}
              <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
                <p className="mb-1.5 text-[10px] font-bold tracking-wider text-[var(--color-brand-primary)] uppercase">Midjourney V7</p>
                <p className="line-clamp-3">
                  cinematic medium shot, male anchor standing in dimly lit alley, neon signs reflecting on wet pavement, volumetric fog, shallow depth of field --ar 9:16 --v 7 --style raw
                </p>
              </div>

              {/* Kling 프롬프트 예시 */}
              <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3">
                <p className="mb-1.5 text-[10px] font-bold tracking-wider text-emerald-400 uppercase">Kling 1.6</p>
                <p className="line-clamp-2">
                  카메라가 천천히 달리 인, 남성 앵커가 골목에서 고개를 돌리며 뒤를 바라본다. 네온 간판 빛이 얼굴 위로 번진다.
                </p>
              </div>

              {/* Veo 프롬프트 (블러 처리) */}
              <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-3 select-none">
                <p className="mb-1.5 text-[10px] font-bold tracking-wider text-blue-400 uppercase">Veo 2</p>
                <p className="blur-[6px]">
                  Slow dolly-in through a rain-soaked alley at night. The male anchor turns to look behind, neon signs painting streaks of red and blue across his face.
                </p>
              </div>
            </div>

            {/* 하단 잠금 오버레이 */}
            <div className="absolute inset-x-0 bottom-0 flex items-end justify-center bg-gradient-to-t from-[var(--surface-1)] via-[var(--surface-1)]/90 to-transparent px-4 pb-5 pt-16 pointer-events-none">
              <p className="text-xs font-semibold text-[var(--fg-muted)]">
                수강 후 전체 프롬프트 확인
              </p>
            </div>
          </div>
        </div>

        {/* 3. CTA 섹션 */}
        <section className="stagger-reveal stagger-5 rounded-3xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-5 md:p-6">
          <div className="flex flex-wrap items-center gap-2.5">
            {(requestStatus === "idle" || requestStatus === "error" || !isLoggedIn) && (
              <a
                href="https://cafe.naver.com/antacademy1/5150"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-11 items-center rounded-xl bg-[var(--color-brand-primary)] px-5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              >
                수강 신청하기
              </a>
            )}

            {!isLoggedIn && (
              <a
                href="/api/v1/auth/google/start"
                className="inline-flex min-h-11 items-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-5 text-sm font-semibold text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]"
              >
                Google 로그인
              </a>
            )}

            {isLoggedIn && requestStatus === "idle" && (
              <button
                onClick={handleAccessRequest}
                className="inline-flex min-h-11 items-center rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] px-5 text-sm font-semibold text-[var(--fg-0)] transition-colors hover:bg-[var(--surface-3)]"
              >
                접근 요청
              </button>
            )}
          </div>

          {isLoggedIn && requestStatus !== "idle" && (
            <div className="mt-3">
              {getStatusUI()}
            </div>
          )}

          <p className="mt-4 text-sm text-[var(--fg-muted)]">
            이미 결제하셨나요?{" "}
            <a
              href="mailto:ted.taeeun.kim@gmail.com"
              className="font-medium text-[var(--color-brand-primary)] hover:underline"
            >
              문의하기
            </a>
          </p>
        </section>

        {/* 4. 평생 멤버십 섹션 (Feature Flag) */}
        {SHOW_MEMBERSHIP && (
          <section className="stagger-reveal stagger-6 rounded-3xl border border-[var(--color-brand-primary)]/35 bg-[linear-gradient(135deg,var(--surface-1)_0%,var(--color-brand-primary)/5_100%)] p-6">
            <h2 className="text-xl font-semibold text-[var(--fg-0)]">평생 멤버십</h2>
            <p className="mt-2 text-2xl font-bold text-[var(--color-brand-primary)]">₩300,000</p>
            <p className="mt-1 text-xs text-[var(--fg-muted)]">일회성 결제 · 평생 이용</p>

            <ul className="mt-4 space-y-1.5 text-sm text-[var(--fg-muted)]">
              <li>✓ 무제한 프롬프트 생성</li>
              <li>✓ 모든 툴 연동</li>
              <li>✓ 평생 업데이트</li>
            </ul>

            <div className="mt-4 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-2)] p-4 text-sm text-[var(--fg-muted)]">
              <p className="font-semibold text-[var(--fg-0)]">무통장 입금</p>
              <p className="mt-1">은행: (계좌 정보 확인 필요)</p>
              <p>예금주: (확인 필요)</p>
            </div>

            <a
              href="mailto:ted.taeeun.kim@gmail.com?subject=평생 멤버십 입금 문의"
              className="mt-4 inline-flex min-h-11 items-center rounded-xl border border-[var(--color-brand-primary)]/35 bg-[var(--color-brand-primary)]/10 px-5 text-sm font-semibold text-[var(--color-brand-primary)] transition-opacity hover:opacity-80"
            >
              입금 후 문의하기
            </a>
          </section>
        )}
    </div>
  );
}
