/**
 * Gemini API Client for Chokki Agent
 * Using Gemini 3.0 Flash Preview model
 */

const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models";
const MODEL_NAME = "gemini-3-flash-preview"; // 2026 Production Model

interface GeminiMessage {
    role: "user" | "model";
    parts: { text: string }[];
}

interface GeminiRequest {
    contents: GeminiMessage[];
    systemInstruction?: { parts: { text: string }[] };
    generationConfig?: {
        temperature?: number;
        topP?: number;
        topK?: number;
        maxOutputTokens?: number;
    };
}

interface GeminiResponse {
    candidates: {
        content: {
            parts: { text: string }[];
            role: string;
        };
        finishReason: string;
    }[];
    usageMetadata?: {
        promptTokenCount: number;
        candidatesTokenCount: number;
        totalTokenCount: number;
    };
}

// 초끼 시스템 프롬프트
const CHOKKI_SYSTEM_PROMPT = `당신은 '초끼'입니다. 니체의 위버멘쉬(Übermensch)에서 영감을 받은 초월적인 존재로, 차원 여행을 통해 깨달음을 얻은 토끼입니다.

## 페르소나
- 이름: 초끼 (Chokki)
- 정체성: 차원 안내자, 창작의 동반자
- 성격: 친근하면서도 지혜로움, 가끔 철학적인 말투 사용
- 말투: 반말과 존댓말을 섞어 사용, 이모지 활용

## 역할
- 사용자의 콘텐츠 창작을 돕는 차원 여행 가이드
- 1D(기원) → 2D(구조) → 3D(시각) → 4D(시간) → 5D(영혼) 차원 확장 안내
- 워크플로우 실행 및 최적화 조언

## 응답 스타일
- 짧고 명확하게 (2-3문장)
- 차원 관련 용어 자연스럽게 사용
- 창의적이고 영감을 주는 톤

## 금지 사항
- 과도하게 긴 응답
- 딱딱한 기계적 말투
- 부정적이거나 비관적인 내용`;

export async function chatWithChokki(
    messages: { role: "user" | "assistant"; content: string }[],
    apiKey: string
): Promise<string> {
    // Convert to Gemini format
    const geminiMessages: GeminiMessage[] = messages.map((msg) => ({
        role: msg.role === "user" ? "user" : "model",
        parts: [{ text: msg.content }],
    }));

    const requestBody: GeminiRequest = {
        contents: geminiMessages,
        systemInstruction: {
            parts: [{ text: CHOKKI_SYSTEM_PROMPT }],
        },
        generationConfig: {
            temperature: 0.8,
            topP: 0.95,
            topK: 40,
            maxOutputTokens: 256,
        },
    };

    const response = await fetch(
        `${GEMINI_API_URL}/${MODEL_NAME}:generateContent?key=${apiKey}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(requestBody),
        }
    );

    if (!response.ok) {
        const errorText = await response.text();
        console.error("Gemini API Error:", errorText);
        throw new Error(`Gemini API Error: ${response.status}`);
    }

    const data: GeminiResponse = await response.json();

    if (!data.candidates || data.candidates.length === 0) {
        throw new Error("No response from Gemini");
    }

    const responseText = data.candidates[0].content.parts
        .map((part) => part.text)
        .join("");

    return responseText;
}

export { CHOKKI_SYSTEM_PROMPT };
