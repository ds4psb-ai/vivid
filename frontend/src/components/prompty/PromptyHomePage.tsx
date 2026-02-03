"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PromptyTemplate, AuthSession } from "@/lib/api";
import PromptyDashboard from "@/components/prompty/PromptyDashboard";

export default function PromptyHomePage() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [featuredTemplates, setFeaturedTemplates] = useState<PromptyTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function init() {
      try {
        // Check auth session
        const authSession = await api.getSession();
        setSession(authSession);

        // Only load templates for landing page (not logged in)
        if (!authSession.authenticated) {
          const response = await api.listPromptyTemplates(1, 6, { featured_only: true });
          setFeaturedTemplates(response.items);
        }
      } catch (error) {
        console.error("Failed to initialize:", error);
        // On auth error, show landing page
        try {
          const response = await api.listPromptyTemplates(1, 6, { featured_only: true });
          setFeaturedTemplates(response.items);
        } catch {
          // Ignore template load error
        }
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Show loading state
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-8">
          <div className="h-48 bg-muted rounded-xl" />
          <div className="grid md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-muted rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Logged in -> Show Dashboard
  if (session?.authenticated) {
    return <PromptyDashboard />;
  }

  // Not logged in -> Show Landing (PromptyLanding inlined)

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold mb-8">
          prompty<span className="text-primary">.co.kr</span>
        </h1>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link
            href="/templates"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
          >
            템플릿 둘러보기
          </Link>
          <Link
            href="/projects"
            className="px-6 py-3 border border-border rounded-lg font-medium hover:bg-accent transition"
          >
            내 프로젝트
          </Link>
          <a
            href="/api/download/package"
            className="px-6 py-3 border border-border rounded-lg font-medium hover:bg-accent transition flex items-center gap-2"
          >
            <span>📦</span>
            <span>프로젝트 패키지 다운로드</span>
          </a>
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
          <Link href="/templates" className="text-primary hover:underline">
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
                href={`/templates/${template.id}`}
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

    </div>
  );
}
