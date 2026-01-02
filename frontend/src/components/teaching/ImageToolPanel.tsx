"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import TeachingPanelLayout from "./TeachingPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

const CREDIT_COST = 5;

interface ImagePromptResult {
    prompt: string;
    negative_prompt?: string;
    parameters?: {
        style?: string;
        aspect_ratio?: string;
        quality?: string;
    };
}

const STYLES = [
    { value: "photorealistic", label: "포토리얼리스틱" },
    { value: "cinematic", label: "시네마틱" },
    { value: "anime", label: "애니메이션" },
    { value: "illustration", label: "일러스트" },
    { value: "3d-render", label: "3D 렌더" },
    { value: "oil-painting", label: "유화" },
    { value: "watercolor", label: "수채화" },
    { value: "digital-art", label: "디지털 아트" },
];

const ASPECT_RATIOS = [
    { value: "16:9", label: "16:9 (와이드)" },
    { value: "9:16", label: "9:16 (세로)" },
    { value: "1:1", label: "1:1 (정사각형)" },
    { value: "4:3", label: "4:3 (스탠다드)" },
    { value: "3:2", label: "3:2 (사진)" },
    { value: "21:9", label: "21:9 (울트라와이드)" },
];

const MODELS = [
    { value: "gemini-2.5-flash", label: "Flash (빠름)" },
    { value: "gemini-2.5-pro", label: "Pro (고품질)" },
];

export default function ImageToolPanel() {
    const [description, setDescription] = useState("");
    const [style, setStyle] = useState("photorealistic");
    const [aspectRatio, setAspectRatio] = useState("16:9");
    const [model, setModel] = useState("gemini-2.5-flash");

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<ImagePromptResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    const getErrorMessage = (err: unknown): string => {
        if (err instanceof Error) {
            const msg = err.message.toLowerCase();
            if (msg.includes("timeout")) return "요청 시간이 초과되었습니다. 다시 시도해주세요.";
            if (msg.includes("api key")) return "서비스 설정 오류입니다. 관리자에게 문의하세요.";
            if (msg.includes("network") || msg.includes("fetch")) return "네트워크 오류입니다. 인터넷 연결을 확인해주세요.";
            if (msg.includes("insufficient") || msg.includes("402")) return "크레딧이 부족합니다.";
            return err.message;
        }
        return "알 수 없는 오류가 발생했습니다.";
    };

    const handleGenerate = async () => {
        if (!description.trim()) {
            setError("이미지 설명을 입력해주세요");
            return;
        }

        // Credit check (only when not using BYOK)
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post<{
                success: boolean;
                output: ImagePromptResult;
                error?: string;
            }>("/api/teaching/image/generate", {
                description,
                style,
                aspect_ratio: aspectRatio,
                model,
            }, getBYOKHeaders(byokKey));

            if (response.success) {
                setResult(response.output);
                // Refresh credit balance
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(response.error || "생성 실패");
            }
        } catch (err) {
            const errorMsg = getErrorMessage(err);
            if (errorMsg.includes("크레딧")) {
                setShowCreditModal(true);
            } else {
                setError(errorMsg);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopy = async (text: string, field: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        } catch {
            setError("클립보드 복사에 실패했습니다.");
        }
    };

    const SidebarContent = (
        <>
            {/* Description Input */}
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">이미지 설명</label>
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="생성하고 싶은 이미지를 설명하세요..."
                    className="w-full h-32 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/20 focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all resize-none text-sm leading-relaxed"
                />
            </div>

            {/* Style */}
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">스타일</label>
                <div className="relative">
                    <select
                        value={style}
                        onChange={(e) => setStyle(e.target.value)}
                        className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
                    >
                        {STYLES.map((s) => (
                            <option key={s.value} value={s.value}>{s.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Aspect Ratio */}
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">비율</label>
                <div className="grid grid-cols-2 gap-2">
                    {ASPECT_RATIOS.map((ratio) => (
                        <button
                            key={ratio.value}
                            onClick={() => setAspectRatio(ratio.value)}
                            className={`py-2 text-xs font-medium rounded-lg border transition-all ${aspectRatio === ratio.value
                                ? "bg-amber-400/10 border-amber-400/50 text-amber-400"
                                : "bg-white/5 border-white/5 text-zinc-400 hover:bg-white/10 hover:text-white"
                                }`}
                        >
                            {ratio.value}
                        </button>
                    ))}
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-2 border-t border-white/5">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !description.trim()}
                className="w-full py-3 mt-4 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-[#121212] font-bold rounded-lg shadow-lg shadow-amber-500/10 transition-all hover:shadow-amber-500/20 active:scale-[0.98] flex items-center justify-center gap-2"
            >
                {isLoading ? (
                    <span className="flex items-center gap-2">Generating...</span>
                ) : (
                    "이미지 프롬프트 생성"
                )}
            </button>

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs break-keep leading-relaxed animate-in fade-in slide-in-from-top-1">
                    {error}
                </div>
            )}
        </>
    );

    return (
        <>
            <TeachingPanelLayout
                title="이미지 프롬프트 생성기"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
            >
                {result ? (
                    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
                        {/* Main Prompt */}
                        <div className="group relative">
                            <div className="flex items-center justify-between mb-3 px-1">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                                    Generated Prompt
                                </h3>
                                <button
                                    onClick={() => handleCopy(result.prompt, "prompt")}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${copiedField === "prompt"
                                        ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                        : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                        }`}
                                >
                                    {copiedField === "prompt" ? (
                                        <>
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                            Copied
                                        </>
                                    ) : (
                                        <>
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            </svg>
                                            Copy
                                        </>
                                    )}
                                </button>
                            </div>
                            <div className="p-6 bg-[#18181b] border border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-zinc-100 whitespace-pre-wrap group-hover:border-white/20 transition-colors relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-400/50 to-transparent opacity-50"></div>
                                {result.prompt}
                            </div>
                        </div>

                        {/* Negative Prompt */}
                        <div className="group relative">
                            <div className="flex items-center justify-between mb-3 px-1">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-red-400/50"></span>
                                    Negative Prompt
                                </h3>
                                <button
                                    onClick={() => handleCopy(result.negative_prompt || "text, watermark", "negative")}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${copiedField === "negative"
                                        ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                        : "bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5 hover:border-white/10"
                                        }`}
                                >
                                    {copiedField === "negative" ? "Copied" : "Copy"}
                                </button>
                            </div>
                            <div className="p-5 bg-[#18181b]/50 border border-white/10 rounded-xl shadow-inner font-mono text-sm leading-relaxed text-zinc-400 whitespace-pre-wrap group-hover:border-white/20 transition-colors">
                                {result.negative_prompt || "text, watermark, low quality, blurred, distorted"}
                            </div>
                        </div>

                        {/* Parameters Grid */}
                        {result.parameters && (
                            <div className="p-6 bg-white/[0.02] border border-white/5 rounded-xl space-y-4 hover:border-white/10 transition-colors">
                                <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest border-b border-white/5 pb-3 mb-1">Parameters</h3>
                                <div className="grid grid-cols-3 gap-6">
                                    {Object.entries(result.parameters).map(([key, value]) => (
                                        <div key={key} className="flex flex-col gap-1">
                                            <span className="text-xs text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                                            <span className="text-sm font-mono text-amber-400/90">{value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-6">
                        <div className="w-24 h-24 rounded-3xl bg-white/[0.03] border border-white/5 flex items-center justify-center shadow-2xl">
                            <svg className="w-10 h-10 opacity-20 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <div className="text-center space-y-2">
                            <h3 className="text-lg font-medium text-white/40">Ready to Generate</h3>
                            <p className="text-sm text-zinc-600 max-w-xs mx-auto">
                                이미지를 설명하고 생성형 AI를 위한<br />최적화된 프롬프트를 받아보세요.
                            </p>
                        </div>
                    </div>
                )}
            </TeachingPanelLayout>

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
