# 🎬 FRAME-TO-VIDEO 범용 가이드

> **용도**: 완성된 이미지 → AI 영상 생성
> **도구**: Kling 2.6 Canvas / Veo 3.1
> **2026 최신 스펙 반영**

---

## 🔄 워크플로우 개요

```
┌─────────────────────────────────────────┐
│ 1. 완성된 씬 이미지 준비                  │
│    (NanoBanana / MJ V7로 생성)           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 2. 도구 선택                             │
│    대사 없음 → Kling 2.6 Canvas          │
│    대사 있음 → Veo 3.1                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 3. Motion Prompt + Settings 적용         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 4. 5초 생성 → 0.5~2.5초만 사용           │
│    (K-PARADOX 원칙)                      │
└─────────────────────────────────────────┘
```

---

## 🎯 도구 선택 가이드

| 조건 | 도구 | 이유 |
|------|------|------|
| 대사 없음 | **Kling 2.6** | Elements + Motion Control |
| 대사 있음 | **Veo 3.1** | Native Lip-Sync |
| 30초 이상 | **Kling 2.6** | One-Shot Continuity |
| 복잡한 물리 (연기, 불) | **Kling 2.6** | Physics Simulation |

---

## 🎛️ Kling 2.6 Canvas 사용법

### STEP 1: 이미지 업로드
```
1. Kling Canvas 모드 접속
2. 완성된 씬 이미지 드래그앤드롭
3. 이미지가 Start Frame으로 설정됨
```

### STEP 2: Motion Score 설정

| 씬 유형 | Motion Score | 예시 |
|---------|-------------|------|
| 빠른 동작 | 6-7 | 걷기, 박수, 달리기 |
| 중간 동작 | 4-5 | 말하기, 고개 끄덕임 |
| 정적 샷 | 2-3 | 케이크, 오브젝트 |

### STEP 3: Camera Control

| 파라미터 | 값 범위 | 용도 |
|----------|--------|------|
| Horizontal | -5 ~ +5 | Left/Right Pan |
| Vertical | -5 ~ +5 | Up/Down Tilt |
| Zoom | -5 ~ +5 | Zoom In/Out |
| Roll | -5 ~ +5 | Handheld 느낌 |

### STEP 4: 프롬프트 구조

```
[동작 설명]. [물리 힌트]. [카메라 힌트]. [분위기].
```

**예시:**
```
The woman walks briskly forward with natural gait.
Her dress sways with each step following physics.
Slow tracking shot following her movement.
Warm, nostalgic atmosphere.
```

---

## 🎤 Veo 3.1 사용법 (대사 있는 씬)

### 프롬프트 구조

```
[캐릭터 설명]. [대사 내용]. [표정/감정]. [카메라].
```

### Beat Map 활용
```
beat 1: glance at camera
beat 2: starts speaking "대사 내용"
beat 3: emotional reaction
beat 4: hold expression
```

### Lip-Sync 최적화
| 팁 | 설명 |
|----|------|
| 파열음 명시 | ㅂ,ㅍ,ㅁ에서 입술 닫힘 |
| 감정 명시 | 대사와 표정 일치 |
| 3-6초 단위 | 클립 길이 적정화 |

---

## ⚠️ K-PARADOX 원칙

### 슬로우모션 방지
```
❌ 피해야 할 것:
- 모호한 동작 설명
- Motion Score 미설정
- "cinematic" 단독 사용

✅ 해야 할 것:
- "real-time speed" 명시
- "not slow motion" 추가
- Motion Score 6+ (동적 씬)
```

### 5초 생성 → 앞부분만 사용
```
WHY: AI 영상은 뒷부분에서 품질 저하
HOW: 0.5초 ~ 2.5초 구간만 잘라서 사용
```

### Negative Prompt 필수 항목
```
[공통]
slow motion, morphing, melting face, distortion, freeze frame

[손/팔]
fused fingers, extra fingers, spaghetti hands, morphing limbs

[불/연기]
frozen fire, backward smoke, fire remaining

[얼굴]
changing features, scary face, morphing face
```

---

## 📊 Motion Score 레퍼런스

| Score | 동작 수준 | 적합한 씬 |
|-------|----------|----------|
| **7** | 매우 빠름 | 박수, 달리기, 점프 |
| **6** | 빠름 | 걷기, 손 흔들기 |
| **5** | 보통 | 고개 끄덕임, 말하기 |
| **4** | 느림 | 미소, 눈 깜빡임 |
| **3** | 최소 | 촛불 흔들림 |
| **2** | 거의 정지 | 정물, 케이크 |

---

## 📋 씬별 프롬프트 템플릿

### 걷기/이동 씬
```
[캐릭터] walks [방향] with natural, real-time gait.
[의상/물체] sways following realistic physics.
[카메라 움직임 설명].
[분위기].
```

### 감정 표현 씬
```
Close-up of [캐릭터] showing [감정].
[미세 동작: 눈, 입, 표정 변화].
Real-time subtle movement.
[조명/분위기].
```

### 오브젝트 중심 씬
```
[오브젝트 설명] in [환경].
[물리 힌트: 불, 연기, 반사 등].
Static camera, minimal movement.
```

---

## ✅ 생성 전 체크리스트

- [ ] 이미지가 Canvas에 로드됨?
- [ ] Motion Score가 씬 유형에 맞음?
- [ ] Camera Control 설정됨?
- [ ] Positive Prompt에 "real-time speed" 포함?
- [ ] Negative Prompt에 "slow motion" 포함?
- [ ] Duration 5초 설정됨?
