# App 1.3: 시나리오 생성기 (Scenario Generator) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: Story

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/story.py"

# 엔드포인트
endpoints = [
    "POST /dimension/story/architect",
    "POST /dimension/story/architect/stream",
    "POST /dimension/story/refine",
    "POST /dimension/story/refine/stream",
    "POST /dimension/story/shot-list",
]

# 현재 기능
current_features = [
    "시나리오 생성 (story_architect)",
    "컨셉 정제 (story_refine)",
    "샷 리스트 생성 (shot_list)",
    "SSE 스트리밍 지원",
    "Intent-Resolver 연동",
    "RAG 통합 (use_rag=True)",
]

# 현재 입력 스키마
StoryArchitectRequest = {
    "concept": "str",           # 비디오 컨셉
    "persona_data": "str",      # 페르소나 DNA
    "reference_analysis": "str", # 레퍼런스 분석
    "genre": "str",             # 장르 (drama, action 등)
    "duration": "int",          # 목표 길이 (초)
    "structure": "str",         # 서사 구조 (3-act 등)
    "language": "str",          # 출력 언어
    "model": "str",             # AI 모델
}
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| 서사 구조 템플릿 부족 | 다양성 제한 | 거장별 서사 구조 DB 구축 |
| 장르별 공식 미흡 | 장르 특성 반영 약함 | 장르 공식 + 비트 시트 |
| 감정 곡선 생성 없음 | 페이싱 최적화 불가 | 감정 아크 설계 기능 |
| 샷 리스트 AI 도구 매핑 고도화 필요 | 비효율적 도구 선택 | 2026 도구 스펙 기반 휴리스틱 |

---

## 2. 핵심 연구 주제

### 2.1 서사 구조 연구

**연구 질문**:
- 거장 감독들이 사용하는 서사 구조는?
- 각 서사 구조의 비트 시트(Beat Sheet)는?
- 영상 길이별 최적 비트 배치는?

**조사 대상**:
1. Blake Snyder's Save the Cat! Beat Sheet
2. Dan Harmon's Story Circle (8-Point Arc)
3. Kishōtenketsu (기승전결) - 동아시아 4막 구조
4. Syd Field's 3-Act Paradigm
5. Robert McKee's Story Structure

### 2.2 장르 공식 연구

**연구 질문**:
- 각 장르의 필수 요소(Tropes)는?
- 장르별 감정 곡선 패턴은?
- 장르 혼합(Genre Hybrid) 규칙은?

**조사 대상**:
1. Film Genre Theory (Rick Altman, Barry Keith Grant)
2. TV Tropes 데이터 (학술적 활용)
3. 거장별 장르 해석 분석

### 2.3 감정 페이싱 연구

**연구 질문**:
- 시간당 최적 감정 변화량은?
- 감정 피크 배치 공식은?
- 짧은 영상(1-3분)의 페이싱 규칙은?

**조사 대상**:
1. Kurt Vonnegut's Story Shapes
2. 영화 감정 분석 연구 (sentiment analysis)
3. 뮤직비디오/광고 페이싱 연구

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: story_structure_templates

```yaml
id: story_structure_templates
description: "서사 구조 템플릿 및 비트 시트"
source: "시나리오 작법 서적, 학술 연구"
size: ~100 documents

schema:
  structure_id:
    type: string
    example: "save_the_cat_15"

  structure_name:
    type: string
    example: "Save the Cat! 15 Beat Sheet"

  origin:
    type: string
    description: "구조의 기원 (서양 3막, 동아시아 4막 등)"

  total_beats:
    type: int
    example: 15

  beats:
    type: list[object]
    schema:
      beat_number: int
      beat_name: string
      position_percent: float  # 전체 대비 위치 (0-100%)
      duration_percent: float  # 전체 대비 길이
      purpose: string
      emotional_tone: string
      common_content: list[string]
      examples:
        type: list[object]
        schema:
          film: string
          description: string

  duration_adaptations:
    type: object
    description: "길이별 적용 방법"
    schema:
      short_1min:
        beats_to_keep: list[int]
        pacing_notes: string
      medium_3min:
        beats_to_keep: list[int]
        pacing_notes: string
      long_10min:
        beats_to_keep: list[int]
        pacing_notes: string

  suitable_genres:
    type: list[string]

  auteur_examples:
    type: list[object]
    schema:
      auteur_key: string
      film: string
      adaptation_notes: string

# 예시 데이터
example_document:
  structure_id: "save_the_cat_15"
  structure_name: "Save the Cat! 15 Beat Sheet"
  origin: "western_3act"
  total_beats: 15
  beats:
    - beat_number: 1
      beat_name: "Opening Image"
      position_percent: 0
      duration_percent: 1
      purpose: "시각적 메타포로 세계관 제시"
      emotional_tone: "curious"
      common_content: ["주인공의 일상", "분위기 설정", "테마 힌트"]
      examples:
        - film: "기생충"
          description: "반지하 창문, 거리의 취객"
    - beat_number: 2
      beat_name: "Theme Stated"
      position_percent: 5
      duration_percent: 2
      purpose: "영화의 핵심 테마를 대사로 암시"
      emotional_tone: "contemplative"
  duration_adaptations:
    short_1min:
      beats_to_keep: [1, 5, 8, 14, 15]  # Opening, Catalyst, Midpoint, Climax, Closing
      pacing_notes: "5비트로 압축, 각 12초"
    medium_3min:
      beats_to_keep: [1, 2, 5, 8, 12, 14, 15]
      pacing_notes: "7비트, 평균 25초"
```

### 3.2 데이터셋: genre_formula_db

```yaml
id: genre_formula_db
description: "장르별 필수 요소 및 공식"
source: "영화학 연구, TV Tropes 분석"
size: ~50 documents

schema:
  genre_id:
    type: string
    example: "psychological_thriller"

  genre_name_ko:
    type: string
    example: "심리 스릴러"

  genre_name_en:
    type: string
    example: "Psychological Thriller"

  parent_genres:
    type: list[string]
    description: "상위 장르"
    example: ["thriller", "drama"]

  required_elements:
    type: list[object]
    schema:
      element_name: string
      importance: float  # 0-1
      description: string
      examples: list[string]

  forbidden_elements:
    type: list[object]
    description: "장르 규칙 위반 요소"
    schema:
      element: string
      reason: string

  emotional_curve:
    type: object
    schema:
      opening_tone: string
      midpoint_shift: string
      climax_peak: string
      resolution_tone: string
      tension_pattern: string  # "escalating", "oscillating", "slow_burn"

  pacing_rules:
    type: object
    schema:
      avg_shot_duration: float  # 초
      dialogue_to_action_ratio: float
      quiet_moment_frequency: string

  visual_conventions:
    type: list[object]
    schema:
      convention: string
      usage: string
      examples: list[string]

  audio_conventions:
    type: list[object]
    schema:
      convention: string
      usage: string

  hybrid_compatibility:
    type: list[object]
    description: "혼합 가능한 장르"
    schema:
      genre: string
      compatibility_score: float
      combination_notes: string

  auteur_interpretations:
    type: list[object]
    schema:
      auteur_key: string
      unique_approach: string
      signature_techniques: list[string]

# 예시 데이터
example_document:
  genre_id: "psychological_thriller"
  genre_name_ko: "심리 스릴러"
  required_elements:
    - element_name: "unreliable_perspective"
      importance: 0.9
      description: "관객의 인식을 흔드는 시점"
      examples: ["신뢰할 수 없는 화자", "반전", "환각/망상"]
    - element_name: "internal_conflict"
      importance: 0.85
      description: "주인공의 내면 갈등"
    - element_name: "paranoia_atmosphere"
      importance: 0.8
      description: "불안과 의심의 분위기"
  emotional_curve:
    opening_tone: "uneasy_calm"
    midpoint_shift: "reality_crack"
    climax_peak: "psychological_breakdown"
    resolution_tone: "ambiguous_dread"
    tension_pattern: "slow_burn"
  auteur_interpretations:
    - auteur_key: "nolan"
      unique_approach: "시간 조작을 통한 심리 혼란"
      signature_techniques: ["nested_timelines", "memory_unreliability"]
    - auteur_key: "fincher"
      unique_approach: "차가운 미장센과 디테일"
      signature_techniques: ["meticulous_framing", "dread_building"]
```

### 3.3 데이터셋: emotional_arc_patterns

```yaml
id: emotional_arc_patterns
description: "감정 곡선 패턴 및 페이싱 규칙"
source: "Kurt Vonnegut 이론, 영화 감정 분석"
size: ~30 documents

schema:
  pattern_id:
    type: string
    example: "rags_to_riches"

  pattern_name:
    type: string
    example: "Rags to Riches"

  description:
    type: string

  emotional_trajectory:
    type: list[object]
    schema:
      position_percent: float
      emotional_value: float  # -1 (최저) ~ +1 (최고)
      label: string

  suitable_genres:
    type: list[string]

  suitable_durations:
    type: list[string]
    example: ["short", "medium", "long"]

  peak_placement:
    type: object
    schema:
      primary_peak_percent: float
      secondary_peaks: list[float]
      valley_placement: list[float]

  pacing_recommendations:
    type: object
    schema:
      transition_speed: string  # "slow", "medium", "fast"
      contrast_intensity: float  # 0-1
      breathing_room: float  # 감정 휴식 비율

  music_sync_notes:
    type: string
    description: "음악과의 동기화 권장사항"

  example_films:
    type: list[object]
    schema:
      film: string
      director: string
      analysis: string

# 예시: Kurt Vonnegut's 6 Story Shapes
story_shapes:
  - pattern_id: "rags_to_riches"
    description: "지속적 상승 - 행운이 찾아온 주인공"
    emotional_trajectory:
      - {position_percent: 0, emotional_value: -0.6, label: "humble_beginning"}
      - {position_percent: 25, emotional_value: -0.3, label: "first_opportunity"}
      - {position_percent: 50, emotional_value: 0.2, label: "rising"}
      - {position_percent: 75, emotional_value: 0.6, label: "near_success"}
      - {position_percent: 100, emotional_value: 0.9, label: "triumph"}

  - pattern_id: "man_in_hole"
    description: "상승-하강-재상승 - 가장 보편적"
    emotional_trajectory:
      - {position_percent: 0, emotional_value: 0.3, label: "normal_life"}
      - {position_percent: 30, emotional_value: -0.7, label: "fall_into_hole"}
      - {position_percent: 60, emotional_value: -0.3, label: "struggle"}
      - {position_percent: 100, emotional_value: 0.8, label: "climb_out"}

  - pattern_id: "icarus"
    description: "상승 후 추락 - 비극적 결말"
    emotional_trajectory:
      - {position_percent: 0, emotional_value: 0.0, label: "ordinary"}
      - {position_percent: 40, emotional_value: 0.8, label: "peak"}
      - {position_percent: 70, emotional_value: 0.2, label: "hubris"}
      - {position_percent: 100, emotional_value: -0.8, label: "fall"}
```

### 3.4 데이터셋: shot_tool_heuristics_2026

```yaml
id: shot_tool_heuristics_2026
description: "2026 AI 비디오 도구 샷 선택 휴리스틱"
source: "도구 스펙, 실험 결과"
size: ~50 documents

schema:
  shot_scenario:
    type: string
    example: "character_closeup_emotional"

  description:
    type: string

  recommended_tool:
    type: string
    enum: ["veo", "kling", "sora"]

  recommendation_score:
    type: float
    description: "0-1 신뢰도"

  reasoning:
    type: string

  tool_parameters:
    type: object
    schema:
      optimal_duration: float
      motion_guidance: string
      style_preset: string

  fallback_tool:
    type: string

  fallback_condition:
    type: string

  quality_metrics:
    type: object
    schema:
      facial_fidelity: float
      motion_consistency: float
      style_adherence: float

# 휴리스틱 규칙 (2026 도구 스펙 기반)
heuristic_rules:
  - shot_scenario: "extreme_closeup_face"
    recommended_tool: "kling"
    recommendation_score: 0.95
    reasoning: "Kling 2.6의 안면 보존력 최고 (CLIP-Face 0.92)"
    tool_parameters:
      optimal_duration: 3.0
      motion_guidance: "minimal"
      style_preset: "photorealistic"

  - shot_scenario: "action_sequence_fullbody"
    recommended_tool: "sora"
    recommendation_score: 0.90
    reasoning: "Sora 2 Pro의 동작 연속성 최고 (FID-Motion 12.3)"
    tool_parameters:
      optimal_duration: 5.0
      motion_guidance: "high_energy"
      style_preset: "cinematic_action"

  - shot_scenario: "establishing_shot_atmospheric"
    recommended_tool: "veo"
    recommendation_score: 0.88
    reasoning: "Veo 3.1의 분위기 표현력 + 네이티브 오디오"
    tool_parameters:
      optimal_duration: 8.0
      motion_guidance: "slow_pan"
      style_preset: "cinematic"
```

---

## 4. 기능 고도화 설계

### 4.1 분석 파이프라인 고도화

```yaml
scenario_generation_pipeline_v2:
  stage_1_input_analysis:
    purpose: "입력 분석 및 구조 선택"
    inputs:
      - concept
      - persona_dna
      - reference_analysis
      - genre
      - duration
    outputs:
      - recommended_structure
      - genre_formula
      - emotional_arc
    rag_queries:
      - "story_structure_templates → duration + genre 기반"
      - "genre_formula_db → genre 기반"
      - "emotional_arc_patterns → persona 기반"

  stage_2_beat_generation:
    purpose: "비트 시트 생성"
    inputs:
      - concept
      - selected_structure
      - duration
    outputs:
      - beat_sheet: list[Beat]
    logic:
      - "선택된 구조의 비트 템플릿 로드"
      - "duration에 맞게 비트 수 조정"
      - "concept 기반 비트별 내용 생성"

  stage_3_emotional_mapping:
    purpose: "감정 곡선 매핑"
    inputs:
      - beat_sheet
      - persona_dna
      - genre_formula
    outputs:
      - emotional_curve: list[EmotionalPoint]
    logic:
      - "persona의 선호 감정 패턴 반영"
      - "장르 규칙에 맞는 감정 흐름 조정"

  stage_4_scene_detailing:
    purpose: "씬 상세화"
    inputs:
      - beat_sheet
      - emotional_curve
      - reference_analysis
    outputs:
      - scenes: list[Scene]
    logic:
      - "각 비트를 구체적 씬으로 변환"
      - "레퍼런스 스타일 반영"

  stage_5_shot_breakdown:
    purpose: "샷 분해 및 도구 추천"
    inputs:
      - scenes
      - total_duration
    outputs:
      - shot_list: list[TimelineShot]
      - tool_allocation: dict
    rag_queries:
      - "shot_tool_heuristics_2026 → 샷 유형별 도구"
```

### 4.2 출력 스키마 고도화

```python
class ScenarioOutput(BaseModel):
    """고도화된 시나리오 출력 스키마"""

    # 메타데이터
    metadata: ScenarioMetadata
    class ScenarioMetadata(BaseModel):
        title: str
        logline: str  # 한 줄 요약
        genre: str
        sub_genres: list[str]
        duration: int  # 초
        structure_used: str
        emotional_arc_type: str

    # 비트 시트
    beat_sheet: BeatSheet
    class BeatSheet(BaseModel):
        structure_name: str
        total_beats: int
        beats: list[Beat]

        class Beat(BaseModel):
            number: int
            name: str
            time_range: str  # "0:00-0:15"
            duration_seconds: int
            summary: str
            emotional_value: float  # -1 ~ +1
            key_action: str
            dialogue_snippet: str | None

    # 감정 곡선
    emotional_curve: EmotionalCurve
    class EmotionalCurve(BaseModel):
        arc_type: str
        peaks: list[EmotionalPeak]
        valleys: list[EmotionalValley]
        overall_trajectory: str

        class EmotionalPeak(BaseModel):
            time_position: float  # 0-1
            intensity: float
            emotion_type: str

        class EmotionalValley(BaseModel):
            time_position: float
            depth: float
            purpose: str  # "breathing_room", "contrast", "setup"

    # 씬 리스트
    scenes: list[Scene]
    class Scene(BaseModel):
        scene_number: int
        beat_reference: int
        time_range: str
        location: str
        characters: list[str]
        action_summary: str
        dialogue: str | None
        visual_notes: str
        audio_notes: str
        mood: str

    # 샷 리스트 (선택적)
    shot_list: ShotList | None
    class ShotList(BaseModel):
        total_shots: int
        shots: list[TimelineShot]
        tool_distribution: dict[str, int]

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     persona_dna     ┌─────────────────┐
│ 1.1 심연의 거울 │ ────────────────────► │ 1.3 시나리오    │
└─────────────────┘                      │     생성기      │
                                         └────────┬────────┘
┌─────────────────┐   reference_analysis          │
│ 1.2 레퍼런스   │ ───────────────────────────────│
│     해석기     │                                │
└─────────────────┘                               │ scenario + beat_sheet
                                                  │
                    ┌─────────────────────────────┼─────────────────────┐
                    │                             │                     │
                    ▼                             ▼                     ▼
          ┌─────────────────┐         ┌─────────────────┐     ┌─────────────────┐
          │ 2.1 사운드      │         │ 2.2 스토리보드  │     │ 2.3 프롬프트    │
          │     크래프터    │         │     스케치      │     │     연금술      │
          └─────────────────┘         └─────────────────┘     └─────────────────┘
               (BGM 생성)               (시각적 스토리보드)       (AI 프롬프트)
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| persona_dna | 심연의 거울 | 성향 기반 구조 선택 | structure_hint | 내부 처리 |
| reference_analysis | 레퍼런스 해석기 | 스타일 반영 | scene_style | 씬 상세화 |
| scenario | - | - | beat_sheet | 사운드 크래프터 |
| scenario | - | - | scene_descriptions | 스토리보드 스케치 |
| shot_list | - | - | shot_descriptions | 프롬프트 연금술 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 서사 구조 조사

- [ ] Save the Cat! 15 비트 시트 상세 분석
- [ ] Dan Harmon Story Circle 상세 분석
- [ ] Kishōtenketsu (기승전결) 현대적 적용 연구
- [ ] 짧은 영상(1-3분)용 압축 구조 연구
- [ ] 거장별 서사 구조 해석 (봉준호, 놀란 등)

### 6.2 장르 공식 조사

- [ ] 드라마 장르 필수 요소 정리
- [ ] 액션 장르 페이싱 규칙 정리
- [ ] 코미디 장르 타이밍 연구
- [ ] 호러/스릴러 긴장 구축 기법
- [ ] 장르 혼합 성공 사례 분석

### 6.3 감정 곡선 조사

- [ ] Kurt Vonnegut 6가지 스토리 형태 상세화
- [ ] 영화 감정 분석 연구 논문 수집
- [ ] 1분/3분/10분 영상별 페이싱 차이 분석
- [ ] 뮤직비디오 감정 곡선 패턴 분석

### 6.4 AI 도구 휴리스틱 조사

- [ ] Veo 3.1/4 최적 사용 시나리오 정리
- [ ] Kling 2.6 강점 샷 유형 분석
- [ ] Sora 2 Pro Max 동작 시퀀스 성능 테스트
- [ ] 도구 간 전환 시 연속성 유지 기법

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 서사 구조 자료 수집 | 2일 | 구조 템플릿 20+ |
| 2 | 장르 공식 정리 | 2일 | 장르 DB 15+ |
| 3 | 감정 곡선 패턴화 | 1일 | 패턴 DB 10+ |
| 4 | Qdrant 컬렉션 구축 | 1일 | 벡터 적재 |
| 5 | 파이프라인 고도화 | 3일 | 코드 업데이트 |
| 6 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 학술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| Save the Cat! | 저서 | Blake Snyder의 15비트 시트 |
| Story Circle | 강의 | Dan Harmon의 8포인트 구조 |
| Story (Robert McKee) | 저서 | 시나리오 작법의 바이블 |
| Vonnegut on Story | 강의 | 6가지 스토리 형태 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| StudioBinder | https://www.studiobinder.com/ | 비트 시트 템플릿 |
| TV Tropes | https://tvtropes.org/ | 장르 공식/트로프 |
| NoFilmSchool | https://nofilmschool.com/ | 시나리오 작법 가이드 |

---

## 9. Part 9/10 기술 연계 (2026 보강)

### 9.1 Dynamic DAG Planner 연동 (Part 10.4)

시나리오 생성기가 **동적 워크플로우 계획**의 핵심 입력 역할을 합니다.

```yaml
dag_integration:
  role: "워크플로우의 첫 번째 컨텐츠 노드"

  output_types:
    beat_sheet:
      data_type: "BEAT_SHEET"
      next_nodes: ["sound_crafter", "storyboard_sketcher"]
      description: "15-beat 또는 8-point 서사 구조"

    scene_descriptions:
      data_type: "SCENE_LIST"
      next_nodes: ["storyboard_sketcher"]
      description: "씬별 상세 설명"

    shot_list:
      data_type: "SHOT_LIST"
      next_nodes: ["prompt_alchemy"]
      description: "샷 레벨 분해"

  conditional_routing:
    based_on_content_type:
      music_video:
        skip: ["detailed_dialogue"]
        prioritize: ["visual_beats", "rhythm_sync"]
        dag_path: "scenario → storyboard → prompt → visual → video"

      short_drama:
        include: ["dialogue_scenes", "character_arcs"]
        dag_path: "scenario → sound (dialogue) → storyboard → prompt → visual → video"

      shortform:
        compress: true
        max_beats: 5
        dag_path: "scenario → prompt → video (single shot)"
```

### 9.2 HITL (Human-in-the-Loop) 체크포인트

시나리오 단계에서 사용자 피드백을 수집합니다.

```yaml
hitl_checkpoints:
  scenario_approval:
    trigger: "beat_sheet 생성 완료"
    checkpoint_type: "APPROVAL"
    user_actions:
      - "approve: 다음 단계로 진행"
      - "modify: 특정 비트 수정 요청"
      - "regenerate: 전체 재생성"

    display_format:
      - "비주얼 비트 시트 (타임라인 형태)"
      - "감정 곡선 그래프"
      - "예상 도구 선택 미리보기"

  shot_list_review:
    trigger: "shot_list 생성 완료"
    checkpoint_type: "REVIEW"
    user_actions:
      - "approve_all"
      - "modify_specific_shots"
      - "add_shots"
      - "remove_shots"

    ai_suggestions:
      - "도구 선택 추천 (Veo/Kling/Sora)"
      - "예상 비용 계산"
      - "품질 예측 점수"

  implementation:
    executor: "HITLWorkflowExecutorV2"
    state_management: "WorkflowState (LangGraph 패턴)"
```

### 9.3 Intent-Aware 서사 생성

IntentFactory와 연동하여 의도에 맞는 서사 구조를 선택합니다.

```yaml
intent_integration:
  intent_to_structure_mapping:
    teaching_reference_analyze:
      preferred_structure: "analysis_framework"
      output_focus: "분석적 해설 흐름"

    teaching_story_write:
      preferred_structure: "save_the_cat"
      output_focus: "15 비트 서사 구조"

    veo_generate:
      preferred_structure: "visual_journey"
      output_focus: "비주얼 중심 비트"

    music_video:
      preferred_structure: "rhythm_based"
      output_focus: "BPM 동기화 비트"

  rag_query_adaptation:
    based_on_intent:
      - "거장 서사 구조 패턴 검색"
      - "장르별 페이싱 가이드 검색"
      - "성공 사례 구조 분석 검색"
```

### 9.4 수정된 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Scenario Generator V2 + Dynamic DAG                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Input: Topic, Persona, Reference Analysis, Intent                          │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                  Structure Selector                         │            │
│  │   - Intent 기반 서사 구조 선택                               │            │
│  │   - 페르소나 기반 페이싱 조정                                │            │
│  │   - 콘텐츠 타입별 압축/확장                                  │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                  Beat Sheet Generator                       │            │
│  │   - RAG: 장르 공식, 거장 구조 패턴                          │            │
│  │   - 감정 곡선 적용                                          │            │
│  │   - 도구 힌트 삽입 (Veo/Kling/Sora)                         │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │              HITL Checkpoint: Beat Sheet Approval           │            │
│  │   ┌─────────┬─────────┬─────────┐                          │            │
│  │   │ Approve │ Modify  │Regenerate│                          │            │
│  │   └─────────┴─────────┴─────────┘                          │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ├──────────────────┬──────────────────┐                                 │
│     ▼                  ▼                  ▼                                 │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│ │ BEAT_SHEET  │  │ SCENE_LIST  │  │ SHOT_LIST   │                          │
│ │     ↓       │  │     ↓       │  │     ↓       │                          │
│ │Sound Crafter│  │ Storyboard  │  │Prompt Alchemy│                         │
│ └─────────────┘  └─────────────┘  └─────────────┘                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                  Dynamic DAG Planner                        │            │
│  │   - 출력 타입 기반 다음 노드 자동 결정                       │            │
│  │   - 조건부 라우팅 (콘텐츠 타입별)                            │            │
│  │   - 병렬 실행 가능 노드 식별                                 │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 서사 구조 수집 시작 |
| 2026-01-17 | Part 9/10 기술 연계 (Dynamic DAG, HITL, Intent) | 완료 | DAG 노드 타입 정의 |
| 2026-01-17 | 웹 리서치 완료 (AI 스토리텔링, 서사 구조) | 완료 | 시나리오 생성 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### AI 스토리텔링 및 시나리오 생성 종합 분석

#### 1. AI 스크린라이팅 도구 현황 (2025)

```yaml
ai_screenwriting_tools:
  sudowrite:
    features:
      - "Story Bible: 캐릭터/세계관 일관성 관리"
      - "Beat Sheet: 구조화된 플롯 포인트"
      - "Describe: 장면 묘사 확장"
      - "Brainstorm: 아이디어 생성"
    pricing: "$10-29/month"
    strengths: "소설/시나리오 장편 작업에 최적"

  melies:
    focus: "시나리오 전문 AI"
    features:
      - "장르별 템플릿"
      - "대화 생성"
      - "씬 분해"
    target: "인디 영화 제작자"

  prescene:
    focus: "시각화 + 스크립트 통합"
    features:
      - "스크립트 → 스토리보드 자동 변환"
      - "씬별 비주얼 프리뷰"
```

#### 2. 서사 구조 패턴 (구현 권장)

```yaml
narrative_structures:
  three_act_structure:
    act1_setup: "25%"
    act2_confrontation: "50%"
    act3_resolution: "25%"
    beat_points:
      - "inciting_incident: 12%"
      - "first_turning_point: 25%"
      - "midpoint: 50%"
      - "second_turning_point: 75%"
      - "climax: 90%"

  heros_journey:
    stages_12:
      - "ordinary_world"
      - "call_to_adventure"
      - "refusal_of_call"
      - "meeting_mentor"
      - "crossing_threshold"
      - "tests_allies_enemies"
      - "approach_innermost_cave"
      - "ordeal"
      - "reward"
      - "road_back"
      - "resurrection"
      - "return_with_elixir"

  save_the_cat:
    beats_15:
      - "opening_image"
      - "theme_stated"
      - "setup"
      - "catalyst"
      - "debate"
      - "break_into_two"
      - "b_story"
      - "fun_and_games"
      - "midpoint"
      - "bad_guys_close_in"
      - "all_is_lost"
      - "dark_night_soul"
      - "break_into_three"
      - "finale"
      - "final_image"
```

#### 3. AI 스토리 생성 최적 패턴

```yaml
ai_story_generation_patterns:
  hierarchical_generation:
    level1_premise: "핵심 전제 (1-2문장)"
    level2_outline: "주요 플롯 포인트 (5-7개)"
    level3_beats: "씬별 비트 (15-30개)"
    level4_scenes: "상세 씬 스크립트"

  character_consistency:
    methods:
      - "Character Bible: 상세 프로필 사전 정의"
      - "Voice Examples: 대화 스타일 샘플"
      - "Motivation Tracking: 목표/동기 추적"

  world_building:
    methods:
      - "Setting Rules: 세계관 규칙 명시"
      - "History Snippets: 배경 역사"
      - "Constraint Enforcement: LLM에 규칙 주입"
```

#### 4. Crebit Scenario Generator 구현 권장

```yaml
crebit_scenario_implementation:
  structure_templates:
    available_structures:
      - "three_act"
      - "heros_journey"
      - "save_the_cat"
      - "nonlinear_parallel"
      - "custom_beats"

    output_format:
      scene_list:
        - scene_number: 1
          location: "INT. APARTMENT - NIGHT"
          characters: ["주인공", "조연"]
          action: "대화를 통해 갈등 표출"
          beat_type: "catalyst"
          emotional_arc: "tension → confrontation"
          estimated_duration: "2:30"

  dag_integration:
    nodes:
      premise_node: "전제 정의"
      outline_node: "구조 선택 + 아웃라인"
      beat_expansion_node: "비트별 상세화"
      scene_writing_node: "씬 스크립트 작성"

    hitl_checkpoints:
      - after: "outline_node"
        action: "사용자 플롯 승인"
      - after: "beat_expansion_node"
        action: "비트 수정 기회"

  auteur_style_injection:
    method: "거장 DNA에서 서사 패턴 추출"
    examples:
      bong: "사회 비판 + 장르 혼합"
      nolan: "비선형 시간 + 듀얼리티"
      tarantino: "대화 중심 + 비순차적"
```

### Sources
- Sudowrite Documentation (2025)
- Save the Cat! Beat Sheet Structure
- Hero's Journey 12 Stages (Joseph Campbell)
- AI Screenwriting Tools Comparison (2025)
