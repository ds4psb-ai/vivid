# Image Prompts

> **Project**: {프로젝트명}
> **Tool**: NanoBanana / Midjourney V7
> **핵심 규칙**: ALL PEOPLE -> Korean (배경 인물 포함!)

---

## 예시 먼저 보기

실제 완성된 프로젝트 예시를 참고하세요:
-> `examples/birthday-parody/prompts/IMAGE_PROMPTS.md`

---

## ANCHOR 시스템 (필수 이해)

**ANCHOR = 주인공 얼굴 고정용 첫 이미지**

| 순서 | 무엇을 | 왜 |
|------|--------|-----|
| 1 | ANCHOR 씬 먼저 생성 | 얼굴 확정 |
| 2 | 나머지 씬 생성 시 ANCHOR 참조 | 얼굴 일관성 |

---

## ANCHOR Scene (먼저 생성!)

> **키프레임**: `reference/keyframes/{ANCHOR_FILE}`
> **결과물**: `generated/images/ANCHOR.png`

### NanoBanana (한글)
```
[키프레임 이미지 첨부]

이 이미지의 구도, 조명, 카메라 앵글 그대로 유지.

주인공 교체: [나이]세 한국인 [성별]
- 헤어: [구체적 스타일]
- 눈: 홑꺼풀
- 표정: [구체적 표정]
- 피부: 한국인 피부톤

주의: 배경 인물이 보이면 모두 한국인으로!

금지: 서양인 특징, 금발, 파란 눈
```

### Midjourney V7 (영어)
```
[키프레임 URL]

Exact same composition, lighting, and camera angle.

Main subject: Replace with [AGE]-year-old Korean [GENDER]:
[HAIR], single eyelids, [EXPRESSION]. Korean skin tone.

Note: If any people visible in background, replace with Korean.

--iw 2.0 --ar 9:16 --v 7 --style raw
--no western features, caucasian skin, blonde, blue eyes
```

---

## Scene N: [씬 이름]

> **키프레임**: `reference/keyframes/sceneN.png`
> **ANCHOR 참조**: 필수

### NanoBanana (한글)
```
**Image 1 (구도용)**: [sceneN.png]
**Image 2 (얼굴용)**: [ANCHOR.png]

Image 1에서 복사: 구도, 조명, 옷 색깔
Image 2에서 복사: 주인공 얼굴

모든 인물 교체 (ALL PEOPLE Rule):
- [위치]: 한국인 [역할]
- 배경 흐릿한 인물도 한국인!

금지: [시대별 금지 요소]
```

### Midjourney V7 (영어)
```
**[Image 1: COMPOSITION]** [sceneN.png URL]
**[Image 2: CHARACTER FACE]** [ANCHOR.png URL]

From Image 1: Copy exact composition, character positions, clothing colors.
From Image 2: Copy the Korean [CHARACTER]'s face.

Replace **all people** with Korean:
- [POSITION]: Korean [ROLE]

--iw 2.0 --ar 9:16 --v 7 --style raw --cw 50
--no [ERA_NEGATIVES]
```

---

(씬 반복...)

---

## 시대별 --no 요소

### 1990년대
```
--no western features, caucasian skin, blonde, blue eyes, smartphones, LED lights, modern furniture, sharp digital look
```

### 2020년대
```
--no warm lighting, candles, tungsten, genuine happiness, film grain, retro furniture
```

---

## 체크리스트

- [ ] ANCHOR 씬 먼저 생성
- [ ] 모든 씬에서 ANCHOR.png 참조
- [ ] ALL PEOPLE Rule 준수 (배경 인물 포함)
- [ ] 시대별 --no 요소 확인 (1990s vs 2020s)
