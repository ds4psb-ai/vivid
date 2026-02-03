import { GoogleGenAI, Chat } from "@google/genai";
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

export const startAnalysisChat = async (
  file: File,
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

  const finalSystemPrompt = SYSTEM_PROMPT_TEMPLATE.replace("{{MODE}}", mode);

  // Initialize Chat
  currentChat = ai.chats.create({
    model: GEMINI_MODEL,
    config: {
      systemInstruction: finalSystemPrompt,
      temperature: 0.2,
      maxOutputTokens: 32768, // RAW 출력 잘림 방지
    },
  });

  // First message: Send video and trigger Step 1
  try {
    const response = await currentChat.sendMessage({
      message: [
        {
          inlineData: currentFileBase64
        },
        {
          text: "분석을 시작해주세요. [STEP 1: 컷 분석] 결과를 보여주세요."
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
  message: string
): Promise<string> => {
  if (!currentChat) throw new Error("활성 채팅 세션이 없습니다.");
  
  // Re-send the video with the user feedback to ensure the model analyzes it individually for the next step
  const parts: any[] = [{ text: message }];
  
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