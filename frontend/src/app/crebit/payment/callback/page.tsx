"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2, CheckCircle, XCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

function PaymentCallbackContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [status, setStatus] = useState<"processing" | "success" | "failed">("processing");
    const [message, setMessage] = useState("결제 처리 중...");

    useEffect(() => {
        const processPayment = async () => {
            // Get callback parameters
            const authResultCode = searchParams.get("authResultCode");
            const tid = searchParams.get("tid");
            const orderId = searchParams.get("orderId");
            const amount = searchParams.get("amount");

            if (!authResultCode || !tid || !orderId || !amount) {
                setStatus("failed");
                setMessage("결제 정보가 누락되었습니다.");
                return;
            }

            if (authResultCode !== "0000") {
                setStatus("failed");
                setMessage(searchParams.get("authResultMsg") || "카드 인증에 실패했습니다.");
                return;
            }

            try {
                // Call backend to confirm payment
                const response = await fetch(`${API_BASE_URL}/api/v1/payment/confirm`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        tid,
                        amount: parseInt(amount),
                        application_id: orderId,
                    }),
                });

                const result = await response.json();

                if (result.success) {
                    setStatus("success");
                    setMessage("결제가 완료되었습니다!");
                } else {
                    setStatus("failed");
                    setMessage(result.result_msg || "결제 승인에 실패했습니다.");
                }
            } catch (error) {
                console.error("Payment confirmation error:", error);
                setStatus("failed");
                setMessage("결제 처리 중 오류가 발생했습니다.");
            }
        };

        processPayment();
    }, [searchParams]);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md bg-[#0a0a0c] border border-white/10 rounded-2xl p-8 text-center"
        >
            {status === "processing" && (
                <>
                    <Loader2 className="w-16 h-16 text-[#4200FF] animate-spin mx-auto mb-6" />
                    <h1 className="text-xl font-bold text-white mb-2">결제 처리 중</h1>
                    <p className="text-slate-400">{message}</p>
                </>
            )}

            {status === "success" && (
                <>
                    <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h1 className="text-xl font-bold text-white mb-2">결제 완료!</h1>
                    <p className="text-slate-400 mb-8">{message}</p>
                    <div className="space-y-3">
                        <Link
                            href="/crebit"
                            className="block w-full bg-[#4200FF] text-white py-3 rounded-xl font-bold hover:bg-[#5500FF] transition-colors"
                        >
                            Crebit 페이지로 돌아가기
                        </Link>
                    </div>
                </>
            )}

            {status === "failed" && (
                <>
                    <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
                        <XCircle className="w-10 h-10 text-red-400" />
                    </div>
                    <h1 className="text-xl font-bold text-white mb-2">결제 실패</h1>
                    <p className="text-slate-400 mb-8">{message}</p>
                    <div className="space-y-3">
                        <Link
                            href="/crebit"
                            className="flex items-center justify-center gap-2 w-full bg-white/10 text-white py-3 rounded-xl font-bold hover:bg-white/20 transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            다시 시도하기
                        </Link>
                    </div>
                </>
            )}
        </motion.div>
    );
}

function LoadingFallback() {
    return (
        <div className="w-full max-w-md bg-[#0a0a0c] border border-white/10 rounded-2xl p-8 text-center">
            <Loader2 className="w-16 h-16 text-[#4200FF] animate-spin mx-auto mb-6" />
            <h1 className="text-xl font-bold text-white mb-2">로딩 중...</h1>
        </div>
    );
}

export default function PaymentCallbackPage() {
    return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6">
            <Suspense fallback={<LoadingFallback />}>
                <PaymentCallbackContent />
            </Suspense>
        </div>
    );
}
