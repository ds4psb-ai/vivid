# 🎬 GEMINI VIDEO → MIDJOURNEY PROMPT 지시문

> **목표**: 이 영상을 분석하고, 아래 형식으로 **바로 복사 가능한 Midjourney 프롬프트**를 생성해줘

---

## 📋 작업 지시

### 1단계: 영상 분석
이 영상을 씬 단위로 분할해줘:
- 컷 변경점 기준
- 각 씬의 정확한 타임스탬프 (1/100초 단위, 예: 00:01.15)
- Motion Blur 없는 가장 깨끗한 프레임 타임코드

### 2단계: 각 씬 분석
각 씬에서 다음을 파악해줘:
- Shot Type (Wide/Medium/Close-up)
- Camera Angle (Eye-level/High/Low)
- **모든 등장인물** (주인공 + 배경 인물, 흐릿해도!)
- 각 인물의 위치 (9분할 그리드 기준)
- 각 인물의 옷 색깔 (유지해야 함!)
- 조명 (색온도 K값, 방향)
- 분위기 (nostalgic/cold/happy/isolated 등)
- 시대 (1990s/2020s)

### 3단계: Visual Rhyme 식별
- 같은 구도인데 분위기가 반전되는 씬 쌍을 찾아줘
- 예: 과거(따뜻함) ↔ 현재(차가움)

### 4단계: ANCHOR 씬 선정
- 주인공 얼굴이 가장 선명하게 보이는 씬
- 정면 또는 3/4 앵글, 모션 블러 없음

---

## 📤 출력 형식 (이 형식 그대로 따라해줘!)

아래 형식으로 **각 씬마다** 출력해줘:

```
## 📼 Scene [N]: [씬 이름] (타임스탬프)

> **파일**: `keyframes/[파일명].png`
> **타임스탬프**: [MM:SS.CC]

[레퍼런스 이미지 URL 자리]

Exact same composition, lighting, and camera angle.
Replace [원본 인물 설명] with [Korean 버전 설명].
Keep [유지할 조명/분위기 설명].

--iw 2.0 --ar 9:16 --v 6.0 --style raw --no [제외할 요소들]
```

---

## 🎯 프롬프트 작성 규칙

### 1. 3줄 구조 (KEEP/REPLACE/KEEP)
```
1. Exact same [composition/framing/camera angle] ← 구도 유지
2. Replace [원본] with [Korean 버전] ← 인종 변경
3. Keep [lighting/mood/aesthetic] ← 분위기 유지
```

### 2. --no 파라미터 필수 항목
**과거 씬 (1990s)**:
```
--no western features, caucasian, blonde, blue eyes, modern furniture, LED lights, smartphones, cold lighting, sharp digital
```

**현대 씬 (2020s)**:
```
--no western features, warm lighting, candles, tungsten, film grain, genuine happiness
```

### 3. 조명 키워드
- 과거: `warm tungsten 3200K`, `candlelight`, `under-lighting`, `film grain`
- 현재: `cold LED 6500K`, `smartphone flash`, `chiaroscuro`, `sharp digital`

### 4. Korean 스타일링
- 아이: `7-year-old Korean boy, black bowl cut (1990s style), single eyelids`
- 성인 남자: `28-year-old Korean man, dandy cut hair, single eyelids`
- 여자: `Korean woman, single eyelids, K-beauty makeup`

---

## 📝 예시 출력

### ANCHOR 씬 예시:
```
## 📼 Scene 2 ⭐ ANCHOR (00:03.10)

> **파일**: `keyframes/ANCHOR_IMG.png`
> **타임스탬프**: 00:03.10 (아이 정면, 컷 전환 전)

[ANCHOR_IMG.png URL]

Exact same composition, lighting, and camera angle.
Replace the child with a 7-year-old Korean boy: black bowl cut (1990s style), single eyelids, shy excited smile, looking down at birthday candles.
Keep warm candlelight under-lighting and nostalgic 1990s home video aesthetic.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --no western features, caucasian, blonde, blue eyes, modern look, sharp digital
```

### Visual Rhyme 씬 예시:
```
## 📼 Scene 3: The Clapping 🪞 (00:06.05)

> **파일**: `keyframes/scene03_clapping.png`
> **타임스탬프**: 00:06.05 (박수 정점)
> **Visual Rhyme**: Scene 6과 같은 구도, 조명만 반전

[scene03_clapping.png URL] [GENERATED_ANCHOR.png URL]

Exact same composition - triangular framing with child center, parents forming arch behind.
Replace all people with Korean family clapping happily for the Korean birthday boy.
Keep warm tungsten lighting (3200K), motion blur on clapping hands, genuine joy, 1990s home video aesthetic.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no western features, smartphones, cold lighting, sad expressions
```

---

## ⚠️ 주의사항

1. **한 번에 모든 씬** 출력해줘 (ANCHOR 먼저, 나머지 순서대로)
2. **프롬프트는 영어**로 작성 (Midjourney용)
3. **타임스탬프는 정밀하게** (1/100초 단위)
4. **Visual Rhyme 관계** 반드시 표시
5. **ANCHOR 씬**은 ⭐ 표시

---

## ✅ 체크리스트

출력 결과에 다음이 포함되어야 해:

- [ ] ANCHOR 씬 선정 및 ⭐ 표시
- [ ] 모든 씬의 정밀 타임스탬프
- [ ] 모든 씬의 Midjourney 프롬프트
- [ ] Visual Rhyme 관계 표시 (🪞)
- [ ] --no 파라미터 (과거/현재 구분)
- [ ] Korean 스타일링 적용

---

이제 영상을 분석하고 위 형식으로 출력해줘!
