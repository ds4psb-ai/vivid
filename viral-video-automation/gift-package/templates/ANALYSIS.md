# Video Analysis

> **Analyzed by**: Gemini
> **Date**: {DATE}

---

## 예시 먼저 보기

실제 완성된 프로젝트 예시를 참고하세요:
→ `examples/birthday-parody/prompts/ANALYSIS.md`

캐릭터 프로필 상세 예시:
→ `docs/PROFILES.md`

---

## Source Video

- **File**: `reference/source.mp4`
- **Duration**: {TOTAL_DURATION}s
- **Resolution**: {RESOLUTION}
- **FPS**: {FPS}

---

## Cut Breakdown

| Scene | Timecode | Duration | Description | ANCHOR |
|-------|----------|----------|-------------|--------|
| 1 | 00:00.00~00:{XX}.{XX} | {X.XX}s | {DESCRIPTION} | ❌ |
| **2 ⭐** | 00:{XX}.{XX}~00:{XX}.{XX} | {X.XX}s | 주인공 단독 정면 | **ANCHOR** |
| 3 | 00:{XX}.{XX}~00:{XX}.{XX} | {X.XX}s | {DESCRIPTION} | ❌ |
| ... | ... | ... | ... | ... |
| N | 00:{XX}.{XX}~00:{XX}.{XX} | {X.XX}s | {DESCRIPTION} | ❌ |

---

## Character Profiles

### ID_MAIN (주인공)
| 속성 | 값 |
|------|-----|
| **Ethnicity** | Korean |
| **Age** | {AGE} |
| **Gender** | {GENDER} |
| **Hair** | {HAIR_STYLE} |
| **Eyes** | single eyelids |
| **Skin** | Korean skin tone |
| **Clothing** | {CLOTHING} |
| **Expression** | {DEFAULT_EXPRESSION} |

### ID_FAMILY / ID_OTHERS
| 역할 | 나이 | 설명 |
|------|------|------|
| {ROLE_1} | {AGE} | Korean {DESCRIPTION} |
| {ROLE_2} | {AGE} | Korean {DESCRIPTION} |
| ... | ... | ... |

---

## Visual Style

| 항목 | 과거 시대 | 현재 시대 |
|------|-----------|-----------|
| **Era** | {ERA_PAST} | {ERA_PRESENT} |
| **Tone** | {PAST_TONE} | {PRESENT_TONE} |
| **Lighting** | {PAST_LIGHTING} | {PRESENT_LIGHTING} |
| **Color Temp** | {PAST_TEMP}K | {PRESENT_TEMP}K |
| **Texture** | {PAST_TEXTURE} | {PRESENT_TEXTURE} |

---

## ANCHOR 추천

- **추천 Cut**: Scene #{N}
- **이유**: 얼굴 선명도, 조명, 표정
- **파일명**: `ANCHOR_IMG.png`

### ANCHOR 선정 기준
1. 주인공 단독 또는 클로즈업
2. 정면 또는 3/4 앵글
3. 조명이 얼굴을 잘 비춤
4. 표정이 자연스러움

---

## Keyframes (for extract-smart.sh)

> 아래 JSON을 `extract-smart.sh` 스크립트에서 사용

<!-- KEYFRAMES_JSON
{
  "video": "{SOURCE_FILE}",
  "total_duration": {TOTAL_DURATION},
  "keyframes": [
    {
      "scene": 1,
      "timestamp": "00:00.{XX}",
      "filename": "scene01_{NAME}",
      "anchor": false,
      "description": "{DESCRIPTION}"
    },
    {
      "scene": 2,
      "timestamp": "00:{XX}.{XX}",
      "filename": "ANCHOR_IMG",
      "anchor": true,
      "description": "주인공 단독 정면"
    },
    {
      "scene": 3,
      "timestamp": "00:{XX}.{XX}",
      "filename": "scene03_{NAME}",
      "anchor": false,
      "description": "{DESCRIPTION}"
    }
  ]
}
-->

### JSON 형식 설명
| 필드 | 타입 | 설명 |
|------|------|------|
| `scene` | number | 씬 번호 |
| `timestamp` | string | 추출 시점 (MM:SS.ms) |
| `filename` | string | 저장 파일명 (확장자 제외) |
| `anchor` | boolean | ANCHOR 이미지 여부 |
| `description` | string | 씬 설명 |

---

## Phase 구분

| Phase | Scene 범위 | 설명 |
|-------|-----------|------|
| 1 | Scene 2 | ANCHOR (먼저 생성) |
| 2 | Scene 1, 3~{N} | 과거 시대 |
| 3 | Scene {GLITCH_N} | 전환 (글리치/모핑) |
| 4 | Scene {PRESENT_START}~{PRESENT_END} | 현재 시대 |

---

## Notes

(분석 노트)

### 특이사항
- [ ] 특수 씬 (박수, 모핑 등) 표시
- [ ] 극단적 짧은 씬 (0.5초 이하) 표시
- [ ] 롱테이크 씬 (3초+) 표시
