"use client";

/**
 * AppShell - Global Layout Component
 *
 * 2026 Sidebar layout:
 * - Left collapsible sidebar (Global/Academy variants)
 * - TopBar for Canvas/project controls
 * - Chokki AI assistant FAB
 *
 * Mobile: sidebar hidden, CrebitNavbar used via hamburger.
 */

import { ReactNode, useMemo, lazy, Suspense } from "react";
import { usePathname } from "next/navigation";
import { ChokkiFABSkeleton } from "./ChokkiFABSkeleton";
import TopBar from "./TopBar";
import { CrebitSidebar } from "./sidebar/CrebitSidebar";
import { StudioSidebar } from "./sidebar/StudioSidebar";
import { CrebitNavbar } from "./home/CrebitNavbar";
import { AcademyMobileNav } from "./academy/AcademyMobileNav";
import { useCreditBalance } from "@/hooks/useCreditBalance";
import { useSessionContext } from "@/contexts/SessionContext";
import { CreditProvider } from "@/components/CreditGate";
import type { TabKey } from "@/app/academy/constants";

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
   */
  showSidebar?: boolean;
  /** Show the sidebar/navbar (default: true) */
  showNavbar?: boolean;
  /** Show the TopBar (project controls) */
  showTopBar?: boolean;
  /** Show Chokki AI assistant FAB */
  showChokki?: boolean;
  /** Select navigation family for this page */
  navVariant?: "global" | "academy";
  /** Current academy tab (used by academy mobile nav) */
  academyCurrentTab?: TabKey;
  /** Academy tab navigation handler */
  onAcademyTabChange?: (tab: TabKey) => void;
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
  showSidebar = true,
  showNavbar,
  showTopBar = false,
  showChokki = true,
  navVariant = "global",
  academyCurrentTab = "home",
  onAcademyTabChange,
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
  const shouldShowNav = showNavbar ?? showSidebar;

  // Get context-aware initial message for Chokki
  const chokkiInitialMessage = useMemo(() => {
    if (PAGE_CONTEXT_MESSAGES[pathname]) {
      return PAGE_CONTEXT_MESSAGES[pathname];
    }
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
        {/* Sidebar – desktop only */}
        {shouldShowNav && (
          <>
            {navVariant === "academy" ? <CrebitSidebar /> : <StudioSidebar />}
          </>
        )}

        {/* Mobile Navbar – md 이하에서만 표시 */}
        {shouldShowNav && (
          <div className="md:hidden">
            {navVariant === "academy" ? (
              <AcademyMobileNav
                currentTab={academyCurrentTab}
                onTabChange={onAcademyTabChange}
              />
            ) : (
              <CrebitNavbar showSpacer={!showTopBar} />
            )}
          </div>
        )}

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
            hasSidebar={shouldShowNav}
          />
        )}

        {/* Main Content – offset by sidebar on desktop */}
        <main
          className={`transition-[margin] duration-300 ease-out
            ${shouldShowNav ? "md:ml-[var(--sidebar-current,var(--sidebar-collapsed))]" : ""}
            ${showTopBar ? "pt-14" : ""}`}
        >
          {children}
        </main>

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
