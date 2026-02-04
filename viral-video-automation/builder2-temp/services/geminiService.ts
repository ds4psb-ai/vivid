import { GoogleGenAI, Chat, ThinkingMode } from "@google/genai";
import { GEMINI_MODEL, SYSTEM_PROMPT_TEMPLATE } from "../constants";
import { OutputMode } from "../types";

/**
 * Converts a File object to a Base64 string.
 */
const fileToGenerativePart = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result as string;
      const base64Data = base64String.split(",")[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

// Store the chat session and file data in memory to re-send video at each step
let currentChat: Chat | null = null;
let currentFileBase64: { mimeType: string; data: string } | null = null;

// Cached context for deferred injection (STEP 3)
let cachedPersonaJson: string | null = null;
let cachedBestComments: string[] = [];

export const startAnalysisChat = async (
  file: File,
  builder1Output: string,
  bestComments: string[],
  personaJson: string | null,
  mode: OutputMode
): Promise<string> => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) throw new Error("API Key is not configured in process.env.API_KEY");

  const ai = new GoogleGenAI({ apiKey });
  const base64Data = await fileToGenerativePart(file);

  // Cache the file data
  currentFileBase64 = {
    mimeType: file.type,
    data: base64Data
  };

  // Cache Persona and Best Comments for deferred injection in STEP 3
  cachedPersonaJson = personaJson;
  cachedBestComments = bestComments;

  const finalSystemPrompt = SYSTEM_PROMPT_TEMPLATE.replace("{{MODE}}", mode);

  // Initialize Chat with Gemini 3 Pro optimized settings + ThinkingMode
  currentChat = ai.chats.create({
    model: GEMINI_MODEL,
    config: {
      systemInstruction: finalSystemPrompt,
      temperature: 0.2,
      maxOutputTokens: 32000, // Reduced from 64000 for input splitting
      mediaResolution: 'high', // Better frame analysis (10 FPS)
      thinkingConfig: {
        thinkingMode: ThinkingMode.ENABLED,
      },
    },
  });

  // STEP 1: Only send video + Builder 1 output (Persona and comments deferred to STEP 3)
  const contextMessage = `
Here are the inputs for the project:

**Builder 1 Output (IMAGE_PROMPTS.md):**
\`\`\`markdown
${builder1Output}
\`\`\`

Start the analysis. Proceed with **STEP 1: TEXT REPRODUCIBILITY CHECK**.

Your goal: Verify that the Builder 1 text prompts can **reproduce the video WITHOUT the video file**.

Check each scene for:
- **구도 (Composition)**: Camera angle, framing, vanishing point
- **인물 (Characters)**: Face features, clothing, positioning
- **조명 (Lighting)**: Color temperature, shadows, contrast
- **동작 (Actions)**: Start/end actions, timing
- **분위기 (Mood)**: Film grain, color grading

Output a verification table with scores. Flag any scenes that need text enhancement.`;

  // First message: Send video + all context texts
  try {
    const response = await currentChat.sendMessage({
      message: [
        {
          inlineData: currentFileBase64
        },
        {
          text: contextMessage
        }
      ]
    });

    const text = response.text;
    if (!text) throw new Error("AI 응답이 없습니다.");
    return text;

  } catch (error: any) {
    console.error("Gemini API Error:", error);
    throw new Error(error.message || "영상 분석 초기화 실패");
  }
};

export const sendUserFeedback = async (
  message: string,
  currentStep: number = 1
): Promise<string> => {
  if (!currentChat) throw new Error("활성 채팅 세션이 없습니다.");

  let textMessage = message;

  // STEP 3 진입 시 (currentStep === 2에서 "변주" 입력): Persona + 베스트 댓글 주입
  if (currentStep === 2 && (cachedPersonaJson || cachedBestComments.length > 0)) {
    let additionalContext = "\n\n---\n**[STEP 3 추가 컨텍스트]**";

    if (cachedBestComments.length > 0) {
      additionalContext += `\n\n**베스트 댓글 (바이럴 포인트 분석에 활용):**\n${cachedBestComments.map((c, i) => `${i + 1}. ${c}`).join("\n")}`;
    }

    if (cachedPersonaJson && cachedPersonaJson.trim()) {
      additionalContext += `\n\n**Persona JSON (개인화된 변주 아이디어에 활용):**\n\`\`\`json\n${cachedPersonaJson}\n\`\`\``;
    }

    additionalContext += "\n\n위 컨텍스트를 활용하여 변주 옵션을 생성해주세요.";
    textMessage = message + additionalContext;
  }

  // Re-send the video with the user feedback to ensure the model analyzes it individually for the next step
  const parts: any[] = [{ text: textMessage }];

  if (currentFileBase64) {
    // Add the video again to the message payload
    parts.unshift({
      inlineData: currentFileBase64
    });
  }

  try {
    const response = await currentChat.sendMessage({
      message: parts
    });

    const text = response.text;
    if (!text) throw new Error("AI 응답이 없습니다.");
    return text;

  } catch (error: any) {
    console.error("Gemini API Error:", error);
    throw new Error(error.message || "메시지 전송 실패");
  }
};