"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    X,
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    Sparkles,
    LayoutGrid,
    Image as ImageIcon,
    Film,
    CheckCircle,
    Palette,
    Moon,
    Video,
    Play,
    Loader2,
    Copy,
    Check,
    ExternalLink,
    Keyboard,
    RotateCcw,
    Eye,
    AlertCircle,
} from "lucide-react";
import { api, DimensionResponse } from "@/lib/api";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig, type InputFieldConfig } from "@/contexts/DimensionConfigContext";
import { dimensionIdToCode, getDimensionGradient, getDimensionToken } from "@/lib/tokens";
import type { DimensionType } from "@/lib/dimension-types";

// =============================================================================
// Types
// =============================================================================

// DimensionType shared in lib/dimension-types
type CarStatus = "pending" | "ready" | "executing" | "completed" | "failed";

interface Car {
    id: string;
    order: number;
    toolId: string;
    dimension: DimensionType;
    displayName: string;
    icon: string;
    color: string;
    status: CarStatus;
    inputs: Record<string, unknown>;
    output?: Record<string, unknown>;
    error?: string;
    creditCost?: number;
}

interface DimensionPortalModalProps {
    isOpen: boolean;
    onClose: () => void;
    cars: Car[];
    currentCarId: string;
    onNavigate: (carId: string) => void;
    onInputChange: (carId: string, inputs: Record<string, unknown>) => void;
    onExecute: (carId: string) => void;
    onOutputUpdate: (carId: string, output: Record<string, unknown>, creditCost?: number) => void;
    onStatusChange: (carId: string, status: CarStatus, error?: string) => void;
}

// =============================================================================
// Constants
// =============================================================================

const ICON_MAP: Record<string, React.ReactNode> = {
    sparkles: <Sparkles className="h-6 w-6" />,
    "layout-grid": <LayoutGrid className="h-6 w-6" />,
    image: <ImageIcon className="h-6 w-6" />,
    film: <Film className="h-6 w-6" />,
    "check-circle": <CheckCircle className="h-6 w-6" />,
    palette: <Palette className="h-6 w-6" />,
    moon: <Moon className="h-6 w-6" />,
    video: <Video className="h-6 w-6" />,
    eye: <Eye className="h-6 w-6" />,
};

const getGradientStops = (dimension: string | undefined) => {
    if (!dimension) return null;
    const code = dimensionIdToCode(dimension);
    if (!code) return null;
    const gradient = getDimensionGradient(code);
    return gradient.replace("bg-gradient-to-r ", "");
};

const getDimensionColorClasses = (dimension?: string) => {
    if (!dimension) return null;
    const code = dimensionIdToCode(dimension);
    if (!code) return null;
    const token = getDimensionToken(code);
    const key = token.tailwindKey;
    return {
        bg: `bg-${key}/10`,
        bgSolid: `bg-${key}`,
        border: `border-${key}/30`,
        text: `text-${key}`,
        gradient: getGradientStops(dimension) ?? "from-violet-600 to-purple-600",
        glow: `shadow-[0_0_60px_var(--tw-shadow-color)] shadow-${key}/30`,
    };
};

const getDimensionFocusClass = (dimension?: string) => {
    if (!dimension) return null;
    const code = dimensionIdToCode(dimension);
    if (!code) return null;
    const token = getDimensionToken(code);
    const key = token.tailwindKey;
    return `focus:border-${key}/50 focus:ring-${key}/10`;
};

const getHoverGlowClass = (dimension?: string) => {
    if (!dimension) return "";
    const code = dimensionIdToCode(dimension);
    if (!code) return "";
    const key = getDimensionToken(code).tailwindKey;
    return `hover:shadow-${key}/30`;
};

const STATUS_TONE_CLASSES: Record<"success" | "error", { bg: string; border: string; text: string }> = {
    success: {
        bg: "bg-[var(--success)]/10",
        border: "border-[var(--success)]/30",
        text: "text-[var(--success)]",
    },
    error: {
        bg: "bg-[var(--error)]/10",
        border: "border-[var(--error)]/30",
        text: "text-[var(--error)]",
    },
};

const PROGRESS_TONE_CLASSES: Record<"success" | "error", string> = {
    success: "bg-[var(--success)]/60",
    error: "bg-[var(--error)]/40",
};

// Dimension-specific form configurations
const _DIMENSION_CONFIG: Partial<Record<DimensionType, {
    title: string;
    description: string;
    apiEndpoint: string;
    creditCost: number;
    inputFields: Array<{
        key: string;
        label: string;
        type: "text" | "textarea" | "select" | "toggle";
        placeholder?: string;
        options?: Array<{ value: string; label: string }>;
        required?: boolean;
    }>;
}>> = {
    "1D": {
        title: "프롬프트",
        description: "아이디어를 언어로 구체화",
        apiEndpoint: "/api/dimension/1d/generate",
        creditCost: 5,
        inputFields: [
            { key: "topic", label: "주제", type: "textarea", placeholder: "영상의 핵심 주제를 입력하세요...", required: true },
            {
                key: "style", label: "스타일", type: "select", options: [
                    { value: "cinematic", label: "시네마틱" },
                    { value: "documentary", label: "다큐멘터리" },
                    { value: "commercial", label: "광고/커머셜" },
                    { value: "artistic", label: "아트/실험" },
                ]
            },
            {
                key: "mood", label: "무드", type: "select", options: [
                    { value: "neutral", label: "중립" },
                    { value: "dramatic", label: "드라마틱" },
                    { value: "calm", label: "차분함" },
                    { value: "energetic", label: "에너지틱" },
                ]
            },
        ],
    },
    "2D": {
        title: "스토리보드",
        description: "전체 흐름 설계",
        apiEndpoint: "/api/dimension/2d/create",
        creditCost: 10,
        inputFields: [
            { key: "concept", label: "컨셉", type: "textarea", placeholder: "스토리보드로 만들 컨셉을 입력하세요", required: true },
            {
                key: "scene_count", label: "장면 수", type: "select", options: [
                    { value: "3", label: "3장면" },
                    { value: "5", label: "5장면" },
                    { value: "7", label: "7장면" },
                    { value: "10", label: "10장면" },
                ]
            },
        ],
    },
    "3D": {
        title: "비주얼",
        description: "시각적 디테일 완성",
        apiEndpoint: "/api/dimension/3d/generate",
        creditCost: 10,
        inputFields: [
            { key: "description", label: "장면 설명", type: "textarea", placeholder: "시각화할 장면을 설명하세요", required: true },
            {
                key: "aspect_ratio", label: "화면 비율", type: "select", options: [
                    { value: "16:9", label: "16:9 (와이드)" },
                    { value: "9:16", label: "9:16 (세로)" },
                    { value: "1:1", label: "1:1 (정방형)" },
                ]
            },
        ],
    },
    "4D": {
        title: "레퍼런스",
        description: "참고 영상 심층 분석",
        apiEndpoint: "/api/dimension/4d/analyze",
        creditCost: 10,
        inputFields: [
            { key: "video_description", label: "영상 설명", type: "textarea", placeholder: "분석할 레퍼런스 영상을 설명하세요", required: true },
            {
                key: "focus_areas", label: "분석 초점", type: "select", options: [
                    { value: "composition", label: "구도" },
                    { value: "lighting", label: "조명" },
                    { value: "color", label: "색감" },
                    { value: "movement", label: "움직임" },
                ]
            },
        ],
    },
    "QC": {
        title: "퀄리티",
        description: "6가지 기준 품질 검증",
        apiEndpoint: "/api/dimension/quality/check",
        creditCost: 8,
        inputFields: [
            { key: "content", label: "검수 대상", type: "textarea", placeholder: "품질 검수할 콘텐츠를 입력하세요", required: true },
            {
                key: "content_type", label: "타입", type: "select", options: [
                    { value: "prompt", label: "프롬프트" },
                    { value: "storyboard", label: "스토리보드" },
                    { value: "general", label: "일반" },
                ]
            },
        ],
    },
    "AD": {
        title: "디렉팅",
        description: "거장들의 미학 적용",
        apiEndpoint: "/api/dimension/aesthetic/direct",
        creditCost: 10,
        inputFields: [
            { key: "concept", label: "컨셉", type: "textarea", placeholder: "미학 방향을 설정할 컨셉", required: true },
            {
                key: "reference_style", label: "감독 스타일", type: "select", options: [
                    { value: "bong", label: "봉준호" },
                    { value: "park", label: "박찬욱" },
                    { value: "shinkai", label: "신카이 마코토" },
                    { value: "nolan", label: "크리스토퍼 놀란" },
                ]
            },
        ],
    },
    "AI": {
        title: "심연",
        description: "내면의 운명 해석",
        apiEndpoint: "/api/dimension/persona/analyze",
        creditCost: 12,
        inputFields: [
            { key: "user_message", label: "분석 대상", type: "textarea", placeholder: "분석할 주제나 대상을 설명하세요", required: true },
            {
                key: "depth_level", label: "분석 깊이", type: "select", options: [
                    { value: "quick", label: "빠른 분석" },
                    { value: "standard", label: "표준" },
                    { value: "comprehensive", label: "심층" },
                ]
            },
        ],
    },
    "VEO": {
        title: "비디오",
        description: "최종 AI 영상 생성",
        apiEndpoint: "/api/dimension/veo/generate",
        creditCost: 20,
        inputFields: [
            { key: "prompt", label: "비디오 프롬프트", type: "textarea", placeholder: "생성할 비디오를 설명하세요", required: true },
            {
                key: "duration", label: "길이", type: "select", options: [
                    { value: "4", label: "4초" },
                    { value: "6", label: "6초" },
                    { value: "8", label: "8초" },
                ]
            },
            {
                key: "aspect_ratio", label: "화면 비율", type: "select", options: [
                    { value: "16:9", label: "16:9" },
                    { value: "9:16", label: "9:16" },
                    { value: "1:1", label: "1:1" },
                ]
            },
        ],
    },
};

const DIMENSION_ROUTES: Partial<Record<DimensionType, string>> = {
    "1D": "/dimension/prompt",
    "2D": "/dimension/storyboard",
    "3D": "/dimension/visual-realizer",
    "4D": "/dimension/reference-decoder",
    "QC": "/dimension/quality-check",
    "AD": "/dimension/aesthetic",
    "AI": "/dimension/abyss",
    "VEO": "/dimension/video-maker",
    "STORY": "/dimension/story-architect",
    "STORYBOARD": "/dimension/storyboard",
    "SOUND": "/dimension/sound-crafter",
    "SUNO": "/dimension/suno",
    "KLING": "/dimension/kling",
    "CHARACTER": "/dimension/character-consistency",
    "PROMPT": "/dimension/prompt-alchemy",
    "MIRROR": "/dimension/abyss",
    "SA": "/dimension/story-architect",
    "SC": "/dimension/sound-crafter",
};

// =============================================================================
// Component
// =============================================================================

export function DimensionPortalModal({
    isOpen,
    onClose,
    cars,
    currentCarId,
    onNavigate,
    onInputChange,
    onOutputUpdate,
    onStatusChange,
}: DimensionPortalModalProps) {
    // Safe car lookup with fallback
    const currentIndex = cars.findIndex(c => c.id === currentCarId);
    const currentCar = currentIndex >= 0 ? cars[currentIndex] : null;
    const hasPrev = currentIndex > 0;
    const hasNext = currentIndex >= 0 && currentIndex < cars.length - 1;

    // Local form state
    const [localInputs, setLocalInputs] = useState<Record<string, unknown>>({});
    const [isExecuting, setIsExecuting] = useState(false);
    const [copiedField, setCopiedField] = useState<string | null>(null);
    const [showKeyboardHints, setShowKeyboardHints] = useState(false);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    // SSoT: Get tool config and input fields from context
    const { getToolByDimension, getInputFieldsByDimension } = useDimensionConfig();
    const toolConfig = currentCar ? getToolByDimension(currentCar.dimension) : undefined;
    const inputFields = useMemo(
        () => (currentCar ? getInputFieldsByDimension(currentCar.dimension) : []),
        [currentCar, getInputFieldsByDimension]
    );

    // Sync local inputs with car inputs when car changes
    useEffect(() => {
        if (currentCar) {
            setLocalInputs({ ...currentCar.inputs });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentCar?.id]);

    // Also sync when car inputs change externally
    useEffect(() => {
        if (currentCar && JSON.stringify(currentCar.inputs) !== JSON.stringify(localInputs)) {
            // Only sync if inputs are different (avoid infinite loop)
            const carInputKeys = Object.keys(currentCar.inputs);
            const localKeys = Object.keys(localInputs);
            if (carInputKeys.length !== localKeys.length ||
                carInputKeys.some(k => currentCar.inputs[k] !== localInputs[k])) {
                setLocalInputs({ ...currentCar.inputs });
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentCar?.inputs]);

    // Handle input change with live sync
    const handleInputChange = useCallback((key: string, value: unknown) => {
        setLocalInputs(prev => {
            const updated = { ...prev, [key]: value };
            // Live sync to parent
            if (currentCar) {
                onInputChange(currentCar.id, updated);
            }
            return updated;
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentCar?.id, onInputChange]);

    // Execute dimension
    const handleExecute = useCallback(async () => {
        if (!currentCar || !toolConfig) return;

        // Can't execute if not ready
        if (currentCar.status !== "ready" && currentCar.status !== "failed") return;

        // Validate required fields using SSoT inputFields
        const missingFields = inputFields
            .filter((f: InputFieldConfig) => f.required && !localInputs[f.key])
            .map((f: InputFieldConfig) => f.label);

        if (missingFields.length > 0) {
            onStatusChange(currentCar.id, "failed", `필수 입력: ${missingFields.join(", ")}`);
            return;
        }

        // Credit check - Use SSoT creditCost from toolConfig
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(toolConfig.creditCost)) {
            onStatusChange(currentCar.id, "failed", "크레딧이 부족합니다");
            return;
        }

        setIsExecuting(true);
        onStatusChange(currentCar.id, "executing");

        try {
            // Use SSoT endpoint from toolConfig
            const response = await api.post<DimensionResponse>(
                toolConfig.endpoint,
                localInputs,
                getBYOKHeaders(byokKey)
            );

            if (response.success && response.output) {
                onOutputUpdate(currentCar.id, response.output, toolConfig.creditCost);
                onStatusChange(currentCar.id, "completed");

                // Refresh credits
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                onStatusChange(currentCar.id, "failed", response.error || "실행 실패");
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : "알 수 없는 오류";
            onStatusChange(currentCar.id, "failed", errorMsg);
        } finally {
            setIsExecuting(false);
        }
    }, [currentCar, toolConfig, inputFields, localInputs, byokKey, creditCtx, onOutputUpdate, onStatusChange]);

    // Retry (reset to ready and execute)
    const handleRetry = useCallback(() => {
        if (!currentCar) return;
        onStatusChange(currentCar.id, "ready");
        // Execute after a brief delay to allow state update
        setTimeout(() => handleExecute(), 100);
    }, [currentCar, onStatusChange, handleExecute]);

    // Re-run (for completed status)
    const handleRerun = useCallback(() => {
        if (!currentCar) return;
        onStatusChange(currentCar.id, "ready");
    }, [currentCar, onStatusChange]);

    // Keyboard navigation
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            // Ignore if typing in input
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
                if (e.key === "Escape") {
                    (e.target as HTMLElement).blur();
                }
                return;
            }

            switch (e.key) {
                case "Escape":
                    onClose();
                    break;
                case "ArrowLeft":
                    if (hasPrev) {
                        onNavigate(cars[currentIndex - 1].id);
                    }
                    break;
                case "ArrowRight":
                    if (hasNext) {
                        onNavigate(cars[currentIndex + 1].id);
                    }
                    break;
                case "Enter":
                    if ((e.metaKey || e.ctrlKey) && currentCar?.status === "ready") {
                        handleExecute();
                    }
                    break;
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, hasPrev, hasNext, currentIndex, cars, onClose, onNavigate, currentCar?.status, handleExecute]);

    // Copy to clipboard
    const copyToClipboard = useCallback(async (text: string, field: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        } catch {
            // Silent fail
        }
    }, []);

    // Format output value
    const formatOutputValue = (value: unknown): string => {
        if (typeof value === "string") return value;
        if (typeof value === "number" || typeof value === "boolean") return String(value);
        return JSON.stringify(value, null, 2);
    };

    // Early return if no car or no config from SSoT
    if (!currentCar || !isOpen || !toolConfig) return null;

    // SSoT: Use toolConfig from context instead of hardcoded DIMENSION_CONFIG
    const tokenScheme = getDimensionColorClasses(currentCar.dimension);
    const colorClass = tokenScheme ?? getDimensionColorClasses("1d") ?? {
        bg: "bg-gray-800/10", bgSolid: "bg-gray-800", border: "border-gray-600/30",
        text: "text-gray-400", gradient: "from-gray-600 to-gray-700",
        glow: "shadow-[0_0_60px_var(--tw-shadow-color)] shadow-gray-500/30"
    };
    const focusClass = getDimensionFocusClass(currentCar.dimension) || getDimensionFocusClass("1d");
    const hoverGlowClass = getHoverGlowClass(currentCar.dimension);
    const dimensionRoute = DIMENSION_ROUTES[currentCar.dimension];
    const hasRoute = Boolean(dimensionRoute);

    // Determine button state
    const canExecute = currentCar.status === "ready" && !isExecuting;
    const canRetry = currentCar.status === "failed" && !isExecuting;
    const canRerun = currentCar.status === "completed" && !isExecuting;

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="fixed inset-0 z-50 flex items-center justify-center"
                >
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-md"
                    />

                    {/* Portal Modal */}
                    <motion.div
                        initial={{ scale: 0.85, opacity: 0, y: 30 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.9, opacity: 0, y: 20 }}
                        transition={{
                            type: "spring",
                            damping: 28,
                            stiffness: 350,
                        }}
                        className={`
                            relative w-full max-w-5xl max-h-[var(--layout-max-height-lg)] mx-4
                            bg-zinc-900/95 backdrop-blur-xl
                            border ${colorClass.border} rounded-3xl
                            ${colorClass.glow}
                            overflow-hidden flex flex-col
                        `}
                    >
                        {/* Header */}
                        <div className={`
                            flex items-center justify-between
                            px-6 py-4 border-b ${colorClass.border}
                            ${colorClass.bg}
                        `}>
                            {/* Left: Navigation */}
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={onClose}
                                    className="flex items-center gap-2 px-3 py-2 rounded-xl
                                        bg-white/5 hover:bg-white/10 border border-white/10
                                        text-white/70 hover:text-white transition-all text-sm font-medium"
                                >
                                    <ChevronLeft className="h-4 w-4" />
                                    Back to Train
                                </button>

                                {/* Dimension indicator */}
                                <div className="flex items-center gap-3">
                                    <div className={`p-2.5 rounded-xl ${colorClass.bg} ${colorClass.text} border ${colorClass.border}`}>
                                        {ICON_MAP[currentCar.icon] || <Sparkles className="h-6 w-6" />}
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-bold text-white">{toolConfig.displayName}</h2>
                                        <p className="text-xs text-zinc-500">{currentCar.dimension} · {currentIndex + 1}/{cars.length}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Right: Navigation + Actions */}
                            <div className="flex items-center gap-3">
                                {/* Keyboard hints toggle */}
                                <button
                                    onClick={() => setShowKeyboardHints(!showKeyboardHints)}
                                    className={`p-2 rounded-lg transition-colors ${showKeyboardHints
                                        ? `${colorClass.bg} ${colorClass.text}`
                                        : "text-zinc-500 hover:text-white hover:bg-white/5"
                                        }`}
                                    title="키보드 단축키"
                                >
                                    <Keyboard className="h-4 w-4" />
                                </button>

                                {/* Prev/Next Navigation */}
                                <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1">
                                    <button
                                        onClick={() => hasPrev && onNavigate(cars[currentIndex - 1].id)}
                                        disabled={!hasPrev}
                                        className={`
                                            p-2 rounded-lg transition-all
                                            ${hasPrev
                                                ? "text-white hover:bg-white/10"
                                                : "text-zinc-600 cursor-not-allowed"}
                                        `}
                                        title="이전 차원 (←)"
                                    >
                                        <ChevronLeft className="h-5 w-5" />
                                    </button>
                                    <button
                                        onClick={() => hasNext && onNavigate(cars[currentIndex + 1].id)}
                                        disabled={!hasNext}
                                        className={`
                                            p-2 rounded-lg transition-all
                                            ${hasNext
                                                ? "text-white hover:bg-white/10"
                                                : "text-zinc-600 cursor-not-allowed"}
                                        `}
                                        title="다음 차원 (→)"
                                    >
                                        <ChevronRight className="h-5 w-5" />
                                    </button>
                                </div>

                                {/* Open in full page */}
                                {hasRoute && (
                                    <a
                                        href={dimensionRoute}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl
                                            bg-white/5 hover:bg-white/10 border border-white/10
                                            text-zinc-400 hover:text-white transition-all text-xs"
                                    >
                                        <ExternalLink className="h-3.5 w-3.5" />
                                        새 탭
                                    </a>
                                )}

                                {/* Close */}
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-xl hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </div>
                        </div>

                        {/* Keyboard hints bar */}
                        <AnimatePresence>
                            {showKeyboardHints && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden border-b border-white/5"
                                >
                                    <div className="flex items-center justify-center gap-6 py-2.5 bg-white/[0.02] text-xs text-zinc-500">
                                        <span><kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-400 font-mono">←</kbd> 이전</span>
                                        <span><kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-400 font-mono">→</kbd> 다음</span>
                                        <span><kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-400 font-mono">⌘</kbd>+<kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-400 font-mono">Enter</kbd> 실행</span>
                                        <span><kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-400 font-mono">Esc</kbd> 닫기</span>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Content: Two-panel layout */}
                        <div className="flex-1 flex overflow-hidden min-h-0">
                            {/* Left Panel: Inputs */}
                            <div className="w-[var(--layout-sidebar-width)] flex-shrink-0 border-r border-white/5 bg-black/20 overflow-y-auto custom-scrollbar">
                                <div className="p-6 space-y-5">
                                    {/* Description */}
                                    <p className="text-sm text-zinc-400 leading-relaxed">
                                        {toolConfig.description}
                                    </p>

                                    {/* Input Fields */}
                                    {/* SSoT: Use inputFields from context */}
                                    {inputFields.map((field) => (
                                        <div key={field.key} className="space-y-2">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1">
                                                {field.label}
                                                {field.required && <span className={`${STATUS_TONE_CLASSES.error.text} ml-1`}>*</span>}
                                            </label>

                                            {field.type === "textarea" ? (
                                                <textarea
                                                    value={String(localInputs[field.key] || "")}
                                                    onChange={(e) => handleInputChange(field.key, e.target.value)}
                                                    placeholder={field.placeholder}
                                                    disabled={isExecuting}
                                                    className={`
                                                        w-full h-28 px-4 py-3 rounded-xl
                                                        bg-white/5 border border-white/10
                                                        text-white placeholder-white/20 text-sm
                                                        focus:outline-none focus:bg-white/[0.07] focus:ring-4
                                                        ${focusClass}
                                                        transition-all resize-none
                                                        disabled:opacity-50 disabled:cursor-not-allowed
                                                    `}
                                                />
                                            ) : field.type === "select" ? (
                                                <div className="relative">
                                                    <select
                                                        value={String(localInputs[field.key] || field.options?.[0]?.value || "")}
                                                        onChange={(e) => handleInputChange(field.key, e.target.value)}
                                                        disabled={isExecuting}
                                                        className={`
                                                            w-full px-4 py-3 rounded-xl appearance-none cursor-pointer
                                                            bg-white/5 border border-white/10
                                                            text-white text-sm
                                                            focus:outline-none ${focusClass}
                                                            transition-all disabled:opacity-50 disabled:cursor-not-allowed
                                                        `}
                                                    >
                                                        {field.options?.map((opt) => (
                                                            <option key={opt.value} value={opt.value} className="bg-zinc-900 text-white">
                                                                {opt.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30">
                                                        <ChevronDown className="h-4 w-4" />
                                                    </div>
                                                </div>
                                            ) : (
                                                <input
                                                    type="text"
                                                    value={String(localInputs[field.key] || "")}
                                                    onChange={(e) => handleInputChange(field.key, e.target.value)}
                                                    placeholder={field.placeholder}
                                                    disabled={isExecuting}
                                                    className={`
                                                        w-full px-4 py-3 rounded-xl
                                                        bg-white/5 border border-white/10
                                                        text-white placeholder-white/20 text-sm
                                                        focus:outline-none ${focusClass}
                                                        transition-all disabled:opacity-50 disabled:cursor-not-allowed
                                                    `}
                                                />
                                            )}
                                        </div>
                                    ))}

                                    {/* Action Buttons */}
                                    <div className="space-y-3 pt-2">
                                        {/* Primary Execute Button */}
                                        {canExecute && (
                                            <button
                                                onClick={handleExecute}
                                                className={`
                                                    w-full py-4 rounded-xl font-bold text-base
                                                    flex items-center justify-center gap-3
                                                    transition-all active:scale-[0.98]
                                                    bg-gradient-to-r ${colorClass.gradient} text-white
                                                    hover:shadow-lg ${hoverGlowClass}
                                                `}
                                            >
                                                <Play className="h-5 w-5" />
                                                실행하기
                                                <span className="text-xs opacity-70">({toolConfig.creditCost} 크레딧)</span>
                                            </button>
                                        )}

                                        {/* Executing State */}
                                        {isExecuting && (
                                            <button
                                                disabled
                                                className="w-full py-4 rounded-xl font-bold text-base
                                                    flex items-center justify-center gap-3
                                                    bg-zinc-800 text-zinc-400 cursor-wait"
                                            >
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                                실행 중...
                                            </button>
                                        )}

                                        {/* Completed State */}
                                        {canRerun && (
                                            <div className="space-y-2">
                                                <div className={`flex items-center justify-center gap-2 py-3 rounded-xl ${STATUS_TONE_CLASSES.success.bg} ${STATUS_TONE_CLASSES.success.text}`}>
                                                    <CheckCircle className="h-5 w-5" />
                                                    <span className="font-medium">완료됨</span>
                                                </div>
                                                <button
                                                    onClick={handleRerun}
                                                    className="w-full py-3 rounded-xl text-sm font-medium
                                                        flex items-center justify-center gap-2
                                                        bg-white/5 hover:bg-white/10 border border-white/10
                                                        text-zinc-400 hover:text-white transition-all"
                                                >
                                                    <RotateCcw className="h-4 w-4" />
                                                    다시 실행
                                                </button>
                                            </div>
                                        )}

                                        {/* Failed State with Retry */}
                                        {canRetry && (
                                            <button
                                                onClick={handleRetry}
                                                className={`w-full py-4 rounded-xl font-bold text-base flex items-center justify-center gap-3 ${STATUS_TONE_CLASSES.error.bg} ${STATUS_TONE_CLASSES.error.border} ${STATUS_TONE_CLASSES.error.text} hover:opacity-90 transition-all`}
                                            >
                                                <RotateCcw className="h-5 w-5" />
                                                재시도
                                            </button>
                                        )}

                                        {/* Pending State */}
                                        {currentCar.status === "pending" && !isExecuting && (
                                            <div className="flex items-center justify-center gap-2 py-3 rounded-xl bg-zinc-800/50 text-zinc-500">
                                                <span className="text-sm">이전 단계 완료 대기 중...</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Error display */}
                                    {currentCar.error && (
                                        <div className={`p-3 rounded-xl ${STATUS_TONE_CLASSES.error.bg} ${STATUS_TONE_CLASSES.error.border} flex items-start gap-2`}>
                                            <AlertCircle className={`h-4 w-4 ${STATUS_TONE_CLASSES.error.text} flex-shrink-0 mt-0.5`} />
                                            <span className={`${STATUS_TONE_CLASSES.error.text} text-sm`}>{currentCar.error}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Right Panel: Output */}
                            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                                {currentCar.output && Object.keys(currentCar.output).length > 0 ? (
                                    <div className="space-y-6">
                                        {Object.entries(currentCar.output).map(([key, value]) => (
                                            <div key={key} className="group">
                                                <div className="flex items-center justify-between mb-2">
                                                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                                        <span className={`w-1.5 h-1.5 rounded-full ${colorClass.bgSolid}`} />
                                                        {key.replace(/_/g, " ")}
                                                    </label>
                                                    <button
                                                        onClick={() => copyToClipboard(formatOutputValue(value), key)}
                                                        className="flex items-center gap-1 px-2 py-1 rounded-md
                                                            bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white
                                                            text-xs transition-all opacity-0 group-hover:opacity-100"
                                                    >
                                                        {copiedField === key ? (
                                                            <>
                                                                <Check className="h-3 w-3 text-[var(--success)]" />
                                                                복사됨
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Copy className="h-3 w-3" />
                                                                복사
                                                            </>
                                                        )}
                                                    </button>
                                                </div>

                                                {typeof value === "string" ? (
                                                    <div className="p-4 rounded-xl bg-black/40 border border-white/10
                                                        text-sm text-zinc-100 whitespace-pre-wrap leading-relaxed
                                                        relative overflow-hidden">
                                                        <div className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b ${colorClass.gradient}`} />
                                                        <div className="pl-3">{value}</div>
                                                    </div>
                                                ) : Array.isArray(value) ? (
                                                    <div className="space-y-2">
                                                        {value.slice(0, 10).map((item, i) => (
                                                            <div
                                                                key={i}
                                                                className="p-3 rounded-lg bg-black/30 border border-white/5 text-sm text-zinc-300"
                                                            >
                                                                {typeof item === "object" ? (
                                                                    <pre className="text-xs font-mono overflow-x-auto">
                                                                        {JSON.stringify(item, null, 2)}
                                                                    </pre>
                                                                ) : (
                                                                    String(item)
                                                                )}
                                                            </div>
                                                        ))}
                                                        {value.length > 10 && (
                                                            <p className="text-xs text-zinc-500 italic">
                                                                외 {value.length - 10}개 항목...
                                                            </p>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <pre className="p-4 rounded-xl bg-black/40 border border-white/10 text-xs font-mono text-zinc-300 overflow-x-auto">
                                                        {JSON.stringify(value, null, 2)}
                                                    </pre>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full text-center">
                                        <div className="relative mb-6">
                                            <div className={`absolute inset-0 ${colorClass.glow} blur-2xl opacity-30 rounded-full`} />
                                            <div className={`
                                                relative w-24 h-24 rounded-2xl
                                                ${colorClass.bg} border ${colorClass.border}
                                                flex items-center justify-center
                                            `}>
                                                <div className={`${colorClass.text} opacity-50`}>
                                                    {ICON_MAP[currentCar.icon] || <Sparkles className="h-6 w-6" />}
                                                </div>
                                            </div>
                                        </div>
                                        <h3 className="text-xl font-bold text-white mb-2">Ready to Generate</h3>
                                        <p className="text-sm text-zinc-500 max-w-xs">
                                            좌측 패널에서 입력을 완료하고<br />
                                            <span className={colorClass.text}>실행하기</span> 버튼을 클릭하세요
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Progress bar at bottom */}
                        <div className="flex items-center gap-1.5 px-6 py-3 border-t border-white/5 bg-black/20">
                            {cars.map((car) => {
                                const carTokenScheme = getDimensionColorClasses(car.dimension);
                                const carColor = carTokenScheme ?? getDimensionColorClasses("1d") ?? {
                                    bg: "bg-gray-800/10", bgSolid: "bg-gray-800", border: "border-gray-600/30",
                                    text: "text-gray-400", gradient: "from-gray-600 to-gray-700",
                                    glow: "shadow-[0_0_60px_var(--tw-shadow-color)] shadow-gray-500/30"
                                };
                                return (
                                    <button
                                        key={car.id}
                                        onClick={() => onNavigate(car.id)}
                                        className={`
                                            h-2 flex-1 rounded-full transition-all
                                            ${car.id === currentCarId
                                                ? carColor.bgSolid
                                                : car.status === "completed"
                                                    ? PROGRESS_TONE_CLASSES.success
                                                    : car.status === "failed"
                                                        ? PROGRESS_TONE_CLASSES.error
                                                        : "bg-white/10 hover:bg-white/20"
                                            }
                                        `}
                                        title={`${car.dimension}: ${car.displayName}`}
                                    />
                                );
                            })}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
