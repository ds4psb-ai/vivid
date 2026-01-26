"use client";

import { useState, useEffect } from "react";
import { Clapperboard, Video, Film, Music2, Image as ImageIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MegaAppShell, type MegaAppTab } from "@/components/mega-app";

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
 */

const TABS: MegaAppTab[] = [
  {
    value: "veo",
    label: "VEO 3.1",
    labelEn: "VEO 3.1",
    icon: <Video className="w-4 h-4" />,
    description: "Google VEO 3.1 비디오 생성",
    isNew: true,
  },
  {
    value: "kling",
    label: "Kling 2.6",
    labelEn: "Kling 2.6",
    icon: <Film className="w-4 h-4" />,
    description: "고품질 시네마틱 비디오 생성",
  },
  {
    value: "suno",
    label: "Suno AI",
    labelEn: "Suno AI",
    icon: <Music2 className="w-4 h-4" />,
    description: "AI 음악 생성 (작사/작곡)",
  },
  {
    value: "imagen",
    label: "Imagen 3",
    labelEn: "Imagen 3",
    icon: <ImageIcon className="w-4 h-4" />,
    description: "고품질 이미지 생성 (Coming Soon)",
    isDisabled: true,
    badge: "Soon",
  },
];

export default function ProductionPage() {
  return (
    <MegaAppShell
      appId="production"
      title="Production Bridge"
      subtitle="통합 미디어 생성 플랫폼"
      icon={Clapperboard}
      tabs={TABS}
      defaultTab="veo"
      tabParamName="provider"
      headerRight={<ProviderStats />}
    >
      {(activeTab) => (
        <>
          {activeTab === "veo" && <VeoVideoPanel />}
          {activeTab === "kling" && <KlingPanel />}
          {activeTab === "suno" && <SunoPanel />}
          {activeTab === "imagen" && (
            <div className="p-4">
              <ComingSoonPanel
                title="Imagen 3"
                description="Google Imagen 3 고품질 이미지 생성이 곧 출시됩니다."
              />
            </div>
          )}
        </>
      )}
    </MegaAppShell>
  );
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
