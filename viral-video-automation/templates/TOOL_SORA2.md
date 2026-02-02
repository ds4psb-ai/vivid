# 🎬 Sora 2 Pro Unified Guide

> **Platform**: OpenAI Sora 2 Pro
> **Version**: 2026
> **용도**: 시네마틱 AI 영상 생성

---

## 🎯 Sora 2 Pro 특징

| 특징 | 값 |
|------|-----|
| **최대 길이** | 25초 (Pro는 60초까지) |
| **해상도** | 1080p / 4K |
| **오디오** | 네이티브 싱크 지원 |
| **물리** | 최고 수준 시뮬레이션 |
| **일관성** | Cameos 기능으로 캐릭터 유지 |
| **모드** | Storyboard (다중 씬 지원) |

---

## 🎨 3가지 스타일 옵션

### Option 1: Realistic (실사)

```
Style: Photorealistic, 1990s home video aesthetic.
Film: 35mm fine grain, subtle halation on practicals.
Grade: Warm tungsten (3200K), cream highlights.
Motion: 24fps, natural handheld shake.
```

**용도**: 홈 비디오 패러디, 다큐멘터리 스타일

---

### Option 2: Theatrical (극장판 애니)

```
Style: Theatrical hand-drawn animation, early 2000s aesthetic.
Visual: Soft pastel colors, visible brush strokes.
Grade: Warm amber, cream highlights, soft shadows.
Camera: Slow, contemplative movements.
```

**용도**: 감성적 콘텐츠, 향수 자극

---

### Option 3: OTT (Netflix 스타일)

```
Style: Modern cinematic anime, Netflix/Apple aesthetic.
Visual: High contrast, neon accents, sharp lines.
Grade: Past (warm coral) → Present (cold cyan).
Camera: Dynamic, aggressive movements.
```

**용도**: 바이럴 소셜 콘텐츠, 임팩트 영상

---

## 📋 프롬프트 구조 (Beat Timing)

### ❌ 피해야 할 표현

```
IMMEDIATELY, right away, instantly, at once, suddenly
```

### ✅ 권장 표현

```
Beat Timing:
- 0.0–0.7s: [첫 번째 동작]
- 0.7–1.5s: [두 번째 동작 또는 유지]
```

### 프롬프트 예시

```
Reference: [Attach scene01.png]
Continue from this exact frame composition.

Setting: Small 1990s Korean apartment dining room, evening.
Lighting: Warm tungsten overhead (3200K), candle flames as fill.
Film: 35mm fine grain, subtle halation on candle flames.

Subjects:
- Korean mother (30s, red sweater) holds lit birthday cake
- Korean boy (7, black bowl-cut) seated at table, eager expression

Beat Timing:
- 0.0–0.7s: Mother's hands move down, cake descends toward table.
- 0.7–1.5s: Cake touches table. Mother releases hands, holds smile.

Camera: Slow tilt down tracking the cake. No other movement.
Action: One action only (cake placement).
```

---

## 🎬 Storyboard 모드 가이드

### 최소 씬 길이 룰

```
❌ 0.4초, 0.78초 → 실패율 높음
✅ 최소 1.0초 이상 → 안정적
```

### 씬 카드 구조

```
### Scene [N]: [이름]
| Duration | **Xs** | Reference | [image.png] |

**[📋 COPY TO SORA]**
Setting: ...
Lighting: ...
Subjects: ...

Beat Timing:
- 0.0–Xs: ...
- X–end: ...

Camera: [1개만]
Action: [1개만]
```

---

## 🚫 Global Negative Prompt

### 모든 씬에 적용

```
Avoid: Western facial features, AI-looking faces, distorted eyes,
extra limbs, warped hands, melted textures, heavy blur,
oversharpened skin, morphing faces, teleport artifacts.
```

---

## 📸 이미지 앵커링

### 권장 씬

| 타입 | 씬 |
|------|-----|
| 캐릭터 소개 | Scene 1, 2, 3 |
| 감정 전환점 | Scene 8, 9 |
| 클라이맥스 | Scene 10 |

### 사용법

```
Reference: [Attach scene01.png]
Continue from this exact frame composition.

또는

This is the character's face reference. 
Maintain this exact face throughout.
```

---

## 🔧 1 Camera, 1 Action 룰

### ❌ 복합 지시

```
Camera pans left while zooming in and the character walks...
```

### ✅ 단일 지시

```
Camera: Slow tilt down (only)
Action: Cake placement (only)
```

---

## ⚖️ Sora vs Kling 선택

| 상황 | 선택 |
|------|------|
| 물리 정확도 최우선 | **Sora 2 Pro** |
| 긴 영상 (15-25초) | **Sora 2 Pro** |
| 복잡한 상호작용 | **Sora 2 Pro** |
| 시네마틱 품질 | **Sora 2 Pro** |
| 빠른 반복/테스트 | **Kling 2.0** |
| 비용 효율 | **Kling 2.0** |
| 소셜 미디어용 | **Kling 2.0** |
| Image-to-Video | **Kling 2.0** |

---

## ⏱️ 권장 타이밍 구조

| 씬 타입 | 권장 길이 |
|---------|----------|
| 정서 세팅 | 1.5-2.0초 |
| 액션/이벤트 | 2.0-2.5초 |
| 전환 (글리치) | 1.5-2.0초 |
| 클라이맥스 | 3.0-4.0초 |

---

## 🚨 흔한 문제 & 해결

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 동작 지연 | "IMMEDIATELY" 사용 | Beat Timing으로 교체 |
| 얼굴 왜곡 | 이미지 앵커 없음 | Reference 이미지 첨부 |
| 물리 어색 | 설명 부족 | 구체적 물리 묘사 추가 |
| 복잡한 결과 | 다중 동작 | 1 Camera 1 Action 적용 |
| 짧은 씬 실패 | 0.8초 미만 | 최소 1.0초로 확장 |

---

## ✅ 체크리스트

생성 전:
- [ ] 스타일 선택 (Realistic/Theatrical/OTT)
- [ ] Reference 이미지 준비
- [ ] 최소 1.0초 이상 확인
- [ ] Beat Timing 적용
- [ ] 1 Camera 1 Action 확인
- [ ] Global Negative 적용

생성 후:
- [ ] CRITIQUE_VIDEO.md로 품질 평가
- [ ] 버전 폴더에 저장
- [ ] 확정 시 selected/ 폴더로 이동
