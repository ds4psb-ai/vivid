/**
 * Builder2 MD Parser
 *
 * Parses Builder2 (Parody Engine) output format.
 * Extracts scenes with IMAGE/MOTION prompts from delimited sections.
 *
 * Delimiter Tags:
 * - <<<OHMAGE_IMAGE_START>>> ~ <<<OHMAGE_IMAGE_END>>>
 * - <<<OHMAGE_MOTION_START>>> ~ <<<OHMAGE_MOTION_END>>>
 * - <<<VARIATION_IMAGE_START>>> ~ <<<VARIATION_IMAGE_END>>>
 * - <<<VARIATION_MOTION_START>>> ~ <<<VARIATION_MOTION_END>>>
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
}

export interface Builder2ParseResult {
  ohmageScenes: Builder2Scene[];
  variationScenes: Builder2Scene[];
  hasOhmage: boolean;
  hasVariation: boolean;
  anchorSceneNum: number | null;
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
      existingScenes.set(sceneNum, {
        sceneNum,
        title: titleMatch?.[1]?.trim() || `Scene ${sceneNum}`,
        beatTimestamp: titleMatch?.[2]?.trim() || "",
        imagePrompts: { nanoBanana: "", midjourney: "" },
        motionPrompts: { kling, veo },
        isAnchor:
          block.toUpperCase().includes("ANCHOR") ||
          block.includes("(ANCHOR)"),
      });
    }
  }

  return existingScenes;
}

/**
 * Parse IMAGE prompts from unified format block
 */
function parseUnifiedImagePrompts(content: string): { nanoBanana: string; midjourney: string } {
  const nanoBananaMatch = content.match(
    /NanoBanana[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );
  const midjourneyMatch = content.match(
    /Midjourney[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );

  return {
    nanoBanana: nanoBananaMatch?.[1]?.trim() || '',
    midjourney: midjourneyMatch?.[1]?.trim() || '',
  };
}

/**
 * Parse MOTION prompts from unified format block
 */
function parseUnifiedMotionPrompts(content: string): { kling: string; veo: string } {
  const klingMatch = content.match(
    /Kling[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );
  const veoMatch = content.match(
    /Veo[^\n]*\n```(?:text)?\s*\n?([\s\S]*?)```/i
  );

  return {
    kling: klingMatch?.[1]?.trim() || '',
    veo: veoMatch?.[1]?.trim() || '',
  };
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
        const titleMatch = anchorBlock.match(/Scene\s*\d+[:\s]+([^\n(]+)/i);
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

    // Extract timecode
    const timestampMatch = block.match(/타임코드[:\s]*(\d+:\d+\.\d+)~(\d+:\d+\.\d+)/i);
    const timestamp = timestampMatch
      ? `${timestampMatch[1]}~${timestampMatch[2]}`
      : '';

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

    // Find anchor scene
    const allScenes = [...result.ohmageScenes, ...result.variationScenes];
    const anchorScene = allScenes.find((s) => s.isAnchor);
    if (anchorScene) {
      result.anchorSceneNum = anchorScene.sceneNum;
    }

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
