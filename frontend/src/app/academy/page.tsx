"use client";

/**
 * 아카데미 가이드 페이지
 * Stitch 7 디자인 - 화이트 토큰 버튼 스타일 (완전 재현)
 */

import { useState, useEffect, Suspense, startTransition } from "react";
import { useSearchParams } from "next/navigation";

import { NAV_SECTIONS, ADMIN_SECTION, type TabKey } from "./constants";
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
} from "./components";
import { api, type AcademyAccessResponse } from "@/lib/api";

export default function AcademyPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <AcademyContent />
    </Suspense>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center">
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-purple-400 animate-pulse" />
    </div>
  );
}

function AcademyContent() {
  const searchParams = useSearchParams();
  const urlTab = searchParams.get("tab") as TabKey | null;
  const [activeTab, setActiveTab] = useState<TabKey>(urlTab || "home");

  // Access control state
  const [accessState, setAccessState] = useState<{
    loading: boolean;
    hasAccess: boolean;
    accessInfo: AcademyAccessResponse | null;
  }>({
    loading: true,
    hasAccess: false,
    accessInfo: null,
  });

  // Check academy access on mount
  useEffect(() => {
    let cancelled = false;

    async function checkAccess() {
      try {
        const response = await api.checkAcademyAccess();
        if (!cancelled) {
          setAccessState({
            loading: false,
            hasAccess: response.can_access,
            accessInfo: response,
          });
        }
      } catch {
        // 403 or other error means no access
        if (!cancelled) {
          setAccessState({
            loading: false,
            hasAccess: false,
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

  const handleTabChange = (tab: TabKey) => {
    startTransition(() => setActiveTab(tab));
  };

  // Show loading while checking access
  if (accessState.loading) {
    return <LoadingScreen />;
  }

  // Show enrollment required if no access
  if (!accessState.hasAccess) {
    return <EnrollmentRequired />;
  }

  return (
    <>
      {/* Global Styles */}
      <style jsx global>{`
        ::-webkit-scrollbar {
          width: 6px;
        }
        ::-webkit-scrollbar-track {
          background: #050505;
        }
        ::-webkit-scrollbar-thumb {
          background: #333;
          border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: #a855f7;
        }
        .glow-text {
          text-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
        }
        .material-symbols-outlined {
          font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        @keyframes slow-ping {
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
      `}</style>

      {/* Fonts */}
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />

      <div className="min-h-screen bg-[#050505] text-white font-sans overflow-hidden h-screen flex antialiased selection:bg-purple-500 selection:text-white">
        {/* Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} cohort={accessState.accessInfo?.cohort} isAdmin={accessState.accessInfo?.is_admin} />

        {/* Main */}
        <main className="flex-1 relative flex flex-col">
          {/* Grid Background */}
          <div
            className="absolute inset-0 pointer-events-none opacity-20"
            style={{
              backgroundSize: '40px 40px',
              backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)',
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#050505]/90 pointer-events-none" />

          {/* Header */}
          <Header />

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-8 relative z-10">
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
        </main>
      </div>
    </>
  );
}

function Sidebar({ activeTab, setActiveTab, cohort, isAdmin }: { activeTab: TabKey; setActiveTab: (tab: TabKey) => void; cohort?: string | null; isAdmin?: boolean }) {
  // Combine NAV_SECTIONS with ADMIN_SECTION if isAdmin
  const sections = isAdmin ? [...NAV_SECTIONS, ADMIN_SECTION] : NAV_SECTIONS;

  return (
    <aside className="w-72 bg-[#080808] border-r border-white/5 flex-col justify-between shrink-0 z-20 relative hidden lg:flex">
      {/* Logo */}
      <div className="p-6 pb-2">
        <div className="flex items-center gap-3">
          <img
            src="/favicon.png"
            alt="초끼"
            className="w-10 h-10 rounded-full object-cover border-2 border-white/20"
          />
          <span className="text-sm font-bold tracking-widest text-white/90 font-mono">
            AI <span className="opacity-50 font-normal">ACADEMY</span>
          </span>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-8">
        {sections.map((section) => (
          <div key={section.title}>
            <h3 className="text-[10px] font-bold tracking-[0.2em] text-gray-500 mb-4 px-2 font-mono uppercase">
              {section.title}
            </h3>
            <ul className="space-y-3">
              {section.items.map((item) => (
                <li key={item.key}>
                  {activeTab === item.key ? (
                    <a className="flex items-center gap-3 p-3 rounded-lg relative overflow-hidden group" href="#">
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-purple-500 rounded-r-full shadow-[0_0_8px_rgba(168,85,247,0.8)]" />
                      <span className="material-symbols-outlined text-purple-500/80 ml-2">{item.icon}</span>
                      <span className="text-sm font-medium text-white/90">{item.label}</span>
                      <div className="absolute inset-0 bg-purple-500/5 pointer-events-none" />
                    </a>
                  ) : (
                    <button
                      onClick={() => setActiveTab(item.key)}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white text-gray-900 hover:bg-gray-100 transition-all shadow-sm"
                    >
                      <span className="material-symbols-outlined text-gray-700">{item.icon}</span>
                      <span className="text-sm font-bold">{item.label}</span>
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* User */}
      <div className="p-4 border-t border-white/5">
        <div className="bg-white rounded-2xl p-3 flex items-center gap-3 shadow-md">
          <div className="w-10 h-10 rounded-full bg-slate-700 text-white flex items-center justify-center font-bold text-sm">
            {isAdmin ? "A" : "U"}
          </div>
          <div>
            <div className="text-sm font-bold text-gray-900">{isAdmin ? "관리자" : "수강생"}</div>
            <div className="text-xs text-gray-500">{cohort || "1기"}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function Header() {
  return (
    <header className="h-20 border-b border-white/5 flex items-center justify-between px-8 relative z-10 bg-[#050505]/50 backdrop-blur-md">
      <div>
        <h1 className="text-lg font-bold text-white">AI 영상 워크플로우</h1>
        <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mt-0.5">Creative Automation Suite v2.0</p>
      </div>
      <div className="w-80 hidden md:block">
        <div className="relative group">
          <input
            className="w-full bg-white/10 border-none rounded-full py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 transition-all"
            placeholder="검색..."
            type="text"
          />
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-purple-500 transition-colors text-[20px]">
            search
          </span>
        </div>
      </div>
    </header>
  );
}
