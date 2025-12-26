"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
    Gift,
    Copy,
    Check,
    Users,
    TrendingUp,
    Sparkles,
    Share2,
    ExternalLink,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, type AffiliateProfile, type AffiliateReferral } from "@/lib/api";
import { normalizeApiError } from "@/lib/errors";

export default function AffiliatePage() {
    const { language } = useLanguage();
    const [copied, setCopied] = useState(false);
    const [profile, setProfile] = useState<AffiliateProfile | null>(null);
    const [referrals, setReferrals] = useState<AffiliateReferral[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const loadErrorFallback =
        language === "ko" ? "제휴 데이터를 불러오지 못했습니다." : "Unable to load affiliate data.";

    useEffect(() => {
        let active = true;
        const loadAffiliate = async () => {
            setIsLoading(true);
            setLoadError(null);
            try {
                const [profileData, referralData] = await Promise.all([
                    api.getAffiliateProfile(),
                    api.listAffiliateReferrals(20),
                ]);
                if (!active) return;
                setProfile(profileData);
                setReferrals(referralData);
            } catch (err) {
                if (!active) return;
                setLoadError(normalizeApiError(err, loadErrorFallback));
            } finally {
                if (active) setIsLoading(false);
            }
        };
        void loadAffiliate();
        return () => {
            active = false;
        };
    }, [loadErrorFallback]);

    const referralCode = profile?.affiliate_code || "";
    const referralLink =
        profile?.referral_link ||
        (typeof window !== "undefined" && referralCode
            ? `${window.location.origin}/signup?ref=${referralCode}`
            : "");

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(referralLink);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    }, [referralLink]);

    const totalEarned = useMemo(() => {
        if (profile) return profile.total_earned;
        return referrals
            .filter((ref) => ref.reward_status === "granted")
            .reduce((sum, ref) => sum + ref.reward_amount, 0);
    }, [profile, referrals]);
    const pendingCount = useMemo(() => {
        if (profile) return profile.pending_count;
        return referrals.filter((ref) => ref.reward_status === "pending").length;
    }, [profile, referrals]);

    const labels = {
        badge: language === "ko" ? "제휴 프로그램" : "Affiliate Program",
        title: language === "ko" ? "공유하고 크레딧을 받으세요" : "Earn Credits by Sharing",
        subtitle: language === "ko"
            ? "친구가 가입하고 첫 실행을 완료하면 크레딧을 받습니다. 친구도 보너스를 받습니다!"
            : "Earn credits when friends sign up and complete their first run. They get credits too!",
        referralLink: language === "ko" ? "내 추천 링크" : "Your Referral Link",
        copied: language === "ko" ? "복사됨!" : "Copied!",
        copy: language === "ko" ? "복사" : "Copy",
        shareOnX: language === "ko" ? "X에 공유" : "Share on X",
        shareLink: language === "ko" ? "링크 공유" : "Share Link",
        totalReferrals: language === "ko" ? "총 추천" : "Total Referrals",
        creditsEarned: language === "ko" ? "획득 크레딧" : "Credits Earned",
        pending: language === "ko" ? "대기 중" : "Pending",
        referralHistory: language === "ko" ? "추천 내역" : "Referral History",
        joined: language === "ko" ? "가입" : "Joined",
        howItWorks: language === "ko" ? "작동 방식" : "How It Works",
        step1Title: language === "ko" ? "링크 공유" : "Share your link",
        step1Desc: language === "ko" ? "복사해서 친구에게 공유" : "Copy and share with friends",
        step2Title: language === "ko" ? "친구 가입" : "They sign up",
        step2Desc: language === "ko" ? "이메일 인증 및 첫 실행" : "They verify email & first run",
        step3Title: language === "ko" ? "둘 다 적립" : "Both earn credits",
        step3Desc: language === "ko" ? "양쪽 모두 보너스 크레딧 지급" : "Both sides receive bonus credits",
        statusClicked: language === "ko" ? "클릭됨" : "clicked",
        statusSigned: language === "ko" ? "가입" : "signed up",
        statusActivated: language === "ko" ? "활성" : "activated",
        statusPaid: language === "ko" ? "지급됨" : "paid",
        rewardPending: language === "ko" ? "대기" : "pending",
        rewardGranted: language === "ko" ? "지급" : "granted",
        noReferrals: language === "ko" ? "추천 내역이 없습니다." : "No referrals yet.",
        refereeFallback: language === "ko" ? "추천 사용자" : "Referee",
    };

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-3xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 sm:mb-8"
                    >
                        <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 mb-3 sm:px-4 sm:py-1.5 sm:text-sm sm:mb-4">
                            <Gift className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                            {labels.badge}
                        </div>
                        <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                        <p className="mt-2 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                    </motion.div>

                    {loadError && (
                        <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                            {loadError}
                        </div>
                    )}

                    {/* Referral Link Card */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-6 rounded-xl border border-white/10 bg-gradient-to-br from-emerald-500/10 via-transparent to-sky-500/10 p-4 sm:mb-8 sm:rounded-2xl sm:p-6"
                        aria-labelledby="referral-link-heading"
                    >
                        <div id="referral-link-heading" className="text-xs font-medium text-[var(--fg-muted)] mb-2 sm:text-sm">
                            {labels.referralLink}
                        </div>
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                            <div className="flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 font-mono text-xs text-[var(--fg-0)] truncate sm:px-4 sm:py-3 sm:text-sm">
                                {referralLink || (isLoading ? "..." : "-")}
                            </div>
                            <button
                                onClick={handleCopy}
                                disabled={!referralLink}
                                className={`flex items-center justify-center gap-2 rounded-lg px-4 py-2 font-semibold transition-all sm:px-5 sm:py-3 ${copied
                                        ? "bg-emerald-500 text-white"
                                        : "bg-white/10 text-[var(--fg-0)] hover:bg-white/20"
                                    } disabled:cursor-not-allowed disabled:opacity-60`}
                                aria-label={copied ? labels.copied : labels.copy}
                            >
                                {copied ? (
                                    <>
                                        <Check className="h-4 w-4" aria-hidden="true" />
                                        {labels.copied}
                                    </>
                                ) : (
                                    <>
                                        <Copy className="h-4 w-4" aria-hidden="true" />
                                        {labels.copy}
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Share Buttons */}
                        <div className="mt-3 flex flex-wrap gap-2 sm:mt-4 sm:gap-3">
                            <button
                                className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10 sm:px-4 sm:text-sm"
                                aria-label={labels.shareOnX}
                            >
                                <Share2 className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                                {labels.shareOnX}
                            </button>
                            <button
                                className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10 sm:px-4 sm:text-sm"
                                aria-label={labels.shareLink}
                            >
                                <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                                {labels.shareLink}
                            </button>
                        </div>
                    </motion.section>

                    {/* Stats */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="mb-6 grid grid-cols-3 gap-2 sm:mb-8 sm:gap-4"
                    >
                        <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3 sm:rounded-xl sm:p-5">
                            <div className="flex items-center gap-1 text-[var(--fg-muted)] sm:gap-2">
                                <Users className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                                <span className="text-[10px] sm:text-xs">{labels.totalReferrals}</span>
                            </div>
                            <div className="mt-1 text-xl font-bold text-[var(--fg-0)] sm:mt-2 sm:text-2xl">
                                {profile ? profile.total_referrals : referrals.length}
                            </div>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3 sm:rounded-xl sm:p-5">
                            <div className="flex items-center gap-1 text-[var(--fg-muted)] sm:gap-2">
                                <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                                <span className="text-[10px] sm:text-xs">{labels.creditsEarned}</span>
                            </div>
                            <div className="mt-1 text-xl font-bold text-emerald-400 sm:mt-2 sm:text-2xl">
                                +{totalEarned}
                            </div>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3 sm:rounded-xl sm:p-5">
                            <div className="flex items-center gap-1 text-[var(--fg-muted)] sm:gap-2">
                                <Sparkles className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                                <span className="text-[10px] sm:text-xs">{labels.pending}</span>
                            </div>
                            <div className="mt-1 text-xl font-bold text-amber-400 sm:mt-2 sm:text-2xl">
                                {pendingCount}
                            </div>
                        </div>
                    </motion.div>

                    {/* Referral History */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        aria-labelledby="referral-history-heading"
                    >
                        <h2 id="referral-history-heading" className="mb-3 text-base font-semibold text-[var(--fg-0)] sm:mb-4 sm:text-lg">
                            {labels.referralHistory}
                        </h2>
                        <div className="rounded-lg border border-white/10 bg-slate-950/60 divide-y divide-white/5 sm:rounded-xl">
                            {isLoading ? (
                                <div className="px-4 py-4 text-sm text-[var(--fg-muted)]">...</div>
                            ) : referrals.length === 0 ? (
                                <div className="px-4 py-4 text-sm text-[var(--fg-muted)]">{labels.noReferrals}</div>
                            ) : (
                                referrals.map((ref) => {
                                    const statusLabel =
                                        ref.status === "clicked"
                                            ? labels.statusClicked
                                            : ref.status === "signed_up"
                                                ? labels.statusSigned
                                                : ref.status === "activated"
                                                    ? labels.statusActivated
                                                    : labels.statusPaid;
                                    const statusTone =
                                        ref.status === "paid" || ref.status === "activated"
                                            ? "bg-emerald-500/10 text-emerald-400"
                                            : "bg-amber-500/10 text-amber-400";
                                    const rewardLabel =
                                        ref.reward_status === "granted"
                                            ? labels.rewardGranted
                                            : labels.rewardPending;
                                    return (
                                        <div
                                            key={ref.id}
                                            className="flex items-center justify-between px-4 py-3 sm:px-5 sm:py-4"
                                        >
                                            <div>
                                                <div className="text-sm font-medium text-[var(--fg-0)]">
                                                    {ref.referee_label || labels.refereeFallback}
                                                </div>
                                                <div className="text-xs text-[var(--fg-muted)]">
                                                    {labels.joined}{" "}
                                                    {new Date(ref.created_at).toLocaleDateString(
                                                        language === "ko" ? "ko-KR" : "en-US"
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 sm:gap-3">
                                                <span
                                                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${statusTone}`}
                                                >
                                                    {statusLabel}
                                                </span>
                                                <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] uppercase text-slate-300">
                                                    {rewardLabel}
                                                </span>
                                                {ref.reward_amount > 0 && (
                                                    <span className="text-sm font-semibold text-emerald-400">
                                                        +{ref.reward_amount}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </motion.section>

                    {/* How It Works */}
                    <motion.section
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                        className="mt-6 rounded-lg border border-white/10 bg-slate-950/60 p-4 sm:mt-8 sm:rounded-xl sm:p-6"
                        aria-labelledby="how-it-works-heading"
                    >
                        <h3 id="how-it-works-heading" className="mb-3 font-semibold text-[var(--fg-0)] sm:mb-4">{labels.howItWorks}</h3>
                        <div className="grid grid-cols-3 gap-3 text-center sm:gap-6">
                            <div>
                                <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-sky-500/10 text-sm font-bold text-sky-400 sm:mb-3 sm:h-10 sm:w-10 sm:text-lg">
                                    1
                                </div>
                                <div className="text-xs text-[var(--fg-0)] sm:text-sm">{labels.step1Title}</div>
                                <div className="mt-1 text-[10px] text-[var(--fg-muted)] sm:text-xs">{labels.step1Desc}</div>
                            </div>
                            <div>
                                <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-amber-500/10 text-sm font-bold text-amber-400 sm:mb-3 sm:h-10 sm:w-10 sm:text-lg">
                                    2
                                </div>
                                <div className="text-xs text-[var(--fg-0)] sm:text-sm">{labels.step2Title}</div>
                                <div className="mt-1 text-[10px] text-[var(--fg-muted)] sm:text-xs">{labels.step2Desc}</div>
                            </div>
                            <div>
                                <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/10 text-sm font-bold text-emerald-400 sm:mb-3 sm:h-10 sm:w-10 sm:text-lg">
                                    3
                                </div>
                                <div className="text-xs text-[var(--fg-0)] sm:text-sm">{labels.step3Title}</div>
                                <div className="mt-1 text-[10px] text-[var(--fg-muted)] sm:text-xs">{labels.step3Desc}</div>
                            </div>
                        </div>
                    </motion.section>
                </div>
            </div>
        </AppShell>
    );
}
