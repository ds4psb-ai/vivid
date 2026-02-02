/**
 * Local Projects Service Tests
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { localProjectsService } from "./local-projects";
import { SCHEMA_VERSION } from "./schemas/local-project";

// Valid v4 UUIDs for testing (must follow RFC 4122: position 13 = 4, position 17 = 8/9/a/b)
const TEST_UUID_1 = "a1b2c3d4-e5f6-4789-abcd-ef0123456789";
const TEST_UUID_2 = "b2c3d4e5-f6a7-4890-bcde-f01234567890";
const TEMPLATE_UUID = "c3d4e5f6-a7b8-4901-8def-012345678901"; // Note: 8 at position 17
const SERVER_UUID = "d4e5f6a7-b8c9-4012-9ef0-123456789012"; // Note: 9 at position 17

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get store() {
      return store;
    },
  };
})();

// Mock crypto.randomUUID
vi.stubGlobal("crypto", {
  randomUUID: () => TEST_UUID_1,
});

describe("localProjectsService", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", localStorageMock);
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.stubGlobal("crypto", {
      randomUUID: () => TEST_UUID_1,
    });
  });

  describe("isAvailable", () => {
    it("returns true when localStorage works", () => {
      expect(localProjectsService.isAvailable()).toBe(true);
    });

    it("returns false when localStorage throws", () => {
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error("QuotaExceeded");
      });
      expect(localProjectsService.isAvailable()).toBe(false);
    });
  });

  describe("getAll", () => {
    it("returns empty array when no data", () => {
      expect(localProjectsService.getAll()).toEqual([]);
    });

    it("returns projects from localStorage", () => {
      const data = {
        version: SCHEMA_VERSION,
        projects: [
          {
            local_id: TEST_UUID_1,
            name: "Test Project",
            state: {},
            current_stage: "analysis",
            current_step: "step1",
            progress_percent: 0,
            status: "active",
            created_at: "2024-01-01T00:00:00.000Z",
            updated_at: "2024-01-01T00:00:00.000Z",
            synced: false,
          },
        ],
      };
      localStorageMock.store["prompty_local_projects"] = JSON.stringify(data);

      const projects = localProjectsService.getAll();
      expect(projects).toHaveLength(1);
      expect(projects[0].name).toBe("Test Project");
    });

    it("returns empty array for invalid JSON", () => {
      localStorageMock.store["prompty_local_projects"] = "invalid json";
      expect(localProjectsService.getAll()).toEqual([]);
    });

    it("returns empty array for invalid schema", () => {
      localStorageMock.store["prompty_local_projects"] = JSON.stringify({
        invalid: "data",
      });
      expect(localProjectsService.getAll()).toEqual([]);
    });
  });

  describe("create", () => {
    it("creates a new project with defaults", () => {
      const project = localProjectsService.create({ name: "New Project" });

      expect(project).not.toBeNull();
      expect(project?.name).toBe("New Project");
      expect(project?.current_stage).toBe("analysis");
      expect(project?.current_step).toBe("step1");
      expect(project?.progress_percent).toBe(0);
      expect(project?.status).toBe("active");
      expect(project?.synced).toBe(false);
    });

    it("creates project with template_id", () => {
      const project = localProjectsService.create({
        name: "Template Project",
        template_id: TEMPLATE_UUID,
      });

      expect(project?.template_id).toBe(TEMPLATE_UUID);
    });

    it("persists to localStorage", () => {
      localProjectsService.create({ name: "Persisted Project" });

      expect(localStorageMock.setItem).toHaveBeenCalled();
      const savedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1]);
      expect(savedData.projects).toHaveLength(1);
      expect(savedData.version).toBe(SCHEMA_VERSION);
    });
  });

  describe("getById", () => {
    beforeEach(() => {
      const data = {
        version: SCHEMA_VERSION,
        projects: [
          {
            local_id: TEST_UUID_1,
            name: "Find Me",
            state: {},
            current_stage: "analysis",
            current_step: "step1",
            progress_percent: 0,
            status: "active",
            created_at: "2024-01-01T00:00:00.000Z",
            updated_at: "2024-01-01T00:00:00.000Z",
            synced: false,
          },
        ],
      };
      localStorageMock.store["prompty_local_projects"] = JSON.stringify(data);
    });

    it("returns project when found", () => {
      const project = localProjectsService.getById(TEST_UUID_1);
      expect(project?.name).toBe("Find Me");
    });

    it("returns null when not found", () => {
      const project = localProjectsService.getById("nonexistent");
      expect(project).toBeNull();
    });
  });

  describe("update", () => {
    beforeEach(() => {
      const data = {
        version: SCHEMA_VERSION,
        projects: [
          {
            local_id: TEST_UUID_1,
            name: "Original Name",
            state: {},
            current_stage: "analysis",
            current_step: "step1",
            progress_percent: 0,
            status: "active",
            created_at: "2024-01-01T00:00:00.000Z",
            updated_at: "2024-01-01T00:00:00.000Z",
            synced: false,
          },
        ],
      };
      localStorageMock.store["prompty_local_projects"] = JSON.stringify(data);
    });

    it("updates project fields", () => {
      const updated = localProjectsService.update(TEST_UUID_1, {
        name: "Updated Name",
        progress_percent: 50,
      });

      expect(updated?.name).toBe("Updated Name");
      expect(updated?.progress_percent).toBe(50);
    });

    it("updates updated_at timestamp", () => {
      const before = new Date().toISOString();
      const updated = localProjectsService.update(TEST_UUID_1, {
        name: "New Name",
      });
      const after = new Date().toISOString();

      expect(updated?.updated_at).toBeDefined();
      expect(updated!.updated_at >= before).toBe(true);
      expect(updated!.updated_at <= after).toBe(true);
    });

    it("returns null for nonexistent project", () => {
      const result = localProjectsService.update("nonexistent", {
        name: "Fail",
      });
      expect(result).toBeNull();
    });
  });

  describe("delete", () => {
    beforeEach(() => {
      const data = {
        version: SCHEMA_VERSION,
        projects: [
          {
            local_id: TEST_UUID_1,
            name: "Delete Me",
            state: {},
            current_stage: "analysis",
            current_step: "step1",
            progress_percent: 0,
            status: "active",
            created_at: "2024-01-01T00:00:00.000Z",
            updated_at: "2024-01-01T00:00:00.000Z",
            synced: false,
          },
        ],
      };
      localStorageMock.store["prompty_local_projects"] = JSON.stringify(data);
    });

    it("deletes existing project", () => {
      const result = localProjectsService.delete(TEST_UUID_1);
      expect(result).toBe(true);
    });

    it("returns false for nonexistent project", () => {
      const result = localProjectsService.delete("nonexistent");
      expect(result).toBe(false);
    });
  });

  describe("sync methods", () => {
    beforeEach(() => {
      const data = {
        version: SCHEMA_VERSION,
        projects: [
          {
            local_id: TEST_UUID_1,
            name: "Unsynced",
            state: {},
            current_stage: "analysis",
            current_step: "step1",
            progress_percent: 0,
            status: "active",
            created_at: "2024-01-01T00:00:00.000Z",
            updated_at: "2024-01-01T00:00:00.000Z",
            synced: false,
          },
          {
            local_id: TEST_UUID_2,
            name: "Synced",
            state: {},
            current_stage: "analysis",
            current_step: "step1",
            progress_percent: 0,
            status: "active",
            created_at: "2024-01-01T00:00:00.000Z",
            updated_at: "2024-01-01T00:00:00.000Z",
            synced: true,
            server_id: SERVER_UUID,
          },
        ],
      };
      localStorageMock.store["prompty_local_projects"] = JSON.stringify(data);
    });

    it("getUnsynced returns only unsynced projects", () => {
      const unsynced = localProjectsService.getUnsynced();
      expect(unsynced).toHaveLength(1);
      expect(unsynced[0].name).toBe("Unsynced");
    });

    it("markSynced updates sync status", () => {
      localProjectsService.markSynced(TEST_UUID_1, SERVER_UUID);

      expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it("clearSynced removes synced projects", () => {
      localProjectsService.clearSynced();

      expect(localStorageMock.setItem).toHaveBeenCalled();
      const savedData = JSON.parse(
        localStorageMock.setItem.mock.calls[0][1]
      );
      // Only unsynced project should remain
      expect(savedData.projects).toHaveLength(1);
      expect(savedData.projects[0].synced).toBe(false);
    });
  });
});
