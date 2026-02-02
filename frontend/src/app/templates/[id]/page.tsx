"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, PromptyTemplate } from "@/lib/api";

export default function TemplateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;

  const [template, setTemplate] = useState<PromptyTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [using, setUsing] = useState(false);
  const [rating, setRating] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const response = await api.getPromptyTemplate(templateId);
        setTemplate(response);
      } catch (error) {
        console.error("Failed to load template:", error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [templateId]);

  async function useTemplate() {
    setUsing(true);
    try {
      const result = await api.usePromptyTemplate(templateId);
      router.push(`/projects/${result.project_id}`);
    } catch (error) {
      console.error("Failed to use template:", error);
      alert("템플릿 사용에 실패했습니다.");
      setUsing(false);
    }
  }

  async function submitRating(stars: number) {
    setRating(stars);
    try {
      await api.ratePromptyTemplate(templateId, stars);
    } catch (error) {
      console.error("Failed to rate template:", error);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!template) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">템플릿을 찾을 수 없습니다</h1>
        <Link href="/templates" className="text-primary hover:underline">
          템플릿 목록으로 돌아가기
        </Link>
      </div>
    );
  }

  const workflow = (template.workflow_config || {}) as {
    stages?: string[];
    steps?: Record<string, Array<{ id: string; name: string }>>;
  };
  const stages = workflow.stages || [];
  const steps = workflow.steps || {};

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <Link
            href="/templates"
            className="text-muted-foreground hover:text-foreground transition"
          >
            ← 템플릿 목록
          </Link>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-[1fr,400px] gap-8">
          {/* Main Content */}
          <main className="space-y-8">
            {/* Hero */}
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              {/* Thumbnail */}
              <div className="aspect-video bg-muted relative">
                {template.thumbnail_url ? (
                  <img
                    src={template.thumbnail_url}
                    alt={template.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-6xl">
                    {template.category === "video" ? "🎬" : "🖼️"}
                  </div>
                )}
              </div>

              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    {template.is_featured && (
                      <span className="inline-block px-2 py-1 bg-primary/10 text-primary text-xs rounded mb-2">
                        추천 템플릿
                      </span>
                    )}
                    <h1 className="text-3xl font-bold">{template.title}</h1>
                    <p className="text-muted-foreground mt-2">
                      by {template.creator_name}
                    </p>
                  </div>
                </div>

                <p className="text-lg mb-6">{template.description}</p>

                {/* Tags */}
                {template.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-6">
                    {template.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-muted rounded-full text-sm"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Stats */}
                <div className="flex items-center gap-6 text-sm text-muted-foreground">
                  <span>{template.use_count} 사용</span>
                  <span>★ {template.rating_avg.toFixed(1)} ({template.use_count} 평가)</span>
                  <span className="capitalize">{template.category}</span>
                </div>
              </div>
            </div>

            {/* Workflow Preview */}
            {stages.length > 0 && (
              <div className="rounded-xl border border-border bg-card p-6">
                <h2 className="text-xl font-bold mb-6">워크플로우 구성</h2>

                <div className="space-y-6">
                  {stages.map((stage: string, index: number) => (
                    <div key={stage} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                          {index + 1}
                        </div>
                        {index < stages.length - 1 && (
                          <div className="w-0.5 h-full bg-border mt-2" />
                        )}
                      </div>
                      <div className="flex-1 pb-6">
                        <h3 className="font-semibold text-lg capitalize mb-2">
                          {stage}
                        </h3>
                        {steps[stage] && (
                          <ul className="space-y-2">
                            {steps[stage].map((step: { id: string; name: string }) => (
                              <li
                                key={step.id}
                                className="text-sm text-muted-foreground flex items-center gap-2"
                              >
                                <span>○</span>
                                <span>{step.name}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Example Project */}
            {template.example_project_url && (
              <div className="rounded-xl border border-border bg-card p-6">
                <h2 className="text-xl font-bold mb-4">예시 프로젝트</h2>
                <a
                  href={template.example_project_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  예시 프로젝트 보기 →
                </a>
              </div>
            )}
          </main>

          {/* Sidebar */}
          <aside className="space-y-6">
            {/* Use Template CTA */}
            <div className="rounded-xl border border-border bg-card p-6 sticky top-8">
              <h3 className="font-semibold mb-4">이 템플릿으로 시작</h3>

              <button
                onClick={useTemplate}
                disabled={using}
                className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-50"
              >
                {using ? "프로젝트 생성 중..." : "템플릿 사용하기"}
              </button>

              <p className="text-xs text-muted-foreground mt-3 text-center">
                새 프로젝트가 생성되고 워크플로우가 시작됩니다
              </p>
            </div>

            {/* Rate Template */}
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold mb-4">템플릿 평가하기</h3>

              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => submitRating(star)}
                    className={`text-3xl transition ${
                      star <= rating
                        ? "text-yellow-500"
                        : "text-muted-foreground hover:text-yellow-500/50"
                    }`}
                  >
                    ★
                  </button>
                ))}
              </div>

              {rating > 0 && (
                <p className="text-sm text-center text-muted-foreground mt-2">
                  {rating}점으로 평가했습니다
                </p>
              )}
            </div>

            {/* Creator Info */}
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold mb-4">제작자</h3>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-bold text-primary">
                  {template.creator_name.charAt(0)}
                </div>
                <div>
                  <div className="font-medium">{template.creator_name}</div>
                  <div className="text-sm text-muted-foreground">
                    템플릿 제작자
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
