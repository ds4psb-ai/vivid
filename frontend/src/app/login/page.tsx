"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { LogIn, AlertCircle } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";

function LoginContent() {
  const { language } = useLanguage();
  const searchParams = useSearchParams();
  const error = searchParams.get("error") || searchParams.get("reason");
  const isExpired = searchParams.get("expired") === "true";
  const [oauthAvailable, setOauthAvailable] = useState<boolean | null>(null);
  const authStartUrl = (() => {
    const base = process.env.NEXT_PUBLIC_API_URL || "";
    return base ? `${base}/api/v1/auth/google/start` : "/api/v1/auth/google/start";
  })();

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const base = process.env.NEXT_PUBLIC_API_URL || "";
        const statusUrl = base ? `${base}/api/v1/auth/status` : "/api/v1/auth/status";
        const res = await fetch(statusUrl);
        if (res.ok) {
          const data = await res.json();
          setOauthAvailable(data.google_oauth_available ?? false);
        } else {
          setOauthAvailable(false);
        }
      } catch {
        setOauthAvailable(false);
      }
    };
    checkAuthStatus();
  }, []);

  const labels = {
    title: language === "ko" ? "로그인" : "Sign in",
    subtitle:
      language === "ko"
        ? "Google 계정으로 Crebit에 로그인하세요."
        : "Sign in to Crebit with your Google account.",
    button: language === "ko" ? "Google로 계속하기" : "Continue with Google",
    error:
      language === "ko"
        ? "로그인에 실패했습니다. 다시 시도해주세요."
        : "Authentication failed. Please try again.",
    expired:
      language === "ko"
        ? "세션이 만료되었습니다. 다시 로그인해주세요."
        : "Your session has expired. Please sign in again.",
    notConfigured:
      language === "ko"
        ? "Google OAuth가 설정되지 않았습니다. 관리자에게 문의하세요."
        : "Google OAuth is not configured. Please contact administrator.",
    checking:
      language === "ko"
        ? "인증 상태 확인 중..."
        : "Checking authentication status...",
    terms: language === "ko" ? "서비스 이용약관" : "Terms of Service",
    privacy: language === "ko" ? "개인정보 처리방침" : "Privacy Policy",
    guidanceTitle:
      language === "ko" ? "로그인 후 바로 할 수 있는 작업" : "What you can do right away",
    guidanceItems:
      language === "ko"
        ? [
            "워크플로우 시작",
            "크레딧/상태 확인",
            "프로젝트 이어서 작업",
          ]
        : [
            "Start workflows",
            "Check credits and status",
            "Resume your projects",
          ],
  };

  return (
    <div className="min-h-screen px-6 py-16">
      <div className="mx-auto max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-6"
        >
          <h1 className="text-2xl font-semibold text-[var(--fg-0)]">{labels.title}</h1>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">{labels.subtitle}</p>

          <div className="mt-4 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-1)]/70 px-4 py-3">
            <p className="text-xs font-semibold text-[var(--fg-subtle)]">{labels.guidanceTitle}</p>
            <ul className="mt-2 space-y-1 text-sm text-[var(--fg-muted)]">
              {labels.guidanceItems.map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {isExpired && (
            <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              {labels.expired}
            </div>
          )}

          {error && !isExpired && (
            <div className="mt-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {labels.error}
            </div>
          )}

          {oauthAvailable === null ? (
            <div className="mt-6 flex items-center justify-center gap-2 rounded-lg bg-[var(--bg-2)] px-4 py-2 text-sm text-[var(--fg-muted)]">
              {labels.checking}
            </div>
          ) : oauthAvailable ? (
            <Link
              href={authStartUrl}
              className="mt-6 flex items-center justify-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90"
            >
              <LogIn className="h-4 w-4" aria-hidden="true" />
              {labels.button}
            </Link>
          ) : (
            <div className="mt-6 flex items-center justify-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
              {labels.notConfigured}
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-3 text-xs text-[var(--fg-muted)]">
            <Link href="/terms?tab=terms" className="hover:text-[var(--fg-0)]">
              {labels.terms}
            </Link>
            <Link href="/terms?tab=privacy" className="hover:text-[var(--fg-0)]">
              {labels.privacy}
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AppShell showSidebar={false} showTopBar={false}>
      <Suspense fallback={<div className="min-h-screen" />}>
        <LoginContent />
      </Suspense>
    </AppShell>
  );
}
