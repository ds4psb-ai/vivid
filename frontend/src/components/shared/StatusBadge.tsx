/**
 * Status Badge Component (한국어)
 * 
 * 다양한 상태를 지원하는 상태 표시 배지
 */

import { CheckCircle, Clock, XCircle, AlertTriangle, Loader2, Ban } from "lucide-react";

export type StatusType =
    | "pending"
    | "approved"
    | "rejected"
    | "processing"
    | "completed"
    | "failed"
    | "disputed"
    | "in_progress"
    | "draft"
    | "reversed";

interface StatusBadgeProps {
    status: StatusType | string;
    size?: "sm" | "md";
    showIcon?: boolean;
}

const STATUS_CONFIG: Record<string, {
    label: string;
    tone: "idle" | "loading" | "complete" | "error" | "cancelled";
    icon: typeof CheckCircle;
}> = {
    pending: {
        label: "대기 중",
        tone: "idle",
        icon: Clock,
    },
    approved: {
        label: "승인됨",
        tone: "complete",
        icon: CheckCircle,
    },
    completed: {
        label: "완료",
        tone: "complete",
        icon: CheckCircle,
    },
    rejected: {
        label: "거절됨",
        tone: "error",
        icon: XCircle,
    },
    failed: {
        label: "실패",
        tone: "error",
        icon: XCircle,
    },
    processing: {
        label: "처리 중",
        tone: "loading",
        icon: Loader2,
    },
    in_progress: {
        label: "진행 중",
        tone: "loading",
        icon: Loader2,
    },
    disputed: {
        label: "분쟁 중",
        tone: "error",
        icon: AlertTriangle,
    },
    draft: {
        label: "초안",
        tone: "idle",
        icon: Clock,
    },
    reversed: {
        label: "취소됨",
        tone: "cancelled",
        icon: Ban,
    },
    resolved: {
        label: "해결됨",
        tone: "complete",
        icon: CheckCircle,
    },
    skipped: {
        label: "건너뜀",
        tone: "cancelled",
        icon: Ban,
    },
};

export function StatusBadge({ status, size = "sm", showIcon = true }: StatusBadgeProps) {
    const config = STATUS_CONFIG[status.toLowerCase()] || {
        label: status,
        tone: "idle",
        icon: Clock,
    };

    const Icon = config.icon;
    const isAnimated = status === "processing" || status === "in_progress";

    const sizeClasses = size === "sm"
        ? "px-2 py-0.5 text-xs"
        : "px-3 py-1 text-sm";

    const toneClass = `run-state ${config.tone}`;

    return (
        <span className={`inline-flex items-center gap-1 ${sizeClasses} bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded-full font-medium ${toneClass}`}>
            {showIcon && (
                <Icon className={`w-3 h-3 ${toneClass} ${isAnimated ? "animate-spin" : ""}`} />
            )}
            {config.label}
        </span>
    );
}

export default StatusBadge;
