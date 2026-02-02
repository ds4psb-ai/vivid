# Motion Prompts

> **Project**: {PROJECT_NAME}
> **Tool**: Kling 2.0 / Sora 2 Pro
> **핵심 규칙**: "IMMEDIATELY" 키워드로 즉시 동작 유도

---

## 예시 먼저 보기

실제 완성된 프로젝트 예시를 참고하세요:
→ `examples/birthday-parody/prompts/MOTION_PROMPTS.md`

---

## ⚙️ GLOBAL SETTINGS

### Kling Canvas 사용법
```
1. 완성된 씬 이미지 드래그앤드롭
2. 아래 프롬프트 복사 입력
3. 5초 생성 → 해당 씬 길이만큼 앞부분만 사용
```

### 기본 설정
| 항목 | 값 |
|------|-----|
| **Model** | Kling 2.0 High Quality |
| **Duration** | 5s (trim to use) |
| **Aspect** | 9:16 |
| **Creativity** | 0.4-0.6 (얼굴 보존) |

---

## 🎯 Beat Timing 핵심 규칙

### ✅ 사용해야 할 표현
```
- "IMMEDIATELY in the first X seconds"
- "within first second"
- "STARTS from beat one"
- "then holds" / "continuous"
- "throughout entire duration"
```

### ❌ 피해야 할 표현
```
- "slowly"
- "gradually begins"
- "after a moment"
- "eventually"
- "smoothly transitions"
```

### Beat Timing 형식 (선택)
```
0.0-0.5s: [동작 1]
0.5-1.0s: [동작 2]
1.0-1.5s: [동작 3]
1.5-2.0s: [동작 4]
```

---

## 📊 10-CUT TIMEFRAME

> 아래 테이블을 ANALYSIS.md 결과로 채우세요

| Scene | 타임코드 | 길이 | 설명 |
|-------|----------|------|------|
| 1 | 00:00.00~00:{XX}.{XX} | {DURATION}s | {DESCRIPTION} |
| 2 | 00:{XX}.{XX}~00:{XX}.{XX} | {DURATION}s | Anchor |
| 3 | 00:{XX}.{XX}~00:{XX}.{XX} | {DURATION}s | {DESCRIPTION} |
| ... | ... | ... | ... |
| {GLITCH_N} | 00:{XX}.{XX}~00:{XX}.{XX} | {DURATION}s | Glitch (전환) |
| ... | ... | ... | ... |
| N | 00:{XX}.{XX}~00:{XX}.{XX} | {DURATION}s | {DESCRIPTION} |

---

# 📼 PHASE 1: ANCHOR

## Scene 2 ⭐ ANCHOR ({DURATION}s)

> **Use**: 0~{DURATION}초

### [📋 COPY] Positive
```
Close-up of a Korean {CHARACTER}. IMMEDIATELY shows {EXPRESSION} in the first half-second. {LIGHT_EFFECT} on face. Then holds this {MOOD} expression, {GAZE_DIRECTION}. Continuous subtle breathing. Sharp focus.
```

### [📋 COPY] Negative
```
morphing face, changing features, delayed reaction, static image.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **3** |

---

# 📼 PHASE 2: {ERA_PAST} (Scene 1, 3~{N})

## Scene 1: {SCENE_NAME} ({DURATION}s)

> **Use**: 0~{DURATION}초

### [📋 COPY] Positive
```
A warm cinematic home video. IMMEDIATELY the Korean {CHARACTER} {ACTION_VERB} within the first second. {OBJECT} {ACTION_RESULT} by beat one. Then {HOLD_ACTION}, holding pose. {OTHER_CHARACTERS}. {FILM_STYLE}, {LIGHTING_STYLE}.
```

### [📋 COPY] Negative
```
slow motion, {WRONG_ACTION}, delayed action, morphing, {WRONG_OBJECT}, distortion.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **{SCORE}** |

---

## Scene 3: {SCENE_NAME} ({DURATION}s)

> **Use**: 0~{DURATION}초
> **⚠️ 참고**: {SPECIAL_NOTE}

### [📋 COPY] Positive
```
{CAMERA_ANGLE} of the Korean family. IMMEDIATELY {CHARACTER_1} {ACTION_1}. {CHARACTER_2} {ACTION_2}. Everyone {GROUP_ACTION}. Natural, {ATMOSPHERE} movement. Then holds this {POSE_DESCRIPTION} pose.
```

### [📋 COPY] Negative
```
{WRONG_ANGLE}, frozen people, delayed movement, morphing, {MISSING_ELEMENT}.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **{SCORE}** |

---

## Scene {N}: {SCENE_NAME} ({DURATION}s)

> **Use**: 0~{DURATION}초

### [📋 COPY] Positive
```
{ACTION_DESCRIPTION}. IMMEDIATELY {MAIN_ACTION} from beat one. {SECONDARY_ACTION}. {VISUAL_DETAIL}. {ATMOSPHERE}.
```

### [📋 COPY] Negative
```
{WRONG_ELEMENTS}, delayed start, {OPPOSITE_ACTION}.
```

| Camera | Motion Score |
|--------|-------------|
| {CAMERA_TYPE} | **{SCORE}** |

---

# 🎬 특수 씬 처리 가이드

## 📸 박수 씬 (고난이도)

> Motion Score 6-7, 손 표현 어려움

### [📋 COPY] Positive
```
Clapping STARTS IMMEDIATELY from beat one. Korean family clapping rhythmically while singing. Mouths open forming words. Hands meet and separate clearly. Natural swaying bodies. {ATMOSPHERE}.
```

### [📋 COPY] Negative
```
fused fingers, extra fingers, delayed start, slow clapping, static mouths, spaghetti hands.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **6-7** |

### ⚠️ 실패 시 대안
```
Motion Brush → 손 영역 Intensity **8**
- 손만 선택하여 강조
- 나머지 영역은 낮은 intensity
```

---

## ⚡ 극단적 짧은 씬 (0.5초 이하)

> 예: Pre-Blowout, Quick Cut

### [📋 COPY] Positive
```
IMMEDIATELY in the first 0.3 seconds, {CHARACTER} {INSTANT_ACTION}. {BODY_DETAIL}. {EXPRESSION}. {LIGHTING}. Held {POSE} pose.
```

### [📋 COPY] Negative
```
{NEXT_ACTION}, {OPPOSITE_STATE}, delayed {ACTION}, morphing.
```

| Camera | Motion Score |
|--------|-------------|
| {CAMERA_TYPE} | **3** |

### ⚠️ 주의
- **5초 생성 후 앞 0.X초만 사용**
- 너무 긴 구간 사용 시 다음 씬과 어색해짐

---

## 🔄 글리치/전환 씬 (모핑)

> 과거 → 현재 시각적 전환

### [📋 COPY] Positive
```
{CAMERA_ANGLE}. STARTS with {PAST_STATE}. {PAST_DETAIL}. Continuous gentle morphing transition to {PRESENT_STATE}. {PRESENT_LIGHTING} gradually replaces {PAST_LIGHTING}.
```

### [📋 COPY] Negative
```
jump cut, instant change, frozen image, no transition.
```

| Camera | Motion Score |
|--------|-------------|
| Static | **2** |

---

## 📱 현재 시대 씬 (디지털 분위기)

### [📋 COPY] Positive
```
{VISUAL_EFFECT} START {ACTION_VERB} IMMEDIATELY from beat one. {SCENE_DESCRIPTION}. The Korean {CHARACTER} {MAIN_ACTION}, but {SUBTLE_MOVEMENT}. {OTHER_CHARACTERS}. {CAMERA_MOVEMENT}.
```

### [📋 COPY] Negative
```
{WRONG_ELEMENTS}, delayed {EFFECT}, {PAST_ATMOSPHERE}, large movements, {FROZEN_PART}.
```

| Camera | Motion Score |
|--------|-------------|
| {CAMERA_TYPE} | **{SCORE}** |

---

## 🎬 롱테이크 씬 (3초+)

> 긴 호흡의 씬, 미세한 변화 중요

### [📋 COPY] Positive
```
{SHOT_TYPE}. IMMEDIATELY {CHARACTER} {INITIAL_ACTION} in the first second. {CAMERA_EFFECT} throughout entire {DURATION} seconds. {ONGOING_ACTION}. {CHARACTER_2} {SECONDARY_ACTION} around second {TIMING}, then holds {FINAL_STATE}. {LIGHTING_STYLE}.
```

### [📋 COPY] Negative
```
{WRONG_SHOT}, smooth motion, static pose, {WRONG_DIRECTION}, {WRONG_ATMOSPHERE}.
```

| Camera | Motion Score |
|--------|-------------|
| {CAMERA_TYPE} | **{SCORE}** |

---

# 📊 Motion Score 가이드

| 점수 | 설명 | 예시 씬 |
|------|------|---------|
| 1-2 | 최소 동작 | 정적 클로즈업, 미세 호흡 |
| 3-4 | 보통 동작 | 표정 변화, 고개 돌림, 대화 |
| 5-6 | 활발한 동작 | 걷기, 박수, 손 흔들기 |
| 7 | 최대 동작 | 춤, 격렬한 움직임, 클라이맥스 |

---

# ⚙️ Creativity 설정 가이드

| 값 | 설명 | 사용 케이스 |
|----|------|-------------|
| 0.3-0.4 | 얼굴 보존 최우선 | ANCHOR, 클로즈업 |
| 0.4-0.6 | 안정적 모션 **(권장)** | 대부분의 씬 |
| 0.6-0.8 | 자연스러운 동작 | 박수, 활발한 씬 |
| 0.8+ | 창의적 모션 | 글리치, 추상적 전환 |

---

# ✅ Motion 체크리스트

## 생성 전
- [ ] 이미지 먼저 완성 확인
- [ ] 씬 길이 확인 (TIMEFRAME 테이블)
- [ ] Motion Score에 맞는 프롬프트

## 생성 시
- [ ] "IMMEDIATELY" 키워드 포함
- [ ] Negative에 "delayed action" 포함
- [ ] Creativity 0.4-0.6 (얼굴 씬)

## 생성 후
- [ ] 5초 생성 → 각 씬 길이만큼만 컷
- [ ] 박수 씬 손 표현 확인 (실패 시 Motion Brush)
- [ ] 극단적 짧은 씬 (0.5초 이하) 정확히 잘랐는지
- [ ] 글리치 씬 모핑 효과 확인
- [ ] 롱테이크 씬 전체 사용 확인

---

# 🛡️ 에러 방지 룰

## 흔한 실패 패턴

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 동작 지연됨 | "gradually", "slowly" 사용 | "IMMEDIATELY" 강조 |
| 손이 녹아내림 | 박수 Motion Score 높음 | Motion Brush 사용 |
| 얼굴 변형 | Creativity 너무 높음 | 0.4-0.5로 낮춤 |
| 정적인 결과 | Negative에 "static" 없음 | Negative에 추가 |
| 전환 끊김 | "jump cut" 발생 | "continuous" 강조 |

## Negative 필수 요소

```
# 모든 씬에 기본 포함
delayed action, morphing, distortion

# 동작 씬 추가
slow motion, frozen, static

# 박수 씬 추가
fused fingers, extra fingers, spaghetti hands

# 전환 씬 추가
jump cut, instant change
```

---

# 📝 변수 참조

| 변수 | 설명 | 예시 |
|------|------|------|
| `{PROJECT_NAME}` | 프로젝트명 | Birthday Glitch |
| `{DURATION}` | 씬 길이 (초) | 1.27 |
| `{CHARACTER}` | 캐릭터 설명 | Korean boy / Korean mother |
| `{ACTION_VERB}` | 핵심 동작 | lowers a cake / claps hands |
| `{EXPRESSION}` | 표정 | shy gentle smile / hollow smile |
| `{LIGHTING_STYLE}` | 조명 | tungsten lighting / LED flash |
| `{ATMOSPHERE}` | 분위기 | warm joyful / cold isolated |
| `{CAMERA_TYPE}` | 카메라 동작 | Static / Zoom In / Pan |
| `{SCORE}` | Motion Score | 3-7 |

---

# 📋 FINAL MOTION CHECKLIST

| Scene | Use 구간 | Motion Score | IMMEDIATELY | 특이사항 | 상태 |
|-------|---------|--------------|-------------|----------|------|
| 1 | 0~{X}s | {SCORE} | ✅ | | ⬜ |
| 2 ⭐ | 0~{X}s | 3 | ✅ | ANCHOR | ⬜ |
| 3 | 0~{X}s | {SCORE} | ✅ | | ⬜ |
| ... | ... | ... | ... | ... | ... |
| {N} (박수) | 0~{X}s | 6-7 | ✅ | Motion Brush 대기 | ⬜ |
| {N} (짧은) | 0~0.Xs | 3 | ✅ | **0.X초만 사용** | ⬜ |
| {N} (글리치) | 0~{X}s | 2 | ✅ | 모핑 확인 | ⬜ |
| {N} (롱테이크) | 0~{X}s | {SCORE} | ✅ | 전체 사용 | ⬜ |
