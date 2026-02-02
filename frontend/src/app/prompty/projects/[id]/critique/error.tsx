"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

export default function CritiqueError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const params = useParams();
  const projectId = params.id as string;

  return (
    <div className="container mx-auto px-4 py-12 text-center">
      <div className="max-w-md mx-auto">
        <h2 className="text-xl font-bold mb-4">Critique 로딩 실패</h2>
        <p className="text-muted-foreground mb-6">
          {error.message || "Critique 데이터를 불러올 수 없습니다."}
        </p>
        {error.digest && (
          <p className="text-xs text-muted-foreground mb-4">
            Error ID: {error.digest}
          </p>
        )}
        <div className="flex gap-4 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
          >
            다시 시도
          </button>
          <Link
            href={`/prompty/projects/${projectId}`}
            className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition"
          >
            프로젝트로 돌아가기
          </Link>
        </div>
      </div>
    </div>
  );
}
