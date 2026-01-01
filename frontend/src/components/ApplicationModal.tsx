"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, User, Mail, Phone, Check, Loader2, CreditCard } from "lucide-react";
import { api, type CrebitApplicationRequest } from "@/lib/api";
import { requestNicePayment, CREBIT_PAYMENT, loadNicePayScript, type NicePaymentOptions } from "@/lib/nicepay";
import { trackEvent, EVENTS } from "@/lib/analytics";

interface ApplicationModalProps {
    isOpen: boolean;
    onClose: () => void;
}

type NicePayError = Parameters<NonNullable<NicePaymentOptions["fnError"]>>[0];

export default function ApplicationModal({ isOpen, onClose }: ApplicationModalProps) {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        phone: "",
        track: "A" as "A" | "B", // A: 시네마틱, B: 모션그래픽
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Preload NICE SDK and track modal open
    useEffect(() => {
        if (isOpen) {
            loadNicePayScript().catch(console.warn);
            trackEvent(EVENTS.MODAL_OPEN, { source: 'crebit_landing' });
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);

        try {
            // Step 1: Create application (status: pending)
            const application = await api.applyCrebit(formData as CrebitApplicationRequest);
            trackEvent(EVENTS.FORM_SUBMIT, { track: formData.track, applicationId: application.id });

            // Step 2: Open NICE payment window
            const orderId = application.id;
            const returnUrl = `${window.location.origin}/crebit/payment/callback`;

            await requestNicePayment({
                clientId: process.env.NEXT_PUBLIC_NICEPAY_CLIENT_ID || "S2_af4543a0be4d49a98122e01ec2059a56",
                method: "card",
                orderId,
                amount: CREBIT_PAYMENT.AMOUNT,
                goodsName: CREBIT_PAYMENT.GOODS_NAME,
                returnUrl,
                buyerName: formData.name,
                buyerEmail: formData.email,
                buyerTel: formData.phone,
                fnError: (result: NicePayError) => {
                    // 빈 객체는 사용자가 결제창을 닫거나 취소했을 때 발생
                    if (!result || Object.keys(result).length === 0) {
                        setIsSubmitting(false);
                        return;
                    }
                    console.error("Payment error:", result);
                    setError(`결제 오류: ${result.errorMsg || '알 수 없는 오류'}`);
                    setIsSubmitting(false);
                },
            });

            // Note: After NICE payment window opens, the flow continues 
            // on the returnUrl callback page

        } catch (err) {
            console.error("Application error:", err);
            trackEvent(EVENTS.FORM_ERROR, { error: err instanceof Error ? err.message : 'unknown' });
            setError(err instanceof Error ? err.message : "신청 중 오류가 발생했습니다.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, y: 50, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 50, scale: 0.95 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed left-1/2 top-1/2 z-[70] w-full max-w-md -translate-x-1/2 -translate-y-1/2 p-4"
                    >
                        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0a0a0c] shadow-2xl shadow-[#4200FF]/20">
                            {/* Header */}
                            <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
                                <div>
                                    <h2 className="text-lg font-bold text-white">Crebit ATC 1기 신청</h2>
                                    <p className="text-sm text-slate-400">얼리버드 특가 34만원</p>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
                                    aria-label="닫기"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </div>

                            {/* Success State */}
                            {isSuccess ? (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="flex flex-col items-center justify-center gap-4 py-16"
                                >
                                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20">
                                        <Check className="h-8 w-8 text-emerald-400" />
                                    </div>
                                    <div className="text-center">
                                        <h3 className="text-xl font-bold text-white">신청 완료!</h3>
                                        <p className="mt-2 text-sm text-slate-400">
                                            데모 모드: 실제 결제 연동 준비 중
                                        </p>
                                    </div>
                                </motion.div>
                            ) : (
                                /* Form */
                                <form onSubmit={handleSubmit} className="space-y-4 p-6">
                                    {/* Name */}
                                    <div>
                                        <label className="mb-2 block text-sm font-medium text-slate-300">
                                            이름
                                        </label>
                                        <div className="relative">
                                            <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                                            <input
                                                type="text"
                                                name="name"
                                                value={formData.name}
                                                onChange={handleChange}
                                                required
                                                placeholder="홍길동"
                                                className="w-full rounded-lg border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-white placeholder-slate-500 transition-colors focus:border-[#4200FF]/50 focus:outline-none focus:ring-2 focus:ring-[#4200FF]/20"
                                            />
                                        </div>
                                    </div>

                                    {/* Email */}
                                    <div>
                                        <label className="mb-2 block text-sm font-medium text-slate-300">
                                            이메일
                                        </label>
                                        <div className="relative">
                                            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                                            <input
                                                type="email"
                                                name="email"
                                                value={formData.email}
                                                onChange={handleChange}
                                                required
                                                placeholder="you@example.com"
                                                className="w-full rounded-lg border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-white placeholder-slate-500 transition-colors focus:border-[#4200FF]/50 focus:outline-none focus:ring-2 focus:ring-[#4200FF]/20"
                                            />
                                        </div>
                                    </div>

                                    {/* Phone */}
                                    <div>
                                        <label className="mb-2 block text-sm font-medium text-slate-300">
                                            연락처
                                        </label>
                                        <div className="relative">
                                            <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                                            <input
                                                type="tel"
                                                name="phone"
                                                value={formData.phone}
                                                onChange={handleChange}
                                                required
                                                placeholder="010-1234-5678"
                                                className="w-full rounded-lg border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-white placeholder-slate-500 transition-colors focus:border-[#4200FF]/50 focus:outline-none focus:ring-2 focus:ring-[#4200FF]/20"
                                            />
                                        </div>
                                    </div>

                                    {/* Track Selection */}
                                    <div>
                                        <label className="mb-2 block text-sm font-medium text-slate-300">
                                            트랙 선택
                                        </label>
                                        <div className="grid grid-cols-2 gap-3">
                                            <button
                                                type="button"
                                                onClick={() => setFormData((prev) => ({ ...prev, track: "A" }))}
                                                className={`rounded-lg border p-4 text-left transition-all ${formData.track === "A"
                                                    ? "border-[#4200FF] bg-[#4200FF]/10 text-white"
                                                    : "border-white/10 bg-white/5 text-slate-400 hover:border-white/20"
                                                    }`}
                                            >
                                                <div className="text-sm font-bold">A 트랙</div>
                                                <div className="mt-1 text-xs opacity-70">시네마틱 영상</div>
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setFormData((prev) => ({ ...prev, track: "B" }))}
                                                className={`rounded-lg border p-4 text-left transition-all ${formData.track === "B"
                                                    ? "border-[#FF0045] bg-[#FF0045]/10 text-white"
                                                    : "border-white/10 bg-white/5 text-slate-400 hover:border-white/20"
                                                    }`}
                                            >
                                                <div className="text-sm font-bold">B 트랙</div>
                                                <div className="mt-1 text-xs opacity-70">모션그래픽</div>
                                            </button>
                                        </div>
                                    </div>

                                    {/* Submit Button */}
                                    <button
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-[#4200FF] py-4 font-bold text-white transition-all hover:bg-[#5500FF] disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                        {isSubmitting ? (
                                            <>
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                                결제창 호출 중...
                                            </>
                                        ) : (
                                            <>
                                                <CreditCard className="h-5 w-5" />
                                                결제 진행하기
                                            </>
                                        )}
                                    </button>

                                    {/* Error Display */}
                                    {error && (
                                        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
                                            {error}
                                        </div>
                                    )}

                                    {/* Business Info Disclosure */}
                                    <div className="mt-6 pt-4 border-t border-white/5 text-[10px] text-slate-500 space-y-1">
                                        <p className="font-medium text-slate-400">판매자 정보</p>
                                        <p>주식회사 페이지아카데미 | 대표: 이용찬</p>
                                        <p>사업자번호: 751-88-02370 | 통신판매: 2022-서울성동-00228</p>
                                        <p>서울특별시 성동구 성수이로 113, 8층 801호</p>
                                        <p className="text-[#4200FF]">결제: 나이스페이먼츠(주)</p>
                                    </div>
                                </form>
                            )}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
