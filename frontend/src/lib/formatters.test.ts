/**
 * Phase -1: Formatter Utility Tests
 *
 * Unit tests for time, date, and number formatting utilities
 */
import { describe, test, expect } from "vitest";
import { formatTime, formatDateTime, formatNumber } from "./formatters";

describe("formatTime", () => {
  test("formats seconds to mm:ss", () => {
    expect(formatTime(0)).toBe("0:00");
    expect(formatTime(30)).toBe("0:30");
    expect(formatTime(60)).toBe("1:00");
    expect(formatTime(90)).toBe("1:30");
    expect(formatTime(125)).toBe("2:05");
    expect(formatTime(3661)).toBe("61:01");
  });

  test("handles decimal seconds", () => {
    expect(formatTime(30.5)).toBe("0:30");
    expect(formatTime(59.9)).toBe("0:59");
    expect(formatTime(60.1)).toBe("1:00");
  });
});

describe("formatDateTime", () => {
  test("returns null for null/undefined input", () => {
    expect(formatDateTime(null)).toBeNull();
    expect(formatDateTime(undefined)).toBeNull();
    expect(formatDateTime("")).toBeNull();
  });

  test("returns null for invalid date", () => {
    expect(formatDateTime("not-a-date")).toBeNull();
    expect(formatDateTime(NaN)).toBeNull();
  });

  test("formats valid date string", () => {
    const result = formatDateTime("2024-06-15T10:30:00Z");
    expect(result).not.toBeNull();
    expect(typeof result).toBe("string");
    expect(result!.length).toBeGreaterThan(0);
  });

  test("formats Date object", () => {
    const date = new Date("2024-06-15T10:30:00Z");
    const result = formatDateTime(date);
    expect(result).not.toBeNull();
    expect(typeof result).toBe("string");
  });

  test("formats timestamp number", () => {
    const timestamp = 1718443800000; // 2024-06-15T10:30:00Z
    const result = formatDateTime(timestamp);
    expect(result).not.toBeNull();
  });

  test("respects locale parameter", () => {
    const date = new Date("2024-06-15T10:30:00Z");
    const usResult = formatDateTime(date, "en-US");
    const koResult = formatDateTime(date, "ko-KR");
    // Both should return valid strings (may differ in format)
    expect(usResult).not.toBeNull();
    expect(koResult).not.toBeNull();
  });

  test("respects format options", () => {
    const date = new Date("2024-06-15");
    const result = formatDateTime(date, "en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    expect(result).toContain("2024");
    expect(result).toContain("June");
  });
});

describe("formatNumber", () => {
  test("formats valid numbers", () => {
    expect(formatNumber(1234)).toBe("1,234");
    expect(formatNumber(0)).toBe("0");
    expect(formatNumber(-100)).toBe("-100");
  });

  test("returns fallback for null/undefined", () => {
    expect(formatNumber(null)).toBe("-");
    expect(formatNumber(undefined)).toBe("-");
    expect(formatNumber(null, undefined, undefined, "N/A")).toBe("N/A");
  });

  test("returns fallback for non-finite numbers", () => {
    expect(formatNumber(Infinity)).toBe("-");
    expect(formatNumber(-Infinity)).toBe("-");
    expect(formatNumber(NaN)).toBe("-");
  });

  test("respects locale parameter", () => {
    // German uses . as thousands separator
    const result = formatNumber(1234567, "de-DE");
    expect(result).toContain("1");
    expect(result).toContain("234");
    expect(result).toContain("567");
  });

  test("respects number format options", () => {
    const result = formatNumber(1234.56, "en-US", {
      style: "currency",
      currency: "USD",
    });
    expect(result).toContain("$");
    expect(result).toContain("1,234.56");
  });

  test("handles decimal precision options", () => {
    const result = formatNumber(3.14159, "en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    expect(result).toBe("3.14");
  });

  test("handles percentage options", () => {
    const result = formatNumber(0.125, "en-US", {
      style: "percent",
    });
    expect(result).toBe("13%"); // 0.125 * 100 = 12.5, rounded to 13
  });
});
