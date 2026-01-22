/**
 * @deprecated P0 HARDENING: This API route violates the Sealed Capsule principle.
 * All AI calls should go through the FastAPI backend.
 * Use the backend /api/v1/agent/chat endpoint instead.
 *
 * This route is scheduled for removal. If you need chat functionality,
 * use the api.agent.chat() function from @/lib/api.ts which routes
 * to the proper backend endpoint.
 */
import { NextRequest, NextResponse } from "next/server";
import { chatWithChokki } from "@/lib/gemini-client";

export async function POST(request: NextRequest) {
    try {
        const { messages } = await request.json();

        if (!messages || !Array.isArray(messages)) {
            return NextResponse.json(
                { error: "Messages array is required" },
                { status: 400 }
            );
        }

        const apiKey = process.env.GEMINI_API_KEY;

        if (!apiKey || apiKey === "your_gemini_api_key_here") {
            // Fallback: 시뮬레이션 모드
            console.warn("GEMINI_API_KEY not configured, using simulation mode");
            const lastUserMessage = messages.filter((m: { role: string }) => m.role === "user").pop();
            const simulatedResponse = getSimulatedResponse(lastUserMessage?.content || "");
            return NextResponse.json({ response: simulatedResponse });
        }

        const response = await chatWithChokki(messages, apiKey);

        return NextResponse.json({ response });
    } catch (error) {
        console.error("Chat API Error:", error);
        return NextResponse.json(
            { error: "Failed to process chat request" },
            { status: 500 }
        );
    }
}

// Fallback simulation when API key is not set
function getSimulatedResponse(userInput: string): string {
    const lowerInput = userInput.toLowerCase();

    if (lowerInput.includes("실행")) {
        return "전체 워크플로우를 실행할까? 차원 흐름에 따라 순차적으로 진행할게! 🚀";
    }

    if (lowerInput.includes("요리") || lowerInput.includes("브이로그")) {
        return "요리 브이로그! 🍳 1D(기원)에서 컨셉을 잡고, 2D(구조)로 넘어가는 흐름이 좋겠어!";
    }

    if (lowerInput.includes("안녕") || lowerInput.includes("반가워")) {
        return "안녕! 나는 차원 안내자 초끼야 🐰 오늘은 어떤 차원 여행을 떠나볼까?";
    }

    return `"${userInput}"에 대해 최적의 차원 흐름을 안내해줄게! ✨`;
}
