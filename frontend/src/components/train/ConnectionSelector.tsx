"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles,
    LayoutGrid,
    Image as ImageIcon,
    Film,
    ChevronRight,
    Compass,
    RefreshCw
} from "lucide-react";

interface ConnectionOption {
    id: string;
    label: string;
    description: string;
    recommendedToolId: string;
    icon: string;
    color: string;
    confidence: number;
}

interface ConnectionSelectorProps {
    options: ConnectionOption[];
    onSelect: (optionId: string) => void;
    onReRecommend?: () => void;
    isLoading?: boolean;
}

const ICON_MAP: Record<string, React.ReactNode> = {
    sparkles: <Sparkles className="h-5 w-5" />,
    "layout-grid": <LayoutGrid className="h-5 w-5" />,
    image: <ImageIcon className="h-5 w-5" />,
    film: <Film className="h-5 w-5" />,
};

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; hover: string }> = {
    violet: {
        bg: "bg-violet-500/10",
        border: "border-violet-500/30",
        text: "text-violet-400",
        hover: "hover:bg-violet-500/20 hover:border-violet-500/50",
    },
    emerald: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
        text: "text-emerald-400",
        hover: "hover:bg-emerald-500/20 hover:border-emerald-500/50",
    },
    amber: {
        bg: "bg-amber-500/10",
        border: "border-amber-500/30",
        text: "text-amber-400",
        hover: "hover:bg-amber-500/20 hover:border-amber-500/50",
    },
    cyan: {
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/30",
        text: "text-cyan-400",
        hover: "hover:bg-cyan-500/20 hover:border-cyan-500/50",
    },
    lime: {
        bg: "bg-lime-400/10",
        border: "border-lime-400/30",
        text: "text-lime-400",
        hover: "hover:bg-lime-400/20 hover:border-lime-400/50",
    },
};

export function ConnectionSelector({
    options,
    onSelect,
    onReRecommend,
    isLoading = false,
}: ConnectionSelectorProps) {
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    return (
        <div className="flex flex-col items-center gap-4">
            {/* 차원문 포털 심볼 */}
            <div className="flex items-center gap-2">
                <div className="h-px w-8 bg-gradient-to-r from-transparent via-violet-500/50 to-zinc-600" />
                <motion.div
                    animate={{ scale: [1, 1.15, 1], rotate: [0, 180, 360] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="h-10 w-10 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-500/20 border-2 border-violet-500/40 flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)]"
                >
                    <Compass className="h-5 w-5 text-violet-400" />
                </motion.div>
                <div className="h-px w-8 bg-gradient-to-l from-transparent via-violet-500/50 to-zinc-600" />
            </div>

            {/* 3개 옵션 카드 */}
            <div className="flex flex-col gap-2 w-56">
                <AnimatePresence mode="wait">
                    {isLoading ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col gap-2"
                        >
                            {[1, 2, 3].map((i) => (
                                <div
                                    key={i}
                                    className="h-16 rounded-xl bg-zinc-800/50 animate-pulse"
                                />
                            ))}
                        </motion.div>
                    ) : (
                        options.map((option, index) => {
                            const colorScheme = COLOR_MAP[option.color] || COLOR_MAP.violet;
                            const IconComponent = ICON_MAP[option.icon] || <Sparkles className="h-5 w-5" />;
                            const isHovered = hoveredId === option.id;

                            return (
                                <motion.button
                                    key={option.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    onClick={() => onSelect(option.id)}
                                    onMouseEnter={() => setHoveredId(option.id)}
                                    onMouseLeave={() => setHoveredId(null)}
                                    className={`
                                        relative flex items-center gap-3 p-3 rounded-xl
                                        ${colorScheme.bg} ${colorScheme.border} border
                                        ${colorScheme.hover}
                                        transition-all duration-300
                                        group cursor-pointer
                                    `}
                                >
                                    {/* 옵션 번호 */}
                                    <div className="absolute -left-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full bg-zinc-900 border border-zinc-700 flex items-center justify-center text-[10px] font-bold text-zinc-400">
                                        {index + 1}
                                    </div>

                                    {/* 아이콘 */}
                                    <div className={`${colorScheme.text}`}>
                                        {IconComponent}
                                    </div>

                                    {/* 텍스트 */}
                                    <div className="flex-1 text-left">
                                        <p className="text-sm font-medium text-white truncate">
                                            {option.label}
                                        </p>
                                        <p className="text-[10px] text-zinc-500 truncate">
                                            {option.description}
                                        </p>
                                    </div>

                                    {/* 신뢰도 + 화살표 */}
                                    <div className="flex items-center gap-1">
                                        <span className="text-[10px] text-zinc-500">
                                            {Math.round(option.confidence * 100)}%
                                        </span>
                                        <ChevronRight
                                            className={`
                                                h-4 w-4 text-zinc-500
                                                transition-transform duration-300
                                                ${isHovered ? "translate-x-1 text-white" : ""}
                                            `}
                                        />
                                    </div>
                                </motion.button>
                            );
                        })
                    )}
                </AnimatePresence>
            </div>

            {/* 재추천 버튼 */}
            {onReRecommend && !isLoading && (
                <button
                    onClick={onReRecommend}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800/50 border border-zinc-700 text-zinc-400 text-xs hover:bg-zinc-800 hover:text-white transition-all"
                >
                    <RefreshCw className="h-3 w-3" />
                    다른 차원 탐색
                </button>
            )}
        </div>
    );
}
