"use client";

import { useState } from "react";
import { Star } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

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
                    aria-label={`${star}점 평가`}
                    aria-pressed={value >= star}
                    className={`${readonly ? "cursor-default" : "cursor-pointer"} focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 rounded-sm`}
                >
                    <Star
                        className={`${sizeMap[size]} transition-colors ${star <= displayValue
                                ? "fill-[var(--warning)] text-[var(--warning)]"
                                : "fill-transparent text-[var(--fg-muted)]"
                            }`}
                    />
                </motion.button>
            ))}
            {showCount && typeof count === "number" && (
                <span className="ml-1 text-xs text-[var(--fg-muted)]">
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
                className="absolute inset-0 dialog-overlay"
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                role="dialog"
                aria-modal="true"
                aria-labelledby="rating-modal-title"
                className="relative z-10 w-full max-w-md mx-4 p-6 dialog-panel"
            >
                <h3 id="rating-modal-title" className="text-lg font-bold text-[var(--fg-0)] mb-2">
                    템플릿이 도움이 되셨나요?
                </h3>
                <p className="text-sm text-[var(--fg-muted)] mb-4">
                    &quot;{templateTitle}&quot; 템플릿을 평가해주세요
                </p>

                {/* Star Rating */}
                <div className="flex justify-center mb-4">
                    <StarRating value={rating} onChange={setRating} size="lg" />
                </div>

                {/* Feedback */}
                <label htmlFor="rating-feedback" className="sr-only">피드백</label>
                <textarea
                    id="rating-feedback"
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="피드백을 남겨주세요 (선택)"
                    className="input w-full resize-none h-24"
                />

                {/* Actions */}
                <div className="flex gap-3 mt-4">
                    <Button
                        type="button"
                        onClick={onClose}
                        variant="secondary"
                        className="flex-1"
                    >
                        건너뛰기
                    </Button>
                    <Button
                        type="button"
                        onClick={handleSubmit}
                        disabled={rating === 0 || isSubmitting}
                        className="flex-1"
                    >
                        {isSubmitting ? "제출 중..." : "평가하기"}
                    </Button>
                </div>
            </motion.div>
        </div>
    );
}
