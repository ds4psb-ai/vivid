"use client";

/**
 * Root Page (/)
 * - 비로그인: EnrollmentRequired (로그인 + 수강신청 안내)
 * - 로그인 + 접근권한: AppShell + 수평탭 Academy
 * - 로그인 + 권한없음: EnrollmentRequired
 */

import { useState, useEffect, Suspense, startTransition, useCallback } from "react";
import { useSearchParams } from "next/navigation";

import { NAV_SECTIONS, ADMIN_SECTION, type TabKey } from "./academy/constants";
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
  const urlTab = searchParams.get("tab") as TabKey | null;
  const [activeTab, setActiveTab] = useState<TabKey>(urlTab || "home");

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
    startTransition(() => setActiveTab(tab));
  }, []);

  // Guard: redirect non-admin users away from admin tab
  useEffect(() => {
    if (!accessState.loading && activeTab === "admin" && !accessState.accessInfo?.is_admin) {
      setActiveTab("home");
    }
  }, [accessState.loading, accessState.accessInfo?.is_admin, activeTab]);

  if (accessState.loading) {
    return <LoadingScreen />;
  }

  // No access → EnrollmentRequired (handles both logged-out and enrolled-but-no-access)
  if (!accessState.hasAccess) {
    return <EnrollmentRequired isLoggedIn={accessState.isLoggedIn} />;
  }

  // Has access → AppShell + Academy tabs
  const allSections = accessState.accessInfo?.is_admin
    ? [...NAV_SECTIONS, ADMIN_SECTION]
    : NAV_SECTIONS;

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
        {/* Academy Header + Tab Navigation */}
        <div className="sticky top-0 z-30 bg-[var(--bg-0)] border-b border-[var(--glass-border)]">
          <div className="px-6 pt-5 pb-3">
            <h1 className="text-lg font-bold text-[var(--fg-0)]">AI Academy</h1>
            <p className="text-[10px] font-mono text-[var(--fg-muted)] uppercase tracking-widest mt-0.5">
              Creative Automation Suite v2.0
              {accessState.accessInfo?.cohort && (
                <span className="ml-3 text-purple-400">{accessState.accessInfo.cohort}</span>
              )}
            </p>
          </div>

          {/* Horizontal Tab Bar */}
          <div className="px-4 overflow-x-auto scrollbar-none">
            <div className="flex gap-1 min-w-max pb-0">
              {allSections.map((section) =>
                section.items.map((item) => {
                  const isActive = activeTab === item.key;
                  return (
                    <button
                      key={item.key}
                      onClick={() => handleTabChange(item.key)}
                      className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg transition-all whitespace-nowrap border-b-2 ${
                        isActive
                          ? "border-purple-500 text-purple-400 bg-purple-500/5"
                          : "border-transparent text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-[var(--surface-1)]"
                      }`}
                    >
                      <span className="material-symbols-outlined text-base">{item.icon}</span>
                      {item.label}
                    </button>
                  );
                })
              )}
            </div>
          </div>
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
