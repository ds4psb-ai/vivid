"use client";

import { useState } from "react";

export interface CritiqueResult {
  iteration: number;
  score: number;
  verdict: "PASS" | "REVISE" | "REJECT";
  notes?: string;
  improvedPrompt?: string;
}

interface CritiqueInputProps {
  projectId: string;
  stageId: string;
  stepId: string;
  currentIteration: number;
  onSubmit: (result: CritiqueResult) => void;
  isSubmitting?: boolean;
}

const VERDICT_THRESHOLD = {
  PASS: 85,
  REVISE_MIN: 60,
};

/**
 * CritiqueInput - 크리틱 결과 수동 입력
 *
 * Gemini CLI에서 평가한 결과를 입력하고
 * Claude가 개선한 프롬프트를 기록
 */
export function CritiqueInput({
  projectId,
  stageId,
  stepId,
  currentIteration,
  onSubmit,
  isSubmitting = false,
}: CritiqueInputProps) {
  const [score, setScore] = useState<number>(75);
  const [verdict, setVerdict] = useState<"PASS" | "REVISE" | "REJECT">("REVISE");
  const [notes, setNotes] = useState("");
  const [improvedPrompt, setImprovedPrompt] = useState("");

  // 점수에 따라 자동으로 verdict 설정
  function handleScoreChange(newScore: number) {
    setScore(newScore);
    if (newScore >= VERDICT_THRESHOLD.PASS) {
      setVerdict("PASS");
    } else if (newScore >= VERDICT_THRESHOLD.REVISE_MIN) {
      setVerdict("REVISE");
    } else {
      setVerdict("REJECT");
    }
  }

  function handleSubmit() {
    onSubmit({
      iteration: currentIteration,
      score,
      verdict,
      notes: notes || undefined,
      improvedPrompt: improvedPrompt || undefined,
    });
  }

  const verdictColors = {
    PASS: "text-green-500 border-green-500 bg-green-500/10",
    REVISE: "text-yellow-500 border-yellow-500 bg-yellow-500/10",
    REJECT: "text-red-500 border-red-500 bg-red-500/10",
  };

  const verdictDescriptions = {
    PASS: "85점 이상 - 다음 단계로 진행",
    REVISE: "60-84점 - 수정 후 재생성",
    REJECT: "60점 미만 - 프롬프트 재검토",
  };

  return (
    <div className="rounded-xl border border-border bg-card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span className="text-2xl">📊</span>
            Critique 결과 입력
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            {stageId.toUpperCase()} / {stepId} - 반복 #{currentIteration}
          </p>
        </div>
        <div
          className={`px-3 py-1 rounded-full text-sm font-medium border ${verdictColors[verdict]}`}
        >
          {verdict}
        </div>
      </div>

      {/* Score Input */}
      <div className="space-y-3">
        <label className="block font-medium">
          Gemini CLI 평가 점수
        </label>
        <div className="flex items-center gap-4">
          <input
            type="number"
            min={0}
            max={100}
            value={score}
            onChange={(e) => handleScoreChange(parseInt(e.target.value) || 0)}
            className="w-24 px-4 py-2 bg-muted rounded-lg text-center text-xl font-bold"
          />
          <span className="text-muted-foreground">/ 100</span>
          <input
            type="range"
            min={0}
            max={100}
            value={score}
            onChange={(e) => handleScoreChange(parseInt(e.target.value))}
            className="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>

      {/* Verdict Selection */}
      <div className="space-y-3">
        <label className="block font-medium">판정</label>
        <div className="grid grid-cols-3 gap-3">
          {(["PASS", "REVISE", "REJECT"] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setVerdict(v)}
              className={`p-3 rounded-lg border-2 transition text-center ${
                verdict === v
                  ? verdictColors[v]
                  : "border-border hover:border-muted-foreground/50"
              }`}
            >
              <div className="font-bold">{v}</div>
              <div className="text-xs text-muted-foreground mt-1">
                {v === "PASS" && "85+"}
                {v === "REVISE" && "60-84"}
                {v === "REJECT" && "<60"}
              </div>
            </button>
          ))}
        </div>
        <p className="text-sm text-muted-foreground">
          {verdictDescriptions[verdict]}
        </p>
      </div>

      {/* Notes from Gemini */}
      <div className="space-y-3">
        <label className="block font-medium">
          Gemini 개선 제안
          <span className="text-muted-foreground font-normal ml-2">(선택)</span>
        </label>
        <textarea
          placeholder="• --no double eyelids 추가&#10;• 네이비 리본 타이 더 강조&#10;• 조명 방향 수정"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
          className="w-full px-4 py-3 bg-muted rounded-lg resize-none text-sm"
        />
      </div>

      {/* Improved Prompt from Claude */}
      {verdict === "REVISE" && (
        <div className="space-y-3">
          <label className="block font-medium">
            Claude 개선 프롬프트
            <span className="text-muted-foreground font-normal ml-2">(선택)</span>
          </label>
          <textarea
            placeholder="Claude Antigravity에서 정제한 프롬프트를 붙여넣기..."
            value={improvedPrompt}
            onChange={(e) => setImprovedPrompt(e.target.value)}
            rows={4}
            className="w-full px-4 py-3 bg-muted rounded-lg resize-none text-sm font-mono"
          />
          <p className="text-xs text-muted-foreground">
            다음 반복 시 이 프롬프트를 사용하여 재생성합니다.
          </p>
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={isSubmitting}
        className={`w-full py-3 rounded-lg font-medium transition ${
          verdict === "PASS"
            ? "bg-green-500 hover:bg-green-600 text-white"
            : verdict === "REVISE"
            ? "bg-yellow-500 hover:bg-yellow-600 text-black"
            : "bg-red-500 hover:bg-red-600 text-white"
        } disabled:opacity-50`}
      >
        {isSubmitting ? "저장 중..." : "기록 저장"}
      </button>
    </div>
  );
}

export default CritiqueInput;
