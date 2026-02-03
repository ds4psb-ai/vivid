"use client";

/**
 * 아카데미 가이드 페이지
 * Stitch 5 + 6 디자인 조합
 */

import { useState, Suspense, startTransition, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

// Tool Links
const TOOL_LINKS = {
  builder1: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221D3hHLIb6-e4QJQ3tDrOtTb8qZ80cOabz%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  vibe: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221wKUuefdolzOVFp7YAxSfcO13prtAWvgu%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  builder2: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221W-ooRbimFIPbrOfAptWKcThofLDe9GF0%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  antigravity: "https://antigravity.google",
};

type TabKey = "home" | "setup" | "anchor" | "builder1" | "vibe" | "builder2" | "image" | "video" | "homework";

const NAV_ITEMS: { key: TabKey; label: string; icon: string; section?: string }[] = [
  { key: "home", label: "홈 대시보드", icon: "grid_view", section: "Dashboard" },
  { key: "setup", label: "환경 설정", icon: "settings" },
  { key: "anchor", label: "기준 프레임", icon: "aspect_ratio" },
  { key: "builder1", label: "이미지 프롬프트 생성기", icon: "construction", section: "Tools" },
  { key: "vibe", label: "바이브 철학관", icon: "psychology" },
  { key: "builder2", label: "패러디 오마주 엔진", icon: "brush" },
  { key: "image", label: "이미지 생성", icon: "image", section: "Creation" },
  { key: "video", label: "영상 생성", icon: "movie_filter" },
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
    <div className="min-h-screen bg-[#05050A] flex items-center justify-center">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 animate-pulse" />
    </div>
  );
}

function AcademyContent() {
  const searchParams = useSearchParams();
  const urlTab = searchParams.get("tab") as TabKey | null;
  const [activeTab, setActiveTab] = useState<TabKey>(urlTab || "home");

  return (
    <div className="min-h-screen bg-[#05050A] text-gray-300 overflow-hidden selection:bg-purple-500 selection:text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0" style={{
          background: `
            radial-gradient(circle at 15% 50%, rgba(76, 29, 149, 0.15), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(219, 39, 119, 0.15), transparent 25%)
          `
        }} />
        <div className="absolute inset-0" style={{
          backgroundSize: '40px 40px',
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
          `,
          maskImage: 'radial-gradient(circle at center, black 40%, transparent 100%)'
        }} />
      </div>

      <div className="flex h-screen relative z-10">
        {/* Sidebar */}
        <aside className="w-72 hidden lg:flex flex-col border-r border-white/5" style={{
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(16px)',
        }}>
          {/* Logo */}
          <div className="p-8 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.5)]">
                <span className="font-bold text-white text-lg">V</span>
              </div>
              <span className="text-xl font-bold tracking-tight text-white">
                VIVID <span className="text-xs font-normal text-white/50 tracking-widest ml-1">ACADEMY</span>
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {NAV_ITEMS.map((item, idx) => (
              <div key={item.key}>
                {item.section && (
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest px-4 mb-4 mt-6">
                    {item.section}
                  </div>
                )}
                <button
                  onClick={() => startTransition(() => setActiveTab(item.key))}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-r-xl text-sm font-medium transition-all duration-200 ${
                    activeTab === item.key
                      ? "bg-gradient-to-r from-purple-500/15 to-transparent border-l-[3px] border-purple-500 text-white"
                      : "text-gray-400 hover:text-white hover:bg-white/5 border-l-[3px] border-transparent"
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  {item.label}
                </button>
              </div>
            ))}
          </nav>

          {/* User */}
          <div className="p-6 border-t border-white/5">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-gray-700 to-gray-600 border border-white/10 flex items-center justify-center">
                <span className="text-xs font-bold text-white">U</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-white">수강생</span>
                <span className="text-xs text-gray-500">1기</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
          {/* Header */}
          <header className="h-20 flex items-center justify-between px-8 lg:px-12 z-10 border-b border-white/5">
            <div className="hidden lg:block">
              <h1 className="text-2xl font-bold text-white tracking-wide">AI 영상 워크플로우</h1>
              <p className="text-xs text-gray-400 mt-1 font-light tracking-wider">CREATIVE AUTOMATION SUITE V2.0</p>
            </div>
            <div className="lg:hidden flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center">
                <span className="font-bold text-white">V</span>
              </div>
              <span className="text-lg font-bold text-white">VIVID</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="h-10 px-4 rounded-full flex items-center gap-2 text-gray-400 border border-white/10 bg-white/5">
                <span className="material-symbols-outlined text-[18px]">search</span>
                <input
                  className="bg-transparent border-none text-sm focus:ring-0 focus:outline-none text-white w-24 placeholder-gray-600"
                  placeholder="검색..."
                  type="text"
                />
              </div>
            </div>
          </header>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-8 lg:p-12">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === "home" && <HomeContent setActiveTab={setActiveTab} />}
              {activeTab === "setup" && <SetupContent />}
              {activeTab === "anchor" && <AnchorContent />}
              {activeTab === "builder1" && <Builder1Content />}
              {activeTab === "vibe" && <VibeContent />}
              {activeTab === "builder2" && <Builder2Content />}
              {activeTab === "image" && <ImageContent />}
              {activeTab === "video" && <VideoContent />}
              {activeTab === "homework" && <HomeworkContent />}
            </motion.div>
          </div>
        </main>
      </div>

      {/* Material Icons */}
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
    </div>
  );
}

// ============ Home Content ============
function HomeContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  return (
    <div className="w-full max-w-7xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-16 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-500/20 rounded-full blur-[100px] pointer-events-none" />
        <span className="inline-block py-1 px-3 rounded-full bg-white/5 border border-white/10 text-[10px] font-bold tracking-widest text-indigo-300 uppercase mb-4">
          Workflow Visualization
        </span>
        <h2 className="text-5xl lg:text-6xl font-black mb-4 text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200 tracking-tight" style={{ textShadow: '0 0 40px rgba(139, 92, 246, 0.5)' }}>
          AI 영상 오마주 & 패러디
        </h2>
        <p className="text-gray-400 text-lg font-light max-w-2xl mx-auto leading-relaxed">
          바이럴 영상을 분석하고, AI 엔진을 통해 나만의 유니크한 버전으로<br />재창조하는 차세대 크리에이티브 파이프라인.
        </p>
      </div>

      {/* Vertical Flow Diagram */}
      <div className="w-full max-w-2xl mx-auto mb-16 p-8 rounded-2xl border border-white/10" style={{
        background: 'linear-gradient(160deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%)',
        backdropFilter: 'blur(20px)',
      }}>
        <div className="relative flex flex-col items-center">
          {/* Vertical Line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-[2px] bg-gradient-to-b from-indigo-500/50 via-purple-500/50 to-pink-500/50 -translate-x-1/2 z-0" />

          {/* Nodes */}
          <FlowNode icon="movie" label="내 영상 업로드" sub="Input Source" />
          <FlowConnector />
          <FlowNode icon="search" label="이미지 프롬프트 생성기" sub="Analysis Module" href={TOOL_LINKS.builder1} />
          <FlowConnector />

          {/* Split Section */}
          <div className="flex w-full justify-center gap-8 my-4 relative z-10">
            <FlowNode icon="theater_comedy" label="패러디 오마주 엔진" sub="Core Engine" href={TOOL_LINKS.builder2} highlight />
            <FlowNode icon="psychology" label="바이브 철학관" sub="Optional" href={TOOL_LINKS.vibe} dashed />
          </div>

          <FlowConnector />
          <FlowNode icon="image" label="이미지 생성" sub="Generative Process" onClick={() => startTransition(() => setActiveTab("image"))} />
          <FlowConnector />
          <FlowNode icon="movie_filter" label="영상 생성" sub="Rendering" onClick={() => startTransition(() => setActiveTab("video"))} />
          <FlowConnector />
          <FlowNode icon="check" label="나만의 영상 완성!" sub="Output Ready" final />
        </div>
      </div>

      {/* Quick Links */}
      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <span className="w-1 h-6 bg-pink-500 rounded-full" />
        바로가기
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <BentoCard icon="settings" label="환경 설정" sub="Antigravity 설치" color="indigo" onClick={() => startTransition(() => setActiveTab("setup"))} />
        <BentoCard icon="construction" label="이미지 프롬프트 생성기" sub="영상 분석" color="purple" href={TOOL_LINKS.builder1} />
        <BentoCard icon="brush" label="패러디 오마주 엔진" sub="변주 생성" color="pink" href={TOOL_LINKS.builder2} />
        <BentoCard icon="assignment_turned_in" label="과제 확인" sub="제출 안내" color="blue" onClick={() => startTransition(() => setActiveTab("homework"))} highlight />
      </div>

      <footer className="mt-20 text-center text-xs text-gray-600 font-light tracking-wider">
        © 2026 VIVID · AI VIDEO AUTOMATION ACADEMY
      </footer>
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
        <LinkButton href={TOOL_LINKS.antigravity}>Antigravity 다운로드</LinkButton>
        <p className="text-gray-500 text-xs mt-3">설치 후 Google 계정으로 로그인</p>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">도구 바로가기</h3>
        <div className="space-y-3">
          <LinkButton href={TOOL_LINKS.builder1}>🔍 이미지 프롬프트 생성기</LinkButton>
          <LinkButton href={TOOL_LINKS.vibe}>🔮 바이브 철학관</LinkButton>
          <LinkButton href={TOOL_LINKS.builder2}>🎭 패러디 오마주 엔진</LinkButton>
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
          <div>
            <p className="text-emerald-400 font-medium mb-2">✅ 좋음</p>
            <p className="text-gray-400">얼굴 정면, 조명 균일, 선명</p>
          </div>
          <div>
            <p className="text-red-400 font-medium mb-2">❌ 피하기</p>
            <p className="text-gray-400">뒷모습, 역광, 흔들림</p>
          </div>
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
        <LinkButton href={TOOL_LINKS.builder1} large>🔍 이미지 프롬프트 생성기 열기</LinkButton>
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
        <LinkButton href={TOOL_LINKS.vibe} large>🔮 바이브 철학관 열기</LinkButton>
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
        <LinkButton href={TOOL_LINKS.builder2} large>🎭 패러디 오마주 엔진 열기</LinkButton>
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
          <div>
            <p className="text-blue-400 font-medium mb-1">🎬 오마주</p>
            <p className="text-gray-400">원본 구도 유지, 캐릭터만 교체</p>
          </div>
          <div>
            <p className="text-pink-400 font-medium mb-1">🎭 변주</p>
            <p className="text-gray-400">구도 유지, 상황/맥락 변형</p>
          </div>
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
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-orange-400 font-bold mb-2">NanoBanana Pro</p>
            <p className="text-gray-400 text-sm">🇰🇷 한글 지원, 4K, 3~8초</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-violet-400 font-bold mb-2">Midjourney V7</p>
            <p className="text-gray-400 text-sm">🎨 영문, 예술적 스타일</p>
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
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-red-400 font-bold mb-2">Veo 3.1</p>
            <p className="text-gray-400 text-sm">🎬 오디오 자동 생성, Google</p>
            <p className="text-gray-500 text-xs mt-2">Gemini → Flow 메뉴</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-cyan-400 font-bold mb-2">Kling AI</p>
            <p className="text-gray-400 text-sm">👥 캐릭터 일관성 최고</p>
            <p className="text-gray-500 text-xs mt-2">klingai.com</p>
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
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-white font-medium mb-2">1. 이미지 프롬프트 생성기 완료</p>
            <ul className="text-gray-400 text-sm space-y-1">
              <li>• 본인이 선정한 바이럴 영상 분석</li>
              <li>• 결과물(.md) 저장</li>
            </ul>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-white font-medium mb-2">2. 바이브 철학관 세션</p>
            <ul className="text-gray-400 text-sm space-y-1">
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
    <div className={`p-6 rounded-2xl border ${highlight ? 'border-purple-500/30 bg-purple-500/5' : 'border-white/10 bg-white/5'}`} style={{ backdropFilter: 'blur(10px)' }}>
      {children}
    </div>
  );
}

function LinkButton({ href, children, large }: { href: string; children: React.ReactNode; large?: boolean }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`block w-full text-center rounded-xl border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 hover:text-white transition-all ${large ? 'py-4 text-lg font-bold' : 'py-3 text-sm font-medium'}`}
    >
      {children}
    </a>
  );
}

function FlowNode({ icon, label, sub, href, onClick, highlight, dashed, final }: {
  icon: string; label: string; sub: string; href?: string; onClick?: () => void; highlight?: boolean; dashed?: boolean; final?: boolean;
}) {
  const content = (
    <div className={`relative z-10 px-6 py-4 rounded-xl text-center transition-all cursor-pointer hover:scale-105 ${
      final ? 'bg-white text-indigo-600 shadow-[0_0_30px_rgba(255,255,255,0.3)]' :
      highlight ? 'bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 shadow-[0_0_20px_rgba(99,102,241,0.3)]' :
      dashed ? 'bg-white/5 border border-dashed border-white/20' :
      'bg-white/5 border border-white/10 hover:border-purple-500/30'
    }`}>
      <div className="text-[10px] font-mono text-gray-500 mb-1 uppercase tracking-wider">{sub}</div>
      <div className="flex items-center justify-center gap-2">
        <span className={`material-symbols-outlined ${final ? 'text-indigo-600' : 'text-white'}`}>{icon}</span>
        <span className={`font-bold text-sm ${final ? 'text-indigo-600' : 'text-white'}`}>{label}</span>
        {href && <span className="material-symbols-outlined text-[12px] text-gray-500">open_in_new</span>}
      </div>
    </div>
  );

  if (href) {
    return <a href={href} target="_blank" rel="noopener noreferrer" className="w-64">{content}</a>;
  }
  if (onClick) {
    return <button onClick={onClick} className="w-64">{content}</button>;
  }
  return <div className="w-64">{content}</div>;
}

function FlowConnector() {
  return <div className="w-[2px] h-8 bg-gradient-to-b from-purple-500/50 to-pink-500/50 my-1" />;
}

function BentoCard({ icon, label, sub, color, href, onClick, highlight }: {
  icon: string; label: string; sub: string; color: string; href?: string; onClick?: () => void; highlight?: boolean;
}) {
  const colorMap: Record<string, string> = {
    indigo: 'group-hover:text-indigo-300 group-hover:bg-indigo-500/20',
    purple: 'group-hover:text-purple-300 group-hover:bg-purple-500/20',
    pink: 'group-hover:text-pink-300 group-hover:bg-pink-500/20',
    blue: 'group-hover:text-blue-300 group-hover:bg-blue-500/20',
  };

  const content = (
    <div className={`group relative h-48 p-6 rounded-3xl flex flex-col justify-between overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:scale-[1.01] ${highlight ? 'border-indigo-500/20' : ''}`} style={{
      background: 'linear-gradient(160deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      backdropFilter: 'blur(20px)',
    }}>
      <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl -mr-10 -mt-10 transition-all ${colorMap[color]}`} />
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gray-800 to-black border border-white/10 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
        <span className="material-symbols-outlined text-gray-300 group-hover:text-white transition-colors">{icon}</span>
      </div>
      <div>
        <h4 className={`text-lg font-bold text-gray-100 mb-1 transition-colors ${colorMap[color]?.split(' ')[0]}`}>{label}</h4>
        <p className="text-sm text-gray-500 font-light">{sub}</p>
      </div>
      <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transform translate-x-4 group-hover:translate-x-0 transition-all duration-300">
        <span className="material-symbols-outlined text-gray-400">arrow_forward</span>
      </div>
    </div>
  );

  if (href) {
    return <a href={href} target="_blank" rel="noopener noreferrer">{content}</a>;
  }
  return <button onClick={onClick} className="w-full text-left">{content}</button>;
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
