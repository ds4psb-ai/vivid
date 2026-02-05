/**
 * EnrollmentRequired - 미등록 사용자 안내 컴포넌트
 * Academy 접근 권한이 없는 사용자에게 수강 신청 안내를 보여줍니다.
 */


interface EnrollmentRequiredProps {
  isLoggedIn?: boolean;
}

export function EnrollmentRequired({ isLoggedIn = false }: EnrollmentRequiredProps) {
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

            {/* Login Button - only show if not logged in */}
            {!isLoggedIn && (
              <>
                <a
                  href="/api/v1/auth/google/start"
                  className="inline-flex items-center gap-3 px-8 py-4 bg-white text-gray-900 font-bold rounded-2xl hover:bg-gray-100 transition-all shadow-lg shadow-white/10 group mb-4"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Google 로그인
                </a>

                {/* Divider */}
                <div className="flex items-center gap-4 my-6">
                  <div className="flex-1 h-px bg-white/10"></div>
                  <span className="text-xs text-gray-500">또는</span>
                  <div className="flex-1 h-px bg-white/10"></div>
                </div>
              </>
            )}

            {/* CTA Button - 수강 신청 */}
            <a
              href="https://cafe.naver.com/antacademy1/5150"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-3 px-8 py-4 bg-purple-500/20 text-purple-300 font-bold rounded-2xl hover:bg-purple-500/30 transition-all border border-purple-500/30 group"
            >
              <span className="material-symbols-outlined text-xl group-hover:translate-x-1 transition-transform">
                arrow_forward
              </span>
              수강 신청하기
            </a>

            {/* Help text */}
            <p className="text-sm text-gray-500 mt-8">
              이미 결제하셨나요?{" "}
              <a
                href="mailto:ted.taeeun.kim@gmail.com"
                className="text-purple-400 hover:text-purple-300 hover:underline transition-colors"
              >
                문의하기
              </a>
            </p>
            <p className="text-xs text-gray-600 mt-2">
              (수강하신 분은 단톡방 공지에 댓글로 구글 메일 주소 적어주세요)
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
