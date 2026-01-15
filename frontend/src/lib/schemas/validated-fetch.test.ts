/**
 * Validated Fetch Tests
 *
 * Phase -1: F2 API Contract Implementation
 */
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { z } from "zod";
import {
  validatedFetch,
  validateRequest,
  formatZodError,
  getFirstError,
  getFieldErrors,
  parseWithDefaults,
} from "./validated-fetch";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Test schemas
const TestRequestSchema = z.object({
  name: z.string().min(1, "Name is required"),
  age: z.number().int().min(0, "Age must be positive"),
  email: z.string().email("Invalid email").optional(),
});

const TestResponseSchema = z.object({
  success: z.literal(true),
  data: z.object({
    id: z.string(),
    name: z.string(),
  }),
});

describe("validatedFetch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("validates request and returns success", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: { id: "123", name: "Test" },
        }),
    });

    const result = await validatedFetch(
      { name: "John", age: 25 },
      {
        url: "https://api.test.com/users",
        requestSchema: TestRequestSchema,
        responseSchema: TestResponseSchema,
      }
    );

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.data.name).toBe("Test");
    }

    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.test.com/users",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "John", age: 25 }),
      })
    );
  });

  test("returns validation error for invalid request", async () => {
    const result = await validatedFetch(
      { name: "", age: -5 },
      {
        url: "https://api.test.com/users",
        requestSchema: TestRequestSchema,
        responseSchema: TestResponseSchema,
      }
    );

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.validationErrors).toBeDefined();
      expect(result.error).toContain("required");
    }

    // Should not make fetch call
    expect(mockFetch).not.toHaveBeenCalled();
  });

  test("handles HTTP error response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "Bad request" }),
    });

    const result = await validatedFetch(
      { name: "John", age: 25 },
      {
        url: "https://api.test.com/users",
        requestSchema: TestRequestSchema,
        responseSchema: TestResponseSchema,
      }
    );

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBe("Bad request");
      expect(result.statusCode).toBe(400);
    }
  });

  test("handles network error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const result = await validatedFetch(
      { name: "John", age: 25 },
      {
        url: "https://api.test.com/users",
        requestSchema: TestRequestSchema,
        responseSchema: TestResponseSchema,
      }
    );

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBe("Network error");
    }
  });

  test("warns but continues on response validation failure", async () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: { wrongField: "value" }, // Missing required fields
        }),
    });

    const result = await validatedFetch(
      { name: "John", age: 25 },
      {
        url: "https://api.test.com/users",
        requestSchema: TestRequestSchema,
        responseSchema: TestResponseSchema,
      }
    );

    // Should still return success (backward compatibility)
    expect(result.success).toBe(true);
    expect(consoleSpy).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  test("skips response validation when flag is set", async () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ anything: "works" }),
    });

    const result = await validatedFetch(
      { name: "John", age: 25 },
      {
        url: "https://api.test.com/users",
        requestSchema: TestRequestSchema,
        responseSchema: TestResponseSchema,
        skipResponseValidation: true,
      }
    );

    expect(result.success).toBe(true);
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  test("applies defaults from schema", async () => {
    const SchemaWithDefaults = z.object({
      name: z.string(),
      role: z.string().default("user"),
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    await validatedFetch(
      { name: "John" },
      {
        url: "https://api.test.com/users",
        requestSchema: SchemaWithDefaults,
        responseSchema: z.object({ success: z.boolean() }),
      }
    );

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({ name: "John", role: "user" }),
      })
    );
  });
});

describe("validateRequest", () => {
  test("returns success with valid data", () => {
    const result = validateRequest({ name: "John", age: 25 }, TestRequestSchema);

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.name).toBe("John");
    }
  });

  test("returns error with invalid data", () => {
    const result = validateRequest({ name: "", age: -1 }, TestRequestSchema);

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.validationErrors).toBeDefined();
    }
  });
});

describe("formatZodError", () => {
  test("formats Zod error to tree structure", () => {
    const schema = z.object({
      name: z.string().min(1),
      age: z.number().min(0),
    });

    const result = schema.safeParse({ name: "", age: -1 });
    expect(result.success).toBe(false);

    if (!result.success) {
      const tree = formatZodError(result.error);
      // Zod v4 treeifyError returns { errors: [], properties: { field: { errors: [] } } }
      expect(tree.errors).toBeDefined();
      expect(Array.isArray(tree.errors)).toBe(true);
      expect(tree.properties).toBeDefined();
    }
  });
});

describe("getFirstError", () => {
  test("extracts first error message", () => {
    const tree = {
      errors: ["Root error"],
      properties: { name: { errors: ["Name error"] } },
    };

    expect(getFirstError(tree)).toBe("Root error");
  });

  test("returns nested error if no root error", () => {
    const tree = {
      errors: [],
      properties: { name: { errors: ["Name is required"] } },
    };

    expect(getFirstError(tree)).toBe("name: Name is required");
  });

  test("returns fallback if no errors", () => {
    const tree = { errors: [] };

    expect(getFirstError(tree)).toBe("Validation failed");
  });
});

describe("getFieldErrors", () => {
  test("extracts errors for specific field", () => {
    const tree = {
      errors: [],
      properties: {
        name: { errors: ["Name is required", "Name too short"] },
        age: { errors: ["Age must be positive"] },
      },
    };

    const nameErrors = getFieldErrors(tree, "name");
    expect(nameErrors).toEqual(["Name is required", "Name too short"]);

    const ageErrors = getFieldErrors(tree, "age");
    expect(ageErrors).toEqual(["Age must be positive"]);
  });

  test("returns empty array for non-existent field", () => {
    const tree = {
      errors: [],
      properties: {
        name: { errors: ["Error"] },
      },
    };

    expect(getFieldErrors(tree, "email")).toEqual([]);
  });
});

describe("parseWithDefaults", () => {
  test("returns data with defaults applied", () => {
    const schema = z.object({
      name: z.string(),
      role: z.string().default("user"),
    });

    const result = parseWithDefaults({ name: "John" }, schema);
    expect(result).toEqual({ name: "John", role: "user" });
  });

  test("returns undefined for invalid data", () => {
    const schema = z.object({
      name: z.string().min(1),
    });

    const result = parseWithDefaults({ name: "" }, schema);
    expect(result).toBeUndefined();
  });
});
