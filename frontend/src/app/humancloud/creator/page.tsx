"use client";

/**
 * Creator Registration Page
 * 
 * Form for users to register as creators on Human Cloud.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    UserPlus,
    Briefcase,
    Tag,
    DollarSign,
    Send,
    Loader2,
    AlertCircle,
    CheckCircle,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

const SKILL_OPTIONS = [
    "video_editing", "motion_graphics", "color_grading", "sound_design",
    "vfx", "3d_animation", "2d_animation", "ai_image", "ai_video",
    "storytelling", "branding", "short_form", "documentary",
];

const CATEGORY_OPTIONS = [
    { value: "video_creative", label: "Video Creative", labelKo: "영상 크리에이티브" },
    { value: "image_design", label: "Image Design", labelKo: "이미지 디자인" },
    { value: "motion_graphics", label: "Motion Graphics", labelKo: "모션 그래픽" },
    { value: "short_form", label: "Short-form Content", labelKo: "숏폼 콘텐츠" },
    { value: "brand_content", label: "Brand Content", labelKo: "브랜드 콘텐츠" },
];

export default function CreatorRegistrationPage() {
    const router = useRouter();
    const { language } = useLanguage();

    const [formData, setFormData] = useState({
        display_name: "",
        bio: "",
        categories: [] as string[],
        skills: [] as string[],
        hourly_rate: 500,
        min_budget: 100,
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const labels = {
        title: language === "ko" ? "크리에이터 등록" : "Become a Creator",
        backTo: language === "ko" ? "Human Cloud로 돌아가기" : "Back to Human Cloud",
        displayName: language === "ko" ? "활동명" : "Display Name",
        displayNamePlaceholder: language === "ko" ? "예: 영상 장인" : "e.g., Video Master",
        bio: language === "ko" ? "소개" : "Bio",
        bioPlaceholder: language === "ko"
            ? "자신의 경력, 강점, 작업 스타일을 소개해주세요..."
            : "Introduce your experience, strengths, and work style...",
        categories: language === "ko" ? "전문 분야" : "Specializations",
        skills: language === "ko" ? "보유 스킬" : "Skills",
        pricing: language === "ko" ? "가격 설정" : "Pricing",
        hourlyRate: language === "ko" ? "시간당 요금 (크레딧)" : "Hourly Rate (Credits)",
        minBudget: language === "ko" ? "최소 예산 (크레딧)" : "Minimum Budget (Credits)",
        submit: language === "ko" ? "크리에이터 등록하기" : "Register as Creator",
        submitting: language === "ko" ? "등록 중..." : "Registering...",
        successTitle: language === "ko" ? "등록 완료!" : "Registration Complete!",
        successMsg: language === "ko"
            ? "이제 의뢰를 받을 수 있습니다."
            : "You can now receive requests.",
    };

    const toggleCategory = (cat: string) => {
        setFormData((prev) => ({
            ...prev,
            categories: prev.categories.includes(cat)
                ? prev.categories.filter((c) => c !== cat)
                : [...prev.categories, cat],
        }));
    };

    const toggleSkill = (skill: string) => {
        setFormData((prev) => ({
            ...prev,
            skills: prev.skills.includes(skill)
                ? prev.skills.filter((s) => s !== skill)
                : [...prev.skills, skill],
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.display_name || formData.categories.length === 0) return;

        setSubmitting(true);
        setError(null);

        try {
            await fetchWithAuth("/api/v1/humancloud/creators", {
                method: "POST",
                body: JSON.stringify(formData),
            });
            setSuccess(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to register");
        } finally {
            setSubmitting(false);
        }
    };

    // Success State
    if (success) {
        return (
            <AppShell showTopBar={false}>
                <div className="min-h-screen flex items-center justify-center px-4">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="text-center"
                    >
                        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-emerald-500/10 flex items-center justify-center">
                            <CheckCircle className="w-10 h-10 text-emerald-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-[var(--fg-0)] mb-2">{labels.successTitle}</h2>
                        <p className="text-[var(--fg-muted)] mb-6">{labels.successMsg}</p>
                        <button
                            onClick={() => router.push("/humancloud")}
                            className="px-6 py-3 bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-lg transition-colors"
                        >
                            {labels.backTo}
                        </button>
                    </motion.div>
                </div>
            </AppShell>
        );
    }

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
                            <UserPlus className="w-6 h-6 text-violet-400" />
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
                        {/* Display Name */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-2">
                                {labels.displayName}
                            </label>
                            <input
                                type="text"
                                value={formData.display_name}
                                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                                placeholder={labels.displayNamePlaceholder}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg 
                                    text-white placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                                required
                            />
                        </div>

                        {/* Bio */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-2">
                                {labels.bio}
                            </label>
                            <textarea
                                value={formData.bio}
                                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                                placeholder={labels.bioPlaceholder}
                                rows={4}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg 
                                    text-white placeholder-slate-500 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 resize-none"
                            />
                        </div>

                        {/* Categories */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-3 flex items-center gap-2">
                                <Briefcase className="w-4 h-4 text-blue-400" />
                                {labels.categories}
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {CATEGORY_OPTIONS.map((cat) => (
                                    <button
                                        key={cat.value}
                                        type="button"
                                        onClick={() => toggleCategory(cat.value)}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                                            ${formData.categories.includes(cat.value)
                                                ? "bg-violet-600 text-white"
                                                : "bg-slate-800 text-[var(--fg-muted)] hover:bg-slate-700"
                                            }`}
                                    >
                                        {language === "ko" ? cat.labelKo : cat.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Skills */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-3 flex items-center gap-2">
                                <Tag className="w-4 h-4 text-emerald-400" />
                                {labels.skills}
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {SKILL_OPTIONS.map((skill) => (
                                    <button
                                        key={skill}
                                        type="button"
                                        onClick={() => toggleSkill(skill)}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                                            ${formData.skills.includes(skill)
                                                ? "bg-emerald-600 text-white"
                                                : "bg-slate-800 text-[var(--fg-muted)] hover:bg-slate-700"
                                            }`}
                                    >
                                        {skill.replace(/_/g, " ")}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Pricing */}
                        <div className="card-glass p-5">
                            <label className="block text-sm font-medium text-[var(--fg-0)] mb-3 flex items-center gap-2">
                                <DollarSign className="w-4 h-4 text-yellow-400" />
                                {labels.pricing}
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1">{labels.hourlyRate}</label>
                                    <input
                                        type="number"
                                        value={formData.hourly_rate}
                                        onChange={(e) => setFormData({ ...formData, hourly_rate: parseInt(e.target.value) || 0 })}
                                        min={0}
                                        step={100}
                                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-slate-500 mb-1">{labels.minBudget}</label>
                                    <input
                                        type="number"
                                        value={formData.min_budget}
                                        onChange={(e) => setFormData({ ...formData, min_budget: parseInt(e.target.value) || 0 })}
                                        min={0}
                                        step={100}
                                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={submitting || !formData.display_name || formData.categories.length === 0}
                            className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-violet-600 
                                hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed
                                text-white font-medium rounded-xl transition-colors"
                        >
                            {submitting ? (
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
