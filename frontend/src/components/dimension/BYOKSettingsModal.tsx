"use client";

/**
 * BYOKSettingsModal - API Key 설정 모달
 * 
 * 사이드바에서 직접 API Key를 입력/수정/삭제할 수 있는 모달입니다.
 * 작업 중인 화면을 떠나지 않고 설정을 변경할 수 있습니다.
 */

import { useState, useEffect } from "react";
import { useBYOK } from "@/hooks/useBYOK";

interface BYOKSettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function BYOKSettingsModal({ isOpen, onClose }: BYOKSettingsModalProps) {
    const { byokKey, setBYOKKey, isBYOKEnabled, clearBYOKKey } = useBYOK();
    const [inputValue, setInputValue] = useState("");
    const [isSaving, setIsSaving] = useState(false);
    const [showKey, setShowKey] = useState(false);

    // 모달이 열릴 때 기존 키 값으로 초기화
    useEffect(() => {
        if (isOpen) {
            setInputValue(byokKey || "");
        }
    }, [isOpen, byokKey]);

    if (!isOpen) return null;

    const handleSave = async () => {
        if (!inputValue.trim()) return;

        setIsSaving(true);
        setBYOKKey(inputValue.trim());

        // 상태 전파를 위한 짧은 대기
        await new Promise(resolve => setTimeout(resolve, 100));

        setIsSaving(false);
        onClose();
    };

    const handleDelete = async () => {
        setIsSaving(true);
        clearBYOKKey();
        await new Promise(resolve => setTimeout(resolve, 100));
        setIsSaving(false);
        setInputValue("");
        onClose();
    };

    const handleClose = () => {
        setInputValue("");
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={handleClose}
            />

            {/* Modal */}
            <div className="relative bg-[#18181b] border border-white/10 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="p-6 pb-4 text-center border-b border-white/5">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-violet-500/10 flex items-center justify-center">
                        <svg className="w-8 h-8 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">API Key 설정</h2>
                    <p className="text-sm text-zinc-400">
                        Gemini API Key를 등록하면 크레딧 소진 없이<br />무제한으로 사용할 수 있습니다.
                    </p>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    {/* Status Badge */}
                    <div className="flex justify-center">
                        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${isBYOKEnabled
                            ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                            : 'bg-zinc-800 text-zinc-500 border border-white/5'
                            }`}>
                            <span className={`w-2 h-2 rounded-full ${isBYOKEnabled ? 'bg-violet-400' : 'bg-zinc-600'}`} />
                            {isBYOKEnabled ? '내 키 사용 중' : '미설정'}
                        </div>
                    </div>

                    {/* Input */}
                    <div className="space-y-2">
                        <label className="block text-xs font-medium text-zinc-400 uppercase tracking-wider">
                            Gemini API Key
                        </label>
                        <div className="relative">
                            <input
                                type={showKey ? "text" : "password"}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder="AIzaSy... (여기에 붙여넣기)"
                                className="w-full px-4 py-3 pr-12 bg-black/50 border border-white/10 rounded-xl text-white text-sm font-mono placeholder-white/20 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all"
                                autoFocus
                            />
                            <button
                                type="button"
                                onClick={() => setShowKey(!showKey)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-zinc-500 hover:text-zinc-300 transition-colors"
                                title={showKey ? "숨기기" : "보기"}
                            >
                                {showKey ? (
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                                    </svg>
                                ) : (
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                        <p className="text-[10px] text-zinc-500 text-center">
                            키는 브라우저에만 저장되며 서버로 전송되지 않습니다.
                        </p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                        <button
                            onClick={handleSave}
                            disabled={!inputValue.trim() || isSaving}
                            className="flex-1 py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-white font-bold rounded-xl shadow-lg shadow-violet-500/20 transition-all flex items-center justify-center gap-2"
                        >
                            {isSaving ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    저장 중...
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    저장
                                </>
                            )}
                        </button>

                        {isBYOKEnabled && (
                            <button
                                onClick={handleDelete}
                                disabled={isSaving}
                                className="px-4 py-3 text-red-400 hover:bg-red-500/10 border border-red-500/20 hover:border-red-500/30 font-medium rounded-xl transition-all"
                            >
                                삭제
                            </button>
                        )}

                        <button
                            onClick={handleClose}
                            disabled={isSaving}
                            className="px-4 py-3 bg-white/5 hover:bg-white/10 text-zinc-400 font-medium rounded-xl transition-colors"
                        >
                            취소
                        </button>
                    </div>

                    {/* Help Links */}
                    <div className="flex flex-col gap-2 pt-2">
                        <a
                            href="https://aistudio.google.com/app/apikey"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 hover:border-white/10 transition-all group"
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-violet-500/10">
                                    <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                    </svg>
                                </div>
                                <span className="text-sm font-medium text-zinc-300 group-hover:text-white">API Key 바로 발급받기</span>
                            </div>
                            <svg className="w-4 h-4 text-zinc-500 group-hover:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                        </a>
                        <a
                            href="/api-key-guide"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-emerald-500/10 to-teal-500/5 hover:from-emerald-500/15 hover:to-teal-500/10 rounded-xl border border-emerald-500/20 hover:border-emerald-500/30 transition-all group"
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-emerald-500/20">
                                    <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-sm font-medium text-emerald-300 group-hover:text-emerald-200">$300 무료 크레딧 받는 법</span>
                                    <span className="text-[10px] text-zinc-500">90일간 약 40만원 상당 무료!</span>
                                </div>
                            </div>
                            <svg className="w-4 h-4 text-emerald-500/50 group-hover:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </a>
                    </div>
                </div>

                {/* Close button */}
                <button
                    onClick={handleClose}
                    className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    );
}
