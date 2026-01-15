import { test, expect, type Response } from "@playwright/test";

/**
 * Security E2E Tests
 * ==================
 *
 * 2026 Best Practice: Test security headers and CSP compliance
 * Verifies P1.3 Security Hardening implementation
 */

test.describe("Security Headers", () => {
  let response: Response | null;

  test.beforeEach(async ({ page }) => {
    response = await page.goto("/");
  });

  test("should include HSTS header", async () => {
    expect(response).not.toBeNull();
    const hsts = response!.headers()["strict-transport-security"];
    expect(hsts).toContain("max-age=31536000");
    expect(hsts).toContain("includeSubDomains");
  });

  test("should include X-Frame-Options header", async () => {
    expect(response).not.toBeNull();
    const xfo = response!.headers()["x-frame-options"];
    expect(xfo).toBe("DENY");
  });

  test("should include X-Content-Type-Options header", async () => {
    expect(response).not.toBeNull();
    const xcto = response!.headers()["x-content-type-options"];
    expect(xcto).toBe("nosniff");
  });

  test("should include Referrer-Policy header", async () => {
    expect(response).not.toBeNull();
    const rp = response!.headers()["referrer-policy"];
    expect(rp).toBe("strict-origin-when-cross-origin");
  });

  test("should include Content-Security-Policy header", async () => {
    expect(response).not.toBeNull();
    const csp = response!.headers()["content-security-policy"];
    expect(csp).toBeTruthy();
    expect(csp).toContain("default-src");
    expect(csp).toContain("frame-ancestors 'none'");
  });

  test("should include Permissions-Policy header", async () => {
    expect(response).not.toBeNull();
    const pp = response!.headers()["permissions-policy"];
    expect(pp).toContain("camera=()");
    expect(pp).toContain("microphone=()");
    expect(pp).toContain("geolocation=()");
  });
});

test.describe("XSS Protection", () => {
  test("should escape user input in URL parameters", async ({ page }) => {
    // Try to inject script via URL parameter
    await page.goto('/dimension?test=<script>alert("xss")</script>');

    // Page should load without script execution
    await expect(page.locator("body")).toBeVisible();

    // The script tag should not exist in DOM as executable
    const scriptCount = await page.locator('script:text("xss")').count();
    expect(scriptCount).toBe(0);
  });

  test("should not have inline onclick handlers", async ({ page }) => {
    await page.goto("/dimension");

    // Check for inline onclick handlers (bad practice)
    const inlineHandlers = await page.locator("[onclick]").count();
    expect(inlineHandlers).toBe(0);
  });
});

test.describe("Cookie Security", () => {
  test("should use secure cookie flags", async ({ page, context }) => {
    await page.goto("/");

    // Check cookies (if any are set)
    const cookies = await context.cookies();

    for (const cookie of cookies) {
      // In production, cookies should be secure
      if (process.env.CI) {
        expect(cookie.secure || cookie.httpOnly).toBeTruthy();
      }

      // SameSite should be set
      if (cookie.sameSite) {
        expect(["Strict", "Lax", "None"]).toContain(cookie.sameSite);
      }
    }
  });
});

test.describe("Mixed Content", () => {
  test("should not load insecure resources", async ({ page }) => {
    const insecureRequests: string[] = [];

    // Listen for network requests
    page.on("request", (request) => {
      if (request.url().startsWith("http://") && !request.url().includes("localhost")) {
        insecureRequests.push(request.url());
      }
    });

    await page.goto("/dimension");
    await page.waitForLoadState("networkidle");

    // No external HTTP requests
    expect(insecureRequests).toHaveLength(0);
  });
});

test.describe("Error Handling", () => {
  test("should not expose stack traces on 404", async ({ page }) => {
    const response = await page.goto("/nonexistent-page-12345");

    // Should get 404 response
    expect(response?.status()).toBe(404);

    // Page content should not contain stack traces
    const content = await page.content();
    expect(content).not.toContain("at ");
    expect(content).not.toContain("Error:");
    expect(content).not.toContain("node_modules");
  });

  test("should handle malformed URLs gracefully", async ({ page }) => {
    // Test with various malformed URLs
    const malformedUrls = [
      "/dimension/%00",
      "/dimension/..%2F..%2F",
      "/dimension/<>",
    ];

    for (const url of malformedUrls) {
      const response = await page.goto(url);
      // Should not return 500 (server error)
      expect(response?.status()).toBeLessThan(500);
    }
  });
});
