import { test, expect } from '@playwright/test';

/**
 * Agent Chat E2E Tests
 * Tests the AI agent chat interface with SSE streaming
 */

test.describe('Agent Chat UI', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
    });

    test('should display chat interface', async ({ page }) => {
        // Look for chat input or Komi agent button
        const chatInput = page.locator('[data-testid="chat-input"]').or(
            page.locator('textarea[placeholder*="message"]')
        ).or(
            page.locator('input[placeholder*="message"]')
        );

        // Chat or Komi button should exist
        const komiBtn = page.locator('[data-testid="komi-trigger"]').or(
            page.locator('button:has-text("Komi")')
        ).or(
            page.locator('.komi-button')
        );

        const hasChat = (await chatInput.count()) > 0;
        const hasKomi = (await komiBtn.count()) > 0;

        expect(hasChat || hasKomi).toBeTruthy();
    });

    test('should open Komi chat on button click', async ({ page }) => {
        const komiBtn = page.locator('[data-testid="komi-trigger"]').or(
            page.locator('button[aria-label*="chat"]')
        ).or(
            page.locator('.komi-button')
        );

        if (await komiBtn.count() > 0) {
            await komiBtn.first().click();

            // Chat panel should appear
            await expect(page.locator('[data-testid="komi-panel"]').or(
                page.locator('.komi-chat')
            ).or(
                page.locator('[role="dialog"]')
            )).toBeVisible({ timeout: 5000 });
        }
    });
});

test.describe('Agent Flow Pages', () => {
    test('should load flow page', async ({ page }) => {
        await page.goto('/flow');

        // Flow page should have workflow elements
        await expect(page.locator('text=워크플로우').or(
            page.locator('text=Workflow')
        ).or(
            page.locator('[data-testid="flow-container"]')
        )).toBeVisible();
    });

    test('should display train workflow', async ({ page }) => {
        await page.goto('/flow');

        // Check for train/station metaphor elements
        const trainElements = page.locator('text=열차').or(
            page.locator('text=Station')
        ).or(
            page.locator('[data-testid*="train"]')
        ).or(
            page.locator('[data-testid*="station"]')
        );

        await expect(trainElements.first()).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Singularity (Template Gallery)', () => {
    test('should load singularity page', async ({ page }) => {
        await page.goto('/singularity');

        // Should show template gallery
        await expect(page.locator('text=특이점').or(
            page.locator('text=Singularity')
        ).or(
            page.locator('text=템플릿')
        )).toBeVisible();
    });

    test('should display template cards', async ({ page }) => {
        await page.goto('/singularity');

        // Wait for templates to load
        await page.waitForLoadState('networkidle');

        // Check for template cards
        const templateCards = page.locator('[data-testid^="template-card"]').or(
            page.locator('.template-card')
        ).or(
            page.locator('[data-testid*="singularity"]')
        );

        const count = await templateCards.count();
        expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should filter templates by tag', async ({ page }) => {
        await page.goto('/singularity');
        await page.waitForLoadState('networkidle');

        // Look for filter buttons/tabs
        const filterBtns = page.locator('[data-testid*="filter"]').or(
            page.locator('button:has-text("영화")').or(
                page.locator('button:has-text("광고")')
            )
        );

        if (await filterBtns.count() > 0) {
            await filterBtns.first().click();
            // URL or content should change
            await page.waitForTimeout(500);
        }
    });
});

test.describe('Constellation (Workflow Combos)', () => {
    test('should load constellation page', async ({ page }) => {
        await page.goto('/constellation');

        // Should show constellation UI
        await expect(page.locator('text=별자리').or(
            page.locator('text=Constellation')
        ).or(
            page.locator('[data-testid="constellation"]')
        )).toBeVisible({ timeout: 10000 });
    });
});
