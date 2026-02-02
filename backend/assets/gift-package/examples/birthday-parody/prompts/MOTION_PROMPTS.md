# 🎬 K-PARADOX MOTION PROMPTS v9.0 (10-CUT)

> **Project**: Birthday Glitch
> **Total Duration**: 17.5초 (10씬)
> **Engine**: Kling 2.0 High Quality
> **Rule**: 5초 생성 → 각 씬 길이만큼만 잘라서 사용

---

## ⚙️ GLOBAL SETTINGS

### Kling Canvas 사용법
```
1. 완성된 씬 이미지 드래그앤드롭
2. 아래 프롬프트 복사 입력
3. 5초 생성 → 해당 씬 길이만큼 앞부분만 사용
```

### 타이밍 원칙
```
✅ 핵심 동작: "IMMEDIATELY" / "within first second"
✅ 이후 동작: "then holds" / "continuous"
✅ Negative: "delayed *" 추가
```

---

## 📊 10-CUT TIMEFRAME

| Scene | 타임코드 | 길이 | 설명 |
|-------|----------|------|------|
| 1 | 00:00.00~00:01.27 | 1.27s | Arrival |
| 2 | 00:01.27~00:02.28 | 1.01s | Anchor Boy |
| 3 | 00:02.28~00:04.05 | 1.37s | Side View |
| 4 | 00:04.05~00:06.00 | 1.95s | Clapping A |
| 5 | 00:06.00~00:08.10 | 2.10s | Clapping B |
| 6 | 00:08.10~00:08.50 | 0.40s | Pre-Blow |
| 7 | 00:08.50~00:09.28 | 0.78s | Blowout |
| 8 | 00:09.28~00:11.12 | 1.84s | Glitch |
| 9 | 00:11.12~00:13.25 | 2.13s | Isolation |
| 10 | 00:13.25~00:17.29 | 4.04s | Selfie |

---

## 📼 SCENE 1: The Arrival (1.27s)

> **Use**: 0~1.27초

### [📋 COPY] Positive
```
A warm cinematic home video. IMMEDIATELY the Korean mother lowers a lit birthday cake onto the table within the first second. Cake touches table by beat one. Then she releases and smiles, holding pose. Family watches. 35mm grain, tungsten lighting.
```

### [📋 COPY] Negative
```
slow motion, walking around, delayed action, morphing, floating cake, distortion.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **4** |

---

## 📼 SCENE 2: Anchor Boy (1.01s)

> **Use**: 0~1초

### [📋 COPY] Positive
```
Close-up of a Korean boy. IMMEDIATELY he shows a shy gentle smile (lips closed) in the first half-second. Candle flames flicker on his face. Then he holds this anticipating expression, eyes sparkling. Continuous subtle breathing. Sharp focus.
```

### [📋 COPY] Negative
```
morphing face, changing features, delayed reaction, static image.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **3** |

---

## 📼 SCENE 3: Side View (1.37s)

> **Use**: 0~1.4초
> **⚠️ 수정**: 좌측 누나, 후방 부모

### [📋 COPY] Positive
```
Side view of the Korean family. IMMEDIATELY the sister on the left leans on the table, smiling at her brother. The dad and mom in the background lean forward with affection. Everyone gazes warmly at the boy. Natural, cozy family movement. Then holds this intimate pose.
```

### [📋 COPY] Negative
```
frontal view, frozen people, delayed movement, morphing, sister missing.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **4** |

---

## 📼 SCENE 4: Clapping A (1.95s)

> **Use**: 0~2초

### [📋 COPY] Positive
```
Clapping STARTS IMMEDIATELY from beat one. Korean family clapping rhythmically while singing happy birthday. Mouths open forming words. Hands meet and separate clearly. Natural swaying bodies. Warm joyful atmosphere.
```

### [📋 COPY] Negative
```
fused fingers, extra fingers, delayed start, slow clapping, static mouths.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **6** |

---

## 📼 SCENE 5: Clapping B - Climax (2.10s)

> **Use**: 0~2.1초

### [📋 COPY] Positive
```
Peak energy clapping CONTINUOUS from start. Fast, energetic hand clapping by entire Korean family. Maximum motion blur on hands. Hands moving rapidly with distinct separation. Rhythmic beat throughout. Handheld camera shake. Real-time speed.
```

### [📋 COPY] Negative
```
fused fingers, melting hands, spaghetti hands, slow clapping, slowing down.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **7** (Max) |

### ⚠️ 실패 시
Motion Brush → 손 영역 Intensity **8**

---

## 📼 SCENE 6: Pre-Blowout (0.40s) ⚡ CRITICAL

> **Use**: 0~0.4초만! (매우 짧음)

### [📋 COPY] Positive
```
IMMEDIATELY in the first 0.3 seconds, the boy takes a visible deep breath in. His chest rises slightly. Lips pursing, preparing to blow. Eyes open, fixed on candles. Chiaroscuro candlelight on face. Held anticipation pose.
```

### [📋 COPY] Negative
```
blowing out, exhaling, delayed inhale, eyes closing, morphing.
```

| Camera | Motion Score |
|--------|-------------|
| Zoom In (Micro) | **3** |

---

## 📼 SCENE 7: The Blowout (0.78s)

> **Use**: 0~0.8초

### [📋 COPY] Positive
```
IMMEDIATELY in the first 0.3 seconds, the boy blows and ALL candles extinguish instantly. Grey smoke rises rapidly. Room lighting shifts from warm glow to dimmer as flames die. Boy's face relaxes with satisfaction.
```

### [📋 COPY] Negative
```
fire remaining, slow fade, delayed extinguish, sucking air, backward smoke.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **5** |

---

## 🔄 SCENE 8: The Glitch (1.84s)

> **Use**: 0~1.8초 (모핑 전환 구간)

### [📋 COPY] Positive
```
Top-down cake view. STARTS with warm chocolate cake, lit candles, smoke rising. Candle flames flicker naturally. Continuous gentle morphing transition to cold modern white cake with unlit candles. LED lighting gradually replaces tungsten.
```

### [📋 COPY] Negative
```
jump cut, instant change, frozen image, no transition.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **2** |

---

## 📱 SCENE 9: Digital Isolation (2.13s)

> **Use**: 0~2.1초
> **⚠️ 수정**: 남자 어깨 호흡 동작

### [📋 COPY] Positive
```
Flashlights START STROBING IMMEDIATELY from beat one. Dark party scene. The Korean man sits with hollow smile, but his shoulders rise and fall slightly with breathing. Friends behind him are frozen like mannequins, but smartphone flashes strobe and flicker aggressively throughout. Slow zoom out.
```

### [📋 COPY] Negative
```
people walking, talking, delayed flash, warm light, large movements, static shoulders.
```

| Camera | Motion Score |
|--------|-------------|
| Zoom Out (Slow) | **4** |

---

## 📱 SCENE 10: The Selfie (4.04s)

> **Use**: 0~4초 (롱테이크)
> **⚠️ 수정**: 여자 고개 왼쪽 틸트

### [📋 COPY] Positive
```
POV smartphone selfie. IMMEDIATELY the Korean woman tilts her head slightly to the LEFT while posing in the first second. Camera has handheld shake throughout entire 4 seconds. She makes small pose adjustments. The man in background blinks once robotically around second 2, then holds blank stare. Harsh flash lighting.
```

### [📋 COPY] Negative
```
tripod shot, smooth motion, static pose, head tilting right, warm colors.
```

| Camera | Motion Score |
|--------|-------------|
| Roll (Handheld) | **5** |

---

## ✅ FINAL CHECKLIST

- [ ] 5초 생성 → 각 씬 길이만큼만 컷
- [ ] Scene 5 박수 실패 시 Motion Brush
- [ ] Scene 6 **0.4초만** 사용 주의
- [ ] Scene 8 **모핑 효과** 확인
- [ ] Scene 10 **4초 롱테이크** 전체 사용
