# State: umbrella-parody

> **Purpose**: 동적 진행 상황 추적 (AI가 업데이트)
> **Last Updated**: 2026-02-02 12:00

---

## 📊 Scene Progress

| Cut | Description | ANCHOR | Image | Video | Status |
|-----|-------------|--------|-------|-------|--------|
| 2 | ID_GIRL Close-up | ⭐ ANCHOR_GIRL | - | - | ⬜ 먼저! |
| 3 | ID_BOY Close-up | ⭐ ANCHOR_BOY | - | - | ⬜ 두번째! |
| 1 | The Intrusion | 참조 | - | - | ⬜ 대기 |
| 4 | The Escape | 참조 | - | - | ⬜ 대기 |
| 5 | The Bewilderment | 참조 | - | - | ⬜ 대기 |

---

## 📈 Overall Progress

```
Stage 1 (Analysis):  ████████████████████ 100%  ✅ Gemini CLI 완료
Stage 2 (Image):     ░░░░░░░░░░░░░░░░░░░░   0%  ← 현재
Stage 3 (Video):     ░░░░░░░░░░░░░░░░░░░░   0%
Stage 4 (Assembly):  ░░░░░░░░░░░░░░░░░░░░   0%
```

---

## 🚧 Current Task

**ANCHOR_GIRL 생성 (Cut #2)**

### 다음 액션
1. IMAGE_PROMPTS.md에서 "Cut #2 ANCHOR_GIRL" 프롬프트 복사
2. Midjourney V7에 붙여넣기
3. 결과물 Claude에게 Critique 요청
4. PASS 시 → `ANCHOR_GIRL.png` 저장

---

## 💬 Last Conversation Summary

```
세션: 2026-02-02

1. Gemini CLI: 영상 분석 완료
   - 5컷 분해
   - CHARACTER PROFILES (ID_BOY, ID_GIRL)
   - COLOR KEY (DAYTIME RAIN DRAMA KEY)
   - CUT-BY-CUT 프롬프트

2. Claude Code: 정제 완료
   - docs/ANALYSIS.md 저장
   - prompts/IMAGE_PROMPTS.md 생성
   - ANCHOR 시스템 적용 (ID_GIRL → ID_BOY → 나머지)

→ 다음: ANCHOR_GIRL 이미지 생성
```

---

## 📝 Session Notes

### 2026-02-02
- Gemini CLI로 영상 분석 완료
- Claude Code로 프롬프트 정제
- Dual AI Workflow 첫 적용!
- ANCHOR: ID_GIRL (Cut #2), ID_BOY (Cut #3)

---

## 🔖 Key Decisions

| 날짜 | 결정 | 이유 |
|------|------|------|
| 02-02 | ANCHOR_GIRL = Cut #2 | 클로즈업, 얼굴 가장 선명 |
| 02-02 | ANCHOR_BOY = Cut #3 | 얼굴 보이는 유일한 프론트 뷰 |
| 02-02 | Tool: MJ V7 (ANCHOR), NB (Others) | 얼굴 일관성 vs 구도 유연성 |
| 02-02 | Color Key: DAYTIME RAIN DRAMA | 비 오는 날 로맨틱 무드 |

---

## 📌 Quick Resume Prompts

### Gemini CLI
```
"projects/umbrella-parody/reference/source.mp4 영상의 Cut #2 ID_GIRL 표정을 더 자세히 분석해줘"
```

### Claude Code
```
"projects/umbrella-parody/STATE.md 보고 다음 할 일 알려줘"
```

---

## 📁 Key Files

| 파일 | 상태 |
|------|------|
| docs/ANALYSIS.md | ✅ 완료 |
| prompts/IMAGE_PROMPTS.md | ✅ 완료 |
| prompts/MOTION_PROMPTS.md | ⬜ 대기 (Stage 3) |
| generated/images/selected/ANCHOR_GIRL.png | ⬜ 대기 |
| generated/images/selected/ANCHOR_BOY.png | ⬜ 대기 |
