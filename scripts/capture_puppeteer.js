
/**
 * Puppeteer Screenshot Script for Dimension Apps
 */
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3100';
const SCREENSHOT_DIR = '/Users/ted/vivid/scripts/ppt_screenshots';

// App list
const APPS = [
    { route: 'dimension/abyss-mirror', name: 'Abyss Mirror' },
    { route: 'dimension/reference-decoder', name: 'Reference Decoder' },
    { route: 'dimension/story-architect', name: 'Story Architect' },
    { route: 'dimension/aesthetic-director', name: 'Aesthetic Director' },
    { route: 'dimension/storyboard-sketch', name: 'Storyboard Sketch' },
    { route: 'dimension/sound-crafter', name: 'Sound Crafter' },
    { route: 'dimension/prompt-alchemy', name: 'Prompt Alchemy' },
    { route: 'dimension/visual-realizer', name: 'Visual Realizer' },
    { route: 'dimension/video-maker', name: 'Video Maker' },
    { route: 'dimension/quality-director', name: 'Quality Director' },
    { route: 'flow', name: 'Flow Workflow' }
];

(async () => {
    // Ensure dir exists
    if (!fs.existsSync(SCREENSHOT_DIR)) {
        fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }

    console.log('🚀 Launching Puppeteer...');
    const browser = await puppeteer.launch({
        headless: true,
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080'],
        defaultViewport: { width: 1920, height: 1080 }
    });

    try {
        const page = await browser.newPage();

        // 1. Warm up
        console.log('🔥 Warming up...');
        await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(e => console.log('Warmup error:', e.message));

        // 2. Process apps
        for (const app of APPS) {
            console.log(`\n📸 Processing: ${app.name}...`);
            const url = `${BASE_URL}/${app.route}`;
            const filename = app.route.replace('dimension/', '').replace('/', '_') + '.png';
            const filepath = path.join(SCREENSHOT_DIR, filename);

            try {
                await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

                // Add a small delay for animations
                await new Promise(r => setTimeout(r, 2000));

                await page.screenshot({ path: filepath, fullPage: false });
                console.log(`✅ Saved: ${filename}`);
            } catch (err) {
                console.error(`❌ Failed ${app.name}:`, err.message);
            }
        }
    } catch (e) {
        console.error('Fatal Error:', e);
    } finally {
        await browser.close();
        console.log('✨ Done!');
    }
})();
