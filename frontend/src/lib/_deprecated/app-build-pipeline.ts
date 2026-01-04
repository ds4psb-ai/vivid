/**
 * App Build Pipeline
 * 
 * 외부 앱을 Crebit 플랫폼에 안전하게 배포하기 위한 빌드 파이프라인입니다.
 * 
 * 기능:
 * 1. 코드 번들링 (esbuild)
 * 2. JavaScript 난독화 (javascript-obfuscator)
 * 3. Crebit SDK 주입
 * 4. 메타데이터 검증
 */

import * as esbuild from 'esbuild';
import JavaScriptObfuscator from 'javascript-obfuscator';
import * as fs from 'fs';
import * as path from 'path';

// 난독화 설정 (production)
const OBFUSCATION_CONFIG = {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.75,
    deadCodeInjection: true,
    deadCodeInjectionThreshold: 0.4,
    debugProtection: false, // 개발 중에는 false
    debugProtectionInterval: 0,
    disableConsoleOutput: false, // 개발 중에는 false
    identifierNamesGenerator: 'hexadecimal',
    log: false,
    numbersToExpressions: true,
    renameGlobals: false,
    rotateStringArray: true,
    selfDefending: true,
    shuffleStringArray: true,
    splitStrings: true,
    splitStringsChunkLength: 10,
    stringArray: true,
    stringArrayEncoding: ['base64'],
    stringArrayThreshold: 0.75,
    transformObjectKeys: true,
    unicodeEscapeSequence: false
};

// Crebit.json 스키마
interface CrebitManifest {
    name: string;
    version: string;
    entry: string;
    dimension?: {
        theme?: string;
        primaryColor?: string;
        accentColor?: string;
        borderStyle?: string;
    };
    permissions?: string[];
    credits?: {
        perRun?: number;
        perSave?: number;
    };
}

/**
 * 매니페스트 파일 검증
 */
function validateManifest(manifest: unknown): manifest is CrebitManifest {
    if (!manifest || typeof manifest !== 'object') return false;
    const m = manifest as Record<string, unknown>;

    if (typeof m.name !== 'string' || !m.name) return false;
    if (typeof m.version !== 'string' || !m.version) return false;
    if (typeof m.entry !== 'string' || !m.entry) return false;

    return true;
}

/**
 * SDK 템플릿 생성
 */
function generateSDK(appId: string, config: CrebitManifest, platformOrigin: string): string {
    const sdkTemplate = fs.readFileSync(
        path.join(__dirname, '../../public/sdk/crebit-sdk.js'),
        'utf-8'
    );

    return sdkTemplate
        .replace('__PLATFORM_ORIGIN__', platformOrigin)
        .replace('__APP_ID__', appId)
        .replace('__APP_CONFIG__', JSON.stringify(config));
}

/**
 * HTML에 SDK 주입
 */
function injectSDKIntoHTML(html: string, sdk: string): string {
    // </head> 태그 바로 앞에 SDK 삽입
    const sdkScript = `<script>\n${sdk}\n</script>`;

    if (html.includes('</head>')) {
        return html.replace('</head>', `${sdkScript}\n</head>`);
    }

    // <head> 태그가 없으면 <body> 시작 부분에 삽입
    if (html.includes('<body>')) {
        return html.replace('<body>', `<body>\n${sdkScript}`);
    }

    // 둘 다 없으면 맨 앞에 삽입
    return sdkScript + '\n' + html;
}

/**
 * JavaScript 파일 난독화
 */
function obfuscateJS(code: string, isProd: boolean = true): string {
    if (!isProd) {
        // 개발 모드: 난독화 없이 반환
        return code;
    }

    const result = JavaScriptObfuscator.obfuscate(code, OBFUSCATION_CONFIG);
    return result.getObfuscatedCode();
}

/**
 * 앱 빌드 파이프라인
 */
export async function buildApp(options: {
    sourceDir: string;
    outputDir: string;
    appId: string;
    platformOrigin: string;
    isProd?: boolean;
}): Promise<{ success: boolean; error?: string }> {
    const { sourceDir, outputDir, appId, platformOrigin, isProd = true } = options;

    try {
        // 1. 매니페스트 읽기 및 검증
        const manifestPath = path.join(sourceDir, 'crebit.json');
        if (!fs.existsSync(manifestPath)) {
            return { success: false, error: 'crebit.json not found' };
        }

        const manifestRaw = fs.readFileSync(manifestPath, 'utf-8');
        const manifest = JSON.parse(manifestRaw);

        if (!validateManifest(manifest)) {
            return { success: false, error: 'Invalid crebit.json schema' };
        }

        // 2. 출력 디렉토리 생성
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        // 3. SDK 생성
        const sdk = generateSDK(appId, manifest, platformOrigin);
        const obfuscatedSDK = obfuscateJS(sdk, isProd);

        // 4. 엔트리 HTML 처리
        const entryPath = path.join(sourceDir, manifest.entry);
        if (!fs.existsSync(entryPath)) {
            return { success: false, error: `Entry file not found: ${manifest.entry}` };
        }

        let html = fs.readFileSync(entryPath, 'utf-8');
        html = injectSDKIntoHTML(html, obfuscatedSDK);

        // 5. JavaScript 파일 번들링 및 난독화
        const jsFiles = findJSFiles(sourceDir);
        for (const jsFile of jsFiles) {
            const code = fs.readFileSync(jsFile, 'utf-8');
            const obfuscated = obfuscateJS(code, isProd);

            const relativePath = path.relative(sourceDir, jsFile);
            const outputPath = path.join(outputDir, relativePath);

            fs.mkdirSync(path.dirname(outputPath), { recursive: true });
            fs.writeFileSync(outputPath, obfuscated);
        }

        // 6. HTML 출력
        fs.writeFileSync(path.join(outputDir, manifest.entry), html);

        // 7. 기타 파일 복사 (CSS, 이미지 등)
        copyNonJSFiles(sourceDir, outputDir);

        // 8. 빌드 메타데이터 저장
        fs.writeFileSync(
            path.join(outputDir, '.crebit-build.json'),
            JSON.stringify({
                appId,
                version: manifest.version,
                builtAt: new Date().toISOString(),
                isProd
            }, null, 2)
        );

        return { success: true };

    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * JavaScript 파일 찾기
 */
function findJSFiles(dir: string): string[] {
    const files: string[] = [];
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            files.push(...findJSFiles(fullPath));
        } else if (entry.name.endsWith('.js') && !entry.name.endsWith('.min.js')) {
            files.push(fullPath);
        }
    }

    return files;
}

/**
 * 비-JS 파일 복사
 */
function copyNonJSFiles(sourceDir: string, outputDir: string): void {
    const entries = fs.readdirSync(sourceDir, { withFileTypes: true });

    for (const entry of entries) {
        const sourcePath = path.join(sourceDir, entry.name);
        const outputPath = path.join(outputDir, entry.name);

        if (entry.isDirectory()) {
            fs.mkdirSync(outputPath, { recursive: true });
            copyNonJSFiles(sourcePath, outputPath);
        } else if (!entry.name.endsWith('.js') &&
            entry.name !== 'crebit.json' &&
            !entry.name.startsWith('.')) {
            fs.copyFileSync(sourcePath, outputPath);
        }
    }
}

export default buildApp;
