"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    Play,
    CreditCard,
    Menu,
    Save,
    ChevronLeft,
    Loader2,
    LogIn,
    LogOut,
    UserCircle,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, AuthSession } from "@/lib/api";
import { getAuthStartUrl } from "@/lib/auth";

interface TopBarProps {
    projectName?: string;
    creditBalance?: number;
    isSaving?: boolean;
    isRunning?: boolean;
    onRun?: () => void;
    onSave?: () => void;
    onMenuToggle?: () => void;
    onNameChange?: (name: string) => void;
    showBackButton?: boolean;
    backHref?: string;
    session?: AuthSession | null;
}

export default function TopBar({
    projectName = "Untitled Canvas",
    creditBalance = 0,
    isSaving = false,
    isRunning = false,
    onRun,
    onSave,
    onMenuToggle,
    onNameChange,
    showBackButton = false,
    backHref = "/",
    session,
}: TopBarProps) {
    const { t } = useLanguage();
    const router = useRouter();
    const [isEditing, setIsEditing] = useState(false);
    const [editedName, setEditedName] = useState(projectName);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    // Sync editedName when projectName prop changes
    useEffect(() => {
        setEditedName(projectName);
    }, [projectName]);

    const handleNameSubmit = useCallback(() => {
        setIsEditing(false);
        if (editedName.trim() && editedName !== projectName) {
            onNameChange?.(editedName.trim());
        } else {
            setEditedName(projectName);
        }
    }, [editedName, projectName, onNameChange]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            handleNameSubmit();
        } else if (e.key === "Escape") {
            setIsEditing(false);
            setEditedName(projectName);
        }
    }, [handleNameSubmit, projectName]);

    const getLabel = useCallback((key: string, fallback: string) => {
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const translated = t(key as any);
            return translated !== key ? translated : fallback;
        } catch {
            return fallback;
        }
    }, [t]);

    const handleLogout = useCallback(async () => {
        setIsLoggingOut(true);
        try {
            await api.logout();
            router.refresh();
        } finally {
            setIsLoggingOut(false);
        }
    }, [router]);

    // Use centralized auth URL utility
    const authStartUrl = getAuthStartUrl();

    const userLabel = session?.user?.name || session?.user?.email || getLabel("account", "Account");
    const isAuthenticated = Boolean(session?.authenticated);

    return (
        <header
            className="fixed left-60 right-0 top-0 z-30 flex h-14 items-center justify-between border-b border-white/10 bg-[var(--bg-0)]/80 px-4 backdrop-blur-xl"
            role="banner"
        >
            {/* Left Section */}
            <div className="flex items-center gap-3">
                {showBackButton && (
                    <Link
                        href={backHref}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--fg-muted)] transition-colors hover:bg-white/10 hover:text-[var(--fg-0)]"
                        aria-label={getLabel("back", "Go back")}
                    >
                        <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                    </Link>
                )}

                {onMenuToggle && (
                    <button
                        onClick={onMenuToggle}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--fg-muted)] transition-colors hover:bg-white/10 hover:text-[var(--fg-0)] lg:hidden"
                        aria-label={getLabel("toggleMenu", "Toggle menu")}
                        aria-expanded="false"
                    >
                        <Menu className="h-5 w-5" aria-hidden="true" />
                    </button>
                )}

                {isEditing ? (
                    <input
                        type="text"
                        value={editedName}
                        onChange={(e) => setEditedName(e.target.value)}
                        onBlur={handleNameSubmit}
                        onKeyDown={handleKeyDown}
                        className="min-w-[200px] rounded-lg border border-white/20 bg-white/5 px-3 py-1 text-sm font-medium text-[var(--fg-0)] outline-none focus:border-[var(--accent)]"
                        aria-label={getLabel("projectName", "Project name")}
                        autoFocus
                    />
                ) : (
                    <button
                        onClick={() => setIsEditing(true)}
                        className="max-w-[300px] truncate rounded-lg px-3 py-1 text-sm font-medium text-[var(--fg-0)] transition-colors hover:bg-white/5"
                        aria-label={getLabel("editProjectName", "Edit project name")}
                    >
                        {projectName}
                    </button>
                )}

                {isSaving && (
                    <span className="flex items-center gap-1 text-xs text-[var(--fg-muted)]" role="status">
                        <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                        {getLabel("saving", "Saving...")}
                    </span>
                )}
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-3">
                {isAuthenticated ? (
                    <div className="flex items-center gap-2 rounded-lg bg-white/5 px-3 py-1.5 text-sm">
                        <UserCircle className="h-4 w-4 text-[var(--fg-muted)]" aria-hidden="true" />
                        <span className="max-w-[160px] truncate">{userLabel}</span>
                        {session?.user?.role && (
                            <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-[var(--fg-muted)]">
                                {session.user.role}
                            </span>
                        )}
                    </div>
                ) : (
                    <Link
                        href={authStartUrl}
                        className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-[var(--fg-0)] transition-colors hover:bg-white/10"
                    >
                        <LogIn className="h-4 w-4" aria-hidden="true" />
                        {getLabel("signIn", "Sign in")}
                    </Link>
                )}

                {isAuthenticated && (
                    <button
                        onClick={handleLogout}
                        disabled={isLoggingOut}
                        className="flex h-9 items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 text-sm font-medium transition-colors hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label={getLabel("signOut", "Sign out")}
                    >
                        {isLoggingOut ? (
                            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        ) : (
                            <LogOut className="h-4 w-4" aria-hidden="true" />
                        )}
                        {getLabel("signOut", "Sign out")}
                    </button>
                )}

                {/* Credit Balance */}
                <Link
                    href="/credits"
                    className="flex items-center gap-2 rounded-lg bg-white/5 px-3 py-1.5 text-sm transition-colors hover:bg-white/10"
                    aria-label={`${creditBalance.toLocaleString()} ${getLabel("credits", "credits")} available`}
                >
                    <CreditCard className="h-4 w-4 text-[var(--accent)]" aria-hidden="true" />
                    <span className="font-medium">{creditBalance.toLocaleString()}</span>
                </Link>

                {/* Save Button */}
                {onSave && (
                    <button
                        onClick={onSave}
                        disabled={isSaving}
                        className="flex h-9 items-center gap-2 rounded-lg border border-white/20 bg-white/5 px-4 text-sm font-medium transition-colors hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label={isSaving ? getLabel("saving", "Saving...") : getLabel("save", "Save")}
                    >
                        {isSaving ? (
                            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        ) : (
                            <Save className="h-4 w-4" aria-hidden="true" />
                        )}
                        {getLabel("save", "Save")}
                    </button>
                )}

                {/* Run Button */}
                {onRun && (
                    <motion.button
                        onClick={onRun}
                        disabled={isRunning}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="flex h-9 items-center gap-2 rounded-lg bg-gradient-to-r from-sky-500 to-sky-600 px-5 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:from-sky-400 hover:to-sky-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label={isRunning ? getLabel("running", "Running...") : getLabel("run", "Run")}
                    >
                        {isRunning ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                                {getLabel("running", "Running...")}
                            </>
                        ) : (
                            <>
                                <Play className="h-4 w-4" aria-hidden="true" />
                                {getLabel("run", "Run")}
                            </>
                        )}
                    </motion.button>
                )}
            </div>
        </header>
    );
}
