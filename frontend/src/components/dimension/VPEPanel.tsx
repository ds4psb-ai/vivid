"use client";

/**
 * VPEPanel - Video Parsing Engine Panel
 *
 * Extracts Logic Vector from video content for DNA Lab.
 * Analyzes Cadence, Composition, Camera Grammar, Lighting, Color Science.
 *
 * Part of Mega App Panel Integration (Phase 2)
 *
 * DNA Card Context Integration:
 * - Master DNA: 거장 힌트 자동 설정
 * - Masterpiece DNA: Logic Vector 정보 프리로드
 */

import { useState } from "react";
import { Video } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BaseMegaAppPanel } from "@/components/mega-app/panels";
import { useDNACardContextConsumer } from "@/hooks/useDNACardContextConsumer";
import { DNAContextBanner } from "@/components/dna-card/DNAContextBanner";
import { MASTER_AUTEURS } from "@/components/dna-card/constants";
import type { MasterpieceDNAMetadata } from "@/types/dna-card";

interface VPEResult {
  logicVector?: Record<string, unknown>;
  confidence?: number;
}

interface PrefilledLogicVector {
  compositionStyle?: string;
  lightingPattern?: string;
  pacingSignature?: string;
}

export default function VPEPanel() {
  const [videoUrl, setVideoUrl] = useState("");
  const [auteurHint, setAuteurHint] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VPEResult | null>(null);

  // DNA 카드 컨텍스트 상태
  const [dnaContextInfo, setDnaContextInfo] = useState<{
    type: "master" | "masterpiece" | null;
    name: string;
  } | null>(null);
  const [prefilledLogicVector, setPrefilledLogicVector] =
    useState<PrefilledLogicVector | null>(null);

  // DNA 카드 컨텍스트 소비
  const { dismissContext } = useDNACardContextConsumer({
    onMasterpieceContext: (ipId, metadata: MasterpieceDNAMetadata) => {
      // 작품 DNA → Logic Vector 정보 프리로드
      if (metadata.logicVectorSummary) {
        setPrefilledLogicVector(metadata.logicVectorSummary);
        setDnaContextInfo({
          type: "masterpiece",
          name: ipId,
        });
      }
      // 작품에 연결된 거장이 있으면 힌트 설정
      if (metadata.auteurKey) {
        setAuteurHint(metadata.auteurKey);
      }
    },
    onMasterContext: (auteurKey, metadata) => {
      // 거장 DNA → auteur hint 자동 선택
      setAuteurHint(auteurKey);
      const auteurInfo = MASTER_AUTEURS.find((a) => a.key === auteurKey);
      setDnaContextInfo({
        type: "master",
        name: auteurInfo?.name ?? auteurKey,
      });
    },
    autoConsume: false, // 배너 표시를 위해 자동 클리어 비활성화
  });

  // DNA 컨텍스트 해제
  const handleDismissContext = () => {
    dismissContext();
    setDnaContextInfo(null);
    setPrefilledLogicVector(null);
    setAuteurHint("");
  };

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
    <BaseMegaAppPanel
      title="Video Parsing Engine"
      titleEn="VPE"
      icon={Video}
      description="영상을 분석하여 거장의 시네마틱 DNA (Logic Vector)를 추출합니다. Cadence, Composition, Camera Grammar, Lighting, Color Science를 분석합니다."
      nextStep={{
        app: "story-engine",
        tab: "system-prompt",
        label: "System Prompt 생성하기",
      }}
    >
      {/* DNA Context Banner */}
      {dnaContextInfo && (
        <DNAContextBanner
          cardType={dnaContextInfo.type!}
          cardName={dnaContextInfo.name}
          onDismiss={handleDismissContext}
          additionalInfo={
            dnaContextInfo.type === "master"
              ? "거장 힌트가 자동 설정되었습니다"
              : "Logic Vector 정보가 프리로드되었습니다"
          }
          className="mb-4"
        />
      )}

      {/* Prefilled Logic Vector Preview (작품 DNA에서 진입 시) */}
      {prefilledLogicVector && (
        <Card className="mb-4 bg-emerald-500/10 border-emerald-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-emerald-400 flex items-center gap-2">
              <Video className="w-4 h-4" />
              프리로드된 Logic Vector
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-white/70">
            {prefilledLogicVector.compositionStyle && (
              <div>
                <span className="text-white/50">구도:</span>{" "}
                {prefilledLogicVector.compositionStyle}
              </div>
            )}
            {prefilledLogicVector.lightingPattern && (
              <div>
                <span className="text-white/50">조명:</span>{" "}
                {prefilledLogicVector.lightingPattern}
              </div>
            )}
            {prefilledLogicVector.pacingSignature && (
              <div>
                <span className="text-white/50">페이싱:</span>{" "}
                {prefilledLogicVector.pacingSignature}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Video URL Input */}
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

      {/* Auteur Hint Selector */}
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

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={!videoUrl || isLoading}
        className="w-full px-4 py-2 bg-white/10 text-white rounded-md hover:bg-white/20 disabled:opacity-50 transition-colors"
      >
        {isLoading ? "분석 중..." : "Logic Vector 추출"}
      </button>

      {/* Result Display */}
      {result && (
        <Card className="mt-6 bg-black/30 border-white/10">
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
    </BaseMegaAppPanel>
  );
}
