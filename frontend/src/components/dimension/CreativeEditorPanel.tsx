"use client";

import { useState, useCallback } from "react";
import TeachingPanelLayout, {
    type ThemeColor,
    useAsyncOperation,
    useResultExport,
} from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import {
    PenTool,
    GitCompare,
    Check,
    X,
    ArrowRight,
    User,
    FileText,
    Copy,
    Download,
    RefreshCw
} from "lucide-react";

const CREDIT_COST = 5;
const THEME_COLOR: ThemeColor = "rose";
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
    { value: "Senior Editor", label: "수석 에디터 (밸런스 중시)", desc: "전체적인 완성도와 흐름을 개선합니다." },
    { value: "Ruthless Critic", label: "냉철한 비평가 (약점 공략)", desc: "논리적 허점과 개연성을 집중 타격합니다." },
    { value: "Commercial Producer", label: "흥행 프로듀서 (대중성)", desc: "임팩트와 대중적 재미를 극대화합니다." },
    { value: "Artistic Director", label: "예술 감독 (미학)", desc: "표현의 깊이와 예술적 가치를 높입니다." },
];

export default function CreativeEditorPanel() {
    // Inputs
    const [content, setContent] = useState("");
    const [context, setContext] = useState("");
    const [persona, setPersona] = useState("Senior Editor");
    const [viewMode, setViewMode] = useState<"split" | "unified">("split");

    const [showCreditModal, setShowCreditModal] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);

    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();
    const { exportJSON, copyToClipboard } = useResultExport();

    // Async Op
    const {
        isLoading,
        progress,
        error,
        data: result,
        execute,
        cancel,
        retry,
        canRetry,
        currentRetryCount,
    } = useAsyncOperation<{ success: boolean; output: EditorResult; error?: string }>({
        onSuccess: (data) => {
            if (data.success && !byokKey && creditCtx) {
                void creditCtx.refresh();
            }
        },
        onError: (err) => {
            if (err.message.includes("크레딧") || err.message.includes("402")) {
                setShowCreditModal(true);
            }
        },
    });

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

        await execute(
            `${API_BASE}/api/dimension/quality/editor`,
            {
                content: trimmedContent,
                context: context || "General Creative Content",
                persona,
                model: "gemini-1.5-pro",
                use_rag: true
            },
            getBYOKHeaders(byokKey)
        );
    }, [content, context, persona, byokKey, creditCtx, execute]);

    const displayResult = result?.success ? result.output : null;
    const errorMsg = validationError || (result && !result.success ? result.error : error);

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-emerald-400";
        if (score >= 60) return "text-amber-400";
        return "text-rose-400";
    };

    const SidebarContent = (
        <div className="space-y-6">
            {/* Context Input */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">
                    장르 / 맥락
                </label>
                <input
                    type="text"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="예: SF 스릴러 영화, 30초 TV 광고"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 text-sm focus:outline-none focus:border-rose-500/50"
                />
            </div>

            {/* Persona Selection */}
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-[var(--fg-muted)] uppercase tracking-widest ml-1">
                    에디토리얼 페르소나
                </label>
                <div className="space-y-2">
                    {PERSONAS.map((p) => (
                        <button
                            key={p.value}
                            onClick={() => setPersona(p.value)}
                            className={`w-full p-3 rounded-xl border text-left transition-all ${persona === p.value
                                    ? "bg-rose-500/10 border-rose-500/50"
                                    : "bg-white/5 border-white/10 hover:bg-white/10"
                                }`}
                        >
                            <div className={`text-sm font-bold ${persona === p.value ? "text-rose-400" : "text-white"}`}>
                                {p.label}
                            </div>
                            <div className="text-xs text-white/40 mt-1">{p.desc}</div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Run Button */}
            <button
                onClick={handleRunEditor}
                disabled={isLoading || !content}
                className="w-full py-4 mt-4 bg-gradient-to-r from-rose-600 to-pink-600 rounded-xl font-bold flex items-center justify-center gap-2 text-white hover:from-rose-500 hover:to-pink-500 transition-all disabled:opacity-50"
            >
                {isLoading ? (
                    <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        분석 및 수정 중...
                    </>
                ) : (
                    <>
                        에디터 실행
                        <PenTool className="w-4 h-4" />
                    </>
                )}
            </button>

            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance ?? 0}
            />
        </div>
    );

    return (
        <TeachingPanelLayout
            title="크리에이티브 에디터"
            sidebarContent={SidebarContent}
            isLoading={isLoading}
            themeColor={THEME_COLOR}
            progress={progress}
            onCancel={cancel}
            onRetry={retry}
            canRetry={canRetry}
            error={errorMsg}
        >
            {!displayResult ? (
                // Input Mode
                <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto w-full">
                    {content ? (
                        <div className="w-full h-full p-4">
                            <label className="text-xs font-bold text-white/50 uppercase tracking-widest mb-2 block">
                                검토할 원본 콘텐츠
                            </label>
                            <textarea
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                placeholder="여기에 시나리오, 프롬프트, 혹은 아이디어를 입력하세요..."
                                className="w-full h-[60vh] p-6 bg-white/5 border border-white/10 rounded-2xl text-white resize-none focus:outline-none focus:border-rose-500/50 text-lg leading-relaxed font-serif"
                            />
                        </div>
                    ) : (
                        <div className="text-center space-y-6 animate-in fade-in zoom-in-95">
                            <div className="w-20 h-20 bg-rose-500/10 rounded-full flex items-center justify-center mx-auto">
                                <PenTool className="w-8 h-8 text-rose-400" />
                            </div>
                            <h2 className="text-2xl font-bold text-white">Creative Editor</h2>
                            <p className="text-white/50 max-w-md">
                                단순한 오타 수정이 아닙니다.<br />
                                전문 에디터가 당신의 글을 더 강력하고 매력적으로 다시 써드립니다.
                            </p>
                            <button
                                onClick={() => setContent(" ")} // Trigger textarea view
                                className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl text-white font-medium transition-all"
                            >
                                콘텐츠 입력 시작하기
                            </button>
                        </div>
                    )}
                </div>
            ) : (
                // Result Mode (Split View)
                <div className="h-full flex flex-col space-y-4 animate-in fade-in">
                    {/* Top Bar: Critique Summary */}
                    <div className="bg-black/40 border border-white/10 rounded-xl p-4 flex items-center justify-between shrink-0">
                        <div className="flex gap-6">
                            <div className="text-center">
                                <div className="text-xs text-white/40 mb-1">내러티브</div>
                                <div className={`text-xl font-bold ${getScoreColor(displayResult.critique.narrative_score)}`}>
                                    {displayResult.critique.narrative_score}
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-white/40 mb-1">비주얼</div>
                                <div className={`text-xl font-bold ${getScoreColor(displayResult.critique.visual_score)}`}>
                                    {displayResult.critique.visual_score}
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-xs text-white/40 mb-1">페이스</div>
                                <div className={`text-xl font-bold ${getScoreColor(displayResult.critique.pacing_score)}`}>
                                    {displayResult.critique.pacing_score}
                                </div>
                            </div>
                        </div>
                        <div className="flex-1 ml-8 pl-8 border-l border-white/10 overflow-hidden">
                            <div className="text-xs font-bold text-rose-400 mb-1 uppercase">Key Issues</div>
                            <div className="flex gap-2 overflow-x-auto no-scrollbar">
                                {displayResult.critique.key_issues.map((issue, i) => (
                                    <span key={i} className="text-xs px-2 py-1 bg-white/5 rounded text-white/70 whitespace-nowrap">
                                        • {issue}
                                    </span>
                                ))}
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => copyToClipboard(displayResult.improved_content)}
                                className="p-2 hover:bg-white/10 rounded-lg text-white/70 hover:text-white tooltip"
                                title="수정본 복사"
                            >
                                <Copy className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => exportJSON(displayResult, "edit-report.json")}
                                className="p-2 hover:bg-white/10 rounded-lg text-white/70 hover:text-white"
                                title="리포트 다운로드"
                            >
                                <Download className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Split View Area */}
                    <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
                        {/* Original */}
                        <div className="rounded-xl bg-white/5 border border-white/10 flex flex-col overflow-hidden">
                            <div className="px-4 py-3 border-b border-white/10 bg-white/5 flex justify-between items-center">
                                <span className="text-sm font-bold text-white/70">원본 (Original)</span>
                            </div>
                            <div className="flex-1 p-6 overflow-y-auto whitespace-pre-wrap text-white/60 leading-relaxed font-serif">
                                {displayResult.original_content}
                            </div>
                        </div>

                        {/* Improved */}
                        <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 flex flex-col overflow-hidden relative group">
                            <div className="px-4 py-3 border-b border-emerald-500/20 bg-emerald-500/10 flex justify-between items-center">
                                <span className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                                    <Check className="w-4 h-4" />
                                    수정본 (Editor's Cut)
                                </span>
                            </div>
                            <div className="flex-1 p-6 overflow-y-auto whitespace-pre-wrap text-white leading-relaxed font-serif">
                                {displayResult.improved_content}
                            </div>

                            {/* Floating Apply Button */}
                            <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={() => handleRunEditor()}
                                    className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-lg shadow-lg flex items-center gap-2"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    다시 제안받기
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Change Log */}
                    <div className="h-32 shrink-0 bg-white/5 border border-white/10 rounded-xl p-4 overflow-y-auto">
                        <h4 className="text-xs font-bold text-white/40 uppercase mb-2">변경 내역 로그</h4>
                        <div className="space-y-1">
                            {displayResult.changes_made.map((change, i) => (
                                <div key={i} className="text-sm flex items-start gap-2">
                                    <span className="text-emerald-400 font-mono text-xs px-1.5 py-0.5 bg-emerald-500/10 rounded mt-0.5">
                                        {change.type}
                                    </span>
                                    <span className="text-white/70">{change.description}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </TeachingPanelLayout>
    );
}
