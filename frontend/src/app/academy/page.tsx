"use client";

/**
 * 아카데미 가이드 페이지
 * Stitch 7 디자인 - 화이트 토큰 버튼 스타일
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

const NAV_ITEMS: { key: TabKey; label: string; icon: string; section?: string }[] = [
  { key: "home", label: "홈 대시보드", icon: "dashboard", section: "Dashboard" },
  { key: "setup", label: "환경 설정", icon: "settings" },
  { key: "anchor", label: "기준 프레임", icon: "aspect_ratio" },
  { key: "builder1", label: "이미지 프롬프트 생성기", icon: "construction", section: "Tools" },
  { key: "vibe", label: "바이브 철학관", icon: "psychology" },
  { key: "builder2", label: "패러디 오마주 엔진", icon: "brush" },
  { key: "image", label: "이미지 생성", icon: "image", section: "Creation" },
  { key: "video", label: "영상 생성", icon: "movie" },
  { key: "homework", label: "과제", icon: "assignment_turned_in" },
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
    <div className="min-h-screen bg-[#050505] text-white font-sans overflow-hidden h-screen flex antialiased selection:bg-purple-500 selection:text-white">
      {/* Sidebar */}
      <aside className="w-72 bg-[#080808] border-r border-white/5 flex-col justify-between shrink-0 hidden lg:flex">
        {/* Logo */}
        <div className="p-6 pb-2">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-purple-400 flex items-center justify-center text-white font-bold text-lg shadow-[0_0_15px_rgba(168,85,247,0.4)]">
              A
            </div>
            <span className="text-sm font-bold tracking-widest text-white/90 font-mono">
              AI <span className="opacity-50 font-normal">ACADEMY</span>
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {["Dashboard", "Tools", "Creation"].map((section) => (
            <div key={section}>
              <h3 className="text-[10px] font-bold tracking-[0.2em] text-gray-500 mb-4 px-2 font-mono uppercase">
                {section}
              </h3>
              <ul className="space-y-3">
                {NAV_ITEMS.filter((item) => {
                  if (section === "Dashboard") return item.section === "Dashboard" || (!item.section && ["setup", "anchor"].includes(item.key));
                  if (section === "Tools") return item.section === "Tools" || (!item.section && ["vibe", "builder2"].includes(item.key));
                  if (section === "Creation") return item.section === "Creation" || (!item.section && ["video", "homework"].includes(item.key));
                  return false;
                }).map((item) => (
                  <li key={item.key}>
                    {activeTab === item.key ? (
                      <a className="flex items-center gap-3 p-3 rounded-lg relative overflow-hidden group" href="#">
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-purple-500 rounded-r-full shadow-[0_0_8px_rgba(168,85,247,0.8)]" />
                        <span className="material-symbols-outlined text-purple-400/80 ml-2">{item.icon}</span>
                        <span className="text-sm font-medium text-white/90">{item.label}</span>
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
        </nav>

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
      <main className="flex-1 relative flex flex-col overflow-hidden">
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

      {/* Material Icons */}
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@400,1&display=swap" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet" />
    </div>
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
        <h2
          className="text-5xl md:text-6xl font-black mb-6 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-purple-400"
          style={{ textShadow: '0 0 40px rgba(168, 85, 247, 0.5)' }}
        >
          AI 영상 오마주 & 패러디
        </h2>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed font-light">
          바이럴 영상을 분석하고, AI 엔진을 통해 나만의 유니크한 버전으로<br />
          재창조하는 차세대 크리에이티브 파이프라인.
        </p>
      </div>

      {/* Flow Card */}
      <div className="relative max-w-3xl mx-auto">
        <div className="absolute -inset-1 bg-gradient-to-b from-purple-500/20 to-transparent opacity-30 blur-2xl rounded-[3rem]" />
        <div className="relative bg-[#0f0f11] border border-white/10 rounded-[2.5rem] p-12 min-h-[500px] shadow-2xl flex flex-col items-center">

          {/* Input Source */}
          <FlowStep label="Input Source">
            <WhiteButton icon="movie" label="내 영상 업로드" />
          </FlowStep>

          <FlowLine />

          {/* Analysis Module */}
          <FlowStep label="Analysis Module">
            <WhiteButton icon="search" label="이미지 프롬프트 생성기" href={TOOL_LINKS.builder1} external />
          </FlowStep>

          <FlowLine animated />

          {/* Core Engine + Optional */}
          <div className="flex gap-6 mt-4 w-full justify-center">
            <FlowStep label="Core Engine" className="w-1/2 max-w-[280px]">
              <button className="w-full bg-[#1a1a2e] border border-purple-500/30 text-white px-6 py-5 rounded-2xl flex items-center justify-center gap-3 shadow-[0_0_20px_rgba(168,85,247,0.15)] hover:shadow-[0_0_30px_rgba(168,85,247,0.3)] transition-all duration-300 relative overflow-hidden group">
                <div className="absolute inset-0 bg-purple-500/5 group-hover:bg-purple-500/10 transition-colors" />
                <span className="material-symbols-outlined text-purple-500">theater_comedy</span>
                <a href={TOOL_LINKS.builder2} target="_blank" rel="noopener noreferrer" className="font-bold text-gray-100">패러디 오마주 엔진</a>
                <span className="material-symbols-outlined text-gray-500 text-sm ml-auto">open_in_new</span>
              </button>
            </FlowStep>

            <FlowStep label="Optional" className="w-1/2 max-w-[280px]">
              <WhiteButton icon="psychology" label="바이브 철학관" href={TOOL_LINKS.vibe} external />
            </FlowStep>
          </div>

          <FlowLine />

          {/* Image Gen */}
          <FlowStep label="Generative Process">
            <WhiteButton icon="image" label="이미지 생성" onClick={() => setActiveTab("image")} />
          </FlowStep>

          <FlowLine />

          {/* Video Gen */}
          <FlowStep label="Rendering">
            <WhiteButton icon="movie" label="영상 생성" onClick={() => setActiveTab("video")} />
          </FlowStep>

          <FlowLine />

          {/* Output */}
          <FlowStep label="Output Ready">
            <WhiteButton icon="check" label="나만의 영상 완성!" highlight />
          </FlowStep>
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
      <PageHeader title="환경 설정" sub="Antigravity만 설치하면 됩니다" />
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">Antigravity 설치</h3>
        <p className="text-gray-400 mb-4">프레임 추출, 파일 정리 등을 대신 해주는 AI 코딩 도우미</p>
        <WhiteButton icon="download" label="Antigravity 다운로드" href={TOOL_LINKS.antigravity} external />
        <p className="text-gray-500 text-xs mt-3">설치 후 Google 계정으로 로그인</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">도구 바로가기</h3>
        <div className="space-y-3">
          <WhiteButton icon="search" label="🔍 이미지 프롬프트 생성기" href={TOOL_LINKS.builder1} external />
          <WhiteButton icon="psychology" label="🔮 바이브 철학관" href={TOOL_LINKS.vibe} external />
          <WhiteButton icon="theater_comedy" label="🎭 패러디 오마주 엔진" href={TOOL_LINKS.builder2} external />
        </div>
      </ContentCard>
    </div>
  );
}

// ============ Anchor Content ============
function AnchorContent() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="기준 프레임 추출" sub="Antigravity 채팅으로 간단하게" />
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">Antigravity 채팅 순서</h3>
        <div className="space-y-4">
          <Step num={1} title="ffmpeg 설치 요청">
            <ChatBubble>&quot;ffmpeg 설치해줘&quot;</ChatBubble>
          </Step>
          <Step num={2} title="영상 파일 드래그앤드롭">
            <p className="text-gray-400 text-sm">분석할 영상을 Antigravity 화면에 끌어다 놓기</p>
          </Step>
          <Step num={3} title="이미지 프롬프트 생성기 결과물(.md) 드래그앤드롭">
            <p className="text-gray-400 text-sm">씬 테이블이 담긴 마크다운 파일을 채팅창에 끌어다 놓기</p>
          </Step>
          <Step num={4} title="프레임 추출 요청">
            <ChatBubble>&quot;각 씬 전환 직후 첫 컷 프레임 이미지로 추출해서 frames 폴더에 넣어줘&quot;</ChatBubble>
          </Step>
        </div>
        <p className="text-gray-500 text-sm mt-6 text-center">끝. Antigravity가 알아서 해줍니다.</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">좋은 기준 프레임</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><p className="text-emerald-400 font-medium mb-2">✅ 좋음</p><p className="text-gray-400">얼굴 정면, 조명 균일, 선명</p></div>
          <div><p className="text-red-400 font-medium mb-2">❌ 피하기</p><p className="text-gray-400">뒷모습, 역광, 흔들림</p></div>
        </div>
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
        <WhiteButton icon="search" label="🔍 이미지 프롬프트 생성기 열기" href={TOOL_LINKS.builder1} external large />
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
        <WhiteButton icon="psychology" label="🔮 바이브 철학관 열기" href={TOOL_LINKS.vibe} external large />
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
        <WhiteButton icon="theater_comedy" label="🎭 패러디 오마주 엔진 열기" href={TOOL_LINKS.builder2} external large />
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
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">제출 방법</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 font-medium mb-2">📤 디스코드 #과제제출 채널에 업로드</p>
          <ul className="text-emerald-200/70 text-sm space-y-1">
            <li>1. 이미지 프롬프트 생성기 결과물 (.md)</li>
            <li>2. 바이브 철학관 프로필 (.json)</li>
          </ul>
        </div>
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

function WhiteButton({ icon, label, href, onClick, external, large, highlight }: {
  icon: string; label: string; href?: string; onClick?: () => void; external?: boolean; large?: boolean; highlight?: boolean;
}) {
  const className = `w-full flex items-center justify-center gap-3 ${large ? 'px-10 py-5' : 'px-6 py-4'} rounded-2xl transition-all duration-300 ${
    highlight
      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-[0_10px_30px_-10px_rgba(168,85,247,0.5)] hover:scale-105'
      : 'bg-white text-gray-900 shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105'
  }`;

  const content = (
    <>
      <span className={`material-symbols-outlined ${highlight ? 'text-white' : 'text-gray-700'}`}>{icon}</span>
      <span className={`font-bold ${large ? 'text-lg' : 'text-sm'}`}>{label}</span>
      {external && <span className={`material-symbols-outlined text-sm ml-auto ${highlight ? 'text-white/70' : 'text-gray-400'}`}>open_in_new</span>}
    </>
  );

  if (href) {
    return <a href={href} target="_blank" rel="noopener noreferrer" className={className}>{content}</a>;
  }
  return <button onClick={onClick} className={className}>{content}</button>;
}

function FlowStep({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`relative z-10 ${className || ''}`}>
      <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-mono text-gray-400 tracking-[0.1em] uppercase whitespace-nowrap">
        {label}
      </div>
      {children}
    </div>
  );
}

function FlowLine({ animated }: { animated?: boolean }) {
  return (
    <div className="w-px h-16 bg-gradient-to-b from-white/20 via-purple-500 to-purple-500 my-2 relative">
      {animated && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-white rounded-full shadow-[0_0_10px_white] animate-ping" />
      )}
    </div>
  );
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
