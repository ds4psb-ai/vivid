"use client";

import { useState, useEffect } from "react";
import { Image as ImageIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UnifiedWorkflowShell } from "@/components/workflow";

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
 */

export default function ProductionPage() {
  return (
    <UnifiedWorkflowShell
      appId="production"
      showAurora={true}
      showWorkflowProgress={true}
      showChainSummary={true}
      headerRight={<ProviderStats />}
    >
      {(currentStepId) => <StepContent stepId={currentStepId} />}
    </UnifiedWorkflowShell>
  );
}

/**
 * Step content renderer
 */
function StepContent({ stepId }: { stepId: string }) {
  switch (stepId) {
    case "veo":
      return <VeoVideoPanel />;

    case "kling":
      return <KlingPanel />;

    case "suno":
      return <SunoPanel />;

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
      return <VeoVideoPanel />;
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
