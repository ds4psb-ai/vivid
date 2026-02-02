"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, PromptyProject } from "@/lib/api";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<PromptyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<PromptyProject | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const response = await api.listPromptyProjects(1, 50);
      setProjects(response.items);
    } catch (error) {
      console.error("Failed to load projects:", error);
    } finally {
      setLoading(false);
    }
  }

  async function createNewProject() {
    setCreating(true);
    try {
      const project = await api.createPromptyProject({
        name: `새 프로젝트 ${new Date().toLocaleDateString("ko-KR")}`,
      });
      router.push(`/prompty/projects/${project.id}`);
    } catch (error) {
      console.error("Failed to create project:", error);
      setCreating(false);
    }
  }

  function openDeleteModal(project: PromptyProject, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setProjectToDelete(project);
    setDeleteModalOpen(true);
  }

  function closeDeleteModal() {
    setDeleteModalOpen(false);
    setProjectToDelete(null);
  }

  async function confirmDelete() {
    if (!projectToDelete) return;

    setDeleting(true);
    try {
      await api.deletePromptyProject(projectToDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== projectToDelete.id));
      closeDeleteModal();
    } catch (error) {
      console.error("Failed to delete project:", error);
    } finally {
      setDeleting(false);
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "completed":
        return "bg-green-500/10 text-green-500";
      case "active":
        return "bg-blue-500/10 text-blue-500";
      case "paused":
        return "bg-yellow-500/10 text-yellow-500";
      default:
        return "bg-gray-500/10 text-gray-500";
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case "completed":
        return "완료";
      case "active":
        return "진행중";
      case "paused":
        return "일시정지";
      case "archived":
        return "보관됨";
      default:
        return status;
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">내 프로젝트</h1>
          <p className="text-muted-foreground mt-1">진행 중인 워크플로우 프로젝트</p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/prompty/templates"
            className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition"
          >
            템플릿에서 시작
          </Link>
          <button
            onClick={createNewProject}
            disabled={creating}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
          >
            {creating ? "생성 중..." : "+ 새 프로젝트"}
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="grid md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">📂</div>
          <h2 className="text-xl font-semibold mb-2">아직 프로젝트가 없습니다</h2>
          <p className="text-muted-foreground mb-6">
            템플릿을 선택하거나 새 프로젝트를 시작하세요
          </p>
          <div className="flex gap-3 justify-center">
            <Link
              href="/prompty/templates"
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
            >
              템플릿 둘러보기
            </Link>
            <button
              onClick={createNewProject}
              disabled={creating}
              className="px-6 py-3 border border-border rounded-lg font-medium hover:bg-accent transition"
            >
              빈 프로젝트 시작
            </button>
          </div>
        </div>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/prompty/projects/${project.id}`}
              className="group block rounded-xl border border-border bg-card p-6 hover:border-primary/50 transition relative"
            >
              {/* Delete Button */}
              <button
                onClick={(e) => openDeleteModal(project, e)}
                className="absolute top-3 right-3 p-1.5 rounded-md text-muted-foreground hover:text-red-500 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition"
                title="프로젝트 삭제"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M3 6h18" />
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  <line x1="10" y1="11" x2="10" y2="17" />
                  <line x1="14" y1="11" x2="14" y2="17" />
                </svg>
              </button>

              <div className="flex items-start justify-between mb-4 pr-8">
                <h3 className="font-semibold group-hover:text-primary transition line-clamp-1">
                  {project.name}
                </h3>
                <span
                  className={`px-2 py-1 text-xs rounded ${getStatusColor(project.status)}`}
                >
                  {getStatusLabel(project.status)}
                </span>
              </div>

              {project.description && (
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {project.description}
                </p>
              )}

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>{project.current_stage}</span>
                  <span>{project.progress_percent}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${project.progress_percent}%` }}
                  />
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                {new Date(project.updated_at).toLocaleDateString("ko-KR")} 수정됨
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && projectToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-xl border border-border p-6 max-w-md w-full mx-4 shadow-lg">
            <h3 className="text-lg font-semibold mb-2">프로젝트 삭제</h3>
            <p className="text-muted-foreground mb-4">
              <span className="font-medium text-foreground">{projectToDelete.name}</span>
              을(를) 정말 삭제하시겠습니까?
              <br />
              <span className="text-sm text-red-500">이 작업은 되돌릴 수 없습니다.</span>
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={closeDeleteModal}
                disabled={deleting}
                className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition disabled:opacity-50"
              >
                취소
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition disabled:opacity-50"
              >
                {deleting ? "삭제 중..." : "삭제"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
