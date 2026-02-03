"use client";

/**
 * 아카데미 가이드 페이지
 *
 * VIVID AI 영상 자동화 워크샵 - 성수페이지 아카데미
 * prompty.co.kr/academy
 */

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Settings,
  Film,
  Search,
  Sparkles,
  Palette,
  Image as ImageIcon,
  Video,
  ClipboardList,
  CheckCircle2,
  Copy,
  ExternalLink,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

type TabKey = "home" | "setup" | "anchor" | "builder1" | "vibe" | "builder2" | "image" | "video" | "homework";

const TABS: { key: TabKey; label: string; icon: React.ReactNode; color: string }[] = [
  { key: "home", label: "홈", icon: <Sparkles className="w-4 h-4" />, color: "violet" },
  { key: "setup", label: "환경 설정", icon: <Settings className="w-4 h-4" />, color: "emerald" },
  { key: "anchor", label: "기준 프레임", icon: <Film className="w-4 h-4" />, color: "cyan" },
  { key: "builder1", label: "Builder 1", icon: <Search className="w-4 h-4" />, color: "blue" },
  { key: "vibe", label: "바이브 철학관", icon: <Sparkles className="w-4 h-4" />, color: "purple" },
  { key: "builder2", label: "Builder 2", icon: <Palette className="w-4 h-4" />, color: "pink" },
  { key: "image", label: "이미지 생성", icon: <ImageIcon className="w-4 h-4" />, color: "orange" },
  { key: "video", label: "영상 생성", icon: <Video className="w-4 h-4" />, color: "red" },
  { key: "homework", label: "과제", icon: <ClipboardList className="w-4 h-4" />, color: "green" },
];

export default function AcademyPage() {
  return (
    <Suspense
      fallback={<div className="min-h-screen bg-[#0F0F1A] flex items-center justify-center text-white">Loading...</div>}
    >
      <AcademyContent />
    </Suspense>
  );
}

function AcademyContent() {
  const searchParams = useSearchParams();
  const urlTab = searchParams.get("tab") as TabKey | null;
  const [manualTab, setManualTab] = useState<TabKey | null>(null);
  const activeTab = manualTab ?? urlTab ?? "home";

  return (
    <div className="min-h-screen bg-[#0F0F1A] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#0F0F1A]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm hidden sm:inline">홈으로</span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              VIVID
            </span>
            <span className="text-slate-500">×</span>
            <span className="text-white font-medium">성수페이지 아카데미</span>
          </div>
          <div className="w-16" /> {/* Spacer for centering */}
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <nav className="lg:w-56 shrink-0">
          <div className="lg:sticky lg:top-24 space-y-1">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setManualTab(tab.key)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? `bg-${tab.color}-500/20 text-${tab.color}-400 border border-${tab.color}-500/30`
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
                style={
                  activeTab === tab.key
                    ? {
                        backgroundColor: `var(--${tab.color}-500-20, rgba(139, 92, 246, 0.2))`,
                        borderColor: `var(--${tab.color}-500-30, rgba(139, 92, 246, 0.3))`,
                      }
                    : undefined
                }
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === "home" && <HomeContent />}
            {activeTab === "setup" && <SetupContent />}
            {activeTab === "anchor" && <AnchorContent />}
            {activeTab === "builder1" && <Builder1Content />}
            {activeTab === "vibe" && <VibeContent />}
            {activeTab === "builder2" && <Builder2Content />}
            {activeTab === "image" && <ImageGenContent />}
            {activeTab === "video" && <VideoGenContent />}
            {activeTab === "homework" && <HomeworkContent />}
          </motion.div>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-500">
        <p>© 2026 VIVID × 성수페이지 아카데미</p>
        <p className="mt-2">AI 영상 자동화 워크샵 · 1강</p>
      </footer>
    </div>
  );
}

// ============ Content Components ============

function HomeContent() {
  return (
    <div className="space-y-8">
      <div className="text-center py-8">
        <h1 className="text-3xl sm:text-4xl font-bold mb-4">
          <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI 영상 자동화 워크샵
          </span>
        </h1>
        <p className="text-slate-400 text-lg">내 영상을 AI로 재탄생시키는 완전 가이드</p>
      </div>

      {/* Flow Diagram */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/5 border border-violet-500/20">
        <h3 className="text-sm font-medium text-violet-400 mb-4">전체 흐름</h3>
        <div className="flex flex-col items-center gap-2 text-sm">
          <FlowStep emoji="📹" text="내 영상" />
          <FlowArrow />
          <FlowStep emoji="🔍" text="Builder 1 (영상 분석기)" />
          <FlowArrow />
          <div className="flex items-center gap-4">
            <FlowStep emoji="🎭" text="Builder 2 (변주 엔진)" />
            <span className="text-slate-500">←</span>
            <FlowStep emoji="🔮" text="나의 프로필 (선택)" subtle />
          </div>
          <FlowArrow />
          <FlowStep emoji="🖼️" text="이미지 생성" />
          <FlowArrow />
          <FlowStep emoji="🎬" text="영상 생성" />
          <FlowArrow />
          <FlowStep emoji="✨" text="나만의 영상 완성!" highlight />
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "환경 설정", emoji: "⚙️", color: "emerald" },
          { label: "Builder 1", emoji: "🔍", color: "blue" },
          { label: "Builder 2", emoji: "🎭", color: "pink" },
          { label: "과제 확인", emoji: "📝", color: "green" },
        ].map((item) => (
          <div
            key={item.label}
            className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors cursor-pointer text-center"
          >
            <div className="text-2xl mb-2">{item.emoji}</div>
            <div className="text-sm text-slate-300">{item.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SetupContent() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="환경 설정"
        subtitle="시작하기 전에 필요한 것들을 준비해요"
        color="emerald"
      />

      {/* AI Studio */}
      <ContentCard title="Google AI Studio 접속" step={1} color="emerald">
        <p className="text-slate-400 mb-4">모든 도구는 AI Studio에서 실행됩니다</p>
        <Checklist
          items={[
            { text: "브라우저에서 aistudio.google.com 접속", link: "https://aistudio.google.com" },
            { text: "Google 계정으로 로그인" },
          ]}
        />
      </ContentCard>

      {/* Canvas App */}
      <ContentCard title="캔버스 앱 사용법" step={2} color="emerald">
        <Checklist
          items={[
            { text: '좌측 패널 → "+ 새 앱" 클릭' },
            { text: '"Canvas App" 선택' },
            { text: "ZIP 파일 업로드" },
          ]}
        />
        <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left py-2">ZIP 파일</th>
                <th className="text-left py-2">용도</th>
              </tr>
            </thead>
            <tbody className="text-slate-300">
              <tr><td className="py-1.5"><code className="text-emerald-400">builder1-hardened.zip</code></td><td>영상 분석기</td></tr>
              <tr><td className="py-1.5"><code className="text-emerald-400">builder2-hardened.zip</code></td><td>변주 엔진</td></tr>
              <tr><td className="py-1.5"><code className="text-emerald-400">vibe-philosophy.zip</code></td><td>바이브 철학관</td></tr>
            </tbody>
          </table>
        </div>
        <Callout type="warning" className="mt-4">
          ZIP 파일은 최대 10개 파일, 100MB 이하여야 해요
        </Callout>
      </ContentCard>

      {/* FFmpeg */}
      <ContentCard title="FFmpeg 설치" step={3} color="emerald">
        <p className="text-slate-400 mb-4">영상에서 기준 프레임을 추출할 때 필요해요</p>

        <h4 className="text-sm font-medium text-white mb-2">macOS 사용자</h4>
        <CodeBlock
          code={`# 1. Homebrew 업데이트
brew update

# 2. FFmpeg 설치
brew install ffmpeg

# 3. 설치 확인
ffmpeg -version`}
        />

        <Callout type="tip" className="mt-4">
          Homebrew가 없다면 brew.sh에서 먼저 설치하세요
        </Callout>

        <Collapsible title="Windows 사용자" className="mt-6">
          <Checklist
            items={[
              { text: "ffmpeg.org/download.html 접속", link: "https://ffmpeg.org/download.html" },
              { text: "Windows 빌드 다운로드 & 압축 해제" },
              { text: "환경변수 PATH에 ffmpeg/bin 폴더 추가" },
            ]}
          />
        </Collapsible>
      </ContentCard>
    </div>
  );
}

function AnchorContent() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="기준 프레임 추출"
        subtitle="기준 프레임 (ANCHOR) = 모든 이미지 생성의 기준점"
        color="cyan"
      />

      <ContentCard title="왜 필요한가요?" color="cyan">
        <p className="text-slate-300 mb-4">
          AI가 영상 속 캐릭터를 일관되게 그리려면 <strong className="text-white">&quot;이 사람이야!&quot;</strong> 하고 알려줄 기준 이미지가 필요해요.
        </p>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
            <div className="text-2xl mb-2">😵</div>
            <p className="text-red-300">기준 프레임 없이</p>
            <p className="text-red-400/70 text-xs mt-1">매번 다른 얼굴</p>
          </div>
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
            <div className="text-2xl mb-2">😊</div>
            <p className="text-emerald-300">기준 프레임 사용</p>
            <p className="text-emerald-400/70 text-xs mt-1">같은 캐릭터 유지</p>
          </div>
        </div>
      </ContentCard>

      <ContentCard title="기준 프레임 추출하기" step={1} color="cyan">
        <h4 className="text-sm font-medium text-white mb-2">첫 번째 프레임 추출</h4>
        <CodeBlock code={`ffmpeg -i 내영상.mp4 -vf "select=eq(n\\,0)" -vframes 1 기준프레임.png`} />
        <p className="text-xs text-slate-500 mt-2">영상의 맨 첫 장면을 이미지로 저장해요</p>

        <h4 className="text-sm font-medium text-white mt-6 mb-2">특정 시간대 추출 (예: 2.5초 지점)</h4>
        <CodeBlock code={`ffmpeg -i 내영상.mp4 -ss 00:00:02.500 -vframes 1 기준프레임.png`} />
        <Callout type="tip" className="mt-3">
          얼굴이 가장 잘 보이는 장면을 찾아 그 시간대를 입력하세요
        </Callout>
      </ContentCard>

      <ContentCard title="좋은 기준 프레임 vs 나쁜 기준 프레임" color="cyan">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left py-2 text-emerald-400">✅ 좋은 기준 프레임</th>
                <th className="text-left py-2 text-red-400">❌ 피해야 할 기준 프레임</th>
              </tr>
            </thead>
            <tbody className="text-slate-300">
              <tr><td className="py-1.5">얼굴이 정면 또는 3/4 각도</td><td>뒷모습, 옆모습만 보임</td></tr>
              <tr><td className="py-1.5">조명이 균일함</td><td>역광, 극단적 명암</td></tr>
              <tr><td className="py-1.5">표정이 자연스러움</td><td>과격한 표정</td></tr>
              <tr><td className="py-1.5">해상도가 선명함</td><td>모션 블러, 흔들림</td></tr>
            </tbody>
          </table>
        </div>
      </ContentCard>
    </div>
  );
}

function Builder1Content() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Builder 1: 영상 분석기"
        subtitle="영상 넣으면 → 이미지용 명령어 나옴"
        color="blue"
      />

      <ContentCard title="Builder 1이란?" color="blue">
        <div className="flex flex-col items-center gap-2 text-sm py-4">
          <FlowStep emoji="📹" text="내 영상" />
          <FlowArrow />
          <FlowStep emoji="🔍" text="Builder 1이 분석" />
          <FlowArrow />
          <FlowStep emoji="📝" text="이미지 생성용 프롬프트" />
        </div>
        <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
          <p className="text-sm text-slate-400 mb-2">출력 형식 선택 가능:</p>
          <ul className="text-sm text-slate-300 space-y-1">
            <li>• <strong>NanoBanana Pro</strong>: 한글 프롬프트 (기본)</li>
            <li>• <strong>Midjourney V7</strong>: 영문 프롬프트 (선택)</li>
          </ul>
        </div>
      </ContentCard>

      <ContentCard title="4단계 워크플로우" color="blue">
        {[
          { step: 1, title: "영상 분석 📊", items: ["씬 테이블", "캐릭터 프로필", "시각 대비", "구도 분석"] },
          { step: 2, title: "1막 프롬프트 (과거) 🌅", desc: "따뜻한 색감, 부드러운 조명, 빈티지 효과" },
          { step: 3, title: "2막 프롬프트 (현재) 🌆", desc: "선명한 색감, 깔끔한 조명, 고해상도" },
          { step: 4, title: "원본 파일 다운로드 📥", desc: "마크다운 파일로 저장 → Builder 2에 입력으로 사용!" },
        ].map((s) => (
          <div key={s.step} className="mb-4 last:mb-0">
            <div className="flex items-center gap-3 mb-2">
              <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center">
                {s.step}
              </span>
              <h4 className="text-white font-medium">{s.title}</h4>
            </div>
            {s.items && (
              <div className="ml-9 flex flex-wrap gap-2">
                {s.items.map((item) => (
                  <span key={item} className="px-2 py-1 rounded-md bg-white/5 text-xs text-slate-400">{item}</span>
                ))}
              </div>
            )}
            {s.desc && <p className="ml-9 text-sm text-slate-400">{s.desc}</p>}
          </div>
        ))}
      </ContentCard>

      <ContentCard title="출력 예시" color="blue">
        <CodeBlock
          language="markdown"
          code={`## 📊 영상 분석 요약

### 씬 테이블
| Scene | 시간대 | 설명 | 기준 |
|-------|--------|------|------|
| 01 | 00:00~00:01 | 거실에서 케이크 들고 있는 엄마 | ⭐ 기준 프레임 |
| 02 | 00:01~00:02 | 7살 소년의 생일파티 | |

### 시각 대비 (Visual Rhyme)
| 1막 (과거) | 2막 (현재) |
|-----------|-----------|
| 따뜻한 텅스텐 조명 | 차가운 형광등 |
| 세피아 톤 | 뉴트럴 톤 |`}
        />
      </ContentCard>
    </div>
  );
}

function VibeContent() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="바이브 철학관"
        subtitle="AI와 대화하며 나의 프로필을 만들어요"
        color="purple"
      />

      <ContentCard title="바이브 철학관이란?" color="purple">
        <div className="flex flex-col items-center gap-2 text-sm py-4">
          <FlowStep emoji="💬" text="AI와 대화" />
          <FlowArrow />
          <FlowStep emoji="🔍" text="심층 분석 진행" />
          <FlowArrow />
          <FlowStep emoji="💾" text="나의 프로필 (JSON) 저장" />
        </div>
        <Callout type="tip" className="mt-4">
          저장한 프로필은 Builder 2에서 사용해요 → 나의 감성이 담긴 변주 영상을 만들 수 있어요
        </Callout>
      </ContentCard>

      <ContentCard title="분석 깊이 시스템" color="purple">
        <p className="text-slate-400 mb-4">대화가 진행될수록 분석이 깊어져요</p>
        <div className="space-y-2">
          {[
            { emoji: "🌱", name: "탐색", range: "0~25%", desc: "라포 형성, 기본 정보" },
            { emoji: "🌿", name: "전개", range: "26~45%", desc: "표면적 고민 확인" },
            { emoji: "🌲", name: "잠재의식", range: "46~65%", desc: "반응 패턴 분석" },
            { emoji: "🌳", name: "무의식", range: "66~85%", desc: "그림자, 억압된 욕구" },
            { emoji: "🌴", name: "원형", range: "86~95%", desc: "원형 통합" },
            { emoji: "🏔️", name: "합성", range: "96~100%", desc: "최종 솔루션" },
          ].map((stage, i) => (
            <div key={stage.name} className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5">
              <span className="text-lg">{stage.emoji}</span>
              <span className="text-white font-medium w-16">{stage.name}</span>
              <span className="text-purple-400 text-sm w-20">{stage.range}</span>
              <span className="text-slate-400 text-sm">{stage.desc}</span>
            </div>
          ))}
        </div>
        <Callout type="tip" className="mt-4">
          50% 이상 도달하면 &quot;프로필 저장&quot; 버튼이 활성화돼요
        </Callout>
      </ContentCard>

      <ContentCard title="프로필 예시" color="purple">
        <CodeBlock
          language="json"
          code={`{
  "분석깊이": 78,
  "현재단계": "무의식",
  "감정키워드": ["그리움", "후회"],
  "주제키워드": ["가족", "어린시절"],
  "깊은신호": ["인정욕구", "분리불안"],
  "원형": "영원한 소년 (Puer Aeternus)",
  "애착유형": "불안-회피형"
}`}
        />
      </ContentCard>
    </div>
  );
}

function Builder2Content() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Builder 2: 변주 엔진"
        subtitle="분석 결과 + 나의 프로필 → 오마주/변주 생성"
        color="pink"
      />

      <ContentCard title="오마주 vs 변주" color="pink">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <h4 className="text-blue-400 font-medium mb-2">🎬 오마주</h4>
            <p className="text-sm text-slate-300 mb-2">원본 존중</p>
            <p className="text-xs text-slate-400">구도/분위기 유지, 캐릭터만 교체</p>
            <p className="text-xs text-slate-500 mt-2">예: 생일 케이크 씬 → 내 어린시절로</p>
          </div>
          <div className="p-4 rounded-xl bg-pink-500/10 border border-pink-500/20">
            <h4 className="text-pink-400 font-medium mb-2">🎭 변주</h4>
            <p className="text-sm text-slate-300 mb-2">창의적 변형</p>
            <p className="text-xs text-slate-400">구도 유지, 상황/맥락 변형</p>
            <p className="text-xs text-slate-500 mt-2">예: 생일 케이크 → 퇴직 케이크</p>
          </div>
        </div>
      </ContentCard>

      <ContentCard title="입력 데이터" color="pink">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-white mb-2">필수</h4>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>📹 원본 영상</li>
              <li>📝 Builder 1 출력 (마크다운)</li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-medium text-white mb-2">선택</h4>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>🔮 나의 프로필 (JSON)</li>
              <li>💬 베스트 댓글 (최대 5개)</li>
            </ul>
          </div>
        </div>
        <Callout type="tip" className="mt-4">
          나의 프로필을 넣으면 나의 감성이 반영된 변주가 생성돼요
        </Callout>
      </ContentCard>

      <ContentCard title="4단계 워크플로우" color="pink">
        {[
          { step: 1, title: "재현성 검증 ✅", desc: "Builder 1 출력이 영상과 일치하는지 확인" },
          { step: 2, title: "오마주 프롬프트 생성 🎬", desc: "원본을 존중하는 이미지 프롬프트" },
          { step: 3, title: "변주 프롬프트 생성 🎭", desc: "나의 프로필을 반영한 창의적 변형" },
          { step: 4, title: "원본 파일 다운로드 📥", desc: "이미지/영상 생성에 바로 사용 가능!" },
        ].map((s) => (
          <div key={s.step} className="mb-4 last:mb-0">
            <div className="flex items-center gap-3 mb-1">
              <span className="w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-xs font-bold flex items-center justify-center">
                {s.step}
              </span>
              <h4 className="text-white font-medium">{s.title}</h4>
            </div>
            <p className="ml-9 text-sm text-slate-400">{s.desc}</p>
          </div>
        ))}
      </ContentCard>
    </div>
  );
}

function ImageGenContent() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="이미지 생성 도구"
        subtitle="Builder 프롬프트 → 이미지 생성"
        color="orange"
      />

      <ContentCard title="도구 비교" color="orange">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left py-2">도구</th>
                <th className="text-left py-2">언어</th>
                <th className="text-left py-2">강점</th>
                <th className="text-left py-2">추천</th>
              </tr>
            </thead>
            <tbody className="text-slate-300">
              <tr>
                <td className="py-2 font-medium text-orange-400">NanoBanana Pro</td>
                <td>한글</td>
                <td>빠른 속도, 캐릭터 일관성</td>
                <td>입문자</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-violet-400">Midjourney V7</td>
                <td>영문</td>
                <td>예술적 스타일</td>
                <td>고품질</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ContentCard>

      <ContentCard title="NanoBanana Pro (추천)" color="orange">
        <div className="flex items-center gap-2 mb-4">
          <span className="px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium">🇰🇷 한글 지원</span>
          <span className="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs font-medium">4K 출력</span>
          <span className="px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs font-medium">3~8초</span>
        </div>
        <Checklist
          items={[
            { text: "레퍼런스 이미지 업로드 (기준 프레임)" },
            { text: "Builder 프롬프트 붙여넣기" },
            { text: "Generate 클릭" },
            { text: "4K 이미지 다운로드" },
          ]}
        />
        <LinkButton href="https://nanobanana-pro.com" className="mt-4">
          NanoBanana Pro 접속
        </LinkButton>
      </ContentCard>

      <ContentCard title="Midjourney V7" color="violet">
        <p className="text-slate-400 mb-4">예술적 표현, 스타일 커스터마이징 강점</p>
        <h4 className="text-sm font-medium text-white mb-2">핵심 파라미터</h4>
        <CodeBlock
          code={`--v 7         # 버전 7
--ar 9:16     # 세로 영상 비율
--iw 2.0      # 이미지 가중치
--cref [URL]  # 캐릭터 레퍼런스
--stylize 250 # 1막 (과거) - 따뜻하게
--stylize 400 # 2막 (현재) - 선명하게`}
        />
      </ContentCard>
    </div>
  );
}

function VideoGenContent() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="영상 생성 도구"
        subtitle="이미지 + 프롬프트 → 영상 생성"
        color="red"
      />

      <ContentCard title="도구 비교" color="red">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left py-2">도구</th>
                <th className="text-left py-2">강점</th>
                <th className="text-left py-2">특징</th>
              </tr>
            </thead>
            <tbody className="text-slate-300">
              <tr>
                <td className="py-2 font-medium text-red-400">Veo 3.1</td>
                <td>오디오 자동 생성</td>
                <td>Google, 실사 물리 시뮬레이션</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-cyan-400">Kling AI</td>
                <td>캐릭터 일관성</td>
                <td>멀티 이미지 레퍼런스 (최대 4장)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ContentCard>

      <ContentCard title="Veo 3.1 (Google)" color="red">
        <div className="flex items-center gap-2 mb-4">
          <span className="px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs font-medium">1080p/4K</span>
          <span className="px-2 py-1 rounded-full bg-orange-500/20 text-orange-400 text-xs font-medium">오디오 자동</span>
        </div>
        <Checklist
          items={[
            { text: 'Gemini 앱 접속 → "Flow" 메뉴', link: "https://gemini.google.com" },
            { text: "기준 프레임 이미지 업로드" },
            { text: "Builder 프롬프트 입력" },
            { text: "비율 선택 (9:16 세로 / 16:9 가로)" },
            { text: "Generate → 영상 다운로드" },
          ]}
        />
      </ContentCard>

      <ContentCard title="Kling AI" color="cyan">
        <div className="flex items-center gap-2 mb-4">
          <span className="px-2 py-1 rounded-full bg-cyan-500/20 text-cyan-400 text-xs font-medium">최대 4장 레퍼런스</span>
          <span className="px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium">캐릭터 일관성 최고</span>
        </div>
        <Checklist
          items={[
            { text: "klingai.com 접속 & 로그인", link: "https://klingai.com" },
            { text: '"Image to Video" 선택' },
            { text: "기준 프레임 + 추가 참조 이미지 업로드" },
            { text: "Builder 프롬프트 입력" },
            { text: "Generate → 영상 다운로드" },
          ]}
        />
      </ContentCard>

      <ContentCard title="도구 선택 가이드" color="slate">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
            <span className="text-slate-300">오디오(배경음, 대사)까지 필요</span>
            <span className="text-red-400 font-medium">Veo 3.1</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
            <span className="text-slate-300">캐릭터 일관성이 중요</span>
            <span className="text-cyan-400 font-medium">Kling AI</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
            <span className="text-slate-300">빠른 테스트</span>
            <span className="text-red-400 font-medium">Veo 3.1</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
            <span className="text-slate-300">최고 품질</span>
            <span className="text-cyan-400 font-medium">Kling AI</span>
          </div>
        </div>
      </ContentCard>
    </div>
  );
}

function HomeworkContent() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="과제 안내"
        subtitle="📅 2강 예정: 2026년 2월 6일 (목)"
        color="green"
      />

      <ContentCard title="필수 과제 1: Builder 1 완료" color="green">
        <Checklist
          items={[
            { text: "본인이 선정한 바이럴 영상 준비" },
            { text: "Builder 1로 영상 분석" },
            { text: "원본 파일 (마크다운) 저장" },
          ]}
        />
        <Callout type="tip" className="mt-4">
          감정적인 스토리가 있는 영상을 선택하면 좋아요 (가족 이야기, 성장 스토리, 감동 광고)
        </Callout>
      </ContentCard>

      <ContentCard title="필수 과제 2: 바이브 철학관 세션" color="green">
        <Checklist
          items={[
            { text: "바이브 철학관 세션 시작" },
            { text: "최소 50% 깊이 도달" },
            { text: "나의 프로필 (JSON) 다운로드" },
          ]}
        />
        <Callout type="tip" className="mt-4">
          솔직하게 대화할수록 프로필이 풍부해져요
        </Callout>
      </ContentCard>

      <ContentCard title="선택 과제: Builder 2 미리 체험" color="slate">
        <Checklist
          items={[
            { text: "Builder 1 출력 + 영상으로 Builder 2 시작" },
            { text: "오마주 프롬프트 1개 생성 시도" },
          ]}
        />
      </ContentCard>

      <ContentCard title="2강 실습 예정" color="violet">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
            <div className="text-2xl mb-2">🖼️</div>
            <p className="text-sm text-white">오마주 이미지</p>
            <p className="text-xs text-slate-500">NanoBanana Pro</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
            <div className="text-2xl mb-2">🎭</div>
            <p className="text-sm text-white">변주 이미지</p>
            <p className="text-xs text-slate-500">나의 프로필 반영</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
            <div className="text-2xl mb-2">🎬</div>
            <p className="text-sm text-white">영상 생성</p>
            <p className="text-xs text-slate-500">Veo 3.1 / Kling 3</p>
          </div>
        </div>
      </ContentCard>

      <ContentCard title="제출 방법" color="green">
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 font-medium mb-2">📤 디스코드 #과제제출 채널에 업로드</p>
          <ul className="text-sm text-emerald-200/70 space-y-1">
            <li>1. Builder 1 마크다운</li>
            <li>2. 나의 프로필 JSON</li>
            <li>3. (선택) Builder 2 출력</li>
          </ul>
        </div>
      </ContentCard>
    </div>
  );
}

// ============ UI Components ============

function SectionHeader({ title, subtitle, color }: { title: string; subtitle: string; color: string }) {
  return (
    <div className="mb-8">
      <h1 className={`text-2xl sm:text-3xl font-bold text-white mb-2`}>{title}</h1>
      <p className="text-slate-400">{subtitle}</p>
    </div>
  );
}

function ContentCard({
  title,
  step,
  color,
  children,
}: {
  title: string;
  step?: number;
  color: string;
  children: React.ReactNode;
}) {
  const colorClasses: Record<string, string> = {
    emerald: "from-emerald-500/10 border-emerald-500/20 text-emerald-400",
    cyan: "from-cyan-500/10 border-cyan-500/20 text-cyan-400",
    blue: "from-blue-500/10 border-blue-500/20 text-blue-400",
    purple: "from-purple-500/10 border-purple-500/20 text-purple-400",
    pink: "from-pink-500/10 border-pink-500/20 text-pink-400",
    orange: "from-orange-500/10 border-orange-500/20 text-orange-400",
    red: "from-red-500/10 border-red-500/20 text-red-400",
    green: "from-emerald-500/10 border-emerald-500/20 text-emerald-400",
    violet: "from-violet-500/10 border-violet-500/20 text-violet-400",
    slate: "from-slate-500/10 border-slate-500/20 text-slate-400",
  };
  const c = colorClasses[color] || colorClasses.slate;

  return (
    <div className={`rounded-2xl border bg-gradient-to-br ${c.split(" ")[0]} to-transparent ${c.split(" ")[1]} overflow-hidden`}>
      <div className="px-5 py-4 border-b border-white/5 flex items-center gap-3">
        {step && (
          <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold bg-white/10 ${c.split(" ")[2]}`}>
            {step}
          </span>
        )}
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Checklist({ items }: { items: { text: string; link?: string }[] }) {
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-3 text-sm">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
          {item.link ? (
            <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-slate-300 hover:text-white underline underline-offset-2">
              {item.text}
            </a>
          ) : (
            <span className="text-slate-300">{item.text}</span>
          )}
        </li>
      ))}
    </ul>
  );
}

function Callout({ type, children, className = "" }: { type: "tip" | "warning" | "error"; children: React.ReactNode; className?: string }) {
  const styles = {
    tip: "bg-emerald-500/10 border-emerald-500/20 text-emerald-300",
    warning: "bg-amber-500/10 border-amber-500/20 text-amber-300",
    error: "bg-red-500/10 border-red-500/20 text-red-300",
  };
  const icons = {
    tip: "💡",
    warning: "⚠️",
    error: "❌",
  };

  return (
    <div className={`p-4 rounded-xl border ${styles[type]} ${className}`}>
      <span className="mr-2">{icons[type]}</span>
      {children}
    </div>
  );
}

function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="p-4 rounded-xl bg-black/50 border border-white/10 overflow-x-auto text-sm">
        <code className="text-slate-300">{code}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100"
      >
        {copied ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        ) : (
          <Copy className="w-4 h-4 text-slate-400" />
        )}
      </button>
    </div>
  );
}

function Collapsible({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`border border-white/10 rounded-xl overflow-hidden ${className}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-3 flex items-center justify-between text-sm font-medium text-slate-300 hover:bg-white/5 transition-colors"
      >
        <span>{title}</span>
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

function LinkButton({ href, children, className = "" }: { href: string; children: React.ReactNode; className?: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-sm text-slate-300 hover:text-white transition-colors ${className}`}
    >
      {children}
      <ExternalLink className="w-3.5 h-3.5" />
    </a>
  );
}

function FlowStep({ emoji, text, subtle, highlight }: { emoji: string; text: string; subtle?: boolean; highlight?: boolean }) {
  return (
    <div
      className={`px-4 py-2 rounded-xl ${
        highlight
          ? "bg-gradient-to-r from-violet-500/20 to-pink-500/20 border border-violet-500/30"
          : subtle
          ? "bg-white/5 border border-white/5"
          : "bg-white/10 border border-white/10"
      }`}
    >
      <span className="mr-2">{emoji}</span>
      <span className={subtle ? "text-slate-500" : "text-slate-300"}>{text}</span>
    </div>
  );
}

function FlowArrow() {
  return <div className="text-slate-600">↓</div>;
}
