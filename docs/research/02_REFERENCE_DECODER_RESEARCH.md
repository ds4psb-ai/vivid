# App 1.2: 레퍼런스 해석기 (Reference Decoder) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: 4D (Reference Analysis)

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/classic.py"

# 관련 엔드포인트
endpoints = [
    "POST /dimension/4d/analyze",
    "POST /dimension/4d/analyze/stream",
]

# 현재 기능
current_features = [
    "비디오/이미지 분석",
    "조명, 색감, 구도 기본 분석",
    "거장 스타일 매칭",
]
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| 시네마토그래피 용어 부족 | 분석 정밀도 저하 | 전문 용어 DB 구축 |
| 카메라 문법 분석 미약 | 연출 의도 해석 불가 | 카메라 워크 시맨틱 DB |
| 거장별 시그니처 기법 미구축 | 스타일 매칭 부정확 | 거장 기법 DB 구축 |
| 재현 가이드 생성 미약 | 실용성 저하 | AI 프롬프트 변환 로직 |

---

## 2. 핵심 연구 주제

### 2.1 시네마토그래피 기법 체계화

**연구 질문**:
- 시네마토그래피 기법은 어떻게 분류되는가?
- 각 기법의 감정적/서사적 효과는?
- AI 비디오 생성에서 재현 가능한 기법은?

**조사 대상**:
1. ASC (American Society of Cinematographers) 자료
2. 시네마토그래피 교재 (Blain Brown, Bruce Block 등)
3. 영화 분석 학술 자료

### 2.2 조명 패턴 및 의미론

**연구 질문**:
- 주요 조명 패턴과 각각의 무드는?
- 장르별 조명 관습은?
- AI 이미지/비디오에서 조명을 어떻게 지정하는가?

**조사 대상**:
1. 3-Point Lighting 변형들
2. 장르별 조명 케이스 스터디
3. AI 프롬프트에서의 조명 키워드

### 2.3 카메라 움직임 시맨틱

**연구 질문**:
- 각 카메라 움직임의 서사적 의미는?
- 언제 어떤 움직임을 사용해야 하는가?
- AI 비디오에서 카메라 컨트롤 방법은?

**조사 대상**:
1. 영화 문법 이론 (film grammar)
2. 카메라 움직임별 감정 효과 연구
3. Veo/Kling/Sora 카메라 컨트롤 문서

### 2.4 색채 이론 및 컬러 그레이딩

**연구 질문**:
- 색채가 감정에 미치는 영향은?
- 장르별/거장별 색채 관습은?
- LUT 추천 로직을 어떻게 구축하는가?

**조사 대상**:
1. 색채 심리학 연구
2. 영화 컬러 그레이딩 케이스 스터디
3. LUT 라이브러리 분석

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: cinematography_techniques

```yaml
id: cinematography_techniques
description: "시네마토그래피 기법 종합 사전"
source: "ASC publications, cinematography textbooks, academic papers"
size: ~500 documents

schema:
  technique_id:
    type: string
    example: "dolly_zoom"

  category:
    type: string
    enum: ["shot_type", "camera_movement", "lighting", "composition", "lens", "color"]

  name_en:
    type: string
    example: "Dolly Zoom"

  name_ko:
    type: string
    example: "달리 줌"

  aliases:
    type: list[string]
    example: ["Vertigo effect", "Zolly", "Contra-zoom"]

  description:
    type: string

  emotional_effect:
    type: list[string]
    example: ["disorientation", "realization", "dread"]

  narrative_use:
    type: list[string]
    example: ["character epiphany", "horror reveal", "reality distortion"]

  famous_examples:
    type: list[object]
    schema:
      film: string
      scene: string
      director: string
      year: int
      description: string

  execution_details:
    type: object
    schema:
      equipment: list[string]
      difficulty: string  # "easy", "medium", "hard"
      duration_typical: string

  ai_reproducibility:
    type: object
    schema:
      reproducible: boolean
      platforms: list[string]  # ["veo", "kling", "sora"]
      prompt_keywords: list[string]
      limitations: list[string]

  related_techniques:
    type: list[string]
```

### 3.2 데이터셋: lighting_patterns

```yaml
id: lighting_patterns
description: "조명 패턴 및 무드 매핑"
source: "cinematography guides, lighting tutorials, film analysis"
size: ~50 documents

schema:
  pattern_id:
    type: string
    example: "rembrandt"

  name_en:
    type: string
    example: "Rembrandt Lighting"

  name_ko:
    type: string
    example: "렘브란트 조명"

  description:
    type: string

  setup:
    type: object
    schema:
      key_light_position: string
      key_light_angle: string
      fill_ratio: string
      back_light: boolean
      modifiers: list[string]

  visual_signature:
    type: string
    example: "Triangle of light on shadow side of face"

  mood_associations:
    type: list[string]
    example: ["artistic", "intimate", "classical", "thoughtful"]

  genre_usage:
    type: list[string]
    example: ["drama", "portrait", "period_piece"]

  famous_uses:
    type: list[object]
    schema:
      film: string
      scene: string

  ai_prompt_keywords:
    type: list[string]
    example: ["Rembrandt lighting", "dramatic side light", "triangle shadow"]

  color_temperature_typical:
    type: string
    example: "warm (3200K-4000K)"
```

### 3.3 데이터셋: camera_movement_semantics

```yaml
id: camera_movement_semantics
description: "카메라 움직임의 서사적 의미론"
source: "film grammar theory, directing guides"
size: ~30 documents

schema:
  movement_id:
    type: string
    example: "push_in"

  name_en:
    type: string
    example: "Push In / Dolly In"

  name_ko:
    type: string
    example: "푸시 인 / 달리 인"

  execution:
    type: string
    description: "물리적 실행 방법"

  semantic_meaning:
    type: list[string]
    example: ["intensification", "focus", "realization", "intimacy"]

  emotional_effect:
    type: list[string]
    example: ["empathy", "tension", "curiosity"]

  when_to_use:
    type: list[string]
    example: ["character realizes something", "emotional peak", "detail emphasis"]

  when_not_to_use:
    type: list[string]
    example: ["scene ending", "relaxation moment"]

  pacing_impact:
    type: string
    example: "increases tension, accelerates pacing"

  famous_examples:
    type: list[object]
    schema:
      film: string
      scene: string
      context: string

  ai_implementation:
    type: object
    schema:
      veo_prompt: string
      kling_prompt: string
      sora_prompt: string
      limitations: list[string]

  related_movements:
    type: list[string]
```

### 3.4 데이터셋: famous_scene_analysis

```yaml
id: famous_scene_analysis
description: "명장면 분석 데이터베이스"
source: "Every Frame a Painting, StudioBinder, academic analysis"
size: ~200 documents

schema:
  scene_id:
    type: string
    example: "parasite_stairs_sequence"

  film:
    type: object
    schema:
      title: string
      year: int
      director: string
      cinematographer: string

  scene_description:
    type: string

  timestamp:
    type: string
    example: "1:23:45 - 1:25:30"

  analysis:
    type: object
    schema:
      composition:
        description: string
        techniques: list[string]
        meaning: string

      lighting:
        description: string
        pattern: string
        mood: string

      color:
        dominant_colors: list[string]
        color_meaning: string
        grading_style: string

      camera:
        shot_types: list[string]
        movements: list[string]
        lens: string
        meaning: string

      mise_en_scene:
        set_design: string
        props: list[string]
        blocking: string
        costume: string

      sound:
        diegetic: string
        score: string
        silence: string

  thematic_significance:
    type: string

  recreation_guide:
    type: object
    schema:
      key_elements: list[string]
      ai_prompt_suggestion: string
      recommended_tool: string  # "veo", "kling", "sora"
      difficulty: string
```

---

## 4. 기능 고도화 설계

### 4.1 분석 차원 확장

```yaml
analysis_dimensions_v2:
  composition:
    elements:
      - framing
      - rule_of_thirds
      - golden_ratio
      - symmetry
      - leading_lines
      - depth_layers
      - negative_space
    output:
      - grid_overlay_suggestion
      - focal_points_identified
      - composition_technique_name
      - emotional_effect
      - recreation_prompt

  lighting:
    elements:
      - key_light_direction
      - key_light_quality  # hard/soft
      - fill_ratio
      - color_temperature
      - practicals  # in-frame light sources
      - shadows
      - highlights
    output:
      - lighting_pattern_name
      - mood_interpretation
      - setup_description
      - ai_prompt_keywords

  color:
    elements:
      - dominant_hues
      - saturation_level
      - contrast_level
      - color_harmony_type
      - temperature
    output:
      - color_palette_hex
      - mood_keywords
      - grading_style_name
      - lut_recommendation
      - ai_prompt_keywords

  camera:
    elements:
      - shot_type
      - lens_focal_length_equivalent
      - depth_of_field
      - movement_type
      - movement_speed
      - movement_motivation
    output:
      - camera_grammar_interpretation
      - emotional_effect
      - narrative_purpose
      - recreation_prompt_per_platform

  mise_en_scene:
    elements:
      - set_design_style
      - key_props
      - actor_blocking
      - costume_notes
      - depth_staging
    output:
      - style_keywords
      - prop_list_for_recreation
      - blocking_diagram_description

  audio:  # 비디오 분석 시
    elements:
      - diegetic_sounds
      - score_mood
      - silence_usage
      - dialogue_pacing
    output:
      - sound_design_notes
      - music_style_suggestion
      - suno_prompt_hint
```

### 4.2 거장 매칭 로직 고도화

```python
class AuteurMatchingEngine:
    """분석 결과와 거장 스타일 매칭"""

    def match(self, analysis: ReferenceAnalysis) -> list[AuteurMatch]:
        """
        분석 결과를 기반으로 가장 유사한 거장 스타일 추출

        매칭 기준:
        1. 구도 유사도 (composition_similarity)
        2. 조명 유사도 (lighting_similarity)
        3. 색감 유사도 (color_similarity)
        4. 카메라 문법 유사도 (camera_grammar_similarity)
        5. 주제의식 유사도 (thematic_similarity)
        """
        pass

    def get_auteur_techniques(self, auteur_key: str) -> list[Technique]:
        """거장의 시그니처 기법 조회"""
        pass

    def generate_style_blend(
        self,
        primary_auteur: str,
        secondary_auteur: str,
        blend_ratio: float = 0.7
    ) -> StyleGuide:
        """두 거장 스타일 블렌딩"""
        pass
```

### 4.3 AI 프롬프트 변환 로직

```python
class PromptGenerator:
    """분석 결과 → AI 프롬프트 변환"""

    def generate_image_prompt(
        self,
        analysis: ReferenceAnalysis,
        platform: str = "midjourney"
    ) -> str:
        """이미지 생성 프롬프트 생성"""
        pass

    def generate_video_prompt(
        self,
        analysis: ReferenceAnalysis,
        platform: str = "veo"
    ) -> str:
        """비디오 생성 프롬프트 생성"""
        pass

    def generate_recreation_guide(
        self,
        analysis: ReferenceAnalysis
    ) -> RecreationGuide:
        """
        완전한 재현 가이드 생성

        Returns:
            - composition_setup: 구도 설정 가이드
            - lighting_setup: 조명 셋업 가이드
            - color_direction: 색감 방향
            - camera_direction: 카메라 연출
            - prompts: 플랫폼별 프롬프트
        """
        pass
```

---

## 5. 조사 필요 항목 체크리스트

### 5.1 시네마토그래피 기법

- [ ] 샷 유형 완전 분류 (50+ 유형)
- [ ] 카메라 움직임 전체 분류 (20+ 유형)
- [ ] 렌즈 효과 분류 (광각, 망원, 매크로 등)
- [ ] 합성 기법 분류

### 5.2 조명 패턴

- [ ] 기본 조명 패턴 10가지+
- [ ] 장르별 조명 관습
- [ ] 시간대별 조명 특성 (golden hour 등)
- [ ] 실내/실외 조명 차이

### 5.3 색채 이론

- [ ] 색채 심리학 핵심 정리
- [ ] 영화 컬러 그레이딩 트렌드
- [ ] 장르별 색채 관습
- [ ] 거장별 색채 팔레트

### 5.4 거장 분석

- [ ] 봉준호 시그니처 기법 20가지+
- [ ] 놀란 시그니처 기법 20가지+
- [ ] 빌뇌브 시그니처 기법 20가지+
- [ ] 왕가위 시그니처 기법 20가지+
- [ ] 타란티노 시그니처 기법 20가지+

### 5.5 AI 플랫폼 프롬프트

- [ ] Veo 3.1 카메라 컨트롤 문법
- [ ] Kling 2.6 프롬프트 패턴
- [ ] Sora 2 프롬프트 패턴
- [ ] Midjourney V6 프롬프트 패턴

---

## 6. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 기법 분류 체계 수립 | 2일 | 분류 스키마 |
| 2 | 기법 데이터 수집 | 5일 | 500+ 기법 문서 |
| 3 | 명장면 분석 수집 | 3일 | 200+ 분석 문서 |
| 4 | Qdrant 적재 | 1일 | 벡터 DB |
| 5 | 분석 로직 구현 | 3일 | 코드 |
| 6 | 프롬프트 변환 로직 | 2일 | 코드 |
| 7 | 테스트 | 2일 | 테스트 결과 |

---

## 7. 참고 자료

### 핵심 자료

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| Cinematography: Theory and Practice | 교재 | 시네마토그래피 기본 |
| The Visual Story | 교재 | 시각적 스토리텔링 |
| Every Frame a Painting | 유튜브 | 영화 분석 에세이 |
| StudioBinder | 웹사이트 | 영화 제작 가이드 |

### 이미 수집된 정보 (매크로 문서에서)

- 구도 법칙 (Rule of Thirds, Golden Ratio)
- 조명 비율 및 무드 매핑
- 카메라 움직임 시맨틱 기본

---

## 8. Part 9/10 기술 연계 (2026 보강)

### 8.1 Multi-Modal Embedding 통합 (Part 9.3)

레퍼런스 해석기는 **Multi-Modal Embedding**의 핵심 활용처입니다.

#### ImageBind 기반 Cross-Modal 검색

```yaml
multimodal_search_integration:
  purpose: "레퍼런스 영상/이미지 → 유사 씬 검색"

  use_cases:
    reference_to_similar:
      description: "업로드된 레퍼런스로 유사한 명장면 검색"
      flow:
        - "사용자가 이미지/비디오 업로드"
        - "ImageBind 1024D 임베딩 생성"
        - "famous_scene_analysis 컬렉션에서 유사도 검색"
        - "매칭되는 명장면 분석 결과 반환"
      benefit: "언어 설명 없이 시각적 유사성 기반 검색"

    audio_to_scene:
      description: "BGM/분위기 오디오로 어울리는 씬 추천"
      flow:
        - "오디오 입력"
        - "ImageBind 오디오 임베딩"
        - "Cross-Modal: 오디오 → 비디오/이미지 공간 검색"
        - "분위기 매칭 씬 추천"
      benefit: "음악 분위기와 맞는 영상 레퍼런스 자동 추천"

    auteur_style_match:
      description: "레퍼런스 → 거장 스타일 벡터 매칭"
      flow:
        - "레퍼런스 임베딩"
        - "AUTEUR_DNA 소스와 유사도 비교"
        - "가장 유사한 거장 스타일 + 근거 제시"
      benefit: "객관적 벡터 거리 기반 스타일 매칭"

  implementation:
    embedder: "ImageBind (1024D) 또는 Vertex AI Multimodal (1408D)"
    storage: "Qdrant Named Vectors (image_embed, video_embed)"
    retrieval: "CrossModalRetriever + RRF Fusion"
```

#### Vertex AI Video Embedding 활용

```yaml
vertex_video_analysis:
  purpose: "비디오 세그먼트별 임베딩으로 정밀 분석"

  workflow:
    step_1:
      action: "비디오를 8-15초 세그먼트로 분할"
      mode: "standard (max 8 embeddings/min)"

    step_2:
      action: "각 세그먼트 1408D 임베딩 생성"
      includes: ["시각적 특성", "오디오 특성", "모션 특성"]

    step_3:
      action: "세그먼트별 분석 결과 집계"
      output:
        - "전체 영상 톤 분석"
        - "키 모먼트 식별"
        - "스타일 변화 감지"

  benefits:
    - "긴 영상도 세그먼트별 정밀 분석"
    - "시간축 따른 스타일 변화 감지"
    - "키 모먼트 자동 식별"
```

### 8.2 Multi-RAG Router 연동 (Part 10.3)

레퍼런스 분석 시 **다중 RAG 소스**를 자동 라우팅합니다.

```yaml
rag_routing_strategy:
  query_type: "reference_analysis"

  sources_used:
    tier_1_auteur_dna:
      source_type: "AUTEUR_DNA"
      backend: "notebooklm.py (NotebookLM CDP)"
      purpose: "거장의 시그니처 기법 데이터"
      queries:
        - "봉준호의 계단 구도 활용"
        - "놀란의 시간 구조 기법"
        - "왕가위의 색감 특징"

    tier_2_multimodal:
      source_type: "MULTIMODAL_DIMENSION"
      backend: "multimodal_qdrant.py"
      purpose: "비주얼 유사성 검색"
      collections:
        - "cinematography_techniques"
        - "famous_scene_analysis"
        - "lighting_patterns"

    tier_3_user_history:
      source_type: "USER_HISTORY"
      backend: "user_history.py (PostgreSQL)"
      purpose: "사용자 이전 분석/작업 참조"
      use_case: "이전에 분석한 레퍼런스와 비교"

  routing_logic:
    rule_based:
      - "거장 이름 언급 → AUTEUR_DNA 우선"
      - "영상/이미지 첨부 → MULTIMODAL_DIMENSION 우선"
      - "이전 작업 참조 → USER_HISTORY 포함"

    llm_based:
      trigger: "복합 쿼리 또는 모호한 의도"
      example: "느와르 분위기의 봉준호 스타일" → [AUTEUR_DNA, MULTIMODAL_DIMENSION]
```

### 8.3 evidence_refs 자동 생성

분석 결과에 **근거 출처**를 명시합니다.

```python
# 분석 결과 예시
analysis_result = {
    "lighting_pattern": "Rembrandt Lighting",
    "mood": "dramatic, intimate",
    "auteur_match": "Roger Deakins style",

    "evidence_refs": [
        "rag:cinematography_techniques:lighting_patterns:rembrandt_001",
        "rag:auteur_dna:deakins:lighting_signature",
        "db:famous_scenes:no_country_bar_scene"
    ]
}
```

### 8.4 수정된 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Reference Decoder V2 Architecture                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Input                                                                  │
│     │                                                                        │
│     ├──► Image ─────► ImageBind/Vertex ─────┐                               │
│     ├──► Video ─────► Vertex Video Embed ───┼───► Unified 1024D/1408D       │
│     └──► Text Query ─► Gemini Text Embed ───┘         Embedding              │
│                                                          │                   │
│                         ┌────────────────────────────────┘                   │
│                         ▼                                                    │
│              ┌──────────────────────┐                                       │
│              │   Multi-RAG Router   │                                       │
│              │   (Intelligent)      │                                       │
│              └──────────────────────┘                                       │
│                         │                                                    │
│           ┌─────────────┼─────────────┐                                     │
│           ▼             ▼             ▼                                     │
│   ┌─────────────┐ ┌──────────┐ ┌─────────────┐                             │
│   │ NotebookLM  │ │ Qdrant   │ │ PostgreSQL  │                             │
│   │ AUTEUR_DNA  │ │ MM-RAG   │ │ USER_HIST   │                             │
│   └─────────────┘ └──────────┘ └─────────────┘                             │
│           │             │             │                                     │
│           └─────────────┼─────────────┘                                     │
│                         ▼                                                    │
│              ┌──────────────────────┐                                       │
│              │   RRF Fusion +       │                                       │
│              │   Analysis Engine    │                                       │
│              └──────────────────────┘                                       │
│                         │                                                    │
│                         ▼                                                    │
│              ┌──────────────────────┐                                       │
│              │  Structured Output   │                                       │
│              │  + evidence_refs     │                                       │
│              └──────────────────────┘                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 시네마토그래피 자료 수집 |
| 2026-01-17 | Part 9/10 기술 연계 (Multi-Modal Embedding, Multi-RAG Router) | 완료 | Cross-Modal 검색 구현 |
| 2026-01-17 | 웹 리서치 완료 (ImageBind, Vertex AI Multimodal) | 완료 | 멀티모달 검색 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### Multi-Modal Embedding 기술 종합 분석

#### 1. ImageBind (Meta AI)

```yaml
imagebind_specs:
  developer: "Meta AI"
  release: "2023 (Updated 2025)"

  modalities_supported: 6
  modalities:
    - image: "Primary anchor modality"
    - text: "Natural language descriptions"
    - audio: "Sound, speech, music"
    - video: "Temporal visual sequences"
    - depth: "3D depth maps"
    - thermal: "Infrared imagery"
    - imu: "Inertial measurement unit data"

  embedding_dimension: 1024

  key_innovation: |
    Image를 anchor로 사용하여 모든 modality를
    동일한 embedding space에 정렬
    → 학습 없이 cross-modal retrieval 가능

  use_cases:
    - "이미지 → 유사 오디오 검색"
    - "오디오 → 유사 비디오 검색"
    - "텍스트 → 멀티모달 검색"
```

#### 2. Vertex AI Multimodal Embedding

```yaml
vertex_multimodal_specs:
  model: "multimodalembedding@001"
  provider: "Google Cloud"

  embedding_dimensions:
    - 128: "Fast, lightweight"
    - 256: "Balanced"
    - 512: "Standard"
    - 1408: "Maximum fidelity"

  pricing:
    text: "$0.0002 per 1K characters"
    image: "$0.0006 per image"
    video:
      essential: "$0.00008/sec (text+visual)"
      standard: "$0.00016/sec (audio + long video)"
      plus: "$0.00024/sec (everything)"

  video_modes:
    essential: "Visual + Text only"
    standard: "+ Audio, longer videos"
    plus: "All features, highest quality"

  capabilities:
    - "이미지/텍스트 → 임베딩"
    - "비디오 → 임베딩 (프레임 샘플링)"
    - "Cross-modal similarity search"
```

#### 3. 플랫폼 비교

| Feature | ImageBind | Vertex AI |
|---------|-----------|-----------|
| Modalities | 6 | 3 (text, image, video) |
| Embedding Dim | 1024 fixed | 128/256/512/1408 |
| Pricing | Open source | Pay-per-use |
| Deployment | Self-hosted | Cloud API |
| Audio Support | Native | Via video mode |
| Real-time | Requires GPU | Cloud-managed |

#### 4. Crebit Reference Decoder 구현 권장

```yaml
crebit_reference_implementation:
  multimodal_search_pipeline:
    step1_upload:
      - "레퍼런스 영상/이미지 업로드"
      - "자동 썸네일 추출"

    step2_embedding:
      primary: "ImageBind (6-modality, self-hosted)"
      fallback: "Vertex AI (cloud API)"
      storage: "Qdrant Named Vectors"
        - "image_embed: 1024D"
        - "video_embed: 1024D"
        - "audio_embed: 1024D"

    step3_search:
      image_to_similar: "시각적 유사 씬 검색"
      audio_to_scene: "음악/분위기 → 매칭 씬"
      text_to_reference: "텍스트 설명 → 레퍼런스"

  cross_modal_use_cases:
    reference_to_similar:
      input: "레퍼런스 영상 URL"
      output: "유사 씬 리스트 + 유사도 점수"

    audio_mood_to_visual:
      input: "배경음악 또는 음악 설명"
      output: "분위기 매칭 시각적 레퍼런스"

    auteur_style_match:
      input: "거장 키 + 씬 타입"
      output: "해당 스타일의 레퍼런스 씬들"

  qdrant_schema:
    collection: "reference_scenes"
    vectors:
      image_embed:
        size: 1024
        distance: "Cosine"
      video_embed:
        size: 1024
        distance: "Cosine"
      audio_embed:
        size: 1024
        distance: "Cosine"
    payload:
      - source_url
      - scene_description
      - auteur_tags
      - cinematography_notes
```

### Sources
- Meta AI ImageBind Paper (2023)
- Google Cloud Vertex AI Multimodal Embedding Documentation
- Qdrant Named Vectors Documentation
