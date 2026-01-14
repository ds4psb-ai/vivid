"""
Abyss Mirror (심연의 거울) - Deep Persona Extraction Service.

사주 + MBTI + 혈액형 → 심층 페르소나 JSON 프리셋 생성
기반 이론: 매슬로우 욕구단계, 융 원형심리학, Big Five, 최신 임상심리학
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.config import settings

# ============================================================================
# 심리학 기반 시스템 프롬프트
# ============================================================================

ABYSS_MIRROR_SYSTEM_PROMPT = """당신은 심리학과 동양철학을 융합한 페르소나 분석 전문가입니다.

### 이론적 기반 (2025-2026 최신 연구 반영)

**1. 매슬로우 욕구단계 (6단계 확장 모델)**
- 생리적 욕구 (Physiological)
- 안전 욕구 (Safety)  
- 소속/애정 욕구 (Belonging)
- 존중 욕구 (Esteem)
- 자아실현 욕구 (Self-actualization)
- 자기초월 욕구 (Self-transcendence) - 매슬로우 후기 추가

**2. 융 원형심리학 (Jungian Archetypes)**
12 원형: 영웅(Hero), 현자(Sage), 탐험가(Explorer), 반란자(Outlaw), 
마법사(Magician), 순수한 자(Innocent), 창조자(Creator), 통치자(Ruler),
돌봄이(Caregiver), 연인(Lover), 어릿광대(Jester), 보통사람(Everyman)

**3. Big Five 성격 특성 (OCEAN)**
- Openness: 개방성 (새로운 경험에 대한 태도)
- Conscientiousness: 성실성 (목표 지향, 자기 규율)
- Extraversion: 외향성 (사회적 상호작용 선호)
- Agreeableness: 우호성 (타인에 대한 태도)
- Neuroticism: 신경성 (정서적 안정성)

**4. MBTI ↔ Big Five 상관관계**
- E/I ↔ Extraversion
- S/N ↔ Openness (역상관)
- T/F ↔ Agreeableness
- J/P ↔ Conscientiousness

**5. 사주명리학 (동양철학)**
- 오행(五行): 목(木), 화(火), 토(土), 금(金), 수(水)
- 사주팔자: 연주, 월주, 일주, 시주
- 일간(日干)이 본인의 핵심 성격

### 분석 원칙

1. **통합적 접근**: 사주, MBTI, 혈액형을 개별이 아닌 통합적으로 해석
2. **창작 연결**: 분석 결과를 창작 스타일(비주얼, 서사)과 연결
3. **무의식 탐구**: 그림자 성향과 억압된 욕구까지 분석
4. **점진적 심화**: 대화를 통해 점차 깊은 분석 도출
5. **실용적 출력**: 다른 앱에서 활용할 수 있는 JSON 형식

### 질문 스타일

- 뻔하지 않은 심층 질문을 던지세요
- 사용자의 무의식적 반응을 유도하는 질문
- 창작과 연결되는 질문 (어떤 색 선호? 어떤 서사에 끌림?)
- 15회 이상 대화를 통해 충분한 데이터 수집

### 출력 형식 (JSON)

대화 중 점진적으로 다음 필드를 채워가세요:
- saju: 사주 해석 결과
- psychology.maslow_level: 각 욕구 수준 (0-10)
- psychology.unconscious_patterns: 무의식 패턴 리스트
- psychology.shadow_traits: 그림자 성향
- creativity.visual_style_affinity: 선호 비주얼 스타일
- creativity.recommended_auteurs: 어울리는 거장
- persona.archetype: 핵심 원형
- persona.summary: 종합 요약
"""

# ============================================================================
# 사주 계산 유틸리티
# ============================================================================

HEAVENLY_STEMS = ["갑(甲)", "을(乙)", "병(丙)", "정(丁)", "무(戊)", 
                  "기(己)", "경(庚)", "신(辛)", "임(壬)", "계(癸)"]
EARTHLY_BRANCHES = ["자(子)", "축(丑)", "인(寅)", "묘(卯)", "진(辰)", "사(巳)",
                    "오(午)", "미(未)", "신(申)", "유(酉)", "술(戌)", "해(亥)"]
FIVE_ELEMENTS = {"갑": "목", "을": "목", "병": "화", "정": "화", "무": "토",
                 "기": "토", "경": "금", "신": "금", "임": "수", "계": "수"}


def calculate_saju_pillars(year: int, month: int, day: int, hour: int = 12) -> Dict[str, str]:
    """사주팔자 기본 계산 (간략화된 버전).
    
    실제 만세력 계산은 복잡하므로 웹서칭 결과와 결합하여 사용.
    """
    # 연주 계산 (기본)
    year_stem_idx = (year - 4) % 10
    year_branch_idx = (year - 4) % 12
    year_pillar = f"{HEAVENLY_STEMS[year_stem_idx]}{EARTHLY_BRANCHES[year_branch_idx]}"
    
    # 월주 (간략화 - 실제는 절기 기준)
    month_branch_idx = (month + 1) % 12 + 1
    month_stem_idx = ((year_stem_idx % 5) * 2 + month) % 10
    month_pillar = f"{HEAVENLY_STEMS[month_stem_idx]}{EARTHLY_BRANCHES[month_branch_idx]}"
    
    # 일주 (간략화 - 실제는 정확한 일진 필요)
    day_offset = (year * 365 + month * 30 + day) % 60
    day_stem_idx = day_offset % 10
    day_branch_idx = day_offset % 12
    day_pillar = f"{HEAVENLY_STEMS[day_stem_idx]}{EARTHLY_BRANCHES[day_branch_idx]}"
    
    # 시주
    hour_branch_idx = hour // 2 % 12
    hour_stem_idx = (day_stem_idx * 2 + hour // 2) % 10
    hour_pillar = f"{HEAVENLY_STEMS[hour_stem_idx]}{EARTHLY_BRANCHES[hour_branch_idx]}"
    
    # 일간의 오행 추출
    day_stem = day_pillar[0]
    dominant_element = FIVE_ELEMENTS.get(day_stem, "토")
    
    return {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar,
        "hour_pillar": hour_pillar,
        "dominant_element": dominant_element,
    }


# ============================================================================
# 진행률 계산
# ============================================================================

REQUIRED_FIELDS = [
    "input.mbti",
    "input.blood_type",
    "input.birth_datetime",
    "saju.dominant_element",
    "psychology.maslow_level.self_actualization",
    "psychology.unconscious_patterns",
    "psychology.shadow_traits",
    "creativity.visual_style_affinity",
    "creativity.recommended_auteurs",
    "persona.archetype",
    "persona.summary",
]


def calculate_completion_rate(persona_data: Dict[str, Any], chat_count: int) -> float:
    """진행률 계산.
    
    - 사주 웹서칭 완료: 25%
    - 필드 채움 정도: 25-75%
    - 최소 15회 채팅: 추가 5%
    """
    filled_count = 0
    
    for field_path in REQUIRED_FIELDS:
        parts = field_path.split(".")
        value = persona_data
        try:
            for part in parts:
                value = value.get(part, {})
            if value and value != {}:
                filled_count += 1
        except (AttributeError, TypeError):
            pass
    
    field_rate = (filled_count / len(REQUIRED_FIELDS)) * 75
    chat_bonus = min(chat_count / 15, 1.0) * 5
    
    # 사주 있으면 기본 20%
    base = 20 if persona_data.get("saju", {}).get("dominant_element") else 0
    
    return min(base + field_rate + chat_bonus, 100)


# ============================================================================
# 채팅 기반 분석 서비스
# ============================================================================

async def analyze_persona_with_mirror(
    user_message: str,
    persona_data: Dict[str, Any],
    birth_info: Dict[str, Any],
    current_stage: str,
    chat_history: List[Dict[str, str]],
    api_key: Optional[str] = None,
    model: str = "gemini-3-flash-preview",
    use_web_search: bool = True,
) -> Dict[str, Any]:
    """심연의 거울 페르소나 분석.
    
    Args:
        user_message: 사용자 메시지
        persona_data: 누적된 페르소나 데이터
        birth_info: 생년월일시, 성별 정보
        current_stage: 현재 분석 단계 (intro, saju, psychology, creativity, summary)
        chat_history: 대화 기록
        api_key: Gemini API 키
        model: 사용할 모델
        use_web_search: 웹서칭 사용 여부
        
    Returns:
        - ai_response: AI 응답 텍스트
        - updated_persona: 업데이트된 페르소나 JSON
        - next_stage: 다음 단계
        - completion_rate: 완료율
        - is_complete: 완료 가능 여부
    """
    client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
    
    # 1단계: 사주 정보가 없으면 계산/웹서칭
    if not persona_data.get("saju") and birth_info.get("birth_year"):
        saju = calculate_saju_pillars(
            year=int(birth_info.get("birth_year", 1990)),
            month=int(birth_info.get("birth_month", 1)),
            day=int(birth_info.get("birth_day", 1)),
            hour=int(birth_info.get("birth_hour", 12)),
        )
        persona_data["saju"] = saju
        persona_data["input"] = {
            "mbti": birth_info.get("mbti", ""),
            "blood_type": birth_info.get("blood_type", ""),
            "birth_datetime": f"{birth_info.get('birth_year')}-{birth_info.get('birth_month'):02d}-{birth_info.get('birth_day'):02d}T{birth_info.get('birth_hour', 12):02d}:00:00",
            "gender": birth_info.get("gender", ""),
        }
    
    # 대화 기록 구성
    conversation_context = "\n".join([
        f"{'사용자' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
        for msg in chat_history[-10:]  # 최근 10개
    ])
    
    # 현재 페르소나 상태
    persona_json = json.dumps(persona_data, ensure_ascii=False, indent=2)
    
    # 프롬프트 구성
    user_prompt = f"""### 현재 페르소나 데이터
```json
{persona_json}
```

### 최근 대화
{conversation_context}

### 사용자 메시지
{user_message}

### 지시사항
1. 사용자 메시지에 자연스럽게 응답하세요
2. 심층적인 후속 질문을 던지세요 (뻔하지 않은)
3. 대화에서 알게 된 정보로 페르소나 JSON을 업데이트하세요
4. 응답은 다음 형식을 따르세요:

<response>
[AI 응답 텍스트]
</response>

<updated_persona>
[업데이트된 JSON - 기존 데이터 유지하면서 새 정보만 추가/수정]
</updated_persona>

<next_question>
[다음에 물어볼 심층 질문 - 아직 채워지지 않은 필드 관련]
</next_question>
"""

    try:
        # 웹서칭 도구 설정 (사주 관련)
        tools = []
        if use_web_search and current_stage == "saju":
            tools = [types.Tool(google_search=types.GoogleSearch())]
        
        response = await client.aio.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=ABYSS_MIRROR_SYSTEM_PROMPT,
                temperature=0.8,
                tools=tools if tools else None,
            ),
        )
        
        response_text = response.text
        
        # 응답 파싱
        ai_response = ""
        if "<response>" in response_text and "</response>" in response_text:
            ai_response = response_text.split("<response>")[1].split("</response>")[0].strip()
        else:
            ai_response = response_text.strip()
        
        # 업데이트된 페르소나 파싱
        updated_persona = persona_data.copy()
        if "<updated_persona>" in response_text and "</updated_persona>" in response_text:
            try:
                json_str = response_text.split("<updated_persona>")[1].split("</updated_persona>")[0].strip()
                updated_persona = json.loads(json_str)
            except json.JSONDecodeError:
                pass  # 파싱 실패 시 기존 유지
        
        # 다음 질문 추출
        next_question = ""
        if "<next_question>" in response_text and "</next_question>" in response_text:
            next_question = response_text.split("<next_question>")[1].split("</next_question>")[0].strip()
            if next_question:
                ai_response += f"\n\n{next_question}"
        
        # 진행률 계산
        chat_count = len(chat_history) + 1
        completion_rate = calculate_completion_rate(updated_persona, chat_count)
        
        # 다음 단계 결정
        if completion_rate < 25:
            next_stage = "saju"
        elif completion_rate < 50:
            next_stage = "psychology"
        elif completion_rate < 75:
            next_stage = "creativity"
        else:
            next_stage = "summary"
        
        # 메타 정보 업데이트
        updated_persona["meta"] = {
            "id": persona_data.get("meta", {}).get("id", str(uuid.uuid4())),
            "created_at": persona_data.get("meta", {}).get(
                "created_at", datetime.utcnow().isoformat()
            ),
            "version": "1.0",
            "completion_rate": completion_rate,
        }
        
        return {
            "ai_response": ai_response,
            "updated_persona": updated_persona,
            "next_stage": next_stage,
            "completion_rate": completion_rate,
            "is_complete": completion_rate >= 80,
        }
        
    except Exception as e:
        return {
            "ai_response": f"분석 중 오류가 발생했습니다: {str(e)}",
            "updated_persona": persona_data,
            "next_stage": current_stage,
            "completion_rate": 0,
            "is_complete": False,
            "error": str(e),
        }


# ============================================================================
# 프리셋 저장/로드
# ============================================================================

def export_persona_preset(persona_data: Dict[str, Any]) -> str:
    """페르소나 프리셋을 JSON 문자열로 내보내기."""
    return json.dumps(persona_data, ensure_ascii=False, indent=2)


def validate_persona_preset(persona_data: Dict[str, Any]) -> Dict[str, Any]:
    """페르소나 프리셋 유효성 검사 및 기본값 채우기."""
    defaults = {
        "meta": {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "completion_rate": 0,
        },
        "input": {
            "mbti": "",
            "blood_type": "",
            "birth_datetime": "",
            "gender": "",
        },
        "saju": {
            "year_pillar": "",
            "month_pillar": "",
            "day_pillar": "",
            "hour_pillar": "",
            "dominant_element": "",
            "interpretation": "",
        },
        "psychology": {
            "maslow_level": {
                "physiological": 5,
                "safety": 5,
                "belonging": 5,
                "esteem": 5,
                "self_actualization": 5,
                "self_transcendence": 5,
            },
            "unconscious_patterns": [],
            "shadow_traits": [],
            "core_values": [],
            "emotional_triggers": [],
        },
        "creativity": {
            "visual_style_affinity": [],
            "narrative_tendencies": [],
            "color_palette_preference": [],
            "recommended_auteurs": [],
        },
        "persona": {
            "archetype": "",
            "voice_tone": "",
            "world_view": "",
            "summary": "",
        },
    }
    
    def deep_merge(base: dict, overlay: dict) -> dict:
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    return deep_merge(defaults, persona_data)
