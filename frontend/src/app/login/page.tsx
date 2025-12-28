"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { LogIn } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";

function LoginContent() {
  const { language } = useLanguage();
  const searchParams = useSearchParams();
  const error = searchParams.get("error") || searchParams.get("reason");
  const authStartUrl = (() => {
    const base = process.env.NEXT_PUBLIC_API_URL || "";
    return base ? `${base}/api/v1/auth/google/start` : "/api/v1/auth/google/start";
  })();

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
    terms: language === "ko" ? "서비스 이용약관" : "Terms of Service",
    privacy: language === "ko" ? "개인정보 처리방침" : "Privacy Policy",
  };

  return (
    <div className="min-h-screen px-6 py-16">
      <div className="mx-auto max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 backdrop-blur-xl"
        >
          <h1 className="text-2xl font-semibold text-[var(--fg-0)]">{labels.title}</h1>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">{labels.subtitle}</p>

          {error && (
            <div className="mt-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {labels.error}
            </div>
          )}

          <Link
            href={authStartUrl}
            className="mt-6 flex items-center justify-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-slate-950 transition hover:opacity-90"
          >
            <LogIn className="h-4 w-4" aria-hidden="true" />
            {labels.button}
          </Link>

          <div className="mt-6 flex flex-wrap gap-3 text-xs text-[var(--fg-muted)]">
            <Link href="/crebit/terms?tab=terms" className="hover:text-[var(--fg-0)]">
              {labels.terms}
            </Link>
            <Link href="/crebit/terms?tab=privacy" className="hover:text-[var(--fg-0)]">
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
