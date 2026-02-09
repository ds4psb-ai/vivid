"use client";

import { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Image as ImageIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UnifiedWorkflowShell, ProductionOverview } from "@/components/workflow";
import { ProductionStepPanel, type ProductionStepId } from "@/components/production";

// Import existing panels
import VeoVideoPanel from "@/components/dimension/VeoVideoPanel";
import KlingPanel from "@/components/dimension/KlingPanel";
import SunoPanel from "@/components/dimension/SunoPanel";

/**
 * Production Bridge Hub - Mega App for Media Generation
 *
 * Consolidates:
 * - VEO (Video Maker)
 * - Kling (Kling Video)
 * - Suno (Suno Music)
 * - Imagen (Image Generation - Future)
 *
 * Phase 12: Overview 뷰 통합
 * - /production                → Overview (3개 Provider 한눈에)
 * - /production?step=overview  → Overview (명시적)
 * - /production?step=veo       → VEO 3.1
 * - /production?step=kling     → Kling 2.6
 * - /production?step=suno      → Suno AI
 *
 * Features:
 * - Unified provider interface
 * - Auto provider selection
 * - System Prompt integration from Story Engine
 * - Reference Images support (Veo 3.1)
 * - First/Last Frame control (Veo 3.1)
 *
 * Migration Note (2026.01):
 * Using UnifiedWorkflowShell for consistent cross-MegaApp behavior.
 * Step-based workflow replaces tab-based navigation.
 * ProductionStepPanel provides input banner and completion actions.
 */

/**
 * Valid step IDs for Production
 */
const VALID_STEP_IDS: ProductionStepId[] = ["veo", "kling", "suno"];

/**
 * Check if a string is a valid step ID
 */
function isValidStepId(step: string | null): step is ProductionStepId {
  return VALID_STEP_IDS.includes(step as ProductionStepId);
}

/**
 * Inner component that uses useSearchParams
 */
function ProductionPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const stepParam = searchParams.get("step");

  // Determine view mode
  const showOverview = useMemo(() => {
    if (!stepParam) return true;
    if (stepParam === "overview") return true;
    if (!isValidStepId(stepParam)) return true;
    return false;
  }, [stepParam]);

  // Handle step navigation from Overview
  const handleStepClick = useCallback(
    (stepId: string) => {
      router.push(`/production?step=${stepId}`);
    },
    [router]
  );

  // Render Overview or Step Detail
  if (showOverview) {
    return (
      <UnifiedWorkflowShell
        appId="production"
        showAurora={true}
        showWorkflowProgress={false}
        showChainSummary={false}
        headerRight={<ProviderStats />}
      >
        {() => <ProductionOverview onStepClick={handleStepClick} />}
      </UnifiedWorkflowShell>
    );
  }

  return (
    <UnifiedWorkflowShell
      appId="production"
      showAurora={true}
      showWorkflowProgress={true}
      showChainSummary={true}
      headerRight={<ProviderStats />}
    >
      {(currentStepId, _disclosureLevel) => <StepContent stepId={currentStepId} />}
    </UnifiedWorkflowShell>
  );
}

export default function ProductionPage() {
  return (
    <Suspense fallback={<ProductionLoadingFallback />}>
      <ProductionPageInner />
    </Suspense>
  );
}

/**
 * Loading fallback for Suspense boundary
 */
function ProductionLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-stitch-dark">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--stitch-primary)]/20 to-[var(--stitch-primary-accent)]/20 animate-pulse" />
        <div className="text-sm text-white/50">Production 로딩 중...</div>
      </div>
    </div>
  );
}

/**
 * Step content renderer with ProductionStepPanel wrapper
 */
function StepContent({ stepId }: { stepId: string }) {
  switch (stepId) {
    case "veo":
      return (
        <ProductionStepPanel stepId="veo" showCompletionActions>
          <VeoVideoPanel />
        </ProductionStepPanel>
      );

    case "kling":
      return (
        <ProductionStepPanel stepId="kling" showCompletionActions>
          <KlingPanel />
        </ProductionStepPanel>
      );

    case "suno":
      return (
        <ProductionStepPanel stepId="suno" showCompletionActions>
          <SunoPanel />
        </ProductionStepPanel>
      );

    case "imagen":
      return (
        <div className="p-4">
          <ComingSoonPanel
            title="Imagen 3"
            description="Google Imagen 3 고품질 이미지 생성이 곧 출시됩니다."
          />
        </div>
      );

    default:
      return (
        <ProductionStepPanel stepId="veo" showCompletionActions>
          <VeoVideoPanel />
        </ProductionStepPanel>
      );
  }
}

/**
 * Provider Stats - Show available providers and their status
 */
function ProviderStats() {
  const [stats, setStats] = useState<{
    providers: string[];
    default_video: string;
    default_audio: string;
  } | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch("/api/production/providers");
        const data = await response.json();
        setStats(data);
      } catch {
        // Silently fail - stats are not critical
      }
    };
    fetchStats();
  }, []);

  if (!stats) return null;

  return (
    <div className="flex items-center gap-2 text-sm">
      <Badge variant="outline" className="text-xs border-white/20 text-white/60">
        {stats.providers.length} Providers
      </Badge>
    </div>
  );
}

/**
 * Coming Soon Panel - Placeholder for future features
 */
function ComingSoonPanel({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="container max-w-2xl mx-auto py-16">
      <Card className="text-center bg-white/5 border-white/10">
        <CardHeader>
          <div className="mx-auto mb-4 p-4 rounded-full bg-white/5">
            <ImageIcon className="w-12 h-12 text-white/40" />
          </div>
          <CardTitle className="text-white">{title}</CardTitle>
          <CardDescription className="text-white/60">{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-white/40">
            빠른 시일 내에 이용 가능합니다. 기대해 주세요!
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
