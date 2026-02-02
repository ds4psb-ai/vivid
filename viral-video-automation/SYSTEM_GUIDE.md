# 🎬 VIDEO PARODY SYSTEM v4.0

> 범용 바이럴 영상 패러디 시스템 (Dual Mode + 4-Tool)
> **최종 업데이트**: 2026-02-01

---

## 🔀 MODE SELECTOR

| 상황 | 추천 모드 |
|------|----------|
| 빠른 테스트/프로토타입 | 🚀 **ONE-SHOT** |
| 최종 결과물/퍼블리싱 | 🎯 **TIKI-TAKA** |
| 새 프로젝트 첫 번째 씬 | 🎯 **TIKI-TAKA** |
| 검증된 패턴 반복 | 🚀 **ONE-SHOT** |

### 🚀 ONE-SHOT Mode
- **템플릿**: [GEMINI_ONESHOT.md](templates/GEMINI_ONESHOT.md) + [CLAUDE_REFINEMENT.md](templates/CLAUDE_REFINEMENT.md)
- **왕복**: 2회 / **시간**: ~10분 / **퀄리티**: 85%

### 🎯 TIKI-TAKA Mode  
- **템플릿**: [MODE_TIKITAKA.md](templates/MODE_TIKITAKA.md)
- **왕복**: 5-6회 / **시간**: ~30분 / **퀄리티**: 98%

### 📈 A/B Testing
- **로그**: [AB_TEST_LOG.md](templates/AB_TEST_LOG.md)
- **목적**: TIKI-TAKA 발견 → ONE-SHOT 개선

---

## 🏓 Minimal Tiki-Taka Workflow

```
STEP 1: Gemini ONE-SHOT ────────────────────────────
        영상 + GEMINI_ONESHOT.md 업로드
        → 완벽한 JSON 출력 (도구 추천 포함)
                    ↓
STEP 2: Claude 정제 ────────────────────────────────
        JSON → 도구별 프롬프트 분기
        CLAUDE_REFINEMENT.md 규칙 적용
                    ↓
STEP 3: 생성 + QA ──────────────────────────────────
        QA_CHECKLIST.md로 검증
        --no 파라미터로 미세조정
```

**총 왕복: 2회** (기존 4-5회 → 60% 절감)

---

## 🏗️ 4-Tool Architecture

```
                    ┌─────────────────────────────────────┐
                    │         IMAGE GENERATION            │
                    ├─────────────────┬───────────────────┤
                    │ NanoBanana Pro  │   Midjourney V7   │
                    │ (Gemini 3 Pro)  │   (2025.06 ~)     │
                    ├─────────────────┼───────────────────┤
                    │ ✅ 14개 레퍼런스  │ ✅ --oref 얼굴유지 │
                    │ ✅ 4K 출력       │ ✅ --iw 0-3       │
                    │ ✅ 대화형 편집    │ ✅ Korean::2     │
                    └─────────────────┴───────────────────┘
                                      ↓
                    ┌─────────────────────────────────────┐
                    │         VIDEO GENERATION            │
                    ├─────────────────┬───────────────────┤
                    │    Kling 2.6    │     Veo 3.1       │
                    │  (대사 없음)     │   (대사 있음)      │
                    ├─────────────────┼───────────────────┤
                    │ ✅ Elements 4개  │ ✅ Native Lip-Sync │
                    │ ✅ Motion Control│ ✅ 60초 1080p     │
                    └─────────────────┴───────────────────┘
```

---

## 📁 디렉토리 구조

```
viral-video-automation/
├── SYSTEM_GUIDE.md           # 마스터 가이드 (이 파일)
├── scripts/
│   ├── extract-keyframes.sh  # 정밀 프레임 추출
│   ├── workflow.sh           # 워크플로우 가이드
│   └── new-project.sh        # 새 프로젝트 생성
├── templates/
│   ├── PROMPTS_NANOBANANA.md # NanoBanana Pro 가이드
│   ├── PROMPTS_MIDJOURNEY.md # Midjourney V7 가이드
│   ├── VIDEO_KLING.md        # Kling 2.6 가이드
│   ├── VIDEO_VEO.md          # Veo 3.1 가이드
│   ├── GEMINI_VIDEO_ANALYSIS.md
│   └── PROMPT_TEMPLATE.md
└── projects/{name}/
    ├── keyframes/
    ├── generated/
    └── FINAL_PROMPTS_MINIMAL.md
```

---

## 🚀 Quick Start

```bash
# 1. 새 프로젝트 생성
./scripts/new-project.sh my-parody

# 2. 영상 복사
cp ~/Downloads/original.mp4 projects/my-parody/

# 3. 워크플로우 실행
./scripts/workflow.sh my-parody projects/my-parody/original.mp4
```

---

## 🎯 도구 선택 가이드

### 이미지 생성

| 조건 | 추천 도구 | 이유 |
|------|----------|------|
| 3명 이상 인물 | **NanoBanana Pro** | 14개 레퍼런스 |
| ANCHOR 생성 | **Midjourney V7** | --oref 얼굴 유지 |
| 클로즈업 | **Midjourney V7** | 정밀 제어 |
| 대화형 수정 | **NanoBanana Pro** | 반복 편집 |
| 복잡한 구도 | **NanoBanana Pro** | 복합 레퍼런스 |

### 영상 생성

| 조건 | 추천 도구 | 이유 |
|------|----------|------|
| 대사 없음 | **Kling 2.6** | Elements + Motion |
| 대사 있음 | **Veo 3.1** | Native Lip-Sync |
| 10초 이상 | **Veo 3.1** | 60초 지원 |
| 복잡한 동작 | **Kling 2.6** | Motion Control |

### Frame-to-Video (이미지 → 영상)
- **템플릿**: [FRAME_TO_VIDEO.md](templates/FRAME_TO_VIDEO.md)
- **워크플로우**: Kling Canvas 드래그앤드롭
- **핵심 원칙**: K-PARADOX (5초 생성 → 앞부분만 사용)

---

## 📋 씬별 추천 매핑

| Scene | 이미지 | 영상 | 비고 |
|-------|--------|------|------|
| 1: Arrival | NanoBanana | Kling | 다인물 |
| **2: ANCHOR** | **MJ V7** | - | 얼굴 고정 |
| 3: Clapping | NanoBanana | Kling | 손 동작 |
| 4: Blow Out | MJ V7 | Kling | 클로즈업 |
| 5A/5B: Cakes | MJ V7 | Kling | 오브젝트 |
| 6: Digital | NanoBanana | Kling | 다인물 |
| 7: Selfie | MJ V7 | Kling | 왜곡 렌즈 |

---

## 🔑 핵심 규칙

### 1. ALL PEOPLE Rule
프레임의 **모든 사람** 인종 명시 (흐릿해도!)

### 2. Multi-Reference Labeling
```
**[Image 1: COMPOSITION]** [scene.png]
**[Image 2: CHARACTER FACE]** [anchor.png]
```

### 3. ANCHOR System
1. ANCHOR 먼저 생성 (MJ V7 권장)
2. 결과물을 다른 씬에 레퍼런스로

### 4. Tool-Specific Params
- MJ V7: `--oref`, `--iw 2.0`, `Korean::2`
- Kling: Elements 4개, Motion Control
- Veo: 대사 3-6초, 감정 명시

---

## 📊 Target Ethnicity 프리셋

### Korean Edition
```
Child: Korean boy, black bowl cut (1990s), single eyelids
Adult Male: Korean man, dandy cut, single eyelids
Adult Female: Korean woman, K-beauty makeup, single eyelids
Skin: Korean skin tone
--no: western features, caucasian skin, blonde, blue eyes
```

### Japanese Edition
```
Child: Japanese boy, black hair, almond eyes
Adult: Japanese style, neat appearance
--no: western features, Korean features, K-pop styling
```

---

## 📚 템플릿 참조

| 도구 | 템플릿 |
|------|--------|
| NanoBanana Pro | [PROMPTS_NANOBANANA.md](templates/PROMPTS_NANOBANANA.md) |
| Midjourney V7 | [PROMPTS_MIDJOURNEY.md](templates/PROMPTS_MIDJOURNEY.md) |
| Kling 2.6 | [VIDEO_KLING.md](templates/VIDEO_KLING.md) |
| Veo 3.1 | [VIDEO_VEO.md](templates/VIDEO_VEO.md) |

---

## 📝 Version History

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| v1.0 | 2026-02-01 | 초기 시스템 구축 |
| **v2.0** | **2026-02-01** | **4-Tool 아키텍처 추가** |
