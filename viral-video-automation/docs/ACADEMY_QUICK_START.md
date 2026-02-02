# 🎓 TIKI-TAKA ACADEMY: Quick Start Guide

> **For**: 아카데미 Day 1 시작용
> **Version**: 1.0 (2026-02-02)
> **Prerequisites**: 없음 (완전 초보자 가능)

---

## 🎯 오늘의 목표

```
✅ 티키타카 철학 이해
✅ Gemini로 영상 분석
✅ Claude로 프롬프트 정제
✅ 첫 번째 ANCHOR 이미지 생성
```

---

## 📋 STEP 0: 환경 준비 (5분)

### 필요한 것들

| 도구 | 용도 | 접속 방법 |
|------|------|----------|
| **Gemini** | 영상 분석 | gemini.google.com |
| **Claude Code** | 프롬프트 정제 | Antigravity (로컬) |
| **NanoBanana** | 이미지 생성 | nanobanana.com |
| **샘플 영상** | 실습 대상 | 제공됨 |

### 폴더 확인

```bash
# 작업 폴더 위치
cd ~/vivid/viral-video-automation

# 구조 확인
ls -la
# docs/      templates/      scripts/      projects/
```

---

## 🧠 STEP 1: 티키타카 철학 이해 (10분)

### 핵심 개념

```
🏓 TIKI-TAKA = 반복 정제 > 한 번에 완벽

ONE-SHOT:  [생성] → [사용]         → 85% 품질
TIKI-TAKA: [생성] → [평가] → [수정] → [평가] → ... → 98% 품질
```

### 워크플로우

```
Gemini (분석) ←→ Claude (정제) → 생성 도구 → Human (최종 판단)
     ↑                                              ↓
     └──────────── Feedback Loop ─────────────────┘
```

### 왜 Human-in-the-Loop인가?

```
❌ AI가 "대신" 만들어주는 것
✅ AI가 "함께" 만드는 것

- AI: 분석, 평가, 제안
- Human: 창작 의도, 최종 결정
```

---

## 🔍 STEP 2: Gemini로 영상 분석 (15분)

### 2.1 샘플 영상 준비

```bash
# kylenutt-parody 예제 영상 위치
ls projects/kylenutt-parody/reference/
# source.mp4
```

### 2.2 Gemini 접속

1. **gemini.google.com** 접속
2. 로그인 (Google 계정)
3. **+** 버튼으로 새 대화

### 2.3 분석 요청

**[📋 COPY TO GEMINI]**

```
영상을 첨부합니다. 이 영상을 분석해서 아래 형식으로 출력해주세요:

## 컷 분해
| Scene | 시작 | 끝 | 설명 |
|-------|-----|-----|------|

## 캐릭터 프로파일
- 주인공: [나이, 성별, 외형]
- 조연: [역할, 외형]

## 시각 스타일
- 조명: [색온도, 방향]
- 색감: [따뜻함/차가움]
- 시대: [1990s/2020s]

## ANCHOR 씬 추천
캐릭터 얼굴이 가장 잘 보이는 씬 번호와 이유

## 도구 추천
- 이미지: NanoBanana / Midjourney
- 영상: Kling / Sora
```

### 2.4 결과 저장

Gemini 결과를 복사해서:
```bash
# 새 프로젝트면
mkdir -p projects/my-first/docs
# 결과 붙여넣기
# projects/my-first/docs/ANALYSIS.md
```

---

## 🔄 STEP 3: Claude로 프롬프트 정제 (15분)

### 3.1 Claude Code 실행

```bash
# Antigravity Claude Code
claude
```

### 3.2 프롬프트 정제 요청

**[📋 COPY TO CLAUDE]**

```
아래 Gemini 분석 결과를 기반으로 NanoBanana Pro용 이미지 프롬프트를 만들어줘.

## Gemini 분석 결과
[여기에 Gemini 결과 붙여넣기]

## 규칙
1. ANCHOR 씬 프롬프트 먼저 (얼굴 확정용)
2. 모든 인물 → 한국인으로 변경
3. 의상 색깔 원본 유지
4. --no 파라미터에 제외할 요소 포함

## 출력 형식
각 씬별로:
### Scene [N]: [이름]
**[📋 COPY]**
```
[프롬프트]
```
```

### 3.3 결과 저장

```bash
# 프롬프트 파일로 저장
# projects/my-first/prompts/IMAGE_PROMPTS.md
```

---

## 🎨 STEP 4: 첫 ANCHOR 이미지 생성 (20분)

### 4.1 NanoBanana Pro 접속

1. **nanobanana.com** 접속
2. 로그인
3. **Create** 클릭

### 4.2 ANCHOR 씬 생성

```
WHY ANCHOR FIRST?
- 캐릭터 얼굴 확정
- 이 얼굴을 모든 씬에서 참조
- 일관성 유지의 핵심
```

**예시 프롬프트 (Claude가 생성한 것 사용):**

```
7-year-old Korean boy, close-up portrait.
Black bowl cut hair (1990s Korean style), single eyelids.
Warm candlelight illuminating face from below.
Shy, gentle smile with lips closed.
Looking at birthday cake, eyes sparkling with anticipation.

Lighting: Warm tungsten 3200K, underlit by candle flames.
Mood: Nostalgic, intimate, warm.
Style: 1990s home video aesthetic, soft focus edges.

--no western features, blonde hair, blue eyes, double eyelids
```

### 4.3 결과 평가

**Claude에게 Critique 요청:**

```
이 이미지를 평가해줘.

[이미지 첨부 또는 설명]

## 평가 기준
1. 프롬프트 준수: 의도대로 생성됐나?
2. 캐릭터: 한국인으로 보이나?
3. 해부학: 손/얼굴 왜곡?
4. 조명: 따뜻한 촛불 느낌?

## 출력
- 판정: PASS / REVISE / REJECT
- 점수: 0-100
- 강점:
- 약점:
- 개선 제안:
```

### 4.4 결과에 따른 행동

| 판정 | 행동 |
|------|------|
| **PASS** (85+) | → ANCHOR.png로 저장, 다음 씬 진행 |
| **REVISE** (60-84) | → Claude 제안대로 수정 후 재생성 |
| **REJECT** (<60) | → 프롬프트 전면 재검토 |

---

## 💾 STEP 5: 저장 및 정리 (5분)

### 5.1 ANCHOR 저장

```bash
# 확정된 ANCHOR 이미지 저장
cp ~/Downloads/anchor.png projects/my-first/generated/images/selected/ANCHOR.png
```

### 5.2 STATE.md 업데이트

```markdown
# State: my-first

## 📊 Scene Progress

| Scene | Status |
|-------|--------|
| ANCHOR (Scene 2) | ✅ 확정 |
| Scene 1 | ⬜ 대기 |
| Scene 3 | ⬜ 대기 |

## 🚧 다음 작업
- Scene 1 이미지 생성 (ANCHOR 참조)
```

---

## 🏁 Day 1 완료!

### 오늘 배운 것

```
✅ 티키타카 = 반복 정제 > 한 번에 완벽
✅ Gemini = 분석 전문가
✅ Claude = 정제 전문가
✅ ANCHOR = 일관성의 핵심
✅ Critique = PASS / REVISE / REJECT
```

### 숙제 (선택)

```
1. 나머지 씬 이미지 프롬프트 확인
2. Scene 1 이미지 생성 시도
3. Critique 결과 기록
```

---

## 📚 참고 자료

| 문서 | 용도 |
|------|------|
| `templates/MODE_TIKITAKA.md` | 전체 워크플로우 |
| `templates/CRITIQUE_IMAGE.md` | 이미지 평가 기준 |
| `templates/TOOL_NANOBANANA.md` | NanoBanana 사용법 |
| `projects/kylenutt-parody/` | 완성된 예제 |

---

## ❓ FAQ

### Q: Gemini 분석이 부정확해요
```
A: 추가 질문으로 정제하세요.
   "Scene 3의 배경 인물 의상 색깔을 더 자세히 알려줘"
```

### Q: 이미지가 한국인처럼 안 보여요
```
A: Negative prompt 강화
   --no western features, caucasian skin, double eyelids

   Positive 강화
   "Korean boy, single eyelids, natural Korean skin tone"
```

### Q: 손이 이상해요
```
A: 손 숨기기 전략
   "hands hidden behind table" 또는
   "hands clasped together"

   Negative 추가
   --no deformed hands, extra fingers
```

---

> **Day 2 Preview**: 전체 씬 이미지 완성 + Multi-Entity Consistency
