# SPEC: 심연의 거울 (Abyss Mirror)

> **생성일**: 2026-01-14
> **인터뷰 세션**: 15766a54-191c
> **상태**: `DONE` (2026-01-15 완료)

---

## 1. 개요

**사주, MBTI, 혈액형을 조합하여 사용자의 심층 페르소나를 추출**하는 자기분석 도구.
매슬로우 욕구단계, 최신 임상심리학(조던 피터슨 등), 무의식/잠재의식까지 분석하여
**JSON 프리셋으로 추출** → 다른 Vivid 앱들의 창작에 "자기 색깔"로 활용.

---

## 2. 요구사항

### 2.1 기능 요구사항 (Functional)

- [ ] **FR-1**: 사용자 입력 수집 (MBTI, 혈액형, 생년월일+시간, 성별)
- [ ] **FR-2**: 웹서칭으로 사주 해석 데이터 가져오기 (만세력 + 해석)
- [ ] **FR-3**: Gemini 3 Flash Preview 기반 채팅 인터페이스
- [ ] **FR-4**: 진행률 표시 (25% → 80% → 100%)
- [ ] **FR-5**: JSON 페르소나 프리셋 자동 생성 및 점진적 업데이트
- [ ] **FR-6**: 완료 시 프리셋 저장 및 다른 앱에서 참조 가능

### 2.2 비기능 요구사항 (Non-Functional)

- [ ] **NFR-1**: 최소 15회 이상 티키타카 진행
- [ ] **NFR-2**: Gemini API Key 기반 크레딧 차감 (기존 시스템 활용)
- [ ] **NFR-3**: 세션 저장 (가능 시) - 이탈 후 복귀 지원

---

## 3. 기술 설계

### 3.1 JSON 프리셋 스키마 (추론)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["meta", "psychology", "creativity", "persona"],
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "version": { "type": "string", "default": "1.0" },
        "completion_rate": { "type": "number", "minimum": 0, "maximum": 100 }
      }
    },
    "input": {
      "type": "object",
      "properties": {
        "mbti": { "type": "string", "pattern": "^[EI][SN][TF][JP]$" },
        "blood_type": { "enum": ["A", "B", "O", "AB"] },
        "birth_datetime": { "type": "string", "format": "date-time" },
        "gender": { "enum": ["M", "F", "Other"] }
      }
    },
    "saju": {
      "type": "object",
      "description": "사주팔자 분석 결과",
      "properties": {
        "year_pillar": { "type": "string" },
        "month_pillar": { "type": "string" },
        "day_pillar": { "type": "string" },
        "hour_pillar": { "type": "string" },
        "dominant_element": { "enum": ["목", "화", "토", "금", "수"] },
        "interpretation": { "type": "string" }
      }
    },
    "psychology": {
      "type": "object",
      "properties": {
        "maslow_level": {
          "type": "object",
          "description": "매슬로우 욕구단계별 점수",
          "properties": {
            "physiological": { "type": "number", "minimum": 0, "maximum": 10 },
            "safety": { "type": "number", "minimum": 0, "maximum": 10 },
            "belonging": { "type": "number", "minimum": 0, "maximum": 10 },
            "esteem": { "type": "number", "minimum": 0, "maximum": 10 },
            "self_actualization": { "type": "number", "minimum": 0, "maximum": 10 },
            "self_transcendence": { "type": "number", "minimum": 0, "maximum": 10 }
          }
        },
        "unconscious_patterns": {
          "type": "array",
          "items": { "type": "string" },
          "description": "무의식 패턴 (융 원형 기반)"
        },
        "shadow_traits": {
          "type": "array",
          "items": { "type": "string" },
          "description": "그림자 성향"
        },
        "core_values": {
          "type": "array",
          "items": { "type": "string" }
        },
        "emotional_triggers": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "creativity": {
      "type": "object",
      "properties": {
        "visual_style_affinity": {
          "type": "array",
          "items": { "type": "string" },
          "description": "선호하는 비주얼 스타일"
        },
        "narrative_tendencies": {
          "type": "array",
          "items": { "type": "string" },
          "description": "서사 성향"
        },
        "color_palette_preference": {
          "type": "array",
          "items": { "type": "string" }
        },
        "recommended_auteurs": {
          "type": "array",
          "items": { "type": "string" },
          "description": "어울리는 거장 스타일"
        }
      }
    },
    "persona": {
      "type": "object",
      "properties": {
        "archetype": { "type": "string", "description": "캐릭터 원형 (영웅, 현자, 반란자 등)" },
        "voice_tone": { "type": "string" },
        "world_view": { "type": "string" },
        "summary": { "type": "string", "maxLength": 500 }
      }
    }
  }
}
```

### 3.2 Backend

| 파일 | 변경 유형 | 변경 내용 |
|------|---------|---------|
| `app/routers/dimension/mirror.py` | NEW | 심연의 거울 라우터 |
| `app/services/mirror_service.py` | NEW | 사주 웹서칭, 채팅 로직 |
| `app/schemas/mirror.py` | NEW | 요청/응답 스키마 |

### 3.3 Frontend

| 파일 | 변경 유형 | 변경 내용 |
|------|---------|---------|
| `src/components/dimension/AbyssMirrorPanel.tsx` | NEW | 메인 패널 |
| `src/components/dimension/MirrorChatInterface.tsx` | NEW | 채팅 UI |
| `src/components/dimension/MirrorProgressBar.tsx` | NEW | 진행률 바 |

### 3.4 채팅 흐름

```
[초기 입력]
  ↓
[웹서칭: 사주 해석] → 진행률 25%
  ↓
[채팅 시작: 매슬로우/무의식 질문]
  ↓ (15회 이상 반복, JSON 점진적 업데이트)
[진행률 80% 도달]
  ↓
[완료 유도 UI 표시]
  ↓
[프리셋 JSON 저장]
```

---

## 4. UI/UX 설계

### 4.1 화면 흐름

```
[입력 폼] → [분석 중 (웹서칭)] → [채팅 인터페이스] → [완료 & 프리셋 저장]
```

### 4.2 진행률 기준

| 단계 | 진행률 | 조건 |
|------|-------|------|
| 초기 입력 | 0% | 시작 |
| 사주 웹서칭 완료 | 25% | 사주 필드 채움 |
| 채팅 진행 | 25-80% | 질문 수 + 필드 완성도 |
| 완료 가능 | 80%+ | 핵심 필드 모두 채움 |
| 완료 | 100% | 사용자 확인 |

### 4.3 상태 처리

| 상태 | UI 표현 |
|------|--------|
| Loading (웹서칭) | 스켈레톤 + "사주 분석 중..." |
| Chatting | 채팅 UI + 진행률 바 |
| Ready to Complete | "완료하기" 버튼 활성화 |
| Saved | 성공 토스트 + 프리셋 다운로드 옵션 |

---

## 5. 사주 데이터 소스

| 우선순위 | 사이트 | 설명 |
|---------|-------|------|
| 1 | 만세력닷컴 | 정통 통계학 기반 사주 |
| 2 | 사주포럼 | 커뮤니티 해석 |
| 3 | 웹 종합 검색 | Gemini 웹서칭 |

---

## 6. 엣지 케이스 & 에러 처리

| 상황 | 처리 방법 |
|------|---------|
| 웹서칭 실패 | 기본 사주 템플릿 사용, 재시도 버튼 |
| 세션 이탈 | 로컬스토리지 임시 저장 (세션 저장 구현 시 DB) |
| 크레딧 부족 | 표준 CreditGate 적용 |

---

## 7. 트레이드오프 결정

| 결정 사항 | 선택 | 이유 |
|---------|------|------|
| 세션 저장 | 로컬스토리지 우선 | DB 저장은 구현 복잡도 높음, 추후 업그레이드 |
| 채팅 모델 | Gemini 3 Flash Preview | 기존 시스템 호환 |
| 파일 업로드 | 추후 구현 | 현재 스코프에서 제외 |

---

## 8. 테스트 계획

- [ ] Unit: `test_mirror_service.py` - 사주 파싱, JSON 생성
- [ ] Integration: `test_mirror_router.py` - API 엔드포인트
- [ ] E2E: `mirror-flow.spec.ts` - 전체 플로우

---

## 9. 인터뷰 Q&A 로그

### Q1: 핵심 가치?
**A**: 사주+MBTI+혈액형 조합 → 심층 페르소나 추출 → JSON 프리셋으로 다른 앱에 활용

### Q2: 분석 대상?
**A**: 파일 업로드 자유롭게 (추후), 현재는 채팅 기반

### Q3: 출력 형태?
**A**: JSON 프리셋, 개인별 자동 저장

### Q4: 진행률 기준?
**A**: 스키마 완성도, 최소 15회 티키타카, 80% 넘으면 완료 유도

### Q5: 세션 저장?
**A**: 가능하면 좋지만 구현 복잡도 체크 필요 → 로컬스토리지 우선

---

## 10. 최종 체크리스트

- [x] Backend 라우터/서비스 구현 (`routers/dimension/mirror.py`, `services/mirror_service.py`)
- [x] Frontend 패널/채팅 구현 (`AbyssMirrorPanel.tsx`, `abyss/page.tsx`)
- [x] 진행률 시스템 구현
- [x] 웹서칭 연동
- [x] JSON 프리셋 저장/로드
- [x] 테스트 작성 (`test_mirror_service.py`, `test_mirror_run_token.py`)
- [x] 검증 완료 (2026-01-15)
