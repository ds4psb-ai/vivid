/**
 * Dimension Apps Screenshot & Test Script
 * 
 * This script:
 * 1. Navigates to each dimension app
 * 2. Fills in creative test prompts
 * 3. Takes high-quality screenshots
 * 4. Optionally tests execution
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3100';
const SCREENSHOT_DIR = path.join(__dirname, 'ppt_screenshots');

// Creative prompts for each dimension app
const DIMENSION_APPS = [
    {
        route: 'abyss-mirror',
        name: '심연의 거울',
        nameEn: 'Abyss Mirror',
        description: '나만의 창작 DNA를 발견하는 자기 분석 도구. 내가 좋아하는 것들을 입력하면, AI가 숨겨진 창작 패턴을 분석해줍니다.',
        testPrompt: '나는 왕가위 영화의 네온 불빛 아래 고독한 인물들, 이누야샤의 시간을 넘나드는 서사, 그리고 Nujabes의 재즈힙합에 끌립니다',
        inputSelector: 'textarea', // Will be refined
    },
    {
        route: 'reference-decoder',
        name: '레퍼런스 해석기',
        nameEn: 'Reference Decoder',
        description: '레퍼런스 영상/이미지의 연출 기법을 언어로 번역. 조명, 색감, 카메라 워크, 편집 리듬을 전문 용어로 분석합니다.',
        testPrompt: '블레이드 러너 2049의 오프닝 시퀀스',
        inputSelector: 'textarea',
    },
    {
        route: 'story-architect',
        name: '시나리오 생성기',
        nameEn: 'Story Architect',
        description: '아이디어를 구조화된 시나리오로 변환. 3막 구조, 캐릭터 동기, 장면 전환까지 자동 설계합니다.',
        testPrompt: '도시의 마지막 책방 주인이 AI가 소설을 쓰는 시대에 손글씨 편지를 대필해주며 살아가는 이야기',
        inputSelector: 'textarea',
    },
    {
        route: 'aesthetic-director',
        name: '미학디렉터',
        nameEn: 'Aesthetic Director',
        description: '일관된 비주얼 스타일 가이드 생성. 색상 팔레트, 톤앤매너, 레퍼런스 이미지를 통합합니다.',
        testPrompt: '노스탤지어와 미래가 공존하는 Y2K 감성, 파스텔 네온과 로우파이 질감',
        inputSelector: 'textarea',
    },
    {
        route: 'storyboard-sketch',
        name: '스토리보드 스케치',
        nameEn: 'Storyboard Sketch',
        description: '시나리오를 시각적 컷으로 변환. 각 장면을 구체적인 카메라 앵글과 구도로 분해합니다.',
        testPrompt: 'Scene 1: 새벽 안개 속 외로운 등대, 360도 드론샷으로 서서히 접근',
        inputSelector: 'textarea',
    },
    {
        route: 'sound-crafter',
        name: '사운드 크래프터',
        nameEn: 'Sound Crafter',
        description: 'BGM과 효과음 프롬프트 생성. Suno/Udio에서 바로 사용할 수 있는 음악 프롬프트를 생성합니다.',
        testPrompt: '고독한 우주비행사가 지구를 바라보는 장면에 어울리는 앰비언트 음악',
        inputSelector: 'textarea',
    },
    {
        route: 'prompt-alchemy',
        name: '프롬프트 연금술',
        nameEn: 'Prompt Alchemy',
        description: 'AI가 이해하는 전문 프롬프트로 변환. Midjourney나 Veo에서 최적의 결과를 얻을 수 있는 프롬프트로 변환합니다.',
        testPrompt: '비 오는 도쿄 골목길에서 우산 쓴 소녀가 고양이를 쓰다듬는 장면',
        inputSelector: 'textarea',
    },
    {
        route: 'visual-realizer',
        name: '비주얼 리얼라이저',
        nameEn: 'Visual Realizer',
        description: '고품질 키프레임 이미지 생성. 영상의 핵심 장면을 미리 시각화할 수 있습니다.',
        testPrompt: 'Cyberpunk samurai standing on neon-lit rooftop, rain falling, cinematic lighting --ar 16:9 --style raw',
        inputSelector: 'textarea',
    },
    {
        route: 'video-maker',
        name: '비디오 메이커',
        nameEn: 'Video Maker',
        description: '정지 이미지를 움직이는 영상으로 변환. Google Veo 3.1로 4~8초 영상을 생성합니다.',
        testPrompt: '벚꽃 잎이 바람에 날리며 떨어지고, 카메라가 천천히 위로 틸트업하며 하늘을 비춘다',
        inputSelector: 'textarea',
    },
    {
        route: 'quality-director',
        name: '퀄리티 디렉터',
        nameEn: 'Quality Director',
        description: '결과물의 품질을 전문가 시선으로 검수. 시각적 일관성, 동작 자연스러움을 분석합니다.',
        testPrompt: '생성된 영상의 프레임 일관성과 캐릭터 동작 자연스러움을 검토해줘',
        inputSelector: 'textarea',
    },
];

async function captureScreenshots() {
    // Create output directory
    if (!fs.existsSync(SCREENSHOT_DIR)) {
        fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }

    let browser;
    try {
        browser = await chromium.launch({
            headless: true,  // Headless mode for reliable execution
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const context = await browser.newContext({
            viewport: { width: 1920, height: 1080 },
            deviceScaleFactor: 2,  // High DPI for crisp screenshots
        });

        const page = await context.newPage();

        const results = [];

        for (const app of DIMENSION_APPS) {
            console.log(`\n📸 Processing: ${app.name} (${app.route})`);

            try {
                // Navigate to the app
                await page.goto(`${BASE_URL}/dimension/${app.route}`, {
                    waitUntil: 'domcontentloaded',
                    timeout: 60000
                });

                // Wait for page to fully render
                await page.waitForTimeout(2000);

                // Try to find and fill input
                const textarea = await page.$('textarea');
                if (textarea) {
                    await textarea.fill(app.testPrompt);
                    console.log(`  ✏️ Filled prompt: "${app.testPrompt.substring(0, 50)}..."`);
                }

                // Wait for any animations
                await page.waitForTimeout(1000);

                // Take screenshot
                const screenshotPath = path.join(SCREENSHOT_DIR, `${app.route}.png`);
                await page.screenshot({
                    path: screenshotPath,
                    fullPage: false,  // Just viewport
                });
                console.log(`  ✅ Screenshot saved: ${screenshotPath}`);

                results.push({
                    ...app,
                    screenshotPath,
                    status: 'success'
                });

            } catch (error) {
                console.error(`  ❌ Error: ${error.message}`);
                results.push({
                    ...app,
                    status: 'error',
                    error: error.message
                });
            }
        }

        // Also capture Flow page
        console.log('\n📸 Processing: Flow Workflow View');
        try {
            await page.goto(`${BASE_URL}/flow`, { waitUntil: 'domcontentloaded', timeout: 60000 });
            await page.waitForTimeout(2000);
            const flowPath = path.join(SCREENSHOT_DIR, 'flow-workflow.png');
            await page.screenshot({ path: flowPath, fullPage: false });
            console.log(`  ✅ Screenshot saved: ${flowPath}`);
            results.push({ route: 'flow', name: 'Flow 워크플로우', screenshotPath: flowPath, status: 'success' });
        } catch (error) {
            console.error(`  ❌ Flow error: ${error.message}`);
        }

        // Generate summary
        console.log('\n' + '='.repeat(60));
        console.log('📊 SUMMARY');
        console.log('='.repeat(60));
        results.forEach(r => {
            const status = r.status === 'success' ? '✅' : '❌';
            console.log(`${status} ${r.name}`);
        });

        // Save metadata for PDF generation
        const metadataPath = path.join(SCREENSHOT_DIR, 'metadata.json');
        fs.writeFileSync(metadataPath, JSON.stringify(results, null, 2));
        console.log(`\n📄 Metadata saved: ${metadataPath}`);
        console.log(`📁 Screenshots saved to: ${SCREENSHOT_DIR}`);

        return results;
    } finally {
        // Always close browser to prevent zombie processes
        if (browser) {
            console.log('\n🧹 Cleaning up browser...');
            await browser.close();
        }
    }
}

// Run
captureScreenshots().catch(console.error);
