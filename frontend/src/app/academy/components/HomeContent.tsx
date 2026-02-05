"use client";

import { TOOL_LINKS, type TabKey } from "../constants";

interface HomeContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function HomeContent({ setActiveTab }: HomeContentProps) {
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
