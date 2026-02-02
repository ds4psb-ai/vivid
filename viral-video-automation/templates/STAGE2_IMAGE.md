# 🎨 Stage 2: Image Generation Template

> **Purpose**: 씬별 정적 이미지 생성 (티키타카 루프)
> **Tools**: NanoBanana / Midjourney

---

## 🎯 이 단계의 목표

1. 각 씬의 정적 이미지 생성
2. 캐릭터/스타일 일관성 확보
3. 레퍼런스 구도와 100% 매칭
4. critique-refine 반복으로 품질 향상

---

## 📋 생성 순서 (반드시 준수!)

```
1️⃣ ANCHOR 씬 먼저 생성 → anchor.png 저장
2️⃣ 나머지 씬 → anchor.png를 Reference로 사용
```

---

## 🖼️ 이미지 프롬프트 구조

### 기본 구조

```
**[Image 1: COMPOSITION]** [keyframe URL or upload]
**[Image 2: CHARACTER FACE]** [anchor.png] (ANCHOR 이후)

**From Image 1**: Copy exact composition, lighting, camera angle.
**From Image 2**: Copy the character's face exactly.

[상세 설명]

Lighting: [조명 설명]
Mood: [분위기]

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw [50-100] --no [제외할 요소]
```

---

## 🔄 티키타카 루프

### Step 1: 초안 생성 요청

```
User: "Scene 1 이미지 만들어줘"
```

### Step 2: AI 프롬프트 제공

```
AI: [프롬프트 제공]
    "이 프롬프트를 NanoBanana/Midjourney에 붙여넣으세요."
```

### Step 3: 결과물 피드백

```
User: [이미지 첨부]
      "결과물이야. 어때?"
```

### Step 4: AI Critique

```
AI: 📊 Critique:
    ✅ 강점: 구도 일치, 조명 적절
    ❌ 약점: 손 왜곡, 얼굴 불일치
    💡 개선: 손 포즈 단순화, --cw 70으로 조정
    
    [개선된 프롬프트 제공]
```

### Step 5: 반복 또는 확정

```
User: "좋아, 이걸로 확정할게" 또는 "다시 해보자"
```

---

## 📋 이미지 Critique 체크리스트

| 항목 | 체크 |
|------|------|
| 구도가 원본과 일치하는가? | ⬜ |
| 캐릭터 얼굴이 앵커와 일치하는가? | ⬜ |
| 조명 색온도가 적절한가? | ⬜ |
| 인종/외형이 정확한가? | ⬜ |
| 손/팔 등 세부사항이 자연스러운가? | ⬜ |
| 배경 요소가 일치하는가? | ⬜ |
| 의상 색상이 정확한가? | ⬜ |

---

## 💡 흔한 문제 및 해결책

| 문제 | 해결책 |
|------|--------|
| 얼굴 불일치 | `--cw 80-100`으로 올리기 |
| 손 왜곡 | "hands hidden" 또는 단순한 포즈로 수정 |
| 인종 불일치 | Negative에 "western features" 명시 |
| 조명 불일치 | Kelvin 값 명시 (3200K, 6500K 등) |
| 스타일 불일치 | `--style raw` 필수, stylize 낮추기 |

---

## 📁 버전 관리

```bash
# 새 버전 디렉토리 생성
./scripts/version.sh [project] image 01 new

# 결과물 저장
cp ~/Downloads/scene01.png projects/[project]/generated/images/v1/

# 버전 목록 확인
./scripts/version.sh [project] image 01 list

# 최종 버전 선택
./scripts/version.sh [project] image 01 select
```

---

## ➡️ 다음 단계

모든 씬 이미지 확정 후:
1. `generated/images/selected/`에 최종본 확인
2. Stage 3 (영상 생성)로 진행
