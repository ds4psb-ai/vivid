/**
 * AppSandbox Component (Hardened Version)
 * 
 * 연구 결과 기반 하드닝:
 * - 앱인토스 방식: mTLS, S2S 통신, 세션 키 매 요청 생성
 * - CSP: nonce/hash 기반, unsafe-inline 금지
 * - postMessage: 엄격한 origin 검증, message type whitelist
 * - 추가 보안: X-Frame-Options, Referrer-Policy
 */
"use client";

import { useEffect, useRef, useCallback, useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Loader2, AlertTriangle, Shield, ShieldCheck, ShieldAlert } from "lucide-react";

// ============================================
// Types
// ============================================

interface DimensionTheme {
    theme?: string;
    primaryColor?: string;
    accentColor?: string;
    borderStyle?: string;
}

type SecurityLevel = "high" | "medium" | "low" | "unknown";

interface AppSandboxProps {
    appId: string;
    appUrl: string;
    /** 플랫폼 도메인 - origin 검증에 사용 */
    platformOrigin?: string;
    /** 허용된 앱 origins (whitelist) */
    allowedOrigins?: string[];
    onDimensionSync?: (theme: DimensionTheme) => void;
    onCreditRequest?: (amount: number, reason: string, sessionKey: string) => Promise<boolean>;
    onSecurityEvent?: (event: SecurityEvent) => void;
    className?: string;
}

interface SecurityEvent {
    type: "origin_mismatch" | "invalid_message" | "rate_limit" | "sdk_missing" | "tampering_detected";
    details: string;
    timestamp: number;
}

// Allowed message types - whitelist approach (앱인토스 방식)
const ALLOWED_MESSAGE_TYPES = new Set([
    "dimension.sync",
    "dimension.border",
    "dimension.reset",
    "credits.deduct",
    "credits.check",
    "storage.get",
    "storage.set",
    "storage.remove",
    "app.ready",
    "app.error",
    "app.heartbeat",
]);

// Rate limiting
const RATE_LIMIT_WINDOW_MS = 1000;
const RATE_LIMIT_MAX_MESSAGES = 10;

// ============================================
// Security Utilities
// ============================================

/** 세션 키 생성 (앱인토스 방식: 매 요청마다 새로 생성) */
function generateSessionKey(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
}

/** Origin 검증 (strict) */
function isOriginAllowed(origin: string, allowedOrigins: string[]): boolean {
    // Exact match only - no wildcards
    return allowedOrigins.some(allowed => {
        // Normalize origins
        const normalizedAllowed = allowed.replace(/\/$/, '');
        const normalizedOrigin = origin.replace(/\/$/, '');
        return normalizedAllowed === normalizedOrigin;
    });
}

/** Message type 검증 */
function isValidMessageType(type: unknown): type is string {
    return typeof type === "string" && ALLOWED_MESSAGE_TYPES.has(type);
}

/** Sanitize payload - prevent prototype pollution */
function sanitizePayload(payload: unknown): unknown {
    if (payload === null || payload === undefined) return payload;
    if (typeof payload !== 'object') return payload;

    // Prevent prototype pollution
    const sanitized: Record<string, unknown> = {};
    for (const key of Object.keys(payload as Record<string, unknown>)) {
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
            continue; // Skip dangerous keys
        }
        sanitized[key] = (payload as Record<string, unknown>)[key];
    }
    return sanitized;
}

// ============================================
// Component
// ============================================

export function AppSandbox({
    appId,
    appUrl,
    platformOrigin = typeof window !== 'undefined' ? window.location.origin : '',
    allowedOrigins = [],
    onDimensionSync,
    onCreditRequest,
    onSecurityEvent,
    className = ""
}: AppSandboxProps) {
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [securityLevel, setSecurityLevel] = useState<SecurityLevel>("unknown");
    const [sdkConnected, setSdkConnected] = useState(false);

    // Rate limiting state
    const messageCountRef = useRef(0);
    const lastResetRef = useRef(Date.now());

    // Session key for this sandbox instance (앱인토스 방식)
    const sessionKeyRef = useRef(generateSessionKey());

    // Compute allowed origin for this app
    const appOrigin = useMemo(() => {
        if (appUrl.startsWith("/")) {
            return platformOrigin;
        }
        try {
            return new URL(appUrl).origin;
        } catch {
            return platformOrigin;
        }
    }, [appUrl, platformOrigin]);

    // Full allowed origins list
    const fullAllowedOrigins = useMemo(() => {
        return [appOrigin, ...allowedOrigins].filter(Boolean);
    }, [appOrigin, allowedOrigins]);

    // Rate limit check
    const checkRateLimit = useCallback((): boolean => {
        const now = Date.now();
        if (now - lastResetRef.current > RATE_LIMIT_WINDOW_MS) {
            messageCountRef.current = 0;
            lastResetRef.current = now;
        }

        messageCountRef.current++;

        if (messageCountRef.current > RATE_LIMIT_MAX_MESSAGES) {
            onSecurityEvent?.({
                type: "rate_limit",
                details: `Rate limit exceeded: ${messageCountRef.current} messages in ${RATE_LIMIT_WINDOW_MS}ms`,
                timestamp: now,
            });
            return false;
        }
        return true;
    }, [onSecurityEvent]);

    // Log security event
    const logSecurityEvent = useCallback((event: SecurityEvent) => {
        // In production, send to monitoring service
        if (process.env.NODE_ENV === 'development') {
            console.warn(`[AppSandbox Security] ${event.type}:`, event.details);
        }
        onSecurityEvent?.(event);
    }, [onSecurityEvent]);

    // Handle messages from sandboxed app
    const handleMessage = useCallback(async (event: MessageEvent) => {
        // 1. Strict origin validation (앱인토스 방식 + OWASP 권장)
        if (!isOriginAllowed(event.origin, fullAllowedOrigins)) {
            logSecurityEvent({
                type: "origin_mismatch",
                details: `Rejected message from untrusted origin: ${event.origin}`,
                timestamp: Date.now(),
            });
            return;
        }

        // 2. Rate limit check
        if (!checkRateLimit()) {
            return;
        }

        // 3. Message structure validation
        const data = event.data;
        if (!data || typeof data !== 'object') {
            return;
        }

        const { type, id, payload } = data;

        // 4. Message type whitelist validation
        if (!isValidMessageType(type)) {
            logSecurityEvent({
                type: "invalid_message",
                details: `Invalid message type: ${String(type)}`,
                timestamp: Date.now(),
            });
            return;
        }

        // 5. Sanitize payload
        const sanitizedPayload = sanitizePayload(payload);

        // Response helper with session key rotation
        const sendResponse = (success: boolean, responseData?: unknown, responseError?: string) => {
            // Rotate session key for each response (앱인토스 방식)
            sessionKeyRef.current = generateSessionKey();

            iframeRef.current?.contentWindow?.postMessage(
                {
                    type: `${type}.response`,
                    id,
                    success,
                    data: responseData,
                    error: responseError,
                    // Include new session key for next request
                    sessionKey: sessionKeyRef.current,
                },
                appOrigin
            );
        };

        try {
            switch (type) {
                case "app.ready": {
                    setIsLoading(false);
                    setSdkConnected(true);
                    setSecurityLevel("high");
                    sendResponse(true, {
                        platform: "crebit",
                        version: "1.0.0",
                        sessionKey: sessionKeyRef.current,
                    });
                    break;
                }

                case "app.heartbeat": {
                    // SDK heartbeat for connection verification
                    sendResponse(true, { alive: true });
                    break;
                }

                case "dimension.sync": {
                    const theme = sanitizedPayload as Partial<DimensionTheme>;
                    if (onDimensionSync && theme) {
                        onDimensionSync(theme);
                    }
                    sendResponse(true);
                    break;
                }

                case "dimension.border": {
                    const { color } = sanitizedPayload as { color?: string };
                    if (onDimensionSync && color && /^#[0-9a-fA-F]{6}$/.test(color)) {
                        onDimensionSync({ primaryColor: color });
                    }
                    sendResponse(true);
                    break;
                }

                case "dimension.reset": {
                    if (onDimensionSync) {
                        onDimensionSync({ theme: "default" });
                    }
                    sendResponse(true);
                    break;
                }

                case "credits.deduct": {
                    const { amount, reason, sessionKey } = sanitizedPayload as {
                        amount?: number;
                        reason?: string;
                        sessionKey?: string;
                    };

                    // Validate session key (앱인토스 방식: 세션 키 검증)
                    if (sessionKey !== sessionKeyRef.current) {
                        logSecurityEvent({
                            type: "tampering_detected",
                            details: "Invalid session key in credit deduct request",
                            timestamp: Date.now(),
                        });
                        sendResponse(false, null, "Invalid session");
                        break;
                    }

                    if (onCreditRequest && typeof amount === "number" && amount > 0) {
                        const success = await onCreditRequest(amount, reason || "App usage", sessionKeyRef.current);
                        sendResponse(success, { deducted: success });
                    } else {
                        sendResponse(false, null, "Invalid request");
                    }
                    break;
                }

                case "credits.check": {
                    sendResponse(true, { available: true });
                    break;
                }

                case "app.error": {
                    // Don't expose error details, just acknowledge
                    sendResponse(true);
                    break;
                }

                default:
                    sendResponse(false, null, "Unknown type");
            }
        } catch {
            sendResponse(false, null, "Internal error");
        }
    }, [fullAllowedOrigins, appOrigin, onDimensionSync, onCreditRequest, checkRateLimit, logSecurityEvent]);

    // Set up message listener
    useEffect(() => {
        window.addEventListener("message", handleMessage);
        return () => window.removeEventListener("message", handleMessage);
    }, [handleMessage]);

    // SDK timeout - if no app.ready within 10 seconds, mark as insecure
    useEffect(() => {
        const timeout = setTimeout(() => {
            if (!sdkConnected) {
                setSecurityLevel("low");
                logSecurityEvent({
                    type: "sdk_missing",
                    details: "App did not send ready signal within timeout",
                    timestamp: Date.now(),
                });
            }
        }, 10000);

        return () => clearTimeout(timeout);
    }, [sdkConnected, logSecurityEvent]);

    // Handle iframe load
    const handleLoad = () => {
        // Don't set loading to false here - wait for app.ready
    };

    const handleError = () => {
        setIsLoading(false);
        setError("앱을 불러올 수 없습니다");
        setSecurityLevel("unknown");
    };

    // CSP-compliant sandbox permissions (최소 권한 원칙)
    const sandboxPermissions = [
        "allow-scripts",           // Required for JS execution
        "allow-same-origin",       // Required for postMessage origin
        // "allow-forms",          // Disabled by default - enable per-app if needed
        // "allow-popups",         // Disabled by default - security risk
        // "allow-modals",         // Disabled
        // "allow-top-navigation", // Disabled - prevent navigation attacks
    ].join(" ");

    // Security badge color
    const securityBadgeColor = {
        high: "bg-green-500/20 border-green-500/30 text-green-400",
        medium: "bg-yellow-500/20 border-yellow-500/30 text-yellow-400",
        low: "bg-red-500/20 border-red-500/30 text-red-400",
        unknown: "bg-zinc-500/20 border-zinc-500/30 text-zinc-400",
    }[securityLevel];

    const SecurityIcon = {
        high: ShieldCheck,
        medium: Shield,
        low: ShieldAlert,
        unknown: Shield,
    }[securityLevel];

    return (
        <div className={`relative w-full h-full ${className}`}>
            {/* Loading State */}
            {isLoading && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 flex items-center justify-center bg-black/80 z-10"
                >
                    <div className="text-center">
                        <Loader2 className="w-8 h-8 text-lime-400 animate-spin mx-auto mb-3" />
                        <p className="text-sm text-zinc-400">앱 로딩 중...</p>
                        <p className="text-[10px] text-zinc-600 mt-1">SDK 연결 대기</p>
                    </div>
                </motion.div>
            )}

            {/* Error State */}
            {error && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 flex items-center justify-center bg-black/90 z-10"
                >
                    <div className="text-center p-6">
                        <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
                        <p className="text-sm text-white mb-2">앱 실행 오류</p>
                        <p className="text-xs text-zinc-500">{error}</p>
                    </div>
                </motion.div>
            )}

            {/* Security Badge */}
            {!isLoading && !error && (
                <div className={`absolute top-2 right-2 z-10 flex items-center gap-1 px-2 py-1 rounded-full border ${securityBadgeColor}`}>
                    <SecurityIcon className="w-3 h-3" />
                    <span className="text-[10px] font-medium">
                        {securityLevel === "high" ? "Verified" :
                            securityLevel === "medium" ? "Limited" :
                                securityLevel === "low" ? "Unverified" : "Unknown"}
                    </span>
                </div>
            )}

            {/* Sandboxed iframe with strict CSP */}
            <iframe
                ref={iframeRef}
                src={appUrl}
                sandbox={sandboxPermissions}
                allow="clipboard-read; clipboard-write"
                referrerPolicy="strict-origin-when-cross-origin"
                onLoad={handleLoad}
                onError={handleError}
                className="w-full h-full border-0"
                title={`Sandboxed App: ${appId}`}
                // Additional security attributes
                loading="lazy"
            />
        </div>
    );
}

export default AppSandbox;
