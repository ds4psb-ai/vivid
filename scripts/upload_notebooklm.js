const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = 'https://notebooklm.google.com/';
const DATA_DIR = '/Users/ted/vivid/data/notebooklm_ready';
const DIRECTORS = [
    { id: 'bong', name: 'Bong Joon-ho' },
    { id: 'wong', name: 'Wong Kar-wai' },
    { id: 'villeneuve', name: 'Denis Villeneuve' },
    { id: 'nolan', name: 'Christopher Nolan' },
    { id: 'tarantino', name: 'Quentin Tarantino' }
];

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PROFILE_PATH = '/Users/ted/Library/Application Support/Google/Chrome';

(async () => {
    console.log('🚀 Starting NotebookLM Uploader v3 (Profile Mode)...');
    console.log(`👤 Using Chrome Profile: ${PROFILE_PATH}`);

    const browser = await puppeteer.launch({
        headless: false,
        executablePath: CHROME_PATH,
        defaultViewport: null,
        userDataDir: PROFILE_PATH, // Reuses the user's actual login session
        args: ['--start-maximized', '--no-sandbox', '--profile-directory=Default'] // Usually 'Default' or 'Profile 1'
    });

    try {
        // Get the pages to find the active one or create new
        const pages = await browser.pages();
        const page = pages.length > 0 ? pages[0] : await browser.newPage();

        // 1. Navigation
        console.log('🌍 Navigating to NotebookLM...');
        await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

        // Wait for potential redirects or load
        await new Promise(r => setTimeout(r, 5000));

        // Check Login State by looking for "Welcome" or User Avatar
        const isLoggedIn = await page.evaluate(() => {
            return document.querySelector('img[src*="googleusercontent"]') !== null ||
                document.body.innerText.includes('New Notebook') ||
                document.body.innerText.includes('새 노트북');
        });

        if (!isLoggedIn) {
            console.log('⚠️  Login not detected automatically.');
            console.log('👉 ACTION REQUIRED: Please select your profile (arkain.info@gmail.com) in the window if prompted.');
            await page.waitForFunction(() => {
                return document.body.innerText.includes('New Notebook') || document.body.innerText.includes('새 노트북');
            }, { timeout: 600000 }); // 10 min
        }
        console.log('✅ Dashboard Ready.');

        // 2. Process each director
        for (const director of DIRECTORS) {
            console.log(`\n🎬 Processing Director: ${director.name} (${director.id})...`);

            // Check files
            const dirPath = path.join(DATA_DIR, director.id);
            if (!fs.existsSync(dirPath)) continue;
            const files = fs.readdirSync(dirPath)
                .filter(f => f.endsWith('.md') || f.endsWith('.txt'))
                .map(f => path.join(dirPath, f));
            if (files.length === 0) continue;

            console.log(`📄 Found ${files.length} files.`);

            // Ensure we are on Dashboard
            if (!page.url().includes('notebooklm.google.com') || page.url().includes('/notebook/')) {
                await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
                await new Promise(r => setTimeout(r, 3000));
            }

            // Click "New Notebook"
            console.log('➕ Creating new notebook...');

            const clicked = await page.evaluate(() => {
                // XPath-like search for text
                const elements = document.querySelectorAll('div, span, button');
                for (let el of elements) {
                    if (el.innerText && (el.innerText === 'New Notebook' || el.innerText === '새 노트북')) {
                        el.click();
                        return true;
                    }
                }
                // Fallback: aria-label
                const aria = document.querySelector('[aria-label="Create new notebook"], [aria-label="New notebook"], [aria-label="새 노트북"]');
                if (aria) { aria.click(); return true; }

                // Fallback: first card in grid (often the 'New' button)
                const grid = document.querySelector('.notebook-grid');
                if (grid && grid.firstElementChild) {
                    grid.firstElementChild.click();
                    return true;
                }
                return false;
            });

            if (!clicked) {
                console.error(`❌ Failed to click "New Notebook". Skipping ${director.name}`);
                await page.screenshot({ path: `error_${director.id}.png` });
                continue;
            }

            // Wait for Notebook Load (URL change)
            await page.waitForFunction(() => window.location.href.includes('/notebook/'), { timeout: 15000 }).catch(() => { });
            await new Promise(r => setTimeout(r, 4000));

            // Rename
            console.log('🏷️  Renaming...');
            const renamed = await page.evaluate((name) => {
                const titleInput = document.querySelector('input.title-input') || document.querySelector('input[aria-label="Notebook title"]');
                if (titleInput) {
                    titleInput.value = "";
                    titleInput.focus();
                    document.execCommand('insertText', false, name + " Source Pack 2026");
                    titleInput.blur();
                    return true;
                }
                return false;
            }, director.name);

            if (!renamed) console.log('⚠️ Rename failed (UI element not found).');
            await new Promise(r => setTimeout(r, 1000));

            // Upload
            console.log('📤 Uploading...');
            const fileInput = await page.$('input[type="file"]');
            if (fileInput) {
                await fileInput.uploadFile(...files);
                console.log('✅ Files sent to browser.');
                // Wait for the upload validation/processing
                await new Promise(r => setTimeout(r, 15000));
            } else {
                console.error('❌ File input not found.');
            }

            console.log(`🎉 Finished ${director.name}`);
        }

    } catch (e) {
        console.error('❌ Critical Error:', e);
    } finally {
        console.log('✨ Automation Complete.');
        // browser.close(); // Don't close so user can see result
    }
})();
