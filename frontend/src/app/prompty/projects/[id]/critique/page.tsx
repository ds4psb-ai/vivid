"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  api,
  PromptyCritiqueHistory,
  PromptyCritiqueScore,
} from "@/lib/api";
import {
  CritiqueChecklist,
  CritiqueItem,
  DEFAULT_CRITIQUE_ITEMS,
  CritiqueInput,
  CritiqueResult,
  CritiqueHistory,
  CritiqueIteration,
} from "@/components/prompty";

type ViewMode = "quick" | "detailed";

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
  const [critiqueItems, setCritiqueItems] = useState<CritiqueItem[]>(DEFAULT_CRITIQUE_ITEMS);
  const [passingScore, setPassingScore] = useState(85); // Updated to 85 (PASS threshold)
  const [viewMode, setViewMode] = useState<ViewMode>("quick");

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

  const loadCritiqueConfig = useCallback(async () => {
    try {
      const project = await api.getPromptyProject(projectId);
      if (project.template_id) {
        const template = await api.getPromptyTemplate(project.template_id);
        if (template.critique_config) {
          const config = template.critique_config as {
            items?: CritiqueItem[];
            passing_score?: number;
          };
          if (config.items && config.items.length > 0) {
            setCritiqueItems(config.items);
          }
          if (config.passing_score) {
            setPassingScore(config.passing_score);
          }
        }
      }
    } catch (error) {
      console.error("Failed to load critique config:", error);
    }
  }, [projectId]);

  useEffect(() => {
    loadHistory();
    loadCritiqueConfig();
  }, [loadHistory, loadCritiqueConfig]);

  // Convert history to iterations for the step
  const stepIterations = useMemo((): CritiqueIteration[] => {
    if (!history?.items || !stepId) return [];

    return history.items
      .filter((c) => c.step_id === stepId)
      .sort((a, b) => a.revision_number - b.revision_number)
      .map((c) => ({
        iteration: c.revision_number,
        score: c.total_score,
        verdict: c.passed ? "PASS" as const : c.total_score >= 60 ? "REVISE" as const : "REJECT" as const,
        createdAt: c.created_at,
        notes: c.notes || undefined,
      }));
  }, [history, stepId]);

  // Current iteration number
  const currentIteration = stepIterations.length + 1;

  // Handler for quick input mode
  async function handleQuickSubmit(result: CritiqueResult) {
    if (!stage || !stepId) {
      alert("단계와 스텝 정보가 필요합니다.");
      return;
    }

    setSubmitting(true);
    try {
      // Convert quick result to scores format
      const critiqueScores: Record<string, PromptyCritiqueScore> = {
        overall: {
          score: Math.round(result.score / 10), // Convert 0-100 to 1-10
          notes: result.notes || undefined,
        },
      };

      // Include improved prompt in notes if provided
      let fullNotes = result.notes || "";
      if (result.improvedPrompt) {
        fullNotes += `\n\n[개선 프롬프트]\n${result.improvedPrompt}`;
      }

      await api.submitPromptyCritique(projectId, {
        stage,
        step_id: stepId,
        scores: critiqueScores,
        notes: fullNotes || undefined,
      });

      await loadHistory();
    } catch (error) {
      console.error("Failed to submit critique:", error);
      alert("Critique 제출에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  // Handler for detailed checklist mode
  function handleScoreChange(itemId: string, score: number) {
    setScores((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], score, notes: prev[itemId]?.notes || "" },
    }));
  }

  function handleNotesChange(itemId: string, itemNotes: string) {
    setScores((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], score: prev[itemId]?.score || 5, notes: itemNotes },
    }));
  }

  async function submitDetailedCritique() {
    if (!stage || !stepId) {
      alert("단계와 스텝 정보가 필요합니다.");
      return;
    }

    const hasAllScores = critiqueItems.every((item) => scores[item.id]?.score);
    if (!hasAllScores) {
      alert("모든 항목에 점수를 입력해주세요.");
      return;
    }

    setSubmitting(true);
    try {
      const critiqueScores: Record<string, PromptyCritiqueScore> = {};
      critiqueItems.forEach((item) => {
        critiqueScores[item.id] = {
          score: scores[item.id].score,
          notes: scores[item.id].notes || undefined,
        };
      });

      await api.submitPromptyCritique(projectId, {
        stage,
        step_id: stepId,
        scores: critiqueScores,
        notes: notes || undefined,
      });

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
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href={`/prompty/projects/${projectId}`}
              className="text-muted-foreground hover:text-foreground transition"
            >
              ← 워크플로우
            </Link>
            <span className="text-muted-foreground">/</span>
            <h1 className="font-semibold">Critique 평가</h1>
            {stage && stepId && (
              <>
                <span className="text-muted-foreground">/</span>
                <span className="text-sm text-muted-foreground">
                  {stage.toUpperCase()} - {stepId}
                </span>
              </>
            )}
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 bg-muted rounded-lg p-1">
            <button
              onClick={() => setViewMode("quick")}
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                viewMode === "quick"
                  ? "bg-background shadow text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              빠른 입력
            </button>
            <button
              onClick={() => setViewMode("detailed")}
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                viewMode === "detailed"
                  ? "bg-background shadow text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              상세 평가
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {!stage || !stepId ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h2 className="text-xl font-bold mb-2">스텝을 선택하세요</h2>
            <p className="text-muted-foreground mb-6">
              워크플로우 페이지에서 평가할 스텝을 선택하세요.
            </p>
            <Link
              href={`/prompty/projects/${projectId}`}
              className="inline-flex px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
            >
              워크플로우로 이동
            </Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-[1fr,380px] gap-8">
            {/* Main Content */}
            <main className="space-y-6">
              {viewMode === "quick" ? (
                /* Quick Input Mode - CritiqueInput */
                <CritiqueInput
                  projectId={projectId}
                  stageId={stage}
                  stepId={stepId}
                  currentIteration={currentIteration}
                  onSubmit={handleQuickSubmit}
                  isSubmitting={submitting}
                />
              ) : (
                /* Detailed Mode - CritiqueChecklist */
                <div className="rounded-xl border border-border bg-card p-6 space-y-6">
                  <div>
                    <h2 className="text-xl font-bold mb-2">상세 체크리스트</h2>
                    <p className="text-muted-foreground text-sm">
                      각 항목별로 1-10점 점수를 입력하세요. (반복 #{currentIteration})
                    </p>
                  </div>

                  <CritiqueChecklist
                    items={critiqueItems}
                    scores={scores}
                    onScoreChange={handleScoreChange}
                    onNotesChange={handleNotesChange}
                    passingScore={passingScore}
                  />

                  <div className="space-y-3">
                    <label className="block font-medium">전체 메모</label>
                    <textarea
                      placeholder="이 단계에 대한 전체적인 의견..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                      className="w-full px-4 py-3 bg-muted rounded-lg resize-none"
                    />
                  </div>

                  <button
                    onClick={submitDetailedCritique}
                    disabled={submitting}
                    className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50"
                  >
                    {submitting ? "제출 중..." : "Critique 제출"}
                  </button>
                </div>
              )}

              {/* Verdict Guidelines */}
              <div className="rounded-xl border border-border bg-card p-6">
                <h3 className="font-semibold mb-4">📖 판정 기준</h3>
                <div className="grid sm:grid-cols-3 gap-4">
                  <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                    <div className="font-bold text-green-500 mb-1">PASS (85+)</div>
                    <p className="text-sm text-muted-foreground">
                      다음 단계로 진행. 티키타카 완료.
                    </p>
                  </div>
                  <div className="p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                    <div className="font-bold text-yellow-500 mb-1">REVISE (60-84)</div>
                    <p className="text-sm text-muted-foreground">
                      프롬프트 수정 후 재생성.
                    </p>
                  </div>
                  <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                    <div className="font-bold text-red-500 mb-1">REJECT (&lt;60)</div>
                    <p className="text-sm text-muted-foreground">
                      프롬프트 전면 재검토 필요.
                    </p>
                  </div>
                </div>
              </div>
            </main>

            {/* Sidebar */}
            <aside className="space-y-6">
              {/* Tikitaka History Chart */}
              <CritiqueHistory
                iterations={stepIterations}
                targetScore={passingScore}
                stepId={stepId}
              />

              {/* Overall Project Stats */}
              <div className="rounded-xl border border-border bg-card p-6">
                <h3 className="font-semibold mb-4">프로젝트 통계</h3>
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
                <div className="mt-4 text-center text-sm text-muted-foreground">
                  총 {history?.total_critiques || 0}회 평가
                </div>
              </div>

              {/* All History */}
              <div className="rounded-xl border border-border bg-card p-6">
                <h3 className="font-semibold mb-4">
                  전체 이력
                </h3>

                {history?.items.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    아직 기록이 없습니다.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {history?.items.slice(0, 10).map((critique) => (
                      <div
                        key={critique.id}
                        className={`p-3 rounded-lg ${
                          critique.passed ? "bg-green-500/10" : "bg-red-500/10"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">
                            {critique.step_id}
                          </span>
                          <span
                            className={`text-sm font-bold ${
                              critique.passed ? "text-green-500" : "text-red-500"
                            }`}
                          >
                            {critique.total_score.toFixed(0)}점
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
                          <span>#{critique.revision_number}</span>
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
        )}
      </div>
    </div>
  );
}
