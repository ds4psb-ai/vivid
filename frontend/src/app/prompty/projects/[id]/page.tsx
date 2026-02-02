"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, PromptyGuideResponse, TikitakaCurrentResponse } from "@/lib/api";
import {
  CopyPromptButton,
  GuideWorkflow,
  ExternalToolLinks,
  TikitakaWorkflow,
  AnchorSelectionGate,
  ToolPromptTabs,
  QuickResumeBanner,
  Scene,
} from "@/components/prompty";

type WorkflowMode = "guide" | "tikitaka";

export default function ProjectWorkflowPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const projectId = params.id as string;

  // Mode from URL query param (default: guide)
  const initialMode = (searchParams.get("mode") as WorkflowMode) || "guide";

  const [mode, setMode] = useState<WorkflowMode>(initialMode);
  const [guide, setGuide] = useState<PromptyGuideResponse | null>(null);
  const [tikitaka, setTikitaka] = useState<TikitakaCurrentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState(false);

  // ANCHOR selection state
  const [anchorSceneId, setAnchorSceneId] = useState<string | undefined>();
  const [showAnchorGate, setShowAnchorGate] = useState(false);

  // Mock scenes for ANCHOR selection (in real app, load from project state)
  const [scenes] = useState<Scene[]>([
    { id: "scene_1", name: "Scene 1", shotType: "Full shot" },
    { id: "scene_2", name: "Scene 2", shotType: "Close-up" },
    { id: "scene_3", name: "Scene 3", shotType: "Medium shot" },
    { id: "scene_4", name: "Scene 4", shotType: "Wide shot" },
  ]);

  const loadGuide = useCallback(async () => {
    try {
      const response = await api.getPromptyGuide(projectId);
      setGuide(response);

      // Check if tikitaka is active
      try {
        const tikitakaState = await api.getPromptyTikitakaCurrent(projectId);
        setTikitaka(tikitakaState);
        setAnchorSceneId(tikitakaState.anchor_scene_id);
        // Auto-switch to tikitaka mode if workflow is active
        if (tikitakaState.tikitaka_id && !tikitakaState.completed_at) {
          setMode("tikitaka");
        }
      } catch {
        // Tikitaka not started, stay in guide mode
      }
    } catch (error) {
      console.error("Failed to load guide:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadGuide();
  }, [loadGuide]);

  async function handleCopyPrompt() {
    if (!guide) return;
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
        alert("Congratulations! Project completed.");
      }
      await loadGuide();
    } catch (error) {
      console.error("Failed to advance:", error);
    } finally {
      setAdvancing(false);
    }
  }

  async function startTikitaka() {
    // Check if ANCHOR is selected when in IMAGE stage
    if (guide?.current_stage === "image" && !anchorSceneId) {
      setShowAnchorGate(true);
      return;
    }

    try {
      const response = await api.startPromptyTikitaka(projectId, anchorSceneId);
      setTikitaka({
        tikitaka_id: response.tikitaka_id,
        current_step: response.current_step,
        anchor_scene_id: response.anchor_scene_id,
        started_at: new Date().toISOString(),
        tool_prompts: {},
      });
      setMode("tikitaka");
      setShowAnchorGate(false);
    } catch (error) {
      console.error("Failed to start tikitaka:", error);
    }
  }

  async function handleAnchorSelect(sceneId: string) {
    setAnchorSceneId(sceneId);
  }

  async function handleAnchorConfirm() {
    if (!anchorSceneId) return;
    await startTikitaka();
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
        <h1 className="text-2xl font-bold mb-4">Project not found</h1>
        <Link href="/prompty/projects" className="text-primary hover:underline">
          Back to projects
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
              Back
            </Link>
            <span className="text-muted-foreground">/</span>
            <h1 className="font-semibold">{guide.project_name}</h1>
          </div>
          <div className="flex items-center gap-4">
            {/* Mode Toggle */}
            <div className="flex rounded-lg border border-border overflow-hidden">
              <button
                onClick={() => setMode("guide")}
                className={`px-4 py-2 text-sm transition ${
                  mode === "guide"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card hover:bg-accent"
                }`}
              >
                Guide
              </button>
              <button
                onClick={() => (tikitaka ? setMode("tikitaka") : startTikitaka())}
                className={`px-4 py-2 text-sm transition ${
                  mode === "tikitaka"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card hover:bg-accent"
                }`}
              >
                Tikitaka
              </button>
            </div>
            <span className="text-sm text-muted-foreground">
              Stage {guide.stages.findIndex((s) => s.id === guide.current_stage) + 1} /{" "}
              {guide.stages.length}
            </span>
            <Link
              href={`/prompty/projects/${projectId}/critique`}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition text-sm"
            >
              Critique
            </Link>
          </div>
        </div>
      </header>

      {/* Quick Resume Banner (if tikitaka active) */}
      {tikitaka && !tikitaka.completed_at && mode === "guide" && (
        <div className="container mx-auto px-4 pt-4">
          <QuickResumeBanner
            currentStep={tikitaka.current_step}
            projectName={guide.project_name}
            lastActivity={tikitaka.started_at}
            onResume={() => setMode("tikitaka")}
          />
        </div>
      )}

      <div className="container mx-auto px-4 py-8">
        {/* ANCHOR Selection Gate */}
        {showAnchorGate && (
          <div className="mb-8">
            <AnchorSelectionGate
              scenes={scenes}
              selectedAnchorId={anchorSceneId}
              onSelect={handleAnchorSelect}
              onConfirm={handleAnchorConfirm}
            />
          </div>
        )}

        {/* Main Content */}
        {!showAnchorGate && (
          <>
            {mode === "tikitaka" && tikitaka ? (
              /* Tikitaka Mode */
              <div className="max-w-4xl mx-auto">
                <TikitakaWorkflow
                  projectId={projectId}
                  initialStep={tikitaka.current_step}
                  anchorSceneId={anchorSceneId}
                  onStepChange={(step) => {
                    setTikitaka((prev) => (prev ? { ...prev, current_step: step } : null));
                  }}
                  onComplete={() => {
                    alert("Tikitaka workflow completed!");
                    loadGuide();
                  }}
                />

                {/* Tool Prompts (Step 5-6) */}
                {tikitaka.current_step >= 5 && Object.keys(tikitaka.tool_prompts).length > 0 && (
                  <div className="mt-8">
                    <ToolPromptTabs
                      prompts={tikitaka.tool_prompts}
                      onCopy={(toolId) => {
                        api.logPromptyAction(projectId, "copy_tool_prompt", undefined, undefined, {
                          tool: toolId,
                          step: tikitaka.current_step,
                        });
                      }}
                    />
                  </div>
                )}
              </div>
            ) : (
              /* Guide Mode */
              <div className="grid lg:grid-cols-[300px,1fr] gap-8">
                {/* Sidebar - Progress */}
                <aside className="space-y-6">
                  <GuideWorkflow
                    stages={guide.stages}
                    currentStage={guide.current_stage}
                    currentStep={guide.current_step}
                    progressPercent={guide.progress_percent}
                  />

                  {/* Start Tikitaka Button */}
                  {guide.current_stage === "image" && !tikitaka && (
                    <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
                      <h4 className="font-semibold mb-2">Tikitaka Mode</h4>
                      <p className="text-sm text-muted-foreground mb-4">
                        Use Dual AI (Gemini + Claude) for 98% quality output.
                      </p>
                      <button
                        onClick={startTikitaka}
                        className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition text-sm"
                      >
                        Start Tikitaka
                      </button>
                    </div>
                  )}
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
                            <h3 className="font-semibold">Prompt</h3>
                            <CopyPromptButton
                              promptText={currentStep.prompt_text}
                              onCopy={handleCopyPrompt}
                            />
                          </div>

                          <pre className="p-4 bg-muted rounded-lg text-sm overflow-x-auto whitespace-pre-wrap font-mono">
                            {currentStep.prompt_text}
                          </pre>
                        </div>
                      )}

                      {/* External Tool Link */}
                      {currentStep.external_tool && (
                        <ExternalToolLinks
                          toolId={currentStep.external_tool}
                          externalUrl={currentStep.external_url}
                          onOpen={() =>
                            api.logPromptyAction(
                              projectId,
                              "open_external",
                              guide.current_stage,
                              guide.current_step,
                              { tool: currentStep.external_tool }
                            )
                          }
                        />
                      )}

                      {/* Tips */}
                      {currentStep.tips && currentStep.tips.length > 0 && (
                        <div className="rounded-xl border border-border bg-card p-6">
                          <h3 className="font-semibold mb-4">Tips</h3>
                          <ul className="space-y-2">
                            {currentStep.tips.map((tip, index) => (
                              <li key={index} className="flex items-start gap-2 text-sm">
                                <span className="text-primary">-</span>
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
                          Critique
                        </Link>
                        <button
                          onClick={advanceToNext}
                          disabled={advancing}
                          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
                        >
                          {advancing ? "Processing..." : "Next Step"}
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-16 rounded-xl border border-border bg-card">
                      <div className="text-6xl mb-4">Done!</div>
                      <h2 className="text-2xl font-bold mb-2">Project Complete!</h2>
                      <p className="text-muted-foreground mb-6">
                        All steps completed. Check your critique results.
                      </p>
                      <Link
                        href={`/prompty/projects/${projectId}/critique`}
                        className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
                      >
                        View Critique Results
                      </Link>
                    </div>
                  )}
                </main>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
