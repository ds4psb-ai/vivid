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
\`\`\`
${sceneTable}
\`\`\`

**⚠️ 중요**: 먼저 씬 분석 결과를 출력하고, 오마쥬 스타일 입력을 안내하세요.

🎨 **오마쥬 스타일 안내:**
- 사용자가 자유롭게 입력 (예: "한국인 20대", "일본 스타일", "텍사스 느낌")
- 빈 입력 또는 "다음" → 기본값 한국인 적용
- 구도/타이밍/카메라는 100% 원본 유지

STEP 1 결과 출력 후 반드시 멈추고 사용자 입력을 기다리세요.
사용자가 "다음", "계속", "진행"을 입력할 때까지 STEP 2로 자동 진행하지 마세요.
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

  // 변주 요청 시 temperature 0.3으로 올려서 자연스러운 변형 허용
  const isVariation = /변주|variation/i.test(message);

  try {
    const response = await currentChat.sendMessage({
      message: parts,
      ...(isVariation && {
        config: { temperature: 0.3, maxOutputTokens: 32768 },
      }),
    });

    const text = response.text;
    if (!text) throw new Error("AI 응답이 없습니다.");
    return text;

  } catch (error: any) {
    console.error("Gemini API Error:", error);
    throw new Error(error.message || "메시지 전송 실패");
  }
};
