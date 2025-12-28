"use client";

import Link from "next/link";
import { AlertTriangle, Info, ShieldAlert, WifiOff } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

type StatusVariant = "loading" | "error" | "empty" | "admin";

type StatusAction = {
  label: string;
  href?: string;
  onClick?: () => void;
};

interface PageStatusProps {
  variant: StatusVariant;
  title: string;
  message?: string;
  hint?: string;
  action?: StatusAction;
  className?: string;
  isOffline?: boolean;
}

const TONE_STYLES: Record<StatusVariant, { wrapper: string; icon: string }> = {
  loading: {
    wrapper: "border-sky-500/30 bg-sky-500/10 text-sky-100",
    icon: "text-sky-200",
  },
  error: {
    wrapper: "border-rose-500/30 bg-rose-500/10 text-rose-100",
    icon: "text-rose-200",
  },
  empty: {
    wrapper: "border-white/10 bg-white/5 text-[var(--fg-muted)]",
    icon: "text-[var(--fg-muted)]",
  },
  admin: {
    wrapper: "border-amber-500/30 bg-amber-500/10 text-amber-100",
    icon: "text-amber-200",
  },
};

export default function PageStatus({
  variant,
  title,
  message,
  hint,
  action,
  className,
  isOffline = false,
}: PageStatusProps) {
  const { language } = useLanguage();
  const styles = TONE_STYLES[variant];
  const Icon =
    variant === "admin"
      ? ShieldAlert
      : variant === "error"
        ? AlertTriangle
        : Info;
  const offlineHint =
    language === "ko"
      ? "서버에 연결할 수 없습니다. 백엔드(8100)가 실행 중인지 확인하세요."
      : "Unable to reach the API. Confirm the backend is running on port 8100.";
  const resolvedHint = hint || (isOffline && variant === "error" ? offlineHint : undefined);
  const role = variant === "error" ? "alert" : "status";

  return (
    <div
      role={role}
      className={`rounded-xl border px-4 py-4 text-sm ${styles.wrapper} ${className ?? ""}`}
    >
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 rounded-lg bg-white/5 p-2 ${styles.icon}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
        <div className="flex-1">
          <div className="font-semibold">{title}</div>
          {message && <div className="mt-1 text-xs">{message}</div>}
          {resolvedHint && (
            <div className="mt-2 inline-flex items-center gap-2 text-xs text-[var(--fg-muted)]">
              <WifiOff className="h-3 w-3" aria-hidden="true" />
              {resolvedHint}
            </div>
          )}
          {action && action.label && (
            <div className="mt-3">
              {action.href ? (
                <Link
                  href={action.href}
                  className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-white/90 transition hover:bg-white/20"
                >
                  {action.label}
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={action.onClick}
                  className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-white/90 transition hover:bg-white/20"
                >
                  {action.label}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
