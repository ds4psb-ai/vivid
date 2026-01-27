"use client";

/**
 * AppShell - Global Layout Component
 *
 * 2026 Netflix-style layout:
 * - Top header navigation with mega menu (CrebitNavbar)
 * - No sidebar (removed in favor of header navigation)
 * - Chokki AI assistant FAB
 *
 * Migration note: showSidebar prop is deprecated but kept for backward
 * compatibility. It now controls whether to show the header navbar.
 */

import { ReactNode, useMemo, lazy, Suspense } from "react";
import { usePathname } from "next/navigation";
import { ChokkiFABSkeleton } from "./ChokkiFABSkeleton";
import TopBar from "./TopBar";
import { CrebitNavbar } from "./home/CrebitNavbar";
import { useCreditBalance } from "@/hooks/useCreditBalance";
import { useSessionContext } from "@/contexts/SessionContext";
import { CreditProvider } from "@/components/CreditGate";

// Lazy load heavy AgentChatAccordion to reduce initial bundle
const AgentChatAccordion = lazy(() =>
  import("./AgentChatAccordion").then((mod) => ({
    default: mod.AgentChatAccordion,
  }))
);

interface AppShellProps {
  children: ReactNode;
  /**
   * @deprecated Use showNavbar instead. Kept for backward compatibility.
   * Now controls whether to show the top navbar.
   */
  showSidebar?: boolean;
  /** Show the header navbar (default: true) */
  showNavbar?: boolean;
  /** Show the TopBar (project controls) */
  showTopBar?: boolean;
  /** Show Chokki AI assistant FAB */
  showChokki?: boolean;
  projectName?: string;
  creditBalance?: number;
  isSaving?: boolean;
  isRunning?: boolean;
  onRun?: () => void;
  onSave?: () => void;
  onNameChange?: (name: string) => void;
  showBackButton?: boolean;
  backHref?: string;
}

// Page context messages for Chokki
const PAGE_CONTEXT_MESSAGES: Record<string, string> = {
  // Core Pages
  "/dimension":
    "안녕하세요! 저는 초끼예요 🐰 차원문(미니앱)들을 둘러보고 계시네요. 원하는 도구 찾아드릴까요?",
  "/flow":
    "안녕하세요! 차원 흐름을 함께 설계해드릴게요. 어떤 콘텐츠를 만들고 싶으신가요?",
  "/singularity":
    "안녕하세요! 🌌 싱귤래리티 템플릿 갤러리입니다. 마음에 드는 워크플로우 조합 찾아드릴까요?",

  // Tools Pages
  "/tools":
    "안녕하세요! 🔧 도구 대시보드입니다. 새 도구를 만들거나 기존 도구를 Fork해보세요!",
  "/tools/create":
    "새 도구를 만드시는군요! 💡 도구 이름, 설명, 스키마 작성을 도와드릴까요?",

  // HumanCloud Pages
  "/humancloud":
    "안녕하세요! 🎨 휴먼클라우드 마켓플레이스입니다. 요청을 올리거나 크리에이터를 찾아보세요!",
  "/humancloud/requests":
    "요청 목록입니다. 새 요청을 만들거나 기존 요청 상태를 확인해보세요.",
  "/humancloud/creator":
    "크리에이터 프로필 페이지네요. 크리에이터 등록이나 수정을 도와드릴까요?",

  // Settings & Credits
  "/settings":
    "⚙️ 설정 페이지입니다. API 키 연결, 알림 설정 등 궁금한 점 물어보세요!",
  "/credits":
    "💳 크레딧 관리 페이지입니다. 충전, 사용 내역, BYOK 설정을 도와드릴게요.",

  // Sandbox
  "/sandbox": "🧪 샌드박스 모드입니다. 도구를 테스트해보세요!",

  // Admin (for admin users)
  "/admin": "🔐 관리자 페이지입니다. 어떤 관리 작업이 필요하신가요?",

  default: "안녕하세요! 저는 초끼예요 🐰 무엇이든 물어보세요!",
};

export default function AppShell({
  children,
  showSidebar = true, // deprecated, maps to showNavbar
  showNavbar,
  showTopBar = false,
  showChokki = true,
  projectName = "Untitled Canvas",
  creditBalance,
  isSaving = false,
  isRunning = false,
  onRun,
  onSave,
  onNameChange,
  showBackButton = false,
  backHref = "/",
}: AppShellProps) {
  const { session } = useSessionContext();
  const { balance: liveBalance } = useCreditBalance(
    typeof creditBalance !== "number"
  );
  const resolvedBalance =
    typeof creditBalance === "number" ? creditBalance : liveBalance;

  const pathname = usePathname();

  // Resolve navbar visibility: showNavbar takes precedence over showSidebar
  const shouldShowNavbar = showNavbar ?? showSidebar;

  // Get context-aware initial message for Chokki
  const chokkiInitialMessage = useMemo(() => {
    // Check for exact matches first
    if (PAGE_CONTEXT_MESSAGES[pathname]) {
      return PAGE_CONTEXT_MESSAGES[pathname];
    }
    // Check for partial matches (e.g., /tools/xxx)
    for (const [path, message] of Object.entries(PAGE_CONTEXT_MESSAGES)) {
      if (path !== "default" && pathname.startsWith(path)) {
        return message;
      }
    }
    return PAGE_CONTEXT_MESSAGES.default;
  }, [pathname]);

  return (
    <CreditProvider>
      <div className="min-h-screen bg-[var(--bg-0)]">
        {/* Header Navbar - Netflix 2026 style */}
        {shouldShowNavbar && <CrebitNavbar showSpacer={!showTopBar} />}

        {/* TopBar - for project controls (Canvas mode) */}
        {showTopBar && (
          <TopBar
            projectName={projectName}
            creditBalance={resolvedBalance}
            isSaving={isSaving}
            isRunning={isRunning}
            onRun={onRun}
            onSave={onSave}
            onNameChange={onNameChange}
            showBackButton={showBackButton}
            backHref={backHref}
            session={session}
          />
        )}

        {/* Main Content */}
        <main className={showTopBar ? "pt-14" : ""}>{children}</main>

        {/* Global Chokki Agent - Lazy Loaded */}
        {showChokki && (
          <Suspense fallback={<ChokkiFABSkeleton />}>
            <AgentChatAccordion initialMessage={chokkiInitialMessage} />
          </Suspense>
        )}
      </div>
    </CreditProvider>
  );
}
