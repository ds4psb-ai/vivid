# Birthday Parody 예시

이 폴더는 실제 완성된 프로젝트 예시입니다.

---

## 파일 설명

| 파일 | 설명 |
|------|------|
| `docs/ANALYSIS.md` | Gemini Step 1 출력 예시 (영상 분석 결과) |
| `prompts/IMAGE_PROMPTS.md` | 10-Cut 이미지 프롬프트 (완성본, 284줄) |
| `prompts/MOTION_PROMPTS.md` | 10-Cut 모션 프롬프트 (완성본, 258줄) |

---

## 핵심 포인트

### 1. ALL PEOPLE Rule
모든 인물을 한국인으로 명시 (흐릿한 배경 포함!)

```
Replace **all people** with Korean family:
- Center: Korean boy (use face from Image 2) seated at table
- Standing: Korean mom carrying lit cake
- Background: Korean dad and relatives watching
```

### 2. ANCHOR 시스템
Scene 2를 ANCHOR로 먼저 생성 -> 나머지 씬에서 참조

```
Phase 1: ANCHOR FIRST (Scene 2)
Phase 2: THE 90s (Scene 1, 3~7) - ANCHOR 참조
Phase 3: THE GLITCH (Scene 8) - 전환
Phase 4: THE PRESENT (Scene 9~10) - 다른 캐릭터
```

### 3. 복수 이미지 라벨링
2개 이상 이미지 참조 시 명확한 라벨 사용

```
**[Image 1: COMPOSITION]** [scene.png URL]
**[Image 2: CHARACTER FACE]** [ANCHOR.png URL]

From Image 1: Copy exact composition, character positions, clothing colors.
From Image 2: Copy the Korean boy's face.
```

### 4. Beat Timing
"IMMEDIATELY" 키워드로 즉시 동작 유도

```
IMMEDIATELY in the first 0.3 seconds, the boy takes a visible deep breath in.
His chest rises slightly. Lips pursing, preparing to blow.
Then holds anticipation pose.
```

---

## 사용법

1. 이 예시를 참고하여 `templates/` 파일 채우기
2. 자신의 영상/캐릭터 정보로 대체
3. ANCHOR -> 나머지 씬 순서로 생성

---

## 원본 프로젝트

- **Source**: @kylenutt117 "How memories have changed"
- **Duration**: 17.29s (10 cuts)
- **Concept**: 1990s 따뜻한 생일 -> 2020s 차가운 생일 대비
