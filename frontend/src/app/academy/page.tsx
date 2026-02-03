"use client";

/**
 * 아카데미 가이드 페이지
 * Stitch 7 디자인 - 화이트 토큰 버튼 스타일 (완전 재현)
 */

import { useState, Suspense, startTransition } from "react";
import { useSearchParams } from "next/navigation";

// Tool Links
const TOOL_LINKS = {
  builder1: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221D3hHLIb6-e4QJQ3tDrOtTb8qZ80cOabz%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  vibe: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221wKUuefdolzOVFp7YAxSfcO13prtAWvgu%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  builder2: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221W-ooRbimFIPbrOfAptWKcThofLDe9GF0%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  antigravity: "https://antigravity.google",
};

type TabKey = "home" | "setup" | "anchor" | "builder1" | "vibe" | "builder2" | "image" | "video" | "homework";

const NAV_SECTIONS = [
  {
    title: "Dashboard",
    items: [
      { key: "home" as TabKey, label: "홈 대시보드", icon: "dashboard" },
      { key: "setup" as TabKey, label: "환경 설정", icon: "settings" },
      { key: "anchor" as TabKey, label: "기준 프레임", icon: "aspect_ratio" },
    ],
  },
  {
    title: "Tools",
    items: [
      { key: "builder1" as TabKey, label: "이미지 프롬프트 생성기", icon: "construction" },
      { key: "vibe" as TabKey, label: "바이브 철학관", icon: "psychology" },
      { key: "builder2" as TabKey, label: "패러디 오마주 엔진", icon: "brush" },
    ],
  },
  {
    title: "Creation",
    items: [
      { key: "image" as TabKey, label: "이미지 생성", icon: "image" },
      { key: "video" as TabKey, label: "영상 생성", icon: "movie" },
      { key: "homework" as TabKey, label: "과제", icon: "assignment_turned_in" },
    ],
  },
];

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
            {NAV_SECTIONS.map((section) => (
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
                          onClick={() => startTransition(() => setActiveTab(item.key))}
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
                U
              </div>
              <div>
                <div className="text-sm font-bold text-gray-900">수강생</div>
                <div className="text-xs text-gray-500">1기</div>
              </div>
            </div>
          </div>
        </aside>

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

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-8 relative z-10">
            {activeTab === "home" && <HomeContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "setup" && <SetupContent />}
            {activeTab === "anchor" && <AnchorContent />}
            {activeTab === "builder1" && <Builder1Content />}
            {activeTab === "vibe" && <VibeContent />}
            {activeTab === "builder2" && <Builder2Content />}
            {activeTab === "image" && <ImageContent />}
            {activeTab === "video" && <VideoContent />}
            {activeTab === "homework" && <HomeworkContent />}
          </div>
        </main>
      </div>
    </>
  );
}

// ============ Home Content ============
function HomeContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center mt-8 mb-16">
        <div className="inline-block px-4 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-6">
          <span className="text-[10px] font-bold text-indigo-400 tracking-[0.2em] font-mono uppercase">Workflow Visualization</span>
        </div>
        <h2 className="text-5xl md:text-6xl font-black mb-6 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-purple-400 glow-text">
          AI 영상 오마주 & 패러디
        </h2>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed font-light">
          바이럴 영상을 분석하고, AI 엔진을 통해 나만의 유니크한 버전으로<br />
          재창조하는 차세대 크리에이티브 파이프라인.
        </p>
      </div>

      {/* Flow Card */}
      <div className="max-w-3xl mx-auto relative">
        <div className="absolute -inset-1 bg-gradient-to-b from-purple-500/20 to-transparent opacity-30 blur-2xl rounded-[3rem]" />
        <div className="relative bg-[#0f0f11] border border-white/10 rounded-[2.5rem] p-12 min-h-[500px] shadow-2xl flex flex-col items-center">

          {/* Input Source */}
          <div className="relative z-10 group">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-400 tracking-[0.1em] uppercase">Input Source</div>
            <button className="bg-white text-gray-900 px-10 py-5 rounded-2xl flex items-center gap-3 shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105 transition-transform duration-300">
              <span className="material-symbols-outlined">movie</span>
              <span className="font-bold text-lg">아웃라이어 영상 업로드</span>
            </button>
          </div>

          {/* Line 1 */}
          <div className="w-px h-16 bg-gradient-to-b from-white/20 via-purple-500 to-purple-500 my-2" />

          {/* Analysis Module */}
          <div className="relative z-10 group">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-400 tracking-[0.1em] uppercase">Analysis Module</div>
            <a
              href={TOOL_LINKS.builder1}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white text-gray-900 px-8 py-5 rounded-2xl flex items-center gap-4 shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105 transition-transform duration-300"
            >
              <span className="material-symbols-outlined">search</span>
              <span className="font-bold text-lg">이미지 프롬프트 생성기</span>
              <span className="material-symbols-outlined text-gray-400 text-sm">open_in_new</span>
            </a>
          </div>

          {/* Line 2 with animation */}
          <div className="w-px h-16 bg-gradient-to-b from-purple-500 via-purple-500 to-purple-500/20 my-2 relative">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-white rounded-full shadow-[0_0_10px_white] animate-[slow-ping_2s_cubic-bezier(0,0,0.2,1)_infinite]" />
          </div>

          {/* Core Engine + Optional */}
          <div className="flex gap-6 mt-4 w-full justify-center">
            {/* Core Engine */}
            <div className="relative group w-1/2 max-w-[280px]">
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-500 tracking-[0.1em] uppercase">Core Engine</div>
              <a
                href={TOOL_LINKS.builder2}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-[#1a1a2e] border border-purple-500/30 text-white px-6 py-5 rounded-2xl flex items-center justify-center gap-3 shadow-[0_0_20px_rgba(168,85,247,0.15)] group-hover:shadow-[0_0_30px_rgba(168,85,247,0.3)] transition-all duration-300 relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-purple-500/5 group-hover:bg-purple-500/10 transition-colors" />
                <span className="material-symbols-outlined text-purple-500">theater_comedy</span>
                <span className="font-bold text-gray-100">패러디 오마주 엔진</span>
                <span className="material-symbols-outlined text-gray-500 text-sm ml-auto">open_in_new</span>
              </a>
            </div>

            {/* Optional */}
            <div className="relative group w-1/2 max-w-[280px]">
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-400 tracking-[0.1em] uppercase">Optional</div>
              <a
                href={TOOL_LINKS.vibe}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-white text-gray-900 px-6 py-5 rounded-2xl flex items-center justify-center gap-3 shadow-[0_10px_30px_-10px_rgba(255,255,255,0.2)] hover:scale-[1.02] transition-transform duration-300"
              >
                <span className="material-symbols-outlined text-gray-800">psychology</span>
                <span className="font-bold">바이브 철학관</span>
                <span className="material-symbols-outlined text-gray-400 text-sm ml-auto">open_in_new</span>
              </a>
            </div>
          </div>

          {/* Line 3 */}
          <div className="w-px h-16 bg-gradient-to-b from-purple-500/20 via-purple-500/50 to-purple-500 my-2 mt-8" />

          {/* Image Gen */}
          <div className="relative z-10 group">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-400 tracking-[0.1em] uppercase">Generative Process</div>
            <button
              onClick={() => setActiveTab("image")}
              className="bg-white text-gray-900 px-8 py-5 rounded-2xl flex items-center gap-3 shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105 transition-transform duration-300"
            >
              <span className="material-symbols-outlined">image</span>
              <span className="font-bold text-lg">이미지 생성</span>
            </button>
          </div>

          {/* Line 4 */}
          <div className="w-px h-16 bg-gradient-to-b from-purple-500 via-purple-500/50 to-purple-500/20 my-2" />

          {/* Video Gen */}
          <div className="relative z-10 group">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-400 tracking-[0.1em] uppercase">Rendering</div>
            <button
              onClick={() => setActiveTab("video")}
              className="bg-white text-gray-900 px-8 py-5 rounded-2xl flex items-center gap-3 shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105 transition-transform duration-300"
            >
              <span className="material-symbols-outlined">movie</span>
              <span className="font-bold text-lg">영상 생성</span>
            </button>
          </div>

          {/* Line 5 */}
          <div className="w-px h-16 bg-gradient-to-b from-purple-500/20 via-emerald-500/50 to-emerald-500 my-2" />

          {/* Output */}
          <div className="relative z-10 group">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-emerald-400 tracking-[0.1em] uppercase">Output Ready</div>
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-10 py-5 rounded-2xl flex items-center gap-3 shadow-[0_10px_30px_-10px_rgba(16,185,129,0.5)]">
              <span className="material-symbols-outlined">check_circle</span>
              <span className="font-bold text-lg">나만의 영상 완성!</span>
            </div>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="mt-20 text-center opacity-30">
        <div className="h-px w-32 bg-gradient-to-r from-transparent via-gray-500 to-transparent mx-auto" />
      </div>
    </div>
  );
}

// ============ Setup Content ============
function SetupContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="환경 설정" sub="Gemini Pro 구독 + Antigravity 설치" />
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-white mb-4">⚡ Google AI Pro 구독 필수</h3>
        <p className="text-gray-400 mb-4">모든 핵심 도구 사용을 위해 필요합니다 (18세 이상)</p>
        <div className="p-4 rounded-xl bg-white text-gray-900">
          <p className="font-bold text-purple-600 mb-1">Google AI Pro</p>
          <div className="flex items-baseline gap-2 mb-2">
            <p className="text-2xl font-black text-gray-900">₩14,500/월</p>
            <p className="text-sm text-gray-400 line-through">₩29,000</p>
            <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded-full">2개월 프로모션</span>
          </div>
          <ul className="text-gray-600 text-sm space-y-1">
            <li>✓ <strong>Antigravity</strong> - AI 코딩 도우미</li>
            <li>✓ <strong>NanoBanana Pro</strong> - 한글 이미지 생성</li>
            <li>✓ <strong>Veo 3.1 + Flow</strong> - AI 영상 생성</li>
            <li>✓ AI 크레딧 1,000/월 (Flow, Whisk 사용)</li>
            <li>✓ 2TB 클라우드 스토리지</li>
          </ul>
          <a
            href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-bold hover:bg-purple-700 transition-colors"
          >
            구독하기
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">Antigravity 설치</h3>
        <p className="text-gray-400 mb-4">프레임 추출, 파일 정리 등을 대신 해주는 AI 코딩 도우미</p>
        <WhiteButton href={TOOL_LINKS.antigravity}>Antigravity 다운로드</WhiteButton>
        <p className="text-gray-500 text-xs mt-3">설치 후 Google 계정으로 로그인 (Pro 구독 필요)</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">도구 바로가기</h3>
        <div className="space-y-3">
          <WhiteButton href={TOOL_LINKS.builder1}>🔍 이미지 프롬프트 생성기</WhiteButton>
          <WhiteButton href={TOOL_LINKS.vibe}>🔮 바이브 철학관</WhiteButton>
          <WhiteButton href={TOOL_LINKS.builder2}>🎭 패러디 오마주 엔진</WhiteButton>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Anchor Content ============
function AnchorContent() {
  const PROMPT_1 = `ffmpeg 설치해줘`;
  const PROMPT_2 = `영상 프로젝트 폴더에 넣고, 첫 프레임 + 씬 전환 프레임 추출해줘 (threshold 0.18). 타임스탬프는 0.01초로 올림해서 복붙 가능하게 따로 알려줘.`;

  const [copied1, setCopied1] = useState(false);
  const [copied2, setCopied2] = useState(false);

  const handleCopy = async (text: string, setCopied: (v: boolean) => void) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="기준 프레임 추출" sub="Antigravity 복붙 2번이면 끝" />

      {/* 섹션 1: ffmpeg 설치 */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-3">
          <span className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 text-sm font-bold flex items-center justify-center">1</span>
          <p className="text-white font-bold">ffmpeg 설치 (최초 1회)</p>
        </div>
        <div className="relative">
          <div className="p-3 rounded-xl bg-black/50 border border-white/10">
            <p className="text-purple-200 text-sm pr-16">{PROMPT_1}</p>
          </div>
          <button
            onClick={() => handleCopy(PROMPT_1, setCopied1)}
            className={`absolute top-2 right-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              copied1 ? 'bg-emerald-500 text-white' : 'bg-white text-gray-900 hover:bg-gray-100'
            }`}
          >
            {copied1 ? '복사됨!' : '복사'}
          </button>
        </div>
      </ContentCard>

      {/* 섹션 2: 영상 드래그 + 프레임 추출 */}
      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-3">
          <span className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 text-sm font-bold flex items-center justify-center">2</span>
          <p className="text-white font-bold">영상 드래그앤드롭 + 복붙</p>
        </div>
        <p className="text-gray-400 text-sm mb-3">영상 파일을 Antigravity 채팅창에 끌어다 놓고 아래 복붙</p>
        <div className="relative">
          <div className="p-3 rounded-xl bg-black/50 border border-purple-500/30">
            <p className="text-purple-200 text-sm pr-16">{PROMPT_2}</p>
          </div>
          <button
            onClick={() => handleCopy(PROMPT_2, setCopied2)}
            className={`absolute top-2 right-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              copied2 ? 'bg-emerald-500 text-white' : 'bg-white text-gray-900 hover:bg-gray-100'
            }`}
          >
            {copied2 ? '복사됨!' : '복사'}
          </button>
        </div>
        <p className="text-emerald-400 text-sm mt-4 text-center font-medium">
          끝! 씬 전환 자동 감지 → 프레임 추출 → 경로 안내까지
        </p>
      </ContentCard>
    </div>
  );
}

// ============ Builder1 Content ============
function Builder1Content() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="이미지 프롬프트 생성기" sub="영상 넣으면 → 이미지용 프롬프트 나옴" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.builder1} large>🔍 이미지 프롬프트 생성기 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">사용법</h3>
        <div className="space-y-3 text-sm">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">1.</span><span className="text-gray-300">영상 파일 업로드</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">2.</span><span className="text-gray-300">STEP 1~4 순서대로 진행</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">3.</span><span className="text-gray-300">결과물(.md) 다운로드</span></div>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Vibe Content ============
function VibeContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="바이브 철학관" sub="AI와 대화하며 나의 프로필을 만들어요" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.vibe} large>🔮 바이브 철학관 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">사용법</h3>
        <div className="space-y-3 text-sm">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">1.</span><span className="text-gray-300">기본 정보 입력 (이름, 생년월일)</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">2.</span><span className="text-gray-300">AI와 자연스럽게 대화</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">3.</span><span className="text-gray-300">50% 이상 도달 시 프로필 저장</span></div>
        </div>
        <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 text-sm">💡 저장한 프로필은 패러디 엔진에서 사용 → 나의 감성이 담긴 변주 생성</p>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Builder2 Content ============
function Builder2Content() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="패러디 오마주 엔진" sub="분석 결과 + 나의 프로필 → 오마주/변주 생성" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.builder2} large>🎭 패러디 오마주 엔진 열기</WhiteButton>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">사용법</h3>
        <div className="space-y-3 text-sm">
          <div className="flex gap-3"><span className="text-pink-400 font-bold">1.</span><span className="text-gray-300">원본 영상 + 이미지 프롬프트 생성기 결과물(.md) 업로드</span></div>
          <div className="flex gap-3"><span className="text-pink-400 font-bold">2.</span><span className="text-gray-300">(선택) 바이브 철학관 프로필(.json) 업로드</span></div>
          <div className="flex gap-3"><span className="text-pink-400 font-bold">3.</span><span className="text-gray-300">STEP 1~4 순서대로 진행</span></div>
          <div className="flex gap-3"><span className="text-pink-400 font-bold">4.</span><span className="text-gray-300">결과물 다운로드</span></div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">오마주 vs 변주</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><p className="text-blue-400 font-medium mb-1">🎬 오마주</p><p className="text-gray-400">원본 구도 유지, 캐릭터만 교체</p></div>
          <div><p className="text-pink-400 font-medium mb-1">🎭 변주</p><p className="text-gray-400">구도 유지, 상황/맥락 변형</p></div>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Image Content ============
function ImageContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="이미지 생성" sub="프롬프트 → 이미지" />
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-white mb-4">⚡ Google AI Pro 구독 필수</h3>
        <p className="text-gray-400 mb-4">NanoBanana Pro 사용을 위해 필요합니다 (18세 이상)</p>
        <div className="p-4 rounded-xl bg-white text-gray-900">
          <p className="font-bold text-purple-600 mb-1">Google AI Pro</p>
          <div className="flex items-baseline gap-2 mb-2">
            <p className="text-2xl font-black text-gray-900">₩14,500/월</p>
            <p className="text-sm text-gray-400 line-through">₩29,000</p>
            <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded-full">2개월</span>
          </div>
          <ul className="text-gray-600 text-sm space-y-1">
            <li>• Gemini 챗에서 NanoBanana Pro 이미지 생성</li>
            <li>• AI 크레딧 1,000/월</li>
            <li>• 2TB 클라우드 스토리지</li>
          </ul>
          <a
            href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-bold hover:bg-purple-700 transition-colors"
          >
            구독하기
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">도구 비교</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="text-orange-500 font-bold mb-2">NanoBanana Pro</p>
            <p className="text-gray-600 text-sm">🇰🇷 한글 지원, 4K, 3~8초</p>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="text-violet-500 font-bold mb-2">Midjourney V7</p>
            <p className="text-gray-600 text-sm">🎨 영문, 예술적 스타일</p>
          </div>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Video Content ============
function VideoContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="영상 생성" sub="이미지 + 프롬프트 → 영상" />
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-white mb-4">⚡ 구독 안내 (18세 이상)</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold text-purple-600 mb-1">Google AI Pro (필수)</p>
            <div className="flex items-baseline gap-2 mb-2">
              <p className="text-2xl font-black text-gray-900">₩14,500/월</p>
              <p className="text-sm text-gray-400 line-through">₩29,000</p>
            </div>
            <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded-full mb-2 inline-block">2개월 프로모션</span>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>✓ Veo 3.1 + Flow 영상 생성</li>
              <li>✓ Whisk 이미지→영상</li>
              <li>✓ AI 크레딧 1,000/월</li>
            </ul>
            <a
              href="https://one.google.com/ai?utm_source=gemini&utm_medium=web&utm_campaign=geminiplanspage&sc=EgIIAQ&hl=ko&icid=geminiplanspage&g1_landing_page=75"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-bold hover:bg-purple-700 transition-colors"
            >
              구독하기
              <span className="material-symbols-outlined text-sm">open_in_new</span>
            </a>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold text-cyan-600 mb-1">Kling 3.0 (추천)</p>
            <p className="text-2xl font-black text-gray-900 mb-2">₩31,200~/월</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>✓ 4K 고화질 시네마틱</li>
              <li>✓ Pro 3,000cr (2.6기준 5초 60개)</li>
              <li>✓ Premier ₩78,000 (8,000cr)</li>
              <li>✓ 상업용 라이선스 포함</li>
            </ul>
            <a
              href="https://app.klingai.com/global/membership/membership-plan"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 text-white text-sm font-bold hover:bg-cyan-700 transition-colors"
            >
              구독하기
              <span className="material-symbols-outlined text-sm">open_in_new</span>
            </a>
          </div>
        </div>
        <p className="text-gray-500 text-xs mt-4">※ 환율 변동에 따라 가격이 달라질 수 있습니다 (USD 1,200원 기준)</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">Kling 추천 플랜</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-white/10">
                <th className="text-left py-2">플랜</th>
                <th className="text-right py-2">월간</th>
                <th className="text-right py-2">크레딧</th>
                <th className="text-right py-2">5초 영상 (2.6)</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-white/5 bg-cyan-500/10">
                <td className="py-2 font-bold text-cyan-400">Pro (추천)</td>
                <td className="text-right">₩31,200</td>
                <td className="text-right">3,000</td>
                <td className="text-right">~60개</td>
              </tr>
              <tr className="bg-cyan-500/5">
                <td className="py-2 font-bold text-cyan-300">Premier</td>
                <td className="text-right">₩78,000</td>
                <td className="text-right">8,000</td>
                <td className="text-right">~160개</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-gray-500 text-xs mt-3">※ Kling 2.6: 5초=50cr | 3.0 크레딧 미정 | $25.99 / $64.99 (환율 1,200원)</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">언제 뭘 쓰나요?</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <span className="text-red-400 font-bold shrink-0">Veo 3.1</span>
            <span className="text-gray-400">→ 대사/효과음이 필요한 영상 (Flow 활용)</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-cyan-400 font-bold shrink-0">Kling 3.0</span>
            <span className="text-gray-400">→ 고화질 시네마/애니, 대사 없는 모션, Canvas Agent 스토리보드</span>
          </div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">도구 비교</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="text-red-500 font-bold mb-2">Veo 3.1</p>
            <p className="text-gray-600 text-sm">🎬 오디오 자동 생성, Google</p>
            <p className="text-gray-400 text-xs mt-2">Gemini → Flow 메뉴</p>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="text-cyan-500 font-bold mb-2">Kling AI</p>
            <p className="text-gray-600 text-sm">👥 캐릭터 일관성 최고</p>
            <p className="text-gray-400 text-xs mt-2">klingai.com</p>
          </div>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Homework Content ============
function HomeworkContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="과제 안내" sub="📅 2강 예정: 2026년 2월 6일 (목)" />
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">필수 과제</h3>
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold mb-2">1. 이미지 프롬프트 생성기 완료</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>• 본인이 선정한 바이럴 영상 분석</li>
              <li>• 결과물(.md) 저장</li>
            </ul>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold mb-2">2. 바이브 철학관 세션</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>• 최소 50% 깊이 도달</li>
              <li>• 프로필(.json) 다운로드</li>
            </ul>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold mb-2">3. Google 계정 준비</p>
            <ul className="text-gray-600 text-sm space-y-1">
              <li>• 최소 <span className="font-bold text-purple-600">3개</span> 계정 생성</li>
              <li>• 하나의 핸드폰 번호로 5개까지 가능</li>
            </ul>
          </div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">제출 방법</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 font-medium mb-2">📤 디스코드 #과제제출 채널에 업로드</p>
          <ul className="text-emerald-200/70 text-sm space-y-1">
            <li>• 이미지 프롬프트 생성기 결과물 (.md)</li>
          </ul>
        </div>
        <p className="text-gray-500 text-xs mt-3">※ 바이브 철학관 프로필은 개인정보이므로 제출하지 않습니다</p>
      </ContentCard>
    </div>
  );
}

// ============ UI Components ============
function PageHeader({ title, sub }: { title: string; sub: string }) {
  return (
    <div className="mb-8">
      <h2 className="text-3xl font-bold text-white mb-2">{title}</h2>
      <p className="text-gray-400">{sub}</p>
    </div>
  );
}

function ContentCard({ children, highlight }: { children: React.ReactNode; highlight?: boolean }) {
  return (
    <div className={`p-6 rounded-2xl border ${highlight ? 'border-purple-500/30 bg-purple-500/5' : 'border-white/10 bg-white/5'}`}>
      {children}
    </div>
  );
}

function WhiteButton({ href, onClick, children, large }: {
  href?: string; onClick?: () => void; children: React.ReactNode; large?: boolean;
}) {
  const className = `w-full flex items-center justify-center gap-3 ${large ? 'px-10 py-5 text-lg' : 'px-6 py-4 text-sm'} rounded-2xl bg-white text-gray-900 font-bold shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105 transition-transform duration-300`;

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {children}
        <span className="material-symbols-outlined text-gray-400 text-sm ml-auto">open_in_new</span>
      </a>
    );
  }
  return <button onClick={onClick} className={className}>{children}</button>;
}

function Step({ num, title, children }: { num: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-4">
      <span className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 text-sm font-bold flex items-center justify-center shrink-0">{num}</span>
      <div>
        <p className="text-white font-medium mb-2">{title}</p>
        {children}
      </div>
    </div>
  );
}

function ChatBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-3 rounded-lg bg-black/30 border border-white/10">
      <p className="text-purple-300 text-sm">{children}</p>
    </div>
  );
}
