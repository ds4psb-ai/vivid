# 🎨 Midjourney V7 프롬프트 가이드

> **최적 용도**: ANCHOR 생성, 클로즈업, 정교한 얼굴 제어
> **최신 스펙**: 2026년 1월 (V7 기본 모델)

---

## 📊 스펙 요약

| 파라미터 | 범위 | 기본값 | 설명 |
|----------|------|--------|------|
| `--iw` | 0 ~ 3 | 1 | Image Weight (레퍼런스 영향력) |
| `--oref` | URL | - | Omni Reference (얼굴/형태 유지) |
| `--cw` | 0 ~ 100 | 100 | Character Weight |
| `--stylize` | 0 ~ 1000 | 100 | 예술적 해석 강도 |
| `--raw` | flag | - | 프롬프트 충실도 최대화 |

---

## 🎯 추천 씬

| Scene | 추천도 | 이유 |
|-------|--------|------|
| Scene 2 (ANCHOR) | ⭐⭐⭐⭐⭐ | 얼굴 고정 최우선 |
| Scene 4 (Blow Out) | ⭐⭐⭐ | 클로즈업 정밀 제어 |
| Scene 5A/5B (Cakes) | ⭐⭐⭐ | 오브젝트 단순 |
| Scene 7 (Selfie) | ⭐⭐⭐ | 왜곡 렌즈 효과 |

---

## 🔑 프롬프트 공식

### 단일 레퍼런스 (ANCHOR 생성)
```
[ANCHOR_IMG.png URL]

Korean::2 boy, 7 years old, black bowl cut 1990s style, single eyelids, 
shy excited smile, looking down at birthday candles, 
warm candlelight under-lighting, nostalgic 1990s home video aesthetic

--iw 2.0 --ar 9:16 --v 7 --style raw 
--no western features, caucasian skin, blonde, blue eyes, sharp digital
```

### 복수 레퍼런스 + Omni Reference
```
[scene.png URL] [ANCHOR.png URL]

**[Image 1: COMPOSITION]** - copy exact layout, positions, clothing colors
**[Image 2: CHARACTER]** - copy Korean boy face for child

Korean::2 family birthday party, triangular composition,
warm tungsten 3200K, 1990s nostalgic atmosphere

--iw 2.0 --oref [ANCHOR.png URL] --cw 50 --ar 9:16 --v 7 --style raw
--no western features, caucasian skin, blonde, modern furniture
```

---

## 🆕 V7 신규 기능

### 1. `--oref` (Omni Reference)
`--cref` 대체. 얼굴과 오브젝트 형태 유지.

```
[scene URL] --oref [anchor URL] --cw 50

→ scene의 구도 + anchor의 얼굴
```

### 2. Text Weights (`::`)
특정 키워드 강조:

```
Korean::2 boy, birthday party
→ "Korean"에 2배 가중치
```

### 3. Draft Mode
빠른 프로토타입 (저비용):
```
--draft
→ 테스트용 빠른 생성
```

---

## 📝 씬별 프롬프트

### Scene 2: ANCHOR ⭐
```
[ANCHOR_IMG.png URL]

Medium close-up, high angle looking down at Korean::2 boy.
7 years old, black bowl cut 1990s Korean style, single eyelids,
shy excited smile, looking down at birthday cake with candles.
Face illuminated from below by warm candlelight (under-lighting).
Blurred Korean parents in background - green blur left, red blur right.
1990s home video aesthetic, Kodak Portra 400 grain, warm tungsten 3200K.

--iw 2.0 --ar 9:16 --v 7 --style raw --stylize 250
--no western features, caucasian skin, blonde, blue eyes, sharp digital, modern
```

### Scene 4: Blow Out
```
**[Image 1: COMPOSITION]** [scene04_blowout.png URL]
**[Image 2: CHARACTER]** [GENERATED_ANCHOR.png URL]

Extreme close-up Korean::2 boy blowing out birthday candles.
Puffed cheeks, squinted eyes, candlelight illuminating face.
Same striped t-shirt as Image 1.
Warm amber glow, soft bokeh background, 1990s film grain.

--iw 2.0 --oref [GENERATED_ANCHOR.png URL] --cw 70 --ar 9:16 --v 7 --style raw
--no western features, caucasian skin, sharp digital
```

### Scene 5A: Past Cake
```
[scene05a_cake_past.png URL]

Overhead view, homemade chocolate birthday cake perfectly centered.
Colorful tall candles, retro wooden table, warm tungsten lighting 3200K.
1990s film grain, nostalgic home video aesthetic.

--iw 2.5 --ar 9:16 --v 7 --style raw
--no modern cake, minimalist design, cold LED lighting, sharp digital
```

### Scene 5B: Present Cake
```
[scene05b_cake_present.png URL]

Overhead view, minimalist white cream cake perfectly centered.
Thin modern candles, sleek black table surface.
Cold LED lighting 6500K, sharp digital 2020s aesthetic.

--iw 2.5 --ar 9:16 --v 7 --style raw
--no chocolate cake, colorful decorations, warm lighting, film grain
```

### Scene 7: Selfie
```
**[Image 1: COMPOSITION]** [scene07_selfie.png URL]

Selfie angle, extreme wide-angle lens distortion.
Korean::2 woman dominating left 2/3 of frame, taking selfie.
Korean::2 birthday man pushed to right background, forced mechanical smile.
Harsh on-camera flash, red-eye effect, oily skin texture.
Pitch black background, cold LED lighting.

--iw 2.0 --ar 9:16 --v 7 --style raw --stylize 400
--no warm lighting, natural light, genuine smile, tungsten
```

---

## ⚠️ 트러블슈팅

| 문제 | 해결 |
|------|------|
| 구도 무시됨 | `--iw 2.5` 또는 `--iw 3.0` |
| 서양인 나옴 | `Korean::2` + `--no caucasian` |
| 얼굴 불일치 | `--oref [anchor]` + `--cw 50-70` |
| 너무 예술적 | `--style raw` + `--stylize 100` |
| 프로토타입 필요 | `--draft` 사용 |

---

## 📊 --iw 가이드

| 값 | 효과 |
|----|------|
| 0.5 | AI 창의성 높음, 레퍼런스 약함 |
| 1.0 | 균형 (기본값) |
| **2.0** | 레퍼런스 강하게 따름 ✅ 권장 |
| 2.5 | 구도 매우 엄격 |
| 3.0 | 거의 복제 수준 |
