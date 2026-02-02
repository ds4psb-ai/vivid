"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, PromptyProject } from "@/lib/api";

type FilterStatus = "all" | "active" | "completed";
type SortOrder = "recent" | "oldest" | "score";

interface QuickStats {
  inProgress: number;
  completed: number;
  avgScore: number | null;
}

/**
 * PromptyDashboard - Main dashboard for logged-in users
 *
 * Shows:
 * - Quick stats (inline)
 * - In-progress projects with resume CTA
 * - Full project list with filters
 */
export function PromptyDashboard() {
  const [projects, setProjects] = useState<PromptyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [sort, setSort] = useState<SortOrder>("recent");

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setLoading(true);
      const response = await api.listPromptyProjects(1, 100);
      setProjects(response.items);
    } catch (error) {
      console.error("Failed to load projects:", error);
    } finally {
      setLoading(false);
    }
  }

  // Calculate quick stats
  const stats: QuickStats = {
    inProgress: projects.filter((p) => p.status === "active").length,
    completed: projects.filter((p) => p.status === "completed").length,
    avgScore: calculateAvgScore(projects),
  };

  // Filter and sort projects
  const filteredProjects = projects
    .filter((p) => {
      if (filter === "all") return true;
      if (filter === "active") return p.status === "active";
      if (filter === "completed") return p.status === "completed";
      return true;
    })
    .sort((a, b) => {
      if (sort === "recent") {
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      }
      if (sort === "oldest") {
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      }
      if (sort === "score") {
        return (b.avg_score ?? 0) - (a.avg_score ?? 0);
      }
      return 0;
    });

  // Get in-progress projects for hero section
  const inProgressProjects = projects
    .filter((p) => p.status === "active")
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 3);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-24 bg-muted rounded-xl" />
          <div className="h-48 bg-muted rounded-xl" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-muted rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Quick Stats (inline) */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="진행중" value={stats.inProgress} icon="🔥" color="text-orange-500" />
        <StatCard label="완료" value={stats.completed} icon="✅" color="text-green-500" />
        <StatCard
          label="평균 점수"
          value={stats.avgScore !== null ? `${stats.avgScore.toFixed(0)}점` : "-"}
          icon="⭐"
          color="text-yellow-500"
        />
      </div>

      {/* In-Progress Projects Hero */}
      {inProgressProjects.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span className="text-orange-500">🔥</span> 진행 중인 프로젝트
            </h2>
            <Link
              href="/prompty/projects/new"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90 transition"
            >
              + 새 프로젝트
            </Link>
          </div>

          <div className="space-y-3">
            {inProgressProjects.map((project) => (
              <InProgressCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* All Projects */}
      <section className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <span>📁</span> 전체 프로젝트
          </h2>

          <div className="flex items-center gap-3">
            {/* Sort */}
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortOrder)}
              className="px-3 py-1.5 border border-border rounded-lg text-sm bg-background"
            >
              <option value="recent">최신순</option>
              <option value="oldest">오래된순</option>
              <option value="score">점수순</option>
            </select>

            {/* Filter */}
            <div className="flex border border-border rounded-lg overflow-hidden">
              {(["all", "active", "completed"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 text-sm transition ${
                    filter === f
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent"
                  }`}
                >
                  {f === "all" ? "전체" : f === "active" ? "진행중" : "완료"}
                </button>
              ))}
            </div>

            {inProgressProjects.length === 0 && (
              <Link
                href="/prompty/projects/new"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90 transition"
              >
                + 새 프로젝트
              </Link>
            )}
          </div>
        </div>

        {filteredProjects.length === 0 ? (
          <EmptyState filter={filter} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </section>

      {/* Community CTA */}
      <section className="mt-12 p-6 rounded-xl border border-primary/20 bg-primary/5 text-center">
        <h3 className="text-lg font-semibold mb-2">다른 사람들의 프로젝트가 궁금하신가요?</h3>
        <p className="text-muted-foreground mb-4">
          커뮤니티에서 다양한 프로젝트를 둘러보고 Fork해서 나만의 버전을 만들어보세요.
        </p>
        <Link
          href="/prompty/community"
          className="inline-block px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
        >
          커뮤니티 둘러보기
        </Link>
      </section>
    </div>
  );
}

// =============================================================================
// Sub Components
// =============================================================================

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: string;
  color: string;
}) {
  return (
    <div className="p-4 rounded-xl border border-border bg-card">
      <div className="flex items-center gap-3">
        <span className={`text-2xl ${color}`}>{icon}</span>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-muted-foreground">{label}</p>
        </div>
      </div>
    </div>
  );
}

function InProgressCard({ project }: { project: PromptyProject }) {
  const stepNum = parseInt(project.current_step.replace(/\D/g, "") || "1");
  const totalSteps = 6;

  return (
    <Link
      href={`/prompty/projects/${project.id}`}
      className="block p-4 rounded-xl border border-primary/30 bg-primary/5 hover:border-primary/50 transition"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Progress indicator */}
          <div className="w-12 h-12 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold">
            {stepNum}/{totalSteps}
          </div>

          <div>
            <h3 className="font-semibold">{project.name}</h3>
            <p className="text-sm text-muted-foreground">
              Step {stepNum}: {project.current_stage}
              {project.avg_score !== null && project.avg_score !== undefined && (
                <span className="ml-2 text-yellow-500">
                  {project.avg_score.toFixed(0)}점
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {formatRelativeTime(project.updated_at)}
          </span>
          <span className="px-3 py-1 bg-primary text-primary-foreground rounded-lg text-sm">
            재개 &rarr;
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all"
          style={{ width: `${project.progress_percent}%` }}
        />
      </div>
    </Link>
  );
}

function ProjectCard({ project }: { project: PromptyProject }) {
  const isCompleted = project.status === "completed";

  return (
    <Link
      href={`/prompty/projects/${project.id}`}
      className="group block rounded-xl border border-border bg-card overflow-hidden hover:border-primary/50 transition"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-muted relative">
        {project.thumbnail_url ? (
          <img
            src={project.thumbnail_url}
            alt={project.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">
            {isCompleted ? "🎬" : "📝"}
          </div>
        )}

        {/* Status badge */}
        <span
          className={`absolute top-2 right-2 px-2 py-1 rounded text-xs ${
            isCompleted
              ? "bg-green-500/90 text-white"
              : "bg-orange-500/90 text-white"
          }`}
        >
          {isCompleted ? "완료" : `${project.progress_percent}%`}
        </span>

        {/* Visibility badge */}
        {project.visibility !== "private" && (
          <span className="absolute top-2 left-2 px-2 py-1 rounded text-xs bg-blue-500/90 text-white">
            {project.visibility === "full" ? "공개" : "일부공개"}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-semibold mb-1 group-hover:text-primary transition line-clamp-1">
          {project.name}
        </h3>
        {project.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {project.description}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{formatRelativeTime(project.updated_at)}</span>
          <div className="flex items-center gap-3">
            {project.avg_score !== null && project.avg_score !== undefined && (
              <span className="text-yellow-500">
                {project.avg_score.toFixed(0)}점
              </span>
            )}
            {project.fork_count > 0 && (
              <span className="flex items-center gap-1">
                <span>🍴</span> {project.fork_count}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

function EmptyState({ filter }: { filter: FilterStatus }) {
  return (
    <div className="text-center py-12 rounded-xl border border-dashed border-border">
      <div className="text-4xl mb-4">
        {filter === "completed" ? "🎉" : filter === "active" ? "🚀" : "📝"}
      </div>
      <h3 className="text-lg font-semibold mb-2">
        {filter === "completed"
          ? "아직 완료된 프로젝트가 없어요"
          : filter === "active"
          ? "진행 중인 프로젝트가 없어요"
          : "아직 프로젝트가 없어요"}
      </h3>
      <p className="text-muted-foreground mb-4">
        템플릿으로 첫 프로젝트를 시작해보세요!
      </p>
      <Link
        href="/prompty/templates"
        className="inline-block px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
      >
        템플릿 둘러보기
      </Link>
    </div>
  );
}

// =============================================================================
// Utilities
// =============================================================================

function calculateAvgScore(projects: PromptyProject[]): number | null {
  const scored = projects.filter((p) => p.avg_score !== null && p.avg_score !== undefined);
  if (scored.length === 0) return null;
  const sum = scored.reduce((acc, p) => acc + (p.avg_score ?? 0), 0);
  return sum / scored.length;
}

function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "방금";
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString("ko-KR", { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export default PromptyDashboard;
