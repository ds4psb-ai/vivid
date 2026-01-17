# App 2.2: 스토리보드 스케치 (Storyboard Sketcher) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: Visual

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치 (신규 생성 필요)
file_path = "backend/app/routers/dimension/storyboard.py"

# 예상 엔드포인트
endpoints = [
    "POST /dimension/storyboard/sketch",
    "POST /dimension/storyboard/sketch/stream",
    "POST /dimension/storyboard/refine",
    "POST /dimension/storyboard/export",
]

# 현재 기능 (미구현)
current_features = []

# 목표 기능
target_features = [
    "씬별 스토리보드 컷 생성",
    "카메라 앵글/무브먼트 시각화",
    "Flux/SDXL 기반 이미지 생성",
    "샷 연결성 분석",
    "스토리보드 PDF 내보내기",
]
```

### 1.2 현재 한계점 (신규 앱 설계 기준)

| 도전과제 | 영향 | 해결 방향 |
|----------|------|----------|
| 씬 텍스트 → 시각화 변환 | 정확한 묘사 필요 | 구조화된 씬 파싱 |
| 캐릭터 일관성 | 같은 캐릭터가 다르게 보임 | 캐릭터 시트 + IP Adapter |
| 카메라 워크 표현 | 평면 이미지의 한계 | 카메라 가이드 오버레이 |
| 샷 간 연속성 | 독립적 생성의 단점 | 컨텍스트 연결 프롬프트 |

---

## 2. 핵심 연구 주제

### 2.1 스토리보드 기법 연구

**연구 질문**:
- 전문 스토리보드 아티스트의 작업 방식은?
- 스토리보드 컷의 필수 구성 요소는?
- 샷 연결 표기법(화살표, 카메라 노트)은?

**조사 대상**:
1. 스토리보드 제작 가이드 (Disney, Pixar 등)
2. 영화/애니메이션 스토리보드 분석
3. 스토리보드 소프트웨어 (Storyboarder, FrameForge)

### 2.2 AI 이미지 생성 일관성 연구

**연구 질문**:
- 캐릭터 일관성 유지 기법은? (IP Adapter, LoRA 등)
- 배경 일관성 유지 기법은?
- 스타일 통일 방법은?

**조사 대상**:
1. IP Adapter v2 / InstantID 연구
2. StoryMem (2025) 캐릭터 일관성 기법
3. Flux 1.1 Pro 컨시스턴시 기능

### 2.3 카메라 워크 시각화 연구

**연구 질문**:
- 정적 이미지에서 카메라 무브먼트 표현법은?
- 샷 전환 시각화 방법은?
- 동작선(Action Line) 표기법은?

**조사 대상**:
1. 애니메이션 레이아웃 기법
2. 스토리보드 화살표/동작 표기법
3. 카메라 무브먼트 아이콘 시스템

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: storyboard_composition_rules

```yaml
id: storyboard_composition_rules
description: "스토리보드 구성 규칙 및 레이아웃 가이드"
source: "스토리보드 제작 가이드, 영화학"
size: ~50 documents

schema:
  rule_id:
    type: string
    example: "180_degree_rule"

  rule_name:
    type: string
    example: "180도 법칙"

  category:
    type: string
    enum: ["continuity", "composition", "camera", "timing", "emotion"]

  description:
    type: string

  visual_example:
    type: object
    schema:
      diagram_type: string  # "overhead", "sideview", "comparison"
      key_elements: list[string]

  violation_effect:
    type: string
    description: "규칙 위반 시 효과"

  intentional_violation:
    type: object
    description: "의도적 위반 사례"
    schema:
      purpose: string
      example_films: list[string]

  application_context:
    type: list[string]
    description: "적용되는 씬 유형"

# 예시 데이터
storyboard_rules:
  - rule_id: "180_degree_rule"
    rule_name: "180도 법칙"
    category: "continuity"
    description: "두 캐릭터 사이의 가상선(축)을 기준으로 카메라가 같은 쪽에 위치해야 함"
    visual_example:
      diagram_type: "overhead"
      key_elements: ["imaginary_line", "camera_positions", "character_eyelines"]
    violation_effect: "관객의 공간 혼란, 캐릭터 시선 방향 오류"
    intentional_violation:
      purpose: "심리적 혼란, 현실 왜곡 표현"
      example_films: ["The Shining", "Requiem for a Dream"]

  - rule_id: "rule_of_thirds"
    rule_name: "삼분할 법칙"
    category: "composition"
    description: "프레임을 9등분하여 교차점에 중요 요소 배치"
    visual_example:
      diagram_type: "grid_overlay"
      key_elements: ["grid_lines", "power_points", "subject_placement"]

  - rule_id: "headroom"
    rule_name: "헤드룸"
    category: "composition"
    description: "인물 머리 위 적절한 공간 확보"
    violation_effect: "답답함, 불편함"
    application_context: ["close_up", "medium_shot", "interview"]
```

### 3.2 데이터셋: shot_type_visual_guide

```yaml
id: shot_type_visual_guide
description: "샷 타입별 시각적 가이드 및 프롬프트 템플릿"
source: "영화 촬영 교본, 스토리보드 샘플"
size: ~40 documents

schema:
  shot_type_id:
    type: string
    example: "extreme_wide_shot"

  shot_name_ko:
    type: string
    example: "익스트림 와이드 샷"

  shot_name_en:
    type: string
    example: "Extreme Wide Shot (EWS)"

  abbreviation:
    type: string
    example: "EWS"

  description:
    type: string

  frame_coverage:
    type: object
    schema:
      subject_size: string  # "full_body", "waist_up", "face_only"
      environment_visibility: float  # 0-1
      typical_ratio: string  # "16:9", "2.39:1"

  emotional_effect:
    type: list[string]

  common_uses:
    type: list[string]

  composition_tips:
    type: list[string]

  camera_height:
    type: string
    enum: ["eye_level", "low_angle", "high_angle", "birds_eye", "worms_eye"]

  flux_prompt_template:
    type: string
    description: "Flux/SDXL용 프롬프트 템플릿"

  negative_prompt:
    type: string

  example_films:
    type: list[object]
    schema:
      film: string
      scene_description: string
      director: string

# 예시 데이터
shot_types:
  - shot_type_id: "extreme_close_up"
    shot_name_ko: "익스트림 클로즈업"
    shot_name_en: "Extreme Close-Up (ECU)"
    abbreviation: "ECU"
    description: "얼굴의 일부(눈, 입, 손)만 프레임에 가득 채움"
    frame_coverage:
      subject_size: "body_part_only"
      environment_visibility: 0.0
      typical_ratio: "16:9"
    emotional_effect: ["intimacy", "tension", "revelation", "detail_emphasis"]
    common_uses: ["emotional_peak", "detail_shot", "thriller_tension"]
    composition_tips:
      - "피사체가 프레임 85% 이상 차지"
      - "얕은 심도로 배경 완전 흐림"
      - "미세한 움직임도 강조됨"
    flux_prompt_template: "extreme close-up shot of {subject}, filling the frame, shallow depth of field, cinematic lighting, {style}"
    negative_prompt: "full body, wide shot, background visible, multiple subjects"

  - shot_type_id: "over_the_shoulder"
    shot_name_ko: "오버 더 숄더"
    shot_name_en: "Over-the-Shoulder (OTS)"
    abbreviation: "OTS"
    description: "한 인물의 어깨 너머로 다른 인물을 촬영"
    frame_coverage:
      subject_size: "head_and_shoulders"
      environment_visibility: 0.2
    emotional_effect: ["connection", "dialogue_focus", "perspective"]
    common_uses: ["conversation", "confrontation", "interview"]
    composition_tips:
      - "전면 인물이 프레임 1/3 차지"
      - "후면 인물 어깨/머리 일부 포함"
      - "180도 법칙 준수"
    flux_prompt_template: "over-the-shoulder shot, {foreground_character} shoulder and back visible in foreground, {main_character} facing camera in focus, dialogue scene, {style}"
```

### 3.3 데이터셋: camera_movement_notation

```yaml
id: camera_movement_notation
description: "카메라 무브먼트 표기법 및 시각화 가이드"
source: "촬영 교본, 스토리보드 표기 체계"
size: ~30 documents

schema:
  movement_id:
    type: string
    example: "dolly_in"

  movement_name_ko:
    type: string
    example: "달리 인"

  movement_name_en:
    type: string
    example: "Dolly In"

  description:
    type: string

  visual_notation:
    type: object
    schema:
      arrow_type: string  # "solid", "dashed", "curved"
      arrow_direction: string
      icon: string  # 표기 아이콘
      color_code: string

  storyboard_representation:
    type: object
    schema:
      start_frame: string  # 시작 프레임 상태
      end_frame: string    # 종료 프레임 상태
      overlay_elements: list[string]  # 화살표, 텍스트 등

  emotional_purpose:
    type: list[string]

  technical_requirements:
    type: list[string]

  ai_video_compatibility:
    type: object
    schema:
      veo: float  # 0-1 지원도
      kling: float
      sora: float
      prompt_hint: string

# 예시 데이터
camera_movements:
  - movement_id: "dolly_in"
    movement_name_ko: "달리 인"
    movement_name_en: "Dolly In"
    description: "카메라가 피사체를 향해 물리적으로 전진"
    visual_notation:
      arrow_type: "solid"
      arrow_direction: "toward_subject"
      icon: "→●"
      color_code: "#4CAF50"  # 녹색
    storyboard_representation:
      start_frame: "medium_shot"
      end_frame: "close_up"
      overlay_elements: ["forward_arrow", "movement_path", "end_frame_thumbnail"]
    emotional_purpose: ["intimacy_increase", "revelation", "tension_build"]
    ai_video_compatibility:
      veo: 0.9
      kling: 0.7
      sora: 0.85
      prompt_hint: "camera slowly moving forward toward {subject}"

  - movement_id: "pan_left"
    movement_name_ko: "팬 레프트"
    movement_name_en: "Pan Left"
    description: "카메라가 고정된 위치에서 왼쪽으로 회전"
    visual_notation:
      arrow_type: "curved"
      arrow_direction: "left"
      icon: "↶"
      color_code: "#2196F3"  # 파란색
```

### 3.4 데이터셋: character_consistency_techniques

```yaml
id: character_consistency_techniques
description: "AI 이미지 생성 시 캐릭터 일관성 유지 기법"
source: "Flux/SDXL 가이드, StoryMem 논문"
size: ~20 documents

schema:
  technique_id:
    type: string
    example: "ip_adapter_v2"

  technique_name:
    type: string
    example: "IP Adapter v2"

  description:
    type: string

  requirements:
    type: list[string]
    description: "필요 자원/입력"

  implementation:
    type: object
    schema:
      platform: string  # "comfyui", "a1111", "api"
      parameters: dict
      workflow_notes: string

  effectiveness:
    type: object
    schema:
      face_consistency: float
      clothing_consistency: float
      pose_flexibility: float

  limitations:
    type: list[string]

  best_practices:
    type: list[string]

  integration_guide:
    type: string
    description: "Vivid 시스템 통합 방법"

# 예시 데이터
consistency_techniques:
  - technique_id: "character_sheet_reference"
    technique_name: "캐릭터 시트 레퍼런스"
    description: "캐릭터 정면/측면/후면 시트를 생성하고 모든 샷에 참조"
    requirements:
      - "초기 캐릭터 디자인 확정"
      - "5각도 캐릭터 시트 생성"
      - "주요 표정/포즈 변형 시트"
    implementation:
      platform: "flux_pro"
      parameters:
        character_reference: "강한 가중치"
        consistency_mode: "high"
      workflow_notes: "첫 번째 생성에서 캐릭터 확립 후 시트 생성"
    effectiveness:
      face_consistency: 0.85
      clothing_consistency: 0.90
      pose_flexibility: 0.70
    best_practices:
      - "캐릭터 시트는 동일 스타일로 생성"
      - "주요 캐릭터 특징을 프롬프트에 명시"
      - "3-5개 참조 이미지 조합"

  - technique_id: "storymem_approach"
    technique_name: "StoryMem 접근법"
    description: "이야기 맥락을 활용한 캐릭터 메모리 시스템 (2025 논문)"
    requirements:
      - "캐릭터 프로필 데이터"
      - "이전 샷 컨텍스트"
      - "장면 설명"
    effectiveness:
      face_consistency: 0.92
      clothing_consistency: 0.88
      pose_flexibility: 0.85
    integration_guide: "각 샷 생성 시 이전 3개 샷의 캐릭터 정보를 컨텍스트로 전달"
```

### 3.5 데이터셋: storyboard_layout_templates

```yaml
id: storyboard_layout_templates
description: "스토리보드 레이아웃 및 내보내기 템플릿"
source: "업계 표준 스토리보드 형식"
size: ~15 documents

schema:
  template_id:
    type: string
    example: "standard_6panel"

  template_name:
    type: string
    example: "표준 6패널 레이아웃"

  layout:
    type: object
    schema:
      panels_per_page: int
      panel_aspect_ratio: string
      orientation: string  # "portrait", "landscape"
      margin_mm: int

  panel_elements:
    type: list[object]
    schema:
      element: string  # "image", "shot_number", "description", "dialogue", "camera_note"
      position: string
      font_size: int

  export_formats:
    type: list[string]
    example: ["pdf", "png_sequence", "animatic_video"]

  use_case:
    type: string

# 예시 템플릿
layout_templates:
  - template_id: "standard_6panel"
    template_name: "표준 6패널 레이아웃"
    layout:
      panels_per_page: 6
      panel_aspect_ratio: "16:9"
      orientation: "portrait"
      margin_mm: 10
    panel_elements:
      - element: "shot_number"
        position: "top_left"
        font_size: 10
      - element: "image"
        position: "center"
        size: "80%"
      - element: "description"
        position: "bottom"
        font_size: 9
      - element: "camera_note"
        position: "bottom_right"
        font_size: 8
    export_formats: ["pdf", "png_sequence"]
    use_case: "일반 프로덕션, 프리젠테이션"

  - template_id: "animatic_timeline"
    template_name: "애니매틱 타임라인"
    layout:
      panels_per_page: 1
      panel_aspect_ratio: "16:9"
      orientation: "landscape"
    panel_elements:
      - element: "image"
        position: "full"
      - element: "timecode"
        position: "top_right"
      - element: "audio_waveform"
        position: "bottom"
    export_formats: ["video_animatic", "premiere_xml"]
    use_case: "편집 프리뷰, 타이밍 확인"
```

---

## 4. 기능 고도화 설계

### 4.1 분석 파이프라인

```yaml
storyboard_generation_pipeline:
  stage_1_scene_parsing:
    purpose: "씬/샷 리스트 파싱 및 구조화"
    inputs:
      - scenario
      - shot_list (from story architect)
    outputs:
      - structured_shots: list[StructuredShot]
    logic:
      - "각 샷의 시각적 요소 추출"
      - "캐릭터, 배경, 액션 분리"
      - "카메라 정보 파싱"

  stage_2_character_setup:
    purpose: "캐릭터 일관성 설정"
    inputs:
      - character_descriptions
      - style_guide
    outputs:
      - character_sheets: list[CharacterSheet]
      - consistency_prompts: dict
    logic:
      - "주요 캐릭터 식별"
      - "캐릭터 시트 생성 (5각도)"
      - "일관성 프롬프트 템플릿 생성"

  stage_3_shot_composition:
    purpose: "각 샷의 구도 설계"
    inputs:
      - structured_shots
      - character_sheets
      - style_guide
    outputs:
      - composition_guides: list[CompositionGuide]
    rag_queries:
      - "shot_type_visual_guide → shot_type 기반"
      - "storyboard_composition_rules → 연속성 규칙"
      - "camera_movement_notation → camera_movement 기반"

  stage_4_image_generation:
    purpose: "스토리보드 이미지 생성"
    inputs:
      - composition_guides
      - character_sheets
    outputs:
      - storyboard_images: list[Image]
    logic:
      - "Flux 1.1 Pro 또는 SDXL 호출"
      - "캐릭터 일관성 기법 적용"
      - "스타일 통일"

  stage_5_annotation:
    purpose: "카메라 노트 및 동작선 오버레이"
    inputs:
      - storyboard_images
      - camera_movements
      - action_descriptions
    outputs:
      - annotated_images: list[Image]
    logic:
      - "카메라 무브먼트 화살표 추가"
      - "동작선 표기"
      - "샷 번호/설명 추가"

  stage_6_export:
    purpose: "스토리보드 내보내기"
    inputs:
      - annotated_images
      - template_selection
    outputs:
      - storyboard_pdf
      - animatic_video (optional)
```

### 4.2 출력 스키마 설계

```python
class StoryboardOutput(BaseModel):
    """스토리보드 생성 출력 스키마"""

    # 메타데이터
    metadata: StoryboardMetadata
    class StoryboardMetadata(BaseModel):
        project_name: str
        total_panels: int
        total_duration: int
        style: str
        aspect_ratio: str

    # 캐릭터 시트
    character_sheets: list[CharacterSheet]
    class CharacterSheet(BaseModel):
        character_id: str
        character_name: str
        reference_images: list[str]  # URLs or base64
        description: str
        consistency_prompt: str

    # 스토리보드 패널
    panels: list[StoryboardPanel]
    class StoryboardPanel(BaseModel):
        panel_number: int
        shot_number: int
        time_range: str
        shot_type: str
        shot_type_abbr: str  # "CU", "MS", "WS"

        # 시각 요소
        image_url: str
        thumbnail_url: str

        # 설명
        scene_description: str
        action_description: str
        dialogue: str | None

        # 카메라
        camera_angle: str
        camera_movement: str
        movement_notation: str  # 화살표 표기

        # 오디오
        audio_notes: str

        # 연결성
        transition_to_next: str  # "cut", "dissolve", "fade"
        continuity_notes: str

    # 연속성 검증
    continuity_check: ContinuityReport
    class ContinuityReport(BaseModel):
        violations: list[ContinuityViolation]
        warnings: list[str]

        class ContinuityViolation(BaseModel):
            panel_numbers: list[int]
            rule_violated: str
            severity: str  # "error", "warning"
            suggestion: str

    # 내보내기 옵션
    export_options: ExportOptions
    class ExportOptions(BaseModel):
        pdf_url: str | None
        png_sequence_url: str | None
        animatic_url: str | None

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     shot_list + scenario     ┌─────────────────┐
│ 1.3 시나리오    │ ─────────────────────────────► │ 2.2 스토리보드  │
│     생성기      │                                │     스케치      │
└─────────────────┘                                └────────┬────────┘
                                                            │
┌─────────────────┐     character_descriptions              │
│ 1.1 심연의 거울 │ ────────────────────────────────────────│
└─────────────────┘                                         │
                                                            │
┌─────────────────┐     auteur_visual_style                 │
│ 5.1 미학 디렉터 │ ────────────────────────────────────────│
└─────────────────┘                                         │
                                                            │ storyboard_panels
                                                            │ + reference_images
                                                            ▼
                                                  ┌─────────────────┐
                                                  │ 2.3 프롬프트    │
                                                  │     연금술      │
                                                  └─────────────────┘
                                                    (AI 프롬프트 변환)
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| shot_list | 시나리오 생성기 | 구조화 | structured_shots | 내부 처리 |
| character_info | 심연의 거울 | 캐릭터 시트 생성 | character_sheets | 일관성 적용 |
| visual_style | 미학 디렉터 | 스타일 가이드 | style_prompts | 이미지 생성 |
| storyboard_panels | - | - | reference_images | 프롬프트 연금술 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 스토리보드 기법 조사

- [ ] Disney/Pixar 스토리보드 제작 가이드 분석
- [ ] 전문 스토리보드 표기법 정리
- [ ] 카메라 무브먼트 아이콘 시스템 설계
- [ ] 연속성 규칙 체크리스트 작성

### 6.2 AI 이미지 일관성 조사

- [ ] IP Adapter v2 최신 가이드 정리
- [ ] Flux 1.1 Pro 캐릭터 일관성 기법
- [ ] StoryMem 논문 심층 분석
- [ ] 스타일 일관성 유지 기법 연구

### 6.3 도구/플랫폼 조사

- [ ] Flux Pro API 통합 방법
- [ ] ComfyUI 워크플로우 설계
- [ ] PDF 생성 라이브러리 (reportlab, weasyprint)
- [ ] 애니매틱 영상 생성 방법

### 6.4 템플릿 조사

- [ ] 업계 표준 스토리보드 레이아웃 수집
- [ ] 다양한 종횡비 템플릿 설계
- [ ] 내보내기 형식별 요구사항

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 스토리보드 규칙 수집 | 2일 | 규칙 DB |
| 2 | 샷 타입 가이드 정리 | 1일 | 가이드 DB |
| 3 | 캐릭터 일관성 기법 연구 | 2일 | 기법 가이드 |
| 4 | Flux API 통합 | 2일 | 이미지 생성 기능 |
| 5 | 어노테이션 시스템 | 2일 | 오버레이 기능 |
| 6 | 내보내기 시스템 | 1일 | PDF/영상 출력 |
| 7 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 학술/기술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| StoryMem (2025) | 논문 | 28.7% 일관성 향상 |
| Storyboard Guide (Pixar) | 가이드 | 프로덕션 스토리보드 |
| IP Adapter v2 | 기술문서 | 이미지 일관성 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| Storyboarder | https://wonderunit.com/storyboarder/ | 무료 스토리보드 툴 |
| FrameForge | https://frameforge3d.com/ | 3D 스토리보드 |
| Boords | https://boords.com/ | 온라인 스토리보드 |

---

## 9. Part 9/10 기술 연계 (2026 보강)

### 9.1 Prop & Background Consistency 통합 (Part 9.2)

스토리보드 스케처는 **멀티샷 시각적 일관성**의 핵심 앱입니다.
Part 9.2의 StoryMem/VideoMemory 기술을 직접 활용합니다.

#### StoryMem Dynamic Memory Bank 적용

```yaml
storymem_integration:
  purpose: "스토리보드 패널 간 캐릭터/소품/배경 일관성 유지"

  memory_bank_design:
    keyframe_storage:
      per_entity_type:
        characters:
          max_keyframes: 10
          storage: "face, body, costume 별도 저장"
        props:
          max_keyframes: 5
          storage: "shape, color, texture 저장"
        backgrounds:
          max_keyframes: 5
          storage: "location, lighting, atmosphere 저장"

    retrieval_trigger:
      - "새 패널 생성 시 관련 엔티티 자동 주입"
      - "캐릭터 이름 언급 시 해당 키프레임 참조"
      - "동일 장소 설정 시 배경 키프레임 적용"

  rope_encoding:
    description: "시간 인코딩으로 메모리 프레임에 '음수 인덱스' 할당"
    benefit: "AI가 이전 패널을 '과거 이벤트'로 인식하여 일관성 유지"

  benchmark_targets:
    character_consistency: ">= 0.63 (StoryMem 12-shot 기준)"
    prop_consistency: ">= 0.58"
    background_consistency: ">= 0.72"
```

#### 엔티티별 레퍼런스 팩 생성

```yaml
reference_pack_generator:
  character_pack:
    generation_flow:
      - "심연의 거울에서 페르소나 정보 수신"
      - "6-10개 다각도 이미지 자동 생성"
      - "angles: [front, 3/4 left, 3/4 right, profile, back]"
      - "expressions: [neutral, happy, sad, angry, surprised]"
    storage: "세션별 캐릭터 메모리 뱅크"

  prop_pack:
    generation_flow:
      - "시나리오에서 키 소품 추출"
      - "3-5개 다각도 이미지 생성"
      - "angles: [front, 45°, detail closeup]"
      - "lighting: [neutral, dramatic]"
    examples:
      - "마법 지팡이"
      - "빈티지 카메라"
      - "주인공의 특별한 목걸이"

  background_pack:
    generation_flow:
      - "장소 설정에서 키 로케이션 추출"
      - "3-5개 분위기별 이미지 생성"
      - "times: [day, dusk, night]"
      - "weather: [clear, cloudy, rain]"
    examples:
      - "주인공의 방"
      - "카페 외관"
      - "학교 옥상"
```

### 9.2 DINOv2 기반 일관성 스코어링

VideoMemory 평가 메트릭을 스토리보드 QC에 적용합니다.

```yaml
consistency_scoring_system:
  method: "DINOv2 feature similarity"

  automated_check:
    per_panel:
      - "이전 패널과의 엔티티 유사도 계산"
      - "임계값 미달 시 경고 플래그"

    thresholds:
      character: 0.70
      prop: 0.60
      background: 0.65

    action_on_fail:
      warning_level: "재생성 권장"
      auto_fix: "메모리 뱅크에서 키프레임 강제 주입 후 재생성"

  user_feedback:
    display: "패널별 일관성 점수 표시 (0-100%)"
    drill_down: "어떤 엔티티가 불일관한지 하이라이트"
```

### 9.3 Visual Realizer 연동

스토리보드 → 비주얼 리얼라이저로 일관성 데이터 전달

```yaml
visual_realizer_handoff:
  data_transfer:
    from_storyboard:
      - "character_memory_bank: 캐릭터 키프레임들"
      - "prop_memory_bank: 소품 키프레임들"
      - "background_memory_bank: 배경 키프레임들"
      - "style_guide: 스타일 일관성 가이드"

    to_visual_realizer:
      - "동일한 메모리 뱅크 공유"
      - "이미지 생성 시 자동 참조"

  consistency_chain:
    flow:
      - "시나리오 → 스토리보드 (일관성 메모리 생성)"
      - "스토리보드 → 비주얼 리얼라이저 (메모리 전달)"
      - "비주얼 리얼라이저 → 비디오 메이커 (메모리 유지)"
    benefit: "전체 파이프라인에서 시각적 일관성 유지"
```

### 9.4 수정된 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Storyboard Sketcher V2 + Memory Bank                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │  Character  │    │    Prop     │    │ Background  │                      │
│  │  Reference  │    │  Reference  │    │  Reference  │                      │
│  │    Pack     │    │    Pack     │    │    Pack     │                      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                      │
│         │                  │                  │                              │
│         └──────────────────┼──────────────────┘                              │
│                            ▼                                                 │
│              ┌──────────────────────────┐                                   │
│              │   Dynamic Memory Bank    │                                   │
│              │   (StoryMem Pattern)     │                                   │
│              │   ┌────┬────┬────┐       │                                   │
│              │   │Char│Prop│ BG │       │                                   │
│              │   │ KF │ KF │ KF │       │                                   │
│              │   └────┴────┴────┘       │                                   │
│              └──────────────────────────┘                                   │
│                            │                                                 │
│           ┌────────────────┼────────────────┐                               │
│           ▼                ▼                ▼                               │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│   │   Panel 1   │  │   Panel 2   │  │   Panel N   │                        │
│   │  + Score    │  │  + Score    │  │  + Score    │                        │
│   └─────────────┘  └─────────────┘  └─────────────┘                        │
│                            │                                                 │
│                            ▼                                                 │
│              ┌──────────────────────────┐                                   │
│              │   DINOv2 Consistency     │                                   │
│              │   Scoring & QC           │                                   │
│              └──────────────────────────┘                                   │
│                            │                                                 │
│                            ▼                                                 │
│              ┌──────────────────────────┐                                   │
│              │   → Visual Realizer      │                                   │
│              │   (Memory Bank Handoff)  │                                   │
│              └──────────────────────────┘                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 스토리보드 규칙 수집 |
| 2026-01-17 | Part 9/10 기술 연계 (Prop/BG Consistency, Memory Bank) | 완료 | DINOv2 스코어링 구현 |
| 2026-01-17 | 웹 리서치 완료 (StoryMem, Multi-Shot Consistency) | 완료 | 스토리보드 파이프라인 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### 스토리보드 및 Multi-Shot Consistency 종합 분석

#### 1. StoryMem (ByteDance + NTU, Dec 2025)

```yaml
storymem_for_storyboard:
  core_concept: "Memory-to-Video (M2V) 패러다임"

  key_innovation:
    - "Human memory에서 영감받은 keyframe 저장"
    - "LoRA만으로 fine-tuning (경량화)"
    - "기존 single-shot 모델을 multi-shot으로 확장"

  consistency_improvement:
    vs_wan22_baseline:
      character: "+28.7%"
      overall: "minute-long coherent videos"

  memory_bank_mechanism:
    keyframe_selection:
      semantic_criteria: "의미적으로 구별되는 프레임"
      aesthetic_criteria: "미적 품질 필터링"

    memory_management:
      memory_sink: "초기 키프레임 고정 (글로벌 anchor)"
      sliding_window: "최근 키프레임 유지 (로컬 맥락)"

    injection_method: "latent concatenation + negative RoPE shifts"
```

#### 2. Consistency Benchmark 결과

| Method | Character | Prop | Background |
|--------|-----------|------|------------|
| Wan 2.2 (baseline) | 0.34 | 0.48 | 0.25 |
| IC-LoRA + Wan 2.2 | 0.47 | 0.43 | 0.31 |
| StoryDiffusion + Wan 2.2 | 0.54 | 0.47 | 0.42 |
| VGoT + Wan 2.2 | 0.57 | 0.31 | 0.45 |
| **VideoMemory** | **0.63** | **0.58** | **0.72** |

#### 3. 스토리보드 생성 최적 워크플로우

```yaml
storyboard_workflow:
  phase1_script_analysis:
    input: "씬 스크립트"
    output:
      - "주요 캐릭터 리스트"
      - "핵심 소품 리스트"
      - "배경/로케이션 정의"
      - "샷 분해 (shot breakdown)"

  phase2_keyframe_generation:
    method: "IC-LoRA 또는 Image Generator"
    requirements:
      - "캐릭터 레퍼런스 이미지"
      - "배경 레퍼런스"
      - "구도 지시 (샷 타입)"

  phase3_memory_bank_initialization:
    entities:
      characters:
        - "레퍼런스 이미지"
        - "DINOv2 feature 추출"
        - "CLIP embedding 저장"
      props:
        - "소품 이미지"
        - "상태 변화 추적"
      backgrounds:
        - "환경 키프레임"
        - "조명 조건 기록"

  phase4_consistency_validation:
    metrics:
      character_consistency: "DINOv2 similarity >= 0.63"
      prop_consistency: "DINOv2 similarity >= 0.58"
      background_consistency: "CLIP similarity >= 0.72"

    action_on_failure:
      - "memory bank 참조 regeneration"
      - "inpainting으로 수정"
```

#### 4. Crebit Storyboard Sketcher 구현 권장

```yaml
crebit_storyboard_implementation:
  panel_generation_pipeline:
    step1_entity_extraction:
      input: "씬 스크립트"
      output:
        characters: ["이름", "설명", "레퍼런스 URL"]
        props: ["이름", "중요도"]
        backgrounds: ["로케이션", "시간대", "조명"]

    step2_memory_bank_setup:
      per_entity:
        keyframe_slots: "max 10"
        feature_storage: "DINOv2 + CLIP"
        update_policy: "semantic distinctiveness > 0.15"

    step3_panel_generation:
      for_each_shot:
        1. "Memory Bank에서 관련 엔티티 검색"
        2. "검색된 레퍼런스로 프롬프트 보강"
        3. "Image Generator로 패널 생성"
        4. "DINOv2로 일관성 검증"
        5. "통과 시 Memory Bank 업데이트"

    step4_output:
      storyboard_document:
        - panel_image
        - shot_type
        - camera_movement
        - dialogue_overlay
        - duration_estimate

  consistency_targets:
    character: ">= 0.63"
    prop: ">= 0.58"
    background: ">= 0.72"

  fallback_strategies:
    low_consistency:
      - "Memory Bank에서 가장 유사한 keyframe 참조"
      - "일관성 낮은 영역 inpainting"
      - "사용자에게 수동 검토 요청 (HITL)"
```

### Sources
- StoryMem (ByteDance + NTU, arXiv Dec 2025)
- VideoMemory Benchmark Results (Jan 2026)
- IC-LoRA for Film Storyboard Generation
- DINOv2 for Visual Consistency Scoring
