import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Crebit E2E tests.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
    testDir: './e2e',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: 'html',

    use: {
        baseURL: 'http://localhost:3100',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },
        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },
        // Mobile viewports for responsive testing (2026 Best Practice)
        {
            name: 'mobile-chrome',
            use: { ...devices['Pixel 7'] },
        },
        {
            name: 'mobile-safari',
            use: { ...devices['iPhone 14'] },
        },
        // Tablet viewport
        {
            name: 'tablet',
            use: { ...devices['iPad Pro 11'] },
        },
    ],

    // Only start webServer in CI - in development, servers should be running externally
    ...(process.env.CI ? {
        webServer: {
            command: 'npm run dev',
            url: 'http://localhost:3100',
            reuseExistingServer: false,
            timeout: 120 * 1000,
        },
    } : {}),
});
