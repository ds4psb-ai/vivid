"use client";

/**
 * IP Catalog Error Boundary
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * Handles errors that occur during server component rendering.
 * Provides a user-friendly error message and retry option.
 *
 * 2026 Best Practice:
 * - Error boundaries must be client components
 * - Provide actionable recovery options
 * - Log errors for observability
 */

import { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function IPCatalogError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error for observability
    console.error("[IPCatalogError]", {
      message: error.message,
      digest: error.digest,
      stack: error.stack,
    });
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-0)] p-4">
      <div className="max-w-md w-full bg-[var(--bg-1)] rounded-lg p-8 shadow-lg text-center">
        {/* Error icon */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        {/* Error title */}
        <h1 className="text-xl font-semibold text-[var(--fg-0)] mb-2">
          IP 갤러리를 불러올 수 없습니다
        </h1>

        {/* Error message */}
        <p className="text-sm text-[var(--fg-muted)] mb-6">
          일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
        </p>

        {/* Error digest for debugging */}
        {error.digest && (
          <p className="text-xs text-[var(--fg-muted)] mb-4 font-mono">
            Error ID: {error.digest}
          </p>
        )}

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <RefreshCw className="w-4 h-4" />
            다시 시도
          </button>
          <Link
            href="/"
            className="flex items-center justify-center gap-2 px-4 py-2 border border-[var(--border)] text-[var(--fg-0)] rounded-lg hover:bg-[var(--bg-2)] transition-colors"
          >
            <Home className="w-4 h-4" />
            홈으로 이동
          </Link>
        </div>
      </div>
    </div>
  );
}
