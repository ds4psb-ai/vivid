/**
 * Phase -1: Test Utilities
 *
 * Custom render function and test utilities for React Testing Library
 */
import React, { ReactElement } from "react";
import { render, RenderOptions, RenderResult } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// =============================================================================
// Types
// =============================================================================

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  initialState?: Record<string, unknown>;
}

interface CustomRenderResult extends RenderResult {
  user: ReturnType<typeof userEvent.setup>;
}

// =============================================================================
// Providers Wrapper
// =============================================================================

/**
 * AllProviders - Wraps components with all necessary context providers
 * Add your app's providers here (e.g., ThemeProvider, AuthProvider)
 */
function AllProviders({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

// =============================================================================
// Custom Render
// =============================================================================

/**
 * Custom render function that wraps component with all providers
 * and sets up userEvent
 *
 * @example
 * const { user, getByRole } = customRender(<MyComponent />);
 * await user.click(getByRole('button'));
 */
function customRender(
  ui: ReactElement,
  options?: CustomRenderOptions
): CustomRenderResult {
  const user = userEvent.setup();

  return {
    user,
    ...render(ui, {
      wrapper: AllProviders,
      ...options,
    }),
  };
}

// =============================================================================
// Mock Helpers
// =============================================================================

/**
 * Create a mock API response
 */
export function createMockResponse<T>(data: T, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  };
}

/**
 * Create a mock error response
 */
export function createMockErrorResponse(
  message: string,
  status = 500
) {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail: message }),
    text: () => Promise.resolve(JSON.stringify({ detail: message })),
  };
}

/**
 * Wait for async state updates
 */
export async function waitForStateUpdate() {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

/**
 * Create mock SSE event
 */
export function createMockSSEEvent(type: string, payload: unknown) {
  return {
    type,
    payload,
    timestamp: Date.now(),
  };
}

// =============================================================================
// Re-exports
// =============================================================================

export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";

// Export custom render as the default render
export { customRender as render };
