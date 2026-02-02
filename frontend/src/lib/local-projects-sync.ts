/**
 * Local Projects Sync Service - Sync localStorage projects to server
 *
 * Features:
 * - Exponential backoff retry
 * - Error categorization
 * - Sequential processing (rate limit safe)
 * - Automatic cleanup after sync
 */
import { api } from "./api";
import { localProjectsService, LocalProject } from "./local-projects";
import { isNetworkError } from "./errors";

export interface SyncResult {
  synced: number;
  failed: number;
  errors: Array<{
    name: string;
    error: string;
    category: "user" | "system" | "network";
  }>;
}

type ErrorCategory = "user" | "system" | "network";

// Categorize error for retry decisions
function categorizeError(error: unknown): ErrorCategory {
  if (isNetworkError(error)) {
    return "network";
  }

  // Check for HTTP status codes
  if (error && typeof error === "object") {
    const status = (error as { status?: number }).status;
    if (status) {
      if (status >= 400 && status < 500) return "user"; // 4xx: don't retry
      if (status >= 500) return "system"; // 5xx: retry
    }
  }

  // Default to system error (retry)
  return "system";
}

// Exponential backoff delay with jitter
function getRetryDelay(attempt: number): number {
  const base = 1000;
  const max = 10000;
  const delay = Math.min(base * Math.pow(2, attempt), max);
  // Add jitter (±25%)
  return delay * (0.75 + Math.random() * 0.5);
}

async function syncSingleProject(
  local: LocalProject,
  maxRetries: number = 3
): Promise<{ success: boolean; serverId?: string; error?: string }> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Create on server
      const serverProject = await api.createPromptyProject({
        name: local.name,
        description: local.description,
        template_id: local.template_id,
      });

      // Update state if exists
      if (Object.keys(local.state).length > 0) {
        await api.updatePromptyProjectState(serverProject.id, {
          state: local.state,
          current_stage: local.current_stage,
          current_step: local.current_step,
          progress_percent: local.progress_percent,
        });
      }

      return { success: true, serverId: serverProject.id };
    } catch (error) {
      const category = categorizeError(error);

      // Don't retry user errors (400, 403, etc.)
      if (category === "user") {
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      }

      // Retry network/system errors
      if (
        attempt < maxRetries &&
        (category === "network" || category === "system")
      ) {
        await new Promise((r) => setTimeout(r, getRetryDelay(attempt)));
        continue;
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  return { success: false, error: "Max retries exceeded" };
}

export async function syncLocalProjectsToServer(): Promise<SyncResult> {
  const unsynced = localProjectsService.getUnsynced();

  if (unsynced.length === 0) {
    return { synced: 0, failed: 0, errors: [] };
  }

  const result: SyncResult = { synced: 0, failed: 0, errors: [] };

  // Process sequentially to avoid rate limiting
  for (const local of unsynced) {
    const syncResult = await syncSingleProject(local);

    if (syncResult.success && syncResult.serverId) {
      localProjectsService.markSynced(local.local_id, syncResult.serverId);
      result.synced++;
    } else {
      result.failed++;
      result.errors.push({
        name: local.name,
        error: syncResult.error || "Unknown error",
        category: categorizeError(new Error(syncResult.error)),
      });
    }
  }

  // Clean up synced projects from localStorage
  if (result.synced > 0) {
    localProjectsService.clearSynced();
  }

  return result;
}
