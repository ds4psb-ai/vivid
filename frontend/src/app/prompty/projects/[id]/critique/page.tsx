"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  api,
  PromptyCritiqueHistory,
  PromptyCritiqueScore,
} from "@/lib/api";

// Default critique checklist
const DEFAULT_CHECKLIST = [
  { id: "composition", label: "구도", description: "시각적 균형과 구성" },
  { id: "consistency", label: "일관성", description: "스타일과 캐릭터 일관성" },
  { id: "lighting", label: "조명", description: "조명 품질과 분위기" },
  { id: "detail", label: "디테일", description: "세부 묘사 품질" },
  { id: "emotion", label: "감정", description: "의도한 감정 전달" },
];

export default function CritiquePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const projectId = params.id as string;
  const stage = searchParams.get("stage") || "";
  const stepId = searchParams.get("step") || "";

  const [history, setHistory] = useState<PromptyCritiqueHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [scores, setScores] = useState<Record<string, { score: number; notes: string }>>({});
  const [notes, setNotes] = useState("");

  const loadHistory = useCallback(async () => {
    try {
      const response = await api.getPromptyCritiqueHistory(projectId);
      setHistory(response);
    } catch (error) {
      console.error("Failed to load critique history:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  function updateScore(itemId: string, score: number) {
    setScores((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], score, notes: prev[itemId]?.notes || "" },
    }));
  }

  function updateNotes(itemId: string, itemNotes: string) {
    setScores((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], score: prev[itemId]?.score || 5, notes: itemNotes },
    }));
  }

  async function submitCritique() {
    if (!stage || !stepId) {
      alert("단계와 스텝 정보가 필요합니다. 워크플로우 페이지에서 Critique를 시작하세요.");
      return;
    }

    const hasAllScores = DEFAULT_CHECKLIST.every((item) => scores[item.id]?.score);
    if (!hasAllScores) {
      alert("모든 항목에 점수를 입력해주세요.");
      return;
    }

    setSubmitting(true);
    try {
      const critiqueScores: Record<string, PromptyCritiqueScore> = {};
      DEFAULT_CHECKLIST.forEach((item) => {
        critiqueScores[item.id] = {
          score: scores[item.id].score,
          notes: scores[item.id].notes || undefined,
        };
      });

      await api.submitPromptyCritique({
        project_id: projectId,
        stage,
        step_id: stepId,
        scores: critiqueScores,
        notes: notes || undefined,
      });

      alert("Critique가 제출되었습니다!");
      setScores({});
      setNotes("");
      await loadHistory();
    } catch (error) {
      console.error("Failed to submit critique:", error);
      alert("Critique 제출에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex items-center gap-4">
          <Link
            href={`/prompty/projects/${projectId}`}
            className="text-muted-foreground hover:text-foreground transition"
          >
            ← 워크플로우로 돌아가기
          </Link>
          <span className="text-muted-foreground">/</span>
          <h1 className="font-semibold">Critique 평가</h1>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-[1fr,400px] gap-8">
          {/* Main - Submit Form */}
          <main className="space-y-6">
            <div className="rounded-xl border border-border bg-card p-6">
              <h2 className="text-xl font-bold mb-2">새 Critique 제출</h2>
              {stage && stepId ? (
                <p className="text-muted-foreground mb-6">
                  {stage.toUpperCase()} / {stepId} 단계 평가
                </p>
              ) : (
                <p className="text-yellow-500 mb-6">
                  워크플로우 페이지에서 특정 단계의 Critique를 시작하세요.
                </p>
              )}

              {/* Checklist */}
              <div className="space-y-6">
                {DEFAULT_CHECKLIST.map((item) => (
                  <div key={item.id} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{item.label}</h3>
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                      </div>
                      <span className="text-2xl font-bold text-primary">
                        {scores[item.id]?.score || "-"}
                      </span>
                    </div>

                    {/* Score Slider */}
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-muted-foreground w-4">1</span>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={scores[item.id]?.score || 5}
                        onChange={(e) => updateScore(item.id, parseInt(e.target.value))}
                        className="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                      />
                      <span className="text-xs text-muted-foreground w-4">10</span>
                    </div>

                    {/* Notes */}
                    <input
                      type="text"
                      placeholder="메모 (선택)"
                      value={scores[item.id]?.notes || ""}
                      onChange={(e) => updateNotes(item.id, e.target.value)}
                      className="w-full px-3 py-2 bg-muted rounded-lg text-sm"
                    />
                  </div>
                ))}
              </div>

              {/* Overall Notes */}
              <div className="mt-8">
                <label className="block font-medium mb-2">전체 메모</label>
                <textarea
                  placeholder="이 단계에 대한 전체적인 의견..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 bg-muted rounded-lg resize-none"
                />
              </div>

              {/* Submit Button */}
              <button
                onClick={submitCritique}
                disabled={submitting || !stage || !stepId}
                className="w-full mt-6 px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50"
              >
                {submitting ? "제출 중..." : "Critique 제출"}
              </button>
            </div>
          </main>

          {/* Sidebar - History */}
          <aside className="space-y-6">
            {/* Stats */}
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold mb-4">통계</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {history?.average_score.toFixed(1) || "-"}
                  </div>
                  <div className="text-xs text-muted-foreground">평균 점수</div>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-2xl font-bold text-green-500">
                    {history?.pass_rate.toFixed(0) || "-"}%
                  </div>
                  <div className="text-xs text-muted-foreground">합격률</div>
                </div>
              </div>
            </div>

            {/* History */}
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold mb-4">
                Critique 이력 ({history?.total_critiques || 0})
              </h3>

              {history?.items.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  아직 Critique 기록이 없습니다.
                </p>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {history?.items.map((critique) => (
                    <div
                      key={critique.id}
                      className={`p-4 rounded-lg ${
                        critique.passed ? "bg-green-500/10" : "bg-red-500/10"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">
                          {critique.stage} / {critique.step_id}
                        </span>
                        <span
                          className={`text-sm font-bold ${
                            critique.passed ? "text-green-500" : "text-red-500"
                          }`}
                        >
                          {critique.total_score.toFixed(0)}점
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Revision #{critique.revision_number}</span>
                        <span>
                          {new Date(critique.created_at).toLocaleDateString("ko-KR")}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
