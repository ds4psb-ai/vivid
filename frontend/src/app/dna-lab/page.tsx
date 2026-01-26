"use client";

import { useState } from "react";
import { Dna, Video, Palette, Brain, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MegaAppShell, type MegaAppTab } from "@/components/mega-app";

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

const TABS: MegaAppTab[] = [
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

export default function DNALabPage() {
  return (
    <MegaAppShell
      appId="dna-lab"
      title="DNA Lab"
      subtitle="거장 DNA 분석 및 오케스트레이션"
      icon={Dna}
      tabs={TABS}
      defaultTab="vpe"
    >
      {(activeTab) => (
        <>
          {activeTab === "vpe" && (
            <div className="p-4">
              <VPEPanel />
            </div>
          )}
          {activeTab === "ad" && <AestheticDirectorPanel />}
          {activeTab === "mirror" && <AbyssMirrorPanel />}
          {activeTab === "qc" && <QualityDirectorPanel />}
        </>
      )}
    </MegaAppShell>
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
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Video className="w-5 h-5" />
            Video Parsing Engine (VPE)
          </CardTitle>
          <CardDescription className="text-white/60">
            영상을 분석하여 거장의 시네마틱 DNA (Logic Vector)를 추출합니다.
            Cadence, Composition, Camera Grammar, Lighting, Color Science를 분석합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-white/80">영상 URL</label>
            <input
              type="url"
              placeholder="gs://bucket/video.mp4 또는 YouTube URL"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-white/5 border-white/10 text-white placeholder:text-white/40"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white/80">거장 힌트 (선택)</label>
            <select
              value={auteurHint}
              onChange={(e) => setAuteurHint(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-white/5 border-white/10 text-white"
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
            className="w-full px-4 py-2 bg-white/10 text-white rounded-md hover:bg-white/20 disabled:opacity-50 transition-colors"
          >
            {isLoading ? "분석 중..." : "Logic Vector 추출"}
          </button>
        </CardContent>
      </Card>

      {result && (
        <Card className="bg-white/5 border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              분석 결과
              {result.confidence && (
                <Badge variant="secondary" className="bg-emerald-500/20 text-emerald-300">
                  신뢰도: {Math.round(result.confidence * 100)}%
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="p-4 bg-black/30 rounded-md overflow-auto text-sm text-white/80">
              {JSON.stringify(result.logicVector, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
