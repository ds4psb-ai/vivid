"use client";

/**
 * 아카데미 가이드 페이지
 * Stitch 7 디자인 - 화이트 토큰 버튼 스타일 (완전 재현)
 */

import { useState, useEffect, Suspense, startTransition } from "react";
import { useSearchParams } from "next/navigation";

// Tool Links
const TOOL_LINKS = {
  builder: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221aReu3uy_0Ayxo6KhjC1OS-EJUmOmSLVA%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  vibe: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221wKUuefdolzOVFp7YAxSfcO13prtAWvgu%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  antigravity: "https://antigravity.google",
};

type TabKey = "home" | "setup" | "credit" | "upload" | "prompt" | "parse" | "tools" | "vibe" | "homework";

const NAV_SECTIONS = [
  {
    title: "Dashboard",
    items: [
      { key: "home" as TabKey, label: "홈 대시보드", icon: "dashboard" },
      { key: "setup" as TabKey, label: "환경 설정", icon: "settings" },
      { key: "credit" as TabKey, label: "$300 무료 크레딧", icon: "redeem" },
    ],
  },
  {
    title: "Workflow",
    items: [
      { key: "upload" as TabKey, label: "영상 업로드", icon: "cloud_upload" },
      { key: "prompt" as TabKey, label: "프롬프트 생성", icon: "auto_awesome" },
      { key: "parse" as TabKey, label: "파싱 + 복사", icon: "content_copy" },
      { key: "tools" as TabKey, label: "외부 툴", icon: "build" },
    ],
  },
  {
    title: "기타",
    items: [
      { key: "vibe" as TabKey, label: "바이브 철학관", icon: "psychology" },
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
            {activeTab === "setup" && <SetupContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "credit" && <CreditContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "upload" && <UploadContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "prompt" && <PromptContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "parse" && <ParseContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "tools" && <ToolsContent setActiveTab={(tab) => startTransition(() => setActiveTab(tab))} />}
            {activeTab === "vibe" && <VibeContent />}
            {activeTab === "homework" && <HomeworkContent />}
          </div>
        </main>
      </div>
    </>
  );
}

// ============ Home Content ============
function HomeContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  const workflowSteps = [
    { key: "upload" as TabKey, num: 1, label: "영상 업로드", icon: "cloud_upload", sub: "드래그앤드롭" },
    { key: "upload" as TabKey, num: 2, label: "컷 나누기", icon: "content_cut", sub: "FFmpeg 분석" },
    { key: "prompt" as TabKey, num: 3, label: "프롬프트", icon: "auto_awesome", sub: "AI Studio" },
    { key: "parse" as TabKey, num: 4, label: "파싱", icon: "content_copy", sub: "복사" },
    { key: "tools" as TabKey, num: 5, label: "제작", icon: "build", sub: "외부툴" },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center mt-8 mb-12">
        <div className="inline-block px-4 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-6">
          <span className="text-[10px] font-bold text-indigo-400 tracking-[0.2em] font-mono uppercase">Step-by-Step Workflow</span>
        </div>
        <h2 className="text-4xl md:text-5xl font-black mb-6 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-purple-400 glow-text">
          AI 영상 오마주 & 패러디
        </h2>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed font-light">
          바이럴 영상을 분석하고, AI 엔진을 통해 나만의 유니크한 버전으로<br />
          재창조하는 5단계 워크플로우
        </p>
      </div>

      {/* Horizontal Workflow */}
      <div className="max-w-4xl mx-auto relative mb-12">
        <div className="absolute -inset-1 bg-gradient-to-b from-purple-500/20 to-transparent opacity-30 blur-2xl rounded-[3rem]" />
        <div className="relative bg-[#0f0f11] border border-white/10 rounded-[2.5rem] p-8 shadow-2xl">

          {/* Flow Steps - Horizontal */}
          <div className="flex items-center justify-between gap-2">
            {workflowSteps.map((step, index) => (
              <div key={step.num} className="flex items-center flex-1">
                {/* Step Card */}
                <button
                  onClick={() => setActiveTab(step.key)}
                  className="group flex-1 p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/50 hover:bg-purple-500/10 transition-all duration-300 text-center"
                >
                  <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <span className="material-symbols-outlined text-2xl text-purple-400">{step.icon}</span>
                  </div>
                  <div className="text-[10px] font-mono text-purple-400 mb-1">STEP {step.num}</div>
                  <div className="text-white font-bold text-sm mb-1">{step.label}</div>
                  <div className="text-gray-500 text-xs">{step.sub}</div>
                </button>

                {/* Arrow */}
                {index < workflowSteps.length - 1 && (
                  <div className="mx-2 flex-shrink-0">
                    <span className="material-symbols-outlined text-purple-500/50 text-xl">arrow_forward</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Output */}
          <div className="mt-8 text-center">
            <div className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30">
              <span className="material-symbols-outlined text-emerald-400">check_circle</span>
              <span className="font-bold text-emerald-300 text-lg">나만의 영상 완성!</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="max-w-2xl mx-auto">
        <div className="grid grid-cols-2 gap-4">
          <a
            href={TOOL_LINKS.builder}
            target="_blank"
            rel="noopener noreferrer"
            className="p-6 rounded-xl bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-500/30 hover:border-purple-500/50 transition-all text-center group"
          >
            <span className="material-symbols-outlined text-purple-400 text-3xl mb-3 block group-hover:scale-110 transition-transform">movie_filter</span>
            <p className="text-white font-bold">통합빌더</p>
            <p className="text-gray-500 text-xs mt-1">오마주 + 변주 프롬프트 생성</p>
          </a>
          <button
            onClick={() => setActiveTab("vibe")}
            className="p-6 rounded-xl bg-white/5 border border-white/10 hover:border-purple-500/30 transition-all text-center group"
          >
            <span className="material-symbols-outlined text-purple-400 text-3xl mb-3 block group-hover:scale-110 transition-transform">psychology</span>
            <p className="text-white font-bold">바이브 철학관</p>
            <p className="text-gray-500 text-xs mt-1">나의 감성 프로필 (Optional)</p>
          </button>
        </div>
      </div>

      {/* Divider */}
      <div className="mt-16 text-center opacity-30">
        <div className="h-px w-32 bg-gradient-to-r from-transparent via-gray-500 to-transparent mx-auto" />
      </div>
    </div>
  );
}

// ============ Setup Content ============
function SetupContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
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
          <WhiteButton href={TOOL_LINKS.builder}>🎬 통합빌더</WhiteButton>
          <WhiteButton href={TOOL_LINKS.vibe}>🔮 바이브 철학관</WhiteButton>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("credit")} label="$300 무료 크레딧" />
    </div>
  );
}

// ============ Upload Content ============
function UploadContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  const [timestampInput, setTimestampInput] = useState("");
  const [copied, setCopied] = useState(false);

  // Video upload states
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "processing" | "done" | "error">("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [detectedTimestamps, setDetectedTimestamps] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  // Threshold mode: "precise" (0.19) or "standard" (0.25)
  type ThresholdMode = "precise" | "standard";
  const [thresholdMode, setThresholdMode] = useState<ThresholdMode>("standard");
  const [usedThresholdMode, setUsedThresholdMode] = useState<ThresholdMode>("standard");
  const threshold = thresholdMode === "precise" ? 0.19 : 0.25;

  // Parse timestamps from Antigravity output (formats: "00:01.67" or "0:00.00")
  const parseTimestamps = (input: string): string[] => {
    const pattern = /\d{1,2}:\d{2}\.\d{2}/g;
    return input.match(pattern) || [];
  };

  const parsedTimestamps = parseTimestamps(timestampInput);
  const allTimestamps = detectedTimestamps.length > 0 ? detectedTimestamps : parsedTimestamps;

  // Format for Builder1 input - 타임스탬프만
  const formatForBuilder1 = (): string => {
    if (allTimestamps.length === 0) return "";
    return allTimestamps.join('\n');
  };

  const handleCopy = async () => {
    const formatted = formatForBuilder1();
    if (formatted) {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Handle drag events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOut = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await processVideo(files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await processVideo(files[0]);
    }
  };

  const processVideo = async (file: File) => {
    // Validate file type
    if (!file.type.startsWith("video/")) {
      setErrorMessage("영상 파일만 업로드 가능합니다.");
      setUploadStatus("error");
      return;
    }

    // Check file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
      setErrorMessage("파일 크기는 100MB 이하만 가능합니다.");
      setUploadStatus("error");
      return;
    }

    setUploadStatus("uploading");
    setUploadProgress(0);
    setErrorMessage("");
    setDetectedTimestamps([]);
    setUploadedFile(file);

    const formData = new FormData();
    formData.append("video", file);

    try {
      // Upload with progress
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) {
          setUploadProgress(Math.round((event.loaded / event.total) * 100));
        }
      });

      xhr.addEventListener("load", async () => {
        if (xhr.status === 200) {
          const result = JSON.parse(xhr.responseText);
          setDetectedTimestamps(result.timestamps || []);
          setUploadStatus("done");
        } else {
          setErrorMessage("서버 오류가 발생했습니다.");
          setUploadStatus("error");
        }
      });

      xhr.addEventListener("error", () => {
        setErrorMessage("업로드 중 오류가 발생했습니다.");
        setUploadStatus("error");
      });

      setUploadStatus("processing");
      setUsedThresholdMode(thresholdMode);
      xhr.open("POST", `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/scene-detect/?threshold=${threshold}`);
      xhr.send(formData);

    } catch {
      setErrorMessage("네트워크 오류가 발생했습니다.");
      setUploadStatus("error");
    }
  };

  const downloadFrames = async () => {
    if (!uploadedFile) {
      setErrorMessage("먼저 영상을 업로드해주세요.");
      return;
    }

    setUploadStatus("processing");
    setErrorMessage("");

    const formData = new FormData();
    formData.append("video", uploadedFile);

    // 분석에 사용된 threshold 값으로 프레임 추출
    const usedThreshold = usedThresholdMode === "precise" ? 0.19 : 0.25;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1/scene-detect/with-frames?threshold=${usedThreshold}`,
        { method: "POST", body: formData }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${uploadedFile.name.replace(/\.[^/.]+$/, "")}_scenes.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setUploadStatus("done");
      } else {
        setErrorMessage("프레임 추출 실패");
        setUploadStatus("error");
      }
    } catch {
      setErrorMessage("네트워크 오류");
      setUploadStatus("error");
    }
  };

  const resetUpload = () => {
    setUploadStatus("idle");
    setUploadProgress(0);
    setDetectedTimestamps([]);
    setErrorMessage("");
    setUploadedFile(null);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="영상 업로드 + 컷 나누기" sub="레퍼런스 영상 다운로드 → 업로드 → 씬 분석" />

      {/* Step 0: 영상 다운로더 - Premium Design */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-red-500 flex items-center justify-center shadow-[0_0_20px_rgba(236,72,153,0.3)]">
            <span className="material-symbols-outlined text-white">download</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">STEP 0. 레퍼런스 영상 다운로드</h3>
            <p className="text-gray-500 text-xs">오마주할 바이럴 영상을 먼저 다운받으세요</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {/* YouTube Shorts */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/20">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-red-400 text-lg">play_circle</span>
              <span className="text-red-400 font-bold text-sm">YouTube</span>
            </div>
            <div className="space-y-2">
              <a href="https://savefrom.net" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">savefrom.net</a>
              <a href="https://publer.com/tools/youtube-short-downloader" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">publer.com</a>
            </div>
          </div>

          {/* TikTok */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-pink-500/10 to-pink-600/5 border border-pink-500/20">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-pink-400 text-lg">music_note</span>
              <span className="text-pink-400 font-bold text-sm">TikTok</span>
            </div>
            <div className="space-y-2">
              <a href="https://snaptik.app" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">snaptik.app</a>
              <a href="https://ssstik.io" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">ssstik.io</a>
            </div>
          </div>

          {/* Instagram */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-fuchsia-600/5 border border-purple-500/20">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-purple-400 text-lg">photo_camera</span>
              <span className="text-purple-400 font-bold text-sm">Instagram</span>
            </div>
            <div className="space-y-2">
              <a href="https://snapinsta.to" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">snapinsta.to</a>
              <a href="https://sssinstagram.com/reels-downloader" target="_blank" rel="noopener noreferrer" className="block text-xs text-gray-400 hover:text-white transition-colors">sssinstagram.com</a>
            </div>
          </div>
        </div>

        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <p className="text-amber-300 text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">lightbulb</span>
            다운받은 영상을 아래 업로드 영역에 드래그하세요
          </p>
        </div>
      </ContentCard>

      {/* Step 1: Scene Detection Upload Section - Premium Design */}
      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.3)]">
            <span className="material-symbols-outlined text-white">movie_filter</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">STEP 1. 자동 씬 감지</h3>
            <p className="text-gray-500 text-xs">FFmpeg 기반 정밀 분석</p>
          </div>
        </div>

        {/* Threshold Mode Selector - Segmented Control */}
        {uploadStatus === "idle" && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-purple-400 text-sm">tune</span>
              <span className="text-gray-400 text-sm font-medium">감지 모드 선택</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {/* 표준 모드 (기본) */}
              <button
                onClick={() => setThresholdMode("standard")}
                className={`relative p-4 rounded-xl border-2 transition-all text-left group ${
                  thresholdMode === "standard"
                    ? "border-emerald-500 bg-emerald-500/10"
                    : "border-white/10 hover:border-emerald-500/30 hover:bg-emerald-500/5"
                }`}
              >
                {thresholdMode === "standard" && (
                  <div className="absolute top-2 right-2">
                    <span className="material-symbols-outlined text-emerald-400 text-lg">check_circle</span>
                  </div>
                )}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🎯</span>
                  <span className={`font-bold ${thresholdMode === "standard" ? "text-emerald-400" : "text-white"}`}>
                    표준 모드
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-medium">추천</span>
                </div>
                <p className="text-gray-400 text-xs leading-relaxed">
                  트랜지션 효과는 무시<br/>
                  <span className="text-gray-500">일반 영상 · 페이드/디졸브 있는 영상</span>
                </p>
              </button>

              {/* 정밀 모드 */}
              <button
                onClick={() => setThresholdMode("precise")}
                className={`relative p-4 rounded-xl border-2 transition-all text-left group ${
                  thresholdMode === "precise"
                    ? "border-purple-500 bg-purple-500/10"
                    : "border-white/10 hover:border-purple-500/30 hover:bg-purple-500/5"
                }`}
              >
                {thresholdMode === "precise" && (
                  <div className="absolute top-2 right-2">
                    <span className="material-symbols-outlined text-purple-400 text-lg">check_circle</span>
                  </div>
                )}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">⚡</span>
                  <span className={`font-bold ${thresholdMode === "precise" ? "text-purple-400" : "text-white"}`}>
                    정밀 모드
                  </span>
                </div>
                <p className="text-gray-400 text-xs leading-relaxed">
                  빠른 컷도 놓치지 않고 감지<br/>
                  <span className="text-gray-500">빠른 편집 · 많은 장면 전환</span>
                </p>
              </button>
            </div>
            <p className="mt-3 text-gray-500 text-xs flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm">info</span>
              잘 모르겠다면 <span className="text-emerald-400 font-medium">표준 모드</span>로 시작하세요
            </p>
          </div>
        )}

        {uploadStatus === "idle" && (
          <div
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer group ${isDragging
              ? "border-purple-500 bg-purple-500/10"
              : "border-white/20 hover:border-purple-500/50 hover:bg-purple-500/5"
              }`}
            onClick={() => document.getElementById("videoFileInput")?.click()}
          >
            {/* Glow effect on hover */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

            <input
              id="videoFileInput"
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="relative z-10">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined text-4xl text-purple-400">
                  cloud_upload
                </span>
              </div>
              <p className="text-white font-bold text-lg mb-1">영상 파일을 드래그하거나 클릭</p>
              <p className="text-gray-500 text-sm">MP4, MOV, WebM 지원 • 최대 100MB</p>
            </div>
          </div>
        )}

        {(uploadStatus === "uploading" || uploadStatus === "processing") && (
          <div className="p-8 rounded-2xl bg-black/30 border border-purple-500/30">
            <div className="flex items-center gap-4 mb-4">
              <div className="relative">
                <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-500 border-t-transparent" />
                </div>
                {uploadStatus === "processing" && (
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full animate-pulse" />
                )}
              </div>
              <div>
                <p className="text-white font-bold">
                  {uploadStatus === "uploading" ? "업로드 중..." : "씬 분석 중..."}
                </p>
                <p className="text-gray-500 text-sm">
                  {uploadStatus === "uploading" ? `${uploadProgress}% 완료` : "FFmpeg 처리 중"}
                </p>
              </div>
            </div>
            <div className="h-2 bg-black/50 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
                style={{ width: uploadStatus === "processing" ? "100%" : `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {uploadStatus === "done" && detectedTimestamps.length > 0 && (
          <div className="space-y-5">
            {/* Success header */}
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-emerald-400">check_circle</span>
                  </div>
                  <div>
                    <p className="text-emerald-400 font-bold">{detectedTimestamps.length}개 씬 감지 완료!</p>
                    <p className="text-emerald-400/60 text-xs flex items-center gap-1.5 mt-0.5">
                      {usedThresholdMode === "precise" ? "⚡ 정밀 모드" : "🎯 표준 모드"}로 분석됨
                    </p>
                  </div>
                </div>
                <button
                  onClick={resetUpload}
                  className="px-3 py-1.5 rounded-lg text-gray-400 text-sm hover:text-white hover:bg-white/5 transition-all"
                >
                  다시 업로드
                </button>
              </div>

              {/* Re-analyze with different mode */}
              {uploadedFile && usedThresholdMode === "standard" && (
                <button
                  onClick={() => {
                    setThresholdMode("precise");
                    processVideo(uploadedFile);
                  }}
                  className="w-full py-3 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-300 text-sm font-medium hover:bg-purple-500/20 hover:border-purple-500/50 transition-all flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">search</span>
                  혹시 놓친 씬이 있나요? ⚡ 정밀 모드로 다시 분석해보기
                </button>
              )}
              {uploadedFile && usedThresholdMode === "precise" && (
                <button
                  onClick={() => {
                    setThresholdMode("standard");
                    processVideo(uploadedFile);
                  }}
                  className="w-full py-2.5 rounded-lg bg-white/5 border border-white/10 text-gray-300 text-sm font-medium hover:bg-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">refresh</span>
                  씬이 너무 많나요? 🎯 표준 모드로 다시 분석해보기
                </button>
              )}
            </div>

            {/* Result preview */}
            <div className="p-4 rounded-xl bg-black/30 border border-emerald-500/20 overflow-hidden">
              <pre className="text-emerald-200 text-xs whitespace-pre-wrap font-mono leading-relaxed">
                {formatForBuilder1()}
              </pre>
            </div>

            {/* Action buttons */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleCopy}
                className={`py-4 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 ${copied
                  ? 'bg-emerald-500 text-white shadow-[0_0_20px_rgba(52,211,153,0.3)]'
                  : 'bg-white text-gray-900 hover:bg-gray-100 shadow-[0_4px_20px_rgba(255,255,255,0.1)]'
                  }`}
              >
                <span className="material-symbols-outlined text-lg">{copied ? 'check' : 'content_copy'}</span>
                {copied ? '복사됨!' : 'Builder1 입력용 복사'}
              </button>
              <button
                onClick={downloadFrames}
                className="py-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-bold hover:from-purple-700 hover:to-indigo-700 transition-all flex items-center justify-center gap-2 shadow-[0_4px_20px_rgba(168,85,247,0.3)]"
              >
                <span className="material-symbols-outlined text-lg">download</span>
                프레임 이미지 다운로드
              </button>
            </div>
          </div>
        )}

        {uploadStatus === "error" && (
          <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-red-400">error</span>
              </div>
              <p className="text-red-400 font-bold">{errorMessage}</p>
            </div>
            <button
              onClick={resetUpload}
              className="w-full py-3 rounded-xl bg-white text-gray-900 text-sm font-bold hover:bg-gray-100 transition-colors"
            >
              다시 시도
            </button>
          </div>
        )}
      </ContentCard>

      {/* Manual Timestamp Helper Section (Fallback) */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
            <span className="material-symbols-outlined text-gray-400 text-sm">keyboard</span>
          </div>
          <div>
            <h3 className="text-white font-bold">타임스탬프 수동 입력</h3>
            <p className="text-gray-500 text-xs">자동 감지가 안 될 때 백업용</p>
          </div>
        </div>

        <textarea
          value={timestampInput}
          onChange={(e) => setTimestampInput(e.target.value)}
          placeholder="예: 00:00.00, 00:01.67, 00:04.56, 00:07.06..."
          className="w-full h-20 p-4 rounded-xl bg-black/50 border border-white/10 text-gray-200 text-sm placeholder-gray-600 focus:border-purple-500/50 focus:outline-none focus:ring-1 focus:ring-purple-500/20 resize-none font-mono"
        />

        {parsedTimestamps.length > 0 && detectedTimestamps.length === 0 && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-emerald-400 text-sm font-medium flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                {parsedTimestamps.length}개 씬 감지됨
              </p>
              <button
                onClick={handleCopy}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${copied ? 'bg-emerald-500 text-white' : 'bg-white text-gray-900 hover:bg-gray-100'
                  }`}
              >
                <span className="material-symbols-outlined text-sm">{copied ? 'check' : 'content_copy'}</span>
                {copied ? '복사됨!' : '복사'}
              </button>
            </div>
            <div className="p-3 rounded-xl bg-black/30 border border-emerald-500/20">
              <pre className="text-emerald-200 text-xs whitespace-pre-wrap font-mono">
                {formatForBuilder1()}
              </pre>
            </div>
          </div>
        )}
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("prompt")} label="프롬프트 생성" />
    </div>
  );
}

// ============ Prompt Content ============
function PromptContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="통합빌더" sub="영상 → 씬 분석 → 이미지/모션 프롬프트 생성" />
      <ContentCard highlight>
        <WhiteButton href={TOOL_LINKS.builder} large>🎬 통합빌더 열기</WhiteButton>
        <p className="text-gray-500 text-xs mt-3 text-center">Google AI Studio에서 실행됩니다</p>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">워크플로우</h3>
        <div className="space-y-3 text-sm">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 1</span><span className="text-gray-300">씬 분석 + 오마주 스타일 입력</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 2</span><span className="text-gray-300">IMAGE 프롬프트 생성</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 3</span><span className="text-gray-300">MOTION 프롬프트 생성</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">STEP 4</span><span className="text-gray-300">오마주 워크플로우 다운로드</span></div>
          <div className="flex gap-3"><span className="text-cyan-400 font-bold">STEP 5</span><span className="text-gray-300">변주 워크플로우 (선택)</span></div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">오마주 vs 변주</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
            <p className="text-purple-400 font-bold mb-2">🎭 오마주 (STEP 4)</p>
            <p className="text-gray-400 text-sm">구도/타이밍 100% 유지</p>
            <p className="text-gray-500 text-xs mt-2">인종/문화/의상만 변경</p>
          </div>
          <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
            <p className="text-cyan-400 font-bold mb-2">✨ 변주 (STEP 5)</p>
            <p className="text-gray-400 text-sm">구도/내용 변경 가능</p>
            <p className="text-gray-500 text-xs mt-2">A/B/C 옵션 선택</p>
          </div>
        </div>
      </ContentCard>
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">다운로드 후 다음 단계</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 text-sm mb-2">📥 오마쥬.md 또는 변주.md 다운로드 완료 후</p>
          <p className="text-emerald-400 font-medium">→ 파싱 + 복사 탭에서 씬별 프롬프트 복사</p>
        </div>
      </ContentCard>

      <NextStepButton onClick={() => setActiveTab("parse")} label="파싱 + 복사" />
    </div>
  );
}

// ============ Parse Content ============
import { parseBuilder2Output, insertCrefUrl, type Builder2Scene, type Builder2ParseResult } from "@/lib/builder2-md-parser";

function ParseContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  const [mdInput, setMdInput] = useState("");
  const [parseResult, setParseResult] = useState<Builder2ParseResult | null>(null);
  const [activeType, setActiveType] = useState<"ohmage" | "variation">("ohmage");
  const [crefUrl, setCrefUrl] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('academy_cref_url') || "";
    }
    return "";
  });
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});
  const [completedPrompts, setCompletedPrompts] = useState<Set<string>>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('academy_parse_progress');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    }
    return new Set();
  });
  const [isDragging, setIsDragging] = useState(false);

  // 파일 드래그앤드롭 핸들러
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.md') || file.type === 'text/markdown' || file.type === 'text/plain') {
        const text = await file.text();
        setMdInput(text);
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const text = await files[0].text();
      setMdInput(text);
    }
  };

  // Parse MD when input changes
  useEffect(() => {
    if (mdInput.trim()) {
      const result = parseBuilder2Output(mdInput);
      setParseResult(result);
      // Auto-select type based on what's available
      if (result.hasVariation && !result.hasOhmage) {
        setActiveType("variation");
      } else {
        setActiveType("ohmage");
      }
    } else {
      setParseResult(null);
    }
  }, [mdInput]);

  // Save cref URL to localStorage
  useEffect(() => {
    if (crefUrl) {
      localStorage.setItem('academy_cref_url', crefUrl);
    }
  }, [crefUrl]);

  const handleCopy = async (key: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedStates(prev => ({ ...prev, [key]: true }));

    // 진행도 저장
    const newCompleted = new Set(completedPrompts).add(key);
    setCompletedPrompts(newCompleted);
    localStorage.setItem('academy_parse_progress', JSON.stringify([...newCompleted]));

    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [key]: false }));
    }, 2000);
  };

  const clearProgress = () => {
    setCompletedPrompts(new Set());
    localStorage.removeItem('academy_parse_progress');
  };

  const activeScenes = activeType === "ohmage" ? parseResult?.ohmageScenes : parseResult?.variationScenes;

  const totalPrompts = activeScenes?.reduce((acc, scene) => {
    let count = 0;
    if (scene.imagePrompts.nanoBanana) count++;
    if (scene.imagePrompts.midjourney) count++;
    if (scene.motionPrompts.kling) count++;
    if (scene.motionPrompts.veo) count++;
    return acc + count;
  }, 0) || 0;

  const completedCount = activeScenes?.reduce((acc, scene) => {
    let count = 0;
    if (completedPrompts.has(`${scene.sceneNum}-nanoBanana`)) count++;
    if (completedPrompts.has(`${scene.sceneNum}-midjourney`)) count++;
    if (completedPrompts.has(`${scene.sceneNum}-kling`)) count++;
    if (completedPrompts.has(`${scene.sceneNum}-veo`)) count++;
    return acc + count;
  }, 0) || 0;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="파싱 + 복사" sub="MD 결과물 붙여넣기 → 씬별 프롬프트 복사" />

      {/* MD Input */}
      <ContentCard highlight>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">📋 MD 결과물</h3>
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".md,text/markdown,text/plain"
              onChange={handleFileSelect}
              className="hidden"
            />
            <span className="px-3 py-1.5 rounded-lg bg-white/10 text-gray-300 text-xs font-medium hover:bg-white/20 transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">upload_file</span>
              파일 선택
            </span>
          </label>
        </div>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative rounded-xl transition-all ${isDragging ? 'ring-2 ring-purple-500' : ''}`}
        >
          {isDragging && (
            <div className="absolute inset-0 bg-purple-500/20 rounded-xl flex items-center justify-center z-10 pointer-events-none">
              <span className="text-purple-300 font-bold">MD 파일을 여기에 놓으세요</span>
            </div>
          )}
          <textarea
            value={mdInput}
            onChange={(e) => setMdInput(e.target.value)}
            placeholder="통합빌더에서 다운로드한 MD 파일을 드래그하거나 내용을 붙여넣으세요..."
            className="w-full h-40 p-4 rounded-xl bg-black/50 border border-purple-500/30 text-gray-200 text-sm placeholder-gray-600 focus:border-purple-500/50 focus:outline-none focus:ring-1 focus:ring-purple-500/20 resize-none font-mono"
          />
        </div>
        {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-emerald-400 text-sm flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                파싱 완료!
              </span>
              <span className="text-gray-500 text-xs">
                오마주 {parseResult.ohmageScenes.length}개 / 변주 {parseResult.variationScenes.length}개
              </span>
            </div>
            {/* 진행도 표시 */}
            {totalPrompts > 0 && (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 transition-all duration-300"
                      style={{ width: `${(completedCount / totalPrompts) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400">{completedCount}/{totalPrompts}</span>
                </div>
                {completedCount > 0 && (
                  <button
                    onClick={clearProgress}
                    className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    초기화
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </ContentCard>

      {/* Type Tabs + cref URL */}
      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <>
          <div className="flex items-center gap-4">
            {/* Type Tabs */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveType("ohmage")}
                disabled={!parseResult.hasOhmage}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeType === "ohmage"
                  ? "bg-purple-500 text-white"
                  : parseResult.hasOhmage
                    ? "bg-white/10 text-gray-400 hover:bg-white/20"
                    : "bg-white/5 text-gray-600 cursor-not-allowed"
                  }`}
              >
                🎭 오마주 ({parseResult.ohmageScenes.length})
              </button>
              <button
                onClick={() => setActiveType("variation")}
                disabled={!parseResult.hasVariation}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeType === "variation"
                  ? "bg-cyan-500 text-white"
                  : parseResult.hasVariation
                    ? "bg-white/10 text-gray-400 hover:bg-white/20"
                    : "bg-white/5 text-gray-600 cursor-not-allowed"
                  }`}
              >
                ✨ 변주 ({parseResult.variationScenes.length})
              </button>
            </div>

            {/* cref URL Input */}
            <div className="flex-1 flex items-center gap-2">
              <span className="text-gray-500 text-xs">--cref URL:</span>
              <input
                type="text"
                value={crefUrl}
                onChange={(e) => setCrefUrl(e.target.value)}
                placeholder="앵커 이미지 URL (Midjourney용)"
                className="flex-1 px-3 py-2 rounded-lg bg-black/30 border border-white/10 text-gray-200 text-sm placeholder-gray-600 focus:border-purple-500/30 focus:outline-none"
              />
            </div>
          </div>

          {/* Scene Cards */}
          <div className="space-y-4">
            {activeScenes?.map((scene) => (
              <SceneCard
                key={`${activeType}-${scene.sceneNum}`}
                scene={scene}
                crefUrl={crefUrl}
                copiedStates={copiedStates}
                completedPrompts={completedPrompts}
                onCopy={handleCopy}
              />
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!parseResult && (
        <ContentCard>
          <div className="text-center py-8">
            <span className="material-symbols-outlined text-4xl text-gray-600 mb-4 block">content_paste</span>
            <p className="text-gray-500">MD 파일 내용을 위에 붙여넣으면 씬별로 파싱됩니다</p>
          </div>
        </ContentCard>
      )}

      <NextStepButton onClick={() => setActiveTab("tools")} label="외부 툴" />
    </div>
  );
}

// ============ Scene Card Component ============
const PROMPT_COLORS: Record<string, string> = {
  nanoBanana: "text-orange-400",
  midjourney: "text-violet-400",
  kling: "text-cyan-400",
  veo: "text-red-400",
};

function SceneCard({
  scene,
  crefUrl,
  copiedStates,
  completedPrompts,
  onCopy,
}: {
  scene: Builder2Scene;
  crefUrl: string;
  copiedStates: Record<string, boolean>;
  completedPrompts: Set<string>;
  onCopy: (key: string, text: string) => void;
}) {
  const midjourneyPrompt = crefUrl
    ? insertCrefUrl(scene.imagePrompts.midjourney, crefUrl)
    : scene.imagePrompts.midjourney;

  const promptItems = [
    { key: "nanoBanana", label: "NanoBanana", prompt: scene.imagePrompts.nanoBanana },
    { key: "midjourney", label: "Midjourney", prompt: midjourneyPrompt },
    { key: "kling", label: "Kling", prompt: scene.motionPrompts.kling },
    { key: "veo", label: "Veo", prompt: scene.motionPrompts.veo },
  ].filter(item => item.prompt);

  return (
    <ContentCard>
      <div className="flex items-center gap-3 mb-4">
        <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${scene.isAnchor
          ? "bg-amber-500/20 text-amber-400"
          : "bg-purple-500/20 text-purple-400"
          }`}>
          {scene.sceneNum}
        </span>
        <div>
          <h3 className="text-white font-bold">{scene.title || `Scene ${scene.sceneNum}`}</h3>
          {scene.beatTimestamp && (
            <p className="text-gray-500 text-xs">{scene.beatTimestamp}</p>
          )}
        </div>
        {scene.isAnchor && (
          <span className="ml-auto px-2 py-1 rounded text-xs font-bold bg-amber-500/20 text-amber-400">
            ANCHOR
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        {promptItems.map((item) => {
          const copyKey = `${scene.sceneNum}-${item.key}`;
          const isCopied = copiedStates[copyKey];
          const isCompleted = completedPrompts.has(copyKey);

          return (
            <div key={item.key} className={`space-y-2 ${isCompleted ? 'opacity-50' : ''}`}>
              <div className="flex items-center justify-between">
                <span className={`text-xs font-bold ${PROMPT_COLORS[item.key]}`}>
                  {isCompleted && <span className="mr-1">✓</span>}
                  {item.label}
                </span>
                <button
                  onClick={() => onCopy(copyKey, item.prompt)}
                  className={`px-2 py-1 rounded text-xs font-bold transition-all ${isCopied
                    ? "bg-emerald-500 text-white"
                    : isCompleted
                      ? "bg-gray-700 text-gray-400 hover:bg-gray-600"
                      : "bg-white text-gray-900 hover:bg-gray-100"
                    }`}
                >
                  {isCopied ? "✓" : isCompleted ? "재복사" : "복사"}
                </button>
              </div>
              <div className={`p-2 rounded-lg bg-black/30 border max-h-20 overflow-y-auto ${isCompleted ? 'border-emerald-500/30' : 'border-white/10'}`}>
                <p className="text-gray-300 text-xs font-mono whitespace-pre-wrap break-all">
                  {item.prompt.slice(0, 200)}{item.prompt.length > 200 ? "..." : ""}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </ContentCard>
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

// ============ Credit Content ============
const FREE_TRIAL_URL = "https://console.cloud.google.com/freetrial/signup/tos?facet_url=https:%2F%2Fcloud.google.com%2Ffree&facet_utm_source=google&facet_utm_campaign=17100102-GCP-DR-APAC-KR-ko-Google-BKWS-MIX-GenericCloud&facet_utm_medium=cpc";

function CreditContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="$300 무료 크레딧" sub="Google Cloud 가입하면 90일간 40만원 상당 무료" />

      {/* Step 1 */}
      <ContentCard highlight>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-bold flex items-center justify-center">1</span>
          <p className="text-white font-bold">무료 크레딧 신청</p>
        </div>
        <div className="space-y-3 text-sm text-gray-300 mb-4">
          <div className="flex gap-3"><span className="text-emerald-400 font-bold">1.</span><span>아래 버튼 클릭해서 신청 페이지로 이동</span></div>
          <div className="flex gap-3"><span className="text-emerald-400 font-bold">2.</span><span>Google 계정으로 로그인</span></div>
          <div className="flex gap-3"><span className="text-emerald-400 font-bold">3.</span><span>결제 정보 입력</span></div>
        </div>
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 mb-6">
          <p className="text-emerald-300 text-sm">결제 정보 입력해도 바로 결제 안 됨</p>
          <p className="text-emerald-300/70 text-xs mt-1">$300 크레딧 먼저 소진 / 유료 전환 버튼 안 누르면 자동 결제 없음</p>
        </div>
        <a
          href={FREE_TRIAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-4 bg-white text-gray-900 font-bold text-center rounded-xl hover:bg-gray-100 transition-all"
        >
          $300 무료 크레딧 받기
        </a>
      </ContentCard>

      {/* Step 2 */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 text-sm font-bold flex items-center justify-center">2</span>
          <p className="text-white font-bold">API Key 만들기</p>
        </div>
        <div className="space-y-3 text-sm text-gray-300 mb-4">
          <div className="flex gap-3"><span className="text-purple-400 font-bold">1.</span><span>아래 버튼 클릭 → Google AI Studio 이동</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">2.</span><span>왼쪽 위 파란색 "Create API Key" 버튼 클릭</span></div>
          <div className="flex gap-3"><span className="text-purple-400 font-bold">3.</span><span>생성된 키(AIza...) 복사</span></div>
        </div>
        <a
          href="https://aistudio.google.com/app/apikey"
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-3 bg-white text-gray-900 font-bold text-center rounded-xl hover:bg-gray-100 transition-all"
        >
          Google AI Studio 열기
        </a>
      </ContentCard>

      {/* Step 3 */}
      <ContentCard>
        <div className="flex items-center gap-3 mb-4">
          <span className="w-7 h-7 rounded-full bg-pink-500/20 text-pink-400 text-sm font-bold flex items-center justify-center">3</span>
          <p className="text-white font-bold">키 입력</p>
        </div>
        <div className="space-y-2 text-sm text-gray-300">
          <p>앱 사이드바 하단 → <span className="text-white font-medium">API Key</span> 버튼 클릭</p>
          <p>→ 복사한 키 붙여넣기</p>
        </div>
      </ContentCard>

      {/* 주의사항 */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">주의사항</h3>
        <div className="space-y-3 text-sm">
          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <p className="text-yellow-300 font-medium">90일(3개월) 한정</p>
            <p className="text-yellow-300/70 text-xs mt-1">$300 다 쓰거나 90일 지나면 종료</p>
          </div>
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <p className="text-red-300 font-medium">사용량 반영 시간차 있음</p>
            <p className="text-red-300/70 text-xs mt-1">실시간 아님 → 남은 크레딧 자주 확인</p>
          </div>
          <div className="p-3 rounded-lg bg-gray-500/10 border border-gray-500/20">
            <p className="text-gray-300 font-medium">크레딧 확인</p>
            <p className="text-gray-300/70 text-xs mt-1">Google Cloud Console → 결제 → 크레딧</p>
          </div>
        </div>
      </ContentCard>

      <p className="text-center text-xs text-gray-600">API Key는 브라우저에만 저장되고 서버로 전송되지 않음</p>

      <NextStepButton onClick={() => setActiveTab("upload")} label="영상 업로드" />
    </div>
  );
}

// ============ Tools Content ============
function ToolsContent({ setActiveTab }: { setActiveTab: (tab: TabKey) => void }) {
  const [openTool, setOpenTool] = useState<string | null>(null);
  const [openFaq, setOpenFaq] = useState<string | null>(null);

  const toggleTool = (tool: string) => {
    setOpenTool(openTool === tool ? null : tool);
  };

  const toggleFaq = (faq: string) => {
    setOpenFaq(openFaq === faq ? null : faq);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="외부 툴" sub="파싱 탭에서 복사한 프롬프트를 여기 도구에 붙여넣기" />

      {/* Workflow Connection Notice */}
      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-emerald-400">link</span>
          <div>
            <p className="text-emerald-300 font-bold text-sm">워크플로우 연결</p>
            <p className="text-emerald-200/70 text-xs mt-1">
              <span className="text-white font-medium">파싱 탭</span>에서 복사한 프롬프트 → 아래 도구에 붙여넣기
            </p>
          </div>
        </div>
      </div>

      {/* Image Tools Section */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-purple-400">image</span>
          이미지 생성
        </h3>

        {/* NanoBanana Pro */}
        <ToolDetailCard
          title="NanoBanana Pro"
          color="orange"
          url="https://gemini.google.com"
          isOpen={openTool === "nanobanana"}
          onToggle={() => toggleTool("nanobanana")}
          badge="한글 OK"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">실행 단계</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-orange-400 font-bold">1.</span>gemini.google.com 접속</li>
                <li className="flex gap-2"><span className="text-orange-400 font-bold">2.</span>오른쪽 상단 모델 선택 → "2.0 Flash (Experimental)"</li>
                <li className="flex gap-2"><span className="text-orange-400 font-bold">3.</span>파싱탭에서 복사한 NanoBanana 프롬프트 붙여넣기</li>
                <li className="flex gap-2"><span className="text-orange-400 font-bold">4.</span>생성된 이미지 다운로드 (우클릭 → 이미지 저장)</li>
              </ol>
            </div>
            <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <p className="text-orange-300 text-xs">💡 <span className="font-bold">팁:</span> 한글 프롬프트 100% 지원, Google AI Pro 구독 포함</p>
            </div>
          </div>
        </ToolDetailCard>

        {/* Midjourney V7 */}
        <ToolDetailCard
          title="Midjourney V7"
          color="violet"
          url="https://www.midjourney.com"
          isOpen={openTool === "midjourney"}
          onToggle={() => toggleTool("midjourney")}
          badge="--cref"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">웹사이트 방법 (권장)</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-violet-400 font-bold">1.</span>midjourney.com 접속 → 로그인</li>
                <li className="flex gap-2"><span className="text-violet-400 font-bold">2.</span>하단 프롬프트 입력창에 붙여넣기</li>
                <li className="flex gap-2"><span className="text-violet-400 font-bold">3.</span>Enter로 생성</li>
              </ol>
            </div>
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">Discord 방법</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-violet-400 font-bold">1.</span>Discord → Midjourney 서버</li>
                <li className="flex gap-2"><span className="text-violet-400 font-bold">2.</span><code className="text-violet-300 bg-violet-500/20 px-1 rounded">/imagine</code> 명령어 + 프롬프트</li>
              </ol>
            </div>

            {/* Parameter Table */}
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">파라미터 레퍼런스</p>
              <div className="overflow-hidden rounded-lg border border-violet-500/20">
                <table className="w-full text-xs">
                  <thead className="bg-violet-500/10">
                    <tr>
                      <th className="text-left text-violet-300 px-3 py-2 font-bold">파라미터</th>
                      <th className="text-left text-violet-300 px-3 py-2 font-bold">설명</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-violet-500/10">
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--ar 9:16</td><td className="px-3 py-1.5 text-gray-400">세로 비율 (숏폼)</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--ar 16:9</td><td className="px-3 py-1.5 text-gray-400">가로 비율</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--v 7</td><td className="px-3 py-1.5 text-gray-400">버전 7</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--style raw</td><td className="px-3 py-1.5 text-gray-400">실사 느낌</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--stylize 250</td><td className="px-3 py-1.5 text-gray-400">스타일 강도 (0~1000)</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--cref [URL]</td><td className="px-3 py-1.5 text-gray-400">캐릭터 참조 URL</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--cw 30~100</td><td className="px-3 py-1.5 text-gray-400">참조 강도 (얼굴30, 전체100)</td></tr>
                    <tr><td className="px-3 py-1.5 text-violet-200 font-mono">--no [키워드]</td><td className="px-3 py-1.5 text-gray-400">제외 요소</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Anchor Image Workflow */}
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <p className="text-amber-300 text-xs font-bold mb-2">⭐ 앵커 이미지 사용법</p>
              <ol className="text-amber-200/80 text-xs space-y-1">
                <li>1. <span className="text-white">앵커 씬</span> 먼저 생성 (--cref 없는 프롬프트)</li>
                <li>2. 생성된 이미지 URL 복사 (우클릭 → 이미지 주소 복사)</li>
                <li>3. 파싱 탭의 <span className="text-white">--cref URL 입력란</span>에 붙여넣기</li>
                <li>4. 나머지 씬 프롬프트 복사 → 자동으로 --cref 적용됨</li>
              </ol>
            </div>
          </div>
        </ToolDetailCard>
      </ContentCard>

      {/* Video Tools Section */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-red-400">movie</span>
          영상 생성
        </h3>

        {/* Kling 3.0 */}
        <ToolDetailCard
          title="Kling 3.0"
          color="cyan"
          url="https://klingai.com"
          isOpen={openTool === "kling"}
          onToggle={() => toggleTool("kling")}
          badge="4K"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">실행 단계</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">1.</span>klingai.com 접속 → 로그인</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">2.</span>"AI Videos" → "Image to Video" 선택</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">3.</span>생성한 이미지 업로드</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">4.</span>파싱탭에서 복사한 Kling 프롬프트 붙여넣기</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">5.</span>Duration, Camera 설정 → Generate</li>
              </ol>
            </div>

            {/* Camera Options */}
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">카메라 옵션</p>
              <div className="overflow-hidden rounded-lg border border-cyan-500/20">
                <table className="w-full text-xs">
                  <thead className="bg-cyan-500/10">
                    <tr>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">옵션</th>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">설명</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cyan-500/10">
                    <tr><td className="px-3 py-1.5 text-cyan-200">Static</td><td className="px-3 py-1.5 text-gray-400">고정 (클로즈업에 적합)</td></tr>
                    <tr><td className="px-3 py-1.5 text-cyan-200">Dolly In/Out</td><td className="px-3 py-1.5 text-gray-400">줌인/줌아웃</td></tr>
                    <tr><td className="px-3 py-1.5 text-cyan-200">Pan Left/Right</td><td className="px-3 py-1.5 text-gray-400">좌우 패닝</td></tr>
                    <tr><td className="px-3 py-1.5 text-cyan-200">Tilt Up/Down</td><td className="px-3 py-1.5 text-gray-400">상하 틸트</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Motion Score */}
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">Motion Score 가이드</p>
              <div className="overflow-hidden rounded-lg border border-cyan-500/20">
                <table className="w-full text-xs">
                  <thead className="bg-cyan-500/10">
                    <tr>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">점수</th>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">용도</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cyan-500/10">
                    <tr><td className="px-3 py-1.5 text-cyan-200 font-bold">1-2</td><td className="px-3 py-1.5 text-gray-400">정적 (배경, 클로즈업)</td></tr>
                    <tr><td className="px-3 py-1.5 text-cyan-200 font-bold">3-4</td><td className="px-3 py-1.5 text-gray-400">약간 움직임 (대화, 표정)</td></tr>
                    <tr><td className="px-3 py-1.5 text-cyan-200 font-bold">5</td><td className="px-3 py-1.5 text-gray-400">활발한 움직임 (걷기, 액션)</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
              <p className="text-cyan-300 text-xs">💡 <span className="font-bold">팁:</span> 캐릭터 일관성이 가장 좋음. 무음이므로 CapCut에서 오디오 추가</p>
            </div>
          </div>
        </ToolDetailCard>

        {/* Veo 3.1 */}
        <ToolDetailCard
          title="Veo 3.1"
          color="red"
          url="https://labs.google/fx/tools/flow"
          isOpen={openTool === "veo"}
          onToggle={() => toggleTool("veo")}
          badge="오디오 포함"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">실행 단계 (Flow 권장)</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-red-400 font-bold">1.</span>labs.google/fx/tools/flow 접속</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">2.</span>Google 계정 로그인 (AI Pro 필요)</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">3.</span>파싱탭에서 복사한 Veo 프롬프트 붙여넣기</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">4.</span>Generate → 대사/효과음 자동 생성됨</li>
              </ol>
            </div>

            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">대안: AI Studio</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-red-400 font-bold">1.</span>aistudio.google.com 접속</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">2.</span>왼쪽 메뉴 → "Veo" 선택</li>
              </ol>
            </div>

            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">프롬프트 구조</p>
              <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 font-mono text-xs text-red-200">
                <p><span className="text-red-400">[Subject]</span> 주체 (누가)</p>
                <p><span className="text-red-400">[Action]</span> 동작 (무엇을)</p>
                <p><span className="text-red-400">[Setting]</span> 장소 (어디서)</p>
                <p><span className="text-red-400">[Style]</span> 스타일 (cinematic, etc)</p>
                <p><span className="text-red-400">[Camera]</span> 카메라 (close-up, etc)</p>
                <p><span className="text-red-400">[Lighting]</span> 조명 (dramatic, etc)</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-red-300 text-xs">💡 <span className="font-bold">팁:</span> 대사/효과음 필요한 씬에 적합. Flow는 AI 크레딧 소모</p>
            </div>
          </div>
        </ToolDetailCard>
      </ContentCard>

      {/* FAQ Section */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-yellow-400">help</span>
          자주 묻는 질문
        </h3>
        <div className="space-y-2">
          <FAQItem
            question="앵커 이미지란?"
            answer="첫 번째 씬(보통 Scene 1)에서 생성한 캐릭터 기준 이미지입니다. 이 이미지를 --cref로 참조하면 나머지 씬에서도 같은 캐릭터를 유지할 수 있습니다."
            isOpen={openFaq === "anchor"}
            onToggle={() => toggleFaq("anchor")}
          />
          <FAQItem
            question="--cref URL은 어디서 복사하나요?"
            answer="Midjourney 웹사이트: 생성된 이미지 우클릭 → '이미지 주소 복사'\nDiscord: 이미지 클릭 → '브라우저에서 열기' → 주소창 URL 복사\n\n복사한 URL을 파싱 탭의 '--cref URL' 입력란에 붙여넣으면 자동으로 모든 Midjourney 프롬프트에 적용됩니다."
            isOpen={openFaq === "cref"}
            onToggle={() => toggleFaq("cref")}
          />
          <FAQItem
            question="Kling vs Veo, 언제 뭘 쓰나요?"
            answer="• Kling: 캐릭터 일관성 중요할 때, 4K 고화질 필요할 때, 카메라 움직임 세밀 제어\n• Veo: 대사나 효과음이 필요한 씬, 빠른 프로토타입, Google 크레딧 있을 때\n\n💡 보통 Kling으로 영상 만들고, CapCut에서 오디오 추가하는 게 품질이 좋습니다."
            isOpen={openFaq === "klingvsveo"}
            onToggle={() => toggleFaq("klingvsveo")}
          />
          <FAQItem
            question="오디오는 어떻게 적용하나요?"
            answer="1. Veo: 자동으로 대사/효과음 생성됨\n2. Kling: 무음 → CapCut/Premiere에서 오디오 추가\n\n오디오 소스: ElevenLabs(TTS), Suno(음악), 또는 직접 녹음"
            isOpen={openFaq === "audio"}
            onToggle={() => toggleFaq("audio")}
          />
          <FAQItem
            question="영상은 어떻게 합치나요?"
            answer="1. CapCut (무료, 추천): 모바일/PC 모두 지원, 자동 자막\n2. Premiere Pro: 전문가용\n3. DaVinci Resolve: 무료, 컬러그레이딩 강력\n\n씬별로 생성한 클립들을 타임라인에 순서대로 배치하면 됩니다."
            isOpen={openFaq === "merge"}
            onToggle={() => toggleFaq("merge")}
          />
        </div>
      </ContentCard>

      {/* Subscription Info */}
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-purple-400">credit_card</span>
          구독 안내
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold text-purple-600 mb-1">Google AI Pro</p>
            <p className="text-xl font-black text-gray-900">₩14,500/월</p>
            <ul className="text-gray-600 text-xs mt-2 space-y-1">
              <li>✓ NanoBanana + Veo + Flow</li>
              <li>✓ AI 크레딧 1,000/월</li>
            </ul>
            <a
              href="https://one.google.com/ai"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-600 text-white text-xs font-bold hover:bg-purple-700 transition-colors"
            >
              구독하기
              <span className="material-symbols-outlined text-xs">open_in_new</span>
            </a>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold text-cyan-600 mb-1">Kling Pro</p>
            <p className="text-xl font-black text-gray-900">₩31,200/월</p>
            <ul className="text-gray-600 text-xs mt-2 space-y-1">
              <li>✓ 3,000cr (5초 ~60개)</li>
              <li>✓ 상업용 라이선스</li>
            </ul>
            <a
              href="https://app.klingai.com/global/membership/membership-plan"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-600 text-white text-xs font-bold hover:bg-cyan-700 transition-colors"
            >
              구독하기
              <span className="material-symbols-outlined text-xs">open_in_new</span>
            </a>
          </div>
        </div>
        <div className="mt-4 p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
          <p className="text-violet-300 text-xs">
            <span className="font-bold">Midjourney:</span> $10/월 Basic ~ $30/월 Standard (월 15~30시간)
            <a href="https://www.midjourney.com/account" target="_blank" rel="noopener noreferrer" className="ml-2 text-violet-400 underline">구독하기</a>
          </p>
        </div>
      </ContentCard>

      {/* Completion */}
      <div className="text-center py-6">
        <div className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 mb-4">
          <span className="material-symbols-outlined text-emerald-400">celebration</span>
          <span className="font-bold text-emerald-300 text-lg">워크플로우 완료!</span>
        </div>
        <p className="text-gray-500 text-sm mb-6">씬별로 이미지/영상을 생성한 후 CapCut에서 합치면 끝</p>
        <button
          onClick={() => setActiveTab("homework")}
          className="px-6 py-3 rounded-xl bg-white text-gray-900 font-bold hover:bg-gray-100 transition-all inline-flex items-center gap-2"
        >
          <span className="material-symbols-outlined">assignment</span>
          과제 확인하기
        </button>
      </div>
    </div>
  );
}

// ============ Tool Detail Card Component ============
function ToolDetailCard({
  title,
  color,
  url,
  badge,
  isOpen,
  onToggle,
  children,
}: {
  title: string;
  color: string;
  url: string;
  badge?: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  const colorClasses: Record<string, { bg: string; border: string; text: string; hoverBorder: string }> = {
    orange: { bg: "bg-orange-500/10", border: "border-orange-500/20", text: "text-orange-400", hoverBorder: "hover:border-orange-500/50" },
    violet: { bg: "bg-violet-500/10", border: "border-violet-500/20", text: "text-violet-400", hoverBorder: "hover:border-violet-500/50" },
    cyan: { bg: "bg-cyan-500/10", border: "border-cyan-500/20", text: "text-cyan-400", hoverBorder: "hover:border-cyan-500/50" },
    red: { bg: "bg-red-500/10", border: "border-red-500/20", text: "text-red-400", hoverBorder: "hover:border-red-500/50" },
  };
  const c = colorClasses[color] || colorClasses.violet;

  return (
    <div className={`rounded-xl border ${c.border} ${c.bg} mb-3 overflow-hidden transition-all ${c.hoverBorder}`}>
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <span className={`font-bold ${c.text}`}>{title}</span>
          {badge && (
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${c.bg} ${c.text} border ${c.border}`}>
              {badge}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-gray-900 hover:bg-gray-100 transition-colors flex items-center gap-1`}
          >
            열기
            <span className="material-symbols-outlined text-xs text-gray-500">open_in_new</span>
          </a>
          <span className={`material-symbols-outlined ${c.text} text-lg transition-transform ${isOpen ? 'rotate-180' : ''}`}>
            expand_more
          </span>
        </div>
      </button>
      {isOpen && (
        <div className="px-4 pb-4 pt-0 border-t border-white/5">
          {children}
        </div>
      )}
    </div>
  );
}

// ============ FAQ Item Component ============
function FAQItem({
  question,
  answer,
  isOpen,
  onToggle,
}: {
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="rounded-lg border border-white/10 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
      >
        <span className="text-white text-sm font-medium">{question}</span>
        <span className={`material-symbols-outlined text-gray-400 text-lg transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          expand_more
        </span>
      </button>
      {isOpen && (
        <div className="px-3 pb-3 pt-0">
          <p className="text-gray-400 text-xs whitespace-pre-line leading-relaxed">{answer}</p>
        </div>
      )}
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

function NextStepButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <div className="mt-8 pt-6 border-t border-white/10">
      <button
        onClick={onClick}
        className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-lg hover:from-purple-700 hover:to-indigo-700 transition-all flex items-center justify-center gap-3 shadow-[0_4px_20px_rgba(168,85,247,0.3)] group"
      >
        <span>다음 단계:</span>
        <span className="text-purple-200">{label}</span>
        <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
      </button>
    </div>
  );
}
