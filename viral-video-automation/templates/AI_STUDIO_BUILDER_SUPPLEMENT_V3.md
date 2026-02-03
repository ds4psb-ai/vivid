# 🔧 AI STUDIO BUILDER 시스템 프롬프트 개선 지시문 V3

> **목적**: 단계별 문제점 지적 + 구체적 개선 방법
> **대상**: Gemini 3 Pro AI Builder
> **사용법**: 이 문서를 시스템 프롬프트에 추가

---

# � 현재 출력 품질 평가

| STEP | 현재 점수 | 목표 점수 | 주요 문제 |
|------|----------|----------|----------|
| STEP 1 | 85/100 | 100 | Scene 번호 표기, ANCHOR 명시 |
| STEP 2 | 75/100 | 100 | 의상 색상 정밀도
| STEP 3 | 70/100 | 100 | 듀얼 앵커 처리, --no 맞춤 |
| STEP 4 | 80/100 | 100 | Visual Rhyme 대조 강화 |
| STEP 5 | 85/100 | 100 | Phase 제목 테마화, 헤더 구조 |

---

# 📍 STEP 1 개선 지시

## 현재 문제점

현재 출력:
```markdown
| Scene | Timecode (Start~End) | Duration | Filename | Description |
| 1 | 00:00.00~00:01.23 | 1.23s | scene1_mom_brings_cake.png | ... |
```

## 개선 필요 사항

### 1-1. Scene 번호에 ANCHOR 표시 누락

**문제**: 어떤 씬이 ANCHOR인지 테이블에서 바로 안 보임

**해결**: Scene 열에 ⭐ 이모지와 **볼드** 추가

```markdown
| Scene | Timecode | Duration | Filename | Description |
| 1 | 00:00.00~00:01.23 | 1.23s | scene1_xxx.png | ... |
| **5 ⭐** | **00:05.13~00:06.26** | **1.13s** | **ANCHOR_boy.png** | **[ANCHOR]** 소년 정면 |
```

### 1-2. 파일명 형식 불일치

**문제**: `scene1_mom_brings_cake.png` (너무 김)

**해결**: `scene[N]_[2단어].png` 형식 통일

```markdown
✅ 올바름: scene01_arrival.png, scene05_anchor.png
❌ 잘못됨: scene1_mom_brings_cake.png (너무 상세함)
```

### 1-3. Phase 열 누락

**문제**: 어떤 씬이 어떤 Phase인지 테이블에서 안 보임

**해결**: Phase 열 추가

```markdown
| Phase | Scene | Timecode | Duration | Filename |
| 2 | 1 | 00:00.00~00:01.23 | 1.23s | scene01_arrival.png |
| **1** | **5 ⭐** | **00:05.13~00:06.26** | **1.13s** | **ANCHOR_IMG.png** |
| 3 | 7 | 00:09.16~00:10.13 | 0.97s | scene07_glitch.png |
| 4 | 8 | 00:10.13~00:12.16 | 2.03s | scene08_phones.png |
```

---

# 📍 STEP 2 개선 지시

## 현재 문제점

현재 출력:
```markdown
*   **주인공 (과거): [지호 - 아역]**
    *   **나이/외모**: 7세 한국 소년. 바가지 머리 혹은 단정한 90년대 스타일.
    *   **의상**: 흰색 바탕에 얇은 빨강/초록/파랑 가로 줄무늬 티셔츠 (레트로 감성).
```

## 개선 필요 사항

### 2-1. 의상 색상 더 정밀하게

**문제**: "빨강/초록/파랑 줄무늬" → 순서, 굵기, 간격 없음

**해결**: 패턴 상세 기술

```markdown
**의상**: 흰색 바탕 티셔츠, **얇은** 가로 줄무늬 (위에서부터: 빨강 → 초록 → 파랑, 각 줄 간격 1cm)
```

📌 **예시 비교**:
```markdown
❌ 현재: 흰색 바탕에 얇은 빨강/초록/파랑 가로 줄무늬 티셔츠
✅ 개선: white t-shirt with thin multi-colored horizontal stripes (red, green, blue from top, 1cm spacing)
```

### 2-2. 캐릭터 ID 누락

**문제**: 프롬프트에서 참조할 캐릭터 식별자 없음

**해결**: ID 필드 추가

```markdown
*   **ID**: `ID_JIHO_CHILD`
*   **주인공 (과거): 지호 - 아역**
    *   **나이**: 7세
    *   **민족**: Korean (single eyelids, black hair)
    *   **의상 코드**: `OUTFIT_RETRO_STRIPES`
```

### 2-3. Visual Rhyme 테이블 세로 비교 부족

**문제**: 대조가 텍스트로만 설명됨

**해결**: 1:1 매칭 테이블

```markdown
## 🪞 Visual Rhyme 1:1 대조

| 요소 | Scene 5 (과거) | Scene 11 (현재) |
|------|---------------|-----------------|
| **나이** | 7세 | 27세 |
| **의상** | 빨강/초록 줄무늬 티 | 네이비 버튼다운 |
| **표정** | 눈 반짝, 순수한 기대 | 텅 빈 눈, 억지 미소 |
| **조명** | 3200K 텅스텐 + 촛불 | 6000K LED 차가움 |
| **배경** | 가족들 노래 | 스마트폰 플래시 |
| **--stylize** | 250 | 400 |
```

---

# 📍 STEP 3 개선 지시

## 현재 문제점

현재 출력에서 ANCHOR 프롬프트:
```markdown
## 📼 Scene 5: The Birthday Boy (00:05.13~00:06.26)
> 💾 **결과물 저장** → `GENERATED_ANCHOR.png`
```

## 개선 필요 사항

### 3-1. 듀얼 ANCHOR 처리 불명확

**문제**: 과거/현재 주인공이 다른데 ANCHOR 2개 필요 언급 없음

**해결**: 명시적 듀얼 앵커 섹션

```markdown
### 🎭 ANCHOR 전략 (듀얼)

이 영상은 **주인공이 성장**하므로 두 개의 ANCHOR가 필요합니다:

| ANCHOR | Scene | 역할 | 사용처 |
|--------|-------|------|--------|
| **ANCHOR_A** | Scene 5 | 7세 지호 (과거) | Scene 1~6 |
| **ANCHOR_B** | Scene 11 | 27세 지호 (현재) | Scene 8~11 |

> ⚠️ **중요**: Scene 7(전환)은 어느 ANCHOR도 사용 안 함
```

### 3-2. --no 파라미터 씬별 맞춤 부족

**문제**: 모든 씬에 비슷한 --no 사용

**해결**: 씬별 상태에 맞는 --no 추가

```markdown
### 씬별 맞춤 --no 가이드

| Scene | 상태 | 추가 --no |
|-------|------|----------|
| 1 | 케이크 이동 중 | `cake on table` |
| 2 | 케이크만 보임 | `faces, people` |
| 5 | 행복한 미소 | `sad face, tears` |
| 7 | 과거→현재 전환 | `candles, warmth` |
| 11 | 공허한 표정 | `smile, happiness, warm light` |
```

### 3-3. Phase 제목이 일반적

**문제**: `PHASE 2: THE 90s` → 테마 있지만 씬 범위 없음

**해결**: Phase 제목에 씬 범위 명시

```markdown
# 🏗️ PHASE 1: ANCHOR FIRST (Scene 5)

# 🏗️ PHASE 2: THE 90s (Scene 1~4, 6)

# 🏗️ PHASE 3: THE GLITCH (Scene 7)

# 🏗️ PHASE 4: THE PRESENT (Scene 8~11)
```

---

# � STEP 4 개선 지시

## 현재 문제점

현재 출력:
```markdown
## 📼 Scene 11: The Empty Stare (00:15.23~00:17.28)
> **⚠️ Note**: Visual Rhyme with Scene 5 (The Birthday Boy).
```

## 개선 필요 사항

### 4-1. Visual Rhyme 강조 부족

**문제**: 주석으로만 언급, 프롬프트 내에 대조 없음

**해결**: 프롬프트 내에 명시적 대조 지시

```markdown
## 📼 Scene 11: The Empty Stare (00:15.23~00:17.28)

> **⚠️ Visual Rhyme**: Scene 5와 1:1 대조
> - 같은 점: 중앙 클로즈업, 케이크 앞 인물
> - 다른 점: 7세→27세, 따뜻함→차가움, 기대→공허

```
[프롬프트 내용]

**Contrast with Scene 5**:
- Scene 5: Warm candlelight, genuine smile, hopeful eyes
- Scene 11: Cold LED, hollow stare, dead eyes

--stylize 400 (Scene 5는 250이었음)
```
```

### 4-2. 성인 지호 ANCHOR 저장 지시 누락

**문제**: Scene 5만 저장 지시 있고, Scene 11용 ANCHOR 없음

**해결**: Scene 8 또는 11에서 성인 ANCHOR 저장

```markdown
## 📼 Scene 8: Smartphone Ritual (00:10.13~00:12.16)

> 💾 **성인 ANCHOR 저장** → `GENERATED_ANCHOR_ADULT.png`
> (Scene 9, 10, 11에서 **[Image 2]**로 재사용)
```

### 4-3. 체크리스트에 Phase 컬럼 위치 불일치

**문제**: Phase가 2, 2, 2, 1, 2, 3, 4 순서 (논리적이지 않음)

**해결**: 시간 순서대로 정렬하되 Phase 별도 표시

```markdown
## ✅ 작업 순서 체크리스트

### Phase 1: ANCHOR 먼저 (필수)
- [ ] Scene 5 (ANCHOR_CHILD) 생성 → 저장
- [ ] Scene 8 (ANCHOR_ADULT) 생성 → 저장

### Phase 2: 과거 씬 (Scene 1~6)
- [ ] Scene 1 (Image 2: ANCHOR_CHILD)
- [ ] Scene 2 (얼굴 없음)
- [ ] Scene 3 (Image 2: ANCHOR_CHILD)
...

### Phase 3: 전환 (Scene 7)
- [ ] Scene 7 (얼굴 없음)

### Phase 4: 현재 씬 (Scene 8~11)
- [ ] Scene 8 (Image 2: ANCHOR_ADULT)
...
```

---

# � STEP 5 개선 지시

## 현재 문제점

현재 출력:
```markdown
# 🎬 VIDEO REPLICATION: FINAL OUTPUT (V3.1)

## 1. 📍 Cut Analysis Table
...
## 2. 🎭 Visual Rhyme Strategy
...
## 3. 🎨 Midjourney Prompts
```

## 개선 필요 사항

### 5-1. 문서 헤더 형식 개선

**문제**: 목표 문서(IMAGE_PROMPTS.md) 형식과 다름

**해결**: 정확한 헤더 형식

```markdown
# 🎬 VIDEO PARODY: 11-CUT BALANCED PROMPT v3.0

> **Core Philosophy**: 레퍼런스 이미지 구도 100% 유지 + **모든 인물** Korean 변경
> **Critical Rule**: 프레임에 등장하는 **모든 사람**의 인종을 명시해야 함 (흐릿해도!)
> **Total Duration**: 17초 (11씬)

---

## ⚙️ 필수 설정

```
Midjourney /settings
├── Model: V6.0 (또는 V7)
├── Style: Raw
└── Stylize: 250 (현대 씬은 400)
```
```

### 5-2. Phase 헤더 이모지 불일치

**문제**: Phase 헤더에 `📼`만 사용

**해결**: Phase별 다른 이모지

```markdown
# 🏗️ PHASE 1: ANCHOR FIRST
## ⭐ Scene 5: The Birthday Boy

# 🏗️ PHASE 2: THE 90s (Scene 1~4, 6)
## 📼 Scene 1: Mom Arrives

# 🏗️ PHASE 3: THE GLITCH (Scene 7)
## 🔄 Scene 7: Cake Transition

# 🏗️ PHASE 4: THE PRESENT (Scene 8~11)
## 📱 Scene 8: Smartphone Wall
```

### 5-3. 최종 체크리스트 형식

**문제**: Phase 열이 중간에 혼재

**해결**: 작업 순서대로 재배열

```markdown
## ✅ 11-Cut 작업 순서

| 순서 | Phase | Scene | 작업 | ANCHOR | 상태 |
|------|-------|-------|------|--------|------|
| 1 | 1 | **5 ⭐** | 아이 얼굴 확정 | SOURCE | ⬜ 먼저! |
| 2 | 1 | **8 ⭐** | 성인 얼굴 확정 | SOURCE | ⬜ |
| 3 | 2 | 1 | 엄마 케이크 등장 | ✅ A | ⬜ |
| 4 | 2 | 2 | 케이크 클로즈업 | - | ⬜ |
...
```

---

# 📋 전체 개선 체크리스트

Builder가 STEP 5 출력 전 자가 점검할 항목:

## STEP 1 체크
- [ ] Scene 열에 **N ⭐** 형식으로 ANCHOR 표시
- [ ] 파일명 `scene[NN]_[action].png` 형식
- [ ] Phase 열 포함
- [ ] Duration 열 포함

## STEP 2 체크
- [ ] 의상 색상 정밀 (순서, 굵기, 간격)
- [ ] 캐릭터 ID 부여
- [ ] Visual Rhyme 1:1 대조 테이블

## STEP 3 체크
- [ ] 듀얼 ANCHOR 전략 명시 (과거/현재)
- [ ] Phase 제목에 씬 범위 포함
- [ ] 씬별 맞춤 --no 가이드
- [ ] `💾 결과물 저장` 지시

## STEP 4 체크
- [ ] Visual Rhyme 대조 프롬프트 내 명시
- [ ] 성인 ANCHOR 저장 지시
- [ ] 체크리스트 작업 순서대로 정렬

## STEP 5 체크
- [ ] 문서 헤더 3줄 철학 포함
- [ ] Phase별 다른 이모지 (⭐, 📼, 🔄, 📱)
- [ ] 최종 체크리스트 작업 순서대로

---

# ⚡ 즉각 적용 규칙 (시스템 프롬프트에 추가)

```
## 출력 형식 필수 규칙

1. **ANCHOR 표시**: Scene 열에 반드시 **N ⭐** + 볼드로 표시
2. **듀얼 ANCHOR**: 성장 영상은 과거/현재 ANCHOR 2개 필요
3. **Phase 제목**: `# 🏗️ PHASE N: [테마명] (Scene X~Y)`
4. **저장 지시**: ANCHOR 씬 끝에 `> 💾 결과물 저장 → GENERATED_ANCHOR.png`
5. **Visual Rhyme**: 대조 씬은 프롬프트 내에 `**Contrast with Scene N**:` 섹션 필수
6. **씬별 --no**: 상태에 맞는 맞춤 네거티브 추가
7. **작업 순서**: 체크리스트는 생성 순서대로 (ANCHOR 먼저)

## Phase 이모지 가이드
- ANCHOR: ⭐
- 과거 씬: 📼
- 전환 씬: 🔄
- 현재 씬: 📱

## Visual Rhyme 대조 프롬프트 템플릿
```
**Contrast with Scene [N]**:
- Scene [N]: [과거 상태]
- Scene [M]: [현재 상태 - 정반대]
```
```

---

# 📊 개선 전/후 비교 요약

| 항목 | Before (현재) | After (개선) |
|------|--------------|-------------|
| ANCHOR 표시 | Scene 5 (텍스트만) | **5 ⭐** + 볼드 |
| Phase 제목 | `PHASE 2: THE 90s` | `PHASE 2: THE 90s (Scene 1~4, 6)` |
| 듀얼 ANCHOR | 없음 | ANCHOR_CHILD + ANCHOR_ADULT |
| Visual Rhyme | ⚠️ Note로만 | 프롬프트 내 Contrast 섹션 |
| --no 맞춤 | 공통만 | 씬별 상태 반영 |
| 체크리스트 | Phase 순서 | 작업 순서 (ANCHOR 먼저) |
| Phase 이모지 | 📼 통일 | ⭐ 📼 🔄 📱 구분 |
