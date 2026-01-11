"use client";

import { useState } from "react";
import { Star } from "lucide-react";
import { motion } from "framer-motion";

interface StarRatingProps {
    value: number;
    onChange?: (value: number) => void;
    readonly?: boolean;
    size?: "sm" | "md" | "lg";
    showCount?: boolean;
    count?: number;
}

const sizeMap = {
    sm: "h-3 w-3",
    md: "h-5 w-5",
    lg: "h-6 w-6",
};

export function StarRating({
    value,
    onChange,
    readonly = false,
    size = "md",
    showCount = false,
    count,
}: StarRatingProps) {
    const [hoverValue, setHoverValue] = useState(0);
    const displayValue = hoverValue || value;

    return (
        <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
                <motion.button
                    key={star}
                    type="button"
                    disabled={readonly}
                    onClick={() => !readonly && onChange?.(star)}
                    onMouseEnter={() => !readonly && setHoverValue(star)}
                    onMouseLeave={() => setHoverValue(0)}
                    whileHover={!readonly ? { scale: 1.2 } : undefined}
                    whileTap={!readonly ? { scale: 0.9 } : undefined}
                    className={`${readonly ? "cursor-default" : "cursor-pointer"} focus:outline-none`}
                >
                    <Star
                        className={`${sizeMap[size]} transition-colors ${star <= displayValue
                                ? "fill-amber-400 text-amber-400"
                                : "fill-transparent text-slate-400 dark:text-slate-600"
                            }`}
                    />
                </motion.button>
            ))}
            {showCount && typeof count === "number" && (
                <span className="ml-1 text-xs text-slate-500 dark:text-slate-400">
                    ({count})
                </span>
            )}
        </div>
    );
}

interface RatingModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (rating: number, feedback: string) => Promise<void>;
    templateTitle: string;
}

export function RatingModal({
    isOpen,
    onClose,
    onSubmit,
    templateTitle,
}: RatingModalProps) {
    const [rating, setRating] = useState(0);
    const [feedback, setFeedback] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (rating === 0) return;
        setIsSubmitting(true);
        try {
            await onSubmit(rating, feedback);
            onClose();
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative z-10 w-full max-w-md mx-4 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-2xl"
            >
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
                    템플릿이 도움이 되셨나요?
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                    &quot;{templateTitle}&quot; 템플릿을 평가해주세요
                </p>

                {/* Star Rating */}
                <div className="flex justify-center mb-4">
                    <StarRating value={rating} onChange={setRating} size="lg" />
                </div>

                {/* Feedback */}
                <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="피드백을 남겨주세요 (선택)"
                    className="w-full px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 resize-none h-24 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />

                {/* Actions */}
                <div className="flex gap-3 mt-4">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    >
                        건너뛰기
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={rating === 0 || isSubmitting}
                        className="flex-1 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {isSubmitting ? "제출 중..." : "평가하기"}
                    </button>
                </div>
            </motion.div>
        </div>
    );
}
