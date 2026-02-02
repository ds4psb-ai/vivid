/**
 * Local Projects Service - localStorage CRUD with Zod validation
 *
 * Features:
 * - SSR-safe localStorage access
 * - Zod schema validation
 * - BroadcastChannel for cross-tab sync
 * - QuotaExceeded handling
 * - Schema versioning for migrations
 */
import {
  LocalProjectSchema,
  LocalStorageSchema,
  LocalProject,
  LocalStorageData,
  SCHEMA_VERSION,
} from "./schemas/local-project";

const STORAGE_KEY = "prompty_local_projects";
const SYNC_CHANNEL = "prompty-local-projects-sync";

// BroadcastChannel for cross-tab sync
let syncChannel: BroadcastChannel | null = null;

function getSyncChannel(): BroadcastChannel | null {
  if (typeof window === "undefined") return null;
  if (!("BroadcastChannel" in window)) return null;
  if (!syncChannel) {
    try {
      syncChannel = new BroadcastChannel(SYNC_CHANNEL);
    } catch {
      // BroadcastChannel not available (e.g., some Safari versions)
      return null;
    }
  }
  return syncChannel;
}

function broadcastChange(action: string, data?: unknown) {
  getSyncChannel()?.postMessage({ action, data, timestamp: Date.now() });
}

// SSR-safe localStorage read with Zod validation
function readStorage(): LocalStorageData {
  if (typeof window === "undefined") {
    return { version: SCHEMA_VERSION, projects: [] };
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: SCHEMA_VERSION, projects: [] };

    const parsed = JSON.parse(raw);
    const result = LocalStorageSchema.safeParse(parsed);

    if (!result.success) {
      console.warn("[LocalProjects] Invalid data, resetting:", result.error);
      return { version: SCHEMA_VERSION, projects: [] };
    }

    // Schema migration if needed
    if (result.data.version < SCHEMA_VERSION) {
      return migrateSchema(result.data);
    }

    return result.data;
  } catch (error) {
    console.error("[LocalProjects] Read error:", error);
    return { version: SCHEMA_VERSION, projects: [] };
  }
}

// SSR-safe localStorage write with quota handling
function writeStorage(data: LocalStorageData): boolean {
  if (typeof window === "undefined") return false;

  try {
    const json = JSON.stringify(data);
    localStorage.setItem(STORAGE_KEY, json);
    broadcastChange("storage_updated");
    return true;
  } catch (error) {
    if (error instanceof DOMException && error.name === "QuotaExceededError") {
      console.error("[LocalProjects] Storage quota exceeded");
      // Could trigger cleanup of old synced projects here
    }
    return false;
  }
}

function migrateSchema(data: LocalStorageData): LocalStorageData {
  // Future migrations go here
  // Example: if (data.version === 1) { migrate v1 -> v2 }
  return { ...data, version: SCHEMA_VERSION };
}

export const localProjectsService = {
  getAll(): LocalProject[] {
    return readStorage().projects;
  },

  getById(localId: string): LocalProject | null {
    return this.getAll().find((p) => p.local_id === localId) ?? null;
  },

  create(input: { name: string; template_id?: string }): LocalProject | null {
    const now = new Date().toISOString();
    const project: LocalProject = {
      local_id: crypto.randomUUID(),
      name: input.name,
      template_id: input.template_id,
      state: {},
      current_stage: "analysis",
      current_step: "step1",
      progress_percent: 0,
      status: "active",
      created_at: now,
      updated_at: now,
      synced: false,
    };

    // Validate before saving
    const validated = LocalProjectSchema.safeParse(project);
    if (!validated.success) {
      console.error("[LocalProjects] Validation failed:", validated.error);
      return null;
    }

    const storage = readStorage();
    storage.projects.push(validated.data);

    if (!writeStorage(storage)) return null;
    return validated.data;
  },

  update(
    localId: string,
    updates: Partial<LocalProject>
  ): LocalProject | null {
    const storage = readStorage();
    const index = storage.projects.findIndex((p) => p.local_id === localId);
    if (index === -1) return null;

    const updated = {
      ...storage.projects[index],
      ...updates,
      updated_at: new Date().toISOString(),
    };

    // Validate updated project
    const validated = LocalProjectSchema.safeParse(updated);
    if (!validated.success) {
      console.error(
        "[LocalProjects] Update validation failed:",
        validated.error
      );
      return null;
    }

    storage.projects[index] = validated.data;
    if (!writeStorage(storage)) return null;
    return validated.data;
  },

  delete(localId: string): boolean {
    const storage = readStorage();
    const filtered = storage.projects.filter((p) => p.local_id !== localId);
    if (filtered.length === storage.projects.length) return false;
    storage.projects = filtered;
    return writeStorage(storage);
  },

  getUnsynced(): LocalProject[] {
    return this.getAll().filter((p) => !p.synced);
  },

  markSynced(localId: string, serverId: string): void {
    this.update(localId, { synced: true, server_id: serverId });
  },

  clearSynced(): void {
    const storage = readStorage();
    storage.projects = storage.projects.filter((p) => !p.synced);
    writeStorage(storage);
  },

  // Subscribe to cross-tab changes
  onStorageChange(callback: () => void): () => void {
    const channel = getSyncChannel();
    if (!channel) return () => {};

    const handler = () => callback();
    channel.addEventListener("message", handler);
    return () => channel.removeEventListener("message", handler);
  },

  // Check if localStorage is available
  isAvailable(): boolean {
    if (typeof window === "undefined") return false;
    try {
      const test = "__storage_test__";
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  },
};

// Re-export types for convenience
export type { LocalProject, LocalStorageData };
