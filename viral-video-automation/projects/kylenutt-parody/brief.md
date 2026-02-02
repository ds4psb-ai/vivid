# 🎬 제작 가이드: "Joy & Isolation" (Nano Banana Pro Edition)

> @kylenutt117 "How memories have changed" 한국판 오마주
> **핵심 변경**: Mixboard → **Nano Banana Pro & Kling 2.6**

---

## 🚀 워크플로우

```
STEP 1. 영상 구조 분석 (Gemini)
        ↓ Nano Banana 시스템 프롬프트 활용
STEP 2. First Keyframe 생성 (Nano Banana)
        ↓ 모든 컷 전환 지점의 첫 프레임
STEP 3. Image-to-Video (Kling 2.6)
        ↓ 일관된 모션 부여
STEP 4. 편집 및 합성
```

---

## 🛠️ 준비물

1. **[nano-banana-system.md](../prompts/nano-banana-system.md)**
   - Gemini에게 부여할 페르소나 및 지침
2. **타겟 영상 파일** (123.mp4)
   - 분석 대상 원본 영상

---

## 📸 Step 1: Gemini에게 지시 (프롬프트 추출)

**Gemini 채팅창에 아래 내용을 순서대로 입력하세요:**

1. **파일 업로드**: `123.mp4` (타겟 영상)
2. **시스템 프롬프트 입력**: `prompts/nano-banana-system.md` 내용 전체 복사/붙여넣기

**그리고 아래 명령을 추가로 입력:**

```
위 시스템 프롬프트를 당신의 페르소나로 설정합니다.
업로드한 영상을 "Joy & Isolation" 한국판으로 재해석하여,
모든 컷 전환(Shot Boundary)마다 첫 키프레임을 추출하고,
나노바나나 프로 최적화 프롬프트를 생성해주세요.

핵심 요구사항:
1. Scene 1 (1998 생일) → Scene 2 (케이크 전환) → Scene 3 (2026 고독) 순서
2. 총 4-5개의 핵심 컷이 예상됩니다. (인트로, 클로즈업, 케이크 2개, 현대 씬)
3. 모든 출력은 9:16 비율(--ar 9:16) 기준입니다.
4. 한국인 남성 캐릭터의 일관성(동일 눈매)을 유지해주세요.
```

---

## 🍌 Step 2: Nano Banana Pro 입력

Gemini가 생성해준 `[FINAL INTEGRATED PROMPT]` 섹션을 복사하여 Nano Banana Pro에 입력합니다.

**팁:**
- `--ar 9:16` 파라미터 확인
- 여러 번 생성하여 가장 완벽한 **First Frame** 하나를 선택 (이것이 영상 퀄리티를 좌우함)

---

## 🎥 Step 3: Kling 2.6 영상 변환

선택된 First Frame을 Kling에 업로드하고, Gemini가 제안한 `[KLING 2.6 VIDEO CONVERSION NOTES]`를 참고하여 모션 설정을 입력합니다.

| 씬 번호 | 모션 강도 | 카메라 | 비고 |
|---------|-----------|--------|------|
| Scene 1 | Moderate | Handheld Shake | 따뜻한 홈비디오 느낌 |
| Scene 2 | Minimal | Static | 케이크 질감 강조, 흔들림 없이 |
| Scene 3 | Low | Dolly Zoom | 정적이고 불안한 고립감 |

---

## 📁 저장 구조

```
projects/kylenutt-parody/
├── nano-banana-prompts.md  ← Gemini가 생성한 결과 저장
├── keyframes/              ← Nano Banana로 만든 최종 이미지들
│   ├── cut01_intro_1998.png
│   ├── cut02_boy_cu.png
│   ├── cut03_cake_1998.png
│   ├── cut04_cake_2026.png
│   └── cut05_isolation_2026.png
└── output/
    └── (Kling 영상 파일들)
```
