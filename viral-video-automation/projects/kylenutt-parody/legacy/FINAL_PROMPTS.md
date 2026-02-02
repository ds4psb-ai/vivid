# 🎬 BIRTHDAY PARADOX: PRODUCTION MASTER (v9.0 SSOT)

> **Core Concept**: 1990년대 한국 가정의 '따뜻한 유대' vs 2020년대 서울의 '화려한 고립'
> 
> **Technique**: Image Prompting `--iw 2.0` (형태 강제 고정) + Anchor System (얼굴 일관성)

---

## ⚠️ 필수 준비물 (Pre-requisites)

1. **원본 캡처 (Source Images)**: 아래 지정 구간을 **고화질로 캡처**하여 디스코드에 업로드 후 URL 확보
   - 00:01.15 (Scene 1용 - 역삼각형 구도 완벽)
   - 00:03.10 (Scene 2 ANCHOR용 - 아이 정면 안정)
   - 00:06.05 (Scene 3용 - 박수 Apex)
   - 00:11초 (Scene 6용 - 폰 많이 보이는 프레임)
   - 00:14초 (Scene 7용)

2. **Anchor Image (기준 얼굴)**: Scene 2에서 생성된 '가장 완벽한 한국 아이' 이미지를 저장 → 모든 과거 씬에 URL 추가

3. **`--iw 2.0`** → 구도 강제 고정 (Image Weight)

---

## ⚙️ 초기 세팅 (Midjourney /settings)

```
Model: V6.0
Style: Raw
Aspect Ratio: --ar 9:16
Stylize: 250 (적당한 예술성)
Weird: 0 (기괴함 제거)
```

### 🔑 프롬프트 입력 공식

```
[원본 캡처 URL] [프롬프트] --iw 2.0 --ar 9:16 --v 6.0
```

---

# 🏗️ PHASE 1: THE ANCHOR (얼굴 고정)

## 📼 SCENE 2: The Anticipation (00:03.10) ⭐ [ANCHOR]

> **목표**: 이후 모든 씬의 기준이 될 '한국 아이'의 얼굴 확정
> **💾 저장**: `keyframes/ANCHOR_IMG.png`
> **🔗 Reference**: 00:03.10 캡처 (촛불을 바라보는 아이 클로즈업 - 컷 전환 전 안전지점)

### 📐 Visual Forensic 분석 (전문가 팩트)

| 항목 | 분석 |
|------|------|
| **Shot Type** | Medium Close-up (MCU) |
| **Camera Angle** | **High Angle** (아이를 내려다보는 각도) |
| **Camera Height** | 아이보다 높은 위치 |
| **Composition** | Boy's face perfectly centered |
| **Light Direction** | **Under-lighting** (촛불이 아래에서 위로 비춤) |
| **Focus** | 아이 눈에 초점, 배경은 흐릿함 (Bokeh) |

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
- **Focus**: Shallow depth of field (Bokeh), sharp on boy's eyes

### 🌡️ Lighting
- **Type**: Underlight from candle flames
- **Color Temperature**: 3200K (Warm tungsten + candlelight)
- **Quality**: Soft, warm, nostalgic

```
[COPY THIS]

[Insert 00:03.10 Capture URL]

Medium close-up, **high angle shot looking down** at a 7-year-old Korean boy.

**Face**: Black bowl-cut hairstyle (1990s Korean style), single eyelids, looking down at the cake with a shy, excited smile. Face perfectly centered. Face illuminated from below by warm candlelight (under-lighting).

**Foreground**: Birthday cake with tall flickering flames in the bottom 1/3 of frame.

**Background**: Heavily blurred parents - green blob (dad's shirt) on left, red blob (mom's sweater) on right. Shallow depth of field, sharp focus on boy's eyes.

**Details**: Minimalist striped t-shirt (white with thin multi-colored horizontal stripes). Dark home interior background with 1990s floral wallpaper barely visible.

**Vibe**: 1990s home video, Kodak Portra 400 film grain, warm tungsten (3200K), nostalgic atmosphere.

--iw 2.0 --ar 9:16 --stylize 300 --v 6.0 --no text, timestamp, date overlay, ui, hud, watermark, western features, beard, sharp digital look
```

> 👉 **팁**: 가장 완벽한 결과를 `ANCHOR_IMG.png`로 저장. 이후 모든 과거 씬에 이 URL을 추가로 넣습니다.

---

# 🏗️ PHASE 2: THE 90s (과거의 온기)

## 📼 SCENE 1: The Arrival (00:00 - 00:04)

> **🔗 Reference**: 00:01.15 캡처본 + ANCHOR_IMG 링크
> **💾 저장**: `keyframes/scene01_arrival.png`

### 📐 Visual Forensic 분석

| 항목 | 분석 |
|------|------|
| **Shot Type** | Wide Shot (WS) |
| **Camera Angle** | Slight High Angle (above adult eye level) |
| **Camera Height** | Slightly above the seated child |
| **Composition** | Reverse Triangle (역삼각형) |

### 📊 Spatial Map
```
┌─────┬─────┬─────┐
│ DAD │     │ MOM │  ← Adults standing (forming arch)
├─────┼─────┼─────┤
│torso│ dad │torso│  ← Uncle in green behind
├─────┼─────┼─────┤
│     │ BOY │     │  ← Child seated at bottom center
└─────┴─────┴─────┘
```
- **BOY**: Seated at table (bottom center)
- **DAD**: Standing behind/left (vertical striped polo)
- **UNCLE**: Standing left-back (green shirt, mustache)
- **MOM**: Entering from right with cake (red sweater)
- **GUEST**: Seated right (white bucket hat)

### 🎨 Depth Layers
- **Foreground**: Wooden table surface (blurred edge, bottom 30% of frame)
- **Midground**: The boy (seated), Father (standing), Mother (entering with cake)
- **Background**: Wall with floral wallpaper, balloons, cherry wood molding
- **Focus**: Deep focus (entire family relatively sharp)

### 🌡️ Lighting
- **Type**: Indoor ambient + candlelight
- **Color Temperature**: 3200K (Warm tungsten)
- **Quality**: Cozy, soft shadows, nostalgic

```
[COPY THIS]

[Insert 00:01.15 Capture URL] [ANCHOR_IMG URL]

Wide shot, slight high angle looking down at the table from standing adult height. Symmetrical reverse-triangle composition with the boy seated low in the bottom-center.

A nostalgic 1990s Korean family birthday party in a middle-class apartment living room.

**Center-Bottom**: The 7-year-old Korean boy with black bowl cut and single eyelids (from anchor image) sitting at a dark wooden table. He wears a white t-shirt with thin multi-colored horizontal stripes.

**Character Positioning (clockwise from left)**:
1. Left-Front: A Korean father figure in a vertical striped polo shirt leaning in toward the boy.
2. Left-Back: A Korean uncle with a mustache in a green button-up shirt standing behind.
3. Right: A Korean mother in a red/maroon sweater bringing a chocolate birthday cake with lit colorful candles, entering from the right side of frame.
4. Right-Seated: A man in a white bucket hat seated at the table.
5. Left-Seated: A young girl in a striped dress sitting next to the boy.

**Environment**: 1990s South Korean apartment interior. Background features floral wallpaper, dark cherry-wood molding, colorful balloons taped to wall, visible kitchen cabinet edge.

**Foreground**: Wooden table surface visible in the immediate foreground, occupying bottom 30% of frame. Chocolate cake with lit candles exactly in center of table.

**Lighting**: Warm tungsten room lighting (3200K) mixed with candlelight glow, cozy atmosphere, heavy film grain, soft shadows. Deep depth of field keeping whole family in focus.

**Style**: 1990s home video footage (Hi8 aesthetic), 35mm film stock texture, grainy, slightly washed out colors, nostalgic mood.

--iw 2.0 --ar 9:16 --stylize 250 --v 6.0 --no text, timestamp, date overlay, ui, hud, watermark, western features, modern furniture, led lights, sharp digital look
```

---

## 📼 SCENE 3: The Clapping (00:05 - 00:08) 🪞 [VISUAL RHYME SOURCE]

> **🔗 Reference**: 00:06.05 캡처본 + ANCHOR_IMG 링크 (박수 정점)
> **💾 저장**: `keyframes/scene03_clapping.png`
> 
> ⚠️ **중요**: 이 장면의 '박수 치는 손' 위치가 나중에 '스마트폰' 위치가 됩니다!
> | Scene 3 | Scene 6 |
> |---------|----------|
> | 박수치는 손 | 스마트폰을 든 손 |
> | 따뜻한 눈빛 | 차가운 액정 |
> | 행복 | 공허함 |

### 📐 Visual Forensic 분석

| 항목 | 분석 |
|------|------|
| **Shot Type** | Medium Shot (MS) |
| **Camera Angle** | Eye-level |
| **Camera Height** | Level with seated boy |
| **Composition** | Triangular (three figures create triangle) |

### 📊 Spatial Map
```
┌─────┬─────┬─────┐
│ DAD │     │ MOM │  ← Parents standing, clapping
├─────┼─────┼─────┤
│clap │ BOY │clap │  ← Boy in center, all hands visible
├─────┼─────┼─────┤
│     │table│     │  ← Table edge in foreground
└─────┴─────┴─────┘
```
- **BOY**: Clapping in center (main focus)
- **DAD/UNCLE**: Framing the boy from left behind
- **MOM**: Framing the boy from right behind

### 🎨 Depth Layers
- **Foreground**: Table edge
- **Midground**: Boy clapping hands (motion blur on hands)
- **Background**: Parents standing behind, wall decorations
- **Focus**: Focus on boy, slight fall-off on parents

### 🌡️ Lighting
- Same as Scene 1 (3200K tungsten, warm amber)

```
[COPY THIS]

[Insert 00:06.05 Capture URL] [ANCHOR_IMG URL]

Medium shot at eye level with the seated boy. Triangular composition with the seated boy in the center and parents standing on the left and right behind him, forming a protective arch.

The 7-year-old Korean boy (black bowl cut, single eyelids, striped shirt) sits in the center of frame at a wooden table. He is clapping his small hands excitedly, looking up with unadulterated happiness and a broad genuine smile.

**Behind him (forming arch)**:
- Left: Korean father (vertical striped polo) and uncle (green shirt, mustache) clapping enthusiastically
- Right: Korean mother (red/maroon sweater) clapping and singing with genuine joy

**Action**: Everyone is clapping hands happily. All eyes focused lovingly on the boy. Slight motion blur on the clapping hands representing lively energy.

**Foreground**: Table edge visible at bottom of frame.

**Vibe**: Genuine joy, chaotic happiness, authentic Korean family moment, unposed, lively.

**Lighting**: Cozy indoor incandescent lighting (3200K yellowish tungsten tone), warm amber tones, soft film grain texture.

**Style**: 1990s home video, film photography aesthetic.

--iw 2.0 --ar 9:16 --stylize 250 --v 6.0 --no text, timestamp, date overlay, ui, hud, watermark, western features, smartphones, cool lighting, sad faces
```

---

## 📼 SCENE 4: The Blow Out (00:08 - 00:09)

> **🔗 Reference**: 촛불 끄는 장면 캡처 + ANCHOR_IMG
> **💾 저장**: `keyframes/scene04_blowout.png`

### 📐 Visual Forensic 분석

| 항목 | 분석 |
|------|------|
| **Shot Type** | Close-up (CU) to Extreme Close-up |
| **Camera Angle** | Eye-level / Slight side profile |
| **Camera Height** | Level with cake flames |
| **Composition** | Boy leaning forward into lens |

### 📊 Spatial Map
```
┌─────┬─────┬─────┐
│     │Head │     │  ← Top of boy's head
├─────┼─────┼─────┤
│     │FACE │     │  ← Puffed cheeks, squinted eyes
├─────┼─────┼─────┤
│     │Blow │     │  ← Mouth and candles interaction
└─────┴─────┴─────┘
```

### 🎨 Depth Layers
- **Foreground**: Candles (some extinguished, smoke rising)
- **Midground**: Boy's face, puffed cheeks
- **Background**: Dark, undefined warm bokeh (green/red blur)
- **Focus**: Sharp on lips and candles

```
[COPY THIS]

[Insert Original Capture URL] [ANCHOR_IMG URL]

Tight close-up shot. The boy leans forward from the center, face filling the frame.

The 7-year-old Korean boy (black bowl cut, single eyelids) leaning forward with cheeks puffed out, eyes slightly squinted in concentration, blowing out the candles on the birthday cake.

**Focus**: Mouth positioned near the bottom center of frame, blowing towards the lens. Sharp focus on lips and candle flames.

**Detail**: Wisps of gray smoke beginning to rise from extinguished candles visible in the foreground. The moment of wish-making.

**Background**: Dark and creamy bokeh - soft blur of warm colors (green shirt, red sweater, beige wallpaper). High contrast between the flame and the face.

**Atmosphere**: Intimate, nostalgic, the moment before total darkness.

**Lighting**: Warm amber tones (3200K), candlelight as primary source, soft focus background, film grain.

--iw 2.0 --ar 9:16 --stylize 300 --v 6.0 --no text, timestamp, date overlay, ui, hud, watermark, western features, static pose, sharp digital
```

---

# 🏗️ PHASE 3: THE TRANSITION (매치 컷)

> 생성형 비디오 툴에서 Morph 기능을 쓰기 위해 정확한 탑뷰(Top-down) 필요
> 두 케이크의 위치가 **정확히 중앙**에 있어야 Cross Dissolve가 완벽함

## 🔄 SCENE 5A: 과거 케이크

> **💾 저장**: `keyframes/scene05a_cake_past.png`

### 📐 Visual Forensic 분석

| 항목 | 분석 |
|------|------|
| **Shot Type** | Top-down (Overhead / God's eye view) |
| **Camera Angle** | 90-degree vertical down |
| **Composition** | Dead center (perfect circle in rectangle) |
| **Symmetry** | Radial symmetry |

### 📊 Spatial Map
```
┌─────┬─────┬─────┐
│     │     │     │
├─────┼─────┼─────┤
│     │CAKE │     │  ← Perfect center
├─────┼─────┼─────┤
│     │     │     │
└─────┴─────┴─────┘
```

```
[COPY THIS]

Direct top-down 90-degree overhead shot (flat lay). The round cake is perfectly centered in the middle of the frame, creating a symmetrical circle-in-rectangle composition. No perspective distortion.

A messy, homemade imperfect chocolate birthday cake with colorful wax candles (7 candles, some slightly tilted) on a retro dark wooden table. Imperfect frosting with colorful flower decorations.

Warm vintage tungsten lighting, visible heavy film grain, soft focus edges. 1990s film aesthetic.

--ar 9:16 --no text, timestamp, modern cake, white cream, cool lighting, minimalism, sharp digital
```

---

## 🔄 SCENE 5B: 현재 케이크

> **💾 저장**: `keyframes/scene05b_cake_present.png`

```
[COPY THIS]

Direct top-down 90-degree overhead shot (flat lay). The round cake is perfectly centered in the middle of the frame, creating a symmetrical circle-in-rectangle composition. No perspective distortion.

A pristine, store-bought minimalist white cream cake with thin modern candles on a sleek black/dark table. Clean geometric lines, perfect frosting.

Cold white LED lighting (6500K), sharp digital focus, high contrast, sterile atmosphere. Modern 2020s aesthetic.

--ar 9:16 --no text, timestamp, chocolate cake, warm lighting, film grain, colorful decorations, imperfect
```

---

# 🏗️ PHASE 4: THE PRESENT (현대의 냉기)

## 📱 SCENE 6: The Digital Isolation (00:10 - 00:13) 🪞 [VISUAL RHYME TARGET]

> **핵심**: Scene 3의 구도를 **그대로 베끼되**, 내용물만 반전!
> **🔗 Reference**: 00:11초 캡처 (폰이 많이 보이는 프레임)
> **💾 저장**: `keyframes/scene06_lonely.png`
> 
> 🪞 **Visual Rhyme Strategy**: Scene 3 → Scene 6 치환
> | Scene 3 (과거) | Scene 6 (현재) |
> |---------------|---------------|
> | 박수치는 손 | 스마트폰을 든 손 |
> | 가족이 아이를 바라봄 | 친구들이 화면만 봄 |
> | 3200K 따뜻한 텅스텐 | 6500K 차가운 LED |
> | Genuine joy | Instagram vs Reality |

### 📐 Visual Forensic 분석

| 항목 | 분석 |
|------|------|
| **Shot Type** | Medium Shot (MS) - SAME AS SCENE 3 |
| **Camera Angle** | Slightly High Angle (emphasizing isolation) |
| **Camera Height** | Above seated subject |
| **Composition** | Pyramidal (subject at bottom, crowd forms arch above) |

### 📊 Spatial Map
```
┌─────┬─────┬─────┐
│PHONE│PHONE│PHONE│  ← Bright LED lights forming wall
├─────┼─────┼─────┤
│friend│HEAD │friend│  ← Friends holding phones, not looking at him
├─────┼─────┼─────┤
│     │BODY │     │  ← Man seated, isolated
└─────┴─────┴─────┘
```
- **PHONE**: Bright LED flashlights facing camera/man
- **HEAD/BODY**: Man seated, looking disconnected ("dead inside")
- **friends**: Standing around him in semi-circle arch (MATCHING parent positions from Scene 3)

### 🎨 Depth Layers
- **Foreground**: Empty table space or minimalist white cake
- **Midground**: The man (seated, isolated)
- **Background**: Wall of people holding phones (5-6 friends in semi-circle)
- **Lighting**: Flashlights from background cut through darkness (Chiaroscuro)

### 🌡️ Lighting (CRITICAL)
- **Type**: ONLY smartphone LED flashlights (no other light source)
- **Color Temperature**: 6500K (Cold white)
- **Quality**: Harsh, directional, Chiaroscuro effect
- **Effect**: Rim lighting on shoulders, lens flares, oily skin texture

```
[COPY THIS]

[Insert 00:11 Capture URL] (폰이 많이 보이는 프레임 사용)

Medium shot, exact visual composition match to Scene 3 (the 90s clapping scene) but in modern cold context. Slightly high angle from above seated subject.

Pyramidal composition with the seated man at the bottom center foundation. A semi-circle of standing friends fills the upper background, looming over him (EXACTLY where parents stood in Scene 3).

**Subject**: A handsome 28-year-old Korean man with sharp jawline, single eyelids (same eye shape as the boy), pale skin, trendy 'Dandy cut' or 'Guile cut' black hair, wearing a black dress shirt. He sits at a table in a dark room with a minimalist white birthday cake in front of him.

**Expression**: He smiles politely, but his eyes are empty, tired, and dissociated. "Dead inside" despite smiling. Frozen, awkward, performative smile.

**Crowd (5-6 young Korean friends standing in semi-circle arch behind him)**:
- NO ONE is looking at him with their eyes
- Everyone is holding a smartphone up with bright LED flashlight turned on, screens facing themselves
- They are filming/recording him, looking at their phone screens, not at the birthday man
- Their phones form a wall of light behind him

**Lighting**: PITCH BLACK room. The scene is lit ONLY by the harsh, cold white LED flashlights (6500K) from the smartphones. High contrast between dark foreground and bright LED lights. Chiaroscuro effect. Rim lighting on the man's shoulders from the phone lights. Lens flares from the multiple flash sources. Oily skin texture visible (shine).

**Atmosphere**: Cold, sterile, isolated, performative, "Instagram vs Reality", cynical, sharp digital 4K aesthetic, no warmth whatsoever.

--iw 2.0 --ar 9:16 --stylize 450 --v 6.0 --no text, timestamp, watermark, warm lights, candles, sunlight, yellow tones, tungsten, incandescent, happy eyes, genuine smile, clapping hands, film grain, vintage
```

---

## 📱 SCENE 7: The Flashlight Selfie POV (00:14 - End)

> **🔗 Reference**: 마지막 셀카 찍는 장면 캡처
> **💾 저장**: `keyframes/scene07_selfie.png`

### 📐 Visual Forensic 분석 (전문가 팩트)

| 항목 | 분석 |
|------|------|
| **Shot Type** | Medium Close-up (Selfie perspective) |
| **Camera Angle** | **Selfie Arm Extension** (팝을 뼼 각도, 얼굴 왔곡) |
| **Camera Height** | Slightly above eye level |
| **Lens Effect** | Wide-angle barrel distortion |
| **Hierarchy** | **여자가 화면 장악**, 남자는 배경 소품처럼 취급 |

### 📊 Spatial Map (전문가 팩트)
```
┌─────┬─────┬─────┐
│ WOMAN     │     │  ← 여자가 화면 왼쪽 2칸 크게 차지!
├─────┼─────┼─────┤
│     │ MAN │     │  ← 남자는 우측 뒤, 초점 맞음
├─────┼─────┼─────┤
│     │     │     │
└─────┴─────┴─────┘
```
- **WOMAN**: 왼쪽에서 프레임 지배, 폰 화면만 바라보며 포즈 (**렌즈 안 봄**)
- **MAN**: 오른쪽 뒤로 밀려남, 수동적, 가짜 미소

### 🎨 Depth Layers
- **Foreground**: Woman's shoulder/arm, her face
- **Midground**: Man and Woman's faces side-by-side (asymmetrical)
- **Background**: Pitch black void with bokeh points of other phone lights
- **Focus**: Sharp digital focus on both faces

```
[COPY THIS]

[Insert 00:14 Capture URL]

**Selfie angle close-up with wide-angle distortion.** Camera at arm extension angle.

**Foreground (Left - 화면 지배)**: A trendy Korean woman with long dark hair leans in close to take a selfie. **Her face dominates the left side of the frame** (taking up nearly half the image). She looks ONLY at her phone screen, posing, **ignoring the lens entirely**.

**Background (Right - 배경 소품 취급)**: The Korean birthday man (28, black shirt, Dandy cut hair, single eyelids) sits passively behind her. He maintains a frozen, mechanical, fake smile, staring slightly away from the lens. Eyes remain empty and tired.

**Lighting**: **Direct on-camera flash effect**. Harsh white light that flattens features. **"Red-eye" vibe**, oily skin texture, pale skin tones. Realistic night out photography aesthetic.

**Background**: Pitch black darkness punctuated by multiple other phone screens visible recording the event (bokeh points of light).

**Atmosphere**: Artificial, performative, disconnected. No genuine connection between the two people.

--iw 2.0 --ar 9:16 --stylize 450 --v 6.0 --no text, timestamp, watermark, warm lighting, professional lighting, soft box, studio portrait, genuine happiness, natural light, western features
```

---

# 🛠️ TROUBLESHOOTING (전문가 팁)

## 🎭 얼굴이 한국인 같지 않을 때
| 문제 | 해결 |
|------|------|
| 서구적 이목구비 섞임 | 프롬프트에 `Korean styling, dandy cut hair, k-pop visual` 추가 |
| 아이 얼굴 불일치 | ANCHOR_IMG URL을 모든 과거 씬에 추가 |
| 성인 얼굴 불일치 | --iw 올리기 (2.0 → 2.5) |

## 🚫 조명이 안 맞을 때
| 문제 | 해결 |
|------|------|
| 현대 씬이 따뜻함 | `--no warm colors, yellow, tungsten, amber` 파라미터 끝에 추가 |
| 플래시 안 보임 | 프롬프트에 `LED flashlights (6500K)::2` 가중치 추가 |

## 🪞 Visual Rhyme 안 맞을 때
| 문제 | 해결 |
|------|------|
| Scene 6이 Scene 3과 다름 | Scene 3 캡처를 Scene 6 Reference로 추가 |
| 손 위치가 다름 | `exact visual composition match to Scene 3` 강조 |

## 🚫 텍스트/타임스탬프 나올 때
```
--no text, timestamp, date overlay, numbers, digits, watermark, ui, hud
```

---

# 🌡️ 색보정 가이드

| 씬 | Color Temp | Contrast | Grain | Tint |
|----|------------|----------|-------|------|
| 과거 (1-4) | **3200K** (Amber/Tungsten) | -10 | +30 | +Yellow |
| 케이크 (5A) | **3200K** | -5 | +20 | +Yellow |
| 케이크 (5B) | **6500K** | +20 | 0 | +Cyan |
| 현재 (6-7) | **6500K** (Cool White/LED) | +30 | 0 | +Cyan |

### 플래시 효과 (Scene 6, 7)
```
Exposure: +0.7
Black Point: -40
Highlights: +50
Clarity: +30
Chiaroscuro (명암 대비 극대화)
```

---

# 🎬 Kling/Runway Motion 가이드 (전문가 팁)

| Scene | Creativity | Camera | Duration | Action |
|-------|------------|--------|----------|--------|
| 1 | 0.5 | Handheld shake | 3s | 엄마 입장, 가족 환호 |
| 2 | 0.4 | Static | 2s | 촛불 흔들림, 미세한 표정 |
| 3 | 0.5 | Handheld shake | 3s | 박수, 경쾌한 손 움직임 |
| 4 | 0.6 | Static | 1s | 촛불 끄기, 연기 피어오름 |
| 5 | 0.2 | Static | 1s | Morph 전환 |
| 6 | 0.3 | Slight Zoom In | 3s | 정적, 플래시만 깜빡임 |
| 7 | 0.3 | Static | 2s | 셀카 포즈 |

### 🎯 Motion Brush 전문가 팁

**Scene 3 (박수):**
- Motion Brush로 **사람들의 손만** 선택
- 손: **High Motion**
- 얼굴: **Low Motion** (안 일그러짐)

**Scene 6 (플래시):**
- 움직임 **거의 주지 마세요**
- 카메라: Slight Zoom In만
- 폰은 가만히, **플래시 불빛만 번쩍** → 더 섬뜩하고 고립된 느낌

---

# ✅ 체크리스트

| Phase | Scene | 파일명 | Reference | --iw | 상태 |
|-------|-------|--------|-----------|------|------|
| **1** | **Scene 2 (ANCHOR)** | `ANCHOR_IMG.png` | 원본 캡처 | 2.0 | ⬜ |
| 2 | Scene 1 | `scene01_arrival.png` | 원본 + ANCHOR | 2.0 | ⬜ |
| 2 | Scene 3 🪞 | `scene03_clapping.png` | 원본 + ANCHOR | 2.0 | ⬜ |
| 2 | Scene 4 | `scene04_blowout.png` | 원본 + ANCHOR | 2.0 | ⬜ |
| 3 | Scene 5A | `scene05a_cake_past.png` | - | - | ⬜ |
| 3 | Scene 5B | `scene05b_cake_present.png` | - | - | ⬜ |
| **4** | **Scene 6 🪞** | `scene06_lonely.png` | 원본 (+ Scene 3 구도) | 2.0 | ⬜ |
| 4 | Scene 7 | `scene07_selfie.png` | 원본 | 2.0 | ⬜ |
