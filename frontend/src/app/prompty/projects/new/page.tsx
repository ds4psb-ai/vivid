"use client";

/**
 * New Project Creation Page
 *
 * Handles project creation flow:
 * - Authenticated users: Create on server, redirect to project
 * - Unauthenticated users: Create locally, redirect to local project
 */

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useSessionContext } from "@/contexts/SessionContext";
import { useToast } from "@/components/Toast";
import { localProjectsService } from "@/lib/local-projects";

export default function NewProjectPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: sessionLoading } = useSessionContext();
  const toast = useToast();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [storageAvailable, setStorageAvailable] = useState(true);

  // Get template_id from query param if present
  const templateId = searchParams.get("template");

  // Check localStorage availability
  useEffect(() => {
    setStorageAvailable(localProjectsService.isAvailable());
  }, []);

  // Set default name
  useEffect(() => {
    if (!name) {
      setName(`새 프로젝트 ${new Date().toLocaleDateString("ko-KR")}`);
    }
  }, [name]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!name.trim()) {
      toast.error("프로젝트 이름을 입력하세요");
      return;
    }

    setCreating(true);
    try {
      if (isAuthenticated) {
        // Create on server
        const project = await api.createPromptyProject({
          name: name.trim(),
          description: description.trim() || undefined,
          template_id: templateId || undefined,
        });
        router.push(`/prompty/projects/${project.id}`);
      } else {
        // Create locally
        if (!storageAvailable) {
          toast.error("시크릿 모드에서는 프로젝트를 저장할 수 없습니다");
          setCreating(false);
          return;
        }
        // Note: local projects don't support description
        const local = localProjectsService.create({
          name: name.trim(),
        });
        if (local) {
          router.push(`/prompty/projects/local:${local.local_id}`);
        } else {
          toast.error("프로젝트 생성 실패");
          setCreating(false);
        }
      }
    } catch (error) {
      console.error("Failed to create project:", error);
      toast.error("프로젝트 생성 실패");
      setCreating(false);
    }
  }

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link
              href="/prompty/projects"
              className="text-sm text-muted-foreground hover:text-foreground transition mb-4 inline-block"
            >
              ← 프로젝트 목록
            </Link>
            <h1 className="text-3xl font-bold">새 프로젝트</h1>
            <p className="text-muted-foreground mt-2">
              {isAuthenticated
                ? "새 워크플로우 프로젝트를 시작합니다"
                : "로컬에 프로젝트를 저장합니다. 로그인하면 동기화됩니다."}
            </p>
          </div>

          {/* Storage Warning for Incognito */}
          {!isAuthenticated && !storageAvailable && (
            <div className="mb-6 p-4 rounded-xl border border-yellow-500/30 bg-yellow-500/10">
              <p className="text-sm text-yellow-600">
                시크릿/비공개 모드에서는 프로젝트가 저장되지 않습니다.
                <br />
                일반 모드를 사용하거나{" "}
                <Link href="/login" className="underline">
                  로그인
                </Link>
                하세요.
              </p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="rounded-xl border border-border bg-card p-6 space-y-4">
              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-medium mb-2"
                >
                  프로젝트 이름 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="예: 뮤직비디오 프로젝트"
                  maxLength={200}
                  className="w-full px-4 py-3 rounded-lg border border-border bg-background focus:border-primary focus:ring-1 focus:ring-primary outline-none transition"
                  autoFocus
                />
              </div>

              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium mb-2"
                >
                  설명 <span className="text-muted-foreground">(선택)</span>
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="프로젝트에 대한 간단한 설명..."
                  rows={3}
                  className="w-full px-4 py-3 rounded-lg border border-border bg-background focus:border-primary focus:ring-1 focus:ring-primary outline-none transition resize-none"
                />
              </div>

              {templateId && (
                <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                  <p className="text-sm text-muted-foreground">
                    템플릿 기반으로 생성됩니다
                  </p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Link
                href="/prompty/projects"
                className="flex-1 px-6 py-3 text-center border border-border rounded-lg hover:bg-accent transition"
              >
                취소
              </Link>
              <button
                type="submit"
                disabled={creating || (!isAuthenticated && !storageAvailable)}
                className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
              >
                {creating ? "생성 중..." : "프로젝트 생성"}
              </button>
            </div>
          </form>

          {/* Quick Start Options */}
          <div className="mt-8 pt-8 border-t border-border">
            <h2 className="text-lg font-semibold mb-4">또는 템플릿으로 시작</h2>
            <Link
              href="/prompty/templates"
              className="block p-4 rounded-xl border border-border bg-card hover:border-primary/50 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">템플릿 갤러리</h3>
                  <p className="text-sm text-muted-foreground">
                    미리 설정된 워크플로우로 빠르게 시작하세요
                  </p>
                </div>
                <span className="text-muted-foreground">→</span>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
