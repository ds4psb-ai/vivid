import { GoogleGenAI, Chat, ThinkingLevel } from "@google/genai";
import { GEMINI_MODEL, SYSTEM_PROMPT_TEMPLATE } from "../constants";

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

export const startAnalysisChat = async (
  file: File,
  sceneTable: string
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

  const finalSystemPrompt = SYSTEM_PROMPT_TEMPLATE;

  // Initialize Chat with ThinkingMode HIGH for better reasoning
  currentChat = ai.chats.create({
    model: GEMINI_MODEL,
    config: {
      systemInstruction: finalSystemPrompt,
      temperature: 0.2,
      maxOutputTokens: 32768,
      thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH },
    },
  });

  // First message: Send video with scene table and trigger Step 1
  const initialMessage = `
[STEP 1: 입력 정리]를 시작합니다.

## 씬 테이블 (Academy에서 추출)
아래는 Academy에서 추출한 씬 테이블입니다:

\`\`\`
${sceneTable}
\`\`\`

## 🌏 먼저 타겟 문화권을 선택해주세요:

오마쥬 타겟 문화권을 선택해주세요:

🇰🇷 **[A] 한국 (기본값)** - Korean features, K-style fashion
🇯🇵 **[B] 일본** - Japanese features, J-style fashion
🇺🇸 **[C] 서양** - Western/Caucasian features
🇹🇭 **[D] 동남아** - Southeast Asian features
🌍 **[E] 원본 유지** - 원본 영상의 인종/문화 그대로

**A/B/C/D/E 중 하나를 선택하시면 STEP 1 결과를 보여드립니다.**
(미입력 시 기본값: A 한국)
`;

  try {
    const response = await currentChat.sendMessage({
      message: [
        {
          inlineData: currentFileBase64
        },
        {
          text: initialMessage
        }
      ]
    });

    const text = response.text;
    if (!text) throw new Error("AI 응답이 없습니다.");
    return text;

  } catch (error: any) {
    console.error("Gemini API Error:", error);
    throw new Error(error.message || "프롬프트 생성 초기화 실패");
  }
};

export const sendUserFeedback = async (
  message: string
): Promise<string> => {
  if (!currentChat) throw new Error("활성 채팅 세션이 없습니다.");

  // Re-send the video with the user feedback
  const parts: any[] = [{ text: message }];

  if (currentFileBase64) {
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
