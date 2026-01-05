"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    Sparkles,
    LayoutGrid,
    Image as ImageIcon,
    Film,
    CheckCircle,
    Loader2,
    Play,
    RotateCcw,
    AlertCircle,
} from "lucide-react";

interface TrainCarProps {
    id: string;
    order: number;
    toolId: string;
    displayName: string;
    icon: string;
    color: string;
    status: "pending" | "ready" | "executing" | "completed" | "failed";
    isActive?: boolean;
    onExecute?: () => void;
    onRetry?: () => void;
    inputs?: Record<string, unknown>;
    output?: Record<string, unknown>;
    error?: string;
    creditCost?: number;
}

const ICON_MAP: Record<string, React.ReactNode> = {
    sparkles: <Sparkles className="h-6 w-6" />,
    "layout-grid": <LayoutGrid className="h-6 w-6" />,
    image: <ImageIcon className="h-6 w-6" />,
    film: <Film className="h-6 w-6" />,
};

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; glow: string; portalGlow: string }> = {
    violet: {
        bg: "bg-violet-500/20",
        border: "border-violet-500/50",
        text: "text-violet-400",
        glow: "shadow-[0_0_30px_rgba(139,92,246,0.3)]",
        portalGlow: "shadow-[0_0_60px_rgba(139,92,246,0.4),inset_0_0_30px_rgba(139,92,246,0.1)]",
    },
    emerald: {
        bg: "bg-emerald-500/20",
        border: "border-emerald-500/50",
        text: "text-emerald-400",
        glow: "shadow-[0_0_30px_rgba(16,185,129,0.3)]",
        portalGlow: "shadow-[0_0_60px_rgba(16,185,129,0.4),inset_0_0_30px_rgba(16,185,129,0.1)]",
    },
    amber: {
        bg: "bg-amber-500/20",
        border: "border-amber-500/50",
        text: "text-amber-400",
        glow: "shadow-[0_0_30px_rgba(245,158,11,0.3)]",
        portalGlow: "shadow-[0_0_60px_rgba(245,158,11,0.4),inset_0_0_30px_rgba(245,158,11,0.1)]",
    },
    cyan: {
        bg: "bg-cyan-500/20",
        border: "border-cyan-500/50",
        text: "text-cyan-400",
        glow: "shadow-[0_0_30px_rgba(6,182,212,0.3)]",
        portalGlow: "shadow-[0_0_60px_rgba(6,182,212,0.4),inset_0_0_30px_rgba(6,182,212,0.1)]",
    },
};

const STATUS_INDICATOR: Record<string, React.ReactNode> = {
    pending: <div className="h-2 w-2 rounded-full bg-zinc-500" />,
    ready: <div className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />,
    executing: <Loader2 className="h-4 w-4 text-amber-400 animate-spin" />,
    completed: <CheckCircle className="h-4 w-4 text-emerald-400" />,
    failed: <div className="h-2 w-2 rounded-full bg-red-500" />,
};

export function TrainCar({
    order,
    toolId,
    displayName,
    icon,
    color,
    status,
    isActive = false,
    onExecute,
    onRetry,
    output,
    error,
    creditCost,
}: TrainCarProps) {
    const [showFullError, setShowFullError] = useState(false);
    const colorScheme = COLOR_MAP[color] || COLOR_MAP.violet;
    const IconComponent = ICON_MAP[icon] || <Sparkles className="h-6 w-6" />;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: order * 0.1 }}
            className={`
                relative flex flex-col items-center
                ${isActive ? "z-10" : "z-0"}
            `}
        >
            {/* 차원 노드 본체 */}
            <div
                className={`
                    relative w-40 h-48 rounded-3xl
                    ${colorScheme.bg} ${colorScheme.border} border-2
                    backdrop-blur-xl
                    flex flex-col items-center justify-center gap-3
                    transition-all duration-500
                    ${isActive ? colorScheme.portalGlow : colorScheme.glow}
                    ${status === "completed" ? "opacity-80" : ""}
                `}
            >
                {/* 포털 링 이펙트 */}
                {isActive && (
                    <div className={`absolute inset-0 rounded-3xl border ${colorScheme.border} animate-pulse opacity-50`} />
                )}

                {/* 상태 표시 */}
                <div className="absolute top-3 right-3">
                    {STATUS_INDICATOR[status]}
                </div>

                {/* 아이콘 */}
                <div
                    className={`
                        h-14 w-14 rounded-2xl
                        ${colorScheme.bg} ${colorScheme.border} border
                        flex items-center justify-center
                        ${colorScheme.text}
                        transition-transform duration-300
                        ${isActive ? "scale-110" : ""}
                    `}
                >
                    {IconComponent}
                </div>

                {/* 이름 */}
                <div className="text-center px-3">
                    <h4 className="text-sm font-bold text-white truncate max-w-[130px]">
                        {displayName}
                    </h4>
                    <p className="text-[10px] text-zinc-500 mt-0.5">
                        {toolId.replace("_", " ")}
                    </p>
                </div>

                {/* 실행 버튼 */}
                {status === "ready" && onExecute && (
                    <button
                        onClick={onExecute}
                        className={`
                            flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                            bg-gradient-to-r from-violet-600 to-purple-600
                            text-white text-xs font-medium
                            hover:shadow-[0_0_20px_rgba(139,92,246,0.5)]
                            transition-all duration-300
                        `}
                    >
                        <Play className="h-3 w-3" />
                        실행
                    </button>
                )}

                {/* [TIER2] 실행 중 상태 피드백 */}
                {status === "executing" && (
                    <div className="text-[10px] text-amber-400 text-center px-2 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        실행 중...
                    </div>
                )}

                {/* 완료 시 출력 미리보기 */}
                {status === "completed" && output && (
                    <div className="text-[10px] text-emerald-400 text-center px-2 flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" />
                        차원 전개 완료
                        {creditCost !== undefined && (
                            <span className="text-amber-400 ml-1">(-{creditCost})</span>
                        )}
                    </div>
                )}

                {/* [TIER2] 실패 시 에러 메시지 + 재시도 버튼 */}
                {status === "failed" && (
                    <div className="flex flex-col items-center gap-2">
                        {/* 에러 메시지 (클릭으로 확장) */}
                        <button
                            onClick={() => setShowFullError(!showFullError)}
                            className="text-[10px] text-red-400 text-center px-2 flex items-center gap-1 hover:text-red-300 transition-colors"
                        >
                            <AlertCircle className="h-3 w-3 flex-shrink-0" />
                            <span className={showFullError ? "" : "max-w-[100px] truncate"}>
                                {error || "실행 실패"}
                            </span>
                        </button>

                        {/* 재시도 버튼 */}
                        {onRetry && (
                            <button
                                onClick={onRetry}
                                className={`
                                    flex items-center gap-1 px-2.5 py-1 rounded-lg
                                    bg-red-500/20 border border-red-500/50
                                    text-red-400 text-[10px] font-medium
                                    hover:bg-red-500/30 hover:text-red-300
                                    transition-all duration-200
                                `}
                            >
                                <RotateCcw className="h-3 w-3" />
                                재시도
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* 차원 연결 포인트 */}
            <div className="flex gap-4 mt-3">
                <div className={`h-2 w-2 rounded-full ${colorScheme.bg} ${colorScheme.border} border`} />
                <div className={`h-1 w-8 rounded-full bg-gradient-to-r ${colorScheme.bg}`} />
                <div className={`h-2 w-2 rounded-full ${colorScheme.bg} ${colorScheme.border} border`} />
            </div>
        </motion.div>
    );
}
