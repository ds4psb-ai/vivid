"use client";

/**
 * FeedbackButtons - Feedback collection component for P6 RAG Feedback system
 *
 * Features:
 * - Thumbs up/down buttons
 * - Optional 1-5 star rating
 * - Optional comment input
 * - Compact mode for inline use
 * - Theme color support
 * - Optimistic UI updates
 */

import { useState, useCallback } from "react";
import { ThumbsUp, ThumbsDown, MessageSquare, Send, Check, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { type ThemeColor, THEME_COLOR_CLASSES } from "@/lib/dimension-theme";
import { StarRating } from "@/components/ui/StarRating";

export type FeedbackType = "positive" | "negative";

export interface FeedbackButtonsProps {
    /** P6 RAGResponse ID */
    responseId: string;
    /** Callback when feedback is submitted */
    onFeedback?: (type: FeedbackType, rating?: number, comment?: string) => Promise<void>;
    /** Show 1-5 star rating */
    showRating?: boolean;
    /** Show comment input */
    showComment?: boolean;
    /** Disabled state */
    disabled?: boolean;
    /** Compact mode (inline) */
    compact?: boolean;
    /** Theme color */
    themeColor?: ThemeColor;
    /** Initial feedback state (if already submitted) */
    initialFeedback?: FeedbackType | null;
}

export default function FeedbackButtons({
    responseId: _responseId,
    onFeedback,
    showRating = false,
    showComment = false,
    disabled = false,
    compact = false,
    themeColor = "emerald",
    initialFeedback = null,
}: FeedbackButtonsProps) {
    const [selectedType, setSelectedType] = useState<FeedbackType | null>(initialFeedback);
    const [rating, setRating] = useState(0);
    const [comment, setComment] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [hasSubmitted, setHasSubmitted] = useState(!!initialFeedback);
    const [showExtended, setShowExtended] = useState(false);
    const colors = THEME_COLOR_CLASSES[themeColor];

    const handleFeedback = useCallback(
        async (type: FeedbackType) => {
            if (disabled || isSubmitting) return;

            // If already selected the same type, unselect
            if (selectedType === type && !hasSubmitted) {
                setSelectedType(null);
                setShowExtended(false);
                return;
            }

            setSelectedType(type);

            // If no extended options, submit immediately
            if (!showRating && !showComment) {
                setIsSubmitting(true);
                try {
                    await onFeedback?.(type);
                    setHasSubmitted(true);
                } catch (error) {
                    console.error("Feedback submission failed:", error);
                    setSelectedType(null);
                } finally {
                    setIsSubmitting(false);
                }
            } else {
                // Show extended options
                setShowExtended(true);
            }
        },
        [disabled, isSubmitting, selectedType, hasSubmitted, showRating, showComment, onFeedback]
    );

    const handleSubmitExtended = useCallback(async () => {
        if (!selectedType || isSubmitting) return;

        setIsSubmitting(true);
        try {
            await onFeedback?.(selectedType, rating > 0 ? rating : undefined, comment.trim() || undefined);
            setHasSubmitted(true);
            setShowExtended(false);
        } catch (error) {
            console.error("Feedback submission failed:", error);
        } finally {
            setIsSubmitting(false);
        }
    }, [selectedType, rating, comment, onFeedback, isSubmitting]);

    const handleSkip = useCallback(() => {
        setShowExtended(false);
        setSelectedType(null);
    }, []);

    // Compact mode - just two buttons
    if (compact) {
        return (
            <div className="flex items-center gap-2">
                {hasSubmitted ? (
                    <div className="flex items-center gap-1.5 text-xs text-white/50">
                        <Check className="w-3.5 h-3.5" />
                        <span>피드백 완료</span>
                    </div>
                ) : (
                    <>
                        <button
                            onClick={() => handleFeedback("positive")}
                            disabled={disabled || isSubmitting}
                            className={`p-1.5 rounded-lg transition-all ${
                                selectedType === "positive"
                                    ? "bg-emerald-500/20 text-emerald-400"
                                    : "text-slate-400 dark:text-white/40 hover:text-emerald-400 hover:bg-emerald-500/10"
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            {isSubmitting && selectedType === "positive" ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <ThumbsUp className="w-4 h-4" />
                            )}
                        </button>
                        <button
                            onClick={() => handleFeedback("negative")}
                            disabled={disabled || isSubmitting}
                            className={`p-1.5 rounded-lg transition-all ${
                                selectedType === "negative"
                                    ? "bg-rose-500/20 text-rose-400"
                                    : "text-slate-400 dark:text-white/40 hover:text-rose-400 hover:bg-rose-500/10"
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            {isSubmitting && selectedType === "negative" ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <ThumbsDown className="w-4 h-4" />
                            )}
                        </button>
                    </>
                )}
            </div>
        );
    }

    // Full mode
    return (
        <div className={`rounded-xl ${colors.bg} border ${colors.border} overflow-hidden`}>
            {/* Main Feedback Buttons */}
            <div className="p-4">
                {hasSubmitted ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex items-center justify-center gap-2 py-2"
                    >
                        <div className={`p-2 rounded-full ${selectedType === "positive" ? "bg-emerald-500/20" : "bg-rose-500/20"}`}>
                            {selectedType === "positive" ? (
                                <ThumbsUp className="w-5 h-5 text-emerald-400" />
                            ) : (
                                <ThumbsDown className="w-5 h-5 text-rose-400" />
                            )}
                        </div>
                        <span className={`text-sm font-medium ${colors.text}`}>
                            피드백 감사합니다!
                        </span>
                    </motion.div>
                ) : (
                    <>
                        <p className="text-xs text-slate-500 dark:text-white/50 mb-3 text-center">
                            이 답변이 도움이 되었나요?
                        </p>
                        <div className="flex items-center justify-center gap-3">
                            <button
                                onClick={() => handleFeedback("positive")}
                                disabled={disabled || isSubmitting}
                                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl transition-all font-medium text-sm
                                    ${selectedType === "positive"
                                        ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                                        : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                            >
                                {isSubmitting && selectedType === "positive" ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <ThumbsUp className="w-4 h-4" />
                                )}
                                <span>도움됨</span>
                            </button>
                            <button
                                onClick={() => handleFeedback("negative")}
                                disabled={disabled || isSubmitting}
                                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl transition-all font-medium text-sm
                                    ${selectedType === "negative"
                                        ? "bg-rose-500 text-white shadow-lg shadow-rose-500/20"
                                        : "bg-rose-500/10 text-rose-400 hover:bg-rose-500/20"
                                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                            >
                                {isSubmitting && selectedType === "negative" ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <ThumbsDown className="w-4 h-4" />
                                )}
                                <span>아쉬움</span>
                            </button>
                        </div>
                    </>
                )}
            </div>

            {/* Extended Options */}
            <AnimatePresence>
                {showExtended && !hasSubmitted && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-slate-200 dark:border-white/10 overflow-hidden"
                    >
                        <div className="p-4 space-y-4 bg-white/50 dark:bg-white/[0.02]">
                            {/* Star Rating */}
                            {showRating && (
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-slate-500 dark:text-white/50">
                                        평점 (선택)
                                    </label>
                                    <StarRating
                                        value={rating}
                                        onChange={setRating}
                                        size="md"
                                    />
                                </div>
                            )}

                            {/* Comment Input */}
                            {showComment && (
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-slate-500 dark:text-white/50">
                                        의견 (선택)
                                    </label>
                                    <div className="relative">
                                        <textarea
                                            value={comment}
                                            onChange={(e) => setComment(e.target.value)}
                                            placeholder="더 나은 서비스를 위해 의견을 남겨주세요..."
                                            maxLength={2000}
                                            className="w-full px-4 py-3 pr-10 rounded-xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-white/30 text-sm resize-none h-20 focus:outline-none focus:border-slate-300 dark:focus:border-white/20 transition-colors"
                                        />
                                        <MessageSquare className="absolute right-3 top-3 w-4 h-4 text-slate-300 dark:text-white/20" />
                                    </div>
                                    <p className="text-[10px] text-slate-400 dark:text-white/30 text-right">
                                        {comment.length}/2000
                                    </p>
                                </div>
                            )}

                            {/* Submit / Skip Buttons */}
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSkip}
                                    className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-white/10 text-slate-500 dark:text-white/50 text-sm hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                                >
                                    건너뛰기
                                </button>
                                <button
                                    onClick={handleSubmitExtended}
                                    disabled={isSubmitting}
                                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-white text-sm font-medium transition-all
                                        ${selectedType === "positive"
                                            ? "bg-emerald-500 hover:bg-emerald-400"
                                            : "bg-rose-500 hover:bg-rose-400"
                                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                                >
                                    {isSubmitting ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <>
                                            <Send className="w-4 h-4" />
                                            <span>제출</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
