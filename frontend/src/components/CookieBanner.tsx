'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cookie, X, Settings, Check } from 'lucide-react';
import Link from 'next/link';

const COOKIE_CONSENT_KEY = 'cookie_consent';

interface CookiePreferences {
    necessary: boolean;
    analytics: boolean;
    marketing: boolean;
}

export default function CookieBanner() {
    const [isVisible, setIsVisible] = useState(() => {
        if (typeof window === "undefined") return false;
        const storedConsent = localStorage.getItem(COOKIE_CONSENT_KEY);
        return !storedConsent;
    });
    const [showSettings, setShowSettings] = useState(false);
    const [preferences, setPreferences] = useState<CookiePreferences>(() => {
        const defaults = { necessary: true, analytics: false, marketing: false };
        if (typeof window === "undefined") return defaults;
        const storedConsent = localStorage.getItem(COOKIE_CONSENT_KEY);
        if (!storedConsent) return defaults;
        try {
            const parsed = JSON.parse(storedConsent) as CookiePreferences;
            return { ...defaults, ...parsed };
        } catch {
            return defaults;
        }
    });

    const handleAcceptAll = () => {
        const allAccepted = { necessary: true, analytics: true, marketing: true };
        localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(allAccepted));
        setPreferences(allAccepted);
        setIsVisible(false);
    };

    const handleAcceptNecessary = () => {
        const necessaryOnly = { necessary: true, analytics: false, marketing: false };
        localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(necessaryOnly));
        setPreferences(necessaryOnly);
        setIsVisible(false);
    };

    const handleSavePreferences = () => {
        localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(preferences));
        setIsVisible(false);
        setShowSettings(false);
    };

    if (!isVisible) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 100, opacity: 0 }}
                className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:max-w-md z-50"
            >
                <div className="bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
                    {/* Main Banner */}
                    {!showSettings && (
                        <div className="p-5">
                            <div className="flex items-start gap-4">
                                <div className="p-2.5 rounded-xl bg-purple-500/20 border border-purple-500/20">
                                    <Cookie size={20} className="text-purple-400" />
                                </div>
                                <div className="flex-1">
                                    <h3 className="text-white font-semibold mb-2">쿠키 사용 안내</h3>
                                    <p className="text-gray-400 text-sm leading-relaxed mb-4">
                                        더 나은 서비스 제공을 위해 쿠키를 사용합니다.{' '}
                                        <Link href="/privacy" className="text-purple-400 hover:text-purple-300 underline">
                                            개인정보처리방침
                                        </Link>
                                        에서 자세한 내용을 확인하세요.
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        <button
                                            onClick={handleAcceptAll}
                                            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5"
                                        >
                                            <Check size={14} />
                                            모두 동의
                                        </button>
                                        <button
                                            onClick={handleAcceptNecessary}
                                            className="px-4 py-2 bg-white/10 hover:bg-white/15 text-white text-sm font-medium rounded-lg transition-colors"
                                        >
                                            필수만 동의
                                        </button>
                                        <button
                                            onClick={() => setShowSettings(true)}
                                            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-gray-400 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5"
                                        >
                                            <Settings size={14} />
                                            설정
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Settings Panel */}
                    {showSettings && (
                        <div className="p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-white font-semibold">쿠키 설정</h3>
                                <button
                                    onClick={() => setShowSettings(false)}
                                    className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                                >
                                    <X size={18} className="text-gray-400" />
                                </button>
                            </div>
                            <div className="space-y-3 mb-4">
                                {/* Necessary - Always on */}
                                <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                                    <div>
                                        <span className="text-white text-sm font-medium">필수 쿠키</span>
                                        <p className="text-gray-500 text-xs mt-0.5">서비스 이용에 필수적인 쿠키입니다</p>
                                    </div>
                                    <div className="w-10 h-6 bg-purple-600 rounded-full flex items-center justify-end px-1">
                                        <div className="w-4 h-4 bg-white rounded-full" />
                                    </div>
                                </label>

                                {/* Analytics */}
                                <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition-colors">
                                    <div>
                                        <span className="text-white text-sm font-medium">분석 쿠키</span>
                                        <p className="text-gray-500 text-xs mt-0.5">서비스 개선을 위한 익명 통계</p>
                                    </div>
                                    <button
                                        onClick={() => setPreferences(p => ({ ...p, analytics: !p.analytics }))}
                                        className={`w-10 h-6 rounded-full flex items-center transition-colors ${preferences.analytics ? 'bg-purple-600 justify-end' : 'bg-gray-700 justify-start'
                                            } px-1`}
                                    >
                                        <div className="w-4 h-4 bg-white rounded-full" />
                                    </button>
                                </label>

                                {/* Marketing */}
                                <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition-colors">
                                    <div>
                                        <span className="text-white text-sm font-medium">마케팅 쿠키</span>
                                        <p className="text-gray-500 text-xs mt-0.5">맞춤형 광고 및 콘텐츠 제공</p>
                                    </div>
                                    <button
                                        onClick={() => setPreferences(p => ({ ...p, marketing: !p.marketing }))}
                                        className={`w-10 h-6 rounded-full flex items-center transition-colors ${preferences.marketing ? 'bg-purple-600 justify-end' : 'bg-gray-700 justify-start'
                                            } px-1`}
                                    >
                                        <div className="w-4 h-4 bg-white rounded-full" />
                                    </button>
                                </label>
                            </div>
                            <button
                                onClick={handleSavePreferences}
                                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors"
                            >
                                설정 저장
                            </button>
                        </div>
                    )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
