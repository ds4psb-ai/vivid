import { test, expect } from '@playwright/test';

/**
 * Dimension Workflow E2E Tests
 * Tests the core Dimension mini-app workflows
 */

test.describe('Dimension Hub', () => {
    test('should load dimension hub page', async ({ page }) => {
        await page.goto('/dimension');

        // Should display dimension hub title or grid
        await expect(page.locator('h1, [data-testid="dimension-hub"]')).toBeVisible();
    });

    test('should show all dimension cards', async ({ page }) => {
        await page.goto('/dimension');

        // Check for dimension card presence (10+ dimensions)
        const dimensionCards = page.locator('[data-testid^="dimension-card"]').or(
            page.locator('.dimension-card')
        ).or(
            page.locator('a[href*="/dimension/"]')
        );

        const count = await dimensionCards.count();
        expect(count).toBeGreaterThan(5);
    });
});

test.describe('Story Architect', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dimension/story-architect');
        // Wait for DOM to load, then wait for textarea (avoids networkidle polling issue)
        await page.waitForLoadState('domcontentloaded');
        await page.waitForSelector('textarea', { state: 'visible' });
    });

    test('should display Story Architect panel', async ({ page }) => {
        // Check for title
        await expect(page.locator('text=시나리오 생성기').or(
            page.locator('text=Story Architect')
        )).toBeVisible();

        // Check for concept textarea
        await expect(page.locator('textarea')).toBeVisible();
    });

    test('should show genre and duration selectors', async ({ page }) => {
        // Genre selector
        const genreSelect = page.locator('select').first();
        await expect(genreSelect).toBeVisible();

        // Verify genre options exist
        const options = await genreSelect.locator('option').count();
        expect(options).toBeGreaterThan(3);
    });

    test('should validate concept input', async ({ page }) => {
        // Try to submit with empty concept
        const submitBtn = page.locator('button:has-text("아이디어 다듬기")').or(
            page.locator('button:has-text("Pitch")')
        );

        // Button should be disabled or show validation error
        const isDisabled = await submitBtn.isDisabled();
        expect(isDisabled).toBeTruthy();
    });

    test('should enable submit after typing concept', async ({ page }) => {
        const textarea = page.locator('textarea').first();
        await textarea.fill('외로운 로봇이 감정을 배우는 이야기');

        const submitBtn = page.locator('button:has-text("아이디어 다듬기")').or(
            page.locator('button:has-text("Pitch")')
        );

        // Button should now be enabled
        await expect(submitBtn).toBeEnabled();
    });
});

test.describe('Aesthetic Director', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dimension/aesthetic');
        // Wait for DOM to load, then wait for textarea (avoids networkidle polling issue)
        await page.waitForLoadState('domcontentloaded');
        await page.waitForSelector('textarea', { state: 'visible' });
    });

    test('should display Aesthetic Director panel', async ({ page }) => {
        // Check for title
        await expect(page.locator('text=미학디렉터').or(
            page.locator('text=Aesthetic Director')
        )).toBeVisible();

        // Check for concept input
        await expect(page.locator('textarea')).toBeVisible();
    });

    test('should show mood selector', async ({ page }) => {
        // Mood dropdown
        const moodSelect = page.locator('select').first();
        await expect(moodSelect).toBeVisible();
    });
});

test.describe('Sound Crafter', () => {
    test('should load Sound Crafter page', async ({ page }) => {
        await page.goto('/dimension/sound-crafter');

        // Should have title
        await expect(page.locator('text=사운드 크래프터').or(
            page.locator('text=Sound Crafter')
        )).toBeVisible();
    });
});

test.describe('Video Maker (Veo)', () => {
    test('should load Video Maker page', async ({ page }) => {
        await page.goto('/dimension/video-maker');

        // Should have title
        await expect(page.locator('text=비디오 메이커').or(
            page.locator('text=Video Maker')
        )).toBeVisible();
    });

    test('should show duration options', async ({ page }) => {
        await page.goto('/dimension/video-maker');

        // Check for duration selector (4s, 6s, 8s)
        const durationText = page.locator('text=4초').or(
            page.locator('text=6초')
        ).or(
            page.locator('text=8초')
        );

        const count = await durationText.count();
        expect(count).toBeGreaterThan(0);
    });
});

test.describe('Quality Check / Creative Editor', () => {
    test('should load Quality Check page', async ({ page }) => {
        await page.goto('/dimension/quality-check');

        // Should have Creative Editor title (mapped by design)
        await expect(page.locator('text=크리에이티브 에디터').or(
            page.locator('text=Creative Editor')
        ).or(
            page.locator('text=퀄리티')
        )).toBeVisible();
    });
});

test.describe('Dimension Navigation', () => {
    test('should navigate between dimensions', async ({ page }) => {
        await page.goto('/dimension');

        // Click on a dimension card
        const storyCard = page.locator('a[href*="story-architect"]').or(
            page.locator('[data-testid="dimension-card-story"]')
        );

        if (await storyCard.count() > 0) {
            await storyCard.first().click();
            await expect(page).toHaveURL(/story-architect/);
        }
    });
});
