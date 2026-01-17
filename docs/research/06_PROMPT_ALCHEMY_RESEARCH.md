# App 2.3: 프롬프트 연금술 (Prompt Alchemy) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: Prompt

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치 (신규 생성 필요)
file_path = "backend/app/routers/dimension/prompt.py"

# 예상 엔드포인트
endpoints = [
    "POST /dimension/prompt/translate",
    "POST /dimension/prompt/translate/stream",
    "POST /dimension/prompt/optimize",
    "POST /dimension/prompt/batch",
]

# 현재 기능 (미구현)
current_features = []

# 목표 기능
target_features = [
    "씬 설명 → 플랫폼별 프롬프트 변환",
    "Veo 3.1/Kling 2.6/Sora 2 최적화",
    "샷 특성 기반 도구 자동 선택",
    "프롬프트 품질 점수 평가",
    "배치 프롬프트 생성",
]
```

### 1.2 현재 한계점 (신규 앱 설계 기준)

| 도전과제 | 영향 | 해결 방향 |
|----------|------|----------|
| 플랫폼별 프롬프트 문법 상이 | 수동 변환 필요 | 플랫폼별 템플릿 + 변환 규칙 |
| 최적 도구 선택 기준 부재 | 비효율적 도구 사용 | 샷 특성 기반 휴리스틱 |
| 프롬프트 품질 객관화 어려움 | 시행착오 반복 | 품질 메트릭 + 자동 평가 |
| 거장 스타일 반영 미흡 | 일반적 결과물 | 거장 스타일 프롬프트 DB |

---

## 2. 핵심 연구 주제

### 2.1 AI 비디오 플랫폼별 프롬프트 연구

**연구 질문**:
- 각 플랫폼의 프롬프트 문법/구조는?
- 플랫폼별 효과적인 키워드는?
- 부정 프롬프트(Negative Prompt) 패턴은?

**조사 대상**:
1. Veo 3.1/4 공식 프롬프트 가이드
2. Kling 2.6 프롬프트 모범 사례
3. Sora 2 Pro Max 프롬프팅 기법
4. 커뮤니티 프롬프트 분석 (Reddit, Discord)

### 2.2 샷-도구 매핑 휴리스틱 연구

**연구 질문**:
- 각 샷 유형에 최적의 도구는?
- 모션 레벨별 도구 선택 기준은?
- 도구 간 품질/비용 트레이드오프는?

**조사 대상**:
1. 2026 AI 비디오 도구 벤치마크
2. 샷 유형별 생성 품질 비교
3. 커뮤니티 경험 데이터

### 2.3 거장 스타일 프롬프트화 연구

**연구 질문**:
- 거장의 시각적 스타일을 프롬프트로 어떻게 표현?
- 영화 조명/색감을 프롬프트로 어떻게 지정?
- 거장별 시그니처 기법의 프롬프트 표현?

**조사 대상**:
1. 거장 영화 시각적 분석
2. 촬영 기법 → 프롬프트 변환 패턴
3. 색 보정/그레이딩 프롬프트

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: platform_prompt_guides

```yaml
id: platform_prompt_guides
description: "AI 비디오 플랫폼별 프롬프트 가이드"
source: "공식 문서, 커뮤니티 분석"
size: ~100 documents

schema:
  platform_id:
    type: string
    enum: ["veo_3_1", "veo_4", "kling_2_6", "sora_2_pro", "runway_gen3"]

  platform_name:
    type: string

  version:
    type: string

  prompt_structure:
    type: object
    schema:
      max_length: int
      recommended_length: int
      structure_template: string
      key_sections: list[string]

  effective_keywords:
    type: list[object]
    schema:
      keyword: string
      category: string  # "camera", "lighting", "motion", "style", "quality"
      effect: string
      strength: float  # 0-1 효과 강도

  negative_keywords:
    type: list[object]
    schema:
      keyword: string
      prevents: string

  motion_guidance:
    type: object
    schema:
      supported: bool
      format: string
      examples: list[string]

  camera_controls:
    type: object
    schema:
      movement_keywords: list[string]
      angle_keywords: list[string]
      speed_keywords: list[string]

  style_modifiers:
    type: list[object]
    schema:
      modifier: string
      effect: string
      compatibility: float

  example_prompts:
    type: list[object]
    schema:
      description: string
      prompt: string
      result_notes: string
      quality_score: float

# 예시 데이터
platform_guides:
  - platform_id: "veo_3_1"
    platform_name: "Google Veo 3.1"
    version: "3.1"
    prompt_structure:
      max_length: 2000
      recommended_length: 200-400
      structure_template: "[SCENE DESCRIPTION] [CAMERA] [LIGHTING] [STYLE] [QUALITY]"
      key_sections:
        - "scene_description"  # 무엇이 일어나는가
        - "camera_movement"    # 카메라 동작
        - "lighting_mood"      # 조명과 분위기
        - "style_reference"    # 스타일 참조
        - "quality_tags"       # 품질 태그
    effective_keywords:
      - keyword: "cinematic"
        category: "style"
        effect: "영화적 색감과 구도"
        strength: 0.9
      - keyword: "slow motion"
        category: "motion"
        effect: "슬로우 모션 효과"
        strength: 0.85
      - keyword: "dolly shot"
        category: "camera"
        effect: "달리 카메라 무브먼트"
        strength: 0.8
      - keyword: "golden hour lighting"
        category: "lighting"
        effect: "따뜻한 골든아워 조명"
        strength: 0.85
    motion_guidance:
      supported: true
      format: "[camera movement] [subject motion] [speed]"
      examples:
        - "camera slowly pushes in while subject walks toward camera"
        - "static camera, subject runs left to right"
    camera_controls:
      movement_keywords: ["dolly", "pan", "tilt", "crane", "tracking", "steadicam", "handheld"]
      angle_keywords: ["low angle", "high angle", "eye level", "bird's eye", "dutch angle"]
      speed_keywords: ["slow", "medium", "fast", "dynamic"]

  - platform_id: "kling_2_6"
    platform_name: "Kling 2.6"
    version: "2.6"
    prompt_structure:
      max_length: 1500
      recommended_length: 150-300
      structure_template: "[SUBJECT] [ACTION] [ENVIRONMENT] [CAMERA] [STYLE]"
    effective_keywords:
      - keyword: "photorealistic"
        category: "quality"
        effect: "사실적인 텍스처와 디테일"
        strength: 0.95
      - keyword: "portrait shot"
        category: "camera"
        effect: "인물 클로즈업 최적화"
        strength: 0.9
    motion_guidance:
      supported: true
      format: "start frame + end frame + motion description"
      examples:
        - "Start: close-up of eye, End: face in medium shot, Motion: slow zoom out"

  - platform_id: "sora_2_pro"
    platform_name: "OpenAI Sora 2 Pro Max"
    version: "2.0"
    prompt_structure:
      max_length: 4000
      recommended_length: 300-800
      structure_template: "[DETAILED SCENE] [TEMPORAL FLOW] [PHYSICAL ACCURACY] [STYLE]"
    effective_keywords:
      - keyword: "physically accurate"
        category: "quality"
        effect: "물리 시뮬레이션 향상"
        strength: 0.88
      - keyword: "continuous shot"
        category: "camera"
        effect: "끊김 없는 롱테이크"
        strength: 0.85
```

### 3.2 데이터셋: shot_tool_selection_matrix

```yaml
id: shot_tool_selection_matrix
description: "샷 특성별 AI 도구 선택 매트릭스"
source: "2026 벤치마크, 실험 데이터"
size: ~80 documents

schema:
  shot_scenario_id:
    type: string
    example: "facial_closeup_emotional"

  shot_description:
    type: string

  characteristics:
    type: object
    schema:
      motion_level: string  # "static", "low", "medium", "high", "extreme"
      detail_requirement: string  # "low", "medium", "high"
      duration: string  # "short", "medium", "long"
      camera_complexity: string  # "simple", "moderate", "complex"
      lighting_requirement: string
      audio_sync: bool

  tool_rankings:
    type: list[object]
    schema:
      tool: string
      score: float  # 0-1 적합도
      reasoning: string
      quality_expectation: float
      cost_per_second: float

  recommended_tool:
    type: string

  fallback_tools:
    type: list[string]

  prompt_template:
    type: object
    schema:
      primary: string  # 추천 도구용 템플릿
      kling: string
      veo: string
      sora: string

  quality_metrics:
    type: object
    schema:
      facial_fidelity: float
      motion_smoothness: float
      style_adherence: float
      temporal_consistency: float

# 예시 데이터
shot_tool_matrix:
  - shot_scenario_id: "facial_closeup_emotional"
    shot_description: "감정적인 순간의 얼굴 클로즈업"
    characteristics:
      motion_level: "low"
      detail_requirement: "high"
      duration: "short"
      camera_complexity: "simple"
      lighting_requirement: "soft_dramatic"
      audio_sync: false
    tool_rankings:
      - tool: "kling"
        score: 0.95
        reasoning: "안면 보존력 최고 (CLIP-Face 0.92)"
        quality_expectation: 0.92
        cost_per_second: 0.10
      - tool: "veo"
        score: 0.75
        reasoning: "좋은 품질이나 얼굴 일관성 약간 낮음"
        quality_expectation: 0.78
        cost_per_second: 0.12
      - tool: "sora"
        score: 0.70
        reasoning: "동작이 많은 씬에 더 적합"
        quality_expectation: 0.75
        cost_per_second: 0.15
    recommended_tool: "kling"
    prompt_template:
      kling: "Extreme close-up portrait shot of {character}, {emotion} expression, soft dramatic lighting, subtle {micro_expression}, cinematic depth of field, photorealistic skin texture"
      veo: "Emotional close-up, {character}'s face filling frame, {emotion}, intimate lighting, shallow depth of field, cinematic"
      sora: "Portrait close-up of {character} showing {emotion}, soft lighting, minimal movement, focus on facial details"

  - shot_scenario_id: "action_sequence_chase"
    shot_description: "추격 액션 시퀀스"
    characteristics:
      motion_level: "extreme"
      detail_requirement: "medium"
      duration: "medium"
      camera_complexity: "complex"
      lighting_requirement: "dynamic"
      audio_sync: true
    tool_rankings:
      - tool: "sora"
        score: 0.92
        reasoning: "고속 동작 연속성 최고 (FID-Motion 12.3)"
        quality_expectation: 0.88
        cost_per_second: 0.15
      - tool: "veo"
        score: 0.80
        reasoning: "오디오 동기화 가능"
        quality_expectation: 0.82
        cost_per_second: 0.12
      - tool: "kling"
        score: 0.55
        reasoning: "빠른 동작에서 일관성 저하"
        quality_expectation: 0.60
        cost_per_second: 0.10
    recommended_tool: "sora"
    prompt_template:
      sora: "Dynamic chase sequence, {character} running through {environment}, camera tracking shot following movement, fast-paced action, motion blur on fast elements, physically accurate movement, continuous shot"
```

### 3.3 데이터셋: auteur_visual_prompts

```yaml
id: auteur_visual_prompts
description: "거장 감독별 시각적 스타일 프롬프트 DB"
source: "영화 분석, 촬영 기법 연구"
size: ~50 documents

schema:
  auteur_key:
    type: string
    example: "bong_joon_ho"

  style_name:
    type: string

  visual_signature:
    type: list[object]
    schema:
      element: string
      prompt_translation: string
      example_film: string

  color_grading:
    type: object
    schema:
      primary_palette: list[string]
      contrast_level: string
      saturation_level: string
      prompt_keywords: list[string]

  lighting_style:
    type: object
    schema:
      primary_approach: string
      key_to_fill_ratio: string
      signature_techniques: list[string]
      prompt_keywords: list[string]

  composition_patterns:
    type: list[object]
    schema:
      pattern: string
      usage_context: string
      prompt_translation: string

  camera_preferences:
    type: object
    schema:
      preferred_movements: list[string]
      preferred_angles: list[string]
      lens_choices: list[string]
      prompt_keywords: list[string]

  full_style_prompt:
    type: string
    description: "거장 스타일 전체 프롬프트"

  platform_adaptations:
    type: object
    schema:
      veo: string
      kling: string
      sora: string

# 예시 데이터
auteur_prompts:
  - auteur_key: "bong_joon_ho"
    style_name: "봉준호 스타일"
    visual_signature:
      - element: "계층적 프레이밍"
        prompt_translation: "layered framing with foreground, midground, and background elements showing social hierarchy"
        example_film: "기생충 - 반지하 계단 씬"
      - element: "대칭과 비대칭의 대비"
        prompt_translation: "symmetrical composition contrasted with asymmetric tension"
        example_film: "기생충 - 거실 침수 씬"
      - element: "수직 공간 활용"
        prompt_translation: "vertical space emphasizing height differences, stairs, levels"
        example_film: "기생충 - 계단 추격"
    color_grading:
      primary_palette: ["muted_tones", "green_yellow", "warm_shadows"]
      contrast_level: "high"
      saturation_level: "selective"
      prompt_keywords: ["muted color palette", "high contrast", "selective saturation", "green-yellow undertones"]
    lighting_style:
      primary_approach: "naturalistic with dramatic accents"
      key_to_fill_ratio: "3:1 to 5:1"
      signature_techniques: ["practicals", "motivated_lighting", "shadow_play"]
      prompt_keywords: ["naturalistic lighting", "high contrast shadows", "practical light sources", "window light"]
    composition_patterns:
      - pattern: "frame_within_frame"
        usage_context: "confinement, voyeurism"
        prompt_translation: "frame within frame, looking through doorway/window, voyeuristic composition"
      - pattern: "symmetrical_tension"
        usage_context: "confrontation, irony"
        prompt_translation: "centered symmetrical composition with subtle asymmetric elements"
    camera_preferences:
      preferred_movements: ["slow_dolly", "slow_pan", "static_wide"]
      preferred_angles: ["eye_level", "slight_low_angle"]
      lens_choices: ["35mm", "40mm", "50mm"]
      prompt_keywords: ["slow deliberate camera movement", "wide angle lens", "eye level perspective"]
    full_style_prompt: "Bong Joon-ho cinematic style, layered framing showing social contrast, muted color palette with green-yellow undertones, high contrast naturalistic lighting, symmetrical composition with subtle tension, slow deliberate camera movement, frame within frame compositions"
    platform_adaptations:
      veo: "cinematic, Bong Joon-ho style, layered composition, muted colors, high contrast, naturalistic lighting with dramatic shadows, slow camera movement, social realism"
      kling: "Korean cinema style, realistic, layered framing, muted palette, high contrast shadows, deliberate composition, social drama aesthetics"
      sora: "Bong Joon-ho inspired cinematography, layered social compositions, muted color grading with green undertones, naturalistic yet dramatic lighting, methodical camera work"

  - auteur_key: "wong_kar_wai"
    style_name: "왕가위 스타일"
    visual_signature:
      - element: "스텝 프린팅 / 언더크랭킹"
        prompt_translation: "step-printed slow motion effect, dreamy motion blur, smeared movement"
        example_film: "중경삼림 - 페이 러닝 씬"
      - element: "네온 컬러 팔레트"
        prompt_translation: "saturated neon colors, deep reds, electric blues, golden yellows"
        example_film: "화양연화 - 골목 씬"
    color_grading:
      primary_palette: ["neon_red", "electric_blue", "golden_yellow", "deep_green"]
      contrast_level: "high"
      saturation_level: "high"
      prompt_keywords: ["neon color palette", "saturated colors", "deep reds and blues", "golden highlights"]
    lighting_style:
      primary_approach: "expressionistic neon"
      signature_techniques: ["neon_practical", "color_gels", "silhouette"]
      prompt_keywords: ["neon lighting", "colored gels", "expressionistic light", "silhouette against light"]
    full_style_prompt: "Wong Kar-wai style, step-printed motion blur, saturated neon color palette with deep reds and electric blues, expressionistic neon lighting, intimate close-ups, fragmented time, nostalgic urban atmosphere"
```

### 3.4 데이터셋: prompt_quality_metrics

```yaml
id: prompt_quality_metrics
description: "프롬프트 품질 평가 기준 및 체크리스트"
source: "커뮤니티 분석, 실험 데이터"
size: ~30 documents

schema:
  metric_id:
    type: string
    example: "clarity_score"

  metric_name:
    type: string

  description:
    type: string

  evaluation_criteria:
    type: list[object]
    schema:
      criterion: string
      weight: float
      scoring_guide: string

  common_issues:
    type: list[object]
    schema:
      issue: string
      impact: string
      fix_suggestion: string

  optimization_tips:
    type: list[string]

# 예시 메트릭
quality_metrics:
  - metric_id: "specificity_score"
    metric_name: "구체성 점수"
    description: "프롬프트가 얼마나 구체적으로 원하는 결과를 묘사하는가"
    evaluation_criteria:
      - criterion: "주체 명확성"
        weight: 0.25
        scoring_guide: "0: 모호함, 0.5: 부분적, 1: 완전히 명확"
      - criterion: "동작 상세도"
        weight: 0.25
        scoring_guide: "0: 없음, 0.5: 기본, 1: 상세한 동작 묘사"
      - criterion: "환경 묘사"
        weight: 0.20
        scoring_guide: "0: 없음, 0.5: 기본, 1: 상세한 환경"
      - criterion: "카메라/구도"
        weight: 0.15
        scoring_guide: "0: 없음, 0.5: 기본, 1: 명확한 카메라 워크"
      - criterion: "스타일 지정"
        weight: 0.15
        scoring_guide: "0: 없음, 0.5: 일반적, 1: 구체적 스타일"
    common_issues:
      - issue: "너무 일반적인 묘사"
        impact: "예측 불가능한 결과"
        fix_suggestion: "구체적인 형용사와 동사 사용"
      - issue: "모순되는 지시"
        impact: "혼란스러운 출력"
        fix_suggestion: "일관된 톤과 스타일 유지"
```

---

## 4. 기능 고도화 설계

### 4.1 변환 파이프라인

```yaml
prompt_alchemy_pipeline:
  stage_1_input_analysis:
    purpose: "입력 씬 분석 및 특성 추출"
    inputs:
      - scene_description
      - shot_info (type, camera, motion)
      - auteur_style (optional)
      - reference_images (optional)
    outputs:
      - shot_characteristics
      - style_requirements
    logic:
      - "씬 설명에서 핵심 요소 추출"
      - "카메라/모션 정보 파싱"
      - "스타일 요구사항 식별"

  stage_2_tool_selection:
    purpose: "최적 AI 도구 선택"
    inputs:
      - shot_characteristics
    outputs:
      - recommended_tool
      - fallback_tools
      - selection_reasoning
    rag_queries:
      - "shot_tool_selection_matrix → 샷 특성 기반"
    logic:
      - "모션 레벨, 디테일 요구사항 평가"
      - "도구별 적합도 점수 계산"
      - "비용 효율성 고려"

  stage_3_prompt_construction:
    purpose: "플랫폼 최적화 프롬프트 생성"
    inputs:
      - scene_description
      - recommended_tool
      - style_requirements
      - auteur_style
    outputs:
      - primary_prompt
      - negative_prompt
    rag_queries:
      - "platform_prompt_guides → 플랫폼별 가이드"
      - "auteur_visual_prompts → 거장 스타일"
    logic:
      - "플랫폼별 프롬프트 구조 적용"
      - "효과적인 키워드 삽입"
      - "거장 스타일 프롬프트 통합"

  stage_4_quality_evaluation:
    purpose: "프롬프트 품질 평가 및 개선"
    inputs:
      - generated_prompt
    outputs:
      - quality_score
      - improvement_suggestions
    rag_queries:
      - "prompt_quality_metrics → 평가 기준"
    logic:
      - "구체성, 명확성, 일관성 평가"
      - "일반적 문제 점검"
      - "개선 제안 생성"

  stage_5_multi_platform_output:
    purpose: "다중 플랫폼 프롬프트 생성"
    inputs:
      - optimized_prompt
      - target_platforms
    outputs:
      - platform_prompts: dict[platform, prompt]
    logic:
      - "각 플랫폼 형식에 맞게 변환"
      - "플랫폼별 키워드 최적화"
```

### 4.2 출력 스키마 설계

```python
class PromptAlchemyOutput(BaseModel):
    """프롬프트 연금술 출력 스키마"""

    # 메타데이터
    metadata: PromptMetadata
    class PromptMetadata(BaseModel):
        shot_number: int
        scene_reference: str
        tool_recommended: str
        tool_alternatives: list[str]
        selection_confidence: float

    # 도구 선택 근거
    tool_selection: ToolSelectionAnalysis
    class ToolSelectionAnalysis(BaseModel):
        shot_characteristics: ShotCharacteristics
        tool_scores: dict[str, float]
        selection_reasoning: str

        class ShotCharacteristics(BaseModel):
            motion_level: str
            detail_requirement: str
            camera_complexity: str
            duration: str
            special_requirements: list[str]

    # 플랫폼별 프롬프트
    prompts: PlatformPrompts
    class PlatformPrompts(BaseModel):
        primary: GeneratedPrompt  # 추천 도구용
        veo: GeneratedPrompt | None
        kling: GeneratedPrompt | None
        sora: GeneratedPrompt | None

        class GeneratedPrompt(BaseModel):
            platform: str
            main_prompt: str
            negative_prompt: str
            style_tags: list[str]
            motion_guidance: str | None
            camera_instructions: str | None
            quality_tags: list[str]
            prompt_length: int
            estimated_quality: float

    # 품질 평가
    quality_assessment: QualityAssessment
    class QualityAssessment(BaseModel):
        overall_score: float
        dimension_scores: dict[str, float]  # specificity, clarity, consistency 등
        issues_found: list[str]
        improvement_suggestions: list[str]

    # 거장 스타일 적용 (있는 경우)
    auteur_adaptation: AuteurAdaptation | None
    class AuteurAdaptation(BaseModel):
        auteur_key: str
        style_elements_applied: list[str]
        style_prompt_fragment: str

    # 참조 이미지 가이드 (있는 경우)
    reference_guidance: ReferenceGuidance | None
    class ReferenceGuidance(BaseModel):
        reference_image_urls: list[str]
        consistency_instructions: str
        character_prompts: dict[str, str]

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     shot_list + descriptions     ┌─────────────────┐
│ 1.3 시나리오    │ ─────────────────────────────────► │ 2.3 프롬프트    │
│     생성기      │                                   │     연금술      │
└─────────────────┘                                   └────────┬────────┘
                                                               │
┌─────────────────┐     reference_images                       │
│ 2.2 스토리보드  │ ───────────────────────────────────────────│
│     스케치      │                                            │
└─────────────────┘                                            │
                                                               │
┌─────────────────┐     auteur_visual_style                    │
│ 5.1 미학 디렉터 │ ───────────────────────────────────────────│
└─────────────────┘                                            │
                                                               │ platform_prompts
                                                               │ + tool_recommendations
                                                               ▼
                                            ┌─────────────────────────────────┐
                                            │       3.1 비주얼 리얼라이저      │
                                            │       (키프레임 이미지)          │
                                            └─────────────────────────────────┘
                                                               │
                                                               ▼
                                            ┌─────────────────────────────────┐
                                            │       3.2 비디오 메이커          │
                                            │       (AI 비디오 생성)           │
                                            └─────────────────────────────────┘
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| shot_descriptions | 시나리오 생성기 | 특성 분석 | shot_characteristics | 도구 선택 |
| storyboard_images | 스토리보드 스케치 | 참조 이미지 | reference_prompts | 프롬프트 생성 |
| auteur_style | 미학 디렉터 | 스타일 프롬프트 | style_fragments | 프롬프트 통합 |
| platform_prompts | - | - | ai_generation_input | 비주얼 리얼라이저 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 플랫폼 프롬프트 조사

- [ ] Veo 3.1/4 공식 프롬프트 가이드 정리
- [ ] Kling 2.6 효과적 키워드 수집
- [ ] Sora 2 Pro Max 프롬프팅 기법 분석
- [ ] Runway Gen-3 프롬프트 패턴 분석
- [ ] 커뮤니티 베스트 프롬프트 수집 (Reddit, Discord)

### 6.2 도구 선택 휴리스틱 조사

- [ ] 2026 AI 비디오 도구 벤치마크 분석
- [ ] 샷 유형별 품질 비교 실험 설계
- [ ] 비용 효율성 분석 모델 개발
- [ ] 도구 간 전환 시 연속성 유지 기법

### 6.3 거장 스타일 프롬프트화

- [ ] 봉준호 시각 스타일 프롬프트화
- [ ] 놀란 시각 스타일 프롬프트화
- [ ] 왕가위 시각 스타일 프롬프트화
- [ ] 미야자키 하야오 시각 스타일 프롬프트화
- [ ] 타란티노 시각 스타일 프롬프트화

### 6.4 품질 메트릭 조사

- [ ] 프롬프트 품질 평가 기준 정립
- [ ] 자동 평가 알고리즘 설계
- [ ] A/B 테스트 프레임워크 설계

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 플랫폼 가이드 수집 | 3일 | 플랫폼 DB |
| 2 | 도구 선택 매트릭스 | 2일 | 선택 규칙 |
| 3 | 거장 스타일 프롬프트 | 3일 | 스타일 DB |
| 4 | 품질 메트릭 정의 | 1일 | 평가 시스템 |
| 5 | 파이프라인 구현 | 3일 | 코드 |
| 6 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 기술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| Veo Prompt Guide | 공식문서 | Google Veo 프롬프팅 |
| Kling Best Practices | 가이드 | Kling 최적화 기법 |
| Sora Prompting | 공식문서 | OpenAI Sora 프롬프팅 |

### 참고 커뮤니티

| 커뮤니티 | URL | 참고 포인트 |
|----------|-----|-------------|
| r/AIVideos | Reddit | 프롬프트 공유 |
| Kling Discord | Discord | 커뮤니티 프롬프트 |
| Civitai | https://civitai.com/ | 이미지 프롬프트 참고 |

---

## 9. Part 9/10 기술 연계 (2026 보강)

### 9.1 Native Audio 프롬프트 통합 (Part 9.1)

2026년 핵심 패러다임 변화: **영상 + 오디오를 하나의 프롬프트로 생성**

#### Native Audio 프롬프트 아키텍처

```yaml
native_audio_prompt_integration:
  paradigm_shift:
    before: "영상 프롬프트 + 오디오 프롬프트 분리"
    after: "통합 멀티모달 프롬프트"

  unified_prompt_structure:
    visual_component:
      - "씬 설명"
      - "카메라 워크"
      - "조명/색감"
      - "캐릭터 액션"

    audio_component:
      - "대화/내레이션"
      - "효과음 힌트"
      - "앰비언트 분위기"
      - "BGM 무드 (옵션)"

  platform_support:
    veo_3_1:
      native_audio: true
      audio_types: ["dialogue", "sfx", "ambient", "bgm"]
      prompt_integration: "텍스트 끝에 오디오 설명 추가"

    kling_2_6:
      native_audio: true
      audio_types: ["dialogue", "singing", "rap", "sfx", "ambient"]
      prompt_integration: "voice_prompt 파라미터 별도"

    sora_2:
      native_audio: true
      audio_types: ["dialogue", "sfx"]
      prompt_integration: "통합 프롬프트"
```

#### 플랫폼별 Native Audio 프롬프트 템플릿

```yaml
audio_prompt_templates:
  veo_dialogue_scene:
    template: |
      [Visual] {visual_description}
      [Dialogue] Character A says: "{line_a}" Character B responds: "{line_b}"
      [Ambient] {ambient_sound_description}
      [Mood] {emotional_tone}
    example: |
      [Visual] Two friends sitting at a cafe table, warm afternoon light
      [Dialogue] Character A says: "I've been thinking about what you said" Character B responds: "And?"
      [Ambient] Gentle cafe ambiance, distant conversations, coffee machine hum
      [Mood] Contemplative, warm, intimate

  kling_musical_scene:
    template: |
      [Visual] {visual_description}
      [Voice] {voice_type}: "{lyrics_or_dialogue}"
      [Performance Style] {performance_notes}
      [Audio Mood] {audio_mood}
    example: |
      [Visual] Singer on stage, dramatic spotlight, audience silhouettes
      [Voice] Emotional female vocal: "Remember when we used to dream..."
      [Performance Style] Building crescendo, powerful vibrato on chorus
      [Audio Mood] Nostalgic ballad, 80 BPM

  sora_action_scene:
    template: |
      [Visual] {visual_description}
      [SFX] {sound_effects}
      [Dialogue] {optional_dialogue}
    example: |
      [Visual] Car chase through city streets, protagonist drifting around corner
      [SFX] Tire screech, engine roar, distant sirens
      [Dialogue] Driver mutters "Come on, come on..."
```

### 9.2 사운드 크래프터 연동

프롬프트 연금술과 사운드 크래프터의 협업 워크플로우

```yaml
sound_crafter_integration:
  decision_flow:
    step_1:
      question: "Native Audio 적합성 판단"
      criteria:
        native_suitable:
          - "대화 립싱크 필요"
          - "효과음 타이밍 중요"
          - "앰비언트 씬"
        separate_suitable:
          - "특정 보컬 아티스트 스타일 필요"
          - "복잡한 BGM 편곡"
          - "저작권 귀속 명확화 필요"

    step_2:
      if_native:
        action: "오디오 설명을 영상 프롬프트에 통합"
        output: "unified_prompt"
      if_separate:
        action: "사운드 크래프터에 별도 요청"
        output: "visual_prompt + audio_request"

  data_exchange:
    to_sound_crafter:
      - "scene_mood: 씬 분위기"
      - "duration: 예상 길이"
      - "audio_type: dialogue/bgm/sfx"
      - "sync_points: 동기화 포인트"

    from_sound_crafter:
      - "suno_prompt: BGM 생성용 (Tier 2)"
      - "voice_script: 내레이션 스크립트 (Tier 3)"
      - "audio_strategy: native/separate/hybrid"
```

### 9.3 Tiered Audio 전략 자동 선택

```yaml
audio_strategy_selector:
  input:
    shot_characteristics:
      - "dialogue_present: bool"
      - "music_intensity: low/medium/high"
      - "sfx_complexity: simple/complex"
      - "lip_sync_required: bool"

  decision_matrix:
    tier_1_native_audio:
      conditions:
        - "dialogue_present AND lip_sync_required"
        - "sfx_complexity == simple"
        - "ambient scene"
      output:
        audio_method: "native"
        prompt_type: "unified"

    tier_2_separate_bgm:
      conditions:
        - "music_intensity == high"
        - "specific artist style needed"
        - "song with lyrics"
      output:
        audio_method: "separate"
        bgm_tool: "suno | udio"
        prompt_type: "visual_only + suno_prompt"

    tier_3_post_enhancement:
      conditions:
        - "native quality insufficient"
        - "specific voice actor needed"
        - "complex sound design"
      output:
        audio_method: "post"
        tools: ["elevenlabs", "mm_audio_v2"]
        prompt_type: "visual_only + post_processing_guide"

  output_schema:
    audio_strategy:
      primary_method: "native | separate | hybrid"
      native_config:
        platform: "veo | kling | sora"
        audio_prompt: "string (영상 프롬프트에 통합)"
      separate_config:
        bgm_prompt: "string (Suno/Udio용)"
        voice_scripts: "list[object]"
      post_config:
        enhancement_notes: "string"
```

### 9.4 수정된 프롬프트 파이프라인

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Prompt Alchemy V2 + Native Audio                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Input Sources                                                               │
│     │                                                                        │
│     ├──► Shot Description ──────┐                                           │
│     ├──► Storyboard Image ──────┼───► Shot Analyzer                         │
│     ├──► Auteur Style ──────────┤                                           │
│     └──► Sound Crafter Hints ───┘                                           │
│                                          │                                   │
│                                          ▼                                   │
│              ┌──────────────────────────────────────────┐                   │
│              │        Audio Strategy Selector           │                   │
│              │  ┌───────┬───────┬───────┐              │                   │
│              │  │Tier 1 │Tier 2 │Tier 3 │              │                   │
│              │  │Native │Separate│ Post  │              │                   │
│              │  └───────┴───────┴───────┘              │                   │
│              └──────────────────────────────────────────┘                   │
│                            │                                                 │
│           ┌────────────────┼────────────────┐                               │
│           ▼                ▼                ▼                               │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│   │   Unified   │  │   Visual +  │  │   Visual +  │                        │
│   │   Prompt    │  │ Suno Prompt │  │ Post Guide  │                        │
│   │ (V+A 통합)  │  │   (분리)    │  │   (후처리)  │                        │
│   └─────────────┘  └─────────────┘  └─────────────┘                        │
│           │                │                │                               │
│           └────────────────┼────────────────┘                               │
│                            ▼                                                 │
│              ┌──────────────────────────────────────────┐                   │
│              │        Platform-Specific Formatter       │                   │
│              │   ┌───────┬───────┬───────┬───────┐     │                   │
│              │   │  Veo  │ Kling │ Sora  │Runway │     │                   │
│              │   └───────┴───────┴───────┴───────┘     │                   │
│              └──────────────────────────────────────────┘                   │
│                            │                                                 │
│                            ▼                                                 │
│              ┌──────────────────────────────────────────┐                   │
│              │   Output: PlatformPromptPack             │                   │
│              │   - visual_prompt: str                   │                   │
│              │   - audio_strategy: AudioStrategy        │                   │
│              │   - platform: str                        │                   │
│              │   - estimated_quality: float             │                   │
│              └──────────────────────────────────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 플랫폼 가이드 수집 |
| 2026-01-17 | Part 9/10 기술 연계 (Native Audio 프롬프트 통합) | 완료 | 플랫폼별 템플릿 구현 |
| 2026-01-17 | 웹 리서치 완료 | 완료 | 프롬프트 구조 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### 2026 AI 비디오 프롬프트 엔지니어링 핵심 발견

#### 1. 프롬프트 4대 필수 요소 (Kling AI 공식 가이드)

```yaml
prompt_structure:
  subject: "비디오의 주요 초점 (캐릭터, 생물, 오브젝트)"
  action: "주체가 수행하는 동작"
  context: "장소, 환경, 시간대 등 배경 정보"
  style: "전체적인 시각 미학 (장르, 톤, 포맷)"

# 예시
prompt_example: |
  Subject: A weary detective in a rumpled coat
  Action: slowly walking through
  Context: a rain-soaked alley at midnight, neon signs reflecting in puddles
  Style: film noir, gritty realism, handheld camera
```

#### 2. Veo 3 프롬프팅 최적 패턴 (2025 연구 기반)

```yaml
veo3_best_practices:
  front_loading: "중요한 요소를 프롬프트 앞부분에 배치 (가중치 높음)"

  one_action_rule: "프롬프트당 하나의 액션만 (복수 액션 = 혼란)"

  specificity_over_creativity:
    bad: "Walking sadly"
    good: "Shuffling with hunched shoulders, eyes downcast"

  audio_cues: "Native Audio 프롬프트는 필수 (영상 현실감 극대화)"

  camera_movements_that_work:
    - "Slow push/pull (dolly in/out)"
    - "Orbit around subject"
    - "Handheld follow"
    - "Static with subject movement"

  avoid:
    - "Complex combinations ('pan while zooming during a dolly')"
    - "Unmotivated movements"
    - "Multiple focal points"

  style_references:
    - "Shot on [specific camera] (예: 'Shot on ARRI Alexa')"
    - "[Director name] style (예: 'Christopher Nolan style')"
    - "[Movie] cinematography (예: 'Blade Runner 2049 cinematography')"
```

#### 3. Kling 2.6 Lip Sync 프롬프트 패턴

```yaml
kling_lip_sync:
  script_format: |
    Beat 0-4s: Slow motion, character walks toward camera
    Beat 4s: EXPLOSION of color, rapid zoom (synced to bass drop)
    Beat 8s: Character lip syncs vocal line

  dialogue_format: |
    Beat 5-8s: Close up. Detective (Male, Weary): "I don't believe in coincidences."

  tone_descriptors:
    - "(whispering)"
    - "(shouting)"
    - "(breathy)"
    - "(resigned)"

  negative_prompts:
    audio: "No background music, no mumble, no overlapping speech, no distortion"
    visual: "No text overlay, no watermark, no lens flare"
```

#### 4. Native Audio 프롬프트 통합 패턴

```yaml
native_audio_prompt_templates:
  veo_comprehensive: |
    [Visual Description]
    + [Dialogue with speaker tags]
    + [Ambient sounds]
    + [Emotional mood]
    + "No subtitles" (자동 자막 방지)

  kling_musical: |
    [Visual Description]
    + [Voice/Performance Style]
    + [Audio Mood]
    + Beat timestamps

  sora_action: |
    [Visual Description]
    + [SFX descriptions]
    + [Dialogue if any]
```

#### 5. Crebit 공식 지원 모델 프롬프트 가이드 (3개)

```yaml
# ============================================================
# Crebit은 다음 3개 모델만 공식 지원
# ============================================================

veo_31_prompting:
  name: "Google Veo 3.1"
  use_case: "대화/나레이션 중심 바이럴 영상"

  prompt_structure: |
    [Visual Description - 구체적 장면 묘사]
    [Dialogue]: Speaker (Tone): "대사 내용"
    [Ambient]: 환경음 묘사
    [Mood]: 감정적 톤
    "No subtitles."

  example: |
    A young woman in a cozy coffee shop, warm afternoon light through windows.
    Close-up shot, shallow depth of field.
    [Dialogue]: Woman (excited, whispering): "I finally figured it out!"
    [Ambient]: Soft cafe chatter, espresso machine hissing
    [Mood]: Intimate, revelatory
    No subtitles.

  tips:
    - "대화는 3-5초로 짧게 유지"
    - "톤 지시어 필수: (whispering), (excited), (calm)"
    - "'No subtitles' 항상 추가"

kling_26_prompting:
  name: "Kling 2.6"
  use_case: "고화질 음성 없는 영상 (특히 추천)"

  prompt_structure: |
    [Subject]: 주체 상세 묘사
    [Action]: 동작 묘사
    [Context]: 환경, 시간, 조명
    [Style]: 시각 스타일
    [Camera]: 카메라 움직임

  example: |
    Subject: A lone samurai in weathered armor
    Action: Walking slowly through a bamboo forest
    Context: Golden hour, mist rising from the ground, autumn leaves falling
    Style: Cinematic, Kurosawa-inspired, high contrast
    Camera: Slow tracking shot, following from behind

  tips:
    - "음성 없이 시각에 집중"
    - "카메라 움직임 구체적 지정"
    - "2분까지 가능 - 긴 씬에 최적"
    - "물리적 모션에 강점"

sora_max_2pro_prompting:
  name: "Sora Max 2 Pro"
  use_case: "애니메이션 스타일 영상"

  prompt_structure: |
    [Style]: Animation style specification
    [Character]: 캐릭터 상세 묘사 (일관성 위해 상세히)
    [Scene]: 장면 묘사
    [Action]: 동작
    [Mood]: 분위기

  example: |
    Style: Studio Ghibli-inspired hand-drawn animation, soft watercolor backgrounds
    Character: A young girl with short black hair, red ribbon, blue dress
    Scene: Flying on a broomstick over a European coastal town at sunset
    Action: Looking down at the tiny houses below with wonder
    Mood: Magical, nostalgic, adventurous

  tips:
    - "스타일 레퍼런스 명시 ('Ghibli', 'Pixar', 'Anime')"
    - "캐릭터 묘사 일관되게 반복"
    - "감정/분위기 키워드 중요"

# ============================================================
# 자동 프롬프트 최적화 로직
# ============================================================
prompt_optimization:
  for_veo_31:
    add_if_missing: ["No subtitles", "Ambient sound"]
    dialogue_format: "[Speaker] (tone): \"text\""
    max_dialogue_duration: "5 seconds"

  for_kling_26:
    remove: ["dialogue", "speech", "talking"]  # 음성 관련 제거
    emphasize: ["visual", "camera movement", "lighting"]
    add: ["cinematic", "high quality"]

  for_sora_max_2pro:
    add_if_missing: ["animation style"]
    character_consistency: "repeat character description each prompt"
```

#### 6. 프롬프트 품질 향상 핵심 인사이트

```yaml
quality_insights:
  identity_consistency: |
    각 생성마다 캐릭터 정체성 재강조 필요
    - 의상 색상
    - 헤어스타일
    - 핵심 소품

  camera_anchoring: |
    영상이 불안정할 때 "on tripod" 추가로 안정화

  unwanted_text_prevention: |
    "No subtitles", "No text overlay" 명시

  prompt_iteration_strategy:
    1. "Fast/Turbo 모드로 프롬프트 검증"
    2. "Seed 파라미터로 스타일 고정 후 변형 탐색"
    3. "4초, 720p로 시작 → 검증 후 확장"
```

### Sources
- Skywork AI: 18 Best Veo 3 Prompts (2025)
- Leonardo.AI: Kling AI Prompt Guide
- fal.ai: Veo3 Prompt Guide
- Medium: How to Control Next-Gen Video AI
- Reddit r/PromptEngineering: Veo 3 Prompting Guide
- Artificial Analysis Video Arena Leaderboard (Dec 2025)
