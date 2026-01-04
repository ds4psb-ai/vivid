/**
 * DimensionBridge Component
 * 
 * 샌드박스된 앱과 플랫폼 간의 양방향 통신 브릿지.
 * 앱이 플랫폼 UI(차원)를 동적으로 변경할 수 있게 합니다.
 */
"use client";

import { createContext, useContext, useCallback, useState, useEffect, ReactNode } from "react";
import { useCreditSystem } from "@/components/CreditGate";

// ============================================
// Dimension Theme Types
// ============================================

export interface DimensionTheme {
    theme: string;
    primaryColor: string;
    accentColor: string;
    borderStyle: string;
    backgroundGradient?: string;
}

// 기본 테마 프리셋
export const DIMENSION_PRESETS: Record<string, DimensionTheme> = {
    default: {
        theme: "default",
        primaryColor: "#84cc16",  // Lime
        accentColor: "#22c55e",   // Green
        borderStyle: "solid",
    },
    cyberpunk: {
        theme: "cyberpunk",
        primaryColor: "#00f0ff",  // Cyan
        accentColor: "#ff00aa",   // Magenta
        borderStyle: "neon-glow",
        backgroundGradient: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2a 100%)",
    },
    cozy: {
        theme: "cozy",
        primaryColor: "#f59e0b",  // Amber
        accentColor: "#ef4444",   // Red
        borderStyle: "rounded",
        backgroundGradient: "linear-gradient(135deg, #1a1510 0%, #2a1a10 100%)",
    },
    horror: {
        theme: "horror",
        primaryColor: "#dc2626",  // Red
        accentColor: "#7c2d12",   // Dark orange
        borderStyle: "jagged",
        backgroundGradient: "linear-gradient(135deg, #0a0505 0%, #1a0a0a 100%)",
    },
    nature: {
        theme: "nature",
        primaryColor: "#22c55e",  // Green
        accentColor: "#14b8a6",   // Teal
        borderStyle: "organic",
        backgroundGradient: "linear-gradient(135deg, #0a1a0f 0%, #0f1a1a 100%)",
    },
};

// ============================================
// Dimension Context
// ============================================

interface DimensionContextType {
    currentTheme: DimensionTheme;
    applyTheme: (theme: Partial<DimensionTheme>) => void;
    resetTheme: () => void;
    isTransitioning: boolean;
}

const DimensionContext = createContext<DimensionContextType | null>(null);

export function useDimension() {
    const context = useContext(DimensionContext);
    if (!context) {
        throw new Error("useDimension must be used within DimensionProvider");
    }
    return context;
}

// ============================================
// Dimension Provider
// ============================================

interface DimensionProviderProps {
    children: ReactNode;
}

export function DimensionProvider({ children }: DimensionProviderProps) {
    const [currentTheme, setCurrentTheme] = useState<DimensionTheme>(DIMENSION_PRESETS.default);
    const [isTransitioning, setIsTransitioning] = useState(false);

    // CSS 변수로 테마 적용
    useEffect(() => {
        const root = document.documentElement;

        root.style.setProperty("--dimension-primary", currentTheme.primaryColor);
        root.style.setProperty("--dimension-accent", currentTheme.accentColor);
        root.style.setProperty("--dimension-border-style", currentTheme.borderStyle);

        if (currentTheme.backgroundGradient) {
            root.style.setProperty("--dimension-bg-gradient", currentTheme.backgroundGradient);
        }
    }, [currentTheme]);

    const applyTheme = useCallback((theme: Partial<DimensionTheme>) => {
        setIsTransitioning(true);

        // 프리셋 테마인 경우
        if (theme.theme && DIMENSION_PRESETS[theme.theme]) {
            setCurrentTheme({
                ...DIMENSION_PRESETS[theme.theme],
                ...theme
            });
        } else {
            // 커스텀 테마
            setCurrentTheme(prev => ({ ...prev, ...theme }));
        }

        // 트랜지션 완료 후 상태 리셋
        setTimeout(() => setIsTransitioning(false), 500);
    }, []);

    const resetTheme = useCallback(() => {
        setIsTransitioning(true);
        setCurrentTheme(DIMENSION_PRESETS.default);
        setTimeout(() => setIsTransitioning(false), 500);
    }, []);

    return (
        <DimensionContext.Provider value={{ currentTheme, applyTheme, resetTheme, isTransitioning }}>
            {children}
        </DimensionContext.Provider>
    );
}

// ============================================
// Dimension Bridge (Message Handler)
// ============================================

interface DimensionBridgeProps {
    allowedOrigins: string[];
    children: ReactNode;
}

export function DimensionBridge({ allowedOrigins, children }: DimensionBridgeProps) {
    const { applyTheme, resetTheme } = useDimension();
    const { deductCredits, checkCredits } = useCreditSystem();

    // 메시지 핸들러
    const handleMessage = useCallback(async (event: MessageEvent) => {
        // Origin 검증
        if (!allowedOrigins.includes(event.origin) && event.origin !== window.location.origin) {
            return;
        }

        const { type, id, payload } = event.data;
        if (!type || typeof type !== "string") return;

        // 응답 전송 헬퍼
        const sendResponse = (success: boolean, data?: unknown, error?: string) => {
            if (event.source && "postMessage" in event.source) {
                (event.source as Window).postMessage(
                    { type: `${type}.response`, id, success, data, error },
                    event.origin
                );
            }
        };

        try {
            switch (type) {
                case "dimension.sync": {
                    const theme = payload as Partial<DimensionTheme>;
                    applyTheme(theme);
                    sendResponse(true);
                    break;
                }

                case "dimension.border": {
                    const { color } = payload as { color: string };
                    applyTheme({ primaryColor: color });
                    sendResponse(true);
                    break;
                }

                case "dimension.reset": {
                    resetTheme();
                    sendResponse(true);
                    break;
                }

                case "credits.deduct": {
                    const { amount, reason } = payload as { amount: number; reason: string };
                    const success = await deductCredits(amount, reason);
                    sendResponse(success, { deducted: success });
                    break;
                }

                case "credits.check": {
                    const { amount } = payload as { amount?: number };
                    const available = await checkCredits(amount ?? 0);
                    sendResponse(true, { available });
                    break;
                }

                case "app.ready": {
                    // 앱이 준비되었음을 알림
                    sendResponse(true, { platform: "crebit", version: "1.0.0" });
                    break;
                }

                case "app.error": {
                    // 에러 로깅 (프로덕션에서는 모니터링 서비스로 전송)
                    sendResponse(true);
                    break;
                }

                default:
                    // 알 수 없는 메시지 타입은 무시
                    break;
            }
        } catch {
            sendResponse(false, null, "Internal error");
        }
    }, [allowedOrigins, applyTheme, resetTheme, deductCredits, checkCredits]);

    // 메시지 리스너 등록
    useEffect(() => {
        window.addEventListener("message", handleMessage);
        return () => window.removeEventListener("message", handleMessage);
    }, [handleMessage]);

    return <>{children}</>;
}

export default DimensionBridge;
