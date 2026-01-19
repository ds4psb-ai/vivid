"use client";

import { ReactNode } from "react";
import AppShell from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";

interface PlaceholderCard {
  title: string;
  description: string;
  tone?: "neutral" | "info" | "warning";
}

interface CreatorPageFrameProps {
  title: string;
  subtitle: string;
  badge?: string;
  children?: ReactNode;
  placeholders?: PlaceholderCard[];
}

export function CreatorPageFrame({
  title,
  subtitle,
  badge = "COMING SOON",
  children,
  placeholders,
}: CreatorPageFrameProps) {
  const { language } = useLanguage();

  const fallbackPlaceholders: PlaceholderCard[] = placeholders ?? [
    {
      title: language === "ko" ? "요약 메트릭" : "Summary metrics",
      description:
        language === "ko"
          ? "크리에이터 주요 지표가 여기에 표시됩니다."
          : "Key creator metrics will appear here.",
    },
    {
      title: language === "ko" ? "승인 대기" : "Pending approvals",
      description:
        language === "ko"
          ? "검토/승인이 필요한 항목을 큐로 정리합니다."
          : "Items awaiting review and approval will be listed.",
    },
    {
      title: language === "ko" ? "피드백 루프" : "Feedback loop",
      description:
        language === "ko"
          ? "피드백 수집과 학습 루프 상태를 보여줍니다."
          : "Feedback ingestion and learning loop status.",
      tone: "info",
    },
  ];

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen bg-[var(--bg-0)]">
        <div className="max-w-6xl mx-auto px-6 py-10 space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-[0.28em] text-violet-500">
              {badge}
            </span>
            <h1 className="text-2xl font-semibold text-[var(--fg-0)]">{title}</h1>
          </div>
          <p className="text-sm text-[var(--fg-muted)] max-w-2xl">{subtitle}</p>

          {children ? (
            children
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {fallbackPlaceholders.map((item) => (
                <Card
                  key={item.title}
                  className={cn(
                    "border border-white/5 bg-[var(--surface-1)]/70",
                    item.tone === "info" && "border-violet-500/30"
                  )}
                >
                  <CardHeader>
                    <CardTitle className="text-base">{item.title}</CardTitle>
                    <CardDescription>{item.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-2 w-3/4 rounded-full bg-white/10 mb-2" />
                    <div className="h-2 w-1/2 rounded-full bg-white/10" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

export default CreatorPageFrame;
