"use client";

/**
 * Create Request Page
 * 
 * Form for clients to create creative requests.
 */

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    FileText,
    DollarSign,
    Calendar,
    Send,
    Loader2,
    AlertCircle,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

const CATEGORIES = [
    { value: "video_creative", label: "Video Creative", labelKo: "영상 크리에이티브" },
    { value: "image_design", label: "Image Design", labelKo: "이미지 디자인" },
    { value: "motion_graphics", label: "Motion Graphics", labelKo: "모션 그래픽" },
    { value: "short_form", label: "Short-form Content", labelKo: "숏폼 콘텐츠" },
    { value: "brand_content", label: "Brand Content", labelKo: "브랜드 콘텐츠" },
];

export default function CreateRequestPage() {
    const router = useRouter();
    const { language } = useLanguage();

    const [formData, setFormData] = useState({
        title: "",
        description: "",
        category: "video_creative",
        budget_credits: 1000,
        deadline: "",
    });
    const [isPending, startTransition] = useTransition();
    const [error, setError] = useState<string | null>(null);

    const labels = {
        title: language === "ko" ? "의뢰 등록" : "Create Request",
        backTo: language === "ko" ? "Human Cloud로 돌아가기" : "Back to Human Cloud",
        requestTitle: language === "ko" ? "의뢰 제목" : "Request Title",
        requestTitlePlaceholder: language === "ko" ? "예: 브랜드 광고 영상 30초" : "e.g., 30-second brand ad video",
        description: language === "ko" ? "상세 설명" : "Description",
        descriptionPlaceholder: language === "ko"
            ? "원하는 스타일, 톤, 참고 영상, 특별 요청사항 등을 자세히 적어주세요..."
            : "Describe the style, tone, reference videos, and any special requirements...",
        category: language === "ko" ? "카테고리" : "Category",
        budget: language === "ko" ? "예산 (크레딧)" : "Budget (Credits)",
        deadline: language === "ko" ? "마감일 (선택)" : "Deadline (Optional)",
        submit: language === "ko" ? "의뢰 등록하기" : "Submit Request",
        submitting: language === "ko" ? "등록 중..." : "Submitting...",
        budgetNote: language === "ko"
            ? "크리에이터에게 75%, 플랫폼 25% 배분됩니다"
            : "75% goes to creator, 25% platform fee",
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title || !formData.description) return;

        setError(null);

        startTransition(async () => {
            try {
                const payload: Record<string, unknown> = {
                    title: formData.title,
                    description: formData.description,
                    category: formData.category,
                    budget_credits: formData.budget_credits,
                };
                if (formData.deadline) {
                    payload.deadline = new Date(formData.deadline).toISOString();
                }

                const result = await fetchWithAuth("/api/v1/humancloud/requests", {
                    method: "POST",
                    body: JSON.stringify(payload),
                }) as { id: string };

                // Redirect to request detail or publish
                router.push(`/humancloud/requests/${result.id}`);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to create request");
            }
        });
    };

    return (
        <AppShell showTopBar={false}>
            <AuroraBackground />
            <div className="min-h-screen relative px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-2xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6"
                    >
                        <button
                            onClick={() => router.push("/humancloud")}
                            className="flex items-center gap-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] mb-4 transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            {labels.backTo}
                        </button>
                        <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl flex items-center gap-2">
                            <FileText className="w-6 h-6 text-violet-400" />
                            {labels.title}
                        </h1>
                    </motion.div>

                    {/* Error */}
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                            <p className="text-red-300">{error}</p>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Title */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-2">
                                {labels.requestTitle}
                            </label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                placeholder={labels.requestTitlePlaceholder}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg 
                                    text-white placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                                required
                            />
                        </div>

                        {/* Description */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-2">
                                {labels.description}
                            </label>
                            <textarea
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                placeholder={labels.descriptionPlaceholder}
                                rows={6}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg 
                                    text-white placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 resize-none"
                                required
                            />
                        </div>

                        {/* Category */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-3">
                                {labels.category}
                            </label>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {CATEGORIES.map((cat) => (
                                    <button
                                        key={cat.value}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, category: cat.value })}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                                            ${formData.category === cat.value
                                                ? "bg-violet-600 text-white"
                                                : "bg-slate-800 text-[var(--fg-muted)] hover:bg-slate-700"
                                            }`}
                                    >
                                        {language === "ko" ? cat.labelKo : cat.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Budget & Deadline */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="card-glass p-5">
                                <label className="block text-sm font-medium text-[var(--fg-0)] mb-2 flex items-center gap-2">
                                    <DollarSign className="w-4 h-4 text-emerald-400" />
                                    {labels.budget}
                                </label>
                                <input
                                    type="number"
                                    value={formData.budget_credits}
                                    onChange={(e) => setFormData({ ...formData, budget_credits: parseInt(e.target.value) || 0 })}
                                    min={100}
                                    step={100}
                                    className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg 
                                        text-white focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                                    required
                                />
                                <p className="text-xs text-slate-500 mt-2">{labels.budgetNote}</p>
                            </div>

                            <div className="card-glass p-5">
                                <label className="block text-sm font-medium text-[var(--fg-0)] mb-2 flex items-center gap-2">
                                    <Calendar className="w-4 h-4 text-blue-400" />
                                    {labels.deadline}
                                </label>
                                <input
                                    type="date"
                                    value={formData.deadline}
                                    onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                                    className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg 
                                        text-white focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                                />
                            </div>
                        </div>

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={isPending || !formData.title || !formData.description}
                            className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-violet-600
                                hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed
                                text-white font-medium rounded-xl transition-colors"
                        >
                            {isPending ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    {labels.submitting}
                                </>
                            ) : (
                                <>
                                    <Send className="w-5 h-5" />
                                    {labels.submit}
                                </>
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </AppShell>
    );
}
