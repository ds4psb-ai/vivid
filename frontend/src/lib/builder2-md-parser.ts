/**
 * Builder2 MD Parser
 *
 * Parses Builder output format (supports both legacy and v8.0 unified format).
 * Extracts scenes with IMAGE/MOTION prompts.
 *
 * Supported Formats:
 *
 * 1. Legacy <<<TAG>>> format:
 *    - <<<OHMAGE_IMAGE_START>>> ~ <<<OHMAGE_IMAGE_END>>>
 *    - <<<OHMAGE_MOTION_START>>> ~ <<<OHMAGE_MOTION_END>>>
 *    - <<<VARIATION_IMAGE_START>>> ~ <<<VARIATION_IMAGE_END>>>
 *    - <<<VARIATION_MOTION_START>>> ~ <<<VARIATION_MOTION_END>>>
 *
 * 2. v8.0 Unified format (Builder1 v8.0):
 *    - ## ⭐ 앵커 이미지 먼저 생성 (anchor section)
 *    - ## 📍 Scene XX: [Title] (scene sections)
 *    - ### 🖼️ IMAGE (image prompts)
 *    - ### 🎥 MOTION (motion prompts)
 *    - [📋 COPY] markers for easy copy
 */

export interface SceneRefInfo {
  composition: string;  // "scene_01.png"
  face: 'MALE_ANCHOR' | 'FEMALE_ANCHOR' | 'BOTH' | 'NONE';
}

export interface Builder2Scene {
  sceneNum: number;
  title: string;
  beatTimestamp: string;
  imagePrompts: {
    nanoBanana: string;
    midjourney: string;
  };
  motionPrompts: {
    kling: string;
    veo: string;
  };
  isAnchor: boolean;
  frameFile: string;           // "frame_01_00-00.00.jpg"
  anchorRefs: string[];        // ["MALE"] - 이 씬에서 참조하는 앵커
  refInfo?: SceneRefInfo;      // [REF] 태그에서 파싱
}

export interface AnchorInfo {
  key: string;           // "MALE", "FEMALE"
  emoji: string;         // "👨", "👩"
  sceneNum: number;      // 2, 5
  title: string;         // "기다림", "미소"
  character: string;     // "청자켓 입은 한국인 남성"
  frameFile: string;     // "frame_02_00-01.67.jpg"
}

export interface ParseWarning {
  sceneNum: number | null;
  type: 'lazy_pattern' | 'missing_param' | 'missing_prompt';
  message: string;
}

export interface Builder2ParseResult {
  ohmageScenes: Builder2Scene[];
  variationScenes: Builder2Scene[];
  hasOhmage: boolean;
  hasVariation: boolean;
  anchorSceneNum: number | null;
  anchors: AnchorInfo[];  // 앵커 정보 목록
  warnings: ParseWarning[];
}

type TagName =
  | "OHMAGE_IMAGE"
  | "OHMAGE_MOTION"
  | "VARIATION_IMAGE"
  | "VARIATION_MOTION";

// ANTI-LAZY detection patterns
const LAZY_PATTERNS = [
  { pattern: /위와\s*동일/g, label: '위와 동일' },
  { pattern: /이하\s*생략/g, label: '이하 생략' },
  { pattern: /similar\s+to\s+Scene/gi, label: 'similar to Scene' },
  { pattern: /같은\s*방식으로/g, label: '같은 방식으로' },
  { pattern: /\(생략\)/g, label: '(생략)' },
  { pattern: /\(skip\)/gi, label: '(skip)' },
];

/**
 * Extract content between <<<TAG_START>>> and <<<TAG_END>>> delimiters
 */
export function extractTagSection(
  content: string,
  tagName: TagName
): string | null {
  const startTag = `<<<${tagName}_START>>>`;
  const endTag = `<<<${tagName}_END>>>`;

  const startIdx = content.indexOf(startTag);
  if (startIdx === -1) return null;

  const endIdx = content.indexOf(endTag, startIdx);
  if (endIdx === -1) return null;

  return content.slice(startIdx + startTag.length, endIdx).trim();
}

/**
 * Parse scene number and title from header like:
 * "### Scene 01: Birthday Party (0:00-0:03)"
 */
function parseSceneHeader(
  header: string
): { sceneNum: number; title: string; timestamp: string } | null {
  // Match patterns like "Scene 01:", "Scene 1:", etc.
  const match = header.match(
    /Scene\s*(\d+)[:\s]+([^(]+)(?:\(([^)]+)\))?/i
  );
  if (!match) return null;

  return {
    sceneNum: parseInt(match[1], 10),
    title: match[2]?.trim() || "",
    timestamp: match[3]?.trim() || "",
  };
}

/**
 * Extract code block content (text between triple backticks)
 */
function extractCodeBlock(text: string): string {
  const match = text.match(/```(?:text)?\s*\n?([\s\S]*?)```/);
  return match ? match[1].trim() : "";
}

/**
 * Extract prompt text with fallback when code fences are missing.
 * Tries code block first, then falls back to raw text after the label line.
 */
function extractPromptWithFallback(block: string, labelPattern: RegExp): string {
  // Try code block first
  const codeBlockMatch = block.match(
    new RegExp(labelPattern.source + '[^\\n]*\\n```(?:text)?\\s*\\n?([\\s\\S]*?)```', labelPattern.flags)
  );
  if (codeBlockMatch && codeBlockMatch[1]?.trim()) {
    return codeBlockMatch[1].trim();
  }

  // Fallback: grab text after the label line until next section marker or end
  const fallbackMatch = block.match(
    new RegExp(labelPattern.source + '[^\\n]*\\n([\\s\\S]*?)(?=\\n(?:\\[📋|#{2,3}\\s|---)|$)', labelPattern.flags)
  );
  if (fallbackMatch && fallbackMatch[1]?.trim()) {
    // Remove leading/trailing empty lines and common markdown artifacts
    return fallbackMatch[1].trim();
  }

  return '';
}

/**
 * Generate frame file name from scene number and timestamp
 * timestamp: "00:00.00~00:01.67" → "frame_01_00-00.00.jpg"
 */
function generateFrameFileName(sceneNum: number, timestamp: string): string {
  if (!timestamp) {
    return `frame_${String(sceneNum).padStart(2, '0')}.jpg`;
  }
  // Extract start time from "00:01.67~00:04.56" format
  const [start] = timestamp.split('~');
  // Convert "00:01.67" to "00-01.67"
  const formatted = start.replace(':', '-');
  return `frame_${String(sceneNum).padStart(2, '0')}_${formatted}.jpg`;
}

/**
 * Extract anchor references from scene block
 * Returns array of anchor keys ("MALE", "FEMALE") that the scene references
 */
function extractAnchorRefs(block: string): string[] {
  const refs: string[] = [];

  // [REF] tag pattern (highest priority)
  const refTag = parseRefTag(block);
  if (refTag) {
    if (refTag.face === 'MALE_ANCHOR') return ['MALE'];
    if (refTag.face === 'FEMALE_ANCHOR') return ['FEMALE'];
    if (refTag.face === 'BOTH') return ['MALE', 'FEMALE'];
    if (refTag.face === 'NONE') return [];
  }

  // Legacy: Check for various anchor reference patterns
  if (block.includes('[MALE_ANCHOR') ||
      block.includes('MALE ANCHOR') ||
      (block.includes('[Image 2: CHARACTER FACE]') && block.toLowerCase().includes('male'))) {
    refs.push('MALE');
  }
  if (block.includes('[FEMALE_ANCHOR') ||
      block.includes('FEMALE ANCHOR') ||
      (block.includes('[Image 2: CHARACTER FACE]') && block.toLowerCase().includes('female'))) {
    refs.push('FEMALE');
  }
  // Generic anchor reference (--cref or --oref)
  if (refs.length === 0 &&
      (block.includes('[ANCHOR') ||
       block.includes('--cref') ||
       block.includes('--oref') ||
       (block.includes('[Image 2:') && block.includes('ANCHOR')))) {
    refs.push('MALE'); // Default to MALE if generic anchor reference
  }
  return refs;
}

/**
 * Parse [REF] tag from a scene block
 * Format: [REF: COMP=scene_XX.png, FACE=MALE_ANCHOR]
 */
function parseRefTag(block: string): SceneRefInfo | undefined {
  const match = block.match(/\[REF:\s*COMP=([^,\]]+)(?:,\s*FACE=([^\]]+))?\]/i);
  if (!match) return undefined;
  return {
    composition: match[1].trim(),
    face: (match[2]?.trim() || 'NONE') as SceneRefInfo['face'],
  };
}

/**
 * Detect ANTI-LAZY patterns in a scene block
 */
function detectLazyPatterns(block: string, sceneNum: number): ParseWarning[] {
  const warnings: ParseWarning[] = [];
  for (const { pattern, label } of LAZY_PATTERNS) {
    // Reset lastIndex for global patterns
    pattern.lastIndex = 0;
    if (pattern.test(block)) {
      warnings.push({
        sceneNum,
        type: 'lazy_pattern',
        message: `LAZY 패턴 감지: "${label}"`,
      });
    }
  }
  return warnings;
}

/**
 * Validate MJ parameters in a Midjourney prompt
 */
function validateMJParams(prompt: string, sceneNum: number, isAnchor: boolean): ParseWarning[] {
  const warnings: ParseWarning[] = [];
  if (!prompt) return warnings;

  // --ar missing
  if (!prompt.includes('--ar')) {
    warnings.push({
      sceneNum,
      type: 'missing_param',
      message: '--ar (종횡비) 누락',
    });
  }

  // --v missing
  if (!prompt.includes('--v ')) {
    warnings.push({
      sceneNum,
      type: 'missing_param',
      message: '--v (버전) 누락',
    });
  }

  // Non-anchor scene missing --oref
  if (!isAnchor && !prompt.includes('--oref') && !prompt.includes('--cref')) {
    warnings.push({
      sceneNum,
      type: 'missing_param',
      message: '비앵커 씬에 --oref 누락',
    });
  }

  // --ow > 500 warning
  const owMatch = prompt.match(/--ow\s+(\d+)/);
  if (owMatch) {
    const owValue = parseInt(owMatch[1], 10);
    if (owValue > 500) {
      warnings.push({
        sceneNum,
        type: 'missing_param',
        message: `--ow ${owValue} > 500 (권장: 50-250)`,
      });
    }
  }

  return warnings;
}

/**
 * Parse IMAGE prompts section into scenes
 */
function parseImageSection(content: string): Map<number, Builder2Scene> {
  const scenes = new Map<number, Builder2Scene>();

  // Split by scene headers
  const sceneBlocks = content.split(/(?=###\s*(?:Scene|\uD83C\uDFAC))/i);

  for (const block of sceneBlocks) {
    if (!block.trim()) continue;

    // Find scene header
    const headerMatch = block.match(
      /###\s*(?:\uD83C\uDFAC\s*)?Scene\s*(\d+)[:\s]+([^(\n]+)(?:\(([^)]+)\))?/i
    );
    if (!headerMatch) continue;

    const sceneNum = parseInt(headerMatch[1], 10);
    const title = headerMatch[2]?.trim() || "";
    const timestamp = headerMatch[3]?.trim() || "";

    // Check if anchor scene
    const isAnchor =
      block.toUpperCase().includes("ANCHOR") ||
      block.includes("(ANCHOR)") ||
      block.includes("(앵커)");

    // Extract NanoBanana prompt (with fallback)
    const nanoBanana = extractPromptWithFallback(block, /(?:\[📋\s*COPY\]\s*)?NanoBanana/i);

    // Extract Midjourney prompt (with fallback)
    const midjourney = extractPromptWithFallback(block, /(?:\[📋\s*COPY\]\s*)?(?:Midjourney|MJ)/i);

    scenes.set(sceneNum, {
      sceneNum,
      title,
      beatTimestamp: timestamp,
      imagePrompts: { nanoBanana, midjourney },
      motionPrompts: { kling: "", veo: "" },
      isAnchor,
      frameFile: generateFrameFileName(sceneNum, timestamp),
      anchorRefs: extractAnchorRefs(block),
      refInfo: parseRefTag(block),
    });
  }

  return scenes;
}

/**
 * Parse MOTION prompts section and merge into existing scenes
 */
function parseMotionSection(
  content: string,
  existingScenes: Map<number, Builder2Scene>
): Map<number, Builder2Scene> {
  // Split by scene headers
  const sceneBlocks = content.split(/(?=###\s*(?:Scene|\uD83C\uDFAC))/i);

  for (const block of sceneBlocks) {
    if (!block.trim()) continue;

    // Find scene header
    const headerMatch = block.match(
      /###\s*(?:\uD83C\uDFAC\s*)?Scene\s*(\d+)/i
    );
    if (!headerMatch) continue;

    const sceneNum = parseInt(headerMatch[1], 10);

    // Extract Kling prompt (with fallback)
    const kling = extractPromptWithFallback(block, /(?:\[📋\s*COPY\]\s*)?Kling/i);

    // Extract Veo prompt (with fallback)
    const veo = extractPromptWithFallback(block, /(?:\[📋\s*COPY\]\s*)?Veo/i);

    // Merge with existing scene or create new
    if (existingScenes.has(sceneNum)) {
      const scene = existingScenes.get(sceneNum)!;
      scene.motionPrompts = { kling, veo };
    } else {
      // Create new scene from motion-only data
      const titleMatch = block.match(
        /Scene\s*\d+[:\s]+([^(\n]+)(?:\(([^)]+)\))?/i
      );
      const timestamp = titleMatch?.[2]?.trim() || "";
      existingScenes.set(sceneNum, {
        sceneNum,
        title: titleMatch?.[1]?.trim() || `Scene ${sceneNum}`,
        beatTimestamp: timestamp,
        imagePrompts: { nanoBanana: "", midjourney: "" },
        motionPrompts: { kling, veo },
        isAnchor:
          block.toUpperCase().includes("ANCHOR") ||
          block.includes("(ANCHOR)"),
        frameFile: generateFrameFileName(sceneNum, timestamp),
        anchorRefs: extractAnchorRefs(block),
      });
    }
  }

  return existingScenes;
}

/**
 * Parse IMAGE prompts from unified format block
 * Supports both direct tool names and [📋 COPY] markers
 * Falls back to raw text when code fences are missing
 */
function parseUnifiedImagePrompts(content: string): { nanoBanana: string; midjourney: string } {
  return {
    nanoBanana: extractPromptWithFallback(content, /(?:\[📋\s*COPY\]\s*)?NanoBanana/i),
    midjourney: extractPromptWithFallback(content, /(?:\[📋\s*COPY\]\s*)?(?:Midjourney|MJ)/i),
  };
}

/**
 * Parse MOTION prompts from unified format block
 * Supports both direct tool names and [📋 COPY] markers
 * Falls back to raw text when code fences are missing
 */
function parseUnifiedMotionPrompts(content: string): { kling: string; veo: string } {
  return {
    kling: extractPromptWithFallback(content, /(?:\[📋\s*COPY\]\s*)?Kling/i),
    veo: extractPromptWithFallback(content, /(?:\[📋\s*COPY\]\s*)?Veo/i),
  };
}

/**
 * Extract character description from anchor section table or nearby text
 * Table format: | 👨 MALE | Scene 02 | 청자켓 입은 한국인 남성 | 남자 레퍼런스 |
 */
function extractAnchorCharacter(content: string, anchorKey: string): string {
  const emoji = anchorKey === 'MALE' ? '👨' : '👩';

  // Pattern 1: Table row - extract 3rd column (character description)
  // | 👨 MALE | Scene 02 | 청자켓 입은 남성 | 남자 레퍼런스 |
  const tableRowPattern = new RegExp(
    `\\|\\s*${emoji}\\s*${anchorKey}\\s*\\|\\s*Scene\\s*\\d+\\s*\\|\\s*([^|]+)\\s*\\|`,
    'i'
  );
  const tableMatch = content.match(tableRowPattern);
  if (tableMatch && tableMatch[1].trim()) {
    return tableMatch[1].trim();
  }

  // Pattern 2: Header format ### 👨 MALE ANCHOR (Scene XX: title)
  const headerPattern = new RegExp(
    `${emoji}\\s*${anchorKey}.*?캐릭터[:\\s]*([^\\n]+)`,
    'i'
  );
  const headerMatch = content.match(headerPattern);
  if (headerMatch && headerMatch[1].trim()) {
    return headerMatch[1].trim();
  }

  // Pattern 3: Extract from anchor scene content (fallback)
  // Look for "한국인 남성/여성" pattern in content
  const genderWord = anchorKey === 'MALE' ? '남성' : '여성';
  const koreanPattern = new RegExp(`([^\\n]*한국인\\s*${genderWord}[^\\n]*)`, 'i');
  const koreanMatch = content.match(koreanPattern);
  if (koreanMatch) {
    // Extract a reasonable description (up to 30 chars)
    const desc = koreanMatch[1].trim();
    if (desc.length <= 50) return desc;
    return `한국인 ${genderWord}`;
  }

  return anchorKey === 'MALE' ? '남자 캐릭터' : '여자 캐릭터';
}

/**
 * Parse anchor information from the ⭐ section
 * Supports both header format and table format:
 *
 * Header: ### 👨 MALE ANCHOR (Scene XX: title)
 * Table:  | 👨 MALE | Scene 02 | 청자켓 입은 남성 | 남자 레퍼런스 |
 */
function parseAnchorInfo(content: string, scenes: Builder2Scene[]): AnchorInfo[] {
  const anchors: AnchorInfo[] = [];

  // 1. Try header format: ### 👨 MALE ANCHOR (Scene XX: title)
  const maleHeaderMatch = content.match(/###\s*👨\s*MALE\s*ANCHOR\s*\(Scene\s*(\d+)[:\s]*([^)]*)\)/i);
  if (maleHeaderMatch) {
    const sceneNum = parseInt(maleHeaderMatch[1], 10);
    const title = maleHeaderMatch[2]?.trim() || '';
    const scene = scenes.find(s => s.sceneNum === sceneNum);
    anchors.push({
      key: 'MALE',
      emoji: '👨',
      sceneNum,
      title,
      character: extractAnchorCharacter(content, 'MALE'),
      frameFile: scene?.frameFile || generateFrameFileName(sceneNum, scene?.beatTimestamp || ''),
    });
  }

  const femaleHeaderMatch = content.match(/###\s*👩\s*FEMALE\s*ANCHOR\s*\(Scene\s*(\d+)[:\s]*([^)]*)\)/i);
  if (femaleHeaderMatch) {
    const sceneNum = parseInt(femaleHeaderMatch[1], 10);
    const title = femaleHeaderMatch[2]?.trim() || '';
    const scene = scenes.find(s => s.sceneNum === sceneNum);
    anchors.push({
      key: 'FEMALE',
      emoji: '👩',
      sceneNum,
      title,
      character: extractAnchorCharacter(content, 'FEMALE'),
      frameFile: scene?.frameFile || generateFrameFileName(sceneNum, scene?.beatTimestamp || ''),
    });
  }

  // 2. Try table format: | 👨 MALE | Scene 02 | 청자켓 입은 남성 | 용도 |
  if (anchors.length === 0) {
    // Match MALE row in table
    const maleTableMatch = content.match(/\|\s*👨\s*MALE\s*\|\s*Scene\s*(\d+)\s*\|\s*([^|]+)\s*\|/i);
    if (maleTableMatch) {
      const sceneNum = parseInt(maleTableMatch[1], 10);
      const character = maleTableMatch[2]?.trim() || '';
      const scene = scenes.find(s => s.sceneNum === sceneNum);
      anchors.push({
        key: 'MALE',
        emoji: '👨',
        sceneNum,
        title: scene?.title || '',
        character: character || extractAnchorCharacter(content, 'MALE'),
        frameFile: scene?.frameFile || generateFrameFileName(sceneNum, scene?.beatTimestamp || ''),
      });
    }

    // Match FEMALE row in table
    const femaleTableMatch = content.match(/\|\s*👩\s*FEMALE\s*\|\s*Scene\s*(\d+)\s*\|\s*([^|]+)\s*\|/i);
    if (femaleTableMatch) {
      const sceneNum = parseInt(femaleTableMatch[1], 10);
      const character = femaleTableMatch[2]?.trim() || '';
      const scene = scenes.find(s => s.sceneNum === sceneNum);
      anchors.push({
        key: 'FEMALE',
        emoji: '👩',
        sceneNum,
        title: scene?.title || '',
        character: character || extractAnchorCharacter(content, 'FEMALE'),
        frameFile: scene?.frameFile || generateFrameFileName(sceneNum, scene?.beatTimestamp || ''),
      });
    }
  }

  // 3. Fallback: Extract from isAnchor scenes if no explicit anchor info found
  if (anchors.length === 0) {
    const anchorScenes = scenes.filter(s => s.isAnchor);
    for (const scene of anchorScenes) {
      // Determine anchor key based on content or default to MALE for first anchor
      const existingKeys = anchors.map(a => a.key);
      const key = existingKeys.includes('MALE') ? 'FEMALE' : 'MALE';
      anchors.push({
        key,
        emoji: key === 'MALE' ? '👨' : '👩',
        sceneNum: scene.sceneNum,
        title: scene.title,
        character: extractAnchorCharacter(content, key),
        frameFile: scene.frameFile,
      });
    }
  }

  return anchors;
}

/**
 * Collect all warnings for parsed scenes
 */
function collectWarnings(scenes: Builder2Scene[], rawContent: string): ParseWarning[] {
  const warnings: ParseWarning[] = [];

  // Split raw content into scene blocks for lazy pattern detection
  // Use flexible scene split: ## followed by optional emoji, then Scene
  const sceneBlockPattern = /(?=##\s*(?:📍\s*)?Scene\s*\d+)/i;
  const rawBlocks = rawContent.split(sceneBlockPattern);

  for (const scene of scenes) {
    // Find matching raw block for this scene
    const scenePattern = new RegExp(`Scene\\s*0?${scene.sceneNum}[:\\s]`, 'i');
    const matchingBlock = rawBlocks.find(b => scenePattern.test(b)) || '';

    // ANTI-LAZY detection
    warnings.push(...detectLazyPatterns(matchingBlock, scene.sceneNum));

    // MJ parameter validation
    warnings.push(...validateMJParams(scene.imagePrompts.midjourney, scene.sceneNum, scene.isAnchor));

    // Missing prompt warnings
    if (!scene.imagePrompts.nanoBanana && !scene.imagePrompts.midjourney) {
      warnings.push({
        sceneNum: scene.sceneNum,
        type: 'missing_prompt',
        message: 'IMAGE 프롬프트 없음 (NanoBanana + MJ 모두 빈 값)',
      });
    }
  }

  return warnings;
}

/**
 * Parse unified workflow format (v8.0)
 * New format: ## 📍 Scene XX + ### 🖼️ IMAGE + ### 🎥 MOTION
 * Also supports headers without 📍 emoji
 */
function parseUnifiedWorkflow(content: string): Builder2ParseResult {
  const result: Builder2ParseResult = {
    ohmageScenes: [],
    variationScenes: [],
    hasOhmage: false,
    hasVariation: false,
    anchorSceneNum: null,
    anchors: [],
    warnings: [],
  };

  // Check if this is a variation workflow
  const isVariation = content.includes('변주 워크플로우') || content.includes('VARIATION');

  // Parse anchor section for anchor scene numbers
  const anchorMatches = content.matchAll(/###\s*👨.*MALE.*Scene\s*(\d+)|###\s*👩.*FEMALE.*Scene\s*(\d+)/gi);
  const anchorSceneNums = new Set<number>();
  for (const match of anchorMatches) {
    const sceneNum = parseInt(match[1] || match[2], 10);
    if (!isNaN(sceneNum)) {
      anchorSceneNums.add(sceneNum);
      if (result.anchorSceneNum === null) {
        result.anchorSceneNum = sceneNum;
      }
    }
  }

  // Split by scene markers: ## 📍 Scene or ## Scene (emoji optional) or ## ⭐ (anchor section)
  const sceneBlocks = content.split(/(?=##\s*(?:📍\s*)?Scene\s+\d|##\s*⭐)/i);

  for (const block of sceneBlocks) {
    // Handle anchor scenes in ⭐ section
    if (block.match(/^##\s*⭐/)) {
      // Parse anchor scenes within the anchor section
      const anchorSceneBlocks = block.split(/(?=### 👨|### 👩)/);
      for (const anchorBlock of anchorSceneBlocks) {
        const sceneMatch = anchorBlock.match(/Scene\s*(\d+)/i);
        if (!sceneMatch) continue;

        const sceneNum = parseInt(sceneMatch[1], 10);
        const titleMatch = anchorBlock.match(/Scene\s*\d+[:\s]+([^\n()]+)/i);
        const title = titleMatch?.[1]?.trim() || `Anchor Scene ${sceneNum}`;

        // Extract prompts
        const imagePrompts = parseUnifiedImagePrompts(anchorBlock);
        const motionPrompts = parseUnifiedMotionPrompts(anchorBlock);
        const anchorRefInfo = parseRefTag(anchorBlock);

        const scene: Builder2Scene = {
          sceneNum,
          title,
          beatTimestamp: '',
          imagePrompts,
          motionPrompts,
          isAnchor: true,
          frameFile: generateFrameFileName(sceneNum, ''),
          anchorRefs: [], // Anchor scenes don't reference other anchors
          refInfo: anchorRefInfo,
        };

        if (isVariation) {
          result.variationScenes.push(scene);
        } else {
          result.ohmageScenes.push(scene);
        }
      }
      continue;
    }

    // Handle regular scenes - flexible header (📍 optional)
    const headerMatch = block.match(/##\s*(?:📍\s*)?Scene\s*(\d+)[:\s]+([^\n]+)/i);
    if (!headerMatch) continue;

    const sceneNum = parseInt(headerMatch[1], 10);
    const title = headerMatch[2].trim();

    // Extract timecode - flexible timestamp parsing (leading zero optional, fractional optional)
    let timestamp = '';
    // Pattern: supports "0:00.00", "00:00.00", "0:00", "00:00" formats
    const timestampMatch = block.match(/타임코드[:\s]*(\d+:\d+(?:\.\d+)?)~(\d+:\d+(?:\.\d+)?)/i);
    if (timestampMatch) {
      timestamp = `${timestampMatch[1]}~${timestampMatch[2]}`;
    } else {
      // Try inline format: Scene 01: Title (00:00.00~00:01.67) or (0:00~0:03)
      const inlineMatch = block.match(/\((\d+:\d+(?:\.\d+)?)[~-](\d+:\d+(?:\.\d+)?)\)/);
      if (inlineMatch) {
        timestamp = `${inlineMatch[1]}~${inlineMatch[2]}`;
      }
    }

    // Extract IMAGE section (flexible emoji matching)
    const imageSection = block.match(/###\s*(?:🖼️?\s*)?IMAGE\s*\n([\s\S]*?)(?=###\s*(?:🎥?\s*)?MOTION|##\s*(?:📍\s*)?Scene|## ✅|$)/i);
    const imagePrompts = imageSection
      ? parseUnifiedImagePrompts(imageSection[1])
      : parseUnifiedImagePrompts(block); // Fallback: search entire block

    // Extract MOTION section (flexible emoji matching)
    const motionSection = block.match(/###\s*(?:🎥?\s*)?MOTION\s*\n([\s\S]*?)(?=##\s*(?:📍\s*)?Scene|## ✅|$)/i);
    const motionPrompts = motionSection
      ? parseUnifiedMotionPrompts(motionSection[1])
      : parseUnifiedMotionPrompts(block); // Fallback: search entire block

    // Check if anchor
    const isAnchor = anchorSceneNums.has(sceneNum) ||
      block.toUpperCase().includes('ANCHOR') ||
      block.includes('앵커');

    const refInfo = parseRefTag(block);

    const scene: Builder2Scene = {
      sceneNum,
      title,
      beatTimestamp: timestamp,
      imagePrompts,
      motionPrompts,
      isAnchor,
      frameFile: generateFrameFileName(sceneNum, timestamp),
      anchorRefs: isAnchor ? [] : extractAnchorRefs(block),
      refInfo,
    };

    if (isVariation) {
      result.variationScenes.push(scene);
    } else {
      result.ohmageScenes.push(scene);
    }
  }

  // Sort scenes by number
  result.ohmageScenes.sort((a, b) => a.sceneNum - b.sceneNum);
  result.variationScenes.sort((a, b) => a.sceneNum - b.sceneNum);

  result.hasOhmage = result.ohmageScenes.length > 0;
  result.hasVariation = result.variationScenes.length > 0;

  // Parse anchor info after scenes are parsed (need scenes for frameFile lookup)
  const allScenes = [...result.ohmageScenes, ...result.variationScenes];
  result.anchors = parseAnchorInfo(content, allScenes);

  // Collect warnings
  result.warnings = collectWarnings(allScenes, content);

  return result;
}

/**
 * Parse complete Builder2 output
 * Supports both legacy <<<TAG>>> format and new v8.0 unified format
 */
export function parseBuilder2Output(content: string): Builder2ParseResult {
  const result: Builder2ParseResult = {
    ohmageScenes: [],
    variationScenes: [],
    hasOhmage: false,
    hasVariation: false,
    anchorSceneNum: null,
    anchors: [],
    warnings: [],
  };

  // 1. Try legacy <<<TAG>>> format first (backward compatibility)
  const ohmageImage = extractTagSection(content, "OHMAGE_IMAGE");
  const ohmageMotion = extractTagSection(content, "OHMAGE_MOTION");

  if (ohmageImage || ohmageMotion) {
    result.hasOhmage = true;
    let ohmageSceneMap = new Map<number, Builder2Scene>();

    if (ohmageImage) {
      ohmageSceneMap = parseImageSection(ohmageImage);
    }
    if (ohmageMotion) {
      ohmageSceneMap = parseMotionSection(ohmageMotion, ohmageSceneMap);
    }

    result.ohmageScenes = Array.from(ohmageSceneMap.values()).sort(
      (a, b) => a.sceneNum - b.sceneNum
    );

    // Parse Variation sections (legacy)
    const variationImage = extractTagSection(content, "VARIATION_IMAGE");
    const variationMotion = extractTagSection(content, "VARIATION_MOTION");

    if (variationImage || variationMotion) {
      result.hasVariation = true;
      let variationSceneMap = new Map<number, Builder2Scene>();

      if (variationImage) {
        variationSceneMap = parseImageSection(variationImage);
      }
      if (variationMotion) {
        variationSceneMap = parseMotionSection(variationMotion, variationSceneMap);
      }

      result.variationScenes = Array.from(variationSceneMap.values()).sort(
        (a, b) => a.sceneNum - b.sceneNum
      );
    }

    // Find anchor scene and parse anchor info for legacy format
    const allScenes = [...result.ohmageScenes, ...result.variationScenes];
    const anchorScene = allScenes.find((s) => s.isAnchor);
    if (anchorScene) {
      result.anchorSceneNum = anchorScene.sceneNum;
    }
    result.anchors = parseAnchorInfo(content, allScenes);

    // Collect warnings for legacy format too
    result.warnings = collectWarnings(allScenes, content);

    return result;
  }

  // 2. Try new v8.0 unified format (📍 emoji optional in detection)
  if (content.match(/##\s*(?:📍\s*)?Scene\s+\d/i) || content.includes('## ⭐') || content.includes('오마쥬 워크플로우')) {
    return parseUnifiedWorkflow(content);
  }

  // 3. Empty result if no format matched
  return result;
}

/**
 * Find anchor scene from parsed result
 */
export function findAnchorScene(
  result: Builder2ParseResult
): Builder2Scene | null {
  if (result.anchorSceneNum === null) return null;

  // Prefer ohmage scenes
  const ohmageAnchor = result.ohmageScenes.find(
    (s) => s.sceneNum === result.anchorSceneNum
  );
  if (ohmageAnchor) return ohmageAnchor;

  // Fallback to variation
  return (
    result.variationScenes.find(
      (s) => s.sceneNum === result.anchorSceneNum
    ) || null
  );
}

/**
 * Insert --cref/--oref URL into Midjourney prompt if placeholder exists
 * Supports both legacy --cref (V6) and V7 --oref
 */
export function insertCrefUrl(prompt: string, crefUrl: string): string {
  if (!crefUrl.trim()) return prompt;

  // Replace placeholder like [ANCHOR_URL], [MALE_ANCHOR_URL], [FEMALE_ANCHOR_URL]
  let result = prompt
    .replace(/\[(?:MALE_|FEMALE_)?ANCHOR_URL\]/gi, crefUrl)
    .replace(/--(?:cref|oref)\s*\[URL\]/gi, (match) => {
      const param = match.startsWith('--oref') ? '--oref' : '--cref';
      return `${param} ${crefUrl}`;
    });

  // If no placeholder found but prompt has --oref/--cref without URL, add URL
  if (result === prompt) {
    if (result.includes("--oref")) {
      result = result.replace(/--oref(?!\s+http)/i, `--oref ${crefUrl}`);
    } else if (result.includes("--cref")) {
      result = result.replace(/--cref(?!\s+http)/i, `--cref ${crefUrl}`);
    }
  }

  // If no --oref or --cref at all, add --oref (V7 default) before --ar or at end
  if (!result.includes("--cref") && !result.includes("--oref")) {
    if (result.includes("--ar")) {
      result = result.replace("--ar", `--oref ${crefUrl} --ar`);
    } else {
      result = `${result} --oref ${crefUrl}`;
    }
  }

  return result;
}

/**
 * Get warnings for a specific scene
 */
export function getSceneWarnings(warnings: ParseWarning[], sceneNum: number): ParseWarning[] {
  return warnings.filter(w => w.sceneNum === sceneNum);
}

/**
 * Get scene statistics
 */
export function getBuilder2Stats(result: Builder2ParseResult): {
  totalOhmage: number;
  totalVariation: number;
  hasAnchor: boolean;
  completeness: {
    ohmageImage: number;
    ohmageMotion: number;
    variationImage: number;
    variationMotion: number;
  };
} {
  const countComplete = (
    scenes: Builder2Scene[],
    type: "image" | "motion"
  ): number => {
    return scenes.filter((s) => {
      if (type === "image") {
        return s.imagePrompts.nanoBanana || s.imagePrompts.midjourney;
      }
      return s.motionPrompts.kling || s.motionPrompts.veo;
    }).length;
  };

  return {
    totalOhmage: result.ohmageScenes.length,
    totalVariation: result.variationScenes.length,
    hasAnchor: result.anchorSceneNum !== null,
    completeness: {
      ohmageImage: countComplete(result.ohmageScenes, "image"),
      ohmageMotion: countComplete(result.ohmageScenes, "motion"),
      variationImage: countComplete(result.variationScenes, "image"),
      variationMotion: countComplete(result.variationScenes, "motion"),
    },
  };
}
