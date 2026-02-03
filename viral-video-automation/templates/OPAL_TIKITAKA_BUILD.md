"영상 복제를 위한 AI 이미지 프롬프트 생성기"를 만들어줘.

이 앱은 영상을 분석하여 Midjourney V6/V7에서 바로 사용할 수 있는 전문가급 프롬프트를 생성한다.
내부적으로 3단계 파이프라인을 실행하고, 5회 이상 자기비평 루프를 거쳐 98점 이상 달성 시에만 출력한다.

---

# 🚨 CRITICAL SYSTEM RULES (위반 시 즉시 재시작)

## Rule 1: 컷 전환 = 반드시 분리
영상에서 **화면 전환이 발생하면 무조건 별도 씬으로 분리**해야 함.
- 0.4초짜리 컷도 분리 (0.5초 미만도 포함)
- "비슷해 보여서" 합치기 금지
- 컷 전환 없이 계속되면 하나의 씬

## Rule 2: 모든 인물 Korean 강제
**원본 영상의 인종과 관계없이** 모든 인물을 Korean으로 변경.
- "brown hair" ❌ → "black hair" ✅
- "blonde" ❌ → "black straight hair" ✅
- **흐릿한 배경 인물도** "Korean skin tone" 명시
- "the boy" ❌ → "Korean boy" ✅

## Rule 3: 원샷 출력 금지 (5회 루프 강제)
**첫 번째 결과물을 최종으로 내보내면 안 됨.**
반드시 5회 이상 자기비평 루프 실행.

---

# 입력

1. **영상 파일** (mp4, mov, webm)
2. **출력 모드 선택**:
   - **MINIMAL**: 간결한 듀얼 레퍼런스 프롬프트 (복사-붙여넣기 최적화)
   - **EXPERT**: Visual Forensic 포함 상세 분석 (학습/문서화용)
   - **BOTH**: 둘 다 출력

---

# 내부 파이프라인 (3단계)

## 🔵 STAGE 1: VIDEO FORENSIC ANALYSIS (JSON 출력)

영상을 프레임 단위로 분석하여 아래 JSON 구조 생성:

```json
{
  "video_title": "[가제]",
  "total_duration": "00:17.29",
  "anchor_scene_id": 2,
  "anchor_reason": "얼굴 가장 선명, 단독 클로즈업",
  "target_ethnicity": "Korean",
  
  "scenes": [
    {
      "id": 1,
      "timestamp_start": "00:00.00",
      "timestamp_end": "00:01.27",
      "duration_sec": 1.27,
      "name": "The Arrival",
      "keyframe_file": "scene01_arrival.png",
      
      "visual_forensic": {
        "shot_type": "Wide Shot (WS)",
        "camera_angle": "Slight High Angle",
        "camera_height": "Above adult eye level",
        "composition": "Reverse Triangle (역삼각형)",
        "focus": "Deep focus, entire family sharp"
      },
      
      "spatial_map": {
        "description": "역삼각형 구도: 아이가 하단 중앙, 부모가 상단 양쪽",
        "ascii": "┌─────┬─────┬─────┐\n│ DAD │     │ MOM │\n├─────┼─────┼─────┤\n│     │ BOY │     │\n└─────┴─────┴─────┘"
      },
      
      "depth_layers": {
        "foreground": "Wooden table surface (bottom 30%)",
        "midground": "Boy seated, parents standing",
        "background": "Floral wallpaper, balloons, kitchen"
      },
      
      "all_people": [
        {
          "id": "ID_BOY",
          "position": "center-bottom",
          "role": "생일 아이",
          "age": "7세",
          "hair": "black bowl cut (1990s Korean style)",
          "clothing_color": "white with thin multi-colored horizontal stripes",
          "visibility": "clear"
        },
        {
          "id": "ID_MOM",
          "position": "right-standing",
          "role": "엄마",
          "age": "30대",
          "hair": "black permed shoulder-length",
          "clothing_color": "red/maroon sweater",
          "visibility": "clear"
        },
        {
          "id": "ID_DAD",
          "position": "left-standing",
          "role": "아빠",
          "age": "30대",
          "hair": "short black",
          "clothing_color": "green button-up shirt",
          "visibility": "clear"
        },
        {
          "id": "ID_UNCLE",
          "position": "left-back",
          "role": "삼촌",
          "hair": "short black with mustache",
          "clothing_color": "vertical striped polo",
          "visibility": "partially blurred"
        }
      ],
      
      "lighting": {
        "type": "Indoor ambient + candlelight",
        "color_temp_k": 3200,
        "direction": "front diffuse",
        "quality": "Warm, soft shadows, nostalgic"
      },
      
      "mood": "nostalgic",
      "era": "1990s",
      
      "special_notes": [
        "케이크가 아직 테이블에 없음 - 엄마가 가져오는 중",
        "엄마가 케이크를 완전히 내려놓기 **직전**에 다음 컷으로 전환"
      ],
      
      "scene_specific_no": ["cake on table", "duplicate cake"]
    }
  ],
  
  "visual_rhymes": [
    {
      "source_scene_id": 3,
      "target_scene_id": 9,
      "same_composition": true,
      "contrast": "박수 치는 손 → 스마트폰 든 손",
      "lighting_flip": "warm 3200K → cold 6500K",
      "emotion_flip": "genuine joy → hollow smile"
    }
  ],
  
  "korean_adaptation": {
    "child": {
      "hair": "black bowl cut (1990s Korean style)",
      "eyes": "single eyelids",
      "skin": "Korean skin tone",
      "expression": "shy gentle smile"
    },
    "adults": {
      "style": "Korean family look, 1990s fashion",
      "skin": "Korean skin tones"
    },
    "environment": "1990s Korean apartment (floral wallpaper, cherry wood molding)"
  },
  
  "error_prevention": {
    "global_no_list": [
      "western features",
      "caucasian skin",
      "blonde hair",
      "brown hair",
      "blue eyes",
      "modern furniture",
      "LED lights",
      "sharp digital look"
    ],
    "scene_specific_no": {
      "1": ["cake on table"],
      "6": ["eyes closed", "blowing"],
      "7": ["calm face"],
      "9": ["warm light", "genuine happiness"],
      "10": ["genuine smile"]
    }
  },
  
  "phases": {
    "phase1_anchor": [2],
    "phase2_past": [1, 3, 4, 5, 6, 7],
    "phase3_transition": [8],
    "phase4_present": [9, 10]
  }
}
```

---

## 🟢 STAGE 2: PROMPT GENERATION (JSON → 프롬프트)

### 도구 분기 규칙

| 조건 | 도구 |
|------|------|
| ANCHOR (얼굴 고정) | MJ V7 --iw 2.0 |
| 3명+ 인물 | NanoBanana Pro |
| 듀얼 레퍼런스 | MJ V6/V7 --cw 50 |
| 클로즈업 | MJ V7 |

### Multi-Reference 라벨링 규칙

ANCHOR 이후 모든 씬에 반드시:

```
**[Image 1: COMPOSITION]** [scene_URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, character positions, clothing colors, lighting.
**From Image 2**: Copy the Korean [역할]'s face.
```

### --no 파라미터 자동 생성

```
--no [global_no_list] + [scene_specific_no[scene_id]]
```

예시:
```
--no western features, caucasian skin, blonde hair, brown hair, blue eyes, cake on table
```

---

## 🟡 STAGE 3: OUTPUT FORMATTING

### MINIMAL 모드 출력 형식

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

## 📁 추출된 키프레임

| Scene | 실제 타임코드 | 길이 | 파일명 | 설명 |
|-------|-------------|------|--------|------|
| 1 | 00:00.00~00:01.27 | 1.27s | scene01_arrival.png | 엄마 케이크 등장 |
| **2 ⭐** | **00:01.27~00:02.28** | 1.01s | **ANCHOR_IMG.png** | 아이 단독 정면 |
...

---

# 🏗️ PHASE 1: ANCHOR FIRST

## 📼 Scene 2 ⭐ ANCHOR (00:01.27~00:02.28)

> **파일**: keyframes/ANCHOR_IMG.png
> **목표**: 한국 아이 얼굴 확정 → 모든 과거 씬에 재사용

[ANCHOR_IMG.png URL]

Exact same composition, lighting, and camera angle.

**Main subject**: Replace the child with a 7-year-old **Korean** boy: **black bowl cut (1990s Korean style)**, **single eyelids**, shy gentle smile (lips closed), looking at cake. **Korean skin tone**.

**Note**: If any family visible in background blur, replace with **Korean** parents.

Keep warm candlelight under-lighting, 1990s home video aesthetic, Kodak Portra grain.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --no western features, caucasian skin, blonde, blue eyes, brown hair

> 💾 **결과물 저장** → GENERATED_ANCHOR.png

---

# 🏗️ PHASE 2: THE 90s (Scene 1, 3~7)

## 📼 Scene 1: The Arrival (00:00.00~00:01.27)

> **파일**: keyframes/scene01_arrival.png
> **⚠️ 주의**: 엄마가 케이크를 완전히 내려놓기 **직전**에 컷 전환됨

**[Image 1: COMPOSITION]** [scene01_arrival.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, character positions, clothing colors, lighting.
**From Image 2**: Copy the **Korean** boy's face.

Replace **all people** with **Korean** family:
- **Center**: **Korean** boy (use face from Image 2) seated at table
- **Standing**: **Korean** mom (빨간색 스웨터) carrying lit cake (approaching table)
- **Background**: **Korean** dad (초록색 셔츠) and **Korean** relatives watching

Keep 1990s Korean apartment, warm tungsten lighting (3200K).

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, blonde, brown hair, blue eyes, cake on table

---

## 📼 Scene 3: Side View (00:02.28~00:04.05)

> **파일**: keyframes/scene03_sideview.png
> **카메라**: 측면 앵글
> **⚠️ 주의**: 좌측은 누나(sister), 후방에 부모

**[Image 1: COMPOSITION]** [scene03_sideview.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

Exact side angle composition.
Replace **all people** with **Korean** family:
- **Left (Leaning on table)**: **Korean** sister in striped sleeveless top, smiling at brother.
- **Center**: **Korean** boy (use face from Image 2) sitting.
- **Background (Standing)**: **Korean** dad (green shirt) and **Korean** mom (red sweater).

Action: Parents and sister leaning in towards the boy with affection.
Lighting: Warm 90s tungsten, cozy atmosphere.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, blonde, brown hair, blue eyes

---

(... 모든 씬 반복, 각 씬에 ⚠️ 주의사항 포함 ...)

---

# 🏗️ PHASE 3: THE GLITCH (Scene 8)

## 🔄 Scene 8: Cake Transition (00:09.28~00:11.12)

> **⚠️ 모핑 구간**: 점진적 변화

**8A - 과거 케이크:**
```
Overhead view of homemade chocolate cake with lit colorful candles.
Warm tungsten lighting, 1990s film grain, smoke wisps rising.

--iw 2.0 --ar 9:16 --v 6.0 --no modern objects, cold light
```

**8B - 현재 케이크:**
```
Overhead view of store-bought white cream cake with unlit thin candles.
Cold LED lighting, sharp digital aesthetic, sterile modern table.

--iw 2.0 --ar 9:16 --v 6.0 --no chocolate, warm light, film grain
```

---

# 🏗️ PHASE 4: THE PRESENT (Scene 9~10)

## 📱 Scene 9: Digital Isolation (00:11.12~00:13.25)

> **⚠️ Visual Rhyme**: Scene 3의 박수 구도 → 스마트폰 구도

**[Image 1: COMPOSITION]** [scene09_isolation.png URL]

Subject: 28-year-old **Korean** man sitting at a dark table with a white cake.
Crowd: **Korean** friends standing behind, faces lit ONLY by harsh blue/white smartphone flashes.
Atmosphere: Pitch black background, high contrast, cyberpunk dystopian mood.
Expression: Man has a hollow, forced smile. Friends are expressionless.

--iw 2.0 --ar 9:16 --stylize 400 --v 6.0 --style raw --no warm light, daylight, genuine happiness, western features, caucasian skin

---

## ✅ 체크리스트

| Phase | Scene | 타임코드 | ANCHOR 재사용 | 상태 |
|-------|-------|----------|--------------|------|
| 1 | **2 ⭐** | 00:01.27 | ❌ | ⬜ 먼저! |
| 2 | 1 | 00:00.00 | ✅ | ⬜ |
| 2 | 3 | 00:02.28 | ✅ | ⬜ |
...
```

---

### EXPERT 모드 추가 섹션

EXPERT 모드에서는 MINIMAL의 모든 내용 + 아래 추가:

```markdown
## 📐 Visual Forensic 분석

### Scene 2 (ANCHOR)

| 항목 | 분석 |
|------|------|
| **Shot Type** | Medium Close-up (MCU) |
| **Camera Angle** | High Angle (내려다보는 각도) |
| **Camera Height** | 아이보다 높은 위치 |
| **Composition** | Boy's face perfectly centered |
| **Light Direction** | Under-lighting (촛불이 아래에서 위로) |
| **Focus** | Shallow DOF, sharp on boy's eyes |

### 📊 Spatial Map
```
┌─────┬─────┬─────┐
│Blur │ FACE│Blur │  ← Parents out of focus (green left, red right)
├─────┼─────┼─────┤
│Body │Smile│Body │  ← Boy's upper body centered
├─────┼─────┼─────┤
│     │CAKE │     │  ← Glowing candles in foreground
└─────┴─────┴─────┘
```

### 🎨 Depth Layers
- **Foreground**: Birthday cake with tall candles (bottom 1/3)
- **Midground**: Boy's face illuminated by fire
- **Background**: Heavily blurred parents (Green blob left, Red blob right)

---

## 🪞 Visual Rhyme 전략

| Scene 3 (과거) | Scene 9 (현재) |
|---------------|---------------|
| 박수 치는 손 | 스마트폰을 든 손 |
| 가족이 아이를 바라봄 | 친구들이 화면만 봄 |
| 3200K 따뜻한 텅스텐 | 6500K 차가운 LED |
| Genuine joy | Instagram vs Reality |

---

## 🛠️ TROUBLESHOOTING

| 문제 | 해결 |
|------|------|
| 서구적 이목구비 섞임 | `Korean styling, dandy cut hair, k-pop visual` 추가 |
| 아이 얼굴 불일치 | ANCHOR_IMG URL을 모든 과거 씬에 추가 |
| 성인 얼굴 불일치 | --iw 올리기 (2.0 → 2.5) |
| 현대 씬이 따뜻함 | `--no warm colors, yellow, tungsten, amber` 추가 |

---

## 🌡️ 색보정 가이드

| 씬 | Color Temp | Contrast | Grain | Tint |
|----|------------|----------|-------|------|
| 과거 (1-7) | **3200K** | -10 | +30 | +Yellow |
| 케이크 (8A) | **3200K** | -5 | +20 | +Yellow |
| 케이크 (8B) | **6500K** | +20 | 0 | +Cyan |
| 현재 (9-10) | **6500K** | +30 | 0 | +Cyan |

---

## 🎬 Kling/Runway Motion 가이드

| Scene | Creativity | Camera | Duration | Action |
|-------|------------|--------|----------|--------|
| 1 | 0.5 | Handheld | 3s | 엄마 입장, 가족 환호 |
| 2 | 0.4 | Static | 2s | 촛불 흔들림, 미세 표정 |
| 3 | 0.5 | Handheld | 3s | 박수, 경쾌한 손 |
| 6 | 0.3 | Zoom In | 3s | 정적, 플래시 깜빡 |
| 7 | 0.3 | Static | 2s | 셀카 포즈 |
```

---

# 5회 자기비평 루프

## Loop 1: 기초 검증
- [ ] 모든 컷 전환이 개별 씬으로 분리됐는가?
- [ ] 모든 인물에 "Korean" 명시?
- [ ] "brown", "blonde" 단어 없는가?

## Loop 2: 파라미터 검증
- [ ] --iw 2.0, --cw 50, --ar 9:16, --v 6.0 포함?
- [ ] --no 파라미터가 씬별로 다른가?

## Loop 3: 구조 검증
- [ ] Phase 1, 2, 3, 4 헤더 존재?
- [ ] 각 씬에 ⚠️ 주의사항 포함?

## Loop 4: 레퍼런스 검증
- [ ] [Image 1: COMPOSITION] 라벨 있는가?
- [ ] [Image 2: CHARACTER FACE] 라벨 있는가?
- [ ] GENERATED_ANCHOR.png 재사용 표시?

## Loop 5: 최종 점검
- [ ] 타임코드 밀리초 형식? (00:01.27)
- [ ] 의상 색상 정확? (빨간색 스웨터)
- [ ] 체크리스트 테이블 존재?

---

# 📊 Tikitaka Log (반드시 출력에 포함)

| Loop | 점수 | 수정 사항 |
|------|------|----------|
| 1 | 65 | 컷 3개→10개 분리, Korean 추가 |
| 2 | 78 | --no 씬별 맞춤, 파라미터 완성 |
| 3 | 86 | Phase 분리, 주의사항 추가 |
| 4 | 93 | 듀얼 레퍼런스 라벨 |
| 5 | 98 | 타임코드 밀리초, 최종 점검 |

---

# ❌ 실패 조건 (즉시 재시작)

1. 컷 3개로 퉁침
2. "brown hair" 또는 "blonde" 사용
3. Loop 2회 이하로 끝냄
4. Phase 분리 없음
5. 듀얼 레퍼런스 라벨 없음
6. Korean 누락
7. ⚠️ 주의사항 누락
