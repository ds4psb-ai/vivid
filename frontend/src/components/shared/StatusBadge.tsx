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
    bg: string;
    text: string;
    icon: typeof CheckCircle;
}> = {
    pending: {
        label: "대기 중",
        bg: "bg-yellow-500/20",
        text: "text-yellow-400",
        icon: Clock,
    },
    approved: {
        label: "승인됨",
        bg: "bg-green-500/20",
        text: "text-green-400",
        icon: CheckCircle,
    },
    completed: {
        label: "완료",
        bg: "bg-green-500/20",
        text: "text-green-400",
        icon: CheckCircle,
    },
    rejected: {
        label: "거절됨",
        bg: "bg-red-500/20",
        text: "text-red-400",
        icon: XCircle,
    },
    failed: {
        label: "실패",
        bg: "bg-red-500/20",
        text: "text-red-400",
        icon: XCircle,
    },
    processing: {
        label: "처리 중",
        bg: "bg-blue-500/20",
        text: "text-blue-400",
        icon: Loader2,
    },
    in_progress: {
        label: "진행 중",
        bg: "bg-blue-500/20",
        text: "text-blue-400",
        icon: Loader2,
    },
    disputed: {
        label: "분쟁 중",
        bg: "bg-orange-500/20",
        text: "text-orange-400",
        icon: AlertTriangle,
    },
    draft: {
        label: "초안",
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        icon: Clock,
    },
    reversed: {
        label: "취소됨",
        bg: "bg-purple-500/20",
        text: "text-purple-400",
        icon: Ban,
    },
    resolved: {
        label: "해결됨",
        bg: "bg-green-500/20",
        text: "text-green-400",
        icon: CheckCircle,
    },
    skipped: {
        label: "건너뜀",
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        icon: Ban,
    },
};

export function StatusBadge({ status, size = "sm", showIcon = true }: StatusBadgeProps) {
    const config = STATUS_CONFIG[status.toLowerCase()] || {
        label: status,
        bg: "bg-gray-500/20",
        text: "text-gray-400",
        icon: Clock,
    };

    const Icon = config.icon;
    const isAnimated = status === "processing" || status === "in_progress";

    const sizeClasses = size === "sm"
        ? "px-2 py-0.5 text-xs"
        : "px-3 py-1 text-sm";

    return (
        <span className={`inline-flex items-center gap-1 ${sizeClasses} ${config.bg} ${config.text} rounded-full font-medium`}>
            {showIcon && (
                <Icon className={`w-3 h-3 ${isAnimated ? "animate-spin" : ""}`} />
            )}
            {config.label}
        </span>
    );
}

export default StatusBadge;
