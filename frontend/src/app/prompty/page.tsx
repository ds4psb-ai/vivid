"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PromptyTemplate } from "@/lib/api";

export default function PromptyHomePage() {
  const [featuredTemplates, setFeaturedTemplates] = useState<PromptyTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTemplates() {
      try {
        const response = await api.listPromptyTemplates(1, 6, { featured_only: true });
        setFeaturedTemplates(response.items);
      } catch (error) {
        console.error("Failed to load templates:", error);
      } finally {
        setLoading(false);
      }
    }
    loadTemplates();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold mb-4">
          prompty<span className="text-primary">.co.kr</span>
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          AI 없이도 98% 품질. Gemini CLI + Antigravity로 직접 만드는 바이럴 콘텐츠 가이드
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/prompty/templates"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
          >
            템플릿 둘러보기
          </Link>
          <Link
            href="/prompty/projects"
            className="px-6 py-3 border border-border rounded-lg font-medium hover:bg-accent transition"
          >
            내 프로젝트
          </Link>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-12">
        <h2 className="text-2xl font-bold mb-8 text-center">Tiki-Taka 워크플로우</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { step: 1, title: "템플릿 선택", desc: "검증된 워크플로우 템플릿으로 시작" },
            { step: 2, title: "프롬프트 복사", desc: "단계별 프롬프트를 클립보드에 복사" },
            { step: 3, title: "외부 도구 실행", desc: "NanoBanana, Kling 등에서 직접 생성" },
            { step: 4, title: "Critique 평가", desc: "체크리스트로 품질 점수화" },
          ].map((item) => (
            <div key={item.step} className="text-center p-6 rounded-xl border border-border bg-card">
              <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xl font-bold mx-auto mb-4">
                {item.step}
              </div>
              <h3 className="font-semibold mb-2">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Featured Templates */}
      <section className="py-12">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold">추천 템플릿</h2>
          <Link href="/prompty/templates" className="text-primary hover:underline">
            전체 보기 &rarr;
          </Link>
        </div>

        {loading ? (
          <div className="grid md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        ) : featuredTemplates.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            아직 템플릿이 없습니다. 곧 추가될 예정입니다.
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {featuredTemplates.map((template) => (
              <Link
                key={template.id}
                href={`/prompty/templates/${template.id}`}
                className="group block rounded-xl border border-border bg-card overflow-hidden hover:border-primary/50 transition"
              >
                <div className="aspect-video bg-muted relative">
                  {template.thumbnail_url ? (
                    <img
                      src={template.thumbnail_url}
                      alt={template.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl">
                      {template.category === "video" ? "🎬" : "🖼️"}
                    </div>
                  )}
                  {template.is_featured && (
                    <span className="absolute top-2 right-2 px-2 py-1 bg-primary text-primary-foreground text-xs rounded">
                      추천
                    </span>
                  )}
                </div>
                <div className="p-4">
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition">
                    {template.title}
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {template.description}
                  </p>
                  <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                    <span>{template.use_count} 사용</span>
                    <span>★ {template.rating_avg.toFixed(1)}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Why Prompty */}
      <section className="py-12 text-center">
        <h2 className="text-2xl font-bold mb-8">왜 Prompty인가요?</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="p-6">
            <div className="text-4xl mb-4">💰</div>
            <h3 className="font-semibold mb-2">비용 $200 → $10</h3>
            <p className="text-sm text-muted-foreground">
              AI API 직접 호출 대신 로컬 도구 활용으로 95% 비용 절감
            </p>
          </div>
          <div className="p-6">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="font-semibold mb-2">품질 70% → 98%</h3>
            <p className="text-sm text-muted-foreground">
              Critique 체크리스트로 각 단계 품질 보장
            </p>
          </div>
          <div className="p-6">
            <div className="text-4xl mb-4">🚀</div>
            <h3 className="font-semibold mb-2">학습 효과</h3>
            <p className="text-sm text-muted-foreground">
              단순 생성이 아닌 프로세스 학습으로 실력 향상
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
