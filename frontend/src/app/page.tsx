"use client";

/**
 * Root Landing Page (/)
 * - 비로그인: 현대적 랜딩 페이지 (서비스 소개 + 로그인 + 수강신청)
 * - 로그인 + 접근권한: /academy 리다이렉트
 * - 로그인 + 권한없음: 랜딩 + 결제 CTA
 */

import { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { api, type AcademyAccessResponse } from "@/lib/api";

export default function RootPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <RootContent />
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

function RootContent() {
  const router = useRouter();
  const [state, setState] = useState<{
    loading: boolean;
    isLoggedIn: boolean;
    hasAccess: boolean;
  }>({ loading: true, isLoggedIn: false, hasAccess: false });

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const response: AcademyAccessResponse = await api.checkAcademyAccess();
        if (!cancelled) {
          if (response.can_access) {
            router.replace("/academy");
            return;
          }
          setState({ loading: false, isLoggedIn: true, hasAccess: false });
        }
      } catch (err) {
        const status = (err as { status?: number })?.status;
        if (!cancelled) {
          if (status === 403) {
            // Logged in but not enrolled
            setState({ loading: false, isLoggedIn: true, hasAccess: false });
          } else {
            // Not logged in
            setState({ loading: false, isLoggedIn: false, hasAccess: false });
          }
        }
      }
    }

    check();
    return () => { cancelled = true; };
  }, [router]);

  if (state.loading) {
    return <LoadingScreen />;
  }

  return <LandingPage isLoggedIn={state.isLoggedIn} />;
}

/* ──────────────── Landing Page ──────────────── */

function LandingPage({ isLoggedIn }: { isLoggedIn: boolean }) {
  return (
    <>
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />

      <style jsx global>{`
        .material-symbols-outlined {
          font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
      `}</style>

      <div className="min-h-screen bg-[#050505] text-white font-sans antialiased selection:bg-purple-500 selection:text-white">
        {/* Grid Background */}
        <div
          className="fixed inset-0 pointer-events-none opacity-20"
          style={{
            backgroundSize: "40px 40px",
            backgroundImage:
              "linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)",
          }}
        />

        {/* Nav */}
        <nav className="relative z-10 flex items-center justify-between px-8 py-5">
          <div className="flex items-center gap-3">
            <img src="/favicon.png" alt="Crebit" className="w-9 h-9 rounded-full border-2 border-white/20" />
            <span className="text-sm font-bold tracking-widest font-mono text-white/90">
              AI <span className="opacity-50 font-normal">ACADEMY</span>
            </span>
          </div>
          {!isLoggedIn && (
            <a
              href="/api/v1/auth/google/start"
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-gray-900 text-sm font-bold hover:bg-gray-100 transition-all shadow-lg shadow-white/10"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              로그인
            </a>
          )}
          {isLoggedIn && (
            <a
              href="/academy"
              className="px-5 py-2.5 rounded-full bg-purple-500 text-white text-sm font-bold hover:bg-purple-600 transition-all"
            >
              아카데미 입장
            </a>
          )}
        </nav>

        {/* Hero Section */}
        <section className="relative z-10 max-w-4xl mx-auto px-8 pt-16 pb-20 text-center">
          <div className="inline-block px-4 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 mb-8">
            <span className="text-[10px] font-bold text-purple-400 tracking-[0.2em] font-mono uppercase">
              1기 모집 중
            </span>
          </div>

          <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-tight mb-6">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-purple-400">
              AI 영상 워크플로우
            </span>
            <br />
            <span className="text-white/80">아카데미</span>
          </h1>

          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mb-10">
            씬 감지부터 AI 프롬프트 생성, 이미지 & 영상 제작까지.
            <br className="hidden md:block" />
            프로 크리에이터의 영상 워크플로우를 단계별로 배워보세요.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {!isLoggedIn ? (
              <a
                href="/api/v1/auth/google/start"
                className="inline-flex items-center gap-3 px-8 py-4 bg-white text-gray-900 font-bold rounded-2xl hover:bg-gray-100 transition-all shadow-lg shadow-white/10 group"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Google 로그인으로 시작하기
              </a>
            ) : (
              <a
                href="https://cafe.naver.com/antacademy1/5150"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-bold rounded-2xl hover:from-purple-600 hover:to-indigo-600 transition-all shadow-lg shadow-purple-500/20"
              >
                <span className="material-symbols-outlined text-xl">arrow_forward</span>
                수강 신청하기
              </a>
            )}
            <a
              href="https://cafe.naver.com/antacademy1/5150"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-4 text-gray-400 font-medium rounded-2xl hover:text-white hover:bg-white/5 transition-all"
            >
              자세히 알아보기
              <span className="material-symbols-outlined text-base">open_in_new</span>
            </a>
          </div>
        </section>

        {/* Features Section */}
        <section className="relative z-10 max-w-5xl mx-auto px-8 pb-20">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon="movie_filter"
              title="AI 씬 감지"
              description="영상을 업로드하면 AI가 자동으로 씬 전환 포인트를 감지합니다. 정밀/표준 모드 지원."
            />
            <FeatureCard
              icon="auto_awesome"
              title="프롬프트 생성"
              description="감지된 씬별로 MidJourney, Kling, Veo 등 AI 도구용 프롬프트를 자동 생성합니다."
            />
            <FeatureCard
              icon="build"
              title="도구 통합"
              description="NanoBanana, MidJourney V7, Kling, Veo 등 외부 AI 도구와 원클릭 연동."
            />
          </div>
        </section>

        {/* Workflow Section */}
        <section className="relative z-10 max-w-4xl mx-auto px-8 pb-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-3">워크플로우 4단계</h2>
            <p className="text-gray-500">영상 분석부터 최종 편집까지, 체계적으로 배웁니다.</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { step: "01", label: "ANALYZE", desc: "영상 분석 + 씬 감지" },
              { step: "02", label: "IMAGE", desc: "이미지 프롬프트 생성" },
              { step: "03", label: "VIDEO", desc: "모션 프롬프트 생성" },
              { step: "04", label: "ASSEMBLY", desc: "최종 편집 + 내보내기" },
            ].map((s) => (
              <div key={s.step} className="p-5 rounded-2xl bg-white/[0.02] border border-white/5 text-center hover:border-purple-500/30 transition-all">
                <div className="text-xs font-mono text-purple-400 mb-2">{s.step}</div>
                <div className="text-sm font-bold text-white mb-1">{s.label}</div>
                <div className="text-xs text-gray-500">{s.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="relative z-10 max-w-3xl mx-auto px-8 pb-24 text-center">
          <div className="p-10 rounded-3xl bg-gradient-to-b from-purple-500/10 to-transparent border border-purple-500/20">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">지금 시작하세요</h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              AI 영상 제작의 모든 것을 배울 수 있는 기회.
              {!isLoggedIn && " Google 계정으로 간편하게 시작하세요."}
            </p>
            {!isLoggedIn ? (
              <a
                href="/api/v1/auth/google/start"
                className="inline-flex items-center gap-3 px-8 py-4 bg-white text-gray-900 font-bold rounded-2xl hover:bg-gray-100 transition-all shadow-lg shadow-white/10"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Google 로그인
              </a>
            ) : (
              <a
                href="https://cafe.naver.com/antacademy1/5150"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-bold rounded-2xl hover:from-purple-600 hover:to-indigo-600 transition-all shadow-lg shadow-purple-500/20"
              >
                <span className="material-symbols-outlined text-xl">arrow_forward</span>
                수강 신청하기
              </a>
            )}
          </div>

          <p className="text-sm text-gray-500 mt-6">
            이미 결제하셨나요?{" "}
            <a href="mailto:ted.taeeun.kim@gmail.com" className="text-purple-400 hover:text-purple-300 hover:underline transition-colors">
              문의하기
            </a>
          </p>
        </section>

        {/* Footer */}
        <footer className="relative z-10 border-t border-white/5 py-8 px-8 text-center">
          <p className="text-xs text-gray-600">&copy; 2026 Crebit Studio. All rights reserved.</p>
        </footer>
      </div>
    </>
  );
}

function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-purple-500/30 transition-all group">
      <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4 group-hover:bg-purple-500/20 transition-all">
        <span className="material-symbols-outlined text-2xl text-purple-400">{icon}</span>
      </div>
      <h3 className="text-base font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 leading-relaxed">{description}</p>
    </div>
  );
}
