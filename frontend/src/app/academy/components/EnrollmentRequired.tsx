/**
 * EnrollmentRequired - 미등록 사용자 안내 컴포넌트
 * Academy 접근 권한이 없는 사용자에게 수강 신청 안내를 보여줍니다.
 */

import Link from "next/link";

export function EnrollmentRequired() {
  return (
    <>
      {/* Fonts - Academy 페이지와 동일 */}
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

      <div className="min-h-screen bg-[#050505] flex items-center justify-center p-8 font-sans">
        {/* Grid Background */}
        <div
          className="fixed inset-0 pointer-events-none opacity-20"
          style={{
            backgroundSize: '40px 40px',
            backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)',
          }}
        />

        <div className="relative max-w-lg w-full">
          {/* Glow Effect */}
          <div className="absolute -inset-1 bg-gradient-to-b from-purple-500/20 to-transparent opacity-30 blur-2xl rounded-[3rem]" />

          {/* Card */}
          <div className="relative bg-[#0f0f11] border border-white/10 rounded-[2.5rem] p-10 shadow-2xl text-center">
            {/* Badge */}
            <div className="inline-block px-4 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 mb-8">
              <span className="text-[10px] font-bold text-purple-400 tracking-[0.2em] font-mono uppercase">
                Members Only
              </span>
            </div>

            {/* Icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-purple-400">
                lock
              </span>
            </div>

            {/* Title */}
            <h1 className="text-3xl font-black mb-4 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-purple-400 glow-text">
              수강생 전용 페이지
            </h1>

            {/* Description */}
            <p className="text-gray-400 text-lg leading-relaxed font-light mb-8">
              AI Academy 콘텐츠를 이용하시려면<br />
              수강 신청 및 결제가 필요합니다.
            </p>

            {/* CTA Button - Academy 흰색 버튼 스타일 */}
            <Link
              href="/crebit"
              className="inline-flex items-center gap-3 px-8 py-4 bg-white text-gray-900 font-bold rounded-2xl hover:bg-gray-100 transition-all shadow-lg shadow-white/10 group"
            >
              <span className="material-symbols-outlined text-xl text-gray-700 group-hover:translate-x-1 transition-transform">
                arrow_forward
              </span>
              수강 신청하기
            </Link>

            {/* Help text */}
            <p className="text-sm text-gray-500 mt-8">
              이미 결제하셨나요?{" "}
              <a
                href="mailto:support@crebit.studio"
                className="text-purple-400 hover:text-purple-300 hover:underline transition-colors"
              >
                문의하기
              </a>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
