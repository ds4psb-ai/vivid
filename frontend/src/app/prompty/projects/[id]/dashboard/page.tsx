"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, PromptyCritiqueHistory, PromptyProject } from "@/lib/api";

interface ScoreData {
  sceneId: string;
  sceneName: string;
  isAnchor: boolean;
  imageScore: number | null;
  videoScore: number | null;
  imageVerdict: "PASS" | "REVISE" | "REJECT" | null;
  videoVerdict: "PASS" | "REVISE" | "REJECT" | null;
  issues: string[];
  suggestions: string[];
}

function getVerdict(score: number | null): "PASS" | "REVISE" | "REJECT" | null {
  if (score === null) return null;
  if (score >= 85) return "PASS";
  if (score >= 60) return "REVISE";
  return "REJECT";
}

function getVerdictColor(verdict: "PASS" | "REVISE" | "REJECT" | null): string {
  switch (verdict) {
    case "PASS":
      return "text-green-500";
    case "REVISE":
      return "text-yellow-500";
    case "REJECT":
      return "text-red-500";
    default:
      return "text-muted-foreground";
  }
}

function getVerdictBg(verdict: "PASS" | "REVISE" | "REJECT" | null): string {
  switch (verdict) {
    case "PASS":
      return "bg-green-500/10 border-green-500/30";
    case "REVISE":
      return "bg-yellow-500/10 border-yellow-500/30";
    case "REJECT":
      return "bg-red-500/10 border-red-500/30";
    default:
      return "bg-muted/50 border-border";
  }
}

function ScoreCard({ data }: { data: ScoreData }) {
  const combinedScore =
    data.imageScore !== null && data.videoScore !== null
      ? Math.round((data.imageScore + data.videoScore) / 2)
      : data.imageScore ?? data.videoScore ?? null;

  const verdict = getVerdict(combinedScore);

  return (
    <div
      className={`rounded-lg border p-4 ${getVerdictBg(verdict)} ${
        data.isAnchor ? "ring-2 ring-primary" : ""
      }`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold">
            {data.isAnchor && <span className="text-primary mr-1">⭐</span>}
            {data.sceneName}
          </h3>
          {data.isAnchor && (
            <span className="text-xs text-primary">ANCHOR</span>
          )}
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${getVerdictColor(verdict)}`}>
            {combinedScore !== null ? combinedScore : "-"}
          </div>
          {verdict && (
            <span className={`text-xs font-medium ${getVerdictColor(verdict)}`}>
              {verdict}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-2">
        {/* Image Score */}
        <div className="flex items-center gap-2 text-sm">
          <span className="w-14 text-muted-foreground">Image</span>
          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                data.imageScore !== null && data.imageScore >= 85
                  ? "bg-green-500"
                  : data.imageScore !== null && data.imageScore >= 60
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${data.imageScore ?? 0}%` }}
            />
          </div>
          <span className="w-10 text-right">
            {data.imageScore !== null ? `${data.imageScore}%` : "-"}
          </span>
        </div>

        {/* Video Score */}
        <div className="flex items-center gap-2 text-sm">
          <span className="w-14 text-muted-foreground">Video</span>
          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                data.videoScore !== null && data.videoScore >= 85
                  ? "bg-green-500"
                  : data.videoScore !== null && data.videoScore >= 60
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${data.videoScore ?? 0}%` }}
            />
          </div>
          <span className="w-10 text-right">
            {data.videoScore !== null ? `${data.videoScore}%` : "-"}
          </span>
        </div>
      </div>

      {/* Issues & Suggestions */}
      {(data.issues.length > 0 || data.suggestions.length > 0) && (
        <div className="mt-3 pt-3 border-t border-border/50 text-xs space-y-1">
          {data.issues.map((issue, i) => (
            <p key={i} className="text-red-400">
              • {issue}
            </p>
          ))}
          {data.suggestions.map((sug, i) => (
            <p key={i} className="text-blue-400">
              → {sug}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<PromptyProject | null>(null);
  const [critiqueHistory, setCritiqueHistory] =
    useState<PromptyCritiqueHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [proj, critiques] = await Promise.all([
          api.getPromptyProject(projectId),
          api.getPromptyCritiqueHistory(projectId),
        ]);
        setProject(proj);
        setCritiqueHistory(critiques);
      } catch (err) {
        setError("Failed to load dashboard data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-muted rounded" />
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <p className="text-destructive mb-4">{error || "Project not found"}</p>
          <Link href="/prompty/projects" className="text-primary hover:underline">
            Back to projects
          </Link>
        </div>
      </div>
    );
  }

  // Build score data from critique history
  const sceneScores: ScoreData[] = [];
  const state = (project.state || {}) as Record<string, unknown>;
  const stages = (state.stages || {}) as Record<string, unknown>;
  const imageStage = (stages.stage2 || {}) as Record<string, unknown>;

  // Get all scenes from state
  Object.entries(imageStage).forEach(([stepId, stepData]: [string, unknown]) => {
    if (typeof stepData === "object" && stepData !== null && stepId.startsWith("scene")) {
      const data = stepData as { description?: string; is_anchor?: boolean };
      const sceneNum = stepId.replace("scene", "");

      // Find critiques for this scene
      const imageCritiques =
        critiqueHistory?.items.filter(
          (c) => c.step_id === stepId && c.stage === "image"
        ) || [];
      const videoCritiques =
        critiqueHistory?.items.filter(
          (c) => c.step_id === stepId && c.stage === "video"
        ) || [];

      const latestImageCritique = imageCritiques[0];
      const latestVideoCritique = videoCritiques[0];

      sceneScores.push({
        sceneId: stepId,
        sceneName: `Scene ${sceneNum}: ${data.description || ""}`,
        isAnchor: data.is_anchor || false,
        imageScore: latestImageCritique?.total_score ?? null,
        videoScore: latestVideoCritique?.total_score ?? null,
        imageVerdict: getVerdict(latestImageCritique?.total_score ?? null),
        videoVerdict: getVerdict(latestVideoCritique?.total_score ?? null),
        issues: [],  // TODO: Add issues to PromptyCritique type
        suggestions: [],  // TODO: Add suggestions to PromptyCritique type
      });
    }
  });

  // Sort: ANCHOR first, then by scene number
  sceneScores.sort((a, b) => {
    if (a.isAnchor && !b.isAnchor) return -1;
    if (!a.isAnchor && b.isAnchor) return 1;
    return parseInt(a.sceneId.replace("scene", "")) - parseInt(b.sceneId.replace("scene", ""));
  });

  // Calculate summary stats
  const stats = {
    total: sceneScores.length,
    pass: sceneScores.filter(
      (s) =>
        getVerdict(
          s.imageScore !== null && s.videoScore !== null
            ? Math.round((s.imageScore + s.videoScore) / 2)
            : s.imageScore ?? s.videoScore ?? null
        ) === "PASS"
    ).length,
    revise: sceneScores.filter(
      (s) =>
        getVerdict(
          s.imageScore !== null && s.videoScore !== null
            ? Math.round((s.imageScore + s.videoScore) / 2)
            : s.imageScore ?? s.videoScore ?? null
        ) === "REVISE"
    ).length,
    reject: sceneScores.filter(
      (s) =>
        getVerdict(
          s.imageScore !== null && s.videoScore !== null
            ? Math.round((s.imageScore + s.videoScore) / 2)
            : s.imageScore ?? s.videoScore ?? null
        ) === "REJECT"
    ).length,
    pending: sceneScores.filter(
      (s) => s.imageScore === null && s.videoScore === null
    ).length,
  };

  const overallScore =
    sceneScores.length > 0
      ? Math.round(
          sceneScores.reduce((sum, s) => {
            const score =
              s.imageScore !== null && s.videoScore !== null
                ? (s.imageScore + s.videoScore) / 2
                : s.imageScore ?? s.videoScore ?? 0;
            return sum + score;
          }, 0) / sceneScores.length
        )
      : 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <Link
            href={`/prompty/projects/${projectId}`}
            className="text-muted-foreground hover:text-foreground text-sm mb-2 inline-block"
          >
            ← Back to Project
          </Link>
          <h1 className="text-2xl font-bold">Quality Dashboard</h1>
          <p className="text-muted-foreground">{project.name}</p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-bold ${getVerdictColor(getVerdict(overallScore))}`}>
            {overallScore}%
          </div>
          <span className="text-muted-foreground">Overall Score</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="flex gap-4 mb-8 text-sm">
        <div className="px-4 py-2 rounded-lg bg-muted">
          Total: <strong>{stats.total}</strong>
        </div>
        <div className="px-4 py-2 rounded-lg bg-green-500/10 text-green-500">
          ✅ PASS: <strong>{stats.pass}</strong>
        </div>
        <div className="px-4 py-2 rounded-lg bg-yellow-500/10 text-yellow-500">
          🔄 REVISE: <strong>{stats.revise}</strong>
        </div>
        <div className="px-4 py-2 rounded-lg bg-red-500/10 text-red-500">
          ❌ REJECT: <strong>{stats.reject}</strong>
        </div>
        <div className="px-4 py-2 rounded-lg bg-muted text-muted-foreground">
          ⏳ Pending: <strong>{stats.pending}</strong>
        </div>
      </div>

      {/* Scene Grid */}
      {sceneScores.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-border rounded-lg">
          <p className="text-muted-foreground mb-4">
            아직 Critique 데이터가 없습니다.
          </p>
          <Link
            href={`/prompty/projects/${projectId}/critique`}
            className="text-primary hover:underline"
          >
            Critique 시작하기 →
          </Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sceneScores.map((data) => (
            <ScoreCard key={data.sceneId} data={data} />
          ))}
        </div>
      )}

      {/* Critique Helper Link */}
      <div className="mt-8 p-4 border border-border rounded-lg bg-card">
        <h3 className="font-semibold mb-2">Critique Helper</h3>
        <p className="text-sm text-muted-foreground mb-3">
          이미지나 영상을 평가하고 점수를 기록하세요.
        </p>
        <Link
          href={`/prompty/projects/${projectId}/critique`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
        >
          <span>📋</span>
          <span>Critique 입력하기</span>
        </Link>
      </div>
    </div>
  );
}
