"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dna, Video, Palette, Brain, CheckCircle, Loader2 } from "lucide-react";

// Import existing panels
import AestheticDirectorPanel from "@/components/dimension/AestheticDirectorPanel";
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";
import QualityDirectorPanel from "@/components/dimension/QualityDirectorPanel";

/**
 * DNA Lab Hub - Mega App for Auteur DNA Orchestration
 *
 * Consolidates:
 * - VPE (Video Parsing Engine) - NEW
 * - AD (Aesthetic Director)
 * - Mirror (Abyss Mirror)
 * - QC (Quality Director)
 */

interface TabConfig {
  value: string;
  label: string;
  labelEn: string;
  icon: React.ReactNode;
  description: string;
  isNew?: boolean;
}

const TAB_CONFIG: TabConfig[] = [
  {
    value: "vpe",
    label: "비디오 파싱",
    labelEn: "Video Parsing",
    icon: <Video className="w-4 h-4" />,
    description: "영상 분석으로 Logic Vector 추출",
    isNew: true,
  },
  {
    value: "ad",
    label: "미학 디렉터",
    labelEn: "Aesthetic Director",
    icon: <Palette className="w-4 h-4" />,
    description: "거장들의 미학을 적용합니다",
  },
  {
    value: "mirror",
    label: "심연의 거울",
    labelEn: "Abyss Mirror",
    icon: <Brain className="w-4 h-4" />,
    description: "나만의 취향과 창작 DNA 분석",
  },
  {
    value: "qc",
    label: "퀄리티 디렉터",
    labelEn: "Quality Director",
    icon: <CheckCircle className="w-4 h-4" />,
    description: "시각적 일관성 및 품질 검수",
  },
];

/**
 * DNALabPage - Wrapper with Suspense boundary
 */
export default function DNALabPage() {
  return (
    <Suspense fallback={<DNALabLoading />}>
      <DNALabContent />
    </Suspense>
  );
}

/**
 * Loading state for DNALabPage
 */
function DNALabLoading() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading DNA Lab...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * DNALabContent - Actual content with useSearchParams
 */
function DNALabContent() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState(tabParam || "vpe");

  // Sync with URL params
  useEffect(() => {
    if (tabParam && TAB_CONFIG.find((t) => t.value === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Dna className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold">DNA Lab</h1>
                <p className="text-sm text-muted-foreground">
                  거장 DNA 분석 및 오케스트레이션
                </p>
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
                    className="flex items-center gap-2 px-4 py-2.5 data-[state=active]:bg-background"
                  >
                    {tab.icon}
                    <span className="hidden sm:inline">{tab.label}</span>
                    {tab.isNew && (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        NEW
                      </Badge>
                    )}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>
          </div>

          {/* Tab Contents */}
          <div className="flex-1 overflow-auto">
            {/* VPE - Video Parsing Engine */}
            <TabsContent value="vpe" className="h-full m-0 p-4">
              <VPEPanel />
            </TabsContent>

            {/* AD - Aesthetic Director */}
            <TabsContent value="ad" className="h-full m-0">
              <AestheticDirectorPanel />
            </TabsContent>

            {/* Mirror - Abyss Mirror */}
            <TabsContent value="mirror" className="h-full m-0">
              <AbyssMirrorPanel />
            </TabsContent>

            {/* QC - Quality Director */}
            <TabsContent value="qc" className="h-full m-0">
              <QualityDirectorPanel />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </AppShell>
  );
}

/**
 * VPE Panel - Video Parsing Engine
 * Extracts Logic Vector from video content
 */
function VPEPanel() {
  const [videoUrl, setVideoUrl] = useState("");
  const [auteurHint, setAuteurHint] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    logicVector?: Record<string, unknown>;
    confidence?: number;
  } | null>(null);

  const handleAnalyze = async () => {
    if (!videoUrl) return;

    setIsLoading(true);
    try {
      const response = await fetch("/api/dna-lab/vpe/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_uri: videoUrl,
          auteur_hint: auteurHint || undefined,
          extract_shots: true,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setResult({
          logicVector: data.logic_vector,
          confidence: data.confidence,
        });
      }
    } catch (error) {
      console.error("VPE analysis failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Video className="w-5 h-5" />
            Video Parsing Engine (VPE)
          </CardTitle>
          <CardDescription>
            영상을 분석하여 거장의 시네마틱 DNA (Logic Vector)를 추출합니다.
            Cadence, Composition, Camera Grammar, Lighting, Color Science를 분석합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">영상 URL</label>
            <input
              type="url"
              placeholder="gs://bucket/video.mp4 또는 YouTube URL"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">거장 힌트 (선택)</label>
            <select
              value={auteurHint}
              onChange={(e) => setAuteurHint(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
            >
              <option value="">자동 감지</option>
              <option value="bong">봉준호</option>
              <option value="nolan">크리스토퍼 놀란</option>
              <option value="kubrick">스탠리 큐브릭</option>
              <option value="wong">왕가위</option>
              <option value="tarantino">쿠엔틴 타란티노</option>
              <option value="park">박찬욱</option>
              <option value="spielberg">스티븐 스필버그</option>
              <option value="fincher">데이비드 핀처</option>
              <option value="villeneuve">드니 빌뇌브</option>
              <option value="wes_anderson">웨스 앤더슨</option>
            </select>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!videoUrl || isLoading}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading ? "분석 중..." : "Logic Vector 추출"}
          </button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              분석 결과
              {result.confidence && (
                <Badge variant="secondary">
                  신뢰도: {Math.round(result.confidence * 100)}%
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="p-4 bg-muted rounded-md overflow-auto text-sm">
              {JSON.stringify(result.logicVector, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
