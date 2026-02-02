# 🎬 VIDEO PARODY: 10-CUT BALANCED PROMPT v3.0

> **Core Philosophy**: 레퍼런스 이미지 구도 100% 유지 + **모든 인물** Korean 변경
> **Critical Rule**: 프레임에 등장하는 **모든 사람**의 인종을 명시해야 함 (흐릿해도!)
> **Total Duration**: 17.5초 (10씬)

---

## ⚙️ 필수 설정

```
Midjourney /settings
├── Model: V6.0 (또는 V7)
├── Style: Raw
└── Stylize: 250
```

---

## 📁 추출된 키프레임 (10-Cut 정밀)

| Scene | 실제 타임코드 | 길이 | 파일명 | 설명 |
|-------|-------------|------|--------|------|
| 1 | 00:00.00~00:01.27 | 1.27s | `scene01_arrival.png` | 엄마 케이크 등장 |
| **2 ⭐** | **00:01.27~00:02.28** | 1.01s | **`ANCHOR_IMG.png`** | 아이 단독 정면 |
| 3 | 00:02.28~00:04.05 | 1.37s | `scene03_sideview.png` | 측면 가족 반응 |
| 4 | 00:04.05~00:06.00 | 1.95s | `scene04_clapping_a.png` | 박수 초반 |
| 5 | 00:06.00~00:08.10 | 2.10s | `scene05_clapping_b.png` | 박수 클라이맥스 |
| 6 | 00:08.10~00:08.50 | 0.40s | `scene06_pre_blow.png` | 숨 들이마심 |
| 7 | 00:08.50~00:09.28 | 0.78s | `scene07_blowout.png` | 촛불 끄기 |
| 8 | 00:09.28~00:11.12 | 1.84s | `scene08_glitch.png` | 케이크 모핑 전환 |
| 9 | 00:11.12~00:13.25 | 2.13s | `scene09_isolation.png` | 플래시 고립 |
| 10 | 00:13.25~00:17.29 | 4.04s | `scene10_selfie.png` | 셀카 엔딩 |

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
> **⚠️ 수정**: 좌측은 누나(sister), 후방에 부모

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

## 📼 Scene 4: Clapping A (00:04.05~00:06.00)

> **파일**: `keyframes/scene04_clapping_a.png`
> **박수 초반**: 노래 시작, 활기찬 분위기

```
**[Image 1: COMPOSITION]** [scene04_clapping_a.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact composition, hand positions.
**From Image 2**: Copy the Korean boy's face.

Replace **all people** with Korean family:
- Center: Korean boy (use face from Image 2) smiling shyly
- Parents: Korean mom and dad clapping, mouths open singing

Keep motion blur on hands, warm tungsten lighting, joyful atmosphere.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin
```

---

## 📼 Scene 5: Clapping B - Climax (00:06.00~00:08.10)

> **파일**: `keyframes/scene05_clapping_b.png`
> **박수 클라이맥스**: 가장 활기찬 순간

```
**[Image 1: COMPOSITION]** [scene05_clapping_b.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

**From Image 1**: Copy exact triangular composition, hand blur apex.
**From Image 2**: Copy the Korean boy's face.

Replace **all people** with Korean family:
- Center: Korean boy (use face from Image 2) receiving applause
- Parents: Korean mom and dad clapping energetically

Keep heavy motion blur on clapping hands, warm amber lighting.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, static hands
```

---

## 📼 Scene 6: Pre-Blowout (00:08.10~00:08.50)

> **파일**: `keyframes/scene06_pre_blow.png`
> **0.4초 찰나**: 눈 뜨고 숨 들이마시는 순간

```
**[Image 1: COMPOSITION]** [scene06_pre_blow.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

Close-up. Replace child with Korean boy (face from Image 2):
- Expression: Eyes open, looking at candles, lips pursing, taking deep breath (inhale)
- Lighting: Strong candlelight reflecting on face (chiaroscuro)

Keep magical anticipating mood, warm tungsten + candlelight mix.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, eyes closed, blowing
```

---

## 📼 Scene 7: The Blowout (00:08.50~00:09.28)

> **파일**: `keyframes/scene07_blowout.png`
> **⚠️ 주의**: 촛불 꺼지자마자 화면 어두워짐

```
**[Image 1: COMPOSITION]** [scene07_blowout.png URL]
**[Image 2: CHARACTER FACE]** [GENERATED_ANCHOR.png URL]

Extreme close-up. Replace child with Korean boy (face from Image 2):
- Action: Cheeks puffed out, blowing air
- Details: Candle flames bending away from breath

Keep warm amber candlelight transitioning to dimmer room light.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, caucasian skin, calm face
```

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

## ✅ 10-Cut 체크리스트

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
