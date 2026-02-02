"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, PromptyCommunityProject } from "@/lib/api";
import { ProjectCard } from "@/components/prompty/ProjectCard";
import { ForkModal } from "@/components/prompty/ForkModal";

type SortOrder = "recent" | "top-scores" | "most-forked";
type StatusFilter = "all" | "active" | "completed";

export default function CommunityPage() {
  const [projects, setProjects] = useState<PromptyCommunityProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState<SortOrder>("recent");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Fork modal state
  const [forkModalOpen, setForkModalOpen] = useState(false);
  const [forkTarget, setForkTarget] = useState<PromptyCommunityProject | null>(null);

  useEffect(() => {
    loadProjects();
  }, [sort, statusFilter, page]);

  async function loadProjects() {
    try {
      setLoading(true);
      const response = await api.listCommunityProjects(page, pageSize, {
        sort,
        status: statusFilter === "all" ? undefined : statusFilter,
      });
      setProjects(response.items);
      setTotal(response.total);
    } catch (error) {
      console.error("Failed to load community projects:", error);
    } finally {
      setLoading(false);
    }
  }

  function handleForkClick(projectId: string) {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      setForkTarget(project);
      setForkModalOpen(true);
    }
  }

  async function handleForkConfirm(name: string) {
    if (!forkTarget) return;

    try {
      const newProject = await api.forkProject(forkTarget.id, name);
      setForkModalOpen(false);
      setForkTarget(null);
      // Redirect to new project
      window.location.href = `/projects/${newProject.id}`;
    } catch (error) {
      console.error("Failed to fork project:", error);
      alert("Fork에 실패했습니다. 다시 시도해주세요.");
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Community</h1>
            <p className="text-muted-foreground mt-1">
              다른 학습자들의 프로젝트를 둘러보고 영감을 얻어보세요
            </p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition"
          >
            내 프로젝트로
          </Link>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Sort */}
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value as SortOrder);
              setPage(1);
            }}
            className="px-3 py-2 border border-border rounded-lg text-sm bg-background"
          >
            <option value="recent">최신순</option>
            <option value="top-scores">점수순</option>
            <option value="most-forked">Fork순</option>
          </select>

          {/* Status filter */}
          <div className="flex border border-border rounded-lg overflow-hidden">
            {(["all", "completed", "active"] as const).map((status) => (
              <button
                key={status}
                onClick={() => {
                  setStatusFilter(status);
                  setPage(1);
                }}
                className={`px-4 py-2 text-sm transition ${
                  statusFilter === status
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent"
                }`}
              >
                {status === "all" ? "전체" : status === "completed" ? "완료" : "진행중"}
              </button>
            ))}
          </div>

          {/* Results count */}
          <span className="text-sm text-muted-foreground ml-auto">
            총 {total}개 프로젝트
          </span>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-72 bg-muted rounded-xl animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 rounded-xl border border-dashed border-border">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold mb-2">
            아직 공개된 프로젝트가 없어요
          </h3>
          <p className="text-muted-foreground mb-4">
            첫 번째로 프로젝트를 공개해보세요!
          </p>
          <Link
            href="/"
            className="inline-block px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
          >
            내 프로젝트로 이동
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                showUser
                showForkButton
                onFork={handleForkClick}
                linkPrefix="/community"
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border border-border rounded-lg disabled:opacity-50 hover:bg-accent transition"
              >
                이전
              </button>
              <span className="px-4 py-2">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 border border-border rounded-lg disabled:opacity-50 hover:bg-accent transition"
              >
                다음
              </button>
            </div>
          )}
        </>
      )}

      {/* Fork Modal */}
      {forkModalOpen && forkTarget && (
        <ForkModal
          project={forkTarget}
          onConfirm={handleForkConfirm}
          onCancel={() => {
            setForkModalOpen(false);
            setForkTarget(null);
          }}
        />
      )}
    </div>
  );
}
