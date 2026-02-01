"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to Sentry
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="ko">
      <body className="min-h-screen bg-neutral-950 flex items-center justify-center">
        <div className="text-center p-8 max-w-md">
          <div className="text-6xl mb-4">💥</div>
          <h1 className="text-2xl font-bold text-white mb-4">
            문제가 발생했습니다
          </h1>
          <p className="text-neutral-400 mb-6">
            예상치 못한 오류가 발생했습니다. 문제가 자동으로 보고되었습니다.
          </p>
          <button
            onClick={reset}
            className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            다시 시도
          </button>
          {error.digest && (
            <p className="text-neutral-600 text-xs mt-4">
              Error ID: {error.digest}
            </p>
          )}
        </div>
      </body>
    </html>
  );
}
