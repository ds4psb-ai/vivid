# 🎨 IMAGE PROMPTS: Umbrella Encounter

> **Project**: umbrella-parody
> **Tool**: Midjourney V7 (ANCHOR) / NanoBanana Pro (Other)
> **Date**: 2026-02-02
> **Based on**: docs/ANALYSIS.md (Gemini CLI 분석)

---

## 🔗 ANCHOR 시스템

| 순서 | Scene | Tool | Reference | Status |
|------|-------|------|-----------|--------|
| 1 | **#2 ⭐ ANCHOR_GIRL** | MJ V7 | 없음 | ⬜ 먼저! |
| 2 | **#3 ⭐ ANCHOR_BOY** | MJ V7 | 없음 | ⬜ 두번째! |
| 3 | #1 | NanoBanana | ANCHOR_GIRL, ANCHOR_BOY | ⬜ |
| 4 | #4 | NanoBanana | ANCHOR_BOY | ⬜ |
| 5 | #5 | NanoBanana | ANCHOR_GIRL | ⬜ |

---

# 🏗️ PHASE 1: ANCHOR (얼굴 확정)

## 📼 Cut #2 ⭐ ANCHOR_GIRL

> **Goal**: ID_GIRL 얼굴 확정 → 모든 씬에서 재사용
> **Tool**: Midjourney V7

### [📋 COPY TO MJ]

```
Close-up portrait of a beautiful Korean::2 female high school student.

Face: Soft oval shape, fair skin, rosy natural makeup, pink lips.
Hair: Long dark brown wavy hair, parted in middle, falling past shoulders.
Eyes: Korean features, large almond-shaped, dark brown, defined lashes.
Expression: Cold confusion, slightly annoyed, looking at someone off-camera.

She is holding a clear transparent umbrella handle near her face.
Background: Soft bokeh of green foliage, rainy day atmosphere.

Lighting: Soft diffused natural light (overcast), gentle fill on face.
Mood: K-drama romantic tension, cinematic quality.

--ar 9:16 --v 7 --style raw --iw 2.0 --cw 80
--no western features, double eyelids, blonde hair, blue eyes, heavy makeup, smile
```

> 💾 **결과물 저장** → `generated/images/selected/ANCHOR_GIRL.png`

---

## 📼 Cut #3 ⭐ ANCHOR_BOY

> **Goal**: ID_BOY 얼굴 확정 → 모든 씬에서 재사용
> **Tool**: Midjourney V7

### [📋 COPY TO MJ]

```
Medium close-up portrait of a Korean::2 male high school student.

Face: Oval shape, clean-shaven, fair skin, panicked embarrassed expression.
Hair: Black, straight, short bowl cut with bangs covering forehead.
Eyes: Korean features, dark brown, widened with shock and embarrassment.
Expression: Mouth slightly open, apologetic panic, caught in awkward moment.

He wears a white long-sleeved button-up shirt (slightly unbuttoned at top).
Background: Rainy outdoor park with benches, soft bokeh.

Lighting: Soft overcast natural light, gentle shadows.
Mood: K-drama comedic tension, cinematic quality.

--ar 9:16 --v 7 --style raw --iw 2.0 --cw 80
--no western features, double eyelids, blonde hair, blue eyes, beard, calm expression
```

> 💾 **결과물 저장** → `generated/images/selected/ANCHOR_BOY.png`

---

# 🏗️ PHASE 2: SCENE IMAGES

## 📼 Cut #1: The Intrusion (00:00-00:01)

> **Tool**: NanoBanana Pro
> **Characters**: ID_BOY (running in), ID_GIRL (holding umbrella)

### [📋 COPY TO NANOBANANA]

```
**[Image 1: ID_GIRL FACE]** ANCHOR_GIRL.png
**[Image 2: ID_BOY FACE]** ANCHOR_BOY.png

**From Image 1**: Copy the girl's face exactly.
**From Image 2**: Copy the boy's face exactly.

Medium cinematic shot from behind/side angle.
Outdoor park or campus setting with paved wet ground.
Green trees and benches blurred in background.
Rain falling visibly.

Characters:
- Korean female student (face from Image 1): Standing still, holding clear transparent umbrella, facing away/side profile. Wearing white button-up shirt, navy ribbon tie, navy pleated skirt, pink backpack.
- Korean male student (face from Image 2): Rushing in from left side, hunched over to avoid rain, entering under the umbrella. Wearing white shirt, black trousers, large black backpack.

Lighting: Soft overcast, diffused natural light.
Mood: K-drama romantic comedy, slightly comedic tension.
Color: Cool desaturated greens and blues, DAYTIME RAIN DRAMA KEY.

--ar 9:16
--no western features, sunny weather, dry ground, smiling faces
```

---

## 📼 Cut #4: The Escape (00:05-00:06)

> **Tool**: NanoBanana Pro
> **Characters**: ID_BOY (running away), ID_GIRL (shoulder visible)

### [📋 COPY TO NANOBANANA]

```
**[Image 1: ID_BOY FACE]** ANCHOR_BOY.png

**From Image 1**: Copy the boy's face (back of head visible, side profile if turning).

Wide shot.
Korean male student with large black backpack running away desperately.
He is wearing white shirt and black pants.
Running on wet paved path past a brick building and green bushes.
Rain falling on the scene.

In foreground corner: Clear umbrella edge and girl's shoulder visible (framing device).

Lighting: Overcast natural light, wet reflections on ground.
Mood: Comedic escape, embarrassment, K-drama aesthetic.
Color: DAYTIME RAIN DRAMA KEY.

--ar 9:16
--no western features, sunny day, dry ground, walking slowly
```

---

## 📼 Cut #5: The Bewilderment (00:06-00:07)

> **Tool**: NanoBanana Pro
> **Characters**: ID_GIRL (staring forward)

### [📋 COPY TO NANOBANANA]

```
**[Image 1: ID_GIRL FACE]** ANCHOR_GIRL.png

**From Image 1**: Copy the girl's face exactly.

Close-up front view of Korean female student under clear transparent umbrella.
She looks bewildered and speechless, blinking slowly.
Eyes following someone off-camera (the fleeing boy).

She wears white button-up shirt with navy collar/ribbon tie.
Long dark wavy hair frames her face.

Lighting: Soft diffused overcast light, clean and dramatic.
Mood: K-drama reaction shot, comedic confusion.
Color: DAYTIME RAIN DRAMA KEY.

--ar 9:16
--no western features, smiling, laughing, angry expression
```

---

## ✅ 체크리스트

### ANCHOR Phase
- [ ] ANCHOR_GIRL 생성 → Critique → 확정
- [ ] ANCHOR_BOY 생성 → Critique → 확정

### Scene Phase
- [ ] Cut #1 생성 (ANCHOR 참조)
- [ ] Cut #4 생성 (ANCHOR_BOY 참조)
- [ ] Cut #5 생성 (ANCHOR_GIRL 참조)

### Quality
- [ ] 모든 씬 COLOR KEY 일관성
- [ ] 캐릭터 얼굴 ANCHOR와 일치
- [ ] 의상 색깔 원본과 일치
- [ ] 비 효과 + 젖은 바닥 표현

---

## 📝 Notes

### 특별 주의사항
1. **투명 우산**: "clear transparent umbrella" 반복 명시
2. **비 표현**: "rain falling", "wet ground/pavement" 필수
3. **교복 색상**: 흰 셔츠 + 네이비 (tie, skirt)
4. **핑크 가방**: ID_GIRL 특징, 일관성 유지

### Negative 공통
```
--no western features, double eyelids, blonde hair, blue eyes, sunny weather, dry ground
```
