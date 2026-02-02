"use client";

import Link from "next/link";
import { PromptyCommunityProject, PromptyProject } from "@/lib/api";

type ProjectLike = PromptyCommunityProject | PromptyProject;

interface ProjectCardProps {
  project: ProjectLike;
  showUser?: boolean;
  showForkButton?: boolean;
  onFork?: (projectId: string) => void;
  linkPrefix?: string;  // Default: /prompty/projects
}

/**
 * ProjectCard - Reusable project card for dashboard and community
 *
 * Shows:
 * - Thumbnail with before/after if available
 * - Project name and description
 * - Progress/score badges
 * - Fork count
 */
export function ProjectCard({
  project,
  showUser = false,
  showForkButton = false,
  onFork,
  linkPrefix = "/prompty/projects",
}: ProjectCardProps) {
  const isCompleted = project.status === "completed";
  const hasScore = project.avg_score !== null && project.avg_score !== undefined;
  const userName = "user_name" in project ? project.user_name : undefined;

  return (
    <div className="group rounded-xl border border-border bg-card overflow-hidden hover:border-primary/50 transition relative">
      {/* Thumbnail */}
      <Link href={`${linkPrefix}/${project.id}`} className="block">
        <div className="aspect-video bg-muted relative">
          {project.thumbnail_url ? (
            <img
              src={project.thumbnail_url}
              alt={project.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-4xl">{isCompleted ? "🎬" : "📝"}</span>
            </div>
          )}

          {/* Status badge */}
          <div className="absolute top-2 right-2 flex gap-1">
            {isCompleted ? (
              <span className="px-2 py-1 rounded text-xs bg-green-500/90 text-white">
                완료
              </span>
            ) : (
              <span className="px-2 py-1 rounded text-xs bg-orange-500/90 text-white">
                {project.progress_percent}%
              </span>
            )}
          </div>

          {/* Visibility badge (for non-private) */}
          {project.visibility !== "private" && (
            <span className="absolute top-2 left-2 px-2 py-1 rounded text-xs bg-blue-500/90 text-white">
              {project.visibility === "full" ? "공개" : "일부공개"}
            </span>
          )}

          {/* Score overlay for completed projects */}
          {hasScore && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
              <div className="flex items-center justify-between text-white">
                <span className="text-lg font-bold">
                  {project.avg_score!.toFixed(0)}점
                </span>
                {getScoreBadge(project.avg_score!)}
              </div>
            </div>
          )}
        </div>
      </Link>

      {/* Content */}
      <div className="p-4">
        <Link href={`${linkPrefix}/${project.id}`}>
          <h3 className="font-semibold mb-1 group-hover:text-primary transition line-clamp-1">
            {project.name}
          </h3>
        </Link>

        {project.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {project.description}
          </p>
        )}

        {/* Meta row */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            {showUser && userName && (
              <span className="font-medium">{userName}</span>
            )}
            {showUser && !userName && "user_id" in project && (
              <span className="font-medium">
                {maskUserId(project.user_id)}
              </span>
            )}
            <span>{formatRelativeTime(project.updated_at)}</span>
          </div>

          <div className="flex items-center gap-3">
            {project.fork_count > 0 && (
              <span className="flex items-center gap-1" title={`${project.fork_count}번 Fork됨`}>
                🍴 {project.fork_count}
              </span>
            )}
          </div>
        </div>

        {/* Fork button */}
        {showForkButton && onFork && (
          <button
            onClick={(e) => {
              e.preventDefault();
              onFork(project.id);
            }}
            className="mt-3 w-full py-2 border border-primary/30 text-primary rounded-lg text-sm hover:bg-primary/5 transition"
          >
            🍴 Fork
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Compact card variant for lists
 */
export function ProjectCardCompact({
  project,
  showUser = false,
  onClick,
}: {
  project: ProjectLike;
  showUser?: boolean;
  onClick?: () => void;
}) {
  const hasScore = project.avg_score !== null && project.avg_score !== undefined;
  const userName = "user_name" in project ? project.user_name : undefined;

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-4 p-3 rounded-lg border border-border hover:border-primary/50 cursor-pointer transition"
    >
      {/* Thumbnail */}
      <div className="w-16 h-16 rounded-lg bg-muted flex-shrink-0 overflow-hidden">
        {project.thumbnail_url ? (
          <img
            src={project.thumbnail_url}
            alt={project.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-2xl">
            {project.status === "completed" ? "🎬" : "📝"}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h4 className="font-medium truncate">{project.name}</h4>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
          {showUser && (userName || ("user_id" in project && project.user_id)) && (
            <span>{userName || maskUserId(("user_id" in project ? project.user_id : "") as string)}</span>
          )}
          <span>{formatRelativeTime(project.updated_at)}</span>
          {hasScore && (
            <span className="text-yellow-500 font-medium">
              {project.avg_score!.toFixed(0)}점
            </span>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="flex-shrink-0">
        {project.status === "completed" ? (
          <span className="px-2 py-1 rounded text-xs bg-green-500/10 text-green-500">
            완료
          </span>
        ) : (
          <span className="px-2 py-1 rounded text-xs bg-orange-500/10 text-orange-500">
            {project.progress_percent}%
          </span>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Utilities
// =============================================================================

function getScoreBadge(score: number) {
  if (score >= 85) {
    return (
      <span className="px-2 py-0.5 rounded bg-green-500/80 text-xs">
        PASS
      </span>
    );
  }
  if (score >= 60) {
    return (
      <span className="px-2 py-0.5 rounded bg-yellow-500/80 text-xs">
        REVISE
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded bg-red-500/80 text-xs">
      REJECT
    </span>
  );
}

function maskUserId(userId: string): string {
  if (!userId) return "";
  // Show first 3 chars + *** for privacy
  if (userId.length <= 3) return userId;
  return userId.slice(0, 3) + "***";
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

export default ProjectCard;
