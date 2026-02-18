"use client";

import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import {
  api,
  type FoundryC2PAExportResponse,
  type FoundryHealthResponse,
  type FoundryRecommendationResponse,
  type FoundryStatusResponse,
} from "@/lib/api";

const DEMO_RECOMMENDATION_PAYLOAD = {
  scene_context: {
    project_id: "demo-project",
    scene_id: "scene-03",
    target_emotion: "anxiety",
    location: "warehouse",
    characters: ["hero", "rival"],
    desired_camera_rhythm: "dynamic",
    intent_tags: ["power", "isolation"],
  },
  candidates: [
    {
      candidate_id: "cand-a",
      title: "Low-angle confrontation",
      shots: [
        {
          shot_id: "shot-1",
          shot_size: "medium",
          camera_angle: "low_angle",
          camera_movement: "tracking",
          emotion_tone: "anxiety",
          transition_to_next: "cut",
          location: "warehouse",
          characters: ["hero", "rival"],
        },
      ],
      pattern_tags: ["power"],
      mise_en_scene_score: 0.82,
      story_intent_fit: 0.78,
      director_style_fit: 0.72,
      execution_feasibility: 0.86,
      clone_risk: 0.21,
    },
  ],
  rights_action: "reference",
  continuity_floor: 0.6,
  model: "foundry-runtime-v1",
  input_type: "ui_demo",
} as const;

export default function FoundryPage() {
  const [health, setHealth] = useState<FoundryHealthResponse | null>(null);
  const [status, setStatus] = useState<FoundryStatusResponse | null>(null);
  const [recommendation, setRecommendation] = useState<FoundryRecommendationResponse | null>(null);
  const [c2pa, setC2pa] = useState<FoundryC2PAExportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [c2paLoading, setC2paLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const topResult = useMemo(() => recommendation?.ranked?.[0], [recommendation]);

  const loadFoundryStatus = async () => {
    setError(null);
    try {
      const [healthRes, statusRes] = await Promise.all([
        api.getFoundryHealth(),
        api.getFoundryStatus(),
      ]);
      setHealth(healthRes);
      setStatus(statusRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Foundry 상태 조회 실패");
    }
  };

  const runDemoRecommendation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getFoundryRecommendations(DEMO_RECOMMENDATION_PAYLOAD);
      setRecommendation(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "추천 실행 실패");
    } finally {
      setLoading(false);
    }
  };

  const runDemoC2PAExport = async () => {
    setC2paLoading(true);
    setError(null);
    try {
      const result = await api.exportFoundryC2PAManifest({
        project_id: "demo-project",
        scene_id: "scene-03",
        asset_id: "asset-demo-03",
        title: "Demo Scene 03",
        generator_model: "gemini-3-pro",
        source_license: "cc-by-4.0",
        actions: [
          { action: "c2pa.created", parameters: { prompt: "low-angle confrontation" } },
          { action: "c2pa.edited", parameters: { tool: "kling-3.0" } },
        ],
        provenance_trace: [
          { asset_id: "source-clip-1", relationship: "componentOf", title: "Reference Clip" },
          { asset_id: "source-image-2", relationship: "componentOf", title: "Mood Image" },
        ],
        model: "foundry-runtime-v1",
        input_type: "ui_demo_provenance",
      });
      setC2pa(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "C2PA export 실패");
    } finally {
      setC2paLoading(false);
    }
  };

  useEffect(() => {
    void loadFoundryStatus();
  }, []);

  return (
    <AppShell showTopBar={false}>
      <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-bold text-[var(--fg-0)]">Original-IP Foundry</h1>
          <p className="text-sm text-[var(--fg-muted)]">
            권리 게이트 + continuity 우선 추천 + 실험 레이어를 하나의 런타임으로 점검합니다.
          </p>
        </header>

        {error ? (
          <div className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-[var(--glass-border)] bg-[var(--surface-1)] p-4">
            <h2 className="text-sm font-semibold text-[var(--fg-0)]">Foundry Health</h2>
            <pre className="mt-3 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>

          <div className="rounded-2xl border border-[var(--glass-border)] bg-[var(--surface-1)] p-4">
            <h2 className="text-sm font-semibold text-[var(--fg-0)]">Foundry Status</h2>
            <pre className="mt-3 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
              {JSON.stringify(status, null, 2)}
            </pre>
          </div>
        </section>

        <section className="rounded-2xl border border-[var(--glass-border)] bg-[var(--surface-1)] p-4">
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => void loadFoundryStatus()}
              className="rounded-lg border border-[var(--glass-border)] px-3 py-2 text-sm hover:bg-black/5"
            >
              상태 새로고침
            </button>
            <button
              onClick={() => void runDemoRecommendation()}
              disabled={loading}
              className="rounded-lg bg-[var(--color-brand-primary)] px-3 py-2 text-sm text-white disabled:opacity-60"
            >
              {loading ? "추천 실행 중..." : "데모 추천 실행"}
            </button>
            <button
              onClick={() => void runDemoC2PAExport()}
              disabled={c2paLoading}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-60"
            >
              {c2paLoading ? "C2PA Export 중..." : "C2PA Export 데모"}
            </button>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold text-[var(--fg-0)]">Top Candidate</h3>
              <pre className="mt-2 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
                {JSON.stringify(topResult, null, 2)}
              </pre>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--fg-0)]">Raw Recommendation Payload</h3>
              <pre className="mt-2 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
                {JSON.stringify(recommendation, null, 2)}
              </pre>
            </div>
          </div>

          <div className="mt-4">
            <h3 className="text-sm font-semibold text-[var(--fg-0)]">C2PA Manifest Export</h3>
            <pre className="mt-2 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
              {JSON.stringify(c2pa, null, 2)}
            </pre>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
