"use client";

/**
 * Root Page (/)
 * - 비로그인: EnrollmentRequired (로그인 + 수강신청 안내)
 * - 로그인 + 접근권한: AppShell + Academy (사이드바 탭 전환)
 * - 로그인 + 권한없음: EnrollmentRequired
 */

import { useState, useEffect, Suspense, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";

import { type TabKey } from "./academy/constants";
import {
  HomeContent,
  SetupContent,
  CreditContent,
  VibeContent,
  HomeworkContent,
  PromptContent,
  UploadContent,
  ParseContent,
  ToolsContent,
  EnrollmentRequired,
  AdminContent,
} from "./academy/components";
import { api, type AcademyAccessResponse } from "@/lib/api";
import AppShell from "@/components/AppShell";

export default function RootPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <RootContent />
    </Suspense>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-[var(--bg-0)] flex items-center justify-center">
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-purple-400 animate-pulse" />
    </div>
  );
}

function RootContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeTab: TabKey = (searchParams.get("tab") as TabKey) || "home";

  const [accessState, setAccessState] = useState<{
    loading: boolean;
    hasAccess: boolean;
    isLoggedIn: boolean;
    accessInfo: AcademyAccessResponse | null;
  }>({
    loading: true,
    hasAccess: false,
    isLoggedIn: false,
    accessInfo: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function checkAccess() {
      try {
        const response = await api.checkAcademyAccess();
        if (!cancelled) {
          setAccessState({
            loading: false,
            hasAccess: response.can_access,
            isLoggedIn: true,
            accessInfo: response,
          });
        }
      } catch (err) {
        const status = (err as { status?: number })?.status;
        if (!cancelled) {
          setAccessState({
            loading: false,
            hasAccess: false,
            isLoggedIn: status === 403,
            accessInfo: null,
          });
        }
      }
    }

    checkAccess();
    return () => { cancelled = true; };
  }, []);

  const handleTabChange = useCallback((tab: TabKey) => {
    router.push(tab === "home" ? "/" : `/?tab=${tab}`, { scroll: false });
  }, [router]);

  // Guard: redirect non-admin users away from admin tab
  useEffect(() => {
    if (!accessState.loading && activeTab === "admin" && !accessState.accessInfo?.is_admin) {
      router.push("/", { scroll: false });
    }
  }, [accessState.loading, accessState.accessInfo?.is_admin, activeTab, router]);

  if (accessState.loading) {
    return <LoadingScreen />;
  }

  // No access → EnrollmentRequired (handles both logged-out and enrolled-but-no-access)
  if (!accessState.hasAccess) {
    return <EnrollmentRequired isLoggedIn={accessState.isLoggedIn} />;
  }

  // Has access → AppShell + Academy content (tab bar removed, sidebar handles navigation)
  return (
    <AppShell showChokki={false}>
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />

      <style jsx global>{`
        .material-symbols-outlined {
          font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .glow-text {
          text-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
        }
      `}</style>

      <div className="min-h-screen">
        {/* Simple Header */}
        <div className="px-6 pt-5 pb-3">
          <h1 className="text-lg font-bold text-[var(--fg-0)]">AI Academy</h1>
          <p className="text-[10px] font-mono text-[var(--fg-muted)] uppercase tracking-widest mt-0.5">
            Creative Automation Suite v2.0
            {accessState.accessInfo?.cohort && (
              <span className="ml-3 text-purple-400">{accessState.accessInfo.cohort}</span>
            )}
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === "home" && <HomeContent setActiveTab={handleTabChange} />}
          {activeTab === "setup" && <SetupContent setActiveTab={handleTabChange} />}
          {activeTab === "credit" && <CreditContent setActiveTab={handleTabChange} />}
          {activeTab === "upload" && <UploadContent setActiveTab={handleTabChange} />}
          {activeTab === "prompt" && <PromptContent setActiveTab={handleTabChange} />}
          {activeTab === "parse" && <ParseContent setActiveTab={handleTabChange} />}
          {activeTab === "tools" && <ToolsContent setActiveTab={handleTabChange} />}
          {activeTab === "vibe" && <VibeContent />}
          {activeTab === "homework" && <HomeworkContent />}
          {activeTab === "admin" && accessState.accessInfo?.is_admin && <AdminContent />}
        </div>
      </div>
    </AppShell>
  );
}
