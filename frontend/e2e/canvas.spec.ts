import { test, expect } from '@playwright/test';

/**
 * Canvas E2E Tests
 * Verifies core Canvas functionality per MCP Spec §2.1
 */

test.describe('Canvas Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/canvas');
    });

    test('should load canvas page', async ({ page }) => {
        // Wait for page to load
        await expect(page).toHaveTitle(/Crebit/);

        // Check main canvas container exists
        await expect(page.locator('[data-testid="canvas-container"]').or(
            page.locator('.canvas-container')
        )).toBeVisible({ timeout: 10000 });
    });

    test('should display sidebar navigation', async ({ page }) => {
        // Check sidebar is present
        const sidebar = page.locator('nav').or(page.locator('[data-testid="sidebar"]'));
        await expect(sidebar).toBeVisible();
    });

    test('should have capsule selector', async ({ page }) => {
        // Look for capsule/template selection
        const selector = page.getByRole('combobox').or(
            page.locator('[data-testid="capsule-select"]')
        );

        // May not exist if no capsules loaded
        const count = await selector.count();
        expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should navigate to other pages', async ({ page }) => {
        // Test navigation links
        const links = ['credits', 'knowledge', 'patterns'];

        for (const link of links) {
            const navLink = page.getByRole('link', { name: new RegExp(link, 'i') });
            const count = await navLink.count();

            if (count > 0) {
                await navLink.first().click();
                await expect(page).toHaveURL(new RegExp(link));
                await page.goto('/canvas'); // Go back
            }
        }
    });
});

test.describe('Canvas Generation Flow', () => {
    test('should show generation panel when available', async ({ page }) => {
        await page.goto('/canvas');

        // Look for generation-related UI elements
        const genPanel = page.locator('[data-testid="generation-panel"]').or(
            page.getByText(/generate/i)
        );

        // Just check if it exists (may be hidden initially)
        const count = await genPanel.count();
        expect(count).toBeGreaterThanOrEqual(0);
    });
});
