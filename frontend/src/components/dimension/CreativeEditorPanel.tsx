"use client";

/**
 * CreativeEditorPanel - 크리에이티브 에디터
 *
 * AI-powered editorial review and improvement of creative content.
 * Migrated to Panel Design Unity Compound Component System.
 * @see docs/PANEL_DESIGN_UNITY_SPEC.md
 */

import { useState, useCallback, useMemo } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { useLanguage } from "@/contexts/LanguageContext";
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

// =============================================================================
// PRESETS (Dynamic based on language)
// =============================================================================

const getPersonas = (isKo: boolean) => [
  {
    value: "Senior Editor",
    label: isKo ? "수석 에디터 (밸런스 중시)" : "Senior Editor (Balanced)",
    desc: isKo ? "전체적인 완성도와 흐름을 개선합니다." : "Improves overall completeness and flow.",
  },
  {
    value: "Ruthless Critic",
    label: isKo ? "냉철한 비평가 (약점 공략)" : "Ruthless Critic (Weakness Focus)",
    desc: isKo ? "논리적 허점과 개연성을 집중 타격합니다." : "Targets logical gaps and plausibility issues.",
  },
  {
    value: "Commercial Producer",
    label: isKo ? "흥행 프로듀서 (대중성)" : "Commercial Producer (Mass Appeal)",
    desc: isKo ? "임팩트와 대중적 재미를 극대화합니다." : "Maximizes impact and mainstream appeal.",
  },
  {
    value: "Artistic Director",
    label: isKo ? "예술 감독 (미학)" : "Artistic Director (Aesthetics)",
    desc: isKo ? "표현의 깊이와 예술적 가치를 높입니다." : "Enhances depth and artistic value.",
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
  const { language } = useLanguage();
  const isKo = language === "ko";

  // Memoized presets based on language
  const PERSONAS = useMemo(() => getPersonas(isKo), [isKo]);

  // i18n labels
  const labels = useMemo(() => ({
    title: isKo ? "크리에이티브 에디터" : "Creative Editor",
    genreContext: isKo ? "장르 / 맥락" : "Genre / Context",
    genrePlaceholder: isKo ? "예: SF 스릴러 영화, 30초 TV 광고" : "e.g., Sci-Fi thriller movie, 30-second TV ad",
    editorialPersona: isKo ? "에디토리얼 페르소나" : "Editorial Persona",
    runEditor: isKo ? "에디터 실행" : "Run Editor",
    analyzing: isKo ? "분석 및 수정 중..." : "Analyzing and editing...",
    analyzingContent: isKo ? "콘텐츠 분석 및 수정 중..." : "Analyzing and editing content...",
    originalContent: isKo ? "검토할 원본 콘텐츠" : "Original Content to Review",
    contentPlaceholder: isKo ? "여기에 시나리오, 프롬프트, 혹은 아이디어를 입력하세요..." : "Enter your scenario, prompt, or idea here...",
    editorDescription: isKo
      ? "단순한 오타 수정이 아닙니다. 전문 에디터가 당신의 글을 더 강력하고 매력적으로 다시 써드립니다."
      : "More than just typo fixes. A professional editor will rewrite your content to be more powerful and engaging.",
    startInput: isKo ? "콘텐츠 입력 시작하기" : "Start Entering Content",
    narrative: isKo ? "내러티브" : "Narrative",
    visual: isKo ? "비주얼" : "Visual",
    pacing: isKo ? "페이스" : "Pacing",
    keyIssues: "Key Issues",
    original: isKo ? "원본 (Original)" : "Original",
    editorsCut: isKo ? "수정본 (Editor's Cut)" : "Editor's Cut",
    copyEdited: isKo ? "수정본 복사" : "Copy Edited Version",
    downloadReport: isKo ? "리포트 다운로드" : "Download Report",
    regenerate: isKo ? "다시 제안받기" : "Get New Suggestions",
    changeLog: isKo ? "변경 내역 로그" : "Change Log",
    validationError: isKo ? "검토할 콘텐츠를 입력해주세요." : "Please enter content to review.",
  }), [isKo]);

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
      setValidationError(labels.validationError);
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
  }, [content, context, persona, byokKey, creditCtx, wrappedExecute, CREDIT_COST, labels.validationError]);

  const displayError = validationError || error;

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <>
      <DimensionPanel.Header title={labels.title} creditCost={CREDIT_COST} />

      <DimensionPanel.Sidebar>
        {/* Context Input */}
        <div className="space-y-2">
          <label
            className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1`}
          >
            {labels.genreContext}
          </label>
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder={labels.genrePlaceholder}
            className={`w-full px-4 py-3 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 text-sm focus:outline-none focus:border-${token.themeColor}-500/50 transition-all`}
          />
        </div>

        {/* Persona Selection */}
        <div className="space-y-2">
          <label
            className={`text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1`}
          >
            {labels.editorialPersona}
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
          loadingText={labels.analyzing}
        >
          {labels.runEditor}
        </DimensionPanel.GenerateButton>
      </DimensionPanel.Sidebar>

      <DimensionPanel.Content>
        {/* Loading State */}
        <DimensionPanel.Loading message={labels.analyzingContent} />

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
            labels={labels}
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
            labels={labels}
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

interface Labels {
  title: string;
  genreContext: string;
  genrePlaceholder: string;
  editorialPersona: string;
  runEditor: string;
  analyzing: string;
  analyzingContent: string;
  originalContent: string;
  contentPlaceholder: string;
  editorDescription: string;
  startInput: string;
  narrative: string;
  visual: string;
  pacing: string;
  keyIssues: string;
  original: string;
  editorsCut: string;
  copyEdited: string;
  downloadReport: string;
  regenerate: string;
  changeLog: string;
  validationError: string;
}

function ContentInputArea({
  content,
  setContent,
  themeColor,
  labels,
}: {
  content: string;
  setContent: (v: string) => void;
  themeColor: string;
  labels: Labels;
}) {
  if (content) {
    return (
      <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto w-full">
        <div className="w-full h-full p-4">
          <label className="text-xs font-bold text-slate-500 dark:text-white/50 uppercase tracking-widest mb-2 block">
            {labels.originalContent}
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={labels.contentPlaceholder}
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
        {labels.editorDescription}
      </p>
      <button
        onClick={() => setContent(" ")}
        className="px-6 py-3 bg-slate-100 dark:bg-white/10 hover:bg-slate-200 dark:hover:bg-white/20 rounded-xl text-slate-900 dark:text-white font-medium transition-all"
      >
        {labels.startInput}
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
  labels,
}: {
  result: EditorResult;
  onCopy: () => void;
  onExport: () => void;
  onRegenerate: () => void;
  getScoreColor: (score: number) => string;
  labels: Labels;
}) {
  return (
    <div className="h-full flex flex-col space-y-4 animate-in fade-in">
      {/* Top Bar: Critique Summary */}
      <div className="bg-white/80 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl p-4 flex items-center justify-between shrink-0">
        <div className="flex gap-6">
          <div className="text-center">
            <div className="text-xs text-slate-500 dark:text-white/40 mb-1">{labels.narrative}</div>
            <div className={`text-xl font-bold ${getScoreColor(result.critique.narrative_score)}`}>
              {result.critique.narrative_score}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500 dark:text-white/40 mb-1">{labels.visual}</div>
            <div className={`text-xl font-bold ${getScoreColor(result.critique.visual_score)}`}>
              {result.critique.visual_score}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500 dark:text-white/40 mb-1">{labels.pacing}</div>
            <div className={`text-xl font-bold ${getScoreColor(result.critique.pacing_score)}`}>
              {result.critique.pacing_score}
            </div>
          </div>
        </div>
        <div className="flex-1 ml-8 pl-8 border-l border-slate-200 dark:border-white/10 overflow-hidden">
          <div className="text-xs font-bold text-rose-600 dark:text-rose-400 mb-1 uppercase">
            {labels.keyIssues}
          </div>
          <div className="flex gap-2 overflow-x-auto no-scrollbar">
            {result.critique.key_issues.map((issue, i) => (
              <span
                key={i}
                className="text-xs px-2 py-1 bg-slate-100 dark:bg-white/5 rounded text-slate-600 dark:text-white/70 whitespace-nowrap"
              >
                {issue}
              </span>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onCopy}
            className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg text-slate-500 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
            title={labels.copyEdited}
          >
            <Copy className="w-5 h-5" />
          </button>
          <button
            onClick={onExport}
            className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg text-slate-500 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
            title={labels.downloadReport}
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
            <span className="text-sm font-bold text-slate-600 dark:text-white/70">{labels.original}</span>
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
              {labels.editorsCut}
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
              {labels.regenerate}
            </button>
          </div>
        </div>
      </div>

      {/* Change Log */}
      <div className="h-32 shrink-0 bg-white/80 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-4 overflow-y-auto">
        <h4 className="text-xs font-bold text-slate-500 dark:text-white/40 uppercase mb-2">
          {labels.changeLog}
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
