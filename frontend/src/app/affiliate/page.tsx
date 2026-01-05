"use client";

/**
 * Affiliate Dashboard Page
 *
 * Shows affiliate code, referral stats, and referral history.
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    Users,
    DollarSign,
    Clock,
    Copy,
    Check,
    Loader2,
    AlertTriangle,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, AffiliateProfile, AffiliateReferral } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";
import { formatNumber } from "@/lib/formatters";

// =============================================================================
// Components
// =============================================================================

function StatCard({
    icon: Icon,
    label,
    value,
    subtext,
    color,
}: {
    icon: React.ElementType;
    label: string;
    value: string | number;
    subtext?: string;
    color: string;
}) {
    return (
        <div className="p-4 rounded-2xl border border-white/10 bg-slate-900/50">
            <div className="flex items-center gap-3 mb-3">
                <div className={`p-2 rounded-xl ${color}`}>
                    <Icon className="w-4 h-4" />
                </div>
                <span className="text-sm text-slate-400">{label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
            {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
        </div>
    );
}

function ReferralRow({ referral, language }: { referral: AffiliateReferral; language: string }) {
    const statusLabels: Record<string, { label: string; color: string }> = {
        pending: {
            label: language === "ko" ? "대기중" : "Pending",
            color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        },
        converted: {
            label: language === "ko" ? "전환됨" : "Converted",
            color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        },
        expired: {
            label: language === "ko" ? "만료" : "Expired",
            color: "bg-slate-500/10 text-slate-400 border-slate-500/20",
        },
    };

    const rewardStatusLabels: Record<string, { label: string; color: string }> = {
        pending: {
            label: language === "ko" ? "지급대기" : "Pending",
            color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        },
        paid: {
            label: language === "ko" ? "지급완료" : "Paid",
            color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        },
        none: {
            label: language === "ko" ? "-" : "-",
            color: "bg-slate-500/10 text-slate-400 border-slate-500/20",
        },
    };

    const status = statusLabels[referral.status] || statusLabels.pending;
    const rewardStatus = rewardStatusLabels[referral.reward_status] || rewardStatusLabels.none;

    return (
        <div className="flex items-center justify-between p-4 border-b border-white/5 last:border-b-0 hover:bg-white/[0.02] transition-colors">
            <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-medium">
                    {(referral.referee_label || "U").charAt(0).toUpperCase()}
                </div>
                <div>
                    <div className="text-sm font-medium text-white">
                        {referral.referee_label || (language === "ko" ? "익명 사용자" : "Anonymous User")}
                    </div>
                    <div className="text-xs text-slate-500">
                        {new Date(referral.created_at).toLocaleDateString()}
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${status.color}`}>
                    {status.label}
                </span>
                {referral.reward_amount > 0 && (
                    <div className="text-right">
                        <div className="text-sm font-medium text-emerald-400">
                            +{formatNumber(referral.reward_amount)} CR
                        </div>
                        <span className={`text-[10px] ${rewardStatus.color} px-1.5 py-0.5 rounded`}>
                            {rewardStatus.label}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

// =============================================================================
// Page
// =============================================================================

export default function AffiliatePage() {
    const { language } = useLanguage();

    const [profile, setProfile] = useState<AffiliateProfile | null>(null);
    const [referrals, setReferrals] = useState<AffiliateReferral[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const labels = {
        title: language === "ko" ? "제휴 프로그램" : "Affiliate Program",
        subtitle: language === "ko" ? "친구를 초대하고 크레딧을 받으세요" : "Invite friends and earn credits",
        yourCode: language === "ko" ? "내 추천 코드" : "Your Referral Code",
        copyLink: language === "ko" ? "링크 복사" : "Copy Link",
        copied: language === "ko" ? "복사됨!" : "Copied!",
        totalReferrals: language === "ko" ? "총 추천" : "Total Referrals",
        totalEarned: language === "ko" ? "총 수익" : "Total Earned",
        pending: language === "ko" ? "대기중" : "Pending",
        referralHistory: language === "ko" ? "추천 내역" : "Referral History",
        noReferrals: language === "ko" ? "아직 추천 내역이 없습니다" : "No referrals yet",
        inviteFriend: language === "ko" ? "친구에게 공유하고 보상받기" : "Share with friends and earn rewards",
        howItWorks: language === "ko" ? "이용 방법" : "How it works",
        step1: language === "ko" ? "추천 링크 공유" : "Share your referral link",
        step2: language === "ko" ? "친구가 가입" : "Friend signs up",
        step3: language === "ko" ? "보상 지급" : "Both get rewards",
    };

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const [profileData, referralsData] = await Promise.all([
                    api.getAffiliateProfile(),
                    api.listAffiliateReferrals(50),
                ]);
                setProfile(profileData);
                setReferrals(referralsData);
            } catch (err) {
                setError(normalizeApiError(err, "Failed to load affiliate data"));
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleCopyLink = async () => {
        if (!profile?.referral_link && !profile?.affiliate_code) return;

        const link = profile.referral_link || `${window.location.origin}?ref=${profile.affiliate_code}`;
        await navigator.clipboard.writeText(link);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (loading) {
        return (
            <AppShell showTopBar={false}>
                <div className="min-h-screen flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                </div>
            </AppShell>
        );
    }

    if (error) {
        return (
            <AppShell showTopBar={false}>
                <AuroraBackground />
                <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
                    <AlertTriangle className="w-12 h-12 text-amber-400" />
                    <p className="text-lg text-slate-300">{error}</p>
                </div>
            </AppShell>
        );
    }

    return (
        <AppShell showTopBar={false}>
            <AuroraBackground />

            <div className="min-h-screen relative px-4 py-8 sm:px-6">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <h1 className="text-2xl font-bold text-white sm:text-3xl">{labels.title}</h1>
                        <p className="mt-2 text-slate-400">{labels.subtitle}</p>
                    </motion.div>

                    {/* Referral Code Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-6 p-6 rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10"
                    >
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                            <div>
                                <div className="text-sm text-slate-400 mb-2">{labels.yourCode}</div>
                                <div className="text-2xl font-bold font-mono text-white tracking-wider">
                                    {profile?.affiliate_code || "-"}
                                </div>
                            </div>
                            <button
                                onClick={handleCopyLink}
                                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium transition-colors"
                            >
                                {copied ? (
                                    <>
                                        <Check className="w-4 h-4" />
                                        {labels.copied}
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-4 h-4" />
                                        {labels.copyLink}
                                    </>
                                )}
                            </button>
                        </div>
                    </motion.div>

                    {/* Stats */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8"
                    >
                        <StatCard
                            icon={Users}
                            label={labels.totalReferrals}
                            value={formatNumber(profile?.total_referrals || 0)}
                            color="bg-sky-500/10 text-sky-400"
                        />
                        <StatCard
                            icon={DollarSign}
                            label={labels.totalEarned}
                            value={`${formatNumber(profile?.total_earned || 0)} CR`}
                            color="bg-emerald-500/10 text-emerald-400"
                        />
                        <StatCard
                            icon={Clock}
                            label={labels.pending}
                            value={formatNumber(profile?.pending_count || 0)}
                            color="bg-amber-500/10 text-amber-400"
                        />
                    </motion.div>

                    {/* How it works */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mb-8 p-6 rounded-2xl border border-white/10 bg-slate-900/50"
                    >
                        <h3 className="text-sm font-medium text-slate-400 mb-4">{labels.howItWorks}</h3>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center text-sm font-bold">
                                    1
                                </div>
                                <span className="text-sm text-white">{labels.step1}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center text-sm font-bold">
                                    2
                                </div>
                                <span className="text-sm text-white">{labels.step2}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center text-sm font-bold">
                                    3
                                </div>
                                <span className="text-sm text-white">{labels.step3}</span>
                            </div>
                        </div>
                    </motion.div>

                    {/* Referral History */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                        className="rounded-2xl border border-white/10 bg-slate-900/50 overflow-hidden"
                    >
                        <div className="px-6 py-4 border-b border-white/5">
                            <h3 className="font-semibold text-white">{labels.referralHistory}</h3>
                        </div>

                        {referrals.length > 0 ? (
                            <div className="divide-y divide-white/5">
                                {referrals.map((referral) => (
                                    <ReferralRow key={referral.id} referral={referral} language={language} />
                                ))}
                            </div>
                        ) : (
                            <div className="p-12 text-center">
                                <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <p className="text-slate-400">{labels.noReferrals}</p>
                                <p className="text-sm text-slate-500 mt-2">{labels.inviteFriend}</p>
                            </div>
                        )}
                    </motion.div>
                </div>
            </div>
        </AppShell>
    );
}
