# 📊 Video Analysis: Umbrella Encounter

> **Source**: "실수로 모르는 여자애 우산 속에 들어갔을 때"
> **Analyzed by**: Gemini CLI
> **Date**: 2026-02-02

---

## 📹 Video Info

| 항목 | 값 |
|------|-----|
| **Duration** | ~7s |
| **Resolution** | 9:16 (Vertical) |
| **Cut Count** | 5 |
| **Style** | Korean Drama / Romantic Comedy |

---

## 📋 1단계: CHARACTER PROFILES

### [CHARACTER PROFILE: ID_BOY]

| 항목 | 값 |
|------|-----|
| **Role** | Male Student (Intruder) |
| **Ethnicity** | Korean |
| **Apparent Age** | 17-19 years old (High School Student) |
| **Hair** | Black, straight, short bowl cut with bangs covering forehead |
| **Face** | Oval shape, clean-shaven, fair skin, surprised expression |
| **Eyes** | Korean features, dark brown, slightly wide with shock |
| **Clothing** | White long-sleeved button-up shirt (unbuttoned at top), black trousers, large black backpack with straps |
| **Position** | Initially running into frame, then standing close to girl, then running away |

---

### [CHARACTER PROFILE: ID_GIRL]

| 항목 | 값 |
|------|-----|
| **Role** | Female Student (Umbrella Owner) |
| **Ethnicity** | Korean |
| **Apparent Age** | 17-19 years old (High School Student) |
| **Hair** | Dark brown/Black, long, loose waves, parted in middle |
| **Face** | Soft oval shape, fair skin, rosy makeup |
| **Eyes** | Korean features, large, dark, defined lashes, expression shifts from blank to confused |
| **Clothing** | White button-up shirt, navy blue ribbon tie, navy blue pleated skirt, pink backpack with beige straps |
| **Position** | Standing still holding umbrella, looking at ID_BOY |

---

## 🎨 2단계: COLOR GRADE PROFILES

### [DAYTIME RAIN DRAMA KEY]

| 요소 | 값 |
|------|-----|
| **Tone** | Cool, slightly desaturated greens and blues (Rainy Day) |
| **Grain** | Clean, high-definition digital look |
| **Contrast** | Medium contrast, soft shadows due to overcast sky |
| **Lighting** | Diffused natural light (cloudy), soft fill on faces |
| **Atmosphere** | Romantic drama aesthetic, clear visibility despite rain context |

---

## 🎬 3단계: CUT-BY-CUT PROMPTS

### CUT #1 | 00:00 - 00:01

**[CHARACTERS IN THIS CUT]**
- ID_BOY: Rushes in from left, hunched over to avoid rain, huddles under umbrella.
- ID_GIRL: Standing still, facing away/side profile, holding umbrella.

**[SCENE DESCRIPTION]**
Medium shot from behind/side. Outdoor park or campus setting with paved ground, blurred green trees and benches in background. It is raining. A transparent plastic umbrella covers the girl. Text overlay in Korean floats in air.

**[NANO BANANA PRO PROMPT]**
```
A medium cinematic shot of a Korean male high school student with a black backpack running urgently into the shelter of a clear umbrella held by a Korean female student. The boy wears a white shirt and black trousers. The girl wears a school uniform with a pink backpack. They are outdoors on a rainy day with wet pavement and green trees in the background. Soft overcast lighting.

--ar 9:16
```

**[COLOR CONSISTENCY KEY]**: DAYTIME RAIN DRAMA KEY

---

### CUT #2 | 00:02 - 00:03 ⭐ ANCHOR CANDIDATE

**[CHARACTERS IN THIS CUT]**
- ID_GIRL: Turns head slightly, looks directly at ID_BOY (off-screen/shoulder), expression changes to cold confusion.

**[SCENE DESCRIPTION]**
Close-up shot of ID_GIRL's face. The handle of the umbrella is visible near her face. Background is soft bokeh of green foliage and brown structure.

**[NANO BANANA PRO PROMPT]**
```
A close-up of a beautiful Korean female high school student with long dark wavy hair looking confused and annoyed. She has fair skin and pink lips. She is holding an umbrella handle near her face. Soft natural lighting highlights her features against a blurred rainy background of trees. High definition texture.

--ar 9:16
```

**[COLOR CONSISTENCY KEY]**: DAYTIME RAIN DRAMA KEY

---

### CUT #3 | 00:04 - 00:05 ⭐ ANCHOR CANDIDATE (ID_BOY)

**[CHARACTERS IN THIS CUT]**
- ID_BOY: Realizes mistake, eyes widen, mouth opens slightly, stammers, then bows quickly and turns to run.

**[SCENE DESCRIPTION]**
Medium close-up of ID_BOY over ID_GIRL's shoulder. He looks panicked. Background shows park benches and trees.

**[NANO BANANA PRO PROMPT]**
```
A medium close-up of a Korean male student in a white school shirt looking shocked and embarrassed. He realizes he is under the wrong umbrella. He bows apologetically in a panic. The background is a rainy outdoor park with benches. Cinematic depth of field.

--ar 9:16
```

**[COLOR CONSISTENCY KEY]**: DAYTIME RAIN DRAMA KEY

---

### CUT #4 | 00:05 - 00:06

**[CHARACTERS IN THIS CUT]**
- ID_BOY: Runs away quickly into the rain, away from camera.
- ID_GIRL: (Shoulder/umbrella visible).

**[SCENE DESCRIPTION]**
Wide shot. The boy sprints away on the paved path past a brick building and bushes.

**[NANO BANANA PRO PROMPT]**
```
A wide shot of a Korean male student with a black backpack running away desperately into the rain on a paved path. He is wearing a white shirt and black pants. To the side, a brick building and green bushes are visible. The ground is wet.

--ar 9:16
```

**[COLOR CONSISTENCY KEY]**: DAYTIME RAIN DRAMA KEY

---

### CUT #5 | 00:06 - 00:07

**[CHARACTERS IN THIS CUT]**
- ID_GIRL: Stares forward (at fleeing boy), expression is bewildered and speechless.

**[SCENE DESCRIPTION]**
Close-up front view of ID_GIRL under the umbrella. She blinks slowly.

**[NANO BANANA PRO PROMPT]**
```
A close-up of a Korean female student with long hair standing under a clear umbrella, looking bewildered and speechless. She wears a white shirt with a navy collar. Her eyes follow someone off-camera. The lighting is soft and diffused, creating a clean, dramatic look.

--ar 9:16
```

**[COLOR CONSISTENCY KEY]**: DAYTIME RAIN DRAMA KEY

---

## 🎯 ANCHOR 추천

| 후보 | 컷 | 캐릭터 | 이유 |
|------|-----|--------|------|
| **Primary** | #2 | ID_GIRL | 클로즈업, 얼굴 선명, 표정 뚜렷 |
| **Secondary** | #3 | ID_BOY | 얼굴 보이는 유일한 프론트 뷰 |

---

## 📋 도구 추천

| 씬 | 이미지 도구 | 영상 도구 | 이유 |
|----|-------------|----------|------|
| #1 | NanoBanana | Kling 2.6 | 2인 구도, 동작 씬 |
| #2 (ANCHOR) | **MJ V7** | Kling 2.6 | 클로즈업, 얼굴 일관성 |
| #3 (ANCHOR) | **MJ V7** | Kling 2.6 | 클로즈업, 얼굴 일관성 |
| #4 | NanoBanana | Kling 2.6 | 와이드샷, 동작 |
| #5 | NanoBanana | Kling 2.6 | 클로즈업, 동작 적음 |

---

## 📝 특이사항

1. **비 효과**: 모든 씬에 비 내리는 효과 필요
2. **투명 우산**: Clear/transparent umbrella 명시 필요
3. **교복**: 한국 고등학교 교복 스타일 (흰 셔츠 + 네이비)
4. **분위기**: K-드라마 로맨틱 코미디 톤
