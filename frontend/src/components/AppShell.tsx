"use client";

import { ReactNode, useState, useCallback, useMemo } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import CollapsibleSidebar from "./CollapsibleSidebar";
import TopBar from "./TopBar";
import { AgentChatAccordion } from "./AgentChatAccordion";
import { X } from "lucide-react";
import { useCreditBalance } from "@/hooks/useCreditBalance";
import { useSessionContext } from "@/contexts/SessionContext";
import { CreditProvider } from "@/components/CreditGate";

interface AppShellProps {
    children: ReactNode;
    showSidebar?: boolean;
    showTopBar?: boolean;
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
    "/dimension": "안녕하세요! 저는 초끼예요 🐰 차원문(미니앱)들을 둘러보고 계시네요. 어떤 도구가 필요하신지 물어보세요!",
    "/flow": "안녕하세요! 차원 흐름을 함께 설계해드릴게요. 어떤 콘텐츠를 만들고 싶으신가요?",
    "/train": "안녕하세요! 열차 워크플로우에 오셨네요 🚂 도구들을 연결해서 콘텐츠를 만들어볼까요?",
    "/tools": "안녕하세요! 도구 상세 페이지네요. 이 도구 사용법이 궁금하시면 물어보세요!",
    "/crebit": "안녕하세요! Crebit 페이지에 오셨네요. 크레딧이나 구독에 대해 궁금한 점이 있으신가요?",
    default: "안녕하세요! 저는 초끼예요 🐰 무엇을 도와드릴까요?",
};

export default function AppShell({
    children,
    showSidebar = true,
    showTopBar = true,
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
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { session } = useSessionContext();
    const { balance: liveBalance } = useCreditBalance(
        typeof creditBalance !== "number"
    );
    const resolvedBalance =
        typeof creditBalance === "number" ? creditBalance : liveBalance;

    const pathname = usePathname();

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

    const handleMenuToggle = useCallback(() => {
        setMobileMenuOpen((prev) => !prev);
    }, []);

    const handleMobileClose = useCallback(() => {
        setMobileMenuOpen(false);
    }, []);

    return (
        <CreditProvider>
            <div className="min-h-screen bg-[var(--bg-0)]">
                {/* Desktop Sidebar */}
                {showSidebar && (
                    <div className="hidden lg:block">
                        <CollapsibleSidebar />
                    </div>
                )}

                {/* Mobile Sidebar Overlay */}
                <AnimatePresence>
                    {showSidebar && mobileMenuOpen && (
                        <>
                            {/* Backdrop */}
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={handleMobileClose}
                                className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
                                aria-hidden="true"
                            />
                            {/* Sidebar */}
                            <motion.div
                                initial={{ x: "-100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "-100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                                className="fixed inset-y-0 left-0 z-50 lg:hidden"
                            >
                                <CollapsibleSidebar defaultExpanded={true} />
                                {/* Close button - positioned at top right of expanded sidebar area */}
                                <button
                                    onClick={handleMobileClose}
                                    className="absolute top-4 left-[220px] flex h-8 w-8 items-center justify-center rounded-lg bg-black/60 text-white transition-colors hover:bg-black/80 backdrop-blur-sm"
                                    aria-label="Close menu"
                                >
                                    <X className="h-5 w-5" aria-hidden="true" />
                                </button>
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>

                {/* TopBar */}
                {showTopBar && (
                    <TopBar
                        projectName={projectName}
                        creditBalance={resolvedBalance}
                        isSaving={isSaving}
                        isRunning={isRunning}
                        onRun={onRun}
                        onSave={onSave}
                        onNameChange={onNameChange}
                        onMenuToggle={handleMenuToggle}
                        showBackButton={showBackButton}
                        backHref={backHref}
                        session={session}
                    />
                )}

                {/* Main Content */}
                <main
                    className={`transition-all duration-300 ${showSidebar ? "lg:ml-14" : ""} ${showTopBar ? "pt-14" : ""}`}
                >
                    {children}
                </main>

                {/* Global Chokki Agent */}
                {showChokki && (
                    <AgentChatAccordion
                        initialMessage={chokkiInitialMessage}
                    />
                )}
            </div>
        </CreditProvider>
    );
}
