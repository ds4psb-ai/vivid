/**
 * Vitest Test Setup File
 * Phase -1: Technical Foundation
 *
 * This file runs before each test file and sets up:
 * - Jest-DOM matchers for Vitest
 * - Automatic cleanup after each test
 * - Browser API mocks (not provided by JSDOM)
 */

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

// Cleanup after each test to prevent test pollution
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock window.matchMedia (not implemented in JSDOM)
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver (not implemented in JSDOM)
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
window.ResizeObserver = ResizeObserverMock;

// Mock IntersectionObserver (not implemented in JSDOM)
class IntersectionObserverMock {
  root = null;
  rootMargin = "";
  thresholds = [];
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  takeRecords = vi.fn().mockReturnValue([]);
}
window.IntersectionObserver =
  IntersectionObserverMock as unknown as typeof IntersectionObserver;

// Mock scrollTo (not implemented in JSDOM)
Element.prototype.scrollTo = vi.fn();
window.scrollTo = vi.fn();

// Mock crypto.randomUUID (needed for some React patterns)
if (!window.crypto?.randomUUID) {
  Object.defineProperty(window, "crypto", {
    value: {
      randomUUID: () => "mock-uuid-" + Math.random().toString(36).slice(2),
      getRandomValues: (arr: Uint8Array) => {
        for (let i = 0; i < arr.length; i++) {
          arr[i] = Math.floor(Math.random() * 256);
        }
        return arr;
      },
    },
  });
}
