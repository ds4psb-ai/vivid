# State: {PROJECT_NAME}

> **Purpose**: 동적 진행 상황 추적 (AI가 업데이트)
> **Last Updated**: {DATE} {TIME}

---

## 📊 Scene Progress

| Scene | Description | Image | Video | Status |
|-------|-------------|-------|-------|--------|
| 1 | Arrival | v2/scene01.png | - | ✅ 확정 |
| 2 | Anticipation (ANCHOR) | v3/scene02.png | - | ✅ 확정 |
| 3 | Confusion | v1/scene03.png | - | ✅ 확정 |
| 4 | Awkward Smile | 작업 중 | - | 🔄 진행 |
| 5 | Cut to Modern | - | - | ⬜ 대기 |
| 6 | Modern Capture | - | - | ⬜ 대기 |
| 7 | Flash Shock | - | - | ⬜ 대기 |
| 8 | Recovery | - | - | ⬜ 대기 |
| 9 | Close-up | - | - | ⬜ 대기 |
| 10 | Departure | - | - | ⬜ 대기 |

---

## 📈 Overall Progress

```
Stage 1 (Analysis):  ████████████████████ 100%
Stage 2 (Image):     ████████░░░░░░░░░░░░  40%
Stage 3 (Video):     ░░░░░░░░░░░░░░░░░░░░   0%
Stage 4 (Assembly):  ░░░░░░░░░░░░░░░░░░░░   0%
```

---

## 🚧 Current Task

**Scene 4 이미지 생성**

### 시도 이력
| Ver | 결과 | 문제 |
|-----|------|------|
| v1 | REJECT | 손가락 6개 |
| v2 | - | 대기 중 |

### 다음 액션
- `--no deformed hands, extra fingers` 추가하여 재생성

---

## 💬 Last Conversation Summary

```
마지막 세션: 2026-02-02 00:30

1. 사용자: Scene 4 이미지 첨부
2. AI: REVISE 판정 (Score: 65)
   - 문제: 손가락 왜곡
   - 제안: negative prompt 추가
3. 사용자: "수정해서 재생성할게"

→ 다음: 사용자가 수정된 이미지 첨부 예정
```

---

## 📝 Session Notes

### 2026-02-02 (오늘)
- Scene 1-3 이미지 확정
- ANCHOR (Scene 2) 최종 선택: v3
- Scene 4 시작, 손 문제 발견

### 2026-02-01
- 프로젝트 초기 설정
- ANALYSIS.md, PROFILES.md 완성

---

## 🔖 Blockers

| 문제 | 상태 | 해결책 |
|------|------|--------|
| Scene 4 손 왜곡 | 🔄 진행 | --no 파라미터 |

---

## ✅ Decisions Made

| 날짜 | 결정 | 이유 |
|------|------|------|
| 02-02 | ANCHOR = Scene 2 v3 | 얼굴 가장 정확 |
| 02-02 | Tool = NanoBanana | 다인물 구도 |

---

## 📌 Quick Resume Prompt

```
"지난 작업 이어서 하자. STATE.md 보고 다음 할 일 알려줘."
```
