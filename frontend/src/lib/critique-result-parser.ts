/**
 * Critique Result Parser
 *
 * Parses AI critique output (from Gemini/Claude) and extracts structured data.
 * Designed for copy-paste workflow - no API calls.
 */

export interface CritiqueScores {
  identity_accuracy?: number;
  composition_match?: number;
  color_consistency?: number;
  era_authenticity?: number;
  anchor_similarity?: number;
  motion_naturalness?: number;
  face_consistency?: number;
  artifact_free?: number;
  timing_accuracy?: number;
  source_fidelity?: number;
}

export interface ParsedCritiqueResult {
  sceneId: string;
  critiqueType: "image" | "video";
  scores: CritiqueScores;
  totalScore: number;
  verdict: "PASS" | "REVISE" | "REJECT";
  issues: string[];
  suggestions: string[];
  rawJson?: string;
}

/**
 * Parse critique result from AI output
 */
export function parseCritiqueResult(
  aiOutput: string
): ParsedCritiqueResult | null {
  // Try to find JSON block in the output
  const jsonMatch = aiOutput.match(/```json\s*([\s\S]*?)\s*```/);

  if (jsonMatch) {
    try {
      const jsonStr = jsonMatch[1].trim();
      const parsed = JSON.parse(jsonStr);

      // Handle both single object and array
      const item = Array.isArray(parsed) ? parsed[0] : parsed;

      if (!item) return null;

      return {
        sceneId: item.scene_id || "",
        critiqueType: item.critique_type || "image",
        scores: item.scores || {},
        totalScore: item.total_score || 0,
        verdict: normalizeVerdict(item.verdict),
        issues: item.issues || [],
        suggestions: item.suggestions || [],
        rawJson: jsonStr,
      };
    } catch {
      // JSON parsing failed, try manual extraction
    }
  }

  // Try manual extraction if JSON parsing fails
  return parseManually(aiOutput);
}

/**
 * Parse multiple critique results from batch output
 */
export function parseBatchCritiqueResults(
  aiOutput: string
): ParsedCritiqueResult[] {
  const results: ParsedCritiqueResult[] = [];

  // Try to find JSON array
  const jsonMatch = aiOutput.match(/```json\s*([\s\S]*?)\s*```/);

  if (jsonMatch) {
    try {
      const jsonStr = jsonMatch[1].trim();
      const parsed = JSON.parse(jsonStr);

      if (Array.isArray(parsed)) {
        for (const item of parsed) {
          results.push({
            sceneId: item.scene_id || "",
            critiqueType: item.critique_type || "image",
            scores: item.scores || {},
            totalScore: item.total_score || 0,
            verdict: normalizeVerdict(item.verdict),
            issues: item.issues || [],
            suggestions: item.suggestions || [],
          });
        }
      }
    } catch {
      // JSON parsing failed
    }
  }

  return results;
}

/**
 * Normalize verdict string
 */
function normalizeVerdict(verdict: string): "PASS" | "REVISE" | "REJECT" {
  const upper = (verdict || "").toUpperCase().trim();
  if (upper.includes("PASS")) return "PASS";
  if (upper.includes("REVISE")) return "REVISE";
  if (upper.includes("REJECT")) return "REJECT";
  return "REVISE"; // Default to REVISE if unclear
}

/**
 * Manual parsing fallback
 */
function parseManually(text: string): ParsedCritiqueResult | null {
  const scores: CritiqueScores = {};

  // Extract scores from patterns like "인물 정확도: 85/100" or "Identity Accuracy: 85"
  const scorePatterns = [
    { key: "identity_accuracy", patterns: ["인물 정확도", "Identity Accuracy"] },
    { key: "composition_match", patterns: ["구도 일치", "Composition Match"] },
    { key: "color_consistency", patterns: ["색감 일관성", "Color Consistency"] },
    { key: "era_authenticity", patterns: ["시대 재현", "Era Authenticity"] },
    { key: "anchor_similarity", patterns: ["ANCHOR 유사도", "Anchor Similarity"] },
    { key: "motion_naturalness", patterns: ["모션 자연스러움", "Motion Naturalness"] },
    { key: "face_consistency", patterns: ["얼굴 일관성", "Face Consistency"] },
    { key: "artifact_free", patterns: ["아티팩트 없음", "Artifact-Free", "Artifact Free"] },
    { key: "timing_accuracy", patterns: ["타이밍 정확도", "Timing Accuracy"] },
    { key: "source_fidelity", patterns: ["원본 충실도", "Source Fidelity"] },
  ];

  for (const { key, patterns } of scorePatterns) {
    for (const pattern of patterns) {
      const regex = new RegExp(`${pattern}[:\\s]+[\\*]*\\s*(\\d+)`, "i");
      const match = text.match(regex);
      if (match) {
        scores[key as keyof CritiqueScores] = parseInt(match[1]);
        break;
      }
    }
  }

  // Extract total score
  let totalScore = 0;
  const totalMatch = text.match(/(?:총점|Total|Score)[:\s]+\**\s*(\d+)/i);
  if (totalMatch) {
    totalScore = parseInt(totalMatch[1]);
  } else {
    // Calculate from individual scores
    const scoreValues = Object.values(scores).filter(
      (v) => typeof v === "number"
    ) as number[];
    if (scoreValues.length > 0) {
      totalScore = Math.round(
        scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length
      );
    }
  }

  // Extract verdict
  let verdict: "PASS" | "REVISE" | "REJECT" = "REVISE";
  if (text.includes("PASS") || text.includes("✅")) {
    verdict = "PASS";
  } else if (text.includes("REJECT") || text.includes("❌")) {
    verdict = "REJECT";
  }

  // Extract issues
  const issues: string[] = [];
  const issueSection = text.match(
    /(?:주요 문제점|Issues?|Problems?)[:\s]*([\s\S]*?)(?=\n\n|\n##|개선|Suggestion|$)/i
  );
  if (issueSection) {
    const issueLines = issueSection[1]
      .split("\n")
      .filter((l) => l.trim().match(/^[\d\-\*\•]/))
      .map((l) => l.replace(/^[\d\-\*\•\.]+\s*/, "").trim())
      .filter(Boolean);
    issues.push(...issueLines);
  }

  // Extract suggestions
  const suggestions: string[] = [];
  const suggestionSection = text.match(
    /(?:개선 제안|Suggestions?|Improvements?)[:\s]*([\s\S]*?)(?=\n\n|\n##|$)/i
  );
  if (suggestionSection) {
    const suggestionLines = suggestionSection[1]
      .split("\n")
      .filter((l) => l.trim().match(/^[\d\-\*\•]/))
      .map((l) => l.replace(/^[\d\-\*\•\.]+\s*/, "").trim())
      .filter(Boolean);
    suggestions.push(...suggestionLines);
  }

  // Extract scene ID
  let sceneId = "";
  const sceneMatch = text.match(/Scene\s*(\d+)/i);
  if (sceneMatch) {
    sceneId = `scene${sceneMatch[1]}`;
  }

  if (Object.keys(scores).length === 0 && totalScore === 0) {
    return null;
  }

  return {
    sceneId,
    critiqueType: text.toLowerCase().includes("video") ? "video" : "image",
    scores,
    totalScore,
    verdict,
    issues,
    suggestions,
  };
}

/**
 * Calculate weighted total score
 */
export function calculateWeightedScore(
  scores: CritiqueScores,
  critiqueType: "image" | "video"
): number {
  const weights =
    critiqueType === "image"
      ? {
          identity_accuracy: 25,
          composition_match: 20,
          color_consistency: 20,
          era_authenticity: 15,
          anchor_similarity: 20,
        }
      : {
          motion_naturalness: 25,
          face_consistency: 25,
          artifact_free: 20,
          timing_accuracy: 15,
          source_fidelity: 15,
        };

  let totalWeight = 0;
  let weightedSum = 0;

  for (const [key, weight] of Object.entries(weights)) {
    const score = scores[key as keyof CritiqueScores];
    if (typeof score === "number") {
      weightedSum += score * weight;
      totalWeight += weight;
    }
  }

  return totalWeight > 0 ? Math.round(weightedSum / totalWeight) : 0;
}

/**
 * Determine verdict from score
 */
export function getVerdictFromScore(
  score: number
): "PASS" | "REVISE" | "REJECT" {
  if (score >= 85) return "PASS";
  if (score >= 60) return "REVISE";
  return "REJECT";
}
