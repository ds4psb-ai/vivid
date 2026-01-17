# App 3.1: 비주얼 리얼라이저 (Visual Realizer) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: 3D (Image Generation)

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/classic.py"  # 3D 섹션

# 현재 엔드포인트
endpoints = [
    "POST /dimension/3d/generate",      # 기본 이미지 생성
    "POST /dimension/3d/generate/stream",
]

# 현재 기능
current_features = [
    "Flux/SDXL 기반 이미지 생성",
    "기본 스타일 프롬프트 적용",
    "거장 스타일 힌트",
]

# 목표 기능 (고도화)
target_features = [
    "키프레임 이미지 전문 생성",
    "Start/End Frame 페어 생성",
    "캐릭터 일관성 보장",
    "배경 일관성 시스템",
    "Kling I2V 최적화 레퍼런스",
]
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| 일반 이미지 생성에 최적화 | 키프레임 특화 부족 | 키프레임 전문 파이프라인 |
| 캐릭터 일관성 없음 | 샷 간 불연속 | IP Adapter + 캐릭터 시트 |
| Start/End 프레임 연동 없음 | I2V 활용 제한 | 모션 가이드 페어 생성 |
| 배경 변화 관리 없음 | 환경 일관성 깨짐 | 배경 레퍼런스 시스템 |

---

## 2. 핵심 연구 주제

### 2.1 키프레임 이미지 생성 연구

**연구 질문**:
- 영상용 키프레임의 최적 구도/해상도는?
- AI 비디오 도구 친화적인 이미지 특성은?
- Start Frame과 End Frame의 최적 차이는?

**조사 대상**:
1. Kling/Runway I2V 최적 입력 연구
2. 키프레임 디자인 원칙
3. 모션 가이드 이미지 기법

### 2.2 캐릭터/배경 일관성 연구

**연구 질문**:
- 다중 샷에서 캐릭터 일관성 유지 기법은?
- 배경 연속성 유지 방법은?
- 스타일 일관성 보장 방법은?

**조사 대상**:
1. IP Adapter v2 / InstantID 활용
2. 배경 LoRA 기법
3. 스타일 전이 일관성

### 2.3 모션 가이드 이미지 연구

**연구 질문**:
- I2V에서 모션을 가이드하는 이미지 쌍 설계는?
- 시작-종료 프레임 간 최적 차이는?
- 모션 방향 암시 기법은?

**조사 대상**:
1. Kling Start/End Frame 가이드
2. Runway Gen-3 Image-to-Video 패턴
3. 모션 벡터 시각화 기법

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: keyframe_design_principles

```yaml
id: keyframe_design_principles
description: "키프레임 이미지 디자인 원칙 및 가이드"
source: "애니메이션 원리, AI 비디오 최적화"
size: ~40 documents

schema:
  principle_id:
    type: string
    example: "clear_silhouette"

  principle_name:
    type: string
    example: "명확한 실루엣"

  category:
    type: string
    enum: ["composition", "motion_guide", "character", "background", "technical"]

  description:
    type: string

  importance_for_i2v:
    type: float
    description: "I2V 생성에서의 중요도 (0-1)"

  implementation:
    type: object
    schema:
      prompt_additions: list[string]
      negative_prompts: list[string]
      composition_tips: list[string]

  common_mistakes:
    type: list[object]
    schema:
      mistake: string
      impact: string
      fix: string

  platform_specific:
    type: object
    schema:
      kling: string
      runway: string
      veo: string

# 예시 데이터
keyframe_principles:
  - principle_id: "clear_silhouette"
    principle_name: "명확한 실루엣"
    category: "composition"
    description: "주체의 외곽선이 배경과 명확히 구분되어야 I2V가 동작을 추적 가능"
    importance_for_i2v: 0.95
    implementation:
      prompt_additions: ["clear silhouette", "subject separated from background", "distinct edges"]
      negative_prompts: ["cluttered background", "merged elements", "busy composition"]
      composition_tips:
        - "주체와 배경 사이 톤 대비 확보"
        - "역광이나 림 라이트로 분리"
        - "심플한 배경 선호"
    common_mistakes:
      - mistake: "배경과 주체 색상 유사"
        impact: "I2V에서 주체 추적 실패"
        fix: "대비되는 색상/톤 사용"
    platform_specific:
      kling: "Kling은 실루엣 추적에 강함, 명확한 분리 시 최상 결과"
      runway: "Gen-3는 복잡한 배경도 처리하나 명확할수록 좋음"

  - principle_id: "motion_anticipation"
    principle_name: "모션 예고"
    category: "motion_guide"
    description: "이미지 내 포즈/구도가 다음 동작을 암시해야 함"
    importance_for_i2v: 0.90
    implementation:
      prompt_additions: ["dynamic pose", "anticipation", "ready for action", "motion blur hint"]
      composition_tips:
        - "동작 방향으로 약간 기울어진 포즈"
        - "동작선 방향에 공간 확보"
        - "약간의 모션 블러로 움직임 암시"
    common_mistakes:
      - mistake: "완전히 정적인 포즈"
        impact: "생성된 영상이 어색하게 움직이기 시작"
        fix: "동작 직전 순간의 역동적 포즈"

  - principle_id: "optimal_resolution"
    principle_name: "최적 해상도"
    category: "technical"
    description: "AI 비디오 도구에 최적화된 해상도 및 종횡비"
    importance_for_i2v: 0.85
    implementation:
      kling_optimal: "1280x720 (16:9) 또는 768x1024 (3:4)"
      veo_optimal: "1920x1080 (16:9)"
      sora_optimal: "1080x1920 (9:16) 또는 1920x1080"
      flux_generation: "항상 2x 해상도로 생성 후 다운스케일"
```

### 3.2 데이터셋: start_end_frame_patterns

```yaml
id: start_end_frame_patterns
description: "Start-End Frame 쌍 설계 패턴"
source: "I2V 최적화 연구, 실험 데이터"
size: ~50 documents

schema:
  pattern_id:
    type: string
    example: "dolly_in_pattern"

  pattern_name:
    type: string
    example: "달리 인 패턴"

  camera_movement:
    type: string

  motion_type:
    type: string
    enum: ["camera_only", "subject_only", "both", "static"]

  start_frame:
    type: object
    schema:
      shot_type: string
      subject_size: float  # 프레임 내 비율 (0-1)
      subject_position: string  # "center", "left_third", "right_third"
      key_elements: list[string]

  end_frame:
    type: object
    schema:
      shot_type: string
      subject_size: float
      subject_position: string
      key_elements: list[string]

  difference_guidelines:
    type: object
    schema:
      scale_change: float  # 크기 변화 비율
      position_shift: string  # 위치 변화 방향
      max_difference: float  # 최대 권장 차이
      min_difference: float  # 최소 필요 차이

  platform_compatibility:
    type: object
    schema:
      kling: float  # 0-1 호환성
      runway: float
      recommended_for: list[string]

  prompt_instructions:
    type: object
    schema:
      start_prompt_additions: list[string]
      end_prompt_additions: list[string]
      motion_prompt: string

# 예시 패턴
frame_patterns:
  - pattern_id: "dolly_in_pattern"
    pattern_name: "달리 인 패턴"
    camera_movement: "dolly_in"
    motion_type: "camera_only"
    start_frame:
      shot_type: "medium_wide"
      subject_size: 0.3
      subject_position: "center"
      key_elements: ["환경 컨텍스트 보임", "주체 전신 또는 대부분"]
    end_frame:
      shot_type: "close_up"
      subject_size: 0.7
      subject_position: "center"
      key_elements: ["얼굴 또는 상체 클로즈", "배경 블러"]
    difference_guidelines:
      scale_change: 2.3  # 주체 크기 2.3배 증가
      position_shift: "toward_camera"
      max_difference: 3.0  # 3배 이상 크기 변화는 어색
      min_difference: 1.5  # 1.5배 미만은 변화 미미
    platform_compatibility:
      kling: 0.95  # Kling에서 매우 효과적
      runway: 0.80
      recommended_for: ["intimate_moment", "revelation", "focus_shift"]
    prompt_instructions:
      start_prompt_additions: ["wide shot", "full environment visible", "subject at distance"]
      end_prompt_additions: ["close-up", "intimate framing", "shallow depth of field"]
      motion_prompt: "slow camera push-in toward subject"

  - pattern_id: "pan_follow_pattern"
    pattern_name: "팬 팔로우 패턴"
    camera_movement: "pan"
    motion_type: "both"
    start_frame:
      shot_type: "medium"
      subject_size: 0.4
      subject_position: "left_third"
      key_elements: ["주체 왼쪽에 위치", "오른쪽에 이동 공간"]
    end_frame:
      shot_type: "medium"
      subject_size: 0.4
      subject_position: "right_third"
      key_elements: ["주체 오른쪽으로 이동", "새로운 환경 노출"]
    difference_guidelines:
      scale_change: 1.0  # 크기 변화 없음
      position_shift: "left_to_right"
      max_difference: 0.6  # 프레임 60% 이상 이동은 어색
      min_difference: 0.3  # 30% 미만은 변화 미미
    platform_compatibility:
      kling: 0.85
      runway: 0.90
```

### 3.3 데이터셋: character_consistency_presets

```yaml
id: character_consistency_presets
description: "캐릭터 일관성 유지 프리셋 및 기법"
source: "IP Adapter 연구, 실험 데이터"
size: ~30 documents

schema:
  preset_id:
    type: string
    example: "realistic_human"

  preset_name:
    type: string
    example: "사실적 인물"

  character_type:
    type: string
    enum: ["realistic_human", "anime_character", "3d_stylized", "creature", "object"]

  consistency_method:
    type: object
    schema:
      primary_technique: string
      secondary_technique: string
      fallback: string

  required_references:
    type: list[object]
    schema:
      reference_type: string
      purpose: string
      generation_prompt: string

  flux_workflow:
    type: object
    schema:
      ip_adapter_weight: float
      style_weight: float
      composition_freedom: float
      recommended_steps: int

  prompt_template:
    type: string
    description: "일관성 보장 프롬프트 템플릿"

  common_variations:
    type: list[object]
    schema:
      variation_type: string  # "expression", "pose", "lighting"
      handling_method: string

# 예시 프리셋
consistency_presets:
  - preset_id: "realistic_human"
    preset_name: "사실적 인물"
    character_type: "realistic_human"
    consistency_method:
      primary_technique: "ip_adapter_face"
      secondary_technique: "character_sheet_reference"
      fallback: "detailed_text_description"
    required_references:
      - reference_type: "front_face_neutral"
        purpose: "얼굴 일관성 기준점"
        generation_prompt: "portrait photo, front view, neutral expression, even lighting, white background"
      - reference_type: "three_quarter_view"
        purpose: "얼굴 입체감 참조"
        generation_prompt: "portrait photo, three-quarter view, neutral expression, studio lighting"
      - reference_type: "full_body_pose"
        purpose: "체형 및 의상 참조"
        generation_prompt: "full body photo, standing pose, neutral background"
    flux_workflow:
      ip_adapter_weight: 0.85
      style_weight: 0.3
      composition_freedom: 0.5
      recommended_steps: 30
    prompt_template: "[SCENE DESCRIPTION], {character_name}, [consistent with reference], [character features: {features}], [wearing {outfit}]"
    common_variations:
      - variation_type: "expression"
        handling_method: "표정 키워드 추가, IP Adapter 가중치 0.7로 낮춤"
      - variation_type: "pose"
        handling_method: "포즈 설명 상세화, composition_freedom 0.7로 높임"
      - variation_type: "lighting"
        handling_method: "조명 설명 추가, 참조 이미지와 유사한 조명 권장"

  - preset_id: "anime_character"
    preset_name: "애니메이션 캐릭터"
    character_type: "anime_character"
    consistency_method:
      primary_technique: "character_lora"
      secondary_technique: "style_reference"
      fallback: "detailed_anime_description"
    flux_workflow:
      ip_adapter_weight: 0.75
      style_weight: 0.6  # 스타일 가중치 높음
      composition_freedom: 0.6
      recommended_steps: 28
    prompt_template: "[SCENE], {character_name} from {series_style}, [anime style], [key features: {hair_color}, {eye_color}, {outfit}], [expression: {expression}]"
```

### 3.4 데이터셋: background_continuity_system

```yaml
id: background_continuity_system
description: "배경 연속성 유지 시스템"
source: "환경 디자인, 일관성 기법"
size: ~25 documents

schema:
  environment_type:
    type: string
    example: "indoor_modern"

  environment_name:
    type: string

  key_elements:
    type: list[object]
    schema:
      element: string
      importance: float
      consistency_method: string

  lighting_continuity:
    type: object
    schema:
      time_of_day: string
      key_light_direction: string
      color_temperature: string
      prompt_keywords: list[string]

  spatial_consistency:
    type: object
    schema:
      perspective_rules: list[string]
      depth_cues: list[string]
      scale_references: list[string]

  reference_strategy:
    type: object
    schema:
      initial_setup: string
      shot_to_shot: string
      transition_handling: string

# 예시 데이터
background_systems:
  - environment_type: "indoor_apartment"
    environment_name: "현대 아파트 실내"
    key_elements:
      - element: "창문 위치/형태"
        importance: 0.9
        consistency_method: "모든 샷에 동일 창문 묘사 포함"
      - element: "벽 색상/질감"
        importance: 0.85
        consistency_method: "색상 코드 명시 (예: warm beige walls)"
      - element: "가구 배치"
        importance: 0.8
        consistency_method: "공간 다이어그램 기반 위치 설명"
    lighting_continuity:
      time_of_day: "afternoon"
      key_light_direction: "from_window_left"
      color_temperature: "warm_daylight"
      prompt_keywords: ["warm afternoon light from window", "soft shadows to the right", "natural daylight"]
    spatial_consistency:
      perspective_rules:
        - "카메라 높이 일정 유지 (eye level)"
        - "수평선 위치 일관성"
      depth_cues:
        - "전경, 중경, 후경 요소 일관"
        - "심도 처리 일관"
    reference_strategy:
      initial_setup: "첫 와이드 샷에서 전체 공간 확립"
      shot_to_shot: "와이드 샷 레퍼런스 이미지 활용"
      transition_handling: "동일 환경 내 위치 변화 명시"
```

---

## 4. 기능 고도화 설계

### 4.1 키프레임 생성 파이프라인

```yaml
visual_realizer_pipeline:
  stage_1_context_loading:
    purpose: "캐릭터/배경 컨텍스트 로드"
    inputs:
      - character_sheets (from 스토리보드)
      - environment_references
      - auteur_style
    outputs:
      - character_prompts: dict[character_id, prompt_fragment]
      - background_prompts: dict[environment_id, prompt_fragment]
      - style_modifiers: list[string]
    logic:
      - "캐릭터 시트에서 일관성 프롬프트 추출"
      - "환경 레퍼런스에서 연속성 프롬프트 추출"
      - "거장 스타일 시각 요소 로드"

  stage_2_keyframe_design:
    purpose: "키프레임 구도/구성 설계"
    inputs:
      - shot_prompt (from 프롬프트 연금술)
      - shot_type
      - camera_info
      - motion_info
    outputs:
      - keyframe_spec: KeyframeSpec
    rag_queries:
      - "keyframe_design_principles → 샷 타입 기반"
      - "start_end_frame_patterns → 카메라 무브먼트 기반"
    logic:
      - "샷 유형에 맞는 구도 원칙 적용"
      - "I2V 친화적 구성 최적화"

  stage_3_start_frame_generation:
    purpose: "시작 키프레임 생성"
    inputs:
      - keyframe_spec
      - character_prompts
      - background_prompts
      - style_modifiers
    outputs:
      - start_frame_image
    logic:
      - "Flux Pro API 호출"
      - "캐릭터 IP Adapter 적용"
      - "배경 일관성 프롬프트 적용"

  stage_4_end_frame_generation:
    purpose: "종료 키프레임 생성"
    inputs:
      - start_frame_image (참조)
      - keyframe_spec
      - motion_info
    outputs:
      - end_frame_image
    logic:
      - "시작 프레임 기반 변화 적용"
      - "모션 가이드에 맞는 차이 생성"
      - "일관성 유지하며 변화 표현"

  stage_5_validation:
    purpose: "키프레임 쌍 검증"
    inputs:
      - start_frame_image
      - end_frame_image
      - expected_difference
    outputs:
      - validation_result
      - difference_metrics
    logic:
      - "차이 정도 측정"
      - "일관성 검증 (캐릭터, 배경)"
      - "I2V 적합성 평가"
```

### 4.2 출력 스키마 설계

```python
class VisualRealizerOutput(BaseModel):
    """비주얼 리얼라이저 출력 스키마"""

    # 메타데이터
    metadata: KeyframeMetadata
    class KeyframeMetadata(BaseModel):
        shot_number: int
        shot_type: str
        camera_movement: str
        target_duration: float
        style_applied: str
        platform_target: str  # kling, veo, sora

    # 키프레임 이미지
    keyframes: KeyframePair
    class KeyframePair(BaseModel):
        start_frame: KeyframeImage
        end_frame: KeyframeImage | None  # 모션이 없으면 None

        class KeyframeImage(BaseModel):
            image_url: str
            thumbnail_url: str
            resolution: str
            generation_prompt: str
            negative_prompt: str

    # 차이 분석
    difference_analysis: DifferenceAnalysis
    class DifferenceAnalysis(BaseModel):
        scale_change: float
        position_shift: str
        subject_pose_change: str
        background_change: str
        estimated_motion_smoothness: float  # 0-1

    # 일관성 보고
    consistency_report: ConsistencyReport
    class ConsistencyReport(BaseModel):
        character_consistency: float
        background_consistency: float
        style_consistency: float
        issues_detected: list[str]

    # I2V 호환성
    i2v_compatibility: I2VCompatibility
    class I2VCompatibility(BaseModel):
        kling_score: float
        veo_score: float
        sora_score: float
        recommended_tool: str
        optimization_notes: list[str]

    # 참조 정보
    references_used: ReferencesUsed
    class ReferencesUsed(BaseModel):
        character_references: list[str]
        background_references: list[str]
        style_references: list[str]

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     platform_prompts     ┌─────────────────┐
│ 2.3 프롬프트    │ ─────────────────────────► │ 3.1 비주얼      │
│     연금술      │                           │     리얼라이저   │
└─────────────────┘                           └────────┬────────┘
                                                       │
┌─────────────────┐     character_sheets               │
│ 2.2 스토리보드  │ ───────────────────────────────────│
│     스케치      │                                    │
└─────────────────┘                                    │
                                                       │
┌─────────────────┐     auteur_visual_style            │
│ 5.1 미학 디렉터 │ ───────────────────────────────────│
└─────────────────┘                                    │
                                                       │ keyframe_pairs
                                                       │ + i2v_compatibility
                                                       ▼
                                             ┌─────────────────┐
                                             │ 3.2 비디오      │
                                             │     메이커      │
                                             └─────────────────┘
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| shot_prompts | 프롬프트 연금술 | 키프레임 설계 | keyframe_spec | 이미지 생성 |
| character_sheets | 스토리보드 스케치 | 일관성 프롬프트 | character_prompts | 이미지 생성 |
| visual_style | 미학 디렉터 | 스타일 수정자 | style_modifiers | 이미지 생성 |
| keyframe_pairs | - | - | i2v_input | 비디오 메이커 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 키프레임 디자인 조사

- [ ] 애니메이션 키프레임 원칙 정리
- [ ] I2V 최적화 이미지 특성 연구
- [ ] 모션 예고 구도 기법 수집
- [ ] 해상도/종횡비 최적화 실험

### 6.2 Start-End Frame 조사

- [ ] Kling Start/End Frame 최적 설정
- [ ] 카메라 무브먼트별 프레임 쌍 패턴
- [ ] 차이 정도 최적화 실험
- [ ] 모션 방향 암시 기법

### 6.3 일관성 시스템 조사

- [ ] IP Adapter v2 최신 가이드
- [ ] 캐릭터 시트 최적 구성
- [ ] 배경 연속성 유지 기법
- [ ] 스타일 일관성 기법

### 6.4 기술 통합 조사

- [ ] Flux Pro API 통합
- [ ] ComfyUI 워크플로우 설계
- [ ] 배치 생성 최적화
- [ ] 품질 평가 자동화

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 키프레임 원칙 정리 | 2일 | 원칙 DB |
| 2 | Start-End 패턴 수집 | 2일 | 패턴 DB |
| 3 | 일관성 시스템 설계 | 2일 | 프리셋 |
| 4 | Flux API 통합 | 2일 | 이미지 생성 |
| 5 | 파이프라인 구현 | 3일 | 코드 |
| 6 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 기술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| IP Adapter v2 | 논문/코드 | 이미지 일관성 |
| Kling I2V Guide | 가이드 | Start/End Frame |
| Animation Keyframes | 교재 | 키프레임 원칙 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| Flux Pro | https://flux.ai/ | 이미지 생성 |
| Kling | https://kling.ai/ | I2V 최적화 |
| ComfyUI | https://github.com/comfyanonymous/ | 워크플로우 |

---

## 9. Prop & Background Consistency (P0 보강)

> **Updated**: 2026-01-17 (컨설팅 피드백 반영)
> **Reference**: DIMENSION_APP_MACRO_PLANNING_2026.md Part 9.2

### 9.1 확장된 Entity Consistency 범위

기존 캐릭터 일관성만 다루던 범위를 **소품(Prop)과 배경(Location)**까지 확장합니다.

```yaml
entity_consistency_scope:
  v1_current:
    entities: ["character"]
    focus: "얼굴, 체형, 의상"

  v2_extended:
    entities: ["character", "prop", "background"]
    focus:
      character: "얼굴, 체형, 의상, 헤어, 액세서리"
      prop: "형태, 색상, 질감, 크기, 재질"
      background: "장소 유형, 조명 조건, 분위기, 핵심 요소"
```

### 9.2 2026년 Entity Consistency 기술 현황

| 기술 | 개발사 | 지원 엔티티 | 성능 |
|------|--------|------------|------|
| **StoryMem** | ByteDance | 캐릭터, 배경 | 기본 대비 +28.7% 향상 |
| **VideoMemory** | 연구 논문 | 캐릭터, 소품, 배경 | Prop 0.58, BG 0.72 점수 |
| **IC-LoRA** | Diffusion | 스타일, 오브젝트 | 범용 LoRA 적용 |
| **Veo 3.1 Ingredients** | Google | 캐릭터, 배경, 오브젝트 | 최대 3개 레퍼런스 |

### 9.3 StoryMem 핵심 메커니즘

```yaml
storymem_architecture:
  core_concept: "Dynamic Memory Bank"

  memory_bank_design:
    purpose: "키프레임을 메모리에 저장하여 크로스-샷 일관성 유지"
    components:
      semantic_keyframe_selection:
        description: "의미론적으로 중요한 프레임 선택"
        filter_1: "시각적 코어 프레임 (시맨틱 분석)"
        filter_2: "품질 검사 (블러 제거)"

      rope_encoding:
        description: "Rotary Position Embedding으로 시간 인코딩"
        mechanism: "메모리 프레임에 '음수 시간 인덱스' 할당"
        effect: "AI가 '과거 이벤트'로 인식하도록 유도"

      lora_finetuning:
        base_model: "Wan 2.2 (14B)"
        training: "LoRA만 파인튜닝 (경량)"

  benchmark_results:
    st_bench:
      description: "54-case multi-shot consistency benchmark"
      metrics:
        character_consistency: "0.63 avg (12-shot)"
        prop_consistency: "0.58 avg (12-shot)"
        background_consistency: "0.72 avg (12-shot)"
      comparison:
        vs_base_wan22: "+28.7%"
        vs_holocine: "+9.4%"
```

### 9.4 VideoMemory Prop/Background 평가 메트릭

```yaml
videomemory_metrics:
  prop_consistency:
    method: "Grounded SAM → DINOv2 features"
    scoring: "코사인 유사도 정규화"
    measures: "색상, 형태, 질감 일관성"

  background_consistency:
    method: "프레임 간 배경 영역 DINOv2 유사도"
    scoring: "씬 전환 시에도 일관성 측정"

  user_study_results:
    vs_wan22:
      character: "87.50% prefer VideoMemory"
      prop: "79.17% prefer VideoMemory"
      background: "87.50% prefer VideoMemory"
    vs_ic_lora:
      prop: "87.50% prefer VideoMemory"
      background: "91.66% prefer VideoMemory"
```

### 9.5 비주얼 리얼라이저 V2 확장 설계

```yaml
app_3_1_visual_realizer_v2:
  entity_types:
    characters:
      existing: true
      dna_fields: ["face", "body_type", "costume", "hair", "accessories"]
      reference_count: "6-10 images"
      angles: ["front", "3/4 left", "3/4 right", "profile", "back"]
      expressions: ["neutral", "happy", "sad", "angry", "surprised"]

    props:
      new: true
      dna_fields: ["shape", "color", "texture", "size", "material"]
      reference_count: "3-5 images"
      angles: ["front", "45°", "detail closeup"]
      lighting: ["neutral", "dramatic"]
      examples: ["마법 지팡이", "빈티지 카메라", "특정 차량", "무기"]

    backgrounds:
      new: true
      dna_fields: ["location_type", "lighting_condition", "atmosphere", "key_elements"]
      reference_count: "3-5 images"
      times: ["day", "dusk", "night"]  # if applicable
      weather: ["clear", "cloudy"]  # if applicable
      examples: ["주인공의 방", "카페 외관", "우주선 브릿지"]
```

### 9.6 Memory Bank 통합 설계

```yaml
memory_bank_integration:
  description: "StoryMem 스타일 메모리 뱅크 도입"

  implementation:
    keyframe_storage:
      per_entity: "캐릭터/소품/배경별 키프레임 저장"
      max_frames: 10
      storage: "Qdrant 벡터 DB"
      embedding_model: "DINOv2"

    retrieval:
      method: "시맨틱 유사도 기반 검색"
      trigger: "새 샷 생성 시 관련 엔티티 자동 주입"
      injection: "IP Adapter / ControlNet 연동"

    lifecycle:
      creation: "첫 등장 시 레퍼런스 팩에서 메모리 초기화"
      update: "HITL 승인된 샷에서 메모리 보강"
      retrieval: "새 샷 생성 시 상위 3개 메모리 프레임 주입"

  data_schema:
    entity_memory_entry:
      entity_id: str
      entity_type: Literal["character", "prop", "background"]
      keyframe_url: str
      embedding_vector: list[float]  # DINOv2 768-D
      timestamp: datetime
      quality_score: float
      metadata: dict
```

### 9.7 일관성 자동 평가 시스템

```yaml
consistency_scoring:
  automated_check:
    method: "DINOv2 similarity scoring"

  thresholds:
    character: 0.70
    prop: 0.60
    background: 0.65

  action_on_fail:
    below_threshold: "재생성 권장 플래그"
    below_critical: "자동 재생성 트리거 (0.5 미만)"

  output_schema:
    consistency_report:
      character_consistency: float  # 0-1
      prop_consistency: float  # 0-1
      background_consistency: float  # 0-1
      issues_detected: list[str]
      regeneration_recommended: bool
```

### 9.8 Veo 3.1 Ingredients to Video 활용

```yaml
veo_ingredients_integration:
  description: "Veo 3.1의 'Images to Video' 기능으로 일관성 확보"

  capabilities:
    max_references: 3
    reference_types: ["character", "object", "style", "setting"]
    combination: "최대 3개 레퍼런스 조합 사용"

  workflow:
    step_1:
      action: "엔티티별 레퍼런스 이미지 생성"
      tool: "Flux Pro / SDXL"

    step_2:
      action: "Veo Ingredients 모드로 영상 생성"
      input:
        - "character_reference.png"
        - "prop_reference.png"
        - "background_reference.png"
      prompt: "씬 설명 + 동작 지시"

    step_3:
      action: "일관성 점수 자동 평가"
      output: "consistency_report"
```

### 9.9 업데이트된 출력 스키마

```python
class VisualRealizerOutputV2(BaseModel):
    """Prop/Background 일관성 확장 출력 스키마"""

    # 기존 필드 유지
    metadata: KeyframeMetadata
    keyframes: KeyframePair

    # 확장: 엔티티별 일관성 보고
    consistency_report: ExtendedConsistencyReport
    class ExtendedConsistencyReport(BaseModel):
        character_consistency: float
        prop_consistency: float  # 신규
        background_consistency: float  # 신규
        overall_score: float
        issues_detected: list[str]
        regeneration_recommended: bool

    # 신규: 메모리 뱅크 상태
    memory_bank_state: MemoryBankState
    class MemoryBankState(BaseModel):
        character_memories: list[MemoryEntry]
        prop_memories: list[MemoryEntry]
        background_memories: list[MemoryEntry]

        class MemoryEntry(BaseModel):
            entity_id: str
            frame_count: int
            last_updated: str
            avg_quality: float

    # 신규: 레퍼런스 팩 정보
    reference_packs: ReferencePacks
    class ReferencePacks(BaseModel):
        characters: list[CharacterRefPack]
        props: list[PropRefPack]  # 신규
        backgrounds: list[BackgroundRefPack]  # 신규

        class CharacterRefPack(BaseModel):
            character_id: str
            reference_images: list[str]
            dna_summary: dict

        class PropRefPack(BaseModel):
            prop_id: str
            prop_name: str
            reference_images: list[str]
            dna_summary: dict  # shape, color, texture, size, material

        class BackgroundRefPack(BaseModel):
            location_id: str
            location_name: str
            reference_images: list[str]
            dna_summary: dict  # type, lighting, atmosphere, elements

    # 근거
    evidence_refs: list[str]
```

---

## 10. IC-LoRA 및 대안 기법 조사

> **Reference**: DIMENSION_APP_MACRO_PLANNING_2026.md Part 9.2

### 10.1 IC-LoRA (Image-Conditioned LoRA)

```yaml
ic_lora_overview:
  purpose: "단일 레퍼런스 이미지로 일관성 있는 생성"
  approach: "LoRA 가중치를 이미지 조건부로 동적 조정"

  advantages:
    - "파인튜닝 없이 즉시 적용"
    - "다양한 스타일/오브젝트에 범용 적용"
    - "기존 Flux/SDXL 호환"

  limitations:
    - "복잡한 소품에서 정확도 저하"
    - "StoryMem 대비 멀티샷 일관성 약함"

  use_cases:
    - "단순 오브젝트 일관성"
    - "스타일 전이"
    - "빠른 프로토타이핑"
```

### 10.2 기술 선택 가이드

| 시나리오 | 권장 기법 | 이유 |
|----------|----------|------|
| 다중 캐릭터 멀티샷 | StoryMem | 최고의 일관성 (+28.7%) |
| 복잡한 소품 일관성 | VideoMemory | Prop 평가 메트릭 지원 |
| 배경 연속성 | StoryMem | Background 0.72 달성 |
| 빠른 테스트 | IC-LoRA | 파인튜닝 불필요 |
| Veo 기반 제작 | Ingredients | 네이티브 3-레퍼런스 지원 |

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 키프레임 원칙 수집 |
| 2026-01-17 | Prop/BG Consistency 보강 (Part 9,10) | 완료 | Memory Bank 구현 |
| 2026-01-17 | 웹 리서치 완료 (VideoMemory, IC-LoRA) | 완료 | 메모리 뱅크 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### Multi-Shot Video Consistency 핵심 기술 발견

#### 1. VideoMemory (arXiv 2601.03655, Jan 2026)

```yaml
videomemory_overview:
  title: "VideoMemory: Entity-Centric Framework"
  key_innovation: "Dynamic Memory Bank for multi-shot consistency"

  architecture:
    storyboard_agent: "스크립트 → 장면/샷 분해"
    memory_agent: "엔티티 추출 + 메모리 상호작용"
    dynamic_memory_bank:
      - "characters: 시각적/의미적 상태 저장"
      - "props: 소품 외관 + 속성"
      - "backgrounds: 환경 일관성"

  workflow:
    1. "Memory Agent가 샷별 필요 엔티티 추출"
    2. "Dynamic Memory Bank에서 해당 엔티티 상태 검색"
    3. "검색된 상태 기반 키프레임/비디오 합성"
    4. "샷 생성 후 메모리 업데이트"

  benchmark_results:
    character_consistency: 0.63  # vs Wan2.2: 0.34
    prop_consistency: 0.58       # vs Wan2.2: 0.48
    background_consistency: 0.72 # vs Wan2.2: 0.25
    vs_ic_lora: "+16% character, +15% prop, +41% background"
```

#### 2. StoryMem (ByteDance, Dec 2025)

```yaml
storymem_overview:
  title: "StoryMem: Memory-to-Video (M2V) Design"
  core_concept: "Human memory-inspired visual storytelling"

  memory_bank_design:
    keyframe_storage: "히스토리 샷에서 키프레임 추출/저장"
    injection_method: "latent concatenation + negative RoPE shifts"
    finetuning: "LoRA만 필요 (전체 재학습 불필요)"

  keyframe_selection:
    semantic_selection: "의미적으로 구별되는 프레임만 저장"
    aesthetic_filtering: "미적 품질 필터링"
    memory_management:
      - "memory-sink: 초기 키프레임 고정 (글로벌 일관성)"
      - "sliding-window: 최근 키프레임 유지 (로컬 의존성)"

  results_vs_wan22:
    character: "+28.7% improvement"
    cross_shot_consistency: "minute-long coherent videos"
```

#### 3. IC-LoRA (In-Context LoRA)

```yaml
ic_lora_overview:
  title: "In-Context LoRA for Diffusion Transformers"
  use_case: "Film Storyboard Generation, Visual Identity Design"

  key_features:
    simultaneous_generation: "3-image sequence 동시 생성"
    placeholder_identity: "[CHARACTER_NAME] 태그로 정체성 참조"
    no_training_required: "사전학습 모델에 LoRA adapter만 추가"

  prompt_pattern: |
    "In this adventurous three-image sequence,
    [IMAGE1] Ethan, an intrepid archaeologist, uncovers an ancient map...
    [IMAGE2] transitioning to a bustling marketplace where Ethan negotiates...
    [IMAGE3] and finally, Ethan treks through a dense jungle..."

  applications:
    - "Film storyboard: 3-shot sequences with character consistency"
    - "Visual identity: Logo + real-world application consistency"
    - "Product imagery: Multiple angles with style coherence"
```

#### 4. Character Consistency 솔루션 비교 (2025)

| 솔루션 | Consistency Score | Training Needs | Best Use Case |
|--------|-------------------|----------------|---------------|
| LlamaGen C1 | 96% | 5-10 images | Serialized Narratives |
| Flux LoRA | 90% | 50+ images | Enterprise Production |
| LoRA HyperNet | 87% | 15-20 images | Indie Projects |
| ComfyUI | Customizable | 5-10 images | Technical Teams |
| IC-LoRA | ~85% | 0 (pre-trained) | Rapid Prototyping |

#### 5. OneStory: Adaptive Memory (Dec 2025)

```yaml
onestory_architecture:
  challenge: "Multi-shot video는 시공간 variance가 unbounded"

  key_insight: |
    Shot 1: 주인공 등장
    Shot 2: 조연 등장
    Shot 3: 주인공 재등장
    → Shot 3 생성 시 Shot 1을 주로 참조해야 함 (Shot 2 덜 관련)

  frame_selection_module:
    purpose: "의미적으로 관련된 프레임만 선택"
    method: "CLIP space에서 유사도 기반 선택"

  adaptive_memory:
    global_context: "전체 스토리 일관성"
    compact_representation: "효율적 메모리 사용"
```

#### 6. Crebit 구현 권장사항

```yaml
crebit_implementation:
  memory_bank_design:
    tier1_entities:
      characters:
        max_keyframes: 10
        update_trigger: "appearance_change > 0.15"
        storage: "DINOv2 features + CLIP embedding"
      props:
        max_keyframes: 5
        update_trigger: "state_change detected"
      backgrounds:
        max_keyframes: 5
        update_trigger: "scene_transition"

  retrieval_strategy:
    method: "hybrid CLIP + DINOv2 similarity"
    threshold: 0.7
    fallback: "nearest neighbor in memory"

  consistency_targets:
    character: ">= 0.63 (VideoMemory baseline)"
    prop: ">= 0.58"
    background: ">= 0.72"
```

### Sources
- VideoMemory (arXiv:2601.03655, Jan 2026)
- StoryMem (ByteDance + NTU, Dec 2025)
- IC-LoRA (Ali-vilab, 2025)
- OneStory (OpenReview, Dec 2025)
- LlamaGen Character Consistency Guide (2025)
