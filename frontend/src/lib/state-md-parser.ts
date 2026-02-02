/**
 * STATE.md Parser
 *
 * Parses the STATE.md markdown file format used in Prompty projects.
 * Extracts scene progress, overall progress, current task, and metadata.
 */

export interface SceneProgress {
  scene: number;
  description: string;
  image: string | null;
  video: string | null;
  status: "✅" | "🔄" | "⬜";
  isAnchor: boolean;
}

export interface StageProgress {
  stage: string;
  name: string;
  percent: number;
  barFilled: number;
  barEmpty: number;
}

export interface Blocker {
  issue: string;
  status: string;
  solution: string;
}

export interface Decision {
  date: string;
  decision: string;
  reason: string;
}

export interface ParsedState {
  projectName: string | null;
  scenes: SceneProgress[];
  overallProgress: StageProgress[];
  currentTask: string | null;
  lastConversation: string | null;
  sessionNotes: string[];
  blockers: Blocker[];
  decisions: Decision[];
  lastUpdated: string | null;
  quickResumePrompt: string | null;
}

/**
 * Default empty state for error recovery
 */
const DEFAULT_STATE: ParsedState = {
  projectName: null,
  scenes: [],
  overallProgress: [],
  currentTask: null,
  lastConversation: null,
  sessionNotes: [],
  blockers: [],
  decisions: [],
  lastUpdated: null,
  quickResumePrompt: null,
};

/**
 * Parse STATUS.md content into structured data
 */
export function parseStateMd(content: string): ParsedState {
  try {
    return parseStateMdInternal(content);
  } catch (error) {
    console.error("STATE.md parsing failed:", error);
    return { ...DEFAULT_STATE };
  }
}

/**
 * Internal parser (wrapped by try-catch in parseStateMd)
 */
function parseStateMdInternal(content: string): ParsedState {
  const result: ParsedState = { ...DEFAULT_STATE };

  // Extract project name from title
  const titleMatch = content.match(/^#\s+State:\s*(.+)$/m);
  if (titleMatch) {
    result.projectName = titleMatch[1].trim();
  }

  // Extract Last Updated
  const updatedMatch = content.match(/\*\*Last Updated\*\*:\s*([^\n]+)/);
  if (updatedMatch) {
    result.lastUpdated = updatedMatch[1].trim();
  }

  // Parse Scene Progress table
  result.scenes = parseSceneProgressTable(content);

  // Parse Overall Progress bars
  result.overallProgress = parseOverallProgress(content);

  // Parse Current Task
  const currentTaskSection = extractSection(content, "Current Task");
  if (currentTaskSection) {
    // Extract the bold task name or first paragraph
    const taskMatch = currentTaskSection.match(/\*\*([^*]+)\*\*/);
    if (taskMatch) {
      result.currentTask = taskMatch[1].trim();
    } else {
      const lines = currentTaskSection
        .split("\n")
        .filter((l) => l.trim() && !l.startsWith("#"));
      if (lines.length > 0) {
        result.currentTask = lines[0].trim();
      }
    }
  }

  // Parse Last Conversation Summary
  const conversationSection = extractSection(
    content,
    "Last Conversation Summary"
  );
  if (conversationSection) {
    const codeBlockMatch = conversationSection.match(/```[\s\S]*?```/);
    if (codeBlockMatch) {
      result.lastConversation = codeBlockMatch[0]
        .replace(/```/g, "")
        .trim();
    }
  }

  // Parse Session Notes
  const sessionSection = extractSection(content, "Session Notes");
  if (sessionSection) {
    const noteMatches = sessionSection.matchAll(
      /###\s+(\d{4}-\d{2}-\d{2})\n([\s\S]*?)(?=###|\n---|\n##|$)/g
    );
    for (const match of noteMatches) {
      const date = match[1];
      const notes = match[2]
        .split("\n")
        .filter((l) => l.trim().startsWith("-"))
        .map((l) => `[${date}] ${l.replace(/^-\s*/, "").trim()}`);
      result.sessionNotes.push(...notes);
    }
  }

  // Parse Blockers
  result.blockers = parseBlockersTable(content);

  // Parse Decisions Made
  result.decisions = parseDecisionsTable(content);

  // Parse Quick Resume Prompt
  const resumeSection = extractSection(content, "Quick Resume Prompt");
  if (resumeSection) {
    const codeBlockMatch = resumeSection.match(/```[\s\S]*?```/);
    if (codeBlockMatch) {
      result.quickResumePrompt = codeBlockMatch[0]
        .replace(/```/g, "")
        .trim()
        .replace(/^["']|["']$/g, ""); // Remove quotes
    }
  }

  return result;
}

/**
 * Parse Scene Progress table
 */
function parseSceneProgressTable(content: string): SceneProgress[] {
  const scenes: SceneProgress[] = [];

  // Find the Scene Progress section
  const section = extractSection(content, "Scene Progress");
  if (!section) return scenes;

  // Find table rows
  const tableMatch = section.match(
    /\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|/g
  );
  if (!tableMatch) return scenes;

  // Skip header and separator rows
  const dataRows = tableMatch.slice(2);

  for (const row of dataRows) {
    const cols = row
      .split("|")
      .map((c) => c.trim())
      .filter(Boolean);
    if (cols.length < 5) continue;

    const sceneNum = parseInt(cols[0], 10) || 0;
    if (sceneNum === 0) continue;

    const description = cols[1] || "-";
    const image = cols[2] === "-" ? null : cols[2];
    const video = cols[3] === "-" ? null : cols[3];
    const statusCol = cols[4];

    let status: SceneProgress["status"] = "⬜";
    if (statusCol.includes("✅") || statusCol.toLowerCase().includes("확정")) {
      status = "✅";
    } else if (
      statusCol.includes("🔄") ||
      statusCol.toLowerCase().includes("진행")
    ) {
      status = "🔄";
    }

    const isAnchor =
      description.toUpperCase().includes("ANCHOR") ||
      description.includes("앵커");

    scenes.push({
      scene: sceneNum,
      description,
      image,
      video,
      status,
      isAnchor,
    });
  }

  return scenes;
}

/**
 * Parse Overall Progress bars
 */
function parseOverallProgress(content: string): StageProgress[] {
  const progress: StageProgress[] = [];

  // Match progress bar patterns like:
  // Stage 1 (Analysis):  ████████████████████ 100%
  // Stage 2 (Image):     ████████░░░░░░░░░░░░  40%
  const progressMatches = content.matchAll(
    /Stage\s+(\d)\s*\(([^)]+)\):\s*([█░]+)\s*(\d+)%/g
  );

  for (const match of progressMatches) {
    const stageNum = match[1];
    const stageName = match[2].trim();
    const bar = match[3];
    const percent = parseInt(match[4], 10) || 0;

    const filled = (bar.match(/█/g) || []).length;
    const empty = (bar.match(/░/g) || []).length;

    progress.push({
      stage: `Stage ${stageNum}`,
      name: stageName,
      percent,
      barFilled: filled,
      barEmpty: empty,
    });
  }

  return progress;
}

/**
 * Parse Blockers table
 */
function parseBlockersTable(content: string): Blocker[] {
  const blockers: Blocker[] = [];

  const section = extractSection(content, "Blockers");
  if (!section) return blockers;

  const tableMatch = section.match(/\|[^|]+\|[^|]+\|[^|]+\|/g);
  if (!tableMatch) return blockers;

  const dataRows = tableMatch.slice(2);

  for (const row of dataRows) {
    const cols = row
      .split("|")
      .map((c) => c.trim())
      .filter(Boolean);
    if (cols.length < 3 || cols[0] === "-") continue;

    blockers.push({
      issue: cols[0],
      status: cols[1],
      solution: cols[2],
    });
  }

  return blockers;
}

/**
 * Parse Decisions Made table
 */
function parseDecisionsTable(content: string): Decision[] {
  const decisions: Decision[] = [];

  const section = extractSection(content, "Decisions Made");
  if (!section) return decisions;

  const tableMatch = section.match(/\|[^|]+\|[^|]+\|[^|]+\|/g);
  if (!tableMatch) return decisions;

  const dataRows = tableMatch.slice(2);

  for (const row of dataRows) {
    const cols = row
      .split("|")
      .map((c) => c.trim())
      .filter(Boolean);
    if (cols.length < 3 || cols[0] === "-") continue;

    decisions.push({
      date: cols[0],
      decision: cols[1],
      reason: cols[2],
    });
  }

  return decisions;
}

/**
 * Extract a section by header name
 */
function extractSection(content: string, headerName: string): string | null {
  // Match ## or ### headers
  const escapedName = headerName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(
    `##[#]?\\s*[🚧📊📈💬📝📌🔖✅]*\\s*${escapedName}[\\s\\S]*?(?=\\n---\\n|\\n##[^#]|$)`,
    "i"
  );
  const match = content.match(regex);
  return match ? match[0] : null;
}

/**
 * Calculate overall completion percentage
 */
export function calculateOverallCompletion(parsed: ParsedState): number {
  if (parsed.overallProgress.length === 0) return 0;

  const total = parsed.overallProgress.reduce((sum, p) => sum + p.percent, 0);
  return Math.round(total / parsed.overallProgress.length);
}

/**
 * Get scene statistics
 */
export function getSceneStats(parsed: ParsedState): {
  total: number;
  completed: number;
  inProgress: number;
  pending: number;
} {
  return {
    total: parsed.scenes.length,
    completed: parsed.scenes.filter((s) => s.status === "✅").length,
    inProgress: parsed.scenes.filter((s) => s.status === "🔄").length,
    pending: parsed.scenes.filter((s) => s.status === "⬜").length,
  };
}

/**
 * Find ANCHOR scene
 */
export function findAnchorScene(parsed: ParsedState): SceneProgress | null {
  return parsed.scenes.find((s) => s.isAnchor) || null;
}

/**
 * Convert parsed state to JSON for API
 */
export function parsedStateToJson(parsed: ParsedState): object {
  return {
    project_name: parsed.projectName,
    last_updated: parsed.lastUpdated,
    current_task: parsed.currentTask,
    scenes: parsed.scenes.map((s) => ({
      scene_number: s.scene,
      description: s.description,
      image_path: s.image,
      video_path: s.video,
      status: s.status === "✅" ? "completed" : s.status === "🔄" ? "in_progress" : "pending",
      is_anchor: s.isAnchor,
    })),
    overall_progress: parsed.overallProgress.map((p) => ({
      stage: p.stage,
      name: p.name,
      percent: p.percent,
    })),
    blockers: parsed.blockers,
    decisions: parsed.decisions,
    session_notes: parsed.sessionNotes,
  };
}
