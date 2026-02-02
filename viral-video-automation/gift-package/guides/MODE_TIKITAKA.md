# 🎯 TIKI-TAKA MODE (퀄리티 우선)

> **용도**: 최종 결과물, 완벽한 퀄리티 필요 시
> **워크플로우**: Success Brief → Draft → Critique → Revise
> **예상 시간**: 30분 / 예상 퀄리티: 98%

---

## 📊 ONE-SHOT vs TIKI-TAKA

| 항목 | ONE-SHOT | **TIKI-TAKA** |
|------|----------|---------------|
| 왕복 | 2회 | **5-6회** |
| 시간 | 10분 | **30분** |
| 퀄리티 | 85% | **98%** |
| 용도 | 빠른 테스트 | 최종 결과물 |

---

## 🔄 6단계 워크플로우

```
STEP 1: Success Brief (Gemini)
        ↓
STEP 2: Draft (Claude)
        ↓
STEP 3: Critique (Gemini)
        ↓
STEP 4: Revise (Claude)
        ↓
STEP 5: Generate + Review
        ↓
STEP 6: Micro-adjust
```

---

## 📝 STEP 1: Success Brief (Gemini)

### 목표
"성공"이 무엇인지 명확히 정의

### ⚠️ 필수 첨부
- 📎 **원본 영상 파일** (또는 URL)
- 📎 **추출된 키프레임** (있다면)

### Gemini에게 보내기
```
[영상 파일 첨부]

이 영상을 분석해서 아래 항목을 정의해줘:

### 성공 기준
1. **핵심 인물**: 누가 나오는가? (모든 사람, 흐릿해도)
2. **구도**: 정확히 어떤 구도인가? (shot type, angle)
3. **조명**: 색온도, 방향, 분위기
4. **시대**: 1990s vs 2020s
5. **감정**: 어떤 분위기를 전달해야 하는가?

### 잠재적 문제
- 이 씬에서 AI가 실수할 수 있는 것들
- 예: "배경 인물을 서양인으로 생성할 수 있음"

### 출력 형식
JSON으로 구조화해서 출력
```

---

## 📝 STEP 2: Draft (Claude)

### 목표
Gemini JSON을 기반으로 초안 프롬프트 생성

### Claude에게 보내기
```
아래 JSON을 기반으로 각 씬의 프롬프트 초안을 만들어줘.

[Gemini JSON 붙여넣기]

### 규칙
1. ALL PEOPLE Rule 적용 (모든 인물 한국인 명시)
2. 복수 레퍼런스 시 라벨링 필수
3. 도구별 형식 (NanoBanana = 한글, MJ = 영어+파라미터)
4. error_prevention → --no 변환
```

---

## 📝 STEP 3: Critique (Gemini)

### 목표
AI가 스스로 초안의 문제점 발견

### ⚠️ 필수 첨부
- 📎 **원본 영상 파일** (프롬프트와 원본 비교용)

### Gemini에게 보내기
```
[원본 영상 파일 첨부]

아래 프롬프트 초안을 원본 영상과 비교하며 비평해줘.

[Claude 초안 붙여넣기]

### 비평 관점
1. **완전성**: 원본 영상의 모든 인물이 한국인으로 명시되었는가?
2. **구체성**: 모호한 표현이 있는가?
3. **일관성**: ANCHOR와 다른 씬이 연결되는가?
4. **에러 방지**: --no에 빠진 항목이 있는가?
5. **도구 적합성**: 도구별 형식이 맞는가?

### 출력 형식
각 씬별로:
- 문제점
- 개선 제안
```

---

## 📝 STEP 4: Revise (Claude)

### 목표
비평 반영하여 프롬프트 수정

### Claude에게 보내기
```
Gemini 비평을 반영해서 프롬프트를 수정해줘.

### 원본 초안
[STEP 2 결과]

### Gemini 비평
[STEP 3 결과]

### 수정 규칙
1. 비평에서 지적한 모든 문제 해결
2. 새로운 문제 만들지 않기
3. 변경 사항 설명 포함
```

---

## 📝 STEP 5: Generate + Review

### 목표
실제 생성 후 직접 검토

### 체크리스트 (QA_CHECKLIST.md 참조)
- [ ] 모든 인물 한국인?
- [ ] 배경 인물도 한국인 피부톤?
- [ ] 의상 색깔 원본과 동일?
- [ ] 구도 정확?
- [ ] 조명 맞음?

---

## 📝 STEP 6: Micro-adjust

### 목표
재생성 없이 미세조정

### 방법
| 문제 | 해결 |
|------|------|
| 배경 인물 서양인 | `--no background caucasian` 추가 |
| 케이크 2개 | `--no cake on table, duplicate cake` 추가 |
| 의상 색깔 다름 | 프롬프트에 색깔 더 강조 |

---

## 📈 A/B 테스트 피드백

TIKI-TAKA에서 발견한 문제점 → ONE-SHOT 개선에 반영

```
문제: Scene 1에서 배경 부모가 서양인으로 나옴

개선: GEMINI_ONESHOT.md의 error_prevention에 추가
      "background people caucasian skin"
```

---

## 🔑 핵심 원칙

1. **반복 정제** > 한 번에 완벽
2. **AI 자체 비평**으로 문제 조기 발견
3. **Human-in-the-Loop**: 최종 결정은 사람
4. **피드백 루프**: 발견 → 개선 → ONE-SHOT 고도화
