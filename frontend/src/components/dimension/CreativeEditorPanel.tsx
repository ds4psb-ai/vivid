"use client";

/**
 * CreativeEditorPanel - 크리에이티브 에디터
 *
 * AI-powered editorial review and improvement of creative content.
 * Migrated to Panel Design Unity Compound Component System.
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import {
  PenTool,
  Check,
  Copy,
  Download,
  RefreshCw,
} from "lucide-react";

// ============================================================================
// Constants & Types
// ============================================================================

const DIMENSION_CODE = "qc"; // Creative Editor uses qc dimension
const DIMENSION_KEY = "creative-editor";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

interface EditorialCritique {
  narrative_score: number;
  visual_score: number;
  pacing_score: number;
  key_issues: string[];
}

interface Change {
  type: string;
  description: string;
}

interface EditorResult {
  critique: EditorialCritique;
  original_content: string;
  improved_content: string;
  changes_made: Change[];
}

const PERSONAS = [
  {
    value: "Senior Editor",
    label: "수석 에디터 (밸런스 중시)",
    desc: "전체적인 완성도와 흐름을 개선합니다.",
  },
  {
    value: "Ruthless Critic",
    label: "냉철한 비평가 (약점 공략)",
    desc: "논리적 허점과 개연성을 집중 타격합니다.",
  },
  {
    value: "Commercial Producer",
    label: "흥행 프로듀서 (대중성)",
    desc: "임팩트와 대중적 재미를 극대화합니다.",
  },
  {
    value: "Artistic Director",
    label: "예술 감독 (미학)",
    desc: "표현의 깊이와 예술적 가치를 높입니다.",
  },
];

// ============================================================================
// Main Export
// ============================================================================

export default function CreativeEditorPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <CreativeEditorContent />
    </DimensionPanel>
  );
}

// ============================================================================
// Content Component
// ============================================================================

function CreativeEditorContent() {
  const { token, setLoading, setResult, setError, classes } = useDimensionPanel();

  // Form state
  const [content, setContent] = useState("");
  const [context, setContext] = useState("");
  const [persona, setPersona] = useState("Senior Editor");
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Result state
  const [editorResult, setEditorResult] = useState<EditorResult | null>(null);

  // BYOK and credits
  const { byokKey } = useBYOK();
  const creditCtx = useCreditContextOptional();
  const { getToolByDimension } = useDimensionConfig();
  const toolConfig = getToolByDimension("CE");
  const CREDIT_COST = toolConfig?.creditCost ?? 5;

  const { exportJSON, copyToClipboard } = useResultExport();

  // Async operation hook
  const {
    isLoading,
    error,
    execute,
    retry,
    canRetry,
  } = useAsyncOperation<{ success: boolean; output: EditorResult; error?: string }>({
    onSuccess: (data) => {
      if (data.success) {
        setEditorResult(data.output);
        setResult(data.output);
        if (!byokKey && creditCtx) {
          void creditCtx.refresh();
        }
      }
    },
    onError: (err) => {
      setError(err);
      if (err.message.includes("크레딧") || err.message.includes("402")) {
        setShowCreditModal(true);
      }
    },
  });

  // Sync loading state to context
  const wrappedExecute = useCallback(
    async (url: string, payload: object, headers?: Record<string, string>) => {
      setLoading(true);
      try {
        return await execute(url, payload, headers);
      } finally {
        setLoading(false);
      }
    },
    [execute, setLoading]
  );

  const handleRunEditor = useCallback(async () => {
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setValidationError("검토할 콘텐츠를 입력해주세요.");
      return;
    }
    setValidationError(null);

    if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
      setShowCreditModal(true);
      return;
    }

    await wrappedExecute(
      `${API_BASE}/api/dimension/quality/editor`,
      {
        content: trimmedContent,
        context: context || "General Creative Content",
        persona,
        model: "gemini-3-pro-preview",
        use_rag: true,
      },
      getBYOKHeaders(byokKey)
    );
  }, [content, context, persona, byokKey, creditCtx, wrappedExecute, CREDIT_COST]);

  const displayError = validationError || error;

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <>
      <DimensionPanel.Header title="크리에이티브 에디터" creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Context Input */}
        <div className="space-y-2">
          <label
            className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1`}
          >
            장르 / 맥락
          </label>
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="예: SF 스릴러 영화, 30초 TV 광고"
            className={`w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 text-sm focus:outline-none focus:border-${token.themeColor}-500/50 transition-all`}
          />
        </div>

        {/* Persona Selection */}
        <div className="space-y-2">
          <label
            className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1`}
          >
            에디토리얼 페르소나
          </label>
          <div className="space-y-2">
            {PERSONAS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPersona(p.value)}
                className={`w-full p-3 rounded-xl border text-left transition-all ${
                  persona === p.value
                    ? `${classes.bg}/10 border-${token.themeColor}-500/50`
                    : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/10"
                }`}
              >
                <div
                  className={`text-sm font-bold ${
                    persona === p.value ? classes.text : "text-slate-900 dark:text-white"
                  }`}
                >
                  {p.label}
                </div>
                <div className="text-xs text-slate-500 dark:text-white/40 mt-1">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <DimensionPanel.GenerateButton
          onClick={handleRunEditor}
          disabled={!content.trim()}
          loading={isLoading}
          creditCost={CREDIT_COST}
          icon={<PenTool className="w-5 h-5" />}
          loadingText="분석 및 수정 중..."
        >
          에디터 실행
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {/* Loading State */}
        <DimensionPanel.Loading message="콘텐츠 분석 및 수정 중..." />

        {/* Error State */}
        {displayError && !isLoading && (
          <DimensionPanel.Error
            error={displayError}
            onRetry={canRetry ? () => void retry() : undefined}
          />
        )}

        {/* Input/Empty State */}
        {!editorResult && !isLoading && !displayError && (
          <ContentInputArea
            content={content}
            setContent={setContent}
            themeColor={token.themeColor}
          />
        )}

        {/* Result Display */}
        {editorResult && !isLoading && (
          <EditorResultDisplay
            result={editorResult}
            onCopy={() => copyToClipboard(editorResult.improved_content)}
            onExport={() => exportJSON(editorResult, "edit-report.json")}
            onRegenerate={handleRunEditor}
            getScoreColor={getScoreColor}
          />
        )}

        {/* Next Dimension Navigation */}
        <DimensionPanel.NextNav currentDimension={DIMENSION_KEY} />
      </DimensionPanel.Content>

      {/* Credit Modal */}
      <InsufficientCreditsModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        requiredCredits={CREDIT_COST}
        currentBalance={creditCtx?.balance ?? 0}
      />
    </>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function ContentInputArea({
  content,
  setContent,
  themeColor,
}: {
  content: string;
  setContent: (v: string) => void;
  themeColor: string;
}) {
  if (content) {
    return (
      <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto w-full">
        <div className="w-full h-full p-4">
          <label className="text-xs font-bold text-slate-500 dark:text-white/50 uppercase tracking-widest mb-2 block">
            검토할 원본 콘텐츠
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="여기에 시나리오, 프롬프트, 혹은 아이디어를 입력하세요..."
            className={`w-full h-[60vh] p-6 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-2xl text-slate-900 dark:text-white resize-none focus:outline-none focus:border-${themeColor}-500/50 text-lg leading-relaxed font-serif`}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-6 animate-in fade-in zoom-in-95">
      <div className={`w-20 h-20 bg-${themeColor}-500/10 rounded-full flex items-center justify-center mx-auto`}>
        <PenTool className={`w-8 h-8 text-${themeColor}-400`} />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Creative Editor</h2>
      <p className="text-slate-500 dark:text-white/50 max-w-md text-center">
        단순한 오타 수정이 아닙니다.
        <br />
        전문 에디터가 당신의 글을 더 강력하고 매력적으로 다시 써드립니다.
      </p>
      <button
        onClick={() => setContent(" ")}
        className="px-6 py-3 bg-slate-100 dark:bg-white/10 hover:bg-slate-200 dark:hover:bg-white/20 rounded-xl text-slate-900 dark:text-white font-medium transition-all"
      >
        콘텐츠 입력 시작하기
      </button>
    </div>
  );
}

function EditorResultDisplay({
  result,
  onCopy,
  onExport,
  onRegenerate,
  getScoreColor,
}: {
  result: EditorResult;
  onCopy: () => void;
  onExport: () => void;
  onRegenerate: () => void;
  getScoreColor: (score: number) => string;
}) {
  return (
    <div className="h-full flex flex-col space-y-4 animate-in fade-in">
      {/* Top Bar: Critique Summary */}
      <div className="bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl p-4 flex items-center justify-between shrink-0">
        <div className="flex gap-6">
          <div className="text-center">
            <div className="text-xs text-slate-500 dark:text-white/40 mb-1">내러티브</div>
            <div className={`text-xl font-bold ${getScoreColor(result.critique.narrative_score)}`}>
              {result.critique.narrative_score}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500 dark:text-white/40 mb-1">비주얼</div>
            <div className={`text-xl font-bold ${getScoreColor(result.critique.visual_score)}`}>
              {result.critique.visual_score}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500 dark:text-white/40 mb-1">페이스</div>
            <div className={`text-xl font-bold ${getScoreColor(result.critique.pacing_score)}`}>
              {result.critique.pacing_score}
            </div>
          </div>
        </div>
        <div className="flex-1 ml-8 pl-8 border-l border-slate-200 dark:border-white/10 overflow-hidden">
          <div className="text-xs font-bold text-rose-600 dark:text-rose-400 mb-1 uppercase">
            Key Issues
          </div>
          <div className="flex gap-2 overflow-x-auto no-scrollbar">
            {result.critique.key_issues.map((issue, i) => (
              <span
                key={i}
                className="text-xs px-2 py-1 bg-slate-100 dark:bg-white/5 rounded text-slate-600 dark:text-white/70 whitespace-nowrap"
              >
                • {issue}
              </span>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onCopy}
            className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg text-slate-500 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
            title="수정본 복사"
          >
            <Copy className="w-5 h-5" />
          </button>
          <button
            onClick={onExport}
            className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg text-slate-500 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
            title="리포트 다운로드"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Split View Area */}
      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        {/* Original */}
        <div className="rounded-xl bg-white/80 dark:bg-white/5 border border-slate-200 dark:border-white/10 flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-white/5 flex justify-between items-center">
            <span className="text-sm font-bold text-slate-600 dark:text-white/70">원본 (Original)</span>
          </div>
          <div className="flex-1 p-6 overflow-y-auto whitespace-pre-wrap text-slate-600 dark:text-white/60 leading-relaxed font-serif">
            {result.original_content}
          </div>
        </div>

        {/* Improved */}
        <div className="rounded-xl bg-emerald-50 dark:bg-emerald-500/5 border border-emerald-200 dark:border-emerald-500/20 flex flex-col overflow-hidden relative group">
          <div className="px-4 py-3 border-b border-emerald-200 dark:border-emerald-500/20 bg-emerald-100/50 dark:bg-emerald-500/10 flex justify-between items-center">
            <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              <Check className="w-4 h-4" />
              수정본 (Editor&apos;s Cut)
            </span>
          </div>
          <div className="flex-1 p-6 overflow-y-auto whitespace-pre-wrap text-slate-900 dark:text-white leading-relaxed font-serif">
            {result.improved_content}
          </div>

          {/* Floating Apply Button */}
          <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={onRegenerate}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-lg shadow-lg flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              다시 제안받기
            </button>
          </div>
        </div>
      </div>

      {/* Change Log */}
      <div className="h-32 shrink-0 bg-white/80 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-4 overflow-y-auto">
        <h4 className="text-xs font-bold text-slate-500 dark:text-white/40 uppercase mb-2">
          변경 내역 로그
        </h4>
        <div className="space-y-1">
          {result.changes_made.map((change, i) => (
            <div key={i} className="text-sm flex items-start gap-2">
              <span className="text-emerald-600 dark:text-emerald-400 font-mono text-xs px-1.5 py-0.5 bg-emerald-100 dark:bg-emerald-500/10 rounded mt-0.5">
                {change.type}
              </span>
              <span className="text-slate-600 dark:text-white/70">{change.description}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
