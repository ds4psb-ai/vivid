"use client";

/**
 * Creator Profile Page
 *
 * Shows individual creator's profile, skills, ratings, and completed works.
 */

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    Star,
    Shield,
    Briefcase,
    MessageSquare,
    Loader2,
    AlertTriangle,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchWithAuth } from "@/lib/api-client";

// =============================================================================
// Types
// =============================================================================

interface CreatorProfile {
    id: string;
    user_id: string;
    display_name: string;
    bio?: string;
    categories: string[];
    skills: string[];
    completed_count: number;
    avg_rating?: number;
    is_available: boolean;
    is_verified: boolean;
}

// =============================================================================
// Components
// =============================================================================

function RatingStars({ rating }: { rating: number }) {
    return (
        <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
                <Star
                    key={star}
                    className={`w-4 h-4 ${
                        star <= rating
                            ? "text-amber-400 fill-amber-400"
                            : "text-slate-600"
                    }`}
                />
            ))}
            <span className="ml-1 text-sm text-slate-400">
                {rating.toFixed(1)}
            </span>
        </div>
    );
}

function SkillBadge({ skill }: { skill: string }) {
    return (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-violet-500/10 text-violet-300 border border-violet-500/20">
            {skill}
        </span>
    );
}

function CategoryBadge({ category }: { category: string }) {
    const labels: Record<string, string> = {
        video_creative: "Video Creative",
        motion_graphics: "Motion Graphics",
        "3d_animation": "3D Animation",
        vfx: "VFX",
        editing: "Editing",
    };
    return (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-300 border border-sky-500/20">
            {labels[category] || category}
        </span>
    );
}

// =============================================================================
// Page
// =============================================================================

export default function CreatorProfilePage() {
    const router = useRouter();
    const params = useParams();
    const creatorId = params.id as string;
    const { language } = useLanguage();

    const [creator, setCreator] = useState<CreatorProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const labels = {
        back: language === "ko" ? "뒤로" : "Back",
        verified: language === "ko" ? "인증됨" : "Verified",
        available: language === "ko" ? "작업 가능" : "Available",
        unavailable: language === "ko" ? "작업 불가" : "Unavailable",
        completedWorks: language === "ko" ? "완료한 작업" : "Completed Works",
        skills: language === "ko" ? "스킬" : "Skills",
        categories: language === "ko" ? "카테고리" : "Categories",
        bio: language === "ko" ? "소개" : "About",
        contact: language === "ko" ? "연락하기" : "Contact",
        notFound: language === "ko" ? "크리에이터를 찾을 수 없습니다" : "Creator not found",
    };

    useEffect(() => {
        if (!creatorId) return;

        const fetchCreator = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await fetchWithAuth(`/api/v1/humancloud/creators/${creatorId}`) as CreatorProfile;
                setCreator(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load creator");
            } finally {
                setLoading(false);
            }
        };

        fetchCreator();
    }, [creatorId]);

    if (loading) {
        return (
            <AppShell showTopBar={false}>
                <div className="min-h-screen flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                </div>
            </AppShell>
        );
    }

    if (error || !creator) {
        return (
            <AppShell showTopBar={false}>
                <AuroraBackground />
                <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
                    <AlertTriangle className="w-12 h-12 text-amber-400" />
                    <p className="text-lg text-slate-300">{error || labels.notFound}</p>
                    <button
                        onClick={() => router.push("/humancloud")}
                        className="mt-4 px-6 py-2 rounded-full bg-violet-600 hover:bg-violet-500 text-white font-medium transition-colors"
                    >
                        {labels.back}
                    </button>
                </div>
            </AppShell>
        );
    }

    return (
        <AppShell showTopBar={false}>
            <AuroraBackground />

            <div className="min-h-screen relative px-4 py-8 sm:px-6">
                <div className="mx-auto max-w-3xl">
                    {/* Back Button */}
                    <motion.button
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        onClick={() => router.push("/humancloud")}
                        className="flex items-center gap-2 text-slate-400 hover:text-white mb-8 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        {labels.back}
                    </motion.button>

                    {/* Profile Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="card-glass p-8"
                    >
                        <div className="flex items-start gap-6">
                            {/* Avatar */}
                            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-3xl font-bold text-white shrink-0">
                                {creator.display_name.charAt(0).toUpperCase()}
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3 flex-wrap">
                                    <h1 className="text-2xl font-bold text-white">
                                        {creator.display_name}
                                    </h1>
                                    {creator.is_verified && (
                                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                            <Shield className="w-3 h-3" />
                                            {labels.verified}
                                        </span>
                                    )}
                                    <span
                                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                            creator.is_available
                                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                                : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                                        }`}
                                    >
                                        {creator.is_available ? labels.available : labels.unavailable}
                                    </span>
                                </div>

                                {/* Rating */}
                                {creator.avg_rating && (
                                    <div className="mt-3">
                                        <RatingStars rating={creator.avg_rating} />
                                    </div>
                                )}

                                {/* Stats */}
                                <div className="mt-4 flex items-center gap-6 text-sm text-slate-400">
                                    <span className="flex items-center gap-1.5">
                                        <Briefcase className="w-4 h-4 text-violet-400" />
                                        <span className="text-white font-medium">{creator.completed_count}</span>
                                        {labels.completedWorks}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Bio */}
                        {creator.bio && (
                            <div className="mt-6 pt-6 border-t border-white/5">
                                <h3 className="text-sm font-medium text-slate-400 mb-2">{labels.bio}</h3>
                                <p className="text-slate-300 whitespace-pre-wrap">{creator.bio}</p>
                            </div>
                        )}

                        {/* Categories */}
                        {creator.categories.length > 0 && (
                            <div className="mt-6 pt-6 border-t border-white/5">
                                <h3 className="text-sm font-medium text-slate-400 mb-3">{labels.categories}</h3>
                                <div className="flex flex-wrap gap-2">
                                    {creator.categories.map((cat) => (
                                        <CategoryBadge key={cat} category={cat} />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Skills */}
                        {creator.skills.length > 0 && (
                            <div className="mt-6 pt-6 border-t border-white/5">
                                <h3 className="text-sm font-medium text-slate-400 mb-3">{labels.skills}</h3>
                                <div className="flex flex-wrap gap-2">
                                    {creator.skills.map((skill) => (
                                        <SkillBadge key={skill} skill={skill} />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Contact Button */}
                        <div className="mt-8 pt-6 border-t border-white/5">
                            <button
                                onClick={() => {
                                    // TODO: Implement contact/message functionality
                                    router.push(`/humancloud/requests/new?creator=${creator.id}`);
                                }}
                                disabled={!creator.is_available}
                                className="w-full py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium flex items-center justify-center gap-2 transition-colors"
                            >
                                <MessageSquare className="w-4 h-4" />
                                {labels.contact}
                            </button>
                        </div>
                    </motion.div>
                </div>
            </div>
        </AppShell>
    );
}
