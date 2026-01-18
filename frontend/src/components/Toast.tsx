"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, AlertCircle, Info, X } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContextType {
    showToast: (type: ToastType, message: string, duration?: number) => void;
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
}

// =============================================================================
// Context
// =============================================================================

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast(): ToastContextType {
    const context = useContext(ToastContext);
    if (!context) {
        // Return no-op functions if used outside provider (graceful degradation)
        return {
            showToast: () => {},
            success: () => {},
            error: () => {},
            warning: () => {},
            info: () => {},
        };
    }
    return context;
}

// =============================================================================
// Toast Item Component
// =============================================================================

const TOAST_CONFIG: Record<ToastType, { icon: typeof CheckCircle; color: string; bgColor: string }> = {
    success: { icon: CheckCircle, color: "event-tone-success", bgColor: "event-bg-success event-border-success" },
    error: { icon: XCircle, color: "event-tone-error", bgColor: "event-bg-error event-border-error" },
    warning: { icon: AlertCircle, color: "event-tone-warning", bgColor: "event-bg-warning event-border-warning" },
    info: { icon: Info, color: "event-tone-info", bgColor: "event-bg-info event-border-info" },
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
    const config = TOAST_CONFIG[toast.type];
    const Icon = config.icon;

    return (
        <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl shadow-lg ${config.bgColor}`}
        >
            <Icon className={`w-5 h-5 flex-shrink-0 ${config.color}`} />
            <p className="text-sm text-[var(--fg-0)] flex-1">{toast.message}</p>
            <button
                onClick={() => onDismiss(toast.id)}
                className="p-1 rounded-lg hover:bg-[var(--surface-2)] transition-colors"
            >
                <X className="w-4 h-4 text-[var(--fg-subtle)]" />
            </button>
        </motion.div>
    );
}

// =============================================================================
// Toast Provider
// =============================================================================

const DEFAULT_DURATION = 4000;
const MAX_TOASTS = 5;

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const dismissToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const showToast = useCallback((type: ToastType, message: string, duration = DEFAULT_DURATION) => {
        const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        const newToast: Toast = { id, type, message, duration };

        setToasts((prev) => {
            const updated = [...prev, newToast];
            // Keep only the latest MAX_TOASTS
            return updated.slice(-MAX_TOASTS);
        });

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => dismissToast(id), duration);
        }
    }, [dismissToast]);

    const contextValue: ToastContextType = {
        showToast,
        success: (message, duration) => showToast("success", message, duration),
        error: (message, duration) => showToast("error", message, duration),
        warning: (message, duration) => showToast("warning", message, duration),
        info: (message, duration) => showToast("info", message, duration),
    };

    return (
        <ToastContext.Provider value={contextValue}>
            {children}
            {/* Toast Container */}
            <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
                <AnimatePresence mode="popLayout">
                    {toasts.map((toast) => (
                        <div key={toast.id} className="pointer-events-auto">
                            <ToastItem toast={toast} onDismiss={dismissToast} />
                        </div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
}
