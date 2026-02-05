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
}

export interface AnchorInfo {
  key: string;           // "MALE", "FEMALE"
  emoji: string;         // "👨", "👩"
  sceneNum: number;      // 2, 5
  title: string;         // "기다림", "미소"
  character: string;     // "청자켓 입은 한국인 남성"
  frameFile: string;     // "frame_02_00-01.67.jpg"
}

export interface Builder2ParseResult {
  ohmageScenes: Builder2Scene[];
  variationScenes: Builder2Scene[];
  hasOhmage: boolean;
  hasVariation: boolean;
  anchorSceneNum: number | null;
  anchors: AnchorInfo[];  // 앵커 정보 목록
}

type TagName =
  | "OHMAGE_IMAGE"
  | "OHMAGE_MOTION"
  | "VARIATION_IMAGE"
  | "VARIATION_MOTION";

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
  // Check for various anchor reference patterns
  if (block.includes('[MALE_ANCHOR') ||
      block.includes('MALE ANCHOR') ||
      block.includes('[Image 2: CHARACTER FACE]') && block.toLowerCase().includes('male')) {
    refs.push('MALE');
  }
  if (block.includes('[FEMALE_ANCHOR') ||
      block.includes('FEMALE ANCHOR') ||
      block.includes('[Image 2: CHARACTER FACE]') && block.toLowerCase().includes('female')) {
    refs.push('FEMALE');
  }
  // Generic anchor reference
  if (refs.length === 0 &&
      (block.includes('[ANCHOR') ||
       block.includes('--cref') ||
       (block.includes('[Image 2:') && block.includes('ANCHOR')))) {
    refs.push('MALE'); // Default to MALE if generic anchor reference
  }
  return refs;
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

    // Extract NanoBanana prompt
    let nanoBanana = "";
    const nanoBananaMatch = block.match(
      /(?:\[📋\s*COPY\]|NanoBanana)[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
    );
    if (nanoBananaMatch) {
      nanoBanana = nanoBananaMatch[1].trim();
    }

    // Extract Midjourney prompt (comes after NanoBanana)
    let midjourney = "";
    const midjourneyMatch = block.match(
      /(?:Midjourney|MJ)[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
    );
    if (midjourneyMatch) {
      midjourney = midjourneyMatch[1].trim();
    }

    scenes.set(sceneNum, {
      sceneNum,
      title,
      beatTimestamp: timestamp,
      imagePrompts: { nanoBanana, midjourney },
      motionPrompts: { kling: "", veo: "" },
      isAnchor,
      frameFile: generateFrameFileName(sceneNum, timestamp),
      anchorRefs: extractAnchorRefs(block),
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

    // Extract Kling prompt
    let kling = "";
    const klingMatch = block.match(
      /(?:\[📋\s*COPY\]|Kling)[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
    );
    if (klingMatch) {
      kling = klingMatch[1].trim();
    }

    // Extract Veo prompt
    let veo = "";
    const veoMatch = block.match(
      /(?:Veo)[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
    );
    if (veoMatch) {
      veo = veoMatch[1].trim();
    }

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
 */
function parseUnifiedImagePrompts(content: string): { nanoBanana: string; midjourney: string } {
  // Try [📋 COPY] NanoBanana format first, then direct NanoBanana
  const nanoBananaMatch = content.match(
    /(?:\[📋\s*COPY\]\s*)?NanoBanana[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );
  // Try [📋 COPY] Midjourney format first, then direct Midjourney/MJ
  const midjourneyMatch = content.match(
    /(?:\[📋\s*COPY\]\s*)?(?:Midjourney|MJ)[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );

  return {
    nanoBanana: nanoBananaMatch?.[1]?.trim() || '',
    midjourney: midjourneyMatch?.[1]?.trim() || '',
  };
}

/**
 * Parse MOTION prompts from unified format block
 * Supports both direct tool names and [📋 COPY] markers
 */
function parseUnifiedMotionPrompts(content: string): { kling: string; veo: string } {
  // Try [📋 COPY] Kling format first, then direct Kling
  const klingMatch = content.match(
    /(?:\[📋\s*COPY\]\s*)?Kling[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );
  // Try [📋 COPY] Veo format first, then direct Veo
  const veoMatch = content.match(
    /(?:\[📋\s*COPY\]\s*)?Veo[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );

  return {
    kling: klingMatch?.[1]?.trim() || '',
    veo: veoMatch?.[1]?.trim() || '',
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
 * Parse unified workflow format (v8.0)
 * New format: ## 📍 Scene XX + ### 🖼️ IMAGE + ### 🎥 MOTION
 */
function parseUnifiedWorkflow(content: string): Builder2ParseResult {
  const result: Builder2ParseResult = {
    ohmageScenes: [],
    variationScenes: [],
    hasOhmage: false,
    hasVariation: false,
    anchorSceneNum: null,
    anchors: [],
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

  // Split by scene markers: ## 📍 Scene or ## ⭐ (anchor section)
  const sceneBlocks = content.split(/(?=## 📍 Scene|## ⭐)/i);

  for (const block of sceneBlocks) {
    // Handle anchor scenes in ⭐ section
    if (block.includes('## ⭐')) {
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

        const scene: Builder2Scene = {
          sceneNum,
          title,
          beatTimestamp: '',
          imagePrompts,
          motionPrompts,
          isAnchor: true,
          frameFile: generateFrameFileName(sceneNum, ''),
          anchorRefs: [], // Anchor scenes don't reference other anchors
        };

        if (isVariation) {
          result.variationScenes.push(scene);
        } else {
          result.ohmageScenes.push(scene);
        }
      }
      continue;
    }

    // Handle regular scenes
    if (!block.includes('## 📍 Scene')) continue;

    // Extract scene header
    const headerMatch = block.match(/## 📍 Scene\s*(\d+)[:\s]+([^\n]+)/i);
    if (!headerMatch) continue;

    const sceneNum = parseInt(headerMatch[1], 10);
    const title = headerMatch[2].trim();

    // Extract timecode - supports both "타임코드:" and inline "(00:00.00~00:01.67)" formats
    let timestamp = '';
    const timestampMatch = block.match(/타임코드[:\s]*(\d+:\d+\.\d+)~(\d+:\d+\.\d+)/i);
    if (timestampMatch) {
      timestamp = `${timestampMatch[1]}~${timestampMatch[2]}`;
    } else {
      // Try inline format: Scene 01: Title (00:00.00~00:01.67)
      const inlineMatch = block.match(/\((\d+:\d+\.\d+)[~-](\d+:\d+\.\d+)\)/);
      if (inlineMatch) {
        timestamp = `${inlineMatch[1]}~${inlineMatch[2]}`;
      }
    }

    // Extract IMAGE section
    const imageSection = block.match(/### 🖼️ IMAGE\s*\n([\s\S]*?)(?=### 🎥|## 📍|## ✅|$)/i);
    const imagePrompts = imageSection
      ? parseUnifiedImagePrompts(imageSection[1])
      : parseUnifiedImagePrompts(block); // Fallback: search entire block

    // Extract MOTION section
    const motionSection = block.match(/### 🎥 MOTION\s*\n([\s\S]*?)(?=## 📍|## ✅|$)/i);
    const motionPrompts = motionSection
      ? parseUnifiedMotionPrompts(motionSection[1])
      : parseUnifiedMotionPrompts(block); // Fallback: search entire block

    // Check if anchor
    const isAnchor = anchorSceneNums.has(sceneNum) ||
      block.toUpperCase().includes('ANCHOR') ||
      block.includes('앵커');

    const scene: Builder2Scene = {
      sceneNum,
      title,
      beatTimestamp: timestamp,
      imagePrompts,
      motionPrompts,
      isAnchor,
      frameFile: generateFrameFileName(sceneNum, timestamp),
      anchorRefs: isAnchor ? [] : extractAnchorRefs(block),
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

    return result;
  }

  // 2. Try new v8.0 unified format
  if (content.includes('## 📍 Scene') || content.includes('## ⭐') || content.includes('오마쥬 워크플로우')) {
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
 * Insert --cref URL into Midjourney prompt if placeholder exists
 */
export function insertCrefUrl(prompt: string, crefUrl: string): string {
  if (!crefUrl.trim()) return prompt;

  // Replace placeholder like [ANCHOR_URL] or --cref [URL]
  let result = prompt
    .replace(/\[ANCHOR_URL\]/gi, crefUrl)
    .replace(/--cref\s*\[URL\]/gi, `--cref ${crefUrl}`);

  // If no placeholder found but prompt has --cref without URL, add URL
  if (result === prompt && result.includes("--cref")) {
    result = result.replace(/--cref(?!\s+http)/i, `--cref ${crefUrl}`);
  }

  // If no --cref at all, add it before --ar or at end
  if (!result.includes("--cref")) {
    if (result.includes("--ar")) {
      result = result.replace("--ar", `--cref ${crefUrl} --ar`);
    } else {
      result = `${result} --cref ${crefUrl}`;
    }
  }

  return result;
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
