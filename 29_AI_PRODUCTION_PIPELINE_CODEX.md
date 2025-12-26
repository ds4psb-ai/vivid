# AI Production Pipeline (CODEX v29)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering / Production  
**목표**: AI 영상 프로덕션(스토리보드 → 프롬프트 → 생성 → 후반)을 최신 방식으로 표준화

---

## 0) Scope

- **Production 전용 문서**: 실제 영상 생성(shot/scene)부터 후반까지의 흐름에만 집중한다.
- 데이터화/증거 루프는 `10_PIPELINES_AND_USER_FLOWS.md`와 `27_AUTEUR_PIPELINE_E2E_CODEX.md`를 따른다.
- NotebookLM/Opal 역할 정의는 `10_PIPELINES_AND_USER_FLOWS.md`를 기준으로 한다.

---

## 1) Research Sources (2025-12)

- PJ Ace newsletter (AI Filmmaking)  
  - https://pjace.beehiiv.com/  
  - https://pjace.beehiiv.com/p/don-t-miss-the-veo-3-gold-rush  
  - https://pjace.beehiiv.com/p/make-an-ai-tv-show-in-15-easy-steps  
  - https://pjace.beehiiv.com/p/pj-s-secret-midjourney-prompt
- 인터뷰 (Narrative 중심 강조)  
  - https://www.youtube.com/watch?v=zsyqt_KnYR8

---

## 2) 핵심 인사이트 (PJ Ace 사례 요약)

1. **Narrative-first**: 기술보다 **내러티브/스토리**가 결과 품질을 결정한다.  
2. **Shot-list 중심 설계**: 스토리 → 샷 리스트 → 샷별 프롬프트 생성이 가장 안정적이다.  
3. **Prompt 구조화가 품질**: shot type, lens, film stock, lighting, character, pose, environment(전/중/후경)까지 명시하는 구조가 효과적이다.  
4. **Batch 실행 + 선별**: 프롬프트는 5~10개 묶음으로 실행하고, 첫 결과가 나오면 즉시 선별/수정한다.  
5. **일관성 전략**:  
   - Text-to-Video: **역동성**이 좋지만 캐릭터/룩 일관성 약함  
   - Image-to-Video: **일관성**이 좋지만 카메라 움직임 제한  
   - 캐릭터/보이스 일관성은 Kling/Runway + ElevenLabs 조합이 유리함  
6. **Iteration budget**: 한 샷은 3~4회 내 결과 확보를 목표로 하고, 10회 이상이면 샷 설계를 수정한다.  
7. **후반의 중요성**: 편집/사운드/컬러가 완성도를 결정하며, 최종 품질은 후반에서 결정된다.

---

## 3) AI 프로덕션 분업 구조 (역할)

- **Showrunner/Producer**: 톤/내러티브/승인 기준 결정  
- **Story/Shot Designer**: 비트 분해 + 샷 리스트 작성  
- **Storyboard Operator**: Nano-banana Pro 기반 이미지 + 씬 설명 생성  
- **Prompt Architect**: Shot Contract 기반 프롬프트 규격화  
- **Gen Operator**: Veo/Kling 실행 + 재시도/선별  
- **Continuity QC**: 캐릭터/룩/톤 일관성 점검  
- **Post Lead**: 편집/사운드/음악/컬러

---

## 4) Production Pipeline (Vivid 적용)

```
Idea/Script
  → Beat Sheet
  → Shot List (2~3문장/샷 + 대사)
  → Storyboard (Nano-banana Pro: 이미지 + 씬 설명)
  → Prompt Contract (Shot Contract 기반)
  → Gen Run (Veo 3.1 / Kling)
  → Continuity QC
  → Edit / Sound / Color / Final Export
```

**운영 규칙**
- **Shot 단위 생성**이 기본이다. Scene/Sequence는 Shot을 묶어 구성한다.
- **Batch 실행**: 샷 프롬프트는 5~10개 묶음으로 병렬 실행한다.
- **Iteration budget**: 3~4회 내 후보 확보, 10회 이상이면 샷 설계를 재작성한다.
- **일관성 우선**일 때는 Image-to-Video, **역동성 우선**일 때는 Text-to-Video를 선택한다.

---

## 5) Shot Contract (Spec)

**목적**: 샷 단위 출력의 재현성과 일관성 확보

```json
{
  "shot_id": "shot-03-01",
  "sequence_id": "seq-03",
  "scene_id": "scene-03",
  "shot_type": "medium",
  "aspect_ratio": "2.39:1",
  "lens": "50mm anamorphic",
  "film_stock": "Kodak Vision3 250D",
  "lighting": "golden edge light",
  "time_of_day": "sunset",
  "mood": "controlled ferocity",
  "character": {
    "name": "SHIP CAPTAIN",
    "age": "50s",
    "wardrobe": "faded blue linen tunic",
    "notes": "weathered, beard streaked with grey"
  },
  "pose_motion": "pointing outward while gripping rope",
  "dialogue": "I tried everything. Nothing worked.",
  "environment_layers": {
    "foreground": "rigging line whipping across frame",
    "midground": "captain shouting, tunic folds",
    "background": "mast shadow, pink-red clouds"
  },
  "continuity_tags": ["character:captain", "palette:golden", "location:ship_deck"],
  "seed_image_ref": "nb:storyboard:shot-03-01",
  "duration_sec": 4
}
```

---

## 6) Prompt Contract (Spec)

**목적**: Shot Contract → 모델 프롬프트로의 표준 변환

**템플릿 구조**
```
[Shot Type], [Angle], [Aspect Ratio];
Film stock / color treatment / grain;
Lens + aperture;
Character description + wardrobe;
Pose/motion;
Environment (foreground / midground / background);
Lighting + mood;
Dialogue (if any).
```

**예시 (요약형)**
```
Medium shot, low angle, 2.39:1.
Kodak Vision3 250D, light grain, golden contrast.
50mm anamorphic. SHIP CAPTAIN, weathered, blue linen tunic.
Standing, shouting, pointing while gripping rope.
Foreground: rigging blur. Midground: captain focus. Background: mast shadow, stormy clouds.
Golden edge light, controlled ferocity.
```

---

## 7) Vivid Node Mapping (Production Capsules)

- **Beat Sheet Capsule**: 스토리 비트 구조화  
- **Shot List Capsule**: 비트 → 샷 리스트 변환  
- **Storyboard Capsule**: Nano-banana Pro 이미지 + 씬 설명  
- **Prompt Contract Capsule**: Shot Contract → Prompt 변환  
- **Gen Capsule**: Veo/Kling 실행(샷 단위)  
- **Continuity QC Capsule**: 일관성 검사 + 개선 제안  
- **Post Capsule**: 컷/음향/컬러 체크리스트 산출

**캡슐 규칙**
- 내부 프롬프트/체인은 서버에만 저장  
- 사용자에게는 입력/파라미터만 노출

---

## 8) Data Capture / Evidence

- 모든 생성 결과는 **run_id + prompt_version + model_version**으로 추적  
- **shot_id** 단위로 output_ref, 실패/재시도 로그 저장  
- 최종 승격 샷은 **Pattern Trace + Evidence refs**로 연결  

---

## 9) Legacy → AI Migration

1. 기존 시나리오 → **Beat Sheet**로 분해  
2. 기존 콘티 → **Shot Contract**로 전환  
3. Shot Contract → **Prompt Contract** 자동 생성  
4. 생성 결과를 **DB SoR + Notebook Library**에 기록  
5. 반복 성공 샷은 **Pattern Library**로 승격

---

## 10) Risk / Guardrails

- **IP/저작권**: 원본 자료는 NotebookLM에 직접 업로드하지 않는다.  
- **프롬프트 노출 금지**: 클라이언트에 Raw prompt 전송 금지  
- **일관성 리스크**: 인물/룩이 흔들릴 경우 I2V 기반으로 전환  

---

## 11) 연동 문서

- `10_PIPELINES_AND_USER_FLOWS.md`
- `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`
- `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `27_AUTEUR_PIPELINE_E2E_CODEX.md`
- `28_AUTEUR_TEMPLATE_PIPELINE_DETAIL_CODEX.md`
