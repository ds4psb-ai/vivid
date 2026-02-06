"use client";

/**
 * Root Page (/)
 * - 비로그인: EnrollmentRequired
 * - 로그인 + 접근권한: AppShell + Academy
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

const TAB_TITLES: Record<TabKey, string> = {
  home: "홈",
  setup: "시작",
  credit: "크레딧",
  upload: "업로드",
  prompt: "빌더",
  parse: "파싱",
  tools: "툴",
  vibe: "바이브",
  homework: "과제",
  admin: "관리",
};

export default function RootPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <RootContent />
    </Suspense>
  );
}

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-0)]">
      <div className="h-8 w-8 rounded-full bg-[var(--color-brand-primary)] animate-pulse" />
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
    return () => {
      cancelled = true;
    };
  }, []);

  const handleTabChange = useCallback(
    (tab: TabKey) => {
      router.push(tab === "home" ? "/" : `/?tab=${tab}`, { scroll: false });
    },
    [router]
  );

  useEffect(() => {
    if (
      !accessState.loading &&
      activeTab === "admin" &&
      !accessState.accessInfo?.is_admin
    ) {
      router.push("/", { scroll: false });
    }
  }, [accessState.loading, accessState.accessInfo?.is_admin, activeTab, router]);

  if (accessState.loading) {
    return <LoadingScreen />;
  }

  if (!accessState.hasAccess) {
    return <EnrollmentRequired isLoggedIn={accessState.isLoggedIn} />;
  }

  return (
    <AppShell
      showChokki={false}
      navVariant="academy"
      academyCurrentTab={activeTab}
      onAcademyTabChange={handleTabChange}
    >
      <div className="min-h-screen">
        <div className="mx-auto w-full max-w-[1200px] px-4 pb-6 pt-5 md:px-6">
          <div className="mb-5 flex items-center justify-between gap-3">
            <h1 className="font-korean text-xl font-semibold text-[var(--fg-0)] md:text-2xl">
              {TAB_TITLES[activeTab]}
            </h1>
            {accessState.accessInfo?.cohort && (
              <span className="rounded-full border border-[var(--border-muted)] px-2.5 py-1 text-[11px] text-[var(--fg-muted)]">
                {accessState.accessInfo.cohort}
              </span>
            )}
          </div>

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
