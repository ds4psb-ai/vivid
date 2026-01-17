# App 5.1: 미학 디렉터 (Aesthetic Director) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: AD (Aesthetic Direction)

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/aesthetic.py"

# 현재 엔드포인트
endpoints = [
    "POST /dimension/ad/analyze",
    "POST /dimension/ad/analyze/stream",
    "POST /dimension/ad/apply",
    "POST /dimension/ad/apply/stream",
]

# 현재 기능
current_features = [
    "거장 스타일 분석",
    "미학적 방향성 제안",
    "기본 스타일 가이드 생성",
]

# 목표 기능 (고도화)
target_features = [
    "거장 DNA 상세 분석 시스템",
    "수학적 미학 원칙 적용",
    "통합 스타일 가이드 생성",
    "모든 앱에 스타일 전파",
    "거장 융합 스타일 생성",
    "시각-청각-서사 통합 미학",
]
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| 거장 DNA 데이터 부족 | 피상적 분석 | 심층 거장 연구 DB 구축 |
| 수학적 원칙 미적용 | 직관적 판단에 의존 | 황금비/삼분할 등 정량화 |
| 앱 간 스타일 전파 없음 | 일관성 부재 | 통합 스타일 가이드 시스템 |
| 시각-청각 연동 약함 | 분절된 미학 | 통합 미학 프레임워크 |

---

## 2. 핵심 연구 주제

### 2.1 거장 DNA 심층 연구

**연구 질문**:
- 각 거장의 핵심 미학적 철학은?
- 거장의 시그니처 기법을 정량화할 수 있는가?
- 거장 스타일 융합의 규칙은?

**조사 대상**:
1. 거장 전기/인터뷰/마스터클래스
2. 작품 분석 학술 연구
3. 비평가 분석 종합

### 2.2 수학적 미학 연구

**연구 질문**:
- 황금비가 영상 구도에 미치는 영향은?
- 색채 이론의 수학적 원칙은?
- 음악-영상 동기화의 수학적 모델은?

**조사 대상**:
1. 황금비 (Φ = 1.618) 적용 연구
2. 색채 조화 이론 (Itten, Albers)
3. BPM-감정 수학적 모델

### 2.3 통합 미학 프레임워크 연구

**연구 질문**:
- 시각/청각/서사 미학의 통합 원칙은?
- 일관된 미학적 언어 체계 설계는?
- 모든 앱에 전파 가능한 스타일 가이드 형식은?

**조사 대상**:
1. 통합 예술 이론 (Gesamtkunstwerk)
2. 브랜드 스타일 가이드 시스템
3. 영화 프로덕션 디자인 문서

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: auteur_dna_deep_profiles

```yaml
id: auteur_dna_deep_profiles
description: "거장 DNA 심층 프로필 - 모든 미학적 차원 포함"
source: "전기, 인터뷰, 작품 분석, 비평"
size: ~50 documents

schema:
  auteur_key:
    type: string
    example: "bong_joon_ho"

  name_ko:
    type: string

  name_en:
    type: string

  core_philosophy:
    type: object
    schema:
      artistic_vision: string
      recurring_themes: list[string]
      worldview: string
      key_quotes: list[string]

  visual_dna:
    type: object
    schema:
      composition_signature:
        preferred_ratios: list[string]  # "golden_ratio", "symmetry", "asymmetric_tension"
        framing_patterns: list[string]
        depth_usage: string
      color_philosophy:
        palette_type: string  # "muted", "saturated", "naturalistic"
        signature_colors: list[string]
        color_symbolism: dict[string, string]
      lighting_approach:
        primary_style: string
        key_to_fill_ratio: string
        signature_techniques: list[string]
      camera_language:
        preferred_movements: list[string]
        typical_lens_choices: list[string]
        pacing_tendency: string

  audio_dna:
    type: object
    schema:
      music_philosophy: string
      preferred_composers: list[string]
      silence_usage: string
      diegetic_vs_nondiegetic: string
      signature_audio_motifs: list[string]

  narrative_dna:
    type: object
    schema:
      structure_preference: string
      character_depth: string
      dialogue_style: string
      subtext_density: string
      ending_philosophy: string

  production_patterns:
    type: object
    schema:
      prep_methodology: string
      on_set_style: string
      collaboration_approach: string
      revision_philosophy: string

  influences:
    type: list[object]
    schema:
      influence_name: string
      influence_type: string
      specific_elements: list[string]

  evolution:
    type: list[object]
    schema:
      period: string
      characteristics: string
      key_works: list[string]

  compatibility_matrix:
    type: dict[string, float]
    description: "다른 거장과의 스타일 융합 호환성"

# 예시 거장 DNA
auteur_dna_examples:
  - auteur_key: "bong_joon_ho"
    name_ko: "봉준호"
    core_philosophy:
      artistic_vision: "장르적 오락성과 사회 비평의 완벽한 결합"
      recurring_themes: ["class_divide", "family_dynamics", "moral_ambiguity", "systemic_violence"]
      worldview: "시스템이 개인을 어떻게 형성하고 파괴하는가에 대한 탐구"
      key_quotes:
        - "가장 개인적인 것이 가장 창의적이다"
        - "장르는 도구이지 족쇄가 아니다"
    visual_dna:
      composition_signature:
        preferred_ratios: ["golden_ratio", "vertical_thirds"]
        framing_patterns: ["layered_depth", "frame_within_frame", "symmetry_with_tension"]
        depth_usage: "전경-중경-후경에 사회적 계층 배치"
      color_philosophy:
        palette_type: "muted_with_selective_saturation"
        signature_colors: ["desaturated_green", "warm_yellow", "cold_blue"]
        color_symbolism:
          green_yellow: "부패, 썩어가는 것"
          warm_light: "희망의 가능성"
          cold_blue: "시스템의 냉혹함"
      lighting_approach:
        primary_style: "naturalistic_dramatic"
        key_to_fill_ratio: "3:1 to 5:1"
        signature_techniques: ["window_light", "practical_motivated", "shadow_symbolism"]
      camera_language:
        preferred_movements: ["slow_deliberate_dolly", "observational_pan", "static_tableau"]
        typical_lens_choices: ["35mm", "40mm", "50mm"]
        pacing_tendency: "methodical_with_sudden_bursts"
    audio_dna:
      music_philosophy: "음악은 감정을 조작하지 말고 동반해야 한다"
      preferred_composers: ["정재일"]
      silence_usage: "긴장의 축적을 위해 전략적 활용"
      signature_audio_motifs: ["ambient_class_sounds", "ironic_juxtaposition"]
    narrative_dna:
      structure_preference: "classical_three_act_with_subversion"
      character_depth: "archetypes_with_complexity"
      dialogue_style: "naturalistic_with_dark_wit"
      subtext_density: "high"
      ending_philosophy: "closure_with_lingering_questions"
    compatibility_matrix:
      fincher: 0.75
      nolan: 0.60
      tarantino: 0.45
      wong_kar_wai: 0.50
      miyazaki: 0.30

  - auteur_key: "wong_kar_wai"
    name_ko: "왕가위"
    core_philosophy:
      artistic_vision: "시간, 기억, 그리움의 시적 탐구"
      recurring_themes: ["unrequited_love", "urban_loneliness", "memory_nostalgia", "time_passage"]
    visual_dna:
      composition_signature:
        preferred_ratios: ["off_center", "negative_space"]
        framing_patterns: ["reflections", "obstructed_views", "close_intimacy"]
      color_philosophy:
        palette_type: "saturated_neon_expressionist"
        signature_colors: ["electric_blue", "neon_red", "golden_yellow"]
      lighting_approach:
        primary_style: "expressionistic_neon"
        signature_techniques: ["neon_practicals", "color_gels", "silhouette"]
      camera_language:
        preferred_movements: ["handheld_intimate", "step_printing", "undercranking"]
        pacing_tendency: "languid_dreamlike"
```

### 3.2 데이터셋: mathematical_aesthetics

```yaml
id: mathematical_aesthetics
description: "수학적 미학 원칙 및 적용 가이드"
source: "미학 이론, 수학, 인지과학"
size: ~40 documents

schema:
  principle_id:
    type: string
    example: "golden_ratio"

  principle_name:
    type: string
    example: "황금비"

  category:
    type: string
    enum: ["composition", "color", "timing", "audio", "typography"]

  mathematical_basis:
    type: object
    schema:
      formula: string
      value: float
      derivation: string

  perceptual_effect:
    type: string
    description: "인지적/감정적 효과"

  application_domains:
    type: list[object]
    schema:
      domain: string  # "framing", "color_harmony", "music_timing"
      how_to_apply: string
      examples: list[string]

  visual_implementation:
    type: object
    schema:
      prompt_keywords: list[string]
      composition_guide: string
      measurement_points: list[string]

  auteur_usage:
    type: list[object]
    schema:
      auteur_key: string
      usage_pattern: string
      example_work: string

# 예시 수학적 원칙
mathematical_principles:
  - principle_id: "golden_ratio"
    principle_name: "황금비 (Φ)"
    category: "composition"
    mathematical_basis:
      formula: "Φ = (1 + √5) / 2"
      value: 1.618033988749
      derivation: "피보나치 수열의 극한비"
    perceptual_effect: "자연스러운 균형감, 시각적 편안함, 유기적 조화"
    application_domains:
      - domain: "framing"
        how_to_apply: "프레임을 Φ:1 비율로 분할하여 주요 피사체 배치"
        examples:
          - "얼굴 클로즈업에서 눈의 위치를 상단 황금선에"
          - "와이드 샷에서 수평선을 하단 황금선에"
      - domain: "spiral_composition"
        how_to_apply: "피보나치 나선을 따라 시선 유도"
        examples:
          - "액션 동선을 나선 형태로 배치"
          - "시선 흐름을 나선 중심으로 수렴"
    visual_implementation:
      prompt_keywords: ["golden ratio composition", "fibonacci spiral", "phi grid framing"]
      composition_guide: "프레임을 1.618 비율로 분할, 교차점에 관심점 배치"
      measurement_points: ["0.382", "0.618"]  # 프레임 내 비율 위치
    auteur_usage:
      - auteur_key: "kubrick"
        usage_pattern: "기하학적 구도에서 황금비 변형 활용"
        example_work: "The Shining - 복도 구도"

  - principle_id: "rule_of_thirds"
    principle_name: "삼분할 법칙"
    category: "composition"
    mathematical_basis:
      formula: "프레임을 가로 3등분, 세로 3등분 (9개 영역)"
      value: 0.333
      derivation: "황금비의 단순화된 근사"
    perceptual_effect: "역동적 균형, 시각적 흥미, 자연스러운 프레이밍"
    application_domains:
      - domain: "framing"
        how_to_apply: "주요 피사체를 교차점 또는 선 위에 배치"
    visual_implementation:
      prompt_keywords: ["rule of thirds", "off-center composition", "thirds grid"]

  - principle_id: "color_wheel_harmony"
    principle_name: "색상환 조화"
    category: "color"
    mathematical_basis:
      formula: "360° / n (n = 조화 유형에 따른 분할)"
      value: null
      derivation: "색상환에서의 각도 관계"
    application_domains:
      - domain: "complementary"
        how_to_apply: "180° 대비색 사용 (빨강-청록, 파랑-주황)"
      - domain: "triadic"
        how_to_apply: "120° 간격의 3색 사용"
      - domain: "analogous"
        how_to_apply: "30° 이내 인접색 사용"

  - principle_id: "bpm_emotion_curve"
    principle_name: "BPM-감정 곡선"
    category: "audio"
    mathematical_basis:
      formula: "E(bpm) = a * log(bpm) + b * valence + c"
      derivation: "2025 EEG 연구 기반 모델"
    application_domains:
      - domain: "emotional_pacing"
        how_to_apply: "씬의 감정 강도에 따라 BPM 매핑"
        examples:
          - "긴장 고조: 60→140 BPM 상승"
          - "감정적 휴식: 80 BPM 유지"
```

### 3.3 데이터셋: integrated_style_guide_templates

```yaml
id: integrated_style_guide_templates
description: "통합 스타일 가이드 템플릿 - 모든 앱에 전파"
source: "프로덕션 디자인 문서, 브랜드 가이드"
size: ~20 documents

schema:
  template_id:
    type: string
    example: "full_production_guide"

  template_name:
    type: string

  sections:
    type: list[object]
    schema:
      section_id: string
      section_name: string
      target_apps: list[string]
      content_schema: object

  output_formats:
    type: list[string]
    example: ["json", "pdf", "markdown"]

  propagation_rules:
    type: object
    schema:
      automatic_update: bool
      override_allowed: bool
      version_tracking: bool

# 통합 스타일 가이드 구조
style_guide_structure:
  template_id: "vivid_production_style_guide"
  template_name: "Vivid 프로덕션 스타일 가이드"
  sections:
    - section_id: "core_identity"
      section_name: "핵심 아이덴티티"
      target_apps: ["all"]
      content_schema:
        auteur_reference: string
        fusion_ratio: dict[string, float]  # 거장 융합 비율
        overall_tone: string
        thematic_pillars: list[string]

    - section_id: "visual_language"
      section_name: "시각 언어"
      target_apps: ["storyboard", "visual_realizer", "video_maker", "prompt_alchemy"]
      content_schema:
        composition:
          primary_ratio: string
          framing_rules: list[string]
          depth_approach: string
        color:
          primary_palette: list[string]
          accent_colors: list[string]
          mood_mapping: dict[string, string]
        lighting:
          primary_style: string
          key_ratio: string
          signature_techniques: list[string]
        camera:
          movement_vocabulary: list[string]
          lens_preferences: list[string]
          pacing_guide: string

    - section_id: "audio_language"
      section_name: "청각 언어"
      target_apps: ["sound_crafter", "video_maker"]
      content_schema:
        music:
          bpm_range: object
          key_preferences: list[string]
          instrument_palette: list[string]
          composer_reference: string
        sound_design:
          ambient_approach: string
          sfx_philosophy: string
          silence_usage: string

    - section_id: "narrative_language"
      section_name: "서사 언어"
      target_apps: ["scenario_generator", "story_architect"]
      content_schema:
        structure: string
        pacing: string
        dialogue_style: string
        subtext_level: string
        emotional_arc: string

    - section_id: "character_consistency"
      section_name: "캐릭터 일관성"
      target_apps: ["storyboard", "visual_realizer", "video_maker"]
      content_schema:
        character_sheets: list[object]
        consistency_method: string
        expression_vocabulary: list[string]
        costume_guide: object

    - section_id: "quality_standards"
      section_name: "품질 기준"
      target_apps: ["quality_director"]
      content_schema:
        technical_thresholds: dict[string, float]
        aesthetic_priorities: list[string]
        deal_breakers: list[string]
        auteur_checkpoints: list[string]
```

### 3.4 데이터셋: auteur_fusion_rules

```yaml
id: auteur_fusion_rules
description: "거장 스타일 융합 규칙"
source: "스타일 분석, 융합 실험"
size: ~30 documents

schema:
  fusion_id:
    type: string
    example: "bong_nolan_fusion"

  primary_auteur:
    type: string

  secondary_auteur:
    type: string

  compatibility_score:
    type: float

  fusion_approach:
    type: object
    schema:
      visual_blend: string
      narrative_blend: string
      audio_blend: string
      recommended_ratio: string

  preserved_elements:
    type: list[object]
    schema:
      from_auteur: string
      element: string
      reason: string

  conflict_resolution:
    type: list[object]
    schema:
      conflicting_element: string
      resolution_strategy: string

  resulting_style:
    type: object
    schema:
      name: string
      description: string
      best_for: list[string]

# 예시 융합 규칙
fusion_rules:
  - fusion_id: "bong_nolan_fusion"
    primary_auteur: "bong_joon_ho"
    secondary_auteur: "nolan"
    compatibility_score: 0.75
    fusion_approach:
      visual_blend: "봉준호의 계층적 프레이밍 + 놀란의 IMAX 스케일"
      narrative_blend: "봉준호의 사회 비평 + 놀란의 시간 조작"
      audio_blend: "절제된 음악 사용, 전략적 침묵"
      recommended_ratio: "60:40"
    preserved_elements:
      - from_auteur: "bong_joon_ho"
        element: "class_commentary"
        reason: "핵심 주제적 깊이"
      - from_auteur: "nolan"
        element: "temporal_complexity"
        reason: "구조적 흥미"
    conflict_resolution:
      - conflicting_element: "color_palette"
        resolution_strategy: "봉준호의 뮤트 톤 기반, 놀란의 차가운 블루 악센트"
    resulting_style:
      name: "사회적 시간여행"
      description: "계급 구조를 시간 조작을 통해 탐구하는 복잡한 서사"
      best_for: ["social_thriller", "time_drama"]
```

---

## 4. 기능 고도화 설계

### 4.1 통합 미학 디렉션 파이프라인

```yaml
aesthetic_director_pipeline:
  stage_1_auteur_analysis:
    purpose: "거장 DNA 분석 및 융합 설계"
    inputs:
      - primary_auteur_key
      - secondary_auteur_key (optional)
      - project_concept
    outputs:
      - auteur_dna: AuteurDNA
      - fusion_guide: FusionGuide (if applicable)
    rag_queries:
      - "auteur_dna_deep_profiles → 거장 프로필"
      - "auteur_fusion_rules → 융합 규칙 (해당 시)"
    logic:
      - "거장 DNA 로드"
      - "프로젝트 컨셉과 매칭"
      - "융합 시 호환성 및 규칙 적용"

  stage_2_mathematical_calibration:
    purpose: "수학적 미학 원칙 적용"
    inputs:
      - auteur_dna
      - project_requirements
    outputs:
      - mathematical_guides: dict[principle, application]
    rag_queries:
      - "mathematical_aesthetics → 적용 가능 원칙"
    logic:
      - "구도: 황금비/삼분할 적용 가이드"
      - "색채: 색상환 조화 가이드"
      - "타이밍: BPM-감정 매핑"

  stage_3_style_guide_generation:
    purpose: "통합 스타일 가이드 생성"
    inputs:
      - auteur_dna
      - mathematical_guides
      - project_parameters
    outputs:
      - integrated_style_guide: StyleGuide
    rag_queries:
      - "integrated_style_guide_templates → 템플릿"
    logic:
      - "모든 섹션(시각/청각/서사) 생성"
      - "앱별 특화 가이드 추출"
      - "일관성 검증"

  stage_4_propagation:
    purpose: "모든 앱에 스타일 가이드 전파"
    inputs:
      - integrated_style_guide
    outputs:
      - app_specific_guides: dict[app_id, guide]
    logic:
      - "각 앱의 필요 섹션 추출"
      - "앱별 형식으로 변환"
      - "버전 관리 및 업데이트"
```

### 4.2 출력 스키마 설계

```python
class AestheticDirectorOutput(BaseModel):
    """미학 디렉터 출력 스키마"""

    # 메타데이터
    metadata: AestheticMetadata
    class AestheticMetadata(BaseModel):
        project_id: str
        primary_auteur: str
        secondary_auteur: str | None
        fusion_ratio: dict[str, float] | None
        version: str
        created_at: str

    # 거장 DNA 분석
    auteur_analysis: AuteurAnalysis
    class AuteurAnalysis(BaseModel):
        core_philosophy: str
        key_themes: list[str]
        visual_signature: VisualSignature
        audio_signature: AudioSignature
        narrative_signature: NarrativeSignature

        class VisualSignature(BaseModel):
            composition_rules: list[str]
            color_palette: dict[str, str]
            lighting_approach: str
            camera_vocabulary: list[str]

        class AudioSignature(BaseModel):
            music_philosophy: str
            preferred_bpm_range: tuple[int, int]
            silence_usage: str
            composer_reference: str

        class NarrativeSignature(BaseModel):
            structure_preference: str
            pacing_style: str
            subtext_density: str

    # 수학적 미학 적용
    mathematical_aesthetics: MathematicalApplication
    class MathematicalApplication(BaseModel):
        composition: CompositionMath
        color: ColorMath
        timing: TimingMath

        class CompositionMath(BaseModel):
            primary_ratio: str
            grid_system: str
            focal_points: list[str]

        class ColorMath(BaseModel):
            harmony_type: str
            primary_hues: list[int]  # 색상환 각도
            contrast_ratio: float

        class TimingMath(BaseModel):
            bpm_emotion_mapping: dict[str, int]
            pacing_formula: str

    # 통합 스타일 가이드
    style_guide: IntegratedStyleGuide
    class IntegratedStyleGuide(BaseModel):
        visual_language: dict
        audio_language: dict
        narrative_language: dict
        character_consistency: dict
        quality_standards: dict

    # 앱별 가이드
    app_specific_guides: AppGuides
    class AppGuides(BaseModel):
        scenario_generator: dict
        sound_crafter: dict
        storyboard_sketcher: dict
        prompt_alchemy: dict
        visual_realizer: dict
        video_maker: dict
        quality_director: dict

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 모든 앱과의 연동 (오케스트레이터 역할)

```
                                        ┌─────────────────┐
                                        │ 5.1 미학        │
                                        │     디렉터      │ ◄── 프로젝트 설정
                                        └────────┬────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
        ┌───────────┴───────────┐   ┌───────────┴───────────┐   ┌───────────┴───────────┐
        │   시각 언어 가이드    │   │   청각 언어 가이드    │   │   서사 언어 가이드    │
        └───────────┬───────────┘   └───────────┬───────────┘   └───────────┬───────────┘
                    │                            │                            │
        ┌───────────┼───────────┐                │                            │
        ▼           ▼           ▼                ▼                            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐     ┌─────────┐                   ┌─────────┐
   │스토리   │ │프롬프트 │ │비주얼   │     │사운드   │                   │시나리오 │
   │보드     │ │연금술   │ │리얼라   │     │크래프터 │                   │생성기   │
   │스케치   │ │         │ │이저    │     │         │                   │         │
   └────┬────┘ └────┬────┘ └────┬────┘     └────┬────┘                   └────┬────┘
        │           │           │                │                            │
        └───────────┴─────┬─────┴────────────────┴────────────────────────────┘
                          │
                          ▼
                    ┌───────────┐
                    │ 비디오    │
                    │ 메이커    │
                    └─────┬─────┘
                          │
                          ▼
                    ┌───────────┐       ┌─────────────────┐
                    │ 퀄리티    │ ◄──── │ 품질 기준 가이드 │ (from 미학 디렉터)
                    │ 디렉터    │       └─────────────────┘
                    └───────────┘
```

### 5.2 데이터 흐름

| 출력 | 대상 앱 | 가이드 내용 |
|------|---------|-------------|
| visual_language | 스토리보드, 프롬프트, 비주얼 | 구도, 색상, 조명, 카메라 |
| audio_language | 사운드 크래프터 | BPM, 악기, 음악 스타일 |
| narrative_language | 시나리오 생성기 | 구조, 페이싱, 대사 스타일 |
| character_consistency | 스토리보드, 비주얼, 비디오 | 캐릭터 시트, 일관성 규칙 |
| quality_standards | 퀄리티 디렉터 | 평가 기준, 거장 체크포인트 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 거장 DNA 조사

- [ ] 봉준호 심층 DNA 분석
- [ ] 놀란 심층 DNA 분석
- [ ] 왕가위 심층 DNA 분석
- [ ] 미야자키 하야오 심층 DNA 분석
- [ ] 타란티노 심층 DNA 분석
- [ ] 핀처 심층 DNA 분석
- [ ] 드니 빌뇌브 심층 DNA 분석

### 6.2 수학적 미학 조사

- [ ] 황금비 적용 연구 정리
- [ ] 색채 조화 이론 정리
- [ ] BPM-감정 수학 모델
- [ ] 페이싱 수학 공식

### 6.3 통합 가이드 조사

- [ ] 영화 프로덕션 디자인 문서 분석
- [ ] 브랜드 스타일 가이드 벤치마킹
- [ ] 앱 간 데이터 전파 시스템 설계

### 6.4 융합 규칙 조사

- [ ] 거장 간 호환성 매트릭스
- [ ] 스타일 융합 성공 사례 분석
- [ ] 충돌 해결 전략 정립

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 거장 DNA 심층 분석 | 4일 | DNA 프로필 10+ |
| 2 | 수학적 미학 정리 | 2일 | 원칙 DB |
| 3 | 통합 가이드 설계 | 2일 | 템플릿 |
| 4 | 융합 규칙 정립 | 2일 | 융합 매트릭스 |
| 5 | 파이프라인 구현 | 3일 | 코드 |
| 6 | 앱 전파 시스템 | 2일 | 전파 시스템 |
| 7 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 학술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| 황금비와 예술 | 저서 | 수학적 미학 원칙 |
| 색채의 예술 (Itten) | 저서 | 색채 조화 이론 |
| 영화 미학 | 학술서 | 영화 미학 이론 |

### 거장 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| 봉준호 마스터클래스 | 강의 | 연출 철학 |
| 놀란 인터뷰 모음 | 인터뷰 | 시간 구조 접근 |
| 왕가위 비하인드 | 다큐 | 시각 스타일 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| Coolors | https://coolors.co/ | 색상 조화 도구 |
| Phi Calculator | 온라인 | 황금비 계산 |

---

## 9. Part 9/10 기술 연계 (2026 보강)

### 9.1 NotebookLM Tier0 (거장 DNA) 핵심 연동

미학 디렉터는 **AUTEUR_DNA RAG 소스**의 핵심 소비자입니다.

```yaml
notebooklm_integration:
  purpose: "거장의 미학 원칙을 정밀하게 검색하고 적용"

  auteur_dna_queries:
    visual_style:
      query_pattern: "{auteur_key}의 시각적 특징"
      retrieval_fields:
        - "composition_rules: 구도 원칙"
        - "color_philosophy: 색채 철학"
        - "lighting_signature: 조명 시그니처"
        - "lens_preferences: 렌즈 선호도"

    narrative_style:
      query_pattern: "{auteur_key}의 서사 철학"
      retrieval_fields:
        - "structure_patterns: 구조 패턴"
        - "pacing_style: 페이싱 스타일"
        - "thematic_obsessions: 주제적 집착"

    audio_style:
      query_pattern: "{auteur_key}의 사운드 디자인"
      retrieval_fields:
        - "music_preferences: 음악 선호"
        - "silence_usage: 침묵 활용"
        - "sfx_philosophy: 효과음 철학"

  evidence_generation:
    format: "rag:auteur_dna:{auteur_key}:{aspect}:{detail_id}"
    example: "rag:auteur_dna:bong:visual:staircase_symbolism"
```

### 9.2 Multi-RAG Router 최적 활용

미학 가이드 생성 시 **다중 소스 융합**을 수행합니다.

```yaml
multi_rag_orchestration:
  query_type: "aesthetic_guide_generation"

  source_routing:
    primary_auteur:
      source: "AUTEUR_DNA (NotebookLM)"
      weight: 0.50
      query: "봉준호 미학 원칙"

    secondary_auteur:
      source: "AUTEUR_DNA (NotebookLM)"
      weight: 0.30
      query: "왕가위 색감 원칙"
      condition: "블렌딩 요청 시"

    mathematical_aesthetics:
      source: "MULTIMODAL_DIMENSION (Qdrant)"
      weight: 0.15
      collection: "aesthetic_principles"
      query: "황금비 구도 법칙"

    user_preference:
      source: "USER_HISTORY (PostgreSQL)"
      weight: 0.05
      query: "이전 작업 스타일 선호"

  rrf_fusion:
    method: "Reciprocal Rank Fusion"
    output: "통합된 미학 가이드 + evidence_refs"
```

### 9.3 스타일 가이드 전파 시스템

미학 가이드를 다른 앱에 **일관되게 전파**합니다.

```yaml
style_propagation:
  output_format:
    visual_language:
      recipients: ["storyboard_sketcher", "prompt_alchemy", "visual_realizer"]
      data:
        - "composition_rules: list[str]"
        - "color_palette: list[hex]"
        - "lighting_mood: str"
        - "camera_style: str"

    audio_language:
      recipients: ["sound_crafter", "prompt_alchemy"]
      data:
        - "music_genre: str"
        - "bpm_range: tuple[int, int]"
        - "instrument_preferences: list[str]"
        - "silence_strategy: str"

    narrative_language:
      recipients: ["scenario_generator"]
      data:
        - "pacing_curve: str"
        - "structure_preference: str"
        - "thematic_elements: list[str]"

    quality_standards:
      recipients: ["quality_director"]
      data:
        - "auteur_checkpoints: list[str]"
        - "minimum_scores: dict[str, float]"
        - "style_violation_flags: list[str]"

  tiered_context_storage:
    level: "session"
    key: "aesthetic_guide"
    access: "all apps via ctx.resolve()"
```

### 9.4 거장 스타일 블렌딩 엔진

```yaml
style_blending_engine:
  purpose: "2명 이상의 거장 스타일 수학적 융합"

  blend_algorithm:
    method: "weighted_vector_interpolation"
    steps:
      - "각 거장 스타일을 벡터로 표현 (768D Gemini embedding)"
      - "가중치 기반 벡터 보간"
      - "융합된 벡터에서 가장 가까운 특성 추출"

  conflict_resolution:
    strategy: "primary_wins"
    rules:
      - "color: primary 거장의 팔레트 + secondary 악센트"
      - "composition: primary 규칙 우선, secondary로 변형"
      - "pacing: 가중 평균"

  blend_presets:
    bong_wong:
      name: "사회적 감성"
      primary: "bong (0.6)"
      secondary: "wong (0.4)"
      characteristics:
        - "봉준호의 사회적 시선"
        - "왕가위의 색감과 질감"

    nolan_villeneuve:
      name: "시간의 장엄함"
      primary: "nolan (0.6)"
      secondary: "villeneuve (0.4)"
      characteristics:
        - "놀란의 시간 구조"
        - "빌뇌브의 시각적 스케일"
```

### 9.5 수정된 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                Aesthetic Director V2 + Multi-RAG Fusion                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Input: Auteur Selection, Blend Request, Project Context                     │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                   Multi-RAG Router                          │            │
│  │   ┌──────────────┬────────────────┬───────────────┐        │            │
│  │   │ NotebookLM   │   Qdrant       │  PostgreSQL   │        │            │
│  │   │ AUTEUR_DNA   │   AESTHETICS   │  USER_HISTORY │        │            │
│  │   │   (50%)      │     (15%)      │     (5%)      │        │            │
│  │   └──────────────┴────────────────┴───────────────┘        │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                   RRF Fusion Engine                         │            │
│  │   - 다중 소스 결과 융합                                      │            │
│  │   - evidence_refs 생성                                      │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                   Style Blending Engine                     │            │
│  │   - 벡터 보간 블렌딩                                         │            │
│  │   - 충돌 해결                                                │            │
│  │   - 프리셋 적용                                              │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                  Aesthetic Guide Output                     │            │
│  │   - visual_language → Storyboard, Prompt, Visual           │            │
│  │   - audio_language → Sound Crafter, Prompt                 │            │
│  │   - narrative_language → Scenario Generator                │            │
│  │   - quality_standards → Quality Director                   │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                  TieredContext (Session)                    │            │
│  │   ctx.set_session("aesthetic_guide", guide)                │            │
│  │   → 모든 앱에서 ctx.resolve()로 접근 가능                   │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 거장 DNA 심층 분석 |
| 2026-01-17 | Part 9/10 기술 연계 (NotebookLM Tier0, Multi-RAG, 스타일 블렌딩) | 완료 | 블렌딩 프리셋 구현 |
| 2026-01-17 | 웹 리서치 완료 (Auteur Theory, AI Color Grading) | 완료 | 스타일 시스템화 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### 거장 DNA 및 AI 색채 이론 종합 분석

#### 1. Auteur Theory 핵심 개념 (Andrew Sarris 정의)

```yaml
auteur_theory_3_components:
  technical_competence:
    definition: "기술적 영화 제작 능력의 최고 수준"
    elements:
      - "촬영 기법 숙달"
      - "편집 능력"
      - "조명/색상 제어"

  distinguishable_personality:
    definition: "다른 감독과 구분되는 독특한 개성과 스타일"
    markers:
      - "반복되는 촬영 기법"
      - "일관된 테마 탐구"
      - "시그니처 시각 요소"

  interior_meaning:
    definition: "표면적 스토리를 넘어선 깊은 의미와 질문"
    aspects:
      - "인간 존재에 대한 질문"
      - "뉘앙스있는 테마 탐구"
      - "상징주의와 메타포"
```

#### 2. Directors DNA® 개념 (Velro.ai)

```yaml
directors_dna_system:
  concept: "감독의 미학적 선택을 재사용 가능한 프리셋으로 코드화"

  captured_elements:
    camera_package: "카메라 + 렌즈 조합"
    lens_character: "렌즈 특성 (anamorphic, spherical, etc.)"
    film_stock: "필름 스톡 에뮬레이션"
    lighting_approach: "조명 철학"
    color_palette: "색상 팔레트"

  workflow:
    1. "스타일 탐색: 다양한 조합 테스트"
    2. "프리셋 저장: Directors DNA로 저장"
    3. "원클릭 적용: 새 프로젝트에 즉시 적용"

  quote: |
    "I spent six months using Velro to develop my visual style.
    Now I have a library of Directors DNA presets that define my work.
    Clients hire me specifically for that aesthetic."
    - Elena Vasquez, Commercial Director
```

#### 3. AI Color Grading 도구 현황 (2025)

```yaml
ai_color_grading_tools:
  colourlab_ai:
    features:
      - "AI-Powered Color Matching: 다중 카메라 footage 자동 매칭"
      - "Neural Looks: AI 기반 창의적 룩"
      - "Auto Balance: 자동 화이트 밸런스"
    integration: "DaVinci Resolve, Premiere Pro (OFX plugins)"
    use_case: "전문 컬러리스트, 대량 footage 처리"

  lutbuilder_ai:
    features:
      - "AI-Powered LUT Generation: 즉각적인 전문 그레이드 생성"
      - "Advanced Color Matching: 조명/톤 분석 기반 LUT 생성"
    integration: "DaVinci Resolve, Premiere Pro, Final Cut"

  color_io:
    features:
      - "Analog Film Emulation: 필름 에뮬레이션 도구"
      - "Ultra-wide-gamut: 아날로그 색상 모델"
    use_case: "필름 룩, 시네마틱 정밀도"
```

#### 4. Algorithmic Auteur 프레임워크 (2025 학술 연구)

```yaml
algorithmic_auteur_framework:
  concept: "AI를 중립적 도구가 아닌 공동 창작자로 개념화"

  components:
    technical_architecture:
      - "ML, NLP, Computer Vision, GANs"
      - "가능한 출력의 영역을 규정"

    cultural_dataset:
      - "훈련 데이터 (텍스트, 이미지, 사운드)"
      - "문화적 가치와 편향이 내재"

  ai_in_production:
    cgi_automation: "로토스코핑, 컬러 그레이딩, 텍스처 생성"
    audio: "사운드 효과, 더빙, 음악 작곡"
    archival: "복원, 컬러화, 프레임 생성"

  key_insight: |
    AI는 형식적 제어와 서사적 명확성을 강화하지만,
    스타일적 변주와 모호성의 의도적 도입은
    여전히 인간 의사결정의 영역
```

#### 5. NotebookLM 활용 거장 지식베이스 (Tier0)

```yaml
notebooklm_auteur_kb:
  purpose: "거장별 시각 언어, 테마, 기법을 구조화된 지식으로 저장"

  features_2025:
    audio_overview: "Deep Dive, Brief, Critique, Debate 포맷"
    video_overview: "Nano Banana 6가지 비주얼 스타일"
    mind_map: "자동 개념 맵 생성"
    reports: "Briefing Doc, Study Guide, Blog Post"

  visual_styles_available:
    - "Watercolour: 부드러운 예술적 미학"
    - "Papercraft: 3D 페이퍼 컷아웃"
    - "Anime: 일본 애니메이션 스타일"
    - "Whiteboard: 깔끔한 교육용"
    - "Retro Print: 빈티지 신문/포스터"
    - "Heritage: 클래식 포멀"

  integration_pattern: |
    1. 거장별 NotebookLM 노트북 생성
    2. 필모그래피, 인터뷰, 분석 자료 업로드
    3. Audio Overview로 스타일 에센스 추출
    4. Mind Map으로 시각 언어 구조화
    5. 프롬프트 생성 시 참조 소스로 활용
```

#### 6. Crebit Aesthetic Director 구현 권장

```yaml
crebit_aesthetic_implementation:
  auteur_dna_schema:
    visual_signature:
      camera_work:
        - preferred_movements: ["tracking", "static", "handheld"]
        - typical_angles: ["low angle", "eye level", "overhead"]
        - lens_preferences: ["anamorphic", "wide angle", "telephoto"]

      lighting_philosophy:
        - key_style: "high contrast" | "soft diffused" | "natural"
        - color_temperature: "warm" | "cool" | "mixed"
        - shadow_treatment: "deep blacks" | "lifted shadows"

      color_palette:
        - dominant_colors: ["teal", "orange", "desaturated"]
        - color_grading_style: "bleach bypass" | "film emulation" | "vivid"
        - contrast_approach: "high" | "medium" | "low"

    thematic_elements:
      recurring_themes: ["isolation", "duality", "time"]
      narrative_patterns: ["non-linear", "parallel", "circular"]
      symbolic_motifs: ["mirrors", "clocks", "corridors"]

  style_blending_engine:
    input:
      - primary_auteur: "weight 0.7"
      - secondary_auteur: "weight 0.3"
    output:
      - merged_prompt_modifiers: "blended style descriptors"
      - color_lut_blend: "interpolated LUT parameters"
      - camera_movement_hybrid: "combined movement patterns"

  notebooklm_integration:
    tier0_notebooks:
      kubrick: "notebook_id_kubrick"
      bong: "notebook_id_bong"
      villeneuve: "notebook_id_villeneuve"
    query_pattern: |
      notebook_query(notebook_id, f"How would {auteur} approach {scene_type}?")
      → returns: style_hints, visual_references, technique_suggestions
```

### Sources
- MasterClass: Film 101 - What Is an Auteur?
- No Film School: What is Auteur Theory?
- Velro.ai: Directors DNA Style Exploration
- Colourlab.ai Review (Skywork AI, 2025)
- LUTBuilder.ai: Ultimate Guide to AI Color Grading 2025
- Social Sciences and Education Research Review: Algorithmic Auteur Framework (2025)
