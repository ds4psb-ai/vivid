"use client";

import { ReactNode, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { X } from "lucide-react";
import { useCreditBalance } from "@/hooks/useCreditBalance";

interface AppShellProps {
    children: ReactNode;
    showSidebar?: boolean;
    showTopBar?: boolean;
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

export default function AppShell({
    children,
    showSidebar = true,
    showTopBar = true,
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
    const { balance: liveBalance } = useCreditBalance(
        undefined,
        typeof creditBalance !== "number"
    );
    const resolvedBalance =
        typeof creditBalance === "number" ? creditBalance : liveBalance;

    const handleMenuToggle = useCallback(() => {
        setMobileMenuOpen((prev) => !prev);
    }, []);

    const handleMobileClose = useCallback(() => {
        setMobileMenuOpen(false);
    }, []);

    return (
        <div className="min-h-screen bg-[var(--bg-0)]">
            {/* Desktop Sidebar */}
            {showSidebar && (
                <div className="hidden lg:block">
                    <Sidebar creditBalance={resolvedBalance} />
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
                            <Sidebar creditBalance={resolvedBalance} onMobileClose={handleMobileClose} />
                            {/* Close button */}
                            <button
                                onClick={handleMobileClose}
                                className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white transition-colors hover:bg-white/20"
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
                />
            )}

            {/* Main Content */}
            <main
                className={`transition-all duration-300 ${showSidebar ? "lg:ml-60" : ""
                    } ${showTopBar ? "pt-14" : ""}`}
            >
                {children}
            </main>
        </div>
    );
}
