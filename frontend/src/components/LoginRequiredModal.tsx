"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, LogIn } from "lucide-react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { getAuthStartUrl } from "@/lib/auth";

interface LoginRequiredModalProps {
    isOpen: boolean;
    onClose: () => void;
    returnTo?: string;
}

export default function LoginRequiredModal({ isOpen, onClose, returnTo }: LoginRequiredModalProps) {
    const { t } = useLanguage();

    // Use centralized auth URL utility
    const authUrl = getAuthStartUrl(returnTo);

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed left-1/2 top-1/2 z-[101] w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-xl border border-white/10 bg-[#1a1a1c] p-6 shadow-2xl"
                    >
                        <button
                            onClick={onClose}
                            className="absolute right-4 top-4 text-slate-400 hover:text-white"
                        >
                            <X className="h-5 w-5" />
                        </button>

                        <div className="mb-6 flex justify-center">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#4200FF]/20 text-[#4200FF]">
                                <LogIn className="h-6 w-6" />
                            </div>
                        </div>

                        <h3 className="mb-2 text-center text-lg font-bold text-white">
                            {t("signInRequired") || "Sign In Required"}
                        </h3>
                        <p className="mb-6 text-center text-sm text-slate-400">
                            {t("signInRequiredDesc") || "Please sign in to save your progress or run the canvas."}
                        </p>

                        <div className="space-y-3">
                            <Link
                                href={authUrl}
                                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#4200FF] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#3300CC] transition-colors"
                            >
                                <LogIn className="h-4 w-4" />
                                {t("signIn") || "Sign In"}
                            </Link>
                            <button
                                onClick={onClose}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/10 transition-colors"
                            >
                                {t("cancel") || "Cancel"}
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
