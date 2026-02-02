"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  api,
  PromptyGuideResponse,
  PromptyStepInfo,
  PromptyStageInfo,
} from "@/lib/api";

export default function ProjectWorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [guide, setGuide] = useState<PromptyGuideResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [advancing, setAdvancing] = useState(false);

  const loadGuide = useCallback(async () => {
    try {
      const response = await api.getPromptyGuide(projectId);
      setGuide(response);
    } catch (error) {
      console.error("Failed to load guide:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadGuide();
  }, [loadGuide]);

  async function copyPrompt() {
    if (!guide?.current_step_info?.prompt_text) return;

    await navigator.clipboard.writeText(guide.current_step_info.prompt_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);

    // Log action
    await api.logPromptyAction(
      projectId,
      "copy_prompt",
      guide.current_stage,
      guide.current_step
    );
  }

  async function advanceToNext() {
    setAdvancing(true);
    try {
      const response = await api.advancePromptyStep(projectId);
      if (response.completed) {
        alert("축하합니다! 프로젝트를 완료했습니다.");
      }
      await loadGuide();
    } catch (error) {
      console.error("Failed to advance:", error);
    } finally {
      setAdvancing(false);
    }
  }

  function getStageStatus(stage: PromptyStageInfo) {
    if (stage.status === "completed") return "✅";
    if (stage.status === "in_progress") return "◉";
    return "○";
  }

  function getStepStatus(step: PromptyStepInfo) {
    if (step.status === "completed") return "✅";
    if (step.status === "in_progress") return "🔄";
    return "○";
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!guide) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">프로젝트를 찾을 수 없습니다</h1>
        <Link href="/prompty/projects" className="text-primary hover:underline">
          프로젝트 목록으로 돌아가기
        </Link>
      </div>
    );
  }

  const currentStep = guide.current_step_info;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/prompty/projects"
              className="text-muted-foreground hover:text-foreground transition"
            >
              ← 프로젝트 목록
            </Link>
            <span className="text-muted-foreground">/</span>
            <h1 className="font-semibold">{guide.project_name}</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Stage {guide.stages.findIndex((s) => s.id === guide.current_stage) + 1} / {guide.stages.length}
            </span>
            <Link
              href={`/prompty/projects/${projectId}/critique`}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition text-sm"
            >
              Critique 평가
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-[300px,1fr] gap-8">
          {/* Sidebar - Progress */}
          <aside className="space-y-6">
            <div className="rounded-xl border border-border bg-card p-4">
              <h2 className="font-semibold mb-4">진행 상황</h2>

              {/* Overall Progress */}
              <div className="mb-6">
                <div className="flex justify-between text-sm mb-1">
                  <span>전체 진행률</span>
                  <span>{guide.progress_percent}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${guide.progress_percent}%` }}
                  />
                </div>
              </div>

              {/* Stages */}
              <div className="space-y-3">
                {guide.stages.map((stage) => (
                  <div key={stage.id} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span>{getStageStatus(stage)}</span>
                      <span
                        className={`font-medium ${
                          stage.id === guide.current_stage
                            ? "text-primary"
                            : stage.status === "completed"
                            ? "text-muted-foreground"
                            : ""
                        }`}
                      >
                        {stage.name}
                      </span>
                    </div>

                    {/* Steps (expanded if current stage) */}
                    {stage.id === guide.current_stage && stage.steps.length > 0 && (
                      <div className="ml-6 space-y-1">
                        {stage.steps.map((step) => (
                          <div
                            key={step.id}
                            className={`text-sm flex items-center gap-2 ${
                              step.id === guide.current_step
                                ? "text-primary font-medium"
                                : "text-muted-foreground"
                            }`}
                          >
                            <span className="text-xs">{getStepStatus(step)}</span>
                            <span>{step.name}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </aside>

          {/* Main Content - Current Step */}
          <main className="space-y-6">
            {currentStep ? (
              <>
                {/* Step Header */}
                <div className="rounded-xl border border-border bg-card p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <span className="text-sm text-primary font-medium">
                        {guide.current_stage.toUpperCase()}
                      </span>
                      <h2 className="text-2xl font-bold mt-1">{currentStep.name}</h2>
                    </div>
                    {currentStep.score && (
                      <span className="px-3 py-1 bg-green-500/10 text-green-500 rounded-lg text-sm">
                        Score: {currentStep.score}
                      </span>
                    )}
                  </div>

                  {currentStep.description && (
                    <p className="text-muted-foreground">{currentStep.description}</p>
                  )}
                </div>

                {/* Prompt Section */}
                {currentStep.prompt_text && (
                  <div className="rounded-xl border border-border bg-card p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold">프롬프트</h3>
                      <button
                        onClick={copyPrompt}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition text-sm flex items-center gap-2"
                      >
                        {copied ? (
                          <>✓ 복사됨</>
                        ) : (
                          <>📋 클립보드에 복사</>
                        )}
                      </button>
                    </div>

                    <pre className="p-4 bg-muted rounded-lg text-sm overflow-x-auto whitespace-pre-wrap font-mono">
                      {currentStep.prompt_text}
                    </pre>
                  </div>
                )}

                {/* External Tool Link */}
                {currentStep.external_tool && (
                  <div className="rounded-xl border border-border bg-card p-6">
                    <h3 className="font-semibold mb-4">외부 도구</h3>
                    <a
                      href={currentStep.external_url || getToolUrl(currentStep.external_tool)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() =>
                        api.logPromptyAction(
                          projectId,
                          "open_external",
                          guide.current_stage,
                          guide.current_step,
                          { tool: currentStep.external_tool }
                        )
                      }
                      className="inline-flex items-center gap-2 px-6 py-3 bg-muted rounded-lg hover:bg-muted/80 transition"
                    >
                      <span className="text-lg">{getToolIcon(currentStep.external_tool)}</span>
                      <span className="font-medium">{getToolName(currentStep.external_tool)} 열기</span>
                      <span>→</span>
                    </a>
                  </div>
                )}

                {/* Tips */}
                {currentStep.tips && currentStep.tips.length > 0 && (
                  <div className="rounded-xl border border-border bg-card p-6">
                    <h3 className="font-semibold mb-4">💡 팁</h3>
                    <ul className="space-y-2">
                      {currentStep.tips.map((tip, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <span className="text-primary">•</span>
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-between items-center p-6 rounded-xl border border-border bg-card">
                  <Link
                    href={`/prompty/projects/${projectId}/critique?stage=${guide.current_stage}&step=${guide.current_step}`}
                    className="px-6 py-3 border border-border rounded-lg hover:bg-accent transition"
                  >
                    ✅ Critique 평가하기
                  </Link>
                  <button
                    onClick={advanceToNext}
                    disabled={advancing}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
                  >
                    {advancing ? "이동 중..." : "다음 단계로 →"}
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-16 rounded-xl border border-border bg-card">
                <div className="text-6xl mb-4">🎉</div>
                <h2 className="text-2xl font-bold mb-2">프로젝트 완료!</h2>
                <p className="text-muted-foreground mb-6">
                  모든 단계를 완료했습니다. Critique 결과를 확인하세요.
                </p>
                <Link
                  href={`/prompty/projects/${projectId}/critique`}
                  className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
                >
                  Critique 결과 보기
                </Link>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

// Helper functions
function getToolUrl(tool: string): string {
  const urls: Record<string, string> = {
    nanobanana: "https://nanobanana.com",
    kling: "https://klingai.com",
    davinci: "https://www.blackmagicdesign.com/products/davinciresolve",
    suno: "https://suno.ai",
  };
  return urls[tool] || "#";
}

function getToolIcon(tool: string): string {
  const icons: Record<string, string> = {
    nanobanana: "🍌",
    kling: "🎬",
    davinci: "🎞️",
    suno: "🎵",
  };
  return icons[tool] || "🔧";
}

function getToolName(tool: string): string {
  const names: Record<string, string> = {
    nanobanana: "NanoBanana",
    kling: "Kling AI",
    davinci: "DaVinci Resolve",
    suno: "Suno AI",
  };
  return names[tool] || tool;
}
