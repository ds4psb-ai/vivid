# 🎬 모션 프롬프트 생성 가이드

> **입력**: IMAGE_PROMPTS.md + 영상 파일
> **출력**: MOTION_PROMPTS.md

---

## Claude에게 복사할 프롬프트

```markdown
이 IMAGE_PROMPTS.md와 영상을 분석해서 MOTION_PROMPTS.md를 만들어줘.

## 규칙:
1. 각 씬마다 Positive + Negative 프롬프트
2. 핵심 동작은 "IMMEDIATELY" / "within first second" 사용
3. Negative에는 반드시 "delayed" 포함
4. Motion Score (1-7) 표시
5. 5초 생성 → 각 씬 길이만큼 컷

## 출력 형식:
### Scene [N]: [제목] ([길이])

#### [📋 COPY] Positive
[동작 설명. IMMEDIATELY 패턴.]

#### [📋 COPY] Negative
[금지 요소. delayed 포함.]

| Camera | Motion Score |
|--------|-------------|
| [Static/Zoom] | **[1-7]** |
```

---

## 타이밍 패턴 참고

| 상황 | 문구 |
|------|------|
| 동작 시작 | `IMMEDIATELY`, `from beat one` |
| 동작 완료 | `by beat one`, `in first 0.3 seconds` |
| 이후 유지 | `then holds`, `continuous` |

---

## Motion Score 기준

| Score | 설명 |
|-------|------|
| 1-2 | 미세 (눈 깜빡임, 호흡) |
| 3-4 | 작은 (미소, 고개 돌림) |
| 5-6 | 중간 (박수, 걷기) |
| 7 | 큰 (격렬한 동작) |
