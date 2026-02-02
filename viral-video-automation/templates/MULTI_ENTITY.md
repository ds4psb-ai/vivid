# 🔗 Multi-Entity Consistency Guide

> **Purpose**: 캐릭터 외 의상, 소품, 배경까지 일관성 유지
> **Version**: 2026 (Kling Elements / NanoBanana 기반)

---

## 🎯 왜 필요한가?

기존 ANCHOR 시스템:
```
❌ 캐릭터 얼굴만 일관성 유지
❌ 의상, 소품, 배경은 매번 달라짐
```

Multi-Entity 시스템:
```
✅ 캐릭터 + 의상 + 소품 + 배경 모두 일관성
✅ Kling Elements 4슬롯 / NanoBanana 14레퍼런스 활용
```

---

## 📋 Entity 분류

| Entity | 예시 | 레퍼런스 필요? |
|--------|------|---------------|
| **Character** | 아이 얼굴 | ✅ ANCHOR |
| **Costume** | 줄무늬 티셔츠 | ✅ 의상 레퍼런스 |
| **Prop** | 케이크, 촛불 | ⚠️ 상황별 |
| **Background** | 1990s 아파트 | ⚠️ 첫 씬에서 확정 |
| **Lighting** | 3200K 텅스텐 | 프롬프트로 충분 |

---

## 🔧 Kling 2.6 Elements 활용

### 4슬롯 최적 배치

```
Element 1: CHARACTER FACE (ANCHOR.png)
           → 가장 중요, 항상 첫 번째

Element 2: SCENE COMPOSITION (scene_N.png)
           → 구도/포즈 레퍼런스

Element 3: COSTUME (costume_reference.png)  ← 신규!
           → 의상 색상/패턴 고정

Element 4: BACKGROUND (bg_reference.png)    ← 신규!
           → 배경 분위기 고정
```

### 예시 프롬프트

```
**[Element 1: CHARACTER FACE]** anchor.png
**[Element 2: COMPOSITION]** scene03.png
**[Element 3: COSTUME]** striped_shirt.png
**[Element 4: BACKGROUND]** 90s_apartment.png

Korean family birthday scene...
```

---

## 🍌 NanoBanana Pro 멀티 레퍼런스

### 14개 레퍼런스 분배

```
Primary (1-2):
  - Character face anchor
  - Scene composition

Secondary (3-4):
  - Costume reference
  - Prop reference (케이크 등)

Tertiary (5-6):
  - Background/Setting
  - Lighting reference (선택)
```

### 레이블링 규칙

```
**[Image 1: CHARACTER FACE]** anchor.png
**[Image 2: COMPOSITION]** scene.png
**[Image 3: COSTUME - BOY]** striped_tshirt.png
**[Image 4: COSTUME - MOM]** red_sweater.png
**[Image 5: BACKGROUND]** 90s_apartment.png

From Image 1: Copy exact face.
From Image 2: Copy composition and positions.
From Image 3: Copy boy's striped shirt color/pattern.
From Image 4: Copy mom's red sweater exactly.
From Image 5: Copy apartment background atmosphere.
```

---

## 📸 레퍼런스 추출 방법

### 1. 첫 생성물에서 추출

```
Scene 1 생성 후:
1. 캐릭터 얼굴 크롭 → anchor.png
2. 의상 부분 크롭 → costume_boy.png
3. 배경 부분 크롭 → bg_apartment.png
```

### 2. 원본 영상에서 추출

```bash
# 원본에서 의상/배경 레퍼런스 추출
ffmpeg -i source.mp4 -ss 00:00.5 -vframes 1 costume_ref.png
```

---

## ✅ Multi-Entity 체크리스트

생성 전:
- [ ] ANCHOR (캐릭터 얼굴) 준비
- [ ] 의상 레퍼런스 준비 (주요 캐릭터)
- [ ] 배경 레퍼런스 준비 (첫 씬에서 확정)
- [ ] 소품 레퍼런스 (필요시)

씬간 확인:
- [ ] 캐릭터 얼굴 일치
- [ ] 의상 색상/패턴 일치
- [ ] 배경 분위기 일치
- [ ] 소품 연속성 (케이크 등)

---

## 💡 팁

1. **의상은 첫 생성에서 확정** - 나중에 바꾸기 어려움
2. **배경은 간단히** - 복잡한 배경보다 분위기 위주로
3. **소품 일관성** - 같은 케이크가 씬마다 달라지면 눈에 띔
4. **조명은 프롬프트로** - 레퍼런스보다 Kelvin 값 명시가 효과적
