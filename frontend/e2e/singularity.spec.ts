import { test, expect } from '@playwright/test';

/**
 * Singularity Template Gallery E2E Tests
 * Tests the template gallery, preset selector, and template application
 */

test.describe('Singularity Gallery', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/singularity');
        await page.waitForLoadState('domcontentloaded');
    });

    test('should display Singularity page with blackhole visual', async ({ page }) => {
        // Check for main title
        await expect(page.locator('text=차원의 특이점').or(
            page.locator('text=Singularity')
        )).toBeVisible();
    });

    test('should show tag filter buttons', async ({ page }) => {
        // Check for "전체" button
        await expect(page.locator('button:has-text("전체")')).toBeVisible();

        // Check for popular tags
        const tags = ['풀스택', '초스피드', '감독스타일', '숏폼', '사운드', '품질검수'];
        for (const tag of tags.slice(0, 3)) {
            await expect(page.locator(`button:has-text("#${tag}")`)).toBeVisible();
        }
    });

    test('should show preset selector section', async ({ page }) => {
        // Check for preset section header
        await expect(page.locator('text=크리에이티브 프리셋')).toBeVisible();

        // Check for at least one preset button (e.g., 봉준호)
        const presetButtons = page.locator('button:has-text("봉준호")').or(
            page.locator('button:has-text("놀란")')
        ).or(
            page.locator('button:has-text("숏폼")')
        );
        const count = await presetButtons.count();
        expect(count).toBeGreaterThan(0);
    });

    test('should filter templates when tag selected', async ({ page }) => {
        // Click on a tag
        const tagButton = page.locator('button:has-text("#감독스타일")');
        if (await tagButton.count() > 0) {
            await tagButton.click();

            // Button should change style (indicating selected)
            await expect(tagButton).toHaveClass(/bg-violet-500/);
        }
    });

    test('should open template modal on card click', async ({ page }) => {
        // Wait for templates to load
        await page.waitForTimeout(1000);

        // Click first template card if available
        const templateCard = page.locator('[class*="rounded-3xl"]').first();
        if (await templateCard.count() > 0) {
            await templateCard.click();

            // Modal should appear with "이 워크플로우 적용하기" button
            await expect(page.locator('button:has-text("이 워크플로우 적용하기")')).toBeVisible();
        }
    });
});

test.describe('Singularity Preset Integration', () => {
    test('should load presets from API', async ({ page }) => {
        // Intercept preset API call
        await page.route('**/api/v1/intent/presets', async (route) => {
            const response = await route.fetch();
            const json = await response.json();

            // Verify response has presets array
            expect(json.presets).toBeDefined();
            expect(Array.isArray(json.presets)).toBeTruthy();

            await route.fulfill({ response });
        });

        await page.goto('/singularity');
        await page.waitForLoadState('networkidle');
    });

    test('should filter by preset when clicked', async ({ page }) => {
        await page.goto('/singularity');
        await page.waitForLoadState('networkidle');

        // Click on a preset
        const presetBtn = page.locator('button:has-text("봉준호")');
        if (await presetBtn.count() > 0) {
            await presetBtn.click();

            // Button should have selected styling
            await expect(presetBtn).toHaveClass(/ring-1/);
        }
    });
});
