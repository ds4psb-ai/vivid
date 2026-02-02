# 🎬 Kling 2.6 영상 생성 가이드

> **최적 용도**: 대사 없는 영상, 액션/동작 장면
> **최신 스펙**: 2026년 1월

---

## 📊 스펙 요약

| 항목 | 값 |
|------|-----|
| Elements | 최대 **4개** 레퍼런스 이미지 |
| Motion Control | 레퍼런스 영상으로 동작 가이드 |
| 물리 시뮬 | Omni One 아키텍처 |
| 오디오 | 효과음/배경음악 자동 생성 |
| 길이 | 기본 10초 (연결 가능) |

---

## 🎯 추천 씬

| Scene | 추천도 | 이유 |
|-------|--------|------|
| Scene 3 (Clapping) | ⭐⭐⭐⭐⭐ | 손 동작 |
| Scene 4 (Blow Out) | ⭐⭐⭐⭐⭐ | 촛불 끄기 |
| Scene 5A/5B (Cakes) | ⭐⭐⭐⭐ | 오브젝트 |
| Scene 1 (Arrival) | ⭐⭐⭐ | 다인물 이동 |
| Scene 6 (Digital) | ⭐⭐⭐ | 스마트폰 들기 |

---

## 🔑 Elements 활용법

### 기본 설정
```
Element 1: 주인공 얼굴 (ANCHOR.png)
Element 2: 씬 구도 (scene.png)
Element 3: (선택) 배경/의상
Element 4: (선택) 소품
```

### 프롬프트 구조
```
[Elements 업로드]

텍스트 프롬프트:
Korean boy blowing out birthday candles, warm tungsten lighting,
puffed cheeks exhaling, candlelight flickering, nostalgic 1990s aesthetic

Motion: [동작 설명]
Camera: [카메라 움직임]
Duration: [초]
```

---

## 🎬 Motion Control 팁

### 효과적인 사용법
1. **화면 비율 맞추기**: 캐릭터 이미지와 레퍼런스 영상 비율 동일 (예: 9:16)
2. **깔끔한 배경**: 단순한 배경의 레퍼런스 영상 사용
3. **명확한 앵글**: 캐릭터 회전이 있으면 3D 스타일 또는 다각도 이미지

---

## 📝 씬별 프롬프트

### Scene 3: The Clapping
```
**Elements:**
1. ANCHOR.png (한국 아이 얼굴)
2. scene03_clapping.png (구도)

**Prompt:**
Korean family clapping for birthday boy, warm tungsten lighting 3200K,
genuine joy and excitement, hands moving rhythmically,
motion blur on clapping hands, 1990s home video aesthetic

**Motion:** 
- Parents: Enthusiastic clapping, leaning forward slightly
- Boy: Looking at cake, shy excited smile
- Hands: Rhythmic applause motion

**Camera:** Static, slight depth shift on boy's face
**Duration:** 5 seconds
**Audio:** Warm ambient room tone, soft clapping sounds
```

### Scene 4: The Blow Out
```
**Elements:**
1. ANCHOR.png (한국 아이 얼굴)
2. scene04_blowout.png (구도)

**Prompt:**
Korean boy blowing out birthday candles, extreme close-up,
puffed cheeks, squinted eyes, candlelight flickering,
warm amber glow on face, soft bokeh background

**Motion:**
- Boy: Deep breath in, puffed cheeks, gentle exhale
- Candles: Flickering, then going out one by one
- Lighting: Gradual dimming as candles extinguish

**Camera:** Static, focus pull from candles to face
**Duration:** 6 seconds
**Audio:** Ambient room, soft "whoosh" of breath
```

### Scene 5A: Past Cake (Overhead)
```
**Elements:**
1. scene05a_cake_past.png (구도)

**Prompt:**
Overhead view of homemade chocolate birthday cake,
colorful tall candles flickering, warm tungsten lighting,
retro wooden table, 1990s nostalgic film grain

**Motion:**
- Candles: Gentle flickering flames
- Smoke: Thin wisps rising

**Camera:** Static overhead, very slight push-in
**Duration:** 4 seconds
**Audio:** Soft ambient, crackling candle flames
```

### Scene 5B: Present Cake (Overhead)
```
**Elements:**
1. scene05b_cake_present.png (구도)

**Prompt:**
Overhead view of minimalist white cream cake,
thin modern candles, cold LED lighting 6500K,
sleek black table, sharp digital 2020s aesthetic

**Motion:**
- Candles: Steady modern flames
- Environment: Clinical stillness

**Camera:** Static overhead
**Duration:** 4 seconds
**Audio:** Sterile silence, maybe phone notification sound
```

### Scene 6: Digital Isolation
```
**Elements:**
1. scene06_lonely.png (구도)
2. adult_korean_man.png (성인 얼굴, 있다면)

**Prompt:**
28 year old Korean man at birthday party, hollow mechanical smile,
friends holding smartphones with LED flashlights,
cold harsh lighting 6500K, pitch black background,
chiaroscuro effect, digital isolation atmosphere

**Motion:**
- Man: Static, fake smile, slight blink
- Friends: Holding phones up, slight arm adjustments
- Phone flashes: Occasional bright flicker

**Camera:** Static, mimicking Scene 3 composition
**Duration:** 6 seconds
**Audio:** Phone shutter sounds, notification pings, no voices
```

---

## 🔗 클립 연결하기

10초 제한 우회법:

```
1. 첫 번째 클립 생성
2. 마지막 프레임 추출
3. 다음 클립의 첫 프레임으로 삽입
4. 이어지는 장면 생성
```

이렇게 하면 길이 제한 없이 연속 내러티브 가능!

---

## ⚠️ 트러블슈팅

| 문제 | 해결 |
|------|------|
| 캐릭터 얼굴 변함 | Element 1에 얼굴 확실히 지정 |
| 동작 부자연스러움 | Motion Control 레퍼런스 영상 사용 |
| 조명 불일치 | 색온도(K) 명시 |
| 물리 왜곡 | Omni One이 자동 보정, 심하면 재생성 |
| 오디오 안맞음 | 후편집 또는 재생성 |

---

## ⏱️ Beat Timing 패턴 (2026 업데이트)

### ❌ 피해야 할 표현

```
IMMEDIATELY, right away, instantly, suddenly
```

### ✅ 권장 표현

```
Beat Timing:
- 0.0–0.5s: Boy inhales, chest rises, lips form "O" shape.
- 0.5–1.0s: Holds inhaled pose, eyes locked on candles.
```

### Creativity 설정 가이드

| Creativity | 용도 |
|------------|------|
| 0.3-0.4 | 얼굴 보존 최우선, 최소 변형 |
| 0.4-0.6 | 안정적 모션, 권장값 |
| 0.6-0.8 | 자연스러운 동작, 약간의 변형 허용 |
| 0.8+ | 창의적 모션, 변형 많음 |

---

## ⚖️ Kling vs Sora 선택 가이드

| 상황 | Kling 2.6 | Sora 2 Pro |
|------|-----------|------------|
| **비용** | ✅ 저렴 (~$1/영상) | ❌ 고가 ($0.30/초) |
| **속도** | ✅ 빠름 (3-8분) | ❌ 느림 (30-90초) |
| **접근성** | ✅ 쉬움 | ⚠️ Pro 구독 필요 |
| **Image-to-Video** | ✅ 강점 | ⚠️ 보통 |
| **물리 정확도** | ⚠️ 보통 | ✅ 최고 |
| **긴 영상 (25초+)** | ❌ 10초 제한 | ✅ 25초 |
| **시네마틱 품질** | ⚠️ 보통 | ✅ 최고 |

### 권장 워크플로우

```
1. Kling으로 빠른 테스트 → 동작/구도 확인
2. 확정된 씬만 Sora 2 Pro로 고품질 생성
3. 비용 절감 + 품질 확보
```
