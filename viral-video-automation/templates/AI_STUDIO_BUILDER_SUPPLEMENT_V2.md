# 🔧 AI STUDIO BUILDER 보강 문서 (Phase 2)

> **목적**: 현재 4단계 출력을 IMAGE_PROMPTS.md 수준으로 끌어올리기
> **대상**: Gemini 3 Pro AI Builder
> **Version**: 2.0 - 5단계 확장

---

# 🎯 범용 적용 원칙

## 적용 범위

이 문서는 **모든 영상**에 적용되는 범용 가이드입니다.

- ✅ 생일 파티 영상
- ✅ 뮤직비디오
- ✅ 광고 영상
- ✅ 드라마/영화 클립
- ✅ 틱톡/릴스/숏폼
- ✅ 모든 장르의 영상

## 예시 표기 규칙

이 문서에서 **구체적인 예시**는 아래와 같이 표기됩니다:

```
📌 예시 (Birthday Paradox 영상 기준):
[구체적인 예시 내용]
```

**예시는 참고용**이며, 실제 분석 시에는:
- 업로드된 영상의 **실제 컷 수**에 맞게 조정
- 업로드된 영상의 **실제 인물**에 맞게 조정
- 업로드된 영상의 **실제 분위기**에 맞게 조정

## 핵심 범용 규칙

모든 영상에 공통 적용되는 규칙:

| 규칙 | 설명 |
|------|------|
| **컷 분리** | 화면 전환마다 무조건 분리 (0.4초도) |
| **ANCHOR** | 얼굴이 가장 선명한 1개 컷 먼저 생성 |
| **듀얼 레퍼런스** | [Image 1: COMPOSITION] + [Image 2: FACE] |
| **Korean 강제** | 모든 인물을 Korean으로 (brown/blonde ❌) |
| **5회 루프** | 4단계 대화 + 5단계 최종 마크다운 |
| **씬별 --no** | 각 씬의 상황에 맞는 맞춤 네거티브 |

---

# 🚨 현재 출력 vs 목표 출력 Gap 분석

## 현재 부족한 점

| 항목 | 현재 출력 | 목표 (IMAGE_PROMPTS.md) |
|------|----------|------------------------|
| **듀얼 레퍼런스** | ❌ 없음 | `[Image 1: COMPOSITION]` `[Image 2: CHARACTER FACE]` |
| **ANCHOR 재사용** | 언급만 | `[GENERATED_ANCHOR.png URL]` 명시적 참조 |
| **⚠️ 주의사항** | ❌ 없음 | 각 씬별 구체적 특이사항 |
| **--cw 파라미터** | ❌ 없음 | `--cw 50` (캐릭터 가중치) |
| **씬별 --no** | 공통만 | 씬별 맞춤 (`cake on table`, `eyes closed`) |
| **의상 색상** | "striped t-shirt" | "white t-shirt with thin multi-colored horizontal stripes" |
| **타임코드** | "00:01.27 - 00:02.25" | "00:01.27~00:02.28" |
| **Phase 헤더** | ❌ 없음 | `# 🏗️ PHASE 1: ANCHOR FIRST` |
| **파일명 참조** | ❌ 없음 | `keyframes/scene01_arrival.png` |
| **체크리스트** | ❌ 없음 | ✅ 완전한 테이블 |
| **마크다운 형식** | JSON | 완전한 마크다운 |

---

# 📋 5단계 확장 워크플로우

## 기존 4단계 + 신규 5단계

| Step | 기존 | 신규 보강 |
|------|------|----------|
| 1 | 컷 분석 | + 파일명 제안 |
| 2 | 캐릭터 | + 의상 색상 정밀화 |
| 3 | Phase 1-2 | + 듀얼 레퍼런스 라벨 |
| 4 | Phase 3-4 | + 체크리스트 |
| **5 (신규)** | - | **최종 마크다운 문서 출력** |

---

# 🔄 각 단계 보강 규칙

## STEP 1 보강: 파일명 제안 추가

**현재 출력 (부족함)**:
```json
{
  "scene_id": 1,
  "timecode": "00:00.00 - 00:01.27",
  "description": "[설명]"
}
```

**보강된 출력 (목표)**:
```json
{
  "scene_id": "[N]",
  "timecode": "[00:00.00~00:XX.XX]",
  "duration": "[X.XXs]",
  "keyframe_file": "scene[N]_[action].png",
  "description": "[이 컷에서 일어나는 일]",
  "special_note": "[이 씬의 ⚠️ 주의사항 - 타이밍, 상태, 특이점]"
}
```

**추가 필드**:
- `keyframe_file`: 파일명 제안 형식 `scene[N]_[action].png`
- `special_note`: 이 씬만의 특이사항

📌 **예시 (Birthday Paradox 영상 기준)**:
```json
{
  "scene_id": 1,
  "timecode": "00:00.00~00:01.27",
  "duration": "1.27s",
  "keyframe_file": "scene01_arrival.png",
  "description": "엄마가 케이크를 들고 옴",
  "special_note": "케이크가 아직 테이블에 없음 - 엄마가 가져오는 중"
}
```

### 범용 special_note 유형

어떤 영상이든 아래 유형 중 해당하는 것을 작성:

| 유형 | 설명 | 예시 |
|------|------|------|
| **타이밍** | 컷 전환 직전/직후 상태 | "액션이 완료되기 직전에 컷 전환" |
| **짧은 컷** | 0.5초 미만 컷 | "0.4초 찰나, 순간적 표정" |
| **전환** | 모핑/디졸브 | "단순 컷 아님, 점진적 변화" |
| **인물 상태** | 표정/동작 | "눈 감은 상태", "박수 치는 중" |
| **오브젝트** | 있음/없음 | "아직 등장 안 함", "손에 들고 있음" |

---

## STEP 2 보강: 의상 색상 정밀화

### 범용 캐릭터 프로필 구조

**현재 출력 (부족함)**:
```json
{
  "id": "ID_[ROLE]",
  "korean_mapping": "[일반적 설명]"
}
```

**보강된 출력 (목표)**:
```json
{
  "id": "ID_[ROLE]",
  "role": "[역할명]",
  "age": "[나이대]",
  "hair": {
    "original": "[원본 머리색/스타일]",
    "korean": "[Korean화 - 반드시 black]"
  },
  "clothing": {
    "description": "[정확한 의상 설명 - 색상 포함]",
    "primary_color": "[주 색상]",
    "accent_colors": ["[보조 색상1]", "[보조 색상2]"]
  },
  "facial_features": "[Korean 특성 - single eyelids, Korean skin tone]",
  "scenes_appeared": [씬 번호 리스트]
}
```

### 의상 색상 정밀화 규칙 (범용)

| ❌ 피해야 할 표현 | ✅ 정확한 표현 |
|-----------------|--------------|
| "striped shirt" | "white t-shirt with thin multi-colored horizontal stripes (blue, yellow, red)" |
| "red clothes" | "burgundy/maroon long-sleeve sweater" |
| "green shirt" | "forest green button-up shirt" |
| "colorful dress" | "pink and yellow plaid sleeveless dress" |
| "dark outfit" | "navy blue dress shirt" |

📌 **예시 (Birthday Paradox 영상 기준)**:
```json
{
  "id": "ID_BOY",
  "role": "생일 아이",
  "age": "7세",
  "hair": {
    "original": "Long brown hair",
    "korean": "black bowl cut (1990s Korean style)"
  },
  "clothing": {
    "description": "white t-shirt with thin multi-colored horizontal stripes (blue, yellow, red)",
    "primary_color": "white",
    "accent_colors": ["blue", "yellow", "red"]
  },
  "facial_features": "single eyelids, Korean skin tone, shy gentle smile",
  "scenes_appeared": [1, 2, 3, 4, 5, 6, 7]
}
```

---

## STEP 3 보강: 듀얼 레퍼런스 라벨 필수

### 범용 프롬프트 구조

**현재 출력 (부족함)**:
```json
{
  "prompt": "[일반적인 프롬프트]"
}
```

**보강된 출력 (목표 - 마크다운 형식)**:
```markdown
## 📼 Scene [N]: [Title] ([타임코드])

> **파일**: keyframes/[filename].png
> **⚠️ 주의**: [이 씬만의 특이사항]

**[Image 1: COMPOSITION]** [[filename].png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, character positions, clothing colors, lighting.
**From Image 2**: Copy the **Korean** [역할]'s face.

Replace **all people** with **Korean** [관계]:
- **[위치]**: **Korean** [역할] (use face from Image 2) - [의상 색상 정확히]
- **[위치]**: **Korean** [역할] ([의상 색상 정확히])
- **Background**: **Korean** [역할들] ([상태])

[분위기/조명/환경 설명]

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no [공통] + [씬별 맞춤]
```

### 필수 10가지 요소 (모든 씬에 적용)

| # | 요소 | 설명 |
|---|------|------|
| 1 | `## 📼 Scene N:` | 씬 헤더 |
| 2 | `> **파일**:` | 키프레임 파일 참조 |
| 3 | `> **⚠️ 주의**:` | 씬별 특이사항 |
| 4 | `**[Image 1: COMPOSITION]**` | 구도 레퍼런스 라벨 |
| 5 | `**[Image 2: CHARACTER FACE]**` | 얼굴 레퍼런스 라벨 |
| 6 | `**From Image 1/2**:` | 각 이미지에서 가져올 것 |
| 7 | `Replace **all people** with **Korean**` | Korean 강제 구문 |
| 8 | 역할별 의상 색상 | 정확한 색상 명시 |
| 9 | `--cw 50` | 캐릭터 가중치 파라미터 |
| 10 | 씬별 `--no` | 맞춤 네거티브 |

📌 **예시 (Birthday Paradox 영상 Scene 1 기준)**:
```markdown
## 📼 Scene 1: The Arrival (00:00.00~00:01.27)

> **파일**: keyframes/scene01_arrival.png
> **⚠️ 주의**: 엄마가 케이크를 완전히 내려놓기 **직전**에 컷 전환됨

**[Image 1: COMPOSITION]** [scene01_arrival.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, character positions, clothing colors, lighting.
**From Image 2**: Copy the **Korean** boy's face.

Replace **all people** with **Korean** family:
- **Center**: **Korean** boy (use face from Image 2) - white t-shirt with multi-colored stripes
- **Standing**: **Korean** mom (burgundy sweater) - carrying lit cake, approaching table
- **Background**: **Korean** dad (green button-up), **Korean** uncle (striped polo)

Keep 1990s Korean apartment, warm tungsten lighting (3200K), floral wallpaper.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, blonde hair, brown hair, blue eyes, cake on table
```

---

## STEP 4 보강: 체크리스트 테이블 필수

**추가할 내용**:
```markdown
## ✅ 10-Cut 체크리스트

| Phase | Scene | 타임코드 | 파일명 | ANCHOR 재사용 | 상태 |
|-------|-------|----------|--------|--------------|------|
| 1 | **2 ⭐** | 00:01.27 | ANCHOR_IMG.png | ❌ | ⬜ 먼저! |
| 2 | 1 | 00:00.00 | scene01_arrival.png | ✅ | ⬜ |
| 2 | 3 | 00:02.28 | scene03_sideview.png | ✅ | ⬜ |
| 2 | 4 | 00:04.05 | scene04_clapping_a.png | ✅ | ⬜ |
| 2 | 5 | 00:06.00 | scene05_clapping_b.png | ✅ | ⬜ |
| 2 | 6 | 00:08.10 | scene06_pre_blow.png | ✅ | ⬜ |
| 2 | 7 | 00:08.50 | scene07_blowout.png | ✅ | ⬜ |
| 3 | 8 | 00:09.28 | scene08_glitch.png | ❌ | ⬜ |
| 4 | 9 | 00:11.12 | scene09_isolation.png | ❌ | ⬜ |
| 4 | 10 | 00:13.25 | scene10_selfie.png | ❌ | ⬜ |
```

---

# 🆕 STEP 5: 최종 마크다운 문서 출력 (신규)

## 요구사항

STEP 4까지 완료 후, 사용자가 "OK" 또는 "최종 문서로" 라고 하면:

**JSON이 아닌 완전한 마크다운 형식**으로 최종 문서 출력.

---

## STEP 5 출력 템플릿

```markdown
# 🎬 VIDEO PARODY: [N]-CUT BALANCED PROMPT v3.0

> **Core Philosophy**: 레퍼런스 이미지 구도 100% 유지 + **모든 인물** Korean 변경
> **Critical Rule**: 프레임에 등장하는 **모든 사람**의 인종을 명시해야 함 (흐릿해도!)
> **Total Duration**: [X]초 ([N]씬)

---

## ⚙️ 필수 설정

```
Midjourney /settings
├── Model: V6.0 (또는 V7)
├── Style: Raw
└── Stylize: 250
```

---

## 📁 추출된 키프레임 ([N]-Cut 정밀)

| Scene | 실제 타임코드 | 길이 | 파일명 | 설명 |
|-------|-------------|------|--------|------|
| 1 | 00:00.00~00:01.27 | 1.27s | `scene01_arrival.png` | 엄마 케이크 등장 |
| **2 ⭐** | **00:01.27~00:02.28** | 1.01s | **`ANCHOR_IMG.png`** | 아이 단독 정면 |
| 3 | 00:02.28~00:04.05 | 1.37s | `scene03_sideview.png` | 측면 가족 반응 |
| ... | ... | ... | ... | ... |

---

# 🏗️ PHASE 1: ANCHOR FIRST

## 📼 Scene 2 ⭐ ANCHOR (00:01.27~00:02.28)

> **파일**: `keyframes/ANCHOR_IMG.png`
> **목표**: 한국 아이 얼굴 확정 → 모든 과거 씬에 재사용

```
[ANCHOR_IMG.png URL]

Exact same composition, lighting, and camera angle.

**Main subject**: Replace the child with a 7-year-old Korean boy: black bowl cut (1990s Korean style), single eyelids, shy gentle smile (lips closed), looking at cake. Korean skin tone.

**Note**: This is a close-up solo shot of the boy. If any family visible in background blur, replace with Korean parents.

Keep warm candlelight under-lighting, 1990s home video aesthetic, Kodak Portra grain.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --no western features, caucasian skin, blonde, blue eyes
```

> 💾 **결과물 저장** → `GENERATED_ANCHOR.png`

---

# 🏗️ PHASE 2: THE 90s (Scene 1, 3~7)

## 📼 Scene 1: The Arrival (00:00.00~00:01.27)

> **파일**: `keyframes/scene01_arrival.png`
> **⚠️ 주의**: 엄마가 케이크를 완전히 내려놓기 **직전**에 컷 전환됨

```
**[Image 1: COMPOSITION]** [scene01_arrival.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, character positions, clothing colors, lighting.
**From Image 2**: Copy the Korean boy's face.

Replace **all people** with Korean family:
- Center: Korean boy (use face from Image 2) seated at table
- Standing: Korean mom carrying lit cake (approaching table)
- Background: Korean dad and relatives watching

Keep 1990s Korean apartment, warm tungsten lighting (3200K).

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, cake on table
```

---

## 📼 Scene 3: Side View (00:02.28~00:04.05)

> **파일**: `keyframes/scene03_sideview.png`
> **카메라**: 측면 앵글
> **⚠️ 주의**: 좌측은 누나(sister), 후방에 부모

```
**[Image 1: COMPOSITION]** [scene03_sideview.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

Exact side angle composition.
Replace **all people** with Korean family:
- **Left (Leaning on table)**: Korean sister in striped sleeveless top, smiling at brother.
- **Center**: Korean boy (use face from Image 2) sitting.
- **Background (Standing)**: Korean dad (green shirt) and mom (red sweater).

Action: Parents and sister leaning in towards the boy with affection.
Lighting: Warm 90s tungsten, cozy atmosphere.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin
```

---

(... 모든 씬 반복 ...)

---

# 🏗️ PHASE 3: THE GLITCH (Scene 8)

## 🔄 Scene 8: The Glitch Transition (00:09.28~00:11.12)

> **파일**: `keyframes/scene08_glitch.png`
> **⚠️ 모핑 구간**: 단순 컷 전환 아님, 점진적 변화

**8A - 과거 케이크 (0~0.9초)**
```
[scene08_glitch.png URL - early frame]

Overhead view of homemade chocolate cake with lit colorful candles.
Warm tungsten lighting, 1990s film grain, smoke wisps rising.

--iw 2.0 --ar 9:16 --v 6.0 --no modern objects, cold light
```

**8B - 현재 케이크 (0.9~1.84초)**
```
[scene08_glitch.png URL - late frame]

Overhead view of store-bought white cream cake with unlit thin candles.
Cold LED lighting, sharp digital aesthetic, sterile modern table.

--iw 2.0 --ar 9:16 --v 6.0 --no chocolate, warm light, film grain
```

---

# 🏗️ PHASE 4: THE PRESENT (Scene 9~10)

## 📱 Scene 9: Digital Isolation (00:11.12~00:13.25)

> **파일**: `keyframes/scene09_isolation.png`
> **⚠️ 수정**: 남자 어깨 미세 호흡 동작 추가

```
[scene09_isolation.png URL]

Exact composition.
Subject: 28-year-old Korean man sitting at a dark table with a white cake.
Crowd: Korean friends standing behind, faces lit ONLY by harsh blue/white smartphone flashes.
Atmosphere: Pitch black background, high contrast, cyberpunk dystopian mood.
Expression: Man has a hollow, forced smile. Friends are expressionless.

--iw 2.0 --ar 9:16 --stylize 400 --v 6.0 --style raw --no warm light, daylight, genuine happiness, western features
```

---

## 📱 Scene 10: The Selfie (00:13.25~00:17.29)

> **파일**: `keyframes/scene10_selfie.png`
> **4초 롱테이크**
> **⚠️ 수정**: 여자 고개 왼쪽 걸웃거림 추가

```
[scene10_selfie.png URL]

Exact selfie angle.

Replace **all people** with Korean:
- Foreground: Korean woman taking selfie (K-beauty makeup, head tilting slightly to the LEFT)
- Background: Korean birthday man (forced awkward smile, robotic blink)

Keep wide-angle distortion, harsh flash, red-eye effect.

--iw 2.0 --ar 9:16 --stylize 400 --v 6.0 --style raw --no western features, caucasian skin, genuine smile
```

---

## ✅ [N]-Cut 체크리스트

| Phase | Scene | 타임코드 | 파일명 | ANCHOR | 상태 |
|-------|-------|----------|--------|--------|------|
| 1 | **2 ⭐** | 00:01.27 | ANCHOR_IMG | ❌ | ⬜ 먼저! |
| 2 | 1 | 00:00.00 | scene01_arrival | ✅ | ⬜ |
| 2 | 3 | 00:02.28 | scene03_sideview | ✅ | ⬜ |
| 2 | 4 | 00:04.05 | scene04_clapping_a | ✅ | ⬜ |
| 2 | 5 | 00:06.00 | scene05_clapping_b | ✅ | ⬜ |
| 2 | 6 | 00:08.10 | scene06_pre_blow | ✅ | ⬜ |
| 2 | 7 | 00:08.50 | scene07_blowout | ✅ | ⬜ |
| 3 | 8 | 00:09.28 | scene08_glitch | ❌ | ⬜ |
| 4 | 9 | 00:11.12 | scene09_isolation | ❌ | ⬜ |
| 4 | 10 | 00:13.25 | scene10_selfie | ❌ | ⬜ |
```

---

# 📊 씬별 맞춤 --no 파라미터 가이드

## 필수 공통 (모든 씬, 모든 영상)

```
--no western features, caucasian skin, blonde hair, brown hair, blue eyes
```

## 범용 씬별 --no 패턴

어떤 영상이든 상황에 따라 적용:

| 상황 | 추가 --no |
|------|----------|
| **오브젝트 아직 없음** | `[오브젝트] on [위치]` (예: `cake on table`) |
| **오브젝트 이미 등장** | `duplicate [오브젝트]` |
| **눈 뜬 상태** | `eyes closed` |
| **눈 감은 상태** | `eyes open, staring` |
| **입 다문 상태** | `mouth open, speaking` |
| **말하는 중** | `lips closed, silent` |
| **과거/레트로 씬** | `modern objects, LED lights, smartphones` |
| **현재/모던 씬** | `vintage, film grain, tungsten light` |
| **따뜻한 분위기** | `cold light, blue tint, sterile` |
| **차가운 분위기** | `warm light, amber, cozy` |
| **진심 표정** | `forced smile, awkward expression` |
| **억지 표정** | `genuine smile, natural joy` |

📌 **예시 (Birthday Paradox 영상 기준)**:

| Scene | 상황 | 추가 --no |
|-------|------|----------|
| 1 | 케이크 아직 테이블에 없음 | `cake on table, duplicate cake` |
| 6 | 아직 안 불음, 눈 뜬 상태 | `eyes closed, blowing` |
| 7 | 볼이 부푼 상태 | `calm face, static pose` |
| 8A | 과거 케이크 | `modern objects, cold light, minimalism` |
| 8B | 현재 케이크 | `chocolate, warm light, film grain` |
| 9 | 차가운 분위기 | `warm light, daylight, genuine happiness` |
| 10 | 억지 웃음 | `genuine smile, natural light, soft box` |

---

# 🔍 ⚠️ 주의사항 작성 가이드 (범용)

**각 씬에 반드시 포함해야 할 특이사항 유형**:

| 유형 | 설명 | 범용 예시 |
|------|------|----------|
| **컷 타이밍** | 컷 전환 직전/직후 상태 | "액션이 완료되기 직전에 컷 전환" |
| **짧은 컷** | 0.5초 미만 컷 | "0.4초 찰나, 순간적 표정" |
| **전환** | 모핑/디졸브/페이드 | "단순 컷 아님, 점진적 변화" |
| **인물 배치** | 화면 내 위치 | "좌측이 [역할], 우측이 [역할]" |
| **표정 상태** | 감정/표정 | "웃는 중", "놀란 상태" |
| **동작 상태** | 진행 중인 액션 | "손 들어올리는 중", "걸어가는 중" |
| **카메라 앵글** | 특수 앵글 | "탑다운", "셀카 앵글", "네덜란드 앵글" |
| **조명 특이점** | 특수 조명 | "촛불만으로 조명", "스마트폰 플래시" |

---

# ⚡ STEP 5 트리거 조건

사용자가 다음 중 하나를 말하면 STEP 5 실행:
- "OK"
- "계속"
- "최종 문서로"
- "마크다운으로"
- "완료"

**STEP 5 출력 특징**:
1. **JSON 아님** → 완전한 **마크다운**
2. **코드 블록** 안에 프롬프트
3. **Phase 헤더** 포함 (`# 🏗️ PHASE 1: ANCHOR FIRST`)
4. **듀얼 레퍼런스 라벨** 필수
5. **체크리스트 테이블** 포함
6. **복사-붙여넣기 최적화** (Midjourney에 바로 사용 가능)

---

# ❌ 실패 조건 (STEP 5 거부)

다음 중 하나라도 누락되면 STEP 5 출력 불가:

1. `**[Image 1: COMPOSITION]**` 라벨 없음
2. `**[Image 2: CHARACTER FACE]**` 라벨 없음
3. `--cw 50` 파라미터 없음
4. 씬별 맞춤 `--no` 없음
5. `⚠️ 주의` 없음
6. Phase 헤더 없음
7. 체크리스트 테이블 없음
8. 파일명 참조 없음
9. 타임코드가 밀리초가 아님

---

# 📋 최종 품질 체크리스트

STEP 5 출력 전 자가 점검:

- [ ] 모든 씬에 `**[Image 1: COMPOSITION]**` 있음
- [ ] 모든 씬에 `**[Image 2: CHARACTER FACE]**` 있음 (ANCHOR 제외)
- [ ] 모든 프롬프트에 `--iw 2.0 --ar 9:16 --v 6.0 --style raw` 있음
- [ ] 듀얼 레퍼런스 씬에 `--cw 50` 있음
- [ ] 모든 씬에 `--no western features, caucasian skin, blonde, brown hair, blue eyes` 있음
- [ ] 씬별 맞춤 `--no` 추가됨
- [ ] 모든 씬에 `⚠️ 주의` 있음
- [ ] Phase 헤더 4개 있음 (1, 2, 3, 4)
- [ ] 체크리스트 테이블 있음
- [ ] 타임코드가 밀리초 형식 (00:01.27)
- [ ] 의상 색상이 정확함 (striped ❌ → multi-colored stripes ✅)
