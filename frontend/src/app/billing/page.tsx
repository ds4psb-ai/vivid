"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CreditCard, CheckCircle2, ArrowUpRight } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";

type BillingCycle = "monthly" | "yearly";

const PLANS = [
  { id: "starter", name: "Starter", nameKo: "스타터", monthly: 29, yearly: 24, credits: 1000, accounts: 2 },
  { id: "pro", name: "Pro", nameKo: "프로", monthly: 99, yearly: 79, credits: 5000, accounts: 4 },
  { id: "elite", name: "Elite", nameKo: "엘리트", monthly: 249, yearly: 199, credits: 12500, accounts: 10 },
  { id: "research", name: "Research Analyst", nameKo: "리서치 애널리스트", monthly: 19, yearly: 15, credits: 0, accounts: 1 },
];

const TOPUP_PACKS = [
  { id: "topup-500", credits: 500 },
  { id: "topup-2000", credits: 2000 },
  { id: "topup-5000", credits: 5000 },
];

const API_PACKS = [
  { id: "api-5000", credits: 5000 },
  { id: "api-15000", credits: 15000 },
  { id: "api-40000", credits: 40000 },
];

export default function BillingPage() {
  const { language } = useLanguage();
  const [cycle, setCycle] = useState<BillingCycle>("monthly");

  const labels = {
    title: language === "ko" ? "결제" : "Billing",
    subtitle:
      language === "ko"
        ? "플랜과 크레딧 패키지를 관리합니다."
        : "Manage subscription plans and credit packs.",
    monthly: language === "ko" ? "월간" : "Monthly",
    yearly: language === "ko" ? "연간" : "Yearly",
    annualSave: language === "ko" ? "연간 30% 할인" : "Annual 30% Off",
    perMonth: language === "ko" ? "/월" : "/mo",
    credits: language === "ko" ? "크레딧" : "credits",
    accounts: language === "ko" ? "연동 계정" : "connections",
    choosePlan: language === "ko" ? "플랜 선택" : "Choose Plan",
    topupTitle: language === "ko" ? "크레딧 추가 충전" : "Top-up Credits",
    apiTitle: language === "ko" ? "API 크레딧 팩" : "API Credit Packs",
    goCredits: language === "ko" ? "크레딧 페이지로" : "Go to Credits",
  };

  const planList = useMemo(
    () =>
      PLANS.map((plan) => ({
        ...plan,
        price: cycle === "monthly" ? plan.monthly : plan.yearly,
      })),
    [cycle]
  );

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 sm:mb-8"
          >
            <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
            <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-6 flex flex-wrap items-center gap-3"
          >
            <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 p-1 text-xs">
              <button
                onClick={() => setCycle("monthly")}
                className={`rounded-full px-4 py-1.5 ${cycle === "monthly" ? "bg-sky-500/20 text-sky-200" : "text-slate-400"}`}
              >
                {labels.monthly}
              </button>
              <button
                onClick={() => setCycle("yearly")}
                className={`rounded-full px-4 py-1.5 ${cycle === "yearly" ? "bg-emerald-500/20 text-emerald-200" : "text-slate-400"}`}
              >
                {labels.yearly}
              </button>
            </div>
            {cycle === "yearly" && (
              <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-[10px] font-semibold text-emerald-200">
                {labels.annualSave}
              </span>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="grid gap-4 lg:grid-cols-4"
          >
            {planList.map((plan) => (
              <div
                key={plan.id}
                className="rounded-2xl border border-white/10 bg-slate-950/60 p-5"
              >
                <div className="text-sm font-semibold text-[var(--fg-0)]">
                  {language === "ko" ? plan.nameKo : plan.name}
                </div>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white">${plan.price}</span>
                  <span className="text-xs text-[var(--fg-muted)]">{labels.perMonth}</span>
                </div>
                <div className="mt-4 space-y-2 text-xs text-[var(--fg-muted)]">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-3 w-3 text-emerald-300" />
                    {plan.credits.toLocaleString()} {labels.credits}
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-3 w-3 text-emerald-300" />
                    {plan.accounts} {labels.accounts}
                  </div>
                </div>
                <button
                  type="button"
                  className="mt-5 w-full rounded-lg bg-sky-500/10 px-3 py-2 text-xs font-semibold text-sky-200 transition-colors hover:bg-sky-500/20"
                >
                  {labels.choosePlan}
                </button>
              </div>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mt-8 grid gap-4 lg:grid-cols-2"
          >
            <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-[var(--accent)]" />
                <h2 className="text-sm font-semibold text-[var(--fg-0)]">{labels.topupTitle}</h2>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-[var(--fg-muted)]">
                {TOPUP_PACKS.map((pack) => (
                  <span
                    key={pack.id}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1"
                  >
                    {pack.credits.toLocaleString()} {labels.credits}
                  </span>
                ))}
              </div>
              <a
                href="/credits"
                className="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-sky-200 hover:text-sky-100"
              >
                {labels.goCredits}
                <ArrowUpRight className="h-3 w-3" />
              </a>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-[var(--accent)]" />
                <h2 className="text-sm font-semibold text-[var(--fg-0)]">{labels.apiTitle}</h2>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-[var(--fg-muted)]">
                {API_PACKS.map((pack) => (
                  <span
                    key={pack.id}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1"
                  >
                    {pack.credits.toLocaleString()} {labels.credits}
                  </span>
                ))}
              </div>
              <a
                href="/credits"
                className="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-sky-200 hover:text-sky-100"
              >
                {labels.goCredits}
                <ArrowUpRight className="h-3 w-3" />
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </AppShell>
  );
}
