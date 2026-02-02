# Motion Prompts

> **Project**: {프로젝트명}
> **Tool**: Kling 2.0 / Sora 2 Pro
> **핵심 규칙**: "IMMEDIATELY" 키워드로 즉시 동작 유도

---

## 예시 먼저 보기

실제 완성된 프로젝트 예시를 참고하세요:
-> `examples/birthday-parody/prompts/MOTION_PROMPTS.md`

---

## Global Settings

| 항목 | 값 |
|------|-----|
| **Model** | Kling 2.0 High Quality |
| **Duration** | 5s (trim to use) |
| **Aspect** | 9:16 |

---

## Beat Timing 핵심 규칙

### 사용해야 할 표현
```
- "IMMEDIATELY in the first X seconds"
- "within first second"
- "STARTS from beat one"
- "then holds" / "continuous"
```

### 피해야 할 표현
```
- "slowly"
- "gradually begins"
- "after a moment"
- "eventually"
```

### Beat Timing 형식 (권장)
```
0.0-0.5s: [동작 1]
0.5-1.0s: [동작 2]
1.0-1.5s: [동작 3]
1.5-2.0s: [동작 4]
```

---

## Scene 템플릿

### Scene N: [씬 이름]

> **Use**: 0~Xs (실제 사용 구간)
> **Motion Score**: [1-7]

#### [COPY] Positive
```
[주요 동작 설명]. IMMEDIATELY [핵심 동작] within first second.
[세부 동작]. Then holds [지속 포즈].
[배경/분위기].
```

#### [COPY] Negative
```
delayed action, slow motion, morphing, distortion, frozen, static.
```

| Camera | Motion Score |
|--------|-------------|
| [Static/Zoom/Pan] | **[점수]** |

---

(씬 반복...)

---

## Motion Score 가이드

| 점수 | 설명 | 예시 |
|------|------|------|
| 1-2 | 최소 동작 | 호흡, 미세 떨림 |
| 3-4 | 보통 동작 | 표정 변화, 고개 돌림 |
| 5-6 | 활발한 동작 | 박수, 걷기 |
| 7 | 최대 동작 | 춤, 격렬한 움직임 |

---

## Creativity 설정

| 값 | 설명 |
|----|------|
| 0.3-0.4 | 얼굴 보존 최우선, 최소 변형 |
| 0.4-0.6 | 안정적 모션 (권장) |
| 0.6-0.8 | 자연스러운 동작, 약간의 변형 |
| 0.8+ | 창의적 모션, 변형 많음 |

---

## 체크리스트

- [ ] 5초 생성 -> 각 씬 길이만큼만 컷
- [ ] "IMMEDIATELY" 키워드 포함 확인
- [ ] Negative에 "delayed action" 포함
- [ ] Motion Score에 맞는 동작 강도
- [ ] Creativity 0.4-0.6 (얼굴 보존)
