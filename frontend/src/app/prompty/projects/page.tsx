"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, PromptyProject } from "@/lib/api";
import { useSessionContext } from "@/contexts/SessionContext";
import { useToast } from "@/components/Toast";
import { localProjectsService, LocalProject } from "@/lib/local-projects";
import { syncLocalProjectsToServer } from "@/lib/local-projects-sync";

export default function ProjectsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: sessionLoading } = useSessionContext();
  const toast = useToast();

  const [projects, setProjects] = useState<PromptyProject[]>([]);
  const [localProjects, setLocalProjects] = useState<LocalProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [storageAvailable, setStorageAvailable] = useState(true);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<PromptyProject | LocalProject | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Check localStorage availability
  useEffect(() => {
    setStorageAvailable(localProjectsService.isAvailable());
  }, []);

  // Subscribe to cross-tab changes for local projects
  useEffect(() => {
    if (!isAuthenticated) {
      return localProjectsService.onStorageChange(() => {
        setLocalProjects(localProjectsService.getAll());
      });
    }
  }, [isAuthenticated]);

  // Load projects based on auth state
  useEffect(() => {
    if (sessionLoading) return;
    loadProjects();
  }, [isAuthenticated, sessionLoading]);

  async function loadProjects() {
    setLoading(true);
    try {
      if (isAuthenticated) {
        // Load from server
        const response = await api.listPromptyProjects(1, 50);
        setProjects(response.items);

        // Sync local projects if any
        const unsynced = localProjectsService.getUnsynced();
        if (unsynced.length > 0) {
          setSyncing(true);
          const result = await syncLocalProjectsToServer();
          setSyncing(false);

          if (result.synced > 0) {
            toast.success(`${result.synced}개 로컬 프로젝트가 동기화되었습니다`);
            // Reload server projects
            const updated = await api.listPromptyProjects(1, 50);
            setProjects(updated.items);
          }
          if (result.failed > 0) {
            toast.warning(`${result.failed}개 프로젝트 동기화 실패`);
          }
        }
      } else {
        // Load from localStorage
        setLocalProjects(localProjectsService.getAll());
      }
    } catch (error) {
      console.error("Failed to load projects:", error);
      toast.error("프로젝트 로드 실패");
    } finally {
      setLoading(false);
    }
  }

  async function createNewProject() {
    const name = `새 프로젝트 ${new Date().toLocaleDateString("ko-KR")}`;

    setCreating(true);
    try {
      if (isAuthenticated) {
        const project = await api.createPromptyProject({ name });
        router.push(`/prompty/projects/${project.id}`);
      } else {
        if (!storageAvailable) {
          toast.error("시크릿 모드에서는 프로젝트를 저장할 수 없습니다");
          setCreating(false);
          return;
        }
        const local = localProjectsService.create({ name });
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

  function openDeleteModal(
    project: PromptyProject | LocalProject,
    e: React.MouseEvent
  ) {
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
      // Check if it's a local project
      const isLocal = "local_id" in projectToDelete;

      if (isLocal) {
        const success = localProjectsService.delete(projectToDelete.local_id);
        if (success) {
          setLocalProjects((prev) =>
            prev.filter((p) => p.local_id !== projectToDelete.local_id)
          );
        }
      } else {
        await api.deletePromptyProject(projectToDelete.id);
        setProjects((prev) => prev.filter((p) => p.id !== projectToDelete.id));
      }
      closeDeleteModal();
    } catch (error) {
      console.error("Failed to delete project:", error);
      toast.error("프로젝트 삭제 실패");
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

  // Determine which projects to show based on auth state
  const displayProjects = isAuthenticated ? projects : [];
  const displayLocalProjects = isAuthenticated ? [] : localProjects;
  const hasProjects =
    displayProjects.length > 0 || displayLocalProjects.length > 0;

  // Render project card (works for both server and local projects)
  function renderProjectCard(
    project: PromptyProject | LocalProject,
    isLocal: boolean
  ) {
    const id = isLocal
      ? `local:${(project as LocalProject).local_id}`
      : (project as PromptyProject).id;

    return (
      <Link
        key={id}
        href={`/prompty/projects/${id}`}
        className="group block rounded-xl border border-border bg-card p-6 hover:border-primary/50 transition relative"
      >
        {/* Local Badge */}
        {isLocal && (
          <span className="absolute top-3 left-3 px-2 py-0.5 text-xs bg-yellow-500/10 text-yellow-600 rounded">
            로컬
          </span>
        )}

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

        <div className={`flex items-start justify-between mb-4 ${isLocal ? "pt-4" : ""} pr-8`}>
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
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">내 프로젝트</h1>
          <p className="text-muted-foreground mt-1">
            {isAuthenticated
              ? "진행 중인 워크플로우 프로젝트"
              : "로그인하면 모든 기기에서 동기화됩니다"}
          </p>
        </div>
        <div className="flex gap-3">
          {syncing && (
            <span className="px-4 py-2 text-sm text-muted-foreground">
              동기화 중...
            </span>
          )}
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

      {/* Storage Warning for Incognito */}
      {!isAuthenticated && !storageAvailable && (
        <div className="mb-6 p-4 rounded-xl border border-yellow-500/30 bg-yellow-500/10">
          <p className="text-sm text-yellow-600">
            시크릿/비공개 모드에서는 프로젝트가 저장되지 않습니다. 일반 모드를
            사용하거나 로그인하세요.
          </p>
        </div>
      )}

      {/* Projects Grid */}
      {loading || sessionLoading ? (
        <div className="grid md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : !hasProjects ? (
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
          {/* Server Projects */}
          {displayProjects.map((project) => renderProjectCard(project, false))}
          {/* Local Projects */}
          {displayLocalProjects.map((project) =>
            renderProjectCard(project, true)
          )}
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
