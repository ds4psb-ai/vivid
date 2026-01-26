"use client";

import type { LucideIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface NextStepConfig {
  app: "dna-lab" | "story-engine" | "production";
  tab: string;
  label: string;
}

interface BaseMegaAppPanelProps {
  title: string;
  titleEn?: string;
  icon: LucideIcon;
  description?: string;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "4xl";
  nextStep?: NextStepConfig;
  className?: string;
}

export function BaseMegaAppPanel({
  title,
  titleEn,
  icon: Icon,
  description,
  children,
  maxWidth = "4xl",
  nextStep,
  className,
}: BaseMegaAppPanelProps) {
  const maxWidthClass = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "2xl": "max-w-2xl",
    "4xl": "max-w-4xl",
  }[maxWidth];

  return (
    <div className={cn("container mx-auto p-4", maxWidthClass, className)}>
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Icon className="w-5 h-5" />
            {title}
            {titleEn && (
              <span className="text-sm font-normal text-white/40">
                ({titleEn})
              </span>
            )}
          </CardTitle>
          {description && (
            <CardDescription className="text-white/60">
              {description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {children}
        </CardContent>
      </Card>

      {/* Next Step CTA */}
      {nextStep && (
        <div className="mt-6 flex justify-end">
          <Link
            href={`/${nextStep.app}?tab=${nextStep.tab}`}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white/80 hover:text-white transition-colors"
          >
            {nextStep.label}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
