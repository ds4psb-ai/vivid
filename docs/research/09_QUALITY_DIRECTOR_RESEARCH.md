# App 4.1: 퀄리티 디렉터 (Quality Director) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: QC (Quality Control)

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/quality.py"

# 현재 엔드포인트
endpoints = [
    "POST /dimension/qc/review",
    "POST /dimension/qc/review/stream",
]

# 현재 기능
current_features = [
    "기본 품질 리뷰",
    "거장 시점 피드백",
    "개선 제안",
]

# 목표 기능 (고도화)
target_features = [
    "다차원 품질 평가 (기술/미학/서사)",
    "거장별 세부 피드백",
    "자동 개선점 우선순위화",
    "재생성 가이드 생성",
    "품질 점수 대시보드",
    "A/B 비교 평가",
]
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| 단일 차원 평가 | 종합적 품질 파악 불가 | 다차원 평가 체계 |
| 거장별 기준 모호 | 피드백 일반적 | 거장별 평가 매트릭스 |
| 개선 우선순위 없음 | 비효율적 수정 | 영향도 기반 우선순위 |
| 재생성 가이드 없음 | 시행착오 반복 | 구체적 수정 프롬프트 |

---

## 2. 핵심 연구 주제

### 2.1 AI 생성 콘텐츠 품질 평가 연구

**연구 질문**:
- AI 비디오 품질의 객관적 평가 기준은?
- 기술적 품질 vs 미학적 품질 측정법은?
- 인간 평가와 자동 평가의 상관관계는?

**조사 대상**:
1. VBench (비디오 품질 벤치마크)
2. 영화 품질 평가 학술 연구
3. 자동 품질 평가 알고리즘 (CLIP, FID)

### 2.2 거장 평가 기준 연구

**연구 질문**:
- 각 거장이 중시하는 품질 요소는?
- 거장별 '좋은 작품'의 기준은?
- 거장 스타일 일치도 측정법은?

**조사 대상**:
1. 거장 인터뷰/비평 분석
2. 작품 평론 분석
3. 거장별 체크리스트 구성

### 2.3 피드백 시스템 연구

**연구 질문**:
- 효과적인 창작 피드백 형식은?
- 개선 우선순위 결정 기준은?
- 재생성 가이드 자동화 방법은?

**조사 대상**:
1. 창작 피드백 심리학
2. 품질 개선 프레임워크
3. 프롬프트 엔지니어링 수정 패턴

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: quality_evaluation_dimensions

```yaml
id: quality_evaluation_dimensions
description: "다차원 품질 평가 체계"
source: "영화 평론, 품질 벤치마크"
size: ~30 documents

schema:
  dimension_id:
    type: string
    example: "technical_quality"

  dimension_name:
    type: string
    example: "기술적 품질"

  category:
    type: string
    enum: ["technical", "aesthetic", "narrative", "emotional", "style"]

  sub_criteria:
    type: list[object]
    schema:
      criterion_id: string
      criterion_name: string
      description: string
      weight: float  # 0-1
      evaluation_method: string
      scoring_guide: string

  auto_evaluation:
    type: object
    schema:
      possible: bool
      method: string
      accuracy: float

  human_evaluation:
    type: object
    schema:
      questions: list[string]
      scale: string

# 예시 차원
evaluation_dimensions:
  - dimension_id: "technical_quality"
    dimension_name: "기술적 품질"
    category: "technical"
    sub_criteria:
      - criterion_id: "motion_smoothness"
        criterion_name: "모션 부드러움"
        description: "움직임의 자연스러움과 연속성"
        weight: 0.25
        evaluation_method: "optical_flow_analysis"
        scoring_guide: "0: 심각한 끊김, 0.5: 간헐적 문제, 1: 완벽"
      - criterion_id: "temporal_consistency"
        criterion_name: "시간적 일관성"
        description: "프레임 간 시각적 연속성"
        weight: 0.25
        evaluation_method: "frame_diff_analysis"
        scoring_guide: "0: 심각한 플리커, 0.5: 간헐적 불일치, 1: 완벽"
      - criterion_id: "resolution_quality"
        criterion_name: "해상도 품질"
        description: "디테일과 선명도"
        weight: 0.20
        evaluation_method: "sharpness_detection"
      - criterion_id: "artifact_free"
        criterion_name: "아티팩트 부재"
        description: "시각적 결함 없음"
        weight: 0.30
        evaluation_method: "anomaly_detection"
    auto_evaluation:
      possible: true
      method: "computer_vision_metrics"
      accuracy: 0.85

  - dimension_id: "aesthetic_quality"
    dimension_name: "미학적 품질"
    category: "aesthetic"
    sub_criteria:
      - criterion_id: "composition"
        criterion_name: "구도"
        description: "프레임 구성의 균형과 조화"
        weight: 0.30
        evaluation_method: "composition_analysis"
        scoring_guide: "삼분할, 대칭, 리딩 라인 활용도"
      - criterion_id: "color_harmony"
        criterion_name: "색채 조화"
        description: "색상 팔레트의 일관성과 조화"
        weight: 0.25
        evaluation_method: "color_analysis"
      - criterion_id: "lighting_quality"
        criterion_name: "조명 품질"
        description: "조명의 적절성과 분위기"
        weight: 0.25
        evaluation_method: "lighting_analysis"
      - criterion_id: "visual_interest"
        criterion_name: "시각적 흥미"
        description: "시선을 끄는 요소의 적절성"
        weight: 0.20
        evaluation_method: "saliency_detection"

  - dimension_id: "narrative_quality"
    dimension_name: "서사적 품질"
    category: "narrative"
    sub_criteria:
      - criterion_id: "story_clarity"
        criterion_name: "스토리 명확성"
        description: "메시지와 내러티브의 전달력"
        weight: 0.35
        evaluation_method: "human_evaluation"
      - criterion_id: "pacing"
        criterion_name: "페이싱"
        description: "속도감과 리듬의 적절성"
        weight: 0.30
        evaluation_method: "shot_duration_analysis"
      - criterion_id: "emotional_arc"
        criterion_name: "감정 곡선"
        description: "감정적 여정의 완성도"
        weight: 0.35
        evaluation_method: "sentiment_analysis"
```

### 3.2 데이터셋: auteur_quality_standards

```yaml
id: auteur_quality_standards
description: "거장별 품질 평가 기준"
source: "거장 인터뷰, 비평 분석"
size: ~30 documents

schema:
  auteur_key:
    type: string
    example: "bong_joon_ho"

  quality_philosophy:
    type: string
    description: "거장의 품질에 대한 철학"

  priority_criteria:
    type: list[object]
    schema:
      criterion: string
      importance: float  # 0-1
      auteur_perspective: string
      example_from_work: string

  deal_breakers:
    type: list[object]
    schema:
      issue: string
      why_unacceptable: string
      example: string

  signature_elements_check:
    type: list[object]
    schema:
      element: string
      how_to_verify: string
      weight: float

  feedback_style:
    type: object
    schema:
      tone: string
      focus_areas: list[string]
      quote_template: string

# 예시 거장 기준
auteur_standards:
  - auteur_key: "bong_joon_ho"
    quality_philosophy: "디테일에 의미가 있어야 한다. 모든 프레임은 서사를 전달해야 한다."
    priority_criteria:
      - criterion: "visual_metaphor"
        importance: 0.95
        auteur_perspective: "이미지가 말하지 않아도 의미를 전달해야"
        example_from_work: "기생충의 반지하 창문 = 사회적 위치의 은유"
      - criterion: "social_commentary"
        importance: 0.90
        auteur_perspective: "작품은 사회를 비추는 거울이어야"
        example_from_work: "기생충의 계층 구조 시각화"
      - criterion: "genre_subversion"
        importance: 0.80
        auteur_perspective: "장르 규칙을 따르되 예상을 뒤집어야"
    deal_breakers:
      - issue: "empty_spectacle"
        why_unacceptable: "화려하지만 의미 없는 장면은 시간 낭비"
        example: "스토리와 무관한 시각 효과"
      - issue: "character_inconsistency"
        why_unacceptable: "캐릭터가 자신의 논리를 따르지 않으면 관객이 이탈"
    signature_elements_check:
      - element: "layered_framing"
        how_to_verify: "전경/중경/후경에 의미 있는 요소 배치 확인"
        weight: 0.3
      - element: "dark_humor"
        how_to_verify: "긴장과 유머의 병치 존재 확인"
        weight: 0.2
    feedback_style:
      tone: "직접적이고 날카로우나 건설적"
      focus_areas: ["meaning_behind_image", "social_relevance", "genre_awareness"]
      quote_template: "'{issue}'는 문제야. 관객이 '{consequence}' 때문에. 대신 '{suggestion}'를 고려해봐."

  - auteur_key: "nolan"
    quality_philosophy: "복잡함이 혼란이 되어서는 안 된다. 정교하되 명확해야."
    priority_criteria:
      - criterion: "narrative_precision"
        importance: 0.95
        auteur_perspective: "모든 정보는 정확한 타이밍에 전달되어야"
      - criterion: "practical_grounding"
        importance: 0.85
        auteur_perspective: "아무리 상상력이 풍부해도 물리적 현실감 필요"
      - criterion: "temporal_logic"
        importance: 0.90
        auteur_perspective: "시간 조작도 내부 논리가 있어야"
    deal_breakers:
      - issue: "logical_inconsistency"
        why_unacceptable: "관객이 규칙을 이해할 수 없으면 몰입 불가"
    signature_elements_check:
      - element: "time_manipulation"
        how_to_verify: "시간 흐름에 의도적 변형이 있는지"
        weight: 0.25
      - element: "practical_effects_feel"
        how_to_verify: "CG라도 물리적 무게감이 느껴지는지"
        weight: 0.20
```

### 3.3 데이터셋: improvement_priority_matrix

```yaml
id: improvement_priority_matrix
description: "개선 우선순위 결정 매트릭스"
source: "품질 관리 방법론"
size: ~20 documents

schema:
  issue_type:
    type: string
    example: "motion_artifact"

  issue_category:
    type: string
    enum: ["technical", "aesthetic", "narrative"]

  severity_levels:
    type: list[object]
    schema:
      level: string  # "critical", "major", "minor", "cosmetic"
      description: string
      visual_impact: float  # 0-1
      viewer_perception: string

  fix_difficulty:
    type: object
    schema:
      regeneration_required: bool
      prompt_modification: bool
      post_processing: bool
      estimated_effort: string  # "low", "medium", "high"

  priority_score_formula:
    type: string
    description: "우선순위 점수 계산 공식"

  fix_guidance:
    type: list[object]
    schema:
      severity: string
      recommended_action: string
      prompt_modification_hint: string
      alternative_solutions: list[string]

# 예시 이슈 유형
issue_types:
  - issue_type: "motion_artifact"
    issue_category: "technical"
    severity_levels:
      - level: "critical"
        description: "프레임 간 심각한 워핑/왜곡"
        visual_impact: 0.95
        viewer_perception: "즉시 눈에 띄며 시청 중단 유발"
      - level: "major"
        description: "눈에 띄는 떨림/불연속"
        visual_impact: 0.70
        viewer_perception: "불편하지만 시청 가능"
      - level: "minor"
        description: "약간의 부자연스러움"
        visual_impact: 0.40
        viewer_perception: "자세히 봐야 인지"
    fix_difficulty:
      regeneration_required: true
      prompt_modification: true
      post_processing: false  # 보통 후처리로 해결 불가
      estimated_effort: "medium"
    priority_score_formula: "severity * visual_impact * (1 - fix_difficulty)"
    fix_guidance:
      - severity: "critical"
        recommended_action: "전체 재생성"
        prompt_modification_hint: "동작량 줄이기, 정적 요소 증가"
        alternative_solutions: ["다른 플랫폼 시도", "I2V로 전환"]

  - issue_type: "style_inconsistency"
    issue_category: "aesthetic"
    severity_levels:
      - level: "critical"
        description: "완전히 다른 스타일의 샷"
        visual_impact: 0.90
      - level: "major"
        description: "색감/조명 불일치"
        visual_impact: 0.60
    fix_difficulty:
      regeneration_required: true
      prompt_modification: true
      post_processing: true  # 색보정으로 일부 해결 가능
      estimated_effort: "medium"
    fix_guidance:
      - severity: "critical"
        recommended_action: "스타일 프롬프트 강화 후 재생성"
        prompt_modification_hint: "거장 스타일 키워드 강조, 레퍼런스 이미지 추가"
```

### 3.4 데이터셋: regeneration_prompt_templates

```yaml
id: regeneration_prompt_templates
description: "재생성 가이드 프롬프트 템플릿"
source: "프롬프트 수정 패턴 분석"
size: ~50 documents

schema:
  issue_type:
    type: string

  original_issue:
    type: string

  modification_strategy:
    type: object
    schema:
      add_keywords: list[string]
      remove_keywords: list[string]
      emphasize: list[string]
      restructure: string

  prompt_template:
    type: string
    description: "수정 프롬프트 템플릿"

  negative_prompt_additions:
    type: list[string]

  parameter_adjustments:
    type: object
    schema:
      motion_strength: string  # "decrease", "increase", "keep"
      style_weight: string
      guidance_scale: string

  success_indicators:
    type: list[string]

# 예시 템플릿
regeneration_templates:
  - issue_type: "motion_artifact_face"
    original_issue: "얼굴 움직임 시 왜곡 발생"
    modification_strategy:
      add_keywords: ["stable face", "consistent facial features", "smooth motion"]
      remove_keywords: ["dynamic", "rapid"]
      emphasize: ["portrait quality", "facial integrity"]
      restructure: "얼굴 관련 설명을 프롬프트 앞부분으로 이동"
    prompt_template: "[EMPHASIS: consistent facial features, stable face] {original_scene}, smooth natural movement, portrait quality, {style}"
    negative_prompt_additions: ["face distortion", "warping", "morphing", "unstable"]
    parameter_adjustments:
      motion_strength: "decrease"
      style_weight: "keep"
      guidance_scale: "increase"
    success_indicators:
      - "얼굴 윤곽 유지"
      - "눈/코/입 비율 일정"
      - "표정 전환 자연스러움"

  - issue_type: "style_drift"
    original_issue: "씬 중간에 스타일 변화"
    modification_strategy:
      add_keywords: ["consistent style throughout", "unified aesthetic"]
      emphasize: ["거장 스타일 키워드 반복", "색상 팔레트 명시"]
    prompt_template: "{style_keywords} style maintained throughout, {original_scene}, consistent color palette: {color_palette}, unified visual language"
```

---

## 4. 기능 고도화 설계

### 4.1 다차원 품질 평가 파이프라인

```yaml
quality_director_pipeline:
  stage_1_multi_dimensional_analysis:
    purpose: "다차원 품질 분석"
    inputs:
      - video_segments
      - original_prompts
      - expected_style
    outputs:
      - dimension_scores: dict[dimension, score]
      - issue_list: list[Issue]
    rag_queries:
      - "quality_evaluation_dimensions → 평가 기준"
    logic:
      - "기술적 품질 자동 분석 (모션, 일관성, 아티팩트)"
      - "미학적 품질 분석 (구도, 색감, 조명)"
      - "서사적 품질 분석 (페이싱, 감정 곡선)"

  stage_2_auteur_perspective_review:
    purpose: "거장 시점 리뷰"
    inputs:
      - video_segments
      - auteur_key
      - dimension_scores
    outputs:
      - auteur_feedback: list[AuteurFeedback]
      - signature_check: dict[element, score]
    rag_queries:
      - "auteur_quality_standards → 거장 기준"
    logic:
      - "거장 우선순위 기준 적용"
      - "시그니처 요소 존재 확인"
      - "Deal Breaker 체크"

  stage_3_priority_ranking:
    purpose: "개선 우선순위 결정"
    inputs:
      - issue_list
      - auteur_feedback
    outputs:
      - prioritized_issues: list[PrioritizedIssue]
    rag_queries:
      - "improvement_priority_matrix → 이슈 유형별"
    logic:
      - "심각도 × 영향도 × 수정 난이도 계산"
      - "거장 관점 가중치 적용"
      - "상위 이슈 선정"

  stage_4_regeneration_guide:
    purpose: "재생성 가이드 생성"
    inputs:
      - prioritized_issues
      - original_prompts
    outputs:
      - regeneration_guides: list[RegenerationGuide]
    rag_queries:
      - "regeneration_prompt_templates → 이슈 유형별"
    logic:
      - "각 이슈에 맞는 수정 전략 선택"
      - "구체적 프롬프트 수정안 생성"
      - "파라미터 조정 권장사항"
```

### 4.2 출력 스키마 설계

```python
class QualityDirectorOutput(BaseModel):
    """퀄리티 디렉터 출력 스키마"""

    # 메타데이터
    metadata: ReviewMetadata
    class ReviewMetadata(BaseModel):
        review_id: str
        video_id: str
        auteur_perspective: str
        review_timestamp: str
        total_segments_reviewed: int

    # 종합 점수
    overall_scores: OverallScores
    class OverallScores(BaseModel):
        total_score: float  # 0-100
        grade: str  # A, B, C, D, F
        technical_score: float
        aesthetic_score: float
        narrative_score: float
        auteur_alignment_score: float

    # 차원별 상세 분석
    dimension_analysis: list[DimensionAnalysis]
    class DimensionAnalysis(BaseModel):
        dimension: str
        score: float
        sub_scores: dict[str, float]
        strengths: list[str]
        weaknesses: list[str]

    # 거장 피드백
    auteur_feedback: AuteurFeedback
    class AuteurFeedback(BaseModel):
        auteur_key: str
        perspective_summary: str
        signature_elements_found: list[str]
        signature_elements_missing: list[str]
        deal_breakers_detected: list[str]
        detailed_feedback: list[FeedbackItem]

        class FeedbackItem(BaseModel):
            aspect: str
            observation: str
            auteur_quote: str
            suggestion: str

    # 우선순위화된 이슈
    prioritized_issues: list[PrioritizedIssue]
    class PrioritizedIssue(BaseModel):
        issue_id: str
        segment_id: str
        issue_type: str
        severity: str
        priority_score: float
        description: str
        visual_timestamp: str
        impact_assessment: str

    # 재생성 가이드
    regeneration_guides: list[RegenerationGuide]
    class RegenerationGuide(BaseModel):
        issue_id: str
        original_prompt: str
        modified_prompt: str
        modifications_made: list[str]
        negative_prompt_additions: list[str]
        parameter_changes: dict[str, str]
        expected_improvement: str
        alternative_solutions: list[str]

    # A/B 비교 (있는 경우)
    ab_comparison: ABComparison | None
    class ABComparison(BaseModel):
        version_a_score: float
        version_b_score: float
        recommended_version: str
        comparison_details: dict[str, str]

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     generated_video     ┌─────────────────┐
│ 3.2 비디오      │ ─────────────────────────► │ 4.1 퀄리티      │
│     메이커      │                            │     디렉터      │
└─────────────────┘                            └────────┬────────┘
                                                        │
┌─────────────────┐     original_prompts                │
│ 2.3 프롬프트    │ ────────────────────────────────────│
│     연금술      │                                     │
└─────────────────┘                                     │
                                                        │
┌─────────────────┐     auteur_standards                │
│ 5.1 미학        │ ────────────────────────────────────│
│     디렉터      │                                     │
└─────────────────┘                                     │
                                                        │ regeneration_guides
                                                        │ (피드백 루프)
                                                        ▼
                    ┌─────────────────────────────────────────────────┐
                    │      프롬프트 연금술 / 비주얼 리얼라이저         │
                    │              (재생성)                           │
                    └─────────────────────────────────────────────────┘
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| video_segments | 비디오 메이커 | 품질 분석 | quality_scores | 대시보드 |
| original_prompts | 프롬프트 연금술 | 수정 전략 | modified_prompts | 재생성 |
| auteur_style | 미학 디렉터 | 거장 평가 | auteur_feedback | 피드백 |
| regeneration_guides | - | - | new_generation_input | 비디오 메이커 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 품질 평가 조사

- [ ] VBench 평가 지표 분석
- [ ] 영상 품질 자동 평가 알고리즘
- [ ] 인간 평가 vs 자동 평가 상관관계
- [ ] 미학적 품질 측정 기법

### 6.2 거장 기준 조사

- [ ] 봉준호 품질 기준 분석
- [ ] 놀란 품질 기준 분석
- [ ] 왕가위 품질 기준 분석
- [ ] 미야자키 하야오 품질 기준 분석

### 6.3 피드백 시스템 조사

- [ ] 창작 피드백 심리학 연구
- [ ] 효과적 피드백 형식 연구
- [ ] 우선순위 결정 프레임워크

### 6.4 재생성 조사

- [ ] 프롬프트 수정 패턴 분석
- [ ] 이슈별 해결 전략 정리
- [ ] 자동 프롬프트 수정 알고리즘

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 평가 차원 정의 | 2일 | 평가 체계 |
| 2 | 거장 기준 수집 | 3일 | 거장 DB |
| 3 | 우선순위 매트릭스 | 1일 | 우선순위 규칙 |
| 4 | 재생성 템플릿 | 2일 | 템플릿 DB |
| 5 | 파이프라인 구현 | 3일 | 코드 |
| 6 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 기술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| VBench | 논문 | 비디오 품질 벤치마크 |
| CLIP Score | 논문 | 이미지-텍스트 정합성 |
| FID/KID Metrics | 논문 | 생성 품질 지표 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| OpenCV | https://opencv.org/ | 영상 분석 |
| VMAF | Netflix | 비디오 품질 평가 |

---

## 9. Part 9/10 기술 연계 (2026 보강)

### 9.1 DINOv2 기반 일관성 품질 평가 (Part 9.2)

VideoMemory 평가 메트릭을 품질 평가 시스템에 통합합니다.

```yaml
consistency_quality_metrics:
  method: "DINOv2 feature similarity"

  entity_consistency_evaluation:
    character:
      method: "Grounded SAM → DINOv2 features"
      metrics:
        - "face_consistency: 얼굴 일관성"
        - "body_consistency: 체형 일관성"
        - "costume_consistency: 의상 일관성"
      threshold: 0.70
      scoring: "코사인 유사도 (0-1)"

    prop:
      method: "Grounded SAM → DINOv2 features"
      metrics:
        - "shape_consistency: 형태 일관성"
        - "color_consistency: 색상 일관성"
        - "texture_consistency: 질감 일관성"
      threshold: 0.60
      scoring: "코사인 유사도 (0-1)"

    background:
      method: "프레임 간 배경 영역 DINOv2 유사도"
      metrics:
        - "location_consistency: 장소 일관성"
        - "lighting_consistency: 조명 일관성"
        - "atmosphere_consistency: 분위기 일관성"
      threshold: 0.65
      scoring: "코사인 유사도 (0-1)"

  cross_shot_consistency:
    method: "멀티샷 간 동일 엔티티 추적"
    metrics:
      - "tracking_accuracy: 엔티티 추적 정확도"
      - "identity_preservation: 동일성 유지율"
    benchmark: "StoryMem ST-Bench 기준 +28.7% 향상 목표"
```

### 9.2 VBench 통합 평가 프레임워크 (Part 9.3)

2026 AI 비디오 품질 표준 벤치마크를 적용합니다.

```yaml
vbench_integration:
  purpose: "AI 비디오 품질의 객관적 벡터화"

  evaluation_dimensions:
    video_quality:
      - name: "subject_consistency"
        description: "주체 일관성"
        weight: 0.15

      - name: "background_consistency"
        description: "배경 일관성"
        weight: 0.10

      - name: "temporal_flickering"
        description: "시간적 깜빡임"
        weight: 0.10

      - name: "motion_smoothness"
        description: "모션 부드러움"
        weight: 0.10

      - name: "dynamic_degree"
        description: "역동성 정도"
        weight: 0.05

      - name: "aesthetic_quality"
        description: "미학적 품질"
        weight: 0.15

      - name: "imaging_quality"
        description: "이미징 품질"
        weight: 0.10

    video_text_alignment:
      - name: "object_class"
        description: "객체 클래스 정확도"
        weight: 0.05

      - name: "multiple_objects"
        description: "다중 객체 정확도"
        weight: 0.05

      - name: "spatial_relationship"
        description: "공간 관계 정확도"
        weight: 0.05

      - name: "scene"
        description: "장면 정확도"
        weight: 0.05

      - name: "appearance_style"
        description: "외형 스타일 정확도"
        weight: 0.05

  scoring:
    scale: "0-100"
    aggregation: "weighted_average"
    pass_threshold: 70
```

### 9.3 Multi-Modal 품질 평가 파이프라인

영상 + 오디오 통합 품질 평가

```yaml
multimodal_quality_pipeline:
  video_quality:
    tools:
      - "VBench"
      - "DINOv2 Consistency"
      - "VMAF (Netflix)"
    metrics:
      - "visual_fidelity"
      - "temporal_coherence"
      - "aesthetic_score"

  audio_quality:
    tools:
      - "PESQ (음성 품질)"
      - "STOI (음성 명료도)"
      - "Audio-Visual Sync Score"
    metrics:
      - "speech_clarity"
      - "sfx_timing_accuracy"
      - "ambient_naturalness"
      - "lip_sync_accuracy"

  prompt_alignment:
    tools:
      - "CLIP Score"
      - "ImageBind Cross-Modal"
    metrics:
      - "visual_prompt_match"
      - "audio_prompt_match"
      - "overall_intent_satisfaction"

  integrated_score:
    formula: |
      Q_total = w_v * Q_video + w_a * Q_audio + w_p * Q_prompt
      where:
        w_v = 0.50 (영상 품질 가중치)
        w_a = 0.25 (오디오 품질 가중치)
        w_p = 0.25 (프롬프트 정합성 가중치)
```

### 9.4 자동 이슈 감지 및 재생성 가이드

```yaml
auto_issue_detection:
  issue_categories:
    consistency_issues:
      - type: "character_drift"
        detection: "DINOv2 score < 0.70"
        fix_strategy: "메모리 뱅크 키프레임 강제 주입"
        prompt_modification: "Add reference image, strengthen character description"

      - type: "prop_inconsistency"
        detection: "prop DINOv2 score < 0.60"
        fix_strategy: "소품 레퍼런스 팩 재주입"
        prompt_modification: "Explicitly describe prop details"

      - type: "background_shift"
        detection: "background DINOv2 score < 0.65"
        fix_strategy: "배경 키프레임 활용"
        prompt_modification: "Maintain consistent background setting"

    quality_issues:
      - type: "temporal_flickering"
        detection: "VBench flickering score < 70"
        fix_strategy: "프레임 보간 또는 재생성"
        prompt_modification: "Reduce rapid movements, stabilize camera"

      - type: "motion_artifacts"
        detection: "motion_smoothness < 70"
        fix_strategy: "모션 정도 조절"
        prompt_modification: "Slow down motion, simplify movement"

      - type: "aesthetic_low"
        detection: "aesthetic_quality < 70"
        fix_strategy: "스타일 프롬프트 강화"
        prompt_modification: "Enhance lighting description, add cinematic keywords"

    audio_issues:
      - type: "lip_sync_off"
        detection: "lip_sync_accuracy < 0.80"
        fix_strategy: "Native Audio 재시도 또는 플랫폼 변경"
        prompt_modification: "Simplify dialogue, reduce speech speed"

      - type: "audio_visual_mismatch"
        detection: "av_sync_score < 0.75"
        fix_strategy: "타이밍 조정 또는 재생성"
        prompt_modification: "Align sound cues with visual events"

  regeneration_guide_output:
    format: |
      ## Quality Report
      - Overall Score: {score}/100
      - Pass/Fail: {status}

      ## Detected Issues
      1. {issue_type}: {description}
         - Severity: {high/medium/low}
         - Auto-fix available: {yes/no}

      ## Recommended Actions
      1. {action_description}
         - Modified prompt: "{suggested_prompt}"
         - Expected improvement: {percentage}%

      ## Regeneration Settings
      - Platform: {recommended_platform}
      - Additional references: {reference_ids}
```

### 9.5 수정된 품질 평가 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Quality Director V2 + Multi-Modal                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Input: Generated Video (with Native Audio)                                  │
│     │                                                                        │
│     ├──► Video Frames ─────► VBench Evaluator ─────┐                        │
│     │                                               │                        │
│     ├──► Audio Track ──────► Audio Quality ────────┼───► Unified Score      │
│     │                        (PESQ, STOI)          │                        │
│     │                                               │                        │
│     └──► Original Prompt ──► CLIP/ImageBind ───────┘                        │
│                                                                              │
│                         ┌───────────────────────────────┐                   │
│                         │      Integrated Evaluator      │                   │
│                         │  ┌─────┬─────┬─────┐         │                   │
│                         │  │Video│Audio│Prompt│         │                   │
│                         │  │ 50% │ 25% │ 25% │         │                   │
│                         │  └─────┴─────┴─────┘         │                   │
│                         └───────────────────────────────┘                   │
│                                      │                                       │
│                                      ▼                                       │
│                         ┌───────────────────────────────┐                   │
│                         │     Issue Detection Engine     │                   │
│                         │  - Consistency Issues          │                   │
│                         │  - Quality Issues              │                   │
│                         │  - Audio Issues                │                   │
│                         └───────────────────────────────┘                   │
│                                      │                                       │
│                      ┌───────────────┼───────────────┐                      │
│                      ▼               ▼               ▼                      │
│              ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│              │   Pass      │ │  Fix Guide  │ │ Regenerate  │               │
│              │ (Score≥70)  │ │ (Minor Fix) │ │ (Major Fix) │               │
│              └─────────────┘ └─────────────┘ └─────────────┘               │
│                                      │               │                      │
│                                      └───────────────┘                      │
│                                              │                               │
│                                              ▼                               │
│                         ┌───────────────────────────────┐                   │
│                         │   → Prompt Alchemy (수정)      │                   │
│                         │   → Video Maker (재생성)       │                   │
│                         └───────────────────────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 평가 체계 정의 |
| 2026-01-17 | Part 9/10 기술 연계 (DINOv2, VBench, Multi-Modal 품질 평가) | 완료 | 자동 이슈 감지 구현 |
| 2026-01-17 | 웹 리서치 완료 (VBench 2.0, Video-Bench) | 완료 | 품질 평가 파이프라인 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### AI Video Quality Evaluation 종합 분석

#### 1. VBench 프레임워크 (CVPR 2024 Highlight)

```yaml
vbench_overview:
  title: "VBench: Comprehensive Benchmark Suite for Video Generative Models"
  core_principle: "video generation quality를 세분화된 차원으로 분해"

  dimensions_16:
    video_quality:
      - imaging_quality: "해상도, 선명도, 노이즈 (MUSIQ)"
      - aesthetic_quality: "시각적 매력 (LAION predictor)"
      - temporal_consistency: "프레임 간 일관성"
      - motion_smoothness: "동작 자연스러움 (interpolation model)"
      - motion_effects: "모션 효과 품질"
      - dynamic_degree: "움직임 다양성 (RAFT optical flow)"

    video_condition_consistency:
      - video_text_consistency: "프롬프트 준수"
      - object_class_consistency: "객체 클래스 정확성"
      - color_consistency: "색상 일관성"
      - action_consistency: "액션 정확성"
      - scene_consistency: "장면 구성 일치"
      - subject_consistency: "주체 일관성 (CLIP)"

  human_alignment: "Human preference annotation과 0.52+ correlation"
```

#### 2. VBench-2.0 (Mar 2025) - Intrinsic Faithfulness

```yaml
vbench2_overview:
  title: "Advancing Video Generation Benchmark for Intrinsic Faithfulness"
  focus: "표면적 충실도 → 본질적 충실도"

  dimensions_18:
    human_fidelity:
      - human_consistency: "인체 해부학적 정확성"
      - human_anomaly_detection: "이상 감지"

    creativity:
      - composition: "구도의 창의성"
      - diversity: "다양성"

    controllability:
      - complex_prompt_adherence: "복잡한 프롬프트 준수"
      - camera_control: "카메라 제어 정확성"

    physics:
      - mechanics: "물리 역학"
      - material: "재질 표현"
      - thermotics: "열역학 표현"

    commonsense:
      - motion_rationality: "동작 합리성"
      - instance_preservation: "인스턴스 보존"
      - spatial_relation: "공간 관계"
      - temporal_relation: "시간 관계"
      - multi_view_consistency: "다중 시점 일관성"

  evaluation_methods:
    - "VLM/LLM ensemble evaluation"
    - "Specialist detectors (human anomaly)"
    - "SIFT keypoint matching (geometry)"
```

#### 3. Video-Bench (CVPR 2025) - Human-Aligned

```yaml
video_bench_overview:
  title: "Video-Bench: Human-Aligned Video Generation Benchmark"
  key_innovation: "자동 메트릭과 인간 평가 간 misalignment 해결"

  human_alignment_score: 0.52  # inter-rater agreement와 동등

  evaluation_dimensions:
    imaging_quality: "MUSIQ (0.733 correlation)"
    aesthetic_quality: "LAION (0.702)"
    temporal_consistency: "Custom metric (0.402)"
    motion_effects: "RAFT-based (0.514)"
    video_text_consistency: "ViCLIP (0.732)"
    object_class_consistency: "0.735"
    color_consistency: "0.750"
    action_consistency: "0.718"
    scene_consistency: "0.733"

  mllm_advantage: |
    인간 평가자의 perception bias를 완화
    특히 semantic consistency 관련 차원에서 인간보다 객관적
```

#### 4. 실용 평가 메트릭 구현

```yaml
practical_metrics:
  frame_quality:
    imaging_quality:
      tool: "MUSIQ (trained on SPAQ)"
      output: "0-100 score"
    aesthetic_quality:
      tool: "LAION aesthetic predictor (CLIP + MLP)"
      output: "0-10 score"

  temporal_quality:
    motion_smoothness:
      tool: "VBench interpolation model"
      method: "프레임 간 보간 오류 측정"
    dynamic_degree:
      tool: "RAFT optical flow"
      output: "평균 flow magnitude"

  consistency:
    background_consistency:
      tool: "CLIP embedding similarity"
      threshold: ">= 0.72"
    subject_consistency:
      tool: "DINOv2 feature similarity"
      threshold: ">= 0.63"

  prompt_adherence:
    video_text_consistency:
      tool: "ViCLIP or UMT"
      method: "text-video embedding alignment"
```

#### 5. 2026 모델별 VBench-2.0 성능

| Model | Human Consistency | Composition | Physics | Commonsense |
|-------|-------------------|-------------|---------|-------------|
| Sora | 86.45% | 53.65% | 62.22% | 58.22% |
| Kling 1.6 | 86.99% | 43.89% | 65.55% | 64.38% |
| HunyuanVideo | 88.58% | 43.96% | 76.09% | 43.80% |
| CogVideoX-1.5 | 59.72% | 44.70% | 80.80% | 21.79% |

**Key Insight**: 최고 모델도 Action Faithfulness는 ~50% 수준

#### 6. Crebit Quality Director 구현 권장

```yaml
crebit_quality_pipeline:
  stage1_pre_check:
    - "prompt_complexity_analysis: 복잡도 사전 평가"
    - "estimated_difficulty: 생성 난이도 예측"

  stage2_frame_quality:
    metrics:
      - "MUSIQ: imaging quality (threshold: >= 70)"
      - "LAION: aesthetic score (threshold: >= 6.0)"
    auto_action: "< threshold → regenerate or upscale"

  stage3_temporal_quality:
    metrics:
      - "motion_smoothness: VBench interpolation"
      - "dynamic_degree: RAFT optical flow"
    auto_action: "flickering detected → frame interpolation"

  stage4_consistency:
    metrics:
      - "character_consistency: DINOv2 (>= 0.63)"
      - "prop_consistency: DINOv2 (>= 0.58)"
      - "background_consistency: CLIP (>= 0.72)"
    auto_action: "drift detected → memory bank reference"

  stage5_faithfulness:
    metrics:
      - "video_text_alignment: ViCLIP"
      - "action_accuracy: VBench-2.0 action metric"
    auto_action: "misalignment → regenerate with refined prompt"

  output:
    quality_report:
      overall_score: "weighted average"
      dimension_breakdown: "per-metric scores"
      issues_detected: "specific problems + fix suggestions"
      confidence: "reliability of evaluation"
```

### Sources
- VBench (CVPR 2024 Highlight, Vchitect/VBench GitHub)
- VBench-2.0 (arXiv:2503.21755, Mar 2025)
- Video-Bench (CVPR 2025, arXiv:2504.04907)
- GMI Cloud: Video AI Model Benchmarking
- Emergent Mind: FVD & VBench Metrics
