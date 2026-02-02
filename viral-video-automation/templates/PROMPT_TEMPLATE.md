# 🎬 BALANCED PROMPT TEMPLATE

> 새 프로젝트용 범용 템플릿 - 복사해서 프로젝트별로 수정

---

## 📋 프로젝트 정보

- **원본 영상**: [영상 URL 또는 파일명]
- **Target Ethnicity**: Korean / Japanese / Indian / etc.
- **분위기**: 과거(따뜻함) vs 현재(차가움)

---

## 🔑 프롬프트 공식

```
[레퍼런스 이미지 URL]

Exact same composition and framing.
Replace **all people** (including blurred background) with [TARGET ETHNICITY] [description].
Keep exact same clothing colors and positions.
Keep [lighting/mood description].

--iw 2.0 --ar 9:16 --v 6.0 --style raw --no western features, caucasian skin, blonde, blue eyes
```

---

# 🏗️ PHASE 1: ANCHOR

## 📼 Scene [N] ⭐ ANCHOR

> **파일**: `keyframes/ANCHOR_IMG.png`
> **타임스탬프**: [MM:SS.CC]
> **목표**: 주인공 얼굴 확정 → 모든 관련 씬에 재사용

```
[ANCHOR_IMG.png URL]

Exact same composition, lighting, and camera angle.

**Main subject**: Replace with [TARGET ETHNICITY] [age] [gender]: [외모 묘사]. [ETHNICITY] skin tone.

**Background**: Replace blurred figures with [TARGET ETHNICITY] - [인물1] ([옷 설명] on [위치]), [인물2] ([옷 설명] on [위치]). Same clothing colors, [ETHNICITY] skin tones even in blur.

Keep [조명 묘사], [시대] aesthetic.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --no western features, caucasian skin, blonde, blue eyes, [시대 반대 키워드]
```

---

# 🏗️ PHASE 2: MAIN SCENES

## 📼 Scene [N]: [씬 이름] ([MM:SS.CC])

> **파일**: `keyframes/[파일명].png`

```
[이미지 URL] [GENERATED_ANCHOR.png URL]

Exact same composition and character positions.

Replace **all people** with [TARGET ETHNICITY] family:
- [위치]: [인물 묘사]
- [위치]: [인물 묘사]

Keep exact same clothing colors and positions.
Keep [조명 묘사], [시대] aesthetic.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 50 --no [제외 키워드]
```

---

# 🏗️ PHASE 3: TRANSITION

## 🔄 Scene [N]: [전환 씬 이름] ([MM:SS.CC])

> **파일**: `keyframes/[파일명].png`
> **참고**: 인물 없음, 오브젝트만

```
[이미지 URL]

Exact same composition - [오브젝트] perfectly centered.
Keep [오브젝트 묘사].
Keep [조명 묘사], [시대] aesthetic.

--iw 2.0 --ar 9:16 --v 6.0 --no [제외 키워드]
```

---

# 🏗️ PHASE 4: CONTRAST SCENES

## 📱 Scene [N]: [현대 씬 이름] 🪞 ([MM:SS.CC])

> **파일**: `keyframes/[파일명].png`
> **Visual Rhyme**: Scene [X]과 같은 구도, 분위기 반전

```
[이미지 URL]

Exact same composition as Scene [X] but [시대] context.

Replace **all people** with [TARGET ETHNICITY]:
- [위치]: [인물 묘사]
- [위치]: [인물 묘사]

Keep exact same positions.
Keep [반전된 조명 묘사], [반전된 분위기].

--iw 2.0 --ar 9:16 --stylize 400 --v 6.0 --style raw --no [제외 키워드]
```

---

# 🛠️ CUSTOMIZATION CHECKLIST

- [ ] Target Ethnicity 결정
- [ ] 씬 개수 확정
- [ ] ANCHOR 씬 선정
- [ ] Visual Rhyme 쌍 식별
- [ ] 타임스탬프 정밀 측정
- [ ] 각 씬별 조명/분위기 분석

---

# 📊 TARGET ETHNICITY PRESETS

### Korean
```
Child: [age]-year-old Korean [gender], black bowl cut, single eyelids
Adult: Korean [gender], [style] hair, single eyelids
Skin: Korean skin tone
--no: western features, caucasian skin, blonde, blue eyes
```

### Japanese
```
Child: [age]-year-old Japanese [gender], black hair, almond eyes
Adult: Japanese [gender], neat [style]
Skin: Japanese skin tone
--no: western features, Korean features
```

### Indian
```
Child: [age]-year-old Indian [gender], dark hair, brown eyes
Adult: Indian [gender], [traditional/modern] style
Skin: South Asian skin tone
--no: western features, East Asian features
```
