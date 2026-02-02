# 🎤 Veo 3.1 영상 생성 가이드

> **최적 용도**: 대사 있는 영상, 립싱크 필요한 장면
> **최신 스펙**: 2026년 1월 (Veo 3.1, 2025.10.14 릴리즈)

---

## 📊 스펙 요약

| 항목 | 값 |
|------|-----|
| 길이 | 최대 **60초** |
| 해상도 | **1080p** (4K 지원) |
| Lip-Sync | **Native** (후편집 불필요) |
| 프레임레이트 | **24fps** 권장 |
| 오디오 | 대사 + 효과음 + 배경음악 동시 생성 |

---

## 🎯 추천 씬

| Scene | 추천도 | 사용 조건 |
|-------|--------|----------|
| 생일 축하 노래 | ⭐⭐⭐⭐⭐ | 가족이 노래하는 경우 |
| 대화 장면 | ⭐⭐⭐⭐⭐ | 대사가 있는 경우 |
| 소원 말하기 | ⭐⭐⭐⭐ | 아이가 소원 말하는 경우 |

---

## 🔑 Lip-Sync 핵심 규칙

### 1. 대사는 짧게 (3-6초)
```
✅ "I wish for a puppy!"
❌ "I wish for a puppy and also a new bike and maybe some candy too!"
```

### 2. 감정과 속도 명시
```
[DAD says, calm and warm: "Make a wish, son."]
[BOY says, excited and fast: "I wish for a puppy!"]
```

### 3. 정면 또는 3/4 앵글
```
✅ Frontal view, face clearly visible
✅ Three-quarter angle, lips visible
❌ Profile view (lips obscured)
❌ Back of head
```

---

## 🎬 프롬프트 구조

### 기본 템플릿
```
[레퍼런스 이미지 URL]

**Scene Description:**
Korean family singing happy birthday to 7 year old boy.
Warm tungsten lighting 3200K, 1990s home video aesthetic.

**Dialogue:**
[FAMILY sings, joyful and harmonious: "Happy birthday to you, happy birthday to you..."]
[DAD says, warm and gentle: "Make a wish, son."]
[BOY says, shy and excited: "I wish for a puppy!"]

**Visual Style:**
- Camera: Medium shot, steady
- Lighting: Warm tungsten 3200K, candlelight under-lighting
- Color: Nostalgic warm tones, Kodak Portra 400

**Audio Environment:**
- Room ambiance: Warm home interior
- Background: Soft family murmurs
- Music: None (dialogue focus)
```

---

## 📝 씬별 프롬프트 (대사 있는 경우)

### 생일 축하 노래 장면
```
**Reference:** [ANCHOR.png for boy's face]

**Scene:**
Korean family gathered around birthday cake, warm intimate setting.
7 year old Korean boy (bowl cut, single eyelids) center frame.
Korean parents and relatives forming semi-circle behind.
Birthday cake with flickering candles in foreground.

**Dialogue:**
[FAMILY sings together, sincere and joyful, Korean accent:]
"생일 축하합니다, 생일 축하합니다,
사랑하는 우리 아들, 생일 축하합니다"

**Emotion:** Pure family joy, nostalgic warmth
**Pacing:** Slow, heartfelt
**Camera:** Medium shot, static, focus on boy's face
**Lighting:** Warm tungsten 3200K + candlelight under-lighting
**Duration:** 15 seconds
```

### 소원 말하기 장면
```
**Reference:** [scene04_blowout.png for composition]

**Scene:**
Close-up of Korean boy about to blow out candles.
Eyes reflecting candlelight, shy excited expression.
Moment before the exhale.

**Dialogue:**
[BOY whispers, shy and hopeful:]
"강아지 갖고 싶어요..."

[PAUSE - 2 seconds of anticipation]

[BOY takes deep breath and blows]

**Emotion:** Innocent hope, childhood wonder
**Pacing:** Slow, intimate
**Camera:** Close-up, slight push-in
**Lighting:** Warm candlelight from below
**Duration:** 8 seconds
```

---

## 🇰🇷 한국어 대사 팁

### 자연스러운 표현
```
✅ "생일 축하해!" (자연스러운 반말)
✅ "소원 빌어" (부모가 아이에게)
✅ "감사합니다~" (아이가 예의 바르게)

❌ 번역투 표현 피하기
```

### 감정 표현 명시
```
[엄마 says, 다정하고 따뜻하게:]
[아빠 says, 장난스럽게:]
[아이 says, 수줍게 속삭이며:]
```

---

## ⚠️ Lip-Sync 검증 체크리스트

생성 후 확인:

- [ ] 파열음 (ㅂ, ㅍ, ㅁ)에서 입술 완전히 닫히는가?
- [ ] 음절과 입 모양이 동기화되는가?
- [ ] 표정이 대사 감정과 일치하는가?
- [ ] 24fps 유지되는가?

---

## 🔄 다중 캐릭터 대화

복잡한 장면 워크플로우:

```
1. 각 캐릭터 음성 따로 생성 (음성 합성 도구 활용)
2. 개별 립싱크 장면 생성
3. 편집에서 합성

또는

단일 프롬프트에서 명확한 턴테이킹:
[A says: "..."]
[B responds: "..."]
[A replies: "..."]
```

---

## ⚠️ 트러블슈팅

| 문제 | 해결 |
|------|------|
| 립싱크 안맞음 | 대사 3-6초로 짧게 |
| 발음 부자연 | 음성 톤/속도 명시 |
| 표정 안맞음 | 감정 키워드 추가 |
| 다중 화자 혼란 | 턴테이킹 명확히 |
| 한국어 어색 | 자연스러운 구어체로 |

---

## 📊 Kling 2.6 vs Veo 3.1 선택 가이드

| 조건 | 추천 도구 |
|------|----------|
| 대사 없음 | **Kling 2.6** |
| 대사 있음 | **Veo 3.1** |
| 복잡한 동작 | Kling 2.6 (Motion Control) |
| 립싱크 필요 | **Veo 3.1** |
| 10초 이상 | Veo 3.1 (60초 지원) |
| 빠른 생성 | Kling 2.6 |
