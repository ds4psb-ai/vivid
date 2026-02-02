"use client";

import { useState } from "react";
import { TIKITAKA_STEPS, getAiRoleDisplayName, getAiRoleColorClass } from "@/lib/tikitaka-prompts";

interface QuickResumeBannerProps {
  currentStep: number;
  projectName: string;
  lastActivity?: string;
  blockers?: string[];
  onResume?: () => void;
  onCopyResumePrompt?: () => void;
}

/**
 * QuickResumeBanner - Quick resume banner
 *
 * Shows current task status and allows quick resume
 */
export function QuickResumeBanner({
  currentStep,
  projectName,
  lastActivity,
  blockers = [],
  onResume,
  onCopyResumePrompt,
}: QuickResumeBannerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const stepConfig = TIKITAKA_STEPS[currentStep];

  if (!stepConfig) return null;

  const resumePrompt = generateResumePrompt(currentStep, projectName);

  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 overflow-hidden">
      {/* Main Banner */}
      <div
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-primary/10 transition"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-4">
          {/* Step indicator */}
          <div className="w-12 h-12 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold">
            {currentStep}/6
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">{projectName}</span>
              <span className="text-muted-foreground">-</span>
              <span
                className={`px-2 py-0.5 rounded text-xs ${getAiRoleColorClass(stepConfig.aiRole)}`}
              >
                {stepConfig.name}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Next: {getAiRoleDisplayName(stepConfig.aiRole)} action required
              {lastActivity && (
                <span className="ml-2 opacity-60">- Last: {formatRelativeTime(lastActivity)}</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {blockers.length > 0 && (
            <span className="px-2 py-1 rounded bg-yellow-500/10 text-yellow-500 text-xs">
              {blockers.length} blocker{blockers.length > 1 ? "s" : ""}
            </span>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              onResume?.();
            }}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition text-sm"
          >
            Resume
          </button>

          <span className="text-muted-foreground">
            {isExpanded ? "Hide" : "Show"}
          </span>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-border p-4 space-y-4">
          {/* Blockers */}
          {blockers.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 text-yellow-500">Blockers</h4>
              <ul className="space-y-1">
                {blockers.map((blocker, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span>-</span>
                    <span>{blocker}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Resume Prompt */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold">Resume Prompt</h4>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(resumePrompt);
                  onCopyResumePrompt?.();
                }}
                className="text-xs text-primary hover:underline"
              >
                Copy
              </button>
            </div>
            <pre className="p-3 bg-muted rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono">
              {resumePrompt}
            </pre>
          </div>

          {/* Step Progress Overview */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Progress</h4>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5, 6].map((step) => (
                <div
                  key={step}
                  className={`
                    flex-1 h-2 rounded-full
                    ${step < currentStep ? "bg-green-500" : ""}
                    ${step === currentStep ? "bg-primary animate-pulse" : ""}
                    ${step > currentStep ? "bg-muted" : ""}
                  `}
                  title={TIKITAKA_STEPS[step]?.name}
                />
              ))}
            </div>
            <div className="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>Start</span>
              <span>Complete</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Generate resume prompt for AI
 */
function generateResumePrompt(currentStep: number, projectName: string): string {
  const stepConfig = TIKITAKA_STEPS[currentStep];
  if (!stepConfig) return "";

  return `Resume ${projectName} - Step ${currentStep}: ${stepConfig.name}

Current Action: ${stepConfig.aiRole === "user" ? "User action required" : `${getAiRoleDisplayName(stepConfig.aiRole)} prompt`}

Expected Output: ${stepConfig.expectedOutput}

Next step after completion: ${currentStep < 6 ? `Step ${currentStep + 1} (${TIKITAKA_STEPS[currentStep + 1]?.name})` : "Complete!"}`;
}

/**
 * Format relative time
 */
function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  } catch {
    return "";
  }
}

export default QuickResumeBanner;
