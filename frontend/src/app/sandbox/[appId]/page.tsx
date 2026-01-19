/**
 * Sandbox Preview Page
 * 
 * 앱 샌드박스 미리보기
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Maximize2, Minimize2, RefreshCw, AlertTriangle } from "lucide-react";
import { AppSandbox, DimensionProvider, useDimension } from "@/components/sandbox";
import { getApp, type AppDetail } from "@/lib/admin-api";
import { useCreditSystem } from "@/components/CreditGate";

function SandboxContent({ app }: { app: AppDetail }) {
    const router = useRouter();
    const { applyTheme } = useDimension();
    const { deductCredits } = useCreditSystem();
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Handle dimension sync from app
    const handleDimensionSync = useCallback((theme: {
        theme?: string;
        primaryColor?: string;
        accentColor?: string;
        borderStyle?: string;
    }) => {
        applyTheme(theme);
    }, [applyTheme]);

    // Handle credit request from app
    const handleCreditRequest = useCallback(async (amount: number, reason: string) => {
        const success = await deductCredits(amount, reason);
        return success;
    }, [deductCredits]);

    return (
        <div className={`min-h-screen bg-[#0a0a0b] ${isFullscreen ? "fixed inset-0 z-50" : ""}`}>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-zinc-900 border-b border-zinc-800">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.back()}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-zinc-400" />
                    </button>
                    <div>
                        <h1 className="font-bold text-white">{app.manifest.name}</h1>
                        <p className="text-xs text-zinc-500">v{app.currentVersion} • {app.appId}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => window.location.reload()}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        title="새로고침"
                    >
                        <RefreshCw className="w-4 h-4 text-zinc-400" />
                    </button>
                    <button
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        title={isFullscreen ? "축소" : "전체화면"}
                    >
                        {isFullscreen ? (
                            <Minimize2 className="w-4 h-4 text-zinc-400" />
                        ) : (
                            <Maximize2 className="w-4 h-4 text-zinc-400" />
                        )}
                    </button>
                </div>
            </div>

            {/* Sandbox */}
            <div className={`${isFullscreen ? "h-[var(--layout-app-viewport-md)]" : "h-[var(--layout-app-viewport-xl)]"}`}>
                <AppSandbox
                    appId={app.appId}
                    appUrl={app.sandboxUrl}
                    onDimensionSync={handleDimensionSync}
                    onCreditRequest={handleCreditRequest}
                    className="w-full h-full"
                />
            </div>
        </div>
    );
}

export default function SandboxPage() {
    const params = useParams();
    const appId = params.appId as string;
    const [app, setApp] = useState<AppDetail | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function loadApp() {
            try {
                const data = await getApp(appId);
                setApp(data);
            } catch {
                setError("앱을 찾을 수 없습니다");
            } finally {
                setIsLoading(false);
            }
        }
        loadApp();
    }, [appId]);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-2 border-lime-400 border-t-transparent rounded-full" />
            </div>
        );
    }

    if (error || !app) {
        return (
            <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
                <div className="text-center">
                    <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
                    <p className="text-white mb-2">앱을 불러올 수 없습니다</p>
                    <p className="text-sm text-zinc-500">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <DimensionProvider>
            <SandboxContent app={app} />
        </DimensionProvider>
    );
}
