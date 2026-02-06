"use client";

import type { TabKey } from "../../constants";
import { PageHeader, ContentCard, NextStepButton } from "../shared";
import { useMDParse } from "../../hooks/useMDParse";
import { MDInput } from "./MDInput";
import { AnchorGuidePanel } from "./AnchorGuidePanel";
import { SceneCard } from "./SceneCard";

interface ParseContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function ParseContent({ setActiveTab }: ParseContentProps) {
  const {
    mdInput,
    parseResult,
    activeType,
    copiedStates,
    completedPrompts,
    isDragging,
    activeScenes,
    totalPrompts,
    completedCount,
    warnings,
    getWarningsForScene,
    setMdInput,
    setActiveType,
    setIsDragging,
    handleCopy,
    clearProgress,
    handleFileDrop,
  } = useMDParse();

  // 파일 드래그앤드롭 핸들러
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    await handleFileDrop(e.dataTransfer.files);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const text = await files[0].text();
      setMdInput(text);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="파싱" />

      {/* MD Input */}
      <MDInput
        mdInput={mdInput}
        setMdInput={setMdInput}
        parseResult={parseResult}
        isDragging={isDragging}
        totalPrompts={totalPrompts}
        completedCount={completedCount}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onFileSelect={handleFileSelect}
        onClearProgress={clearProgress}
      />

      {/* Type Tabs */}
      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <>
          <div className="flex items-center gap-4">
            {/* Type Tabs */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveType("ohmage")}
                disabled={!parseResult.hasOhmage}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeType === "ohmage"
                  ? "bg-[var(--color-brand-primary)] text-white"
                  : parseResult.hasOhmage
                    ? "bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-muted)] hover:bg-[var(--surface-3)] hover:text-[var(--fg-0)]"
                    : "bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-muted)]/50 cursor-not-allowed"
                  }`}
              >
                🎭 오마주 ({parseResult.ohmageScenes.length})
              </button>
              <button
                onClick={() => setActiveType("variation")}
                disabled={!parseResult.hasVariation}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeType === "variation"
                  ? "bg-cyan-500 text-white"
                  : parseResult.hasVariation
                    ? "bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-muted)] hover:bg-[var(--surface-3)] hover:text-[var(--fg-0)]"
                    : "bg-[var(--surface-2)] border border-[var(--border-muted)] text-[var(--fg-muted)]/50 cursor-not-allowed"
                  }`}
              >
                ✨ 변주 ({parseResult.variationScenes.length})
              </button>
            </div>

          </div>

          {/* Anchor Guide Panel */}
          {parseResult.anchors.length > 0 && (
            <AnchorGuidePanel anchors={parseResult.anchors} />
          )}

          {/* Global warnings summary */}
          {warnings.length > 0 && (
            <div className="px-3 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-xs font-semibold text-yellow-700 dark:text-yellow-300">
              warning {warnings.length}
            </div>
          )}

          {/* Scene Cards */}
          <div className="space-y-4">
            {activeScenes?.map((scene) => (
              <SceneCard
                key={`${activeType}-${scene.sceneNum}`}
                scene={scene}
                copiedStates={copiedStates}
                completedPrompts={completedPrompts}
                onCopy={handleCopy}
                anchors={parseResult.anchors}
                warnings={getWarningsForScene(scene.sceneNum)}
              />
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!parseResult && (
        <ContentCard>
          <div className="text-center py-8">
            <span className="material-symbols-outlined text-4xl text-[var(--fg-muted)] mb-4 block">content_paste</span>
            <p className="text-[var(--fg-muted)]">MD 붙여넣기</p>
          </div>
        </ContentCard>
      )}

      <NextStepButton onClick={() => setActiveTab("tools")} label="툴 이동" />
    </div>
  );
}
