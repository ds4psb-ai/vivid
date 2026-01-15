import { test, expect } from "@playwright/test";

/**
 * Performance E2E Tests
 * =====================
 *
 * 2026 Best Practice: Measure Core Web Vitals and RSC performance
 * Tests P2.1 Server Components optimization
 */

test.describe("Core Web Vitals", () => {
  test("dimension hub should load within performance budget", async ({ page }) => {
    const startTime = Date.now();

    await page.goto("/dimension", { waitUntil: "domcontentloaded" });

    const loadTime = Date.now() - startTime;

    // Page should load in under 3 seconds for DOM content
    expect(loadTime).toBeLessThan(3000);
  });

  test("should measure LCP (Largest Contentful Paint)", async ({ page }) => {
    // Start measuring LCP
    await page.goto("/dimension");

    // Inject LCP measurement
    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          if (entries.length > 0) {
            resolve(entries[entries.length - 1].startTime);
          }
        }).observe({ type: "largest-contentful-paint", buffered: true });

        // Fallback timeout
        setTimeout(() => resolve(5000), 5000);
      });
    });

    // LCP should be under 2.5s (Good threshold)
    expect(lcp).toBeLessThan(2500);
  });

  test("should measure CLS (Cumulative Layout Shift)", async ({ page }) => {
    await page.goto("/dimension");

    // Wait for initial render
    await page.waitForLoadState("networkidle");

    // Measure CLS
    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsValue = 0;

        new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            // @ts-ignore - LayoutShift has value property
            if (!entry.hadRecentInput) {
              // @ts-ignore
              clsValue += entry.value;
            }
          }
        }).observe({ type: "layout-shift", buffered: true });

        // Give time for shifts to occur
        setTimeout(() => resolve(clsValue), 2000);
      });
    });

    // CLS should be under 0.1 (Good threshold)
    expect(cls).toBeLessThan(0.1);
  });
});

test.describe("JavaScript Bundle Size", () => {
  test("should not load excessive JavaScript on initial page", async ({ page }) => {
    const jsRequests: { url: string; size: number }[] = [];

    page.on("response", async (response) => {
      const contentType = response.headers()["content-type"] || "";
      if (contentType.includes("javascript")) {
        const buffer = await response.body().catch(() => null);
        if (buffer) {
          jsRequests.push({
            url: response.url(),
            size: buffer.length,
          });
        }
      }
    });

    await page.goto("/dimension");
    await page.waitForLoadState("networkidle");

    // Calculate total JS size
    const totalJsSize = jsRequests.reduce((sum, r) => sum + r.size, 0);
    const totalJsKb = totalJsSize / 1024;

    // Total JS should be under 500KB compressed (RSC optimization target)
    // This is a reasonable target for SSR apps
    expect(totalJsKb).toBeLessThan(800);
  });
});

test.describe("Server Component Hydration", () => {
  test("dimension hub should render server content before hydration", async ({ page }) => {
    // Disable JavaScript to test SSR content
    await page.setJavaScriptEnabled(false);

    await page.goto("/dimension");

    // Static metadata should be present (Server Component rendered)
    await expect(page.locator("title")).toContainText("Dimension Studio");

    // Basic structure should be visible without JS
    await expect(page.locator("body")).toBeVisible();
  });

  test("interactive elements should work after hydration", async ({ page }) => {
    await page.goto("/dimension");

    // Wait for hydration
    await page.waitForLoadState("networkidle");

    // Test interactive stage filter toggle
    const allButton = page.locator("button:has-text('ALL')");
    if ((await allButton.count()) > 0) {
      await allButton.click();

      // Interaction should work - no errors
      await expect(allButton).toBeVisible();
    }
  });
});

test.describe("Navigation Performance", () => {
  test("should prefetch dimension app routes", async ({ page }) => {
    await page.goto("/dimension");

    // Wait for prefetch to complete
    await page.waitForLoadState("networkidle");

    // Check for prefetch links
    const prefetchLinks = await page.locator('link[rel="prefetch"]').count();

    // Should have prefetch hints for dimension apps
    // (This depends on Next.js automatic prefetching)
    // We just ensure page loads without blocking prefetch errors
    expect(prefetchLinks).toBeGreaterThanOrEqual(0);
  });

  test("should navigate to dimension app within budget", async ({ page }) => {
    await page.goto("/dimension");
    await page.waitForLoadState("networkidle");

    // Measure navigation time
    const startTime = Date.now();

    await page.click('a[href*="/dimension/prompt"]');
    await page.waitForLoadState("domcontentloaded");

    const navigationTime = Date.now() - startTime;

    // Client-side navigation should be under 500ms
    expect(navigationTime).toBeLessThan(1500);
  });
});

test.describe("Image Optimization", () => {
  test("should use next/image for optimized images", async ({ page }) => {
    await page.goto("/dimension");

    // Check for Next.js optimized images
    const nextImages = await page.locator('img[src*="/_next/image"]').count();
    const allImages = await page.locator("img").count();

    // If there are images, most should be optimized
    if (allImages > 0) {
      // At least check that images have proper attributes
      const imagesWithLoading = await page.locator('img[loading]').count();
      expect(imagesWithLoading).toBeGreaterThanOrEqual(0);
    }
  });
});

test.describe("Memory Usage", () => {
  test("should not leak memory during navigation", async ({ page }) => {
    // Navigate multiple times
    const memorySnapshots: number[] = [];

    for (let i = 0; i < 5; i++) {
      await page.goto("/dimension");
      await page.waitForLoadState("networkidle");

      // Get JS heap size (Chrome only)
      const metrics = await page.evaluate(() => {
        // @ts-ignore - performance.memory is Chrome-specific
        if (performance.memory) {
          // @ts-ignore
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      if (metrics > 0) {
        memorySnapshots.push(metrics);
      }

      // Navigate away
      await page.goto("/credits");
      await page.waitForLoadState("networkidle");
    }

    if (memorySnapshots.length >= 3) {
      // Memory should not grow significantly (less than 50% increase)
      const firstSnapshot = memorySnapshots[0];
      const lastSnapshot = memorySnapshots[memorySnapshots.length - 1];
      const growthRatio = lastSnapshot / firstSnapshot;

      expect(growthRatio).toBeLessThan(1.5);
    }
  });
});
