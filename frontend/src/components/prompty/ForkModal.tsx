"use client";

import { useState } from "react";
import { PromptyCommunityProject } from "@/lib/api";

interface ForkModalProps {
  project: PromptyCommunityProject;
  onConfirm: (name: string) => void;
  onCancel: () => void;
}

/**
 * ForkModal - Modal for forking a community project
 *
 * Shows:
 * - Source project info
 * - Name input for the new project
 * - Visibility explanation
 */
export function ForkModal({ project, onConfirm, onCancel }: ForkModalProps) {
  const [name, setName] = useState(`${project.name} (Fork)`);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await onConfirm(name.trim());
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative bg-card border border-border rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <span>🍴</span> 프로젝트 Fork
        </h2>

        {/* Source project info */}
        <div className="p-4 bg-muted rounded-lg mb-4">
          <div className="flex items-start gap-3">
            {project.thumbnail_url ? (
              <img
                src={project.thumbnail_url}
                alt={project.name}
                className="w-16 h-16 rounded-lg object-cover"
              />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-card flex items-center justify-center text-2xl">
                📝
              </div>
            )}
            <div>
              <h3 className="font-semibold">{project.name}</h3>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {project.description || "설명 없음"}
              </p>
              {project.avg_score !== null && project.avg_score !== undefined && (
                <p className="text-sm text-yellow-500 mt-1">
                  평균 점수: {project.avg_score.toFixed(0)}점
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              새 프로젝트 이름
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="프로젝트 이름을 입력하세요"
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              maxLength={200}
              required
            />
          </div>

          {/* Info */}
          <div className="p-3 bg-blue-500/10 text-blue-500 rounded-lg text-sm mb-4">
            <p className="font-medium mb-1">Fork하면:</p>
            <ul className="space-y-1 text-xs">
              <li>• 원본 프로젝트의 설정과 프롬프트가 복사됩니다</li>
              <li>• 새 프로젝트는 비공개로 시작됩니다</li>
              <li>• 원본과 독립적으로 수정할 수 있습니다</li>
            </ul>
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-accent transition disabled:opacity-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !name.trim()}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
            >
              {isSubmitting ? "Fork 중..." : "Fork"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ForkModal;
