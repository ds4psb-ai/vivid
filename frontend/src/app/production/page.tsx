"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clapperboard, Video, Film, Music2, Image as ImageIcon, Loader2 } from "lucide-react";

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

interface TabConfig {
  value: string;
  label: string;
  labelEn: string;
  icon: React.ReactNode;
  description: string;
  isNew?: boolean;
  mediaType: "video" | "audio" | "image";
}

const TAB_CONFIG: TabConfig[] = [
  {
    value: "veo",
    label: "VEO 3.1",
    labelEn: "VEO 3.1",
    icon: <Video className="w-4 h-4" />,
    description: "Google VEO 3.1 비디오 생성",
    isNew: true,
    mediaType: "video",
  },
  {
    value: "kling",
    label: "Kling 2.6",
    labelEn: "Kling 2.6",
    icon: <Film className="w-4 h-4" />,
    description: "고품질 시네마틱 비디오 생성",
    mediaType: "video",
  },
  {
    value: "suno",
    label: "Suno AI",
    labelEn: "Suno AI",
    icon: <Music2 className="w-4 h-4" />,
    description: "AI 음악 생성 (작사/작곡)",
    mediaType: "audio",
  },
  {
    value: "imagen",
    label: "Imagen 3",
    labelEn: "Imagen 3",
    icon: <ImageIcon className="w-4 h-4" />,
    description: "고품질 이미지 생성 (Coming Soon)",
    mediaType: "image",
  },
];

/**
 * ProductionPage - Wrapper with Suspense boundary
 */
export default function ProductionPage() {
  return (
    <Suspense fallback={<ProductionPageLoading />}>
      <ProductionPageContent />
    </Suspense>
  );
}

/**
 * Loading state for ProductionPage
 */
function ProductionPageLoading() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading Production Bridge...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * ProductionPageContent - Actual content with useSearchParams
 */
function ProductionPageContent() {
  const searchParams = useSearchParams();
  const providerParam = searchParams.get("provider");
  const [activeTab, setActiveTab] = useState(providerParam || "veo");

  // Sync with URL params
  useEffect(() => {
    if (providerParam && TAB_CONFIG.find((t) => t.value === providerParam)) {
      setActiveTab(providerParam);
    }
  }, [providerParam]);

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Clapperboard className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Production Bridge</h1>
                <p className="text-sm text-muted-foreground">
                  통합 미디어 생성 플랫폼
                </p>
              </div>
              <div className="ml-auto">
                <ProviderStats />
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col"
        >
          <div className="flex-shrink-0 border-b bg-muted/50">
            <div className="container">
              <TabsList className="h-auto p-1 bg-transparent gap-1">
                {TAB_CONFIG.map((tab) => (
                  <TabsTrigger
                    key={tab.value}
                    value={tab.value}
                    disabled={tab.value === "imagen"} // Coming soon
                    className="flex items-center gap-2 px-4 py-2.5 data-[state=active]:bg-background"
                  >
                    {tab.icon}
                    <span className="hidden sm:inline">{tab.label}</span>
                    {tab.isNew && (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        NEW
                      </Badge>
                    )}
                    {tab.value === "imagen" && (
                      <Badge variant="outline" className="ml-1 text-xs">
                        Soon
                      </Badge>
                    )}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>
          </div>

          {/* Tab Contents */}
          <div className="flex-1 overflow-auto">
            {/* VEO - Video Maker with Veo 3.1 features */}
            <TabsContent value="veo" className="h-full m-0">
              <VeoVideoPanel />
            </TabsContent>

            {/* Kling - Kling Video */}
            <TabsContent value="kling" className="h-full m-0">
              <KlingPanel />
            </TabsContent>

            {/* Suno - Suno Music */}
            <TabsContent value="suno" className="h-full m-0">
              <SunoPanel />
            </TabsContent>

            {/* Imagen - Coming Soon */}
            <TabsContent value="imagen" className="h-full m-0 p-4">
              <ComingSoonPanel
                title="Imagen 3"
                description="Google Imagen 3 고품질 이미지 생성이 곧 출시됩니다."
              />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </AppShell>
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
      <Badge variant="outline" className="text-xs">
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
      <Card className="text-center">
        <CardHeader>
          <div className="mx-auto mb-4 p-4 rounded-full bg-muted">
            <ImageIcon className="w-12 h-12 text-muted-foreground" />
          </div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            빠른 시일 내에 이용 가능합니다. 기대해 주세요!
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
