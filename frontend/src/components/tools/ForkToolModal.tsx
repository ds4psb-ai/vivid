"use client";

/**
 * Fork Tool Modal (한국어)
 * 
 * 도구 포크 기능:
 * - 이름 커스터마이징
 * - 포킹 이유 설명
 * - 변경 미리보기
 * - 시빌 경고
 */

import { useState, useCallback } from "react";
import {
    GitFork,
    X,
    AlertTriangle,
    Loader2,
    Check,
    FileCode,
    Shield,
} from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

interface ForkToolModalProps {
    toolId: string;
    toolName: string;
    toolKey: string;
    onClose: () => void;
    onSuccess: (newToolKey: string) => void;
}

interface DiffPreview {
    diff_stats: {
        lines_added: number;
        lines_removed: number;
        files_changed: number;
    };
    attribution_estimate: number;
    sybil_warning: boolean;
    warning_message?: string;
}

interface ForkResult {
    success: boolean;
    child_tool_id: string;
    child_tool_key: string;
    fork_id: string;
    attribution_score: number;
}

export default function ForkToolModal({
    toolId,
    toolName,
    toolKey,
    onClose,
    onSuccess,
}: ForkToolModalProps) {
    const [step, setStep] = useState<"form" | "preview" | "creating" | "success">("form");
    const [name, setName] = useState(`${toolName} (포크)`);
    const [description, setDescription] = useState("");
    const [newPrompt, setNewPrompt] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [diffPreview, setDiffPreview] = useState<DiffPreview | null>(null);
    const [forkResult, setForkResult] = useState<ForkResult | null>(null);
    const [loading, setLoading] = useState(false);

    const handlePreview = useCallback(async () => {
        if (!newPrompt.trim()) {
            setError("수정된 프롬프트/코드를 입력해주세요");
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const preview = await fetchWithAuth<DiffPreview>(
                `/api/v1/fork/preview/${toolId}`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        new_prompt: newPrompt,
                        new_system_prompt: null,
                    }),
                }
            );
            setDiffPreview(preview);
            setStep("preview");
        } catch (err) {
            setError(err instanceof Error ? err.message : "변경 미리보기 실패");
        } finally {
            setLoading(false);
        }
    }, [toolId, newPrompt]);

    const handleCreateFork = useCallback(async () => {
        setStep("creating");
        setError(null);
        try {
            const result = await fetchWithAuth<ForkResult>(
                `/api/v1/fork/create/${toolId}`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        name,
                        description,
                        new_prompt: newPrompt,
                        new_system_prompt: null,
                    }),
                }
            );
            setForkResult(result);
            setStep("success");
        } catch (err) {
            setError(err instanceof Error ? err.message : "포크 생성 실패");
            setStep("preview");
        }
    }, [toolId, name, description, newPrompt]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="relative w-full max-w-xl bg-[var(--bg-1)] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
                {/* 헤더 */}
                <div className="flex items-center justify-between p-4 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg">
                            <GitFork className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">도구 포크</h2>
                            <p className="text-xs text-gray-500">{toolKey}의 나만의 버전 만들기</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {/* 내용 */}
                <div className="p-6">
                    {step === "form" && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">
                                    포크 이름
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg
                                             text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none"
                                    placeholder="나만의 커스텀 도구"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">
                                    설명 (왜 포크하나요?)
                                </label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={2}
                                    className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg
                                             text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none resize-none"
                                    placeholder="새로운 기능을 추가하려고..."
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">
                                    수정된 프롬프트/코드
                                </label>
                                <textarea
                                    value={newPrompt}
                                    onChange={(e) => setNewPrompt(e.target.value)}
                                    rows={6}
                                    className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg
                                             text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none resize-none
                                             font-mono text-sm"
                                    placeholder="수정된 프롬프트나 코드를 여기에 붙여넣으세요..."
                                />
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 text-red-400 text-sm">
                                    <AlertTriangle className="w-4 h-4" />
                                    {error}
                                </div>
                            )}
                        </div>
                    )}

                    {step === "preview" && diffPreview && (
                        <div className="space-y-4">
                            {/* 변경 통계 */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold text-green-400">
                                        +{diffPreview.diff_stats.lines_added}
                                    </div>
                                    <div className="text-xs text-gray-500">추가된 줄</div>
                                </div>
                                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold text-red-400">
                                        -{diffPreview.diff_stats.lines_removed}
                                    </div>
                                    <div className="text-xs text-gray-500">삭제된 줄</div>
                                </div>
                                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-center">
                                    <div className="text-2xl font-bold text-blue-400">
                                        {diffPreview.diff_stats.files_changed}
                                    </div>
                                    <div className="text-xs text-gray-500">변경된 파일</div>
                                </div>
                            </div>

                            {/* 기여도 점수 */}
                            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Shield className="w-5 h-5 text-purple-400" />
                                        <span className="text-gray-300">예상 기여도 점수</span>
                                    </div>
                                    <span className="text-2xl font-bold text-purple-400">
                                        {diffPreview.attribution_estimate.toFixed(1)}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500 mt-2">
                                    점수가 높을수록 = 더 많은 원본 기여 = 더 높은 수익 배분
                                </p>
                            </div>

                            {/* 시빌 경고 */}
                            {diffPreview.sybil_warning && (
                                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                                    <div className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                                        <div>
                                            <div className="font-medium text-yellow-400">시빌 경고</div>
                                            <p className="text-sm text-yellow-400/80 mt-1">
                                                {diffPreview.warning_message ||
                                                    "변경 사항이 매우 적어 보입니다. 낮은 기여도의 포크는 수익 배분이 줄어들 수 있습니다."}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {error && (
                                <div className="flex items-center gap-2 text-red-400 text-sm">
                                    <AlertTriangle className="w-4 h-4" />
                                    {error}
                                </div>
                            )}
                        </div>
                    )}

                    {step === "creating" && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <Loader2 className="w-12 h-12 text-purple-400 animate-spin mb-4" />
                            <p className="text-gray-400">포크 생성 중...</p>
                        </div>
                    )}

                    {step === "success" && forkResult && (
                        <div className="flex flex-col items-center justify-center py-8">
                            <div className="p-4 bg-emerald-500/20 rounded-full mb-4">
                                <Check className="w-8 h-8 text-emerald-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">포크 생성 완료!</h3>
                            <p className="text-gray-400 text-center mb-4">
                                <span className="text-purple-400">{forkResult.child_tool_key}</span> 포크가
                                기여도 점수 <span className="text-purple-400">{forkResult.attribution_score.toFixed(1)}</span>로 생성되었습니다
                            </p>
                            <div className="bg-gray-800/50 rounded-lg p-3 text-sm">
                                <span className="text-gray-500">도구 키: </span>
                                <code className="text-purple-400">{forkResult.child_tool_key}</code>
                            </div>
                        </div>
                    )}
                </div>

                {/* 푸터 */}
                <div className="flex items-center justify-end gap-3 p-4 border-t border-white/10 bg-gray-800/30">
                    {step === "form" && (
                        <>
                            <button
                                onClick={onClose}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                            >
                                취소
                            </button>
                            <button
                                onClick={handlePreview}
                                disabled={loading || !newPrompt.trim()}
                                className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 
                                         text-white rounded-lg transition-colors disabled:opacity-50"
                            >
                                {loading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <FileCode className="w-4 h-4" />
                                )}
                                변경 미리보기
                            </button>
                        </>
                    )}

                    {step === "preview" && (
                        <>
                            <button
                                onClick={() => setStep("form")}
                                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                            >
                                뒤로
                            </button>
                            <button
                                onClick={handleCreateFork}
                                className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 
                                         text-white rounded-lg transition-colors"
                            >
                                <GitFork className="w-4 h-4" />
                                포크 생성
                            </button>
                        </>
                    )}

                    {step === "success" && (
                        <button
                            onClick={() => onSuccess(forkResult?.child_tool_key || "")}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 
                                     text-white rounded-lg transition-colors"
                        >
                            내 포크 보기
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
