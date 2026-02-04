

import { GoogleGenAI, Chat, Content, ThinkingLevel } from "@google/genai";
import { AnalysisMode, UserProfile, Message, DepthStage, StructuredFaceReading, SajuAnalysis, VibePhilosophyPersona } from "../types";
import {
  GET_MODE_PROMPT,
  DIGITAL_TWIN_PROMPT_TEMPLATE,
  FACE_ANALYSIS_STRUCTURED_PROMPT,
  getSajuAnalysisPrompt,
  EMOTIONAL_KEYWORDS,
  getDepthStage,
  VIBE_PERSONA_SCHEMA,
  PERSONA_UPDATE_SYSTEM_PROMPT,
  deepMergePersona,
  calculateDepthFromFields
} from "../constants";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

let chatSession: Chat | null = null;
let currentDepthStage: DepthStage = 'exploration';
let currentModelType: 'flash' | 'pro' = 'flash';

// ===== 심도에 따른 모델 선택 (40% 임계값, 초기 분석 Pro 강제) =====
export const getModelForDepth = (depthScore: number, isInitialAnalysis: boolean = false): { model: string; type: 'flash' | 'pro' } => {
  // 초기 분석(관상/사주/MBTI)은 Pro 강제
  if (isInitialAnalysis) {
    return { model: 'gemini-3-pro-preview', type: 'pro' };
  }
  // 40% 이상: Pro 모델 (깊은 분석) - 기존 50%에서 변경
  if (depthScore >= 40) {
    return { model: 'gemini-3-pro-preview', type: 'pro' };
  }
  // 40% 미만: Flash 모델 (빠른 응답)
  return { model: 'gemini-3-flash-preview', type: 'flash' };
};

// ===== 현재 모델 타입 getter =====
export const getCurrentModelType = (): 'flash' | 'pro' => currentModelType;

// ===== 단계별 증가 배율 (하드캡 제거) =====
const getStageMultiplier = (depth: number): number => {
  if (depth < 30) return 0.9;      // exploration: 약간 느림
  if (depth < 60) return 1.1;      // development: 부스트
  if (depth < 85) return 1.0;      // deep: 정상
  return 0.8;                       // resolution: 느림
};

// ===== 폴백 심도 계산 (LLM 태그 실패 시) - 60% 하드캡 제거 =====
export const calculateFallbackDepth = (
  currentDepth: number,
  userMessage: string,
  turnCount: number
): number => {
  const messageLength = userMessage.length;

  // 감정 키워드 카운트
  let emotionalKeywordCount = 0;
  for (const keyword of EMOTIONAL_KEYWORDS) {
    if (userMessage.includes(keyword)) {
      emotionalKeywordCount++;
    }
  }

  // 기본 증가량 계산
  let baseIncrement = 0;

  // 1. 메시지 길이 기반
  if (messageLength < 10) {
    // 단답형: 증가 없음 또는 미미
    baseIncrement = 0;
  } else if (messageLength < 30) {
    // 짧은 응답: 1-2점
    baseIncrement = 1 + (emotionalKeywordCount > 0 ? 1 : 0);
  } else if (messageLength < 100) {
    // 중간 길이: 3-5점
    baseIncrement = 3 + Math.min(emotionalKeywordCount, 2);
  } else {
    // 장문: 5-8점
    baseIncrement = 5 + Math.min(emotionalKeywordCount, 3);
  }

  // 2. 깊은 고민 신호 보너스
  const deepSignals = ['진짜', '사실', '솔직히', '고백', '비밀', '처음으로', '아무에게도', '부모님', '가족'];
  for (const signal of deepSignals) {
    if (userMessage.includes(signal)) {
      baseIncrement += 2;
      break; // 한 번만 적용
    }
  }

  // 3. 최대 10점 제한
  baseIncrement = Math.min(baseIncrement, 10);

  // 4. 단계별 배율 적용 (60% 하드캡 제거됨)
  let increment = baseIncrement * getStageMultiplier(currentDepth);

  // 5. 턴 5 이상이면 최소 2점 증가 보장 (너무 느린 진행 방지)
  if (turnCount >= 5 && increment < 2 && baseIncrement > 0) {
    increment = 2;
  }

  // 6. 최종 심도 계산 (100 초과 방지)
  const newDepth = Math.min(currentDepth + increment, 100);

  return Math.round(newDepth);
};

// ===== 1. 관상 분석 전용 함수 (단발성 호출, 채팅 세션과 무관) =====
export const extractFaceFeatures = async (imageBase64: string): Promise<string> => {
  try {
    const matches = imageBase64.match(/^data:(.+);base64,(.+)$/);
    if (!matches || matches.length !== 3) {
      return "이미지 데이터 오류";
    }
    const mimeType = matches[1];
    const base64Data = matches[2];

    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: {
        parts: [
          {
            inlineData: {
              mimeType: mimeType,
              data: base64Data
            }
          },
          { text: "이 사람의 얼굴 관상을 아주 상세하게 분석해줘. 눈매, 코의 모양, 입술, 얼굴형, 전반적인 기운 등을 전문가처럼 묘사해줘. 성격이나 운세와 연결지을 수 있는 특징 위주로." }
        ]
      }
    });

    return response.text || "관상 분석 결과를 불러올 수 없습니다.";
  } catch (error) {
    console.error("Face Analysis Error:", error);
    return "관상을 보는데 실패했습니다. (이미지 분석 오류)";
  }
};

// ===== 1-2. 구조화된 관상 분석 (JSON 반환) =====
export const extractStructuredFaceReading = async (imageBase64: string): Promise<StructuredFaceReading | null> => {
  try {
    const matches = imageBase64.match(/^data:(.+);base64,(.+)$/);
    if (!matches || matches.length !== 3) {
      console.error("Invalid image data format");
      return null;
    }
    const mimeType = matches[1];
    const base64Data = matches[2];

    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: {
        parts: [
          {
            inlineData: {
              mimeType: mimeType,
              data: base64Data
            }
          },
          { text: FACE_ANALYSIS_STRUCTURED_PROMPT }
        ]
      },
      config: {
        responseMimeType: "application/json"
      }
    });

    const jsonText = response.text;
    if (!jsonText) return null;

    const parsed = JSON.parse(jsonText);

    // 타입 매핑
    return {
      eyes: {
        shape: parsed.eyes?.shape || '',
        energy: parsed.eyes?.energy || '',
        leftRight: parsed.eyes?.left_right_balance,
        fortuneIndicator: parsed.eyes?.fortune_indicator
      },
      eyebrows: {
        shape: parsed.eyebrows?.shape || '',
        energy: parsed.eyebrows?.energy || ''
      },
      nose: {
        shape: parsed.nose?.shape || '',
        energy: parsed.nose?.energy || '',
        fortuneIndicator: parsed.nose?.fortune_indicator
      },
      mouth: {
        shape: parsed.mouth?.shape || '',
        energy: parsed.mouth?.energy || '',
        communicationStyle: parsed.mouth?.communication_style
      },
      ears: {
        shape: parsed.ears?.shape || '',
        energy: parsed.ears?.energy || '',
        fortuneIndicator: parsed.ears?.fortune_indicator
      },
      faceShape: parsed.face_shape || '',
      forehead: {
        shape: parsed.forehead?.shape || '',
        energy: parsed.forehead?.energy || '',
        fortuneIndicator: parsed.forehead?.fortune_indicator
      },
      chin: {
        shape: parsed.chin?.shape || '',
        energy: parsed.chin?.energy || '',
        fortuneIndicator: parsed.chin?.fortune_indicator
      },
      overallQi: parsed.overall_qi || '',
      personalityInference: parsed.personality_inference || ''
    };
  } catch (error) {
    console.error("Structured Face Analysis Error:", error);
    return null;
  }
};

// ===== 1-3. 구조화된 사주 분석 (JSON 반환) =====
export const analyzeSajuStructured = async (
  birthDate: string,
  calendarType: 'solar' | 'lunar',
  birthTime: string | null,
  birthPlace: string | null
): Promise<SajuAnalysis | null> => {
  try {
    const prompt = getSajuAnalysisPrompt(birthDate, calendarType, birthTime, birthPlace);

    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: {
        parts: [{ text: prompt }]
      },
      config: {
        responseMimeType: "application/json",
        thinkingConfig: { thinkingLevel: ThinkingLevel.LOW }
      }
    });

    const jsonText = response.text;
    if (!jsonText) return null;

    const parsed = JSON.parse(jsonText);

    // 타입 매핑
    return {
      fourPillars: {
        year: parsed.four_pillars?.year || null,
        month: parsed.four_pillars?.month || null,
        day: parsed.four_pillars?.day || null,
        hour: parsed.four_pillars?.hour || null
      },
      fiveElementsBalance: {
        wood: parsed.five_elements_balance?.wood || 0,
        fire: parsed.five_elements_balance?.fire || 0,
        earth: parsed.five_elements_balance?.earth || 0,
        metal: parsed.five_elements_balance?.metal || 0,
        water: parsed.five_elements_balance?.water || 0
      },
      tenGods: parsed.ten_gods || [],
      dayMaster: parsed.day_master || '',
      dayMasterStrength: parsed.day_master_strength || 'balanced',
      majorLuckCycles: parsed.major_luck_cycles || [],
      currentYearLuck: parsed.current_year_luck || ''
    };
  } catch (error) {
    console.error("Saju Analysis Error:", error);
    return null;
  }
};

// ===== 2. 채팅 초기화 (심도 단계 반영, 모델 동적 선택) =====
export const initializeChat = (
  mode: AnalysisMode,
  profile: UserProfile,
  history: Message[] = [],
  depthScore: number = 0
) => {
  // 현재 심도 단계 업데이트
  currentDepthStage = getDepthStage(depthScore);

  // 심도에 따른 모델 선택
  const { model: selectedModel, type: modelType } = getModelForDepth(depthScore);
  currentModelType = modelType;

  const systemInstruction = GET_MODE_PROMPT(mode, profile, currentDepthStage);

  // Convert internal Message[] to Gemini Content[] format for history restoration
  const geminiHistory: Content[] = history.map(msg => ({
    role: msg.role,
    parts: [{ text: msg.text }]
  }));

  // Pro 모델은 thinking 활성화, 온도 낮춤
  const isPro = modelType === 'pro';

  chatSession = ai.chats.create({
    model: selectedModel,
    history: geminiHistory,
    config: {
      systemInstruction: systemInstruction,
      temperature: isPro ? 0.7 : 0.85,
      thinkingConfig: isPro ? { thinkingLevel: ThinkingLevel.LOW } : undefined,
    },
  });

  console.log(`[initializeChat] Model: ${selectedModel}, Depth: ${depthScore}, Stage: ${currentDepthStage}`);
};

// ===== 2-1. 심도 단계 변경 시 시스템 프롬프트 재주입 =====
export const reinitializeChatWithNewStage = (
  mode: AnalysisMode,
  profile: UserProfile,
  history: Message[],
  newDepthScore: number
) => {
  const newStage = getDepthStage(newDepthScore);

  // 단계가 변경된 경우에만 재초기화
  if (newStage !== currentDepthStage) {
    console.log(`Stage transition: ${currentDepthStage} -> ${newStage}`);
    currentDepthStage = newStage;
    initializeChat(mode, profile, history, newDepthScore);
    return true; // 단계 변경됨
  }
  return false; // 단계 유지
};

// ===== 3. 메시지 전송 (폴백 심도 계산 포함) =====
export const sendMessageToGemini = async (
  message: string,
  currentDepth: number = 0,
  turnCount: number = 0
): Promise<{ text: string; depth: number; stageChanged: boolean }> => {
  if (!chatSession) {
    throw new Error("Chat session not initialized");
  }

  let stageChanged = false;

  try {
    // 30초 타임아웃
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error("Response timed out")), 30000)
    );

    const apiCallPromise = chatSession.sendMessage({
      message: message
    });

    const response = await Promise.race([apiCallPromise, timeoutPromise]);

    const rawText = response.text || "영혼들이 침묵하고 있습니다...";

    // Parse Depth Tag
    const depthMatch = rawText.match(/\[\[DEPTH:\s*(\d+)\]\]/);
    let depth: number;
    let cleanText = rawText;

    if (depthMatch) {
      // LLM이 태그를 제공한 경우
      depth = parseInt(depthMatch[1], 10);
      cleanText = rawText.replace(depthMatch[0], '').trim();

      // 유효성 검사: 10점 초과 증가 방지
      if (depth > currentDepth + 10) {
        depth = currentDepth + 10;
      }
      // 감소 방지 (심도는 증가만 허용)
      if (depth < currentDepth) {
        depth = currentDepth;
      }
    } else {
      // LLM이 태그를 누락한 경우: 폴백 계산
      console.warn("DEPTH tag missing, using fallback calculation");
      depth = calculateFallbackDepth(currentDepth, message, turnCount);
    }

    // 심도 단계 변경 확인
    const newStage = getDepthStage(depth);
    if (newStage !== currentDepthStage) {
      stageChanged = true;
      currentDepthStage = newStage;
    }

    return { text: cleanText, depth, stageChanged };

  } catch (error) {
    console.error("Gemini API Error:", error);
    return {
      text: "기가 약해서 목소리가 잘 안 들리네... 다시 한 번 말해줄래? (통신 오류)",
      depth: currentDepth,
      stageChanged: false
    };
  }
};

// ===== 4. 디지털 트윈 JSON 생성 (HEXACO + 동양철학 확장) =====
export const generateDigitalTwin = async (profile: UserProfile, history: Message[]) => {
  try {
    // Build Context from Profile and History
    const conversationContext = history.map(msg => `${msg.role}: ${msg.text}`).join('\n');

    // Use gemini-3-pro-preview for complex reasoning and structure generation
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: {
        parts: [
          { text: DIGITAL_TWIN_PROMPT_TEMPLATE },
          { text: `\n\n[USER PROFILE DATA]\n${JSON.stringify(profile, null, 2)}` },
          { text: `\n\n[CONVERSATION LOG]\n${conversationContext}` }
        ]
      },
      config: {
        responseMimeType: "application/json",
        // Thinking budget increased for deeper analysis
        thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH }
      }
    });

    return response.text;
  } catch (error) {
    console.error("Digital Twin Generation Error:", error);
    throw error;
  }
};

// ===== 5. 현재 심도 단계 getter =====
export const getCurrentDepthStage = (): DepthStage => {
  return currentDepthStage;
};

// ===== 6. 페르소나 상태 업데이트 (레거시 심연의 거울 방식) - 대수술 버전 =====
export const updatePersonaState = async (
  currentPersona: VibePhilosophyPersona,
  conversationHistory: string,
  userMessage: string,
  isInitialConsultation: boolean = false,
  turnCount: number = 0  // 🔥 턴 카운트 파라미터 추가
): Promise<{
  persona: Partial<VibePhilosophyPersona>;
  response: string;
  updatedPaths: Set<string>;
}> => {
  try {
    // 현재 심도 계산 (턴 카운트 포함)
    const currentDepth = calculateDepthFromFields(currentPersona, turnCount);

    // 모델 선택 (초기 분석 또는 40% 이상이면 Pro)
    const { model: selectedModel, type: modelType } = getModelForDepth(currentDepth, isInitialConsultation);
    const isPro = modelType === 'pro';

    console.log(`[updatePersonaState] Model: ${selectedModel}, Depth: ${currentDepth}, isInitial: ${isInitialConsultation}`);

    // 현재 페르소나 상태를 컨텍스트에 포함
    const personaContext = JSON.stringify(currentPersona, null, 2);

    const response = await ai.models.generateContent({
      model: selectedModel,
      contents: {
        parts: [
          { text: PERSONA_UPDATE_SYSTEM_PROMPT },
          { text: `\n\n[현재 페르소나 상태]\n${personaContext}` },
          { text: `\n\n[대화 기록]\n${conversationHistory}` },
          { text: `\n\n[사용자 최신 메시지]\n${userMessage}` },
          { text: `\n\n[지시] 위 정보를 바탕으로 페르소나를 업데이트하고, next_response에 도사의 응답을 작성하세요.` }
        ]
      },
      config: {
        responseMimeType: "application/json",
        responseSchema: VIBE_PERSONA_SCHEMA,
        thinkingConfig: isPro ? { thinkingLevel: ThinkingLevel.LOW } : undefined,
      }
    });

    const jsonText = response.text;
    if (!jsonText) {
      return {
        persona: {},
        response: "기가 약해서 목소리가 잘 안 들리네... 다시 한 번 말해줄래?",
        updatedPaths: new Set()
      };
    }

    const parsed = JSON.parse(jsonText);
    const nextResponse = parsed.next_response || "음... 좀 더 생각해볼게.";
    delete parsed.next_response;

    // 업데이트된 경로 추적
    const { merged, updatedPaths } = deepMergePersona(currentPersona, parsed);

    return {
      persona: parsed,
      response: nextResponse,
      updatedPaths
    };

  } catch (error) {
    console.error("updatePersonaState Error:", error);
    return {
      persona: {},
      response: "통신 상태가 불안정합니다. 잠시 후 다시 시도해주세요.",
      updatedPaths: new Set()
    };
  }
};

// ===== 7. 다운로드 시점 빈 필드 추론 (대화 맥락 기반) =====
export const inferEmptyFieldsForDownload = async (
  currentPersona: VibePhilosophyPersona,
  conversationHistory: string,
  depthScore: number
): Promise<VibePhilosophyPersona> => {
  try {
    // 50% 미만이면 추론 안 함
    if (depthScore < 50) {
      return currentPersona;
    }

    const personaContext = JSON.stringify(currentPersona, null, 2);

    const inferPrompt = `
<role>심리 프로파일 완성 전문가</role>

<task>
아래 대화 기록과 현재까지 수집된 페르소나 데이터를 바탕으로,
**빈 필드들을 대화 맥락에서 추론하여 풍부하게 채워주세요.**
</task>

<rules>
1. 빈 문자열(""), 빈 배열([]), 빈 객체({})인 필드들을 대화 맥락 기반으로 채울 것
2. 이미 값이 있는 필드는 절대 수정하지 말 것
3. 추론은 대화에서 드러난 성격, 말투, 가치관, 감정 패턴을 근거로 할 것
4. 관상(face_reading)은 대화에서 드러난 성격 특성을 동양 관상학적으로 해석
5. 각 필드는 구체적이고 풍부하게 작성 (1-2문장)
6. 배열 필드는 최소 2-3개 항목으로 채울 것

<inference_guidelines>
- face_reading: 성격 → 관상 역추론 ("냉철한 분석력" → "심장형 눈매, 예리한 안광")
- cognitive_architecture: 대화 패턴에서 인지 스타일 추론
- emotional_landscape: 언급된 감정, 가치관, 두려움 기반
- psychological_entropy: 방어 패턴, 갈등 구조 분석
- life_trajectory: 언급된 가족, 경력, 전환점
- cultural_context: 세대, 사회적 맥락
- master_attributes: 관심사, 작업 스타일, 미적 취향
</inference_guidelines>
</rules>

<current_persona>
${personaContext}
</current_persona>

<conversation_history>
${conversationHistory}
</conversation_history>

<output>
완성된 전체 페르소나 JSON을 반환하세요. 기존 값은 유지하고 빈 필드만 채우세요.
</output>
`;

    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: {
        parts: [{ text: inferPrompt }]
      },
      config: {
        responseMimeType: "application/json",
        thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH }
      }
    });

    const jsonText = response.text;
    if (!jsonText) {
      console.warn("[inferEmptyFieldsForDownload] No response, returning original");
      return currentPersona;
    }

    const inferred = JSON.parse(jsonText);

    // 기존 데이터와 머지 (기존 값 우선 보존)
    const { merged } = deepMergePersona(currentPersona, inferred);

    console.log("[inferEmptyFieldsForDownload] Successfully inferred empty fields");
    return merged;

  } catch (error) {
    console.error("[inferEmptyFieldsForDownload] Error:", error);
    return currentPersona; // 에러 시 원본 반환
  }
};

// ===== 8. 단계별 추가 컨텍스트 주입 (6단계 확장) =====
export const getStageSpecificPromptAddition = (stage: DepthStage): string => {
  switch (stage) {
    case 'subconscious':
      return `
<additional_context for="subconscious_stage">
  이제 잠재의식 단계입니다. 다음을 활성화하십시오:
  - 변연계 반응 패턴 관찰
  - 조건화된 정서 반응 식별
  - "그럴 때 몸이 먼저 반응하지 않아?" 패턴 사용
  - 애착 이론과 체화된 인지 적용
</additional_context>
`;
    case 'unconscious':
      return `
<additional_context for="unconscious_stage">
  이제 무의식 단계입니다. 다음을 활성화하십시오:
  - HEXACO Honesty-Humility 차원으로 도덕적 딜레마 탐색
  - 방어 기제 식별 (합리화, 투사, 억압)
  - 그림자 자아(Shadow Self) 탐색
  - "사실 ~가 아니라, ~인 거 아니야?" 패턴 적극 사용
  - 콤플렉스 구조 분석
</additional_context>
`;
    case 'archetypal':
      return `
<additional_context for="archetypal_stage">
  이제 원형 통합 단계입니다. 다음을 활성화하십시오:
  - 개인적 신화(Personal Myth) 구축
  - 아니마/아니무스 통합
  - 영웅 여정(Hero's Journey) 매핑
  - "네 인생이 하나의 이야기라면" 패턴 사용
</additional_context>
`;
    case 'resolution':
      return `
<additional_context for="resolution_stage">
  이제 최종 합성 단계입니다. 다음을 제공하십시오:
  - 구조화된 솔루션 (문제 요약 → 원인 → 처방)
  - 사주 기반 타이밍 조언 (좋은 시기/피할 시기)
  - 구체적이고 실행 가능한 행동 지침 3가지
  - 통합 메시지 (의미 부여)
  - 선택적: 부적 문구 또는 주문
</additional_context>
`;
    default:
      return '';
  }
};
