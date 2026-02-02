# STEP-BY-STEP 6단계 가이드

> **Tiki-Taka Mode**: Gemini <-> Claude 핑퐁으로 98% 퀄리티 달성
> **예상 시간**: 30분 | **예상 퀄리티**: 98%

---

## 터미널 준비 (2분할)

```
┌─────────────────────┬─────────────────────┐
│  Terminal 1         │  Terminal 2         │
│  gemini             │  claude/antigravity │
│  (영상 분석)        │  (프롬프트 정제)    │
└─────────────────────┴─────────────────────┘
```

---

## STEP 1: Success Brief (Gemini)

### 목표
영상 분석 -> JSON 형식 성공 기준 정의

### 첨부
- `reference/source.mp4` (원본 영상)

### 복사용 프롬프트

━━━━━━ COPY START ━━━━━━
```
@{reference/source.mp4}

이 영상을 분석해줘. 아래 형식으로 출력:

## CUT-BY-CUT (0.01초 정밀도)
| Cut | Timecode | Duration | Description | Camera | Subject |
|-----|----------|----------|-------------|--------|---------|
| 1 | 00:00.00~00:02.34 | 2.34s | ... | Medium | ... |

## CHARACTER PROFILES (ALL PEOPLE - 흐릿한 배경 포함!)
각 인물에 대해:
- ID: ID_[역할]
- Ethnicity: Korean (필수!)
- Age, Hair, Clothing 색상, Position (9-Grid)

## VISUAL STYLE
- Color Temperature: [K값]
- Era: 1990s or 2020s
- Film Style: Kodak Portra 400 / Digital Sharp

## ANCHOR 추천
- Cut #:
- 이유: (얼굴 선명, 조명 좋음, 정면/3/4 앵글)

## ERROR PREVENTION (AI 실수 가능 항목)
- 예: "배경 인물 서양인으로 생성 가능"
- 예: "1990년대인데 스마트폰 등장 가능"

## --no 리스트 (시대별)
1990s: --no western features, caucasian skin, blonde, blue eyes, smartphones, LED lights, modern furniture
2020s: --no warm lighting, candles, tungsten, genuine happiness, film grain, retro furniture

## KEYFRAMES_JSON (필수!)
<!-- KEYFRAMES_JSON
{"keyframes":[
  {"timestamp":"00:XX.XX","filename":"scene01","anchor":false},
  {"timestamp":"00:XX.XX","filename":"ANCHOR_IMG","anchor":true}
]}
-->

JSON으로 구조화해서 출력해줘.
```
━━━━━━ COPY END ━━━━━━

### 결과 저장
`docs/ANALYSIS.md`

---

## STEP 2: Draft (Claude)

### 목표
분석 결과 -> 도구별 프롬프트 초안

### 첨부
- `docs/ANALYSIS.md` (STEP 1 결과)

### 복사용 프롬프트

━━━━━━ COPY START ━━━━━━
```
@docs/ANALYSIS.md

이 분석을 바탕으로 각 씬의 프롬프트 초안을 만들어줘.

## 핵심 규칙

### 1. ALL PEOPLE Rule (절대 규칙)
- 모든 인물을 "한국인"으로 명시 (흐릿한 배경 인물 포함!)
- "Korean" 키워드 필수
- 피부톤: "Korean skin tone"
- 눈: "single eyelids" (홑꺼풀)

### 2. 복수 레퍼런스 라벨링
- **Image 1 (구도용)**: [scene.png]
- **Image 2 (얼굴용)**: [ANCHOR.png]

### 3. 도구별 형식
- NanoBanana = 한글 프롬프트
- Midjourney V7 = 영어 + 파라미터 (--iw, --cw, --oref, --no)
- Kling 2.6 = Elements + Beat Timing
- Veo 3.1 = Dialogue + Emotion

### 4. Error Prevention -> --no 변환
분석의 error_prevention 항목을 --no 파라미터로 변환

## 출력 형식

### NanoBanana (한글)
[전체 프롬프트]

### Midjourney V7 (영어 + 파라미터)
[전체 프롬프트]

### Kling 2.6 (영상)
[전체 프롬프트]

### Veo 3.1 (대사 있는 영상)
[전체 프롬프트]
```
━━━━━━ COPY END ━━━━━━

### 결과 저장
`prompts/IMAGE_PROMPTS.md`

---

## STEP 3: Critique (Gemini)

### 목표
프롬프트 초안 비평 (5D×23 체크리스트)

### 첨부
- `reference/source.mp4` (원본 영상)
- `prompts/IMAGE_PROMPTS.md` (STEP 2 결과)

### 복사용 프롬프트

━━━━━━ COPY START ━━━━━━
```
@{reference/source.mp4}

아래 프롬프트 초안을 원본 영상과 비교하며 비평해줘.

[IMAGE_PROMPTS.md 내용 붙여넣기]

---

## 5차원 23항목 평가 체크리스트

### 1. 프롬프트 준수 (25%) - 6항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| 주제 정확히 표현됨 | | |
| 배경/환경 의도대로 생성됨 | | |
| 조명/색감 K값 명시 | | |
| 스타일(1990s/2020s) 반영 | | |
| 누락된 요소 없음 | | |
| 불필요한 추가 요소 없음 | | |

### 2. 미적 품질 (20%) - 4항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| 구도 원본과 동일 | | |
| 색감 조화 시대에 맞음 | | |
| 조명 자연스러움 | | |
| 전체적 임팩트 | | |

### 3. 기술적 완성도 (15%) - 4항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| 해상도/선명도 충분 | | |
| 텍스처 자연스러움 | | |
| 노이즈/그레인 적절 | | |
| 아티팩트 방지 --no 포함 | | |

### 4. 캐릭터 일관성 (25%) - 5항목 ⭐ 가장 중요
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| 얼굴 ANCHOR 참조 명시 | | |
| 헤어스타일 원본과 동일 | | |
| 민족/피부톤 한국인 (ALL PEOPLE) | | |
| 의상 색상/스타일 정확 | | |
| 나이 적절 | | |

### 5. 해부학/물리 방지 (15%) - 4항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| 손 --no 6 fingers 포함 | | |
| 얼굴 왜곡 방지 문구 | | |
| 신체 비율 자연스러움 | | |
| 물리적 논리(중력, 그림자) | | |

---

## 판정 기준
- ✅ PASS (85점 이상): 바로 사용 가능
- 🔄 REVISE (60-84점): 수정 후 재생성
- ❌ REJECT (60점 미만): 전면 재작성

## 출력 형식
총점: /100
판정: PASS / REVISE / REJECT

### 강점 (Keep)
-

### 약점 (Fix)
-

### 씬별 개선 제안
| 씬 | 문제점 | 개선 방향 |
|----|--------|----------|
```
━━━━━━ COPY END ━━━━━━

### 결과 저장
`docs/CRITIQUE_LOG.md`

---

## STEP 4: Revise (Claude)

### 목표
비평 반영 -> 프롬프트 수정

### 첨부
- `prompts/IMAGE_PROMPTS.md` (STEP 2 결과)
- `docs/CRITIQUE_LOG.md` (STEP 3 결과)

### 복사용 프롬프트

━━━━━━ COPY START ━━━━━━
```
Gemini 비평을 반영해서 프롬프트를 수정해줘.

### 원본 초안
[IMAGE_PROMPTS.md 내용]

### Gemini 비평
[CRITIQUE_LOG.md 내용]

---

## 수정 규칙

### 1. 비평 지적사항 모두 해결
- 각 약점(Fix) 항목 하나씩 해결
- 씬별 개선 제안 모두 반영

### 2. 새로운 문제 만들지 않기
- 기존 강점(Keep) 유지
- --no 항목 삭제하지 않기

### 3. 변경 사항 명시적 설명
각 수정에 대해:
- Before: [원본]
- After: [수정본]
- 이유: [왜 수정했는지]

---

## 출력 형식

### 변경 로그
| 항목 | Before | After | 이유 |
|------|--------|-------|------|

### 수정된 프롬프트 (최종)

**NanoBanana (한글):**
[수정된 전체 프롬프트]

**Midjourney V7:**
[수정된 전체 프롬프트]

**Kling 2.6:**
[수정된 전체 프롬프트]

**Veo 3.1:**
[수정된 전체 프롬프트]
```
━━━━━━ COPY END ━━━━━━

### 결과 저장
`prompts/IMAGE_PROMPTS.md` (덮어쓰기)

---

## STEP 5: Generate + Review (User)

### 목표
실제 이미지/영상 생성 + QA 체크

### 도구
- NanoBanana Pro: https://nanobanana.ai
- Midjourney: Discord
- Kling: https://klingai.com
- Veo: https://labs.google/fx/tools/veo

### QA 체크리스트

━━━━━━ COPY START ━━━━━━
```
## QA 체크리스트

### 캐릭터 일관성 (가장 중요)
- [ ] 모든 인물이 한국인인가? (피부톤, 눈 모양)
- [ ] 배경 인물도 한국인 피부톤인가?
- [ ] 주인공 얼굴이 ANCHOR와 일치하는가?
- [ ] 헤어스타일이 원본과 동일한가?

### 구도/조명
- [ ] 구도가 원본과 정확히 일치하는가?
- [ ] 의상 색깔이 원본과 동일한가?
- [ ] 조명 색온도가 맞는가? (3200K/6500K)
- [ ] 시대 분위기가 맞는가? (1990s/2020s)

### 기술적 품질
- [ ] 손가락 수가 정확한가? (5개)
- [ ] 얼굴 왜곡이 없는가?
- [ ] 아티팩트가 없는가?
- [ ] 해상도가 충분한가?

---

## 점수 기준

| 점수 | 판정 | 다음 액션 |
|------|------|----------|
| 85+ | ✅ PASS | 다음 씬으로 |
| 60-84 | 🔄 REVISE | STEP 6 (Micro-adjust) |
| <60 | ❌ REJECT | STEP 2로 돌아가기 |
```
━━━━━━ COPY END ━━━━━━

### 결과 저장
`generated/images/` (생성된 이미지)

---

## STEP 6: Micro-adjust (User)

### 목표
재생성 없이 파라미터 미세 조정

### 일반적인 문제 -> 해결책

━━━━━━ COPY START ━━━━━━
```
## 문제 -> 해결책

### 캐릭터 관련
| 문제 | 해결책 |
|------|--------|
| 배경 인물 서양인 | `--no background caucasian, western features` |
| 얼굴 불일치 | `--cw 80-100` 올리기 |
| 피부톤 밝음 | `Korean skin tone::2` 강조 |
| 헤어스타일 다름 | 구체적 스타일 명시 (bowl cut, 단발) |

### 구도/조명 관련
| 문제 | 해결책 |
|------|--------|
| 구도 무시됨 | `--iw 2.5` 또는 `--iw 3.0` |
| 조명 차가움 | `--no cold lighting, LED` + `3200K tungsten` |
| 조명 따뜻함 | `--no warm lighting, candles` + `6500K LED` |

### 오브젝트 관련
| 문제 | 해결책 |
|------|--------|
| 케이크 2개 | `--no duplicate cake, cake on table` |
| 현대 가구 | `--no modern furniture, IKEA style` |
| 스마트폰 | `--no smartphones, modern devices` |

### 해부학 관련
| 문제 | 해결책 |
|------|--------|
| 손가락 6개 | `--no 6 fingers, extra fingers, deformed hands` |
| 손 왜곡 | "hands hidden behind back" |
| 얼굴 왜곡 | `--no distorted face, asymmetric features` |

---

## MJ V7 파라미터 Quick Reference

| 파라미터 | 범위 | 권장값 | 용도 |
|----------|------|--------|------|
| `--iw` | 0-3 | 2.0 | 레퍼런스 영향력 |
| `--oref` | URL | ANCHOR URL | 얼굴 고정 |
| `--cw` | 0-100 | 70-90 | 캐릭터 가중치 |
| `--stylize` | 0-1000 | 100-250 | 예술적 해석 |
| `--style raw` | flag | 사용 | 프롬프트 충실도 |

## Text Weight 활용

Korean::2 boy        → "Korean"에 2배 가중치
warm tungsten::1.5   → 1.5배
--no caucasian::2    → 강력 제외
```
━━━━━━ COPY END ━━━━━━

---

## 완료 체크리스트

- [ ] STEP 1: ANALYSIS.md 저장됨
- [ ] STEP 2: IMAGE_PROMPTS.md 초안 저장됨
- [ ] STEP 3: CRITIQUE_LOG.md 저장됨
- [ ] STEP 4: IMAGE_PROMPTS.md 수정 완료
- [ ] STEP 5: 이미지 생성 및 QA 통과
- [ ] STEP 6: 미세 조정 완료 (필요시)

---

## Quick Reference

```
PASS   (85+)  → 다음 단계 진행
REVISE (60-84) → 미세 조정 (STEP 6)
REJECT (<60)  → 처음부터 (STEP 2)
```

**ALL PEOPLE Rule**: 흐릿한 배경 인물도 한국인으로 명시!
