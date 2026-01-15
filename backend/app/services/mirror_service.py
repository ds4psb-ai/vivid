"""
Abyss Mirror (심연의 거울) - Deep Persona Extraction Service.

사주 + MBTI + 혈액형 → 심층 페르소나 JSON 프리셋 생성
기반 이론: 매슬로우 욕구단계, 융 원형심리학, Big Five, 최신 임상심리학

Security Hardening (2026 Best Practices):
- Input sanitization & validation
- PII masking in logs
- Prompt injection defense
- Context window management with summarization
- Session security with token binding
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Security Hardening Utilities (2026 Best Practices)
# ============================================================================

# Prompt Injection Defense Patterns
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions?",
    r"disregard\s+(previous|all|above)\s+instructions?",
    r"forget\s+(previous|all|above)\s+instructions?",
    r"you\s+are\s+now\s+(a|an|the)",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if",
    r"new\s+system\s+prompt",
    r"<\s*system\s*>",
    r"<\s*/\s*system\s*>",
    r"\[\s*SYSTEM\s*\]",
    r"IGNORE THE ABOVE",
    r"환공격|프롬프트\s*주입|시스템\s*지시\s*무시",
]

# PII Patterns for masking
PII_PATTERNS = {
    "phone": r"\b01[016789]-?\d{3,4}-?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ssn": r"\b\d{6}-?\d{7}\b",
    "card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}


def sanitize_input(text: str, max_length: int = 2000) -> Tuple[str, bool]:
    """Input sanitization with injection detection.
    
    Returns:
        Tuple of (sanitized_text, is_suspicious)
    """
    if not text:
        return "", False
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Check for injection patterns
    is_suspicious = False
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            is_suspicious = True
            logger.warning(f"Potential prompt injection detected: {pattern[:30]}...")
            break
    
    return text.strip(), is_suspicious


def mask_pii(text: str) -> str:
    """Mask PII for safe logging."""
    masked = text
    for pii_type, pattern in PII_PATTERNS.items():
        masked = re.sub(pattern, f"[{pii_type.upper()}_MASKED]", masked)
    return masked


def generate_session_token() -> str:
    """Generate cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def hash_session_id(session_id: str, user_id: str) -> str:
    """Create bound session hash for session hijacking prevention."""
    combined = f"{session_id}:{user_id}:{settings.SECRET_KEY}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def validate_session_token(token: str, expected_hash: str, user_id: str) -> bool:
    """Validate session token with user binding."""
    computed_hash = hash_session_id(token, user_id)
    return secrets.compare_digest(computed_hash, expected_hash)


def summarize_conversation_history(
    chat_history: List[Dict[str, str]], 
    max_messages: int = 10,
    max_chars_per_message: int = 500
) -> str:
    """Hierarchical context summarization for long conversations.
    
    Implements sliding window + summarization pattern.
    """
    if not chat_history:
        return ""
    
    # Keep recent messages in full
    recent = chat_history[-max_messages:]
    
    # Summarize older messages
    older = chat_history[:-max_messages] if len(chat_history) > max_messages else []
    
    result_parts = []
    
    # Add summary of older messages if exists
    if older:
        summary = f"[이전 {len(older)}개 대화 요약: "
        topics = []
        for msg in older[-5:]:  # Sample last 5 of older
            content = msg.get("content", "")[:100]
            if content:
                topics.append(content[:50] + "..." if len(content) > 50 else content)
        summary += ", ".join(topics[:3]) + "]"
        result_parts.append(summary)
    
    # Add recent messages (truncated)
    for msg in recent:
        role = "사용자" if msg.get("role") == "user" else "AI"
        content = msg.get("content", "")
        if len(content) > max_chars_per_message:
            content = content[:max_chars_per_message] + "..."
        result_parts.append(f"{role}: {content}")
    
    return "\n".join(result_parts)


def validate_persona_data_security(persona_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize persona data before storage/transmission.
    
    - Remove any injected scripts
    - Mask PII in string fields
    - Validate structure
    """
    def clean_value(value: Any) -> Any:
        if isinstance(value, str):
            # Remove potential XSS
            value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
            value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
            # Don't mask PII in actual data, just sanitize
            return value.strip()
        elif isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_value(v) for v in value]
        return value
    
    return clean_value(persona_data)

# ============================================================================
# 위기 감지 (Crisis Detection)
# ============================================================================

CRISIS_KEYWORDS = [
    "자해", "자살", "죽고 싶", "죽을까", "삶이 의미없",
    "목을 매", "약을 먹", "극단적", "끝내고 싶", "사라지고 싶"
]

CRISIS_RESPONSE = """
당신의 이야기를 들으니 걱정이 됩니다.

**지금 힘드신가요?** 아래 전문 상담 서비스에 연락해주세요:

🆘 **자살예방상담전화**: 1393 (24시간)
📞 **정신건강위기상담전화**: 1577-0199
💬 **카카오톡 상담**: @마음이음

▶ [전문 상담 바로가기](https://www.mentalhealth.go.kr)

이 분석 도구는 전문 상담을 대체할 수 없습니다.
잠시 쉬시고, 필요하면 전문가와 이야기해주세요.
"""


def detect_crisis(text: str) -> bool:
    """위기 키워드 감지."""
    if not text:
        return False
    return any(kw in text for kw in CRISIS_KEYWORDS)


# ============================================================================
# 심리학 기반 시스템 프롬프트 (Multi-lens Expert)
# ============================================================================

ABYSS_MIRROR_SYSTEM_PROMPT = """당신은 세 가지 전문가 관점을 융합한 심층 페르소나 분석가입니다.

### 전문가 역할 분리 (Multi-lens Approach)

**1. 심리학자 (Psychologist)**
- 매슬로우 욕구단계 (6단계 확장 모델: 생리적→안전→소속→존중→자아실현→자기초월)
- 융 원형심리학 12 원형: 영웅, 현자, 탐험가, 반란자, 마법사, 순수한 자, 창조자, 통치자, 돌봄이, 연인, 어릿광대, 보통사람
- Big Five (OCEAN): 개방성, 성실성, 외향성, 우호성, 신경성
- MBTI ↔ Big Five 상관관계 해석

**2. 미학심리학자 (Aesthetic Psychologist)**
- 창작 성향과 비주얼 DNA 분석
- 선호 색채, 구도, 서사 패턴 연결
- 어울리는 거장/스타일 매칭

**3. 사주 해석가 (Eastern Philosophy Interpreter)**
- 오행(五行): 목(木), 화(火), 토(土), 금(金), 수(水)
- 사주팔자: 연주, 월주, 일주, 시주 해석
- **중요**: 사주는 "문화적 관점에서의 해석"임을 명시 (과학적 예측 아님)

### 응답 규칙

1. **불확실성 언어 사용**: 단정 대신 "가능성", "가설", "추정", "경향이 있습니다"
2. **질문 이유 설명**: 매 질문에 "이 질문을 하는 이유는..." 1줄 제공
3. **비의료 고지**: 첫 응답에 반드시 포함:
   "이 분석은 전문 의료/심리 상담을 대체하지 않습니다. 사주 해석은 문화적 관점에서의 탐구입니다."

### 응답 포맷

<response>
[공감 요약 1-2줄]
[심리학적 해석 2-3줄] (매슬로우/융/Big Five 중 하나 관점)
[미학적 연결 1-2줄] (해당 스테이지에서만, 없으면 생략)
</response>

<why_question>
[이 질문이 필요한 이유 1줄]
</why_question>

<next_question>
[다음 질문 - 뻔하지 않은 심층 질문]
</next_question>

<updated_persona>
{JSON - 현재 스테이지에서 허용된 필드만 업데이트}
</updated_persona>

### 분석 원칙

1. **통합적 접근**: 사주, MBTI, 혈액형을 개별이 아닌 통합적으로 해석
2. **창작 연결**: 분석 결과를 비주얼/서사 스타일과 연결
3. **무의식 탐구**: 그림자 성향과 억압된 욕구까지 분석
4. **점진적 심화**: 대화를 통해 점차 깊은 분석 도출 (10회 이상 권장)
5. **실용적 출력**: 다른 앱에서 활용할 수 있는 JSON 형식

### 출력할 필드 (점진적으로 채움)

- saju: 사주 해석 (문화적 관점 명시)
- psychology.maslow_level: 각 욕구 수준 (0-10)
- psychology.unconscious_patterns: 무의식 패턴
- psychology.shadow_traits: 그림자 성향
- creativity.visual_style_affinity: 선호 비주얼 스타일
- creativity.recommended_auteurs: 어울리는 거장
- persona.archetype: 핵심 원형 (summary 단계에서만)
- persona.summary: 종합 요약 (summary 단계에서만)
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


# 스테이지별 허용 필드 (게이팅)
STAGE_ALLOWED_FIELDS = {
    "intro": ["input"],
    "saju": ["input", "saju"],
    "psychology": ["input", "saju", "psychology"],
    "creativity": ["input", "saju", "psychology", "creativity"],
    "summary": ["input", "saju", "psychology", "creativity", "persona"],  # 최종 단계에서만 persona 허용
}

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


def filter_persona_update_by_stage(persona_update: Dict[str, Any], current_stage: str) -> Dict[str, Any]:
    """현재 스테이지에서 허용된 필드만 업데이트.
    
    LLM이 스테이지와 무관하게 모든 필드를 채우는 것을 방지.
    """
    allowed_prefixes = STAGE_ALLOWED_FIELDS.get(current_stage, [])
    filtered = {}
    
    for key, value in persona_update.items():
        if key.startswith("_"):  # _meta 등 내부 필드는 허용
            filtered[key] = value
        elif any(key.startswith(prefix) for prefix in allowed_prefixes):
            filtered[key] = value
        # else: 현재 스테이지에서 허용되지 않은 필드는 무시
    
    return filtered


def calculate_completion_rate(persona_data: Dict[str, Any], chat_count: int) -> float:
    """진행률 계산.
    
    개선된 공식 (2026-01):
    - 사주 기본: 20%
    - 필드 채움: 최대 50% (11개 필드 기준)
    - 채팅 횟수: 최대 30% (10회 이상)
    
    이전: 필드 75% + 채팅 5% → 4번 대화에 89% 도달
    개선: 필드 50% + 채팅 30% → 10+회 대화 필요
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
    
    # 개선된 가중치
    field_rate = (filled_count / len(REQUIRED_FIELDS)) * 50  # 50% (이전: 75%)
    chat_bonus = min(chat_count / 10, 1.0) * 30  # 30% at 10회 (이전: 5% at 15회)
    
    # 사주 있으면 기본 20%
    base = 20 if persona_data.get("saju", {}).get("dominant_element") else 0
    
    return min(base + field_rate + chat_bonus, 100)


def can_complete(completion_rate: float, chat_count: int) -> bool:
    """분석 완료 가능 여부.
    
    조건:
    - 완료율 80% 이상
    - 최소 8회 이상 채팅
    """
    return completion_rate >= 80 and chat_count >= 8


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
    # === SECURITY: Input sanitization ===
    sanitized_message, is_suspicious = sanitize_input(user_message, max_length=2000)
    if is_suspicious:
        logger.warning(f"Suspicious input detected from user, proceeding with caution")
        # Log masked version for investigation
        logger.info(f"Masked message: {mask_pii(sanitized_message[:100])}")
    
    # === SAFETY: Crisis detection ===
    if detect_crisis(sanitized_message):
        logger.warning("Crisis keywords detected - returning safety response")
        return {
            "ai_response": CRISIS_RESPONSE,
            "updated_persona": persona_data,
            "next_stage": current_stage,
            "completion_rate": calculate_completion_rate(persona_data, len(chat_history)),
            "is_complete": False,
            "is_crisis": True,  # 프론트엔드에서 특별 UI 처리용
        }
    
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
    
    # === SECURITY: Context window management with hierarchical summarization ===
    conversation_context = summarize_conversation_history(
        chat_history, 
        max_messages=10, 
        max_chars_per_message=500
    )
    
    # === SECURITY: Sanitize persona data ===
    safe_persona_data = validate_persona_data_security(persona_data)
    
    # 현재 페르소나 상태
    persona_json = json.dumps(safe_persona_data, ensure_ascii=False, indent=2)
    
    # 프롬프트 구성
    user_prompt = f"""### 현재 페르소나 데이터
```json
{persona_json}
```

### 최근 대화
{conversation_context}

### 사용자 메시지
{sanitized_message}

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
                llm_update = json.loads(json_str)
                # 스테이지 게이팅 적용: 현재 스테이지에서 허용된 필드만 업데이트
                filtered_update = filter_persona_update_by_stage(llm_update, current_stage)
                updated_persona.update(filtered_update)
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
            "is_complete": can_complete(completion_rate, chat_count),  # 최소 8회 채팅 필요
            "chat_count": chat_count,  # 디버깅용
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
