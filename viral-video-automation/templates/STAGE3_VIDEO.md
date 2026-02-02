# 🎬 Stage 3: Video Generation Template

> **Purpose**: 정적 이미지를 영상으로 변환 (티키타카 루프)
> **Tools**: Kling 2.0 / Sora 2 Pro

---

## 🎯 이 단계의 목표

1. 각 씬의 정적 이미지를 자연스러운 모션으로 변환
2. 타이밍과 동작의 정확성 확보
3. 물리적 자연스러움 검증
4. critique-refine 반복으로 품질 향상

---

## ⚙️ 도구별 권장 설정

### Kling 2.0

| 항목 | 값 |
|------|-----|
| Model | High Quality |
| Duration | 5s (필요한 구간만 사용) |
| Mode | Image-to-Video |
| Creativity | 0.4-0.6 (안정성 우선) |

### Sora 2 Pro

| 항목 | 값 |
|------|-----|
| Mode | Storyboard (Beta) |
| Duration | Scene별 조절 |
| Style | Photorealistic |
| Resolution | 1080p |

---

## 📋 모션 프롬프트 구조 (Beat Timing)

### ❌ 피해야 할 표현

```
IMMEDIATELY, right away, instantly, at once
```

### ✅ 권장 표현 (Beat Timing)

```
Beat Timing:
- 0.0–0.7s: [첫 번째 동작]
- 0.7–1.5s: [두 번째 동작 또는 유지]
```

### 프롬프트 예시

```
Setting: [장소/조명]
Subject: [주체 설명]

Beat Timing:
- 0.0–0.5s: The cake descends toward the table.
- 0.5–1.2s: Hands release, mother holds warm smile.

Camera: [카메라 동작 - 하나만!]
Action: [동작 - 하나만!]
```

---

## 🔄 티키타카 루프

### Step 1: 영상 생성 요청

```
User: "Scene 1 영상 만들어줘"
```

### Step 2: AI 프롬프트 제공

```
AI: [Kling/Sora 프롬프트 제공]
    "이 프롬프트와 이미지를 Kling에 업로드하세요."
```

### Step 3: 결과물 피드백

```
User: [영상 첨부]
      "결과물이야. 어때?"
```

### Step 4: AI Motion Critique

```
AI: 📊 Motion Critique:
    ✅ 강점: 자연스러운 움직임, 타이밍 적절
    ❌ 약점: 손이 왜곡됨, 조명 변화가 급격함
    💡 개선: Creativity 0.4로 낮추기, 동작 단순화
    
    [개선된 프롬프트 제공]
```

### Step 5: 반복 또는 확정

```
User: "좋아, 이걸로 확정할게" 또는 "다시 해보자"
```

---

## 📋 영상 Critique 체크리스트

| 항목 | 체크 |
|------|------|
| 타이밍이 Beat와 일치하는가? | ⬜ |
| 동작이 자연스러운가? | ⬜ |
| 물리 법칙을 준수하는가? (중력, 관성) | ⬜ |
| 캐릭터 얼굴이 일관되는가? | ⬜ |
| 손/팔 등 세부사항이 왜곡되지 않았는가? | ⬜ |
| 조명 변화가 자연스러운가? | ⬜ |
| 시작/끝 프레임이 적절한가? | ⬜ |

---

## 🚨 1 Camera, 1 Action 룰

### ❌ 피해야 할 복합 지시

```
Camera pans left while zooming in and the character walks...
```

### ✅ 권장 단일 지시

```
Camera: Slow tilt down (only)
Action: Cake placement (only)
```

---

## 💡 흔한 문제 및 해결책

| 문제 | 해결책 |
|------|--------|
| 동작이 지연됨 | Beat Timing 명시, "IMMEDIATELY" 제거 |
| 얼굴 왜곡 | Creativity 낮추기 (0.3-0.4) |
| 손 왜곡 | 동작 단순화, 손 숨기기 |
| 물리 어색함 | 구체적 물리 설명 추가 |
| 모션 과잉 | Motion Score 낮추기 |

---

## 📁 버전 관리

```bash
# 새 버전 디렉토리 생성
./scripts/version.sh [project] video 01 new

# Kling 결과물 저장
cp ~/Downloads/scene01.mp4 projects/[project]/generated/videos/kling/

# Sora 결과물 저장
cp ~/Downloads/scene01.mp4 projects/[project]/generated/videos/sora/

# 최종 버전 선택
./scripts/version.sh [project] video 01 select
```

---

## ➡️ 다음 단계

모든 씬 영상 확정 후:
1. `generated/videos/selected/`에 최종본 확인
2. Stage 4 (조립)로 진행
