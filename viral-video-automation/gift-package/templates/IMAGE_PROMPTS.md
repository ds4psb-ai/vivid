# Image Prompts

> **Project**: {PROJECT_NAME}
> **Tool**: NanoBanana / Midjourney V7
> **핵심 규칙**: ALL PEOPLE → Korean (배경 인물 포함!)

---

## 예시 먼저 보기

실제 완성된 프로젝트 예시를 참고하세요:
→ `examples/birthday-parody/prompts/IMAGE_PROMPTS.md`

---

## 🎯 핵심 철학: 최소 변경 오마주

```
원본 바이럴 영상의:
✅ 구도 (Composition) → 그대로 유지
✅ 색감 (Color Grade) → 그대로 유지
✅ 타이밍 (Beat) → 그대로 유지
✅ 감정 (Emotion) → 그대로 유지

변경하는 것:
🔄 인종 → 한국인 (ALL PEOPLE Rule)
🔄 시대 맥락 → 한국 맥락
```

---

## 📁 추출된 키프레임 테이블

> 아래 테이블을 ANALYSIS.md 결과로 채우세요

| Scene | 타임코드 | 길이 | 파일명 | 설명 |
|-------|----------|------|--------|------|
| 1 | 00:00.00~00:{XX}.{XX} | {DURATION}s | `scene01_{NAME}.png` | {DESCRIPTION} |
| **2 ⭐** | **00:{XX}.{XX}~00:{XX}.{XX}** | {DURATION}s | **`ANCHOR_IMG.png`** | 주인공 단독 정면 |
| 3 | 00:{XX}.{XX}~00:{XX}.{XX} | {DURATION}s | `scene03_{NAME}.png` | {DESCRIPTION} |
| ... | ... | ... | ... | ... |
| N | 00:{XX}.{XX}~00:{XX}.{XX} | {DURATION}s | `sceneN_{NAME}.png` | {DESCRIPTION} |

---

## 🎭 캐릭터 프로필

### ID_MAIN (주인공)
| 속성 | 값 |
|------|-----|
| **Ethnicity** | Korean |
| **Age** | {AGE} |
| **Gender** | {GENDER} |
| **Hair** | {HAIR_STYLE} |
| **Eyes** | single eyelids |
| **Skin** | Korean skin tone |
| **Clothing** | {CLOTHING} |

### ID_FAMILY / ID_OTHERS
| 역할 | 설명 |
|------|------|
| {ROLE_1} | Korean {DESCRIPTION} |
| {ROLE_2} | Korean {DESCRIPTION} |
| ... | ... |

---

# 🏗️ PHASE 1: ANCHOR FIRST

> **왜 먼저?** 주인공 얼굴 확정 → 나머지 씬에서 참조

## 📼 Scene 2 ⭐ ANCHOR ({DURATION}s)

> **파일**: `keyframes/ANCHOR_IMG.png`
> **결과물**: `generated/images/ANCHOR.png`

### NanoBanana (한글)
```
[ANCHOR_IMG.png 이미지 첨부]

이 이미지의 구도, 조명, 카메라 앵글 그대로 유지.

주인공 교체: {AGE}세 한국인 {GENDER}
- 헤어: {HAIR_STYLE} (시대별 스타일)
- 눈: 홑꺼풀
- 표정: {EXPRESSION}
- 피부: 한국인 피부톤

주의: 배경에 인물이 보이면 모두 한국인으로!

금지: 서양인 특징, 금발, 파란 눈
```

### Midjourney V7 (영어)
```
[ANCHOR_IMG.png URL]

Exact same composition, lighting, and camera angle.

**Main subject**: Replace with {AGE}-year-old Korean {GENDER}:
{HAIR_STYLE}, single eyelids, {EXPRESSION}. Korean skin tone.

**Note**: If any family visible in background blur, replace with Korean.

Keep {LIGHTING_STYLE}, {ERA} aesthetic, {FILM_GRAIN}.

--iw 2.0 --ar 9:16 --v 7 --style raw
--no western features, caucasian skin, blonde, blue eyes
```

> 💾 **결과물 저장** → `GENERATED_ANCHOR.png`

---

# 🏗️ PHASE 2: {ERA_PAST} (Scene 1, 3~{N})

> 과거 시대 씬들 - ANCHOR 참조 필수

## 📼 Scene 1: {SCENE_NAME} ({DURATION}s)

> **파일**: `keyframes/scene01_{NAME}.png`
> **ANCHOR 참조**: 필수

### NanoBanana (한글)
```
**Image 1 (구도용)**: [scene01_{NAME}.png]
**Image 2 (얼굴용)**: [GENERATED_ANCHOR.png]

Image 1에서 복사: 구도, 조명, 옷 색깔
Image 2에서 복사: 주인공 얼굴

모든 인물 교체 (ALL PEOPLE Rule):
- {POSITION_1}: 한국인 {ROLE_1}
- {POSITION_2}: 한국인 {ROLE_2}
- 배경 흐릿한 인물도 한국인!

조명: {LIGHTING_STYLE}, {COLOR_TEMP}K

금지: {ERA_NEGATIVES}
```

### Midjourney V7 (영어)
```
**[Image 1: COMPOSITION]** [scene01_{NAME}.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, character positions, clothing colors, lighting.
**From Image 2**: Copy the Korean {ROLE}'s face.

Replace **all people** with Korean:
- {POSITION_1}: Korean {ROLE_1} ({DETAIL})
- {POSITION_2}: Korean {ROLE_2} ({DETAIL})

Keep {ERA} aesthetic, {LIGHTING_STYLE} ({COLOR_TEMP}K).

--iw 2.0 --ar 9:16 --v 7 --style raw --cw 50
--no {ERA_NEGATIVES}
```

---

## 📼 Scene 3: {SCENE_NAME} ({DURATION}s)

> **파일**: `keyframes/scene03_{NAME}.png`
> **ANCHOR 참조**: 필수

### NanoBanana (한글)
```
**Image 1 (구도용)**: [scene03_{NAME}.png]
**Image 2 (얼굴용)**: [GENERATED_ANCHOR.png]

Image 1에서 복사: 구도, 캐릭터 위치
Image 2에서 복사: 주인공 얼굴

모든 인물 교체 (ALL PEOPLE Rule):
- {POSITION_1}: 한국인 {ROLE_1}
- {POSITION_2}: 한국인 {ROLE_2}

동작: {ACTION_DESCRIPTION}
조명: {LIGHTING_STYLE}

금지: {ERA_NEGATIVES}
```

### Midjourney V7 (영어)
```
**[Image 1: COMPOSITION]** [scene03_{NAME}.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

Exact {CAMERA_ANGLE} composition.
Replace **all people** with Korean:
- **{POSITION_1}**: Korean {ROLE_1} ({DETAIL}).
- **{POSITION_2}**: Korean {ROLE_2} ({DETAIL}).

Action: {ACTION_DESCRIPTION}
Lighting: {LIGHTING_STYLE}, {ATMOSPHERE}.

--iw 2.0 --ar 9:16 --v 7 --style raw --cw 50
--no {ERA_NEGATIVES}
```

---

## 📼 Scene {N}: {SCENE_NAME} ({DURATION}s)

> (위 템플릿 반복 - 과거 씬 수만큼)

---

# 🏗️ PHASE 3: THE GLITCH (Scene {GLITCH_N})

> 과거 → 현재 전환 구간 (모핑/컷)

## 🔄 Scene {GLITCH_N}: {GLITCH_NAME} ({DURATION}s)

> **파일**: `keyframes/scene{N}_glitch.png`
> **⚠️ 모핑 구간**: 단순 컷 전환 아님, 점진적 변화

### {GLITCH_N}A - 과거 (0~{HALF}초)
```
[scene{N}_glitch.png URL - early frame]

{PAST_DESCRIPTION}
{PAST_LIGHTING} lighting, {ERA_PAST} aesthetic, {FILM_GRAIN}.

--iw 2.0 --ar 9:16 --v 7
--no modern objects, cold light, LED
```

### {GLITCH_N}B - 현재 ({HALF}~{DURATION}초)
```
[scene{N}_glitch.png URL - late frame]

{PRESENT_DESCRIPTION}
{PRESENT_LIGHTING} lighting, sharp digital aesthetic, modern.

--iw 2.0 --ar 9:16 --v 7
--no {PAST_ELEMENTS}, warm light, film grain
```

---

# 🏗️ PHASE 4: THE PRESENT (Scene {PRESENT_START}~{PRESENT_END})

> 현재 시대 씬들 - 다른 캐릭터 (ANCHOR 불필요)

## 📱 Scene {PRESENT_START}: {SCENE_NAME} ({DURATION}s)

> **파일**: `keyframes/scene{N}_{NAME}.png`
> **ANCHOR 참조**: 불필요 (다른 캐릭터)

### Midjourney V7 (영어)
```
[scene{N}_{NAME}.png URL]

Exact composition.
Subject: {AGE_PRESENT}-year-old Korean {GENDER_PRESENT} {POSE_DESCRIPTION}.
{OTHER_PEOPLE_DESCRIPTION}
Atmosphere: {MODERN_ATMOSPHERE}.
Expression: {EXPRESSION_DESCRIPTION}.

--iw 2.0 --ar 9:16 --stylize 400 --v 7 --style raw
--no warm light, daylight, genuine happiness, western features
```

---

## 📱 Scene {PRESENT_END}: {SCENE_NAME} ({DURATION}s)

> **파일**: `keyframes/scene{N}_{NAME}.png`
> **롱테이크**: {DURATION}초

### Midjourney V7 (영어)
```
[scene{N}_{NAME}.png URL]

Exact {CAMERA_ANGLE} angle.

Replace **all people** with Korean:
- {POSITION_1}: Korean {ROLE_1} ({DETAIL})
- {POSITION_2}: Korean {ROLE_2} ({DETAIL})

Keep {VISUAL_EFFECTS}.

--iw 2.0 --ar 9:16 --stylize 400 --v 7 --style raw
--no {PRESENT_NEGATIVES}
```

---

# 🛡️ 에러 방지 룰

## 시대별 --no 요소

### 과거 시대 (1990년대 등)
```
--no western features, caucasian skin, blonde, blue eyes,
    smartphones, LED lights, modern furniture, sharp digital look,
    cold lighting, flat screens, wireless devices
```

### 현재 시대 (2020년대)
```
--no warm lighting, candles, tungsten, genuine happiness,
    film grain, retro furniture, CRT TV, wired phones,
    1990s interior, soft focus
```

## Multi-Image 주의사항

| 문제 | 해결책 |
|------|--------|
| 얼굴 불일치 | `--cw 50` (character weight) 추가 |
| 구도 변경됨 | `--iw 2.0` (image weight) 확인 |
| 배경 인물 서양인 | 프롬프트에 명시적으로 "all people Korean" |
| 시대 부조화 | --no에 반대 시대 요소 추가 |

## 파라미터 치트시트

| 파라미터 | 용도 | 권장값 |
|----------|------|--------|
| `--iw` | 이미지 가중치 | 2.0 (구도 유지) |
| `--cw` | 캐릭터 가중치 | 50 (얼굴 일관성) |
| `--ar` | 종횡비 | 9:16 (세로) |
| `--v` | 버전 | 7 (최신) |
| `--style raw` | 스타일 | 항상 사용 |
| `--stylize` | 스타일화 | 250 (기본) / 400 (현재 씬) |

---

# ✅ 10-Cut 체크리스트

| Phase | Scene | 타임코드 | 파일명 | ANCHOR 참조 | 상태 |
|-------|-------|----------|--------|-------------|------|
| 1 | **2 ⭐** | 00:{XX}.{XX} | ANCHOR_IMG | ❌ (먼저 생성) | ⬜ |
| 2 | 1 | 00:00.00 | scene01_{NAME} | ✅ | ⬜ |
| 2 | 3 | 00:{XX}.{XX} | scene03_{NAME} | ✅ | ⬜ |
| 2 | ... | ... | ... | ✅ | ⬜ |
| 3 | {GLITCH_N} | 00:{XX}.{XX} | scene{N}_glitch | ❌ | ⬜ |
| 4 | {PRESENT_START} | 00:{XX}.{XX} | scene{N}_{NAME} | ❌ | ⬜ |
| 4 | {PRESENT_END} | 00:{XX}.{XX} | scene{N}_{NAME} | ❌ | ⬜ |

## 완료 전 검증

- [ ] **ANCHOR 먼저**: Scene 2 생성 완료 확인
- [ ] **얼굴 일관성**: 모든 과거 씬에서 ANCHOR.png 참조
- [ ] **ALL PEOPLE Rule**: 배경 인물 포함 모두 한국인
- [ ] **시대 일관성**: --no에 반대 시대 요소 포함
- [ ] **Phase 순서**: ANCHOR → 과거 → 전환 → 현재
- [ ] **Multi-Image 라벨링**: Image 1/2 명확히 구분

---

## 변수 참조

| 변수 | 설명 | 예시 |
|------|------|------|
| `{PROJECT_NAME}` | 프로젝트명 | Birthday Glitch |
| `{AGE}` | 주인공 나이 | 7 |
| `{GENDER}` | 주인공 성별 | boy/girl/man/woman |
| `{HAIR_STYLE}` | 헤어스타일 | black bowl cut (1990s Korean style) |
| `{EXPRESSION}` | 표정 | shy gentle smile (lips closed) |
| `{LIGHTING_STYLE}` | 조명 스타일 | warm tungsten / cold LED |
| `{COLOR_TEMP}` | 색온도 | 3200 (따뜻) / 5600 (차가움) |
| `{ERA}` | 시대 | 1990s / 2020s |
| `{ERA_NEGATIVES}` | 시대별 금지 요소 | 위 "시대별 --no 요소" 참조 |
| `{FILM_GRAIN}` | 필름 그레인 | Kodak Portra grain / none |
