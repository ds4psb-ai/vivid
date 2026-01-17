# App 3.2: 비디오 메이커 (Video Maker) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: VEO (Video Generation)

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/veo.py"

# 현재 엔드포인트
endpoints = [
    "POST /dimension/veo/generate",
    "POST /dimension/veo/generate/stream",
    "POST /dimension/veo/status/{operation_id}",
    "GET /dimension/veo/output/{video_id}",
]

# 현재 기능
current_features = [
    "Google Veo 2 비디오 생성",
    "비동기 작업 상태 확인",
    "생성된 비디오 다운로드",
    "기본 스타일 프롬프트",
]

# 목표 기능 (고도화)
target_features = [
    "Veo 3.1/4 + Kling 2.6 + Sora 2 통합",
    "샷별 최적 도구 자동 선택",
    "Image-to-Video (I2V) 생성",
    "씬 연결 및 편집",
    "오디오 동기화",
    "배치 생성 및 큐 관리",
]
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| Veo 2만 지원 | 도구 선택지 제한 | 멀티 플랫폼 통합 |
| I2V 미지원 | 키프레임 활용 불가 | Kling/Runway I2V 통합 |
| 샷 연결 없음 | 수동 편집 필요 | 자동 씬 연결 기능 |
| 오디오 동기화 없음 | 음악 수동 편집 | Veo 네이티브 오디오 활용 |

---

## 2. 핵심 연구 주제

### 2.1 멀티 플랫폼 AI 비디오 생성 연구

**연구 질문**:
- 각 플랫폼(Veo, Kling, Sora)의 최적 사용 시나리오는?
- 플랫폼 간 전환 시 일관성 유지 방법은?
- 비용/품질 트레이드오프 최적화는?

**조사 대상**:
1. 2026 AI 비디오 플랫폼 비교 벤치마크
2. 플랫폼별 API 특성 및 제한사항
3. 하이브리드 사용 전략

### 2.2 Image-to-Video (I2V) 최적화 연구

**연구 질문**:
- I2V와 T2V의 품질/일관성 비교는?
- 최적의 입력 이미지 조건은?
- 모션 제어 정밀도 향상 방법은?

**조사 대상**:
1. Kling 2.6 I2V 고급 기능
2. Runway Gen-3 Image-to-Video
3. Veo Scene Extension (Images→Video)

### 2.3 씬 연결 및 편집 연구

**연구 질문**:
- AI 생성 비디오 간 자연스러운 전환 방법은?
- 자동 편집 포인트 감지 기법은?
- 오디오 동기화 자동화 방법은?

**조사 대상**:
1. 영상 편집 자동화 기법
2. 씬 전환 효과 라이브러리
3. 오디오-비디오 동기화 알고리즘

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: ai_video_platform_specs_2026

```yaml
id: ai_video_platform_specs_2026
description: "2026 AI 비디오 플랫폼 상세 스펙"
source: "공식 문서, 벤치마크"
size: ~20 documents

schema:
  platform_id:
    type: string
    enum: ["veo_3_1", "veo_4", "kling_2_6", "sora_2_pro", "runway_gen3"]

  platform_name:
    type: string

  version:
    type: string

  capabilities:
    type: object
    schema:
      text_to_video: bool
      image_to_video: bool
      video_extension: bool
      audio_generation: bool
      max_duration: int  # 초
      max_resolution: string
      frame_rate: int

  quality_metrics:
    type: object
    schema:
      fid_score: float  # 낮을수록 좋음
      clip_similarity: float  # 높을수록 좋음
      motion_smoothness: float
      temporal_consistency: float
      facial_fidelity: float

  api_details:
    type: object
    schema:
      endpoint: string
      auth_method: string
      rate_limit: int  # 분당 요청
      async_mode: bool
      webhook_support: bool

  pricing:
    type: object
    schema:
      per_second_usd: float
      per_request_usd: float
      free_tier: bool

  best_for:
    type: list[string]
    description: "최적 사용 시나리오"

  limitations:
    type: list[string]

# 예시 데이터 (2026 스펙)
platform_specs:
  - platform_id: "veo_3_1"
    platform_name: "Google Veo 3.1"
    version: "3.1"
    capabilities:
      text_to_video: true
      image_to_video: true  # Scene Extension
      video_extension: true
      audio_generation: true  # 네이티브 오디오
      max_duration: 120  # 2분
      max_resolution: "4K"
      frame_rate: 24
    quality_metrics:
      fid_score: 15.2
      clip_similarity: 0.88
      motion_smoothness: 0.92
      temporal_consistency: 0.90
      facial_fidelity: 0.78
    best_for:
      - "cinematic_narrative"
      - "atmospheric_establishing"
      - "audio_synchronized"
      - "long_takes"
    limitations:
      - "얼굴 클로즈업 일관성 약함"
      - "복잡한 손 동작 어려움"
    pricing:
      per_second_usd: 0.12
      per_request_usd: 0.0

  - platform_id: "kling_2_6"
    platform_name: "Kling 2.6"
    version: "2.6"
    capabilities:
      text_to_video: true
      image_to_video: true  # Start/End Frame
      video_extension: true
      audio_generation: false
      max_duration: 60
      max_resolution: "1080p"
      frame_rate: 30
    quality_metrics:
      fid_score: 12.8
      clip_similarity: 0.85
      motion_smoothness: 0.88
      temporal_consistency: 0.85
      facial_fidelity: 0.92  # 최고
    best_for:
      - "facial_closeup"
      - "portrait_shot"
      - "slow_motion"
      - "high_detail_texture"
    limitations:
      - "빠른 동작에서 일관성 저하"
      - "복잡한 배경에서 아티팩트"
    pricing:
      per_second_usd: 0.10

  - platform_id: "sora_2_pro"
    platform_name: "OpenAI Sora 2 Pro Max"
    version: "2.0"
    capabilities:
      text_to_video: true
      image_to_video: true
      video_extension: true
      audio_generation: false
      max_duration: 25  # 스토리보드 모드 25초
      max_resolution: "4K"
      frame_rate: 60
    quality_metrics:
      fid_score: 12.3
      clip_similarity: 0.90
      motion_smoothness: 0.95  # 최고
      temporal_consistency: 0.93
      facial_fidelity: 0.75
    best_for:
      - "action_sequence"
      - "complex_motion"
      - "physics_simulation"
      - "rapid_transitions"
    pricing:
      per_second_usd: 0.15
```

### 3.2 데이터셋: shot_to_platform_mapping

```yaml
id: shot_to_platform_mapping
description: "샷 유형에서 플랫폼 자동 선택 규칙"
source: "품질 테스트, 경험 데이터"
size: ~100 documents

schema:
  shot_scenario:
    type: string
    example: "emotional_closeup"

  characteristics:
    type: object
    schema:
      motion_level: string
      detail_requirement: string
      duration_category: string
      audio_required: bool
      style_complexity: string

  platform_ranking:
    type: list[object]
    schema:
      platform: string
      score: float
      reasoning: string
      expected_quality: float
      cost_estimate: float

  decision_rule:
    type: string
    description: "자동 선택 규칙 (의사결정 트리)"

  fallback_strategy:
    type: object
    schema:
      if_primary_fails: string
      quality_threshold: float

# 예시 매핑
shot_platform_mappings:
  - shot_scenario: "emotional_closeup"
    characteristics:
      motion_level: "low"
      detail_requirement: "high"
      duration_category: "short"
      audio_required: false
      style_complexity: "medium"
    platform_ranking:
      - platform: "kling"
        score: 0.95
        reasoning: "안면 보존력 최고, 세밀한 표정 표현"
        expected_quality: 0.92
        cost_estimate: 0.30
      - platform: "veo"
        score: 0.70
        reasoning: "좋은 품질이나 얼굴 일관성 약함"
        expected_quality: 0.78
        cost_estimate: 0.36
    decision_rule: "IF motion_level == 'low' AND detail_requirement == 'high' THEN kling"
    fallback_strategy:
      if_primary_fails: "veo"
      quality_threshold: 0.75

  - shot_scenario: "chase_action_sequence"
    characteristics:
      motion_level: "extreme"
      detail_requirement: "medium"
      duration_category: "medium"
      audio_required: true
      style_complexity: "high"
    platform_ranking:
      - platform: "sora"
        score: 0.92
        reasoning: "고속 동작 연속성 최고, 물리 시뮬레이션"
        expected_quality: 0.90
        cost_estimate: 0.75
      - platform: "veo"
        score: 0.80
        reasoning: "오디오 동기화 가능, 액션 양호"
        expected_quality: 0.82
        cost_estimate: 0.60
    decision_rule: "IF motion_level == 'extreme' THEN sora"
```

### 3.3 데이터셋: i2v_optimization_guide

```yaml
id: i2v_optimization_guide
description: "Image-to-Video 최적화 가이드"
source: "플랫폼 가이드, 실험 데이터"
size: ~40 documents

schema:
  platform:
    type: string

  i2v_mode:
    type: string
    enum: ["start_frame_only", "start_end_frames", "reference_guided"]

  input_requirements:
    type: object
    schema:
      resolution: string
      aspect_ratio: list[string]
      file_format: list[string]
      max_file_size: string

  optimization_tips:
    type: list[object]
    schema:
      tip: string
      impact: string
      priority: float

  motion_control:
    type: object
    schema:
      motion_prompt_support: bool
      motion_strength_control: bool
      camera_control: bool
      speed_control: bool

  quality_comparison:
    type: object
    schema:
      vs_t2v_quality: float  # I2V vs T2V 품질 비율
      consistency_improvement: float
      motion_accuracy: float

# 예시 가이드
i2v_guides:
  - platform: "kling_2_6"
    i2v_mode: "start_end_frames"
    input_requirements:
      resolution: "1280x720 권장"
      aspect_ratio: ["16:9", "9:16", "1:1"]
      file_format: ["png", "jpg"]
      max_file_size: "10MB"
    optimization_tips:
      - tip: "Start/End Frame 간 차이를 30-60% 범위로 유지"
        impact: "자연스러운 모션 생성"
        priority: 0.95
      - tip: "두 프레임 간 캐릭터 포즈 방향성 일관"
        impact: "동작 흐름 자연스러움"
        priority: 0.90
      - tip: "배경 요소 일치시키기"
        impact: "시각적 일관성"
        priority: 0.85
    motion_control:
      motion_prompt_support: true
      motion_strength_control: true
      camera_control: true
      speed_control: true
    quality_comparison:
      vs_t2v_quality: 1.3  # I2V가 30% 더 높은 품질
      consistency_improvement: 0.4  # 일관성 40% 향상
      motion_accuracy: 0.85

  - platform: "veo_3_1"
    i2v_mode: "reference_guided"
    input_requirements:
      resolution: "1920x1080 권장"
      aspect_ratio: ["16:9", "4:3"]
      file_format: ["png", "jpg", "webp"]
      max_file_size: "20MB"
    optimization_tips:
      - tip: "최대 3개의 참조 이미지 사용 (Ingredients to Video)"
        impact: "스타일 및 요소 전달력 향상"
        priority: 0.90
```

### 3.4 데이터셋: scene_transition_library

```yaml
id: scene_transition_library
description: "씬 전환 효과 라이브러리"
source: "영상 편집 이론, 거장 분석"
size: ~50 documents

schema:
  transition_id:
    type: string
    example: "match_cut"

  transition_name:
    type: string
    example: "매치 컷"

  category:
    type: string
    enum: ["cut", "dissolve", "wipe", "creative", "temporal"]

  description:
    type: string

  emotional_effect:
    type: list[string]

  technical_requirements:
    type: object
    schema:
      frame_overlap: int  # 필요한 오버랩 프레임
      processing_complexity: string
      audio_handling: string

  implementation:
    type: object
    schema:
      ffmpeg_command: string
      ai_generation_hint: string
      duration_range: string

  best_for:
    type: list[string]

  auteur_examples:
    type: list[object]
    schema:
      auteur_key: string
      film: string
      scene_description: string

# 예시 전환
transitions:
  - transition_id: "match_cut"
    transition_name: "매치 컷"
    category: "creative"
    description: "유사한 형태/동작을 통해 두 장면을 연결"
    emotional_effect: ["continuity", "connection", "metaphor"]
    technical_requirements:
      frame_overlap: 0
      processing_complexity: "medium"
      audio_handling: "cross_fade"
    implementation:
      ffmpeg_command: "-filter_complex [0:v][1:v]concat=n=2:v=1[outv]"
      ai_generation_hint: "두 씬의 마지막/첫 프레임에 유사한 형태 배치"
      duration_range: "0.5-1.5s"
    best_for: ["time_passage", "thematic_connection", "artistic_statement"]
    auteur_examples:
      - auteur_key: "kubrick"
        film: "2001: A Space Odyssey"
        scene_description: "뼈 → 우주선 매치 컷"

  - transition_id: "j_cut"
    transition_name: "J-컷"
    category: "temporal"
    description: "오디오가 영상보다 먼저 전환"
    emotional_effect: ["anticipation", "smooth_flow", "immersion"]
    technical_requirements:
      frame_overlap: 24  # 약 1초
      processing_complexity: "low"
      audio_handling: "audio_leads_video"
    implementation:
      ffmpeg_command: "별도 오디오 트랙 조작 필요"
      ai_generation_hint: "다음 씬의 오디오를 현재 씬 끝에 미리 재생"
    best_for: ["dialogue_scene", "natural_flow", "documentary"]
```

---

## 4. 기능 고도화 설계

### 4.1 멀티 플랫폼 비디오 생성 파이프라인

```yaml
video_maker_pipeline:
  stage_1_shot_analysis:
    purpose: "각 샷의 특성 분석 및 플랫폼 선택"
    inputs:
      - shot_list (from 시나리오)
      - keyframe_pairs (from 비주얼 리얼라이저)
      - prompt_set (from 프롬프트 연금술)
    outputs:
      - platform_assignments: dict[shot_id, platform]
      - generation_queue: list[GenerationJob]
    rag_queries:
      - "shot_to_platform_mapping → 샷 특성 기반"
      - "ai_video_platform_specs_2026 → 플랫폼 스펙"
    logic:
      - "각 샷 특성 분석 (모션, 디테일 등)"
      - "최적 플랫폼 선택"
      - "비용 최적화 고려"

  stage_2_parallel_generation:
    purpose: "병렬 비디오 생성"
    inputs:
      - generation_queue
      - platform_credentials
    outputs:
      - raw_videos: list[VideoSegment]
      - generation_reports: list[Report]
    logic:
      - "플랫폼별 비동기 생성 요청"
      - "상태 폴링 및 완료 대기"
      - "실패 시 폴백 플랫폼 시도"

  stage_3_quality_check:
    purpose: "생성 영상 품질 검증"
    inputs:
      - raw_videos
      - expected_quality_thresholds
    outputs:
      - quality_scores: dict[video_id, score]
      - regenration_needed: list[shot_id]
    logic:
      - "자동 품질 평가"
      - "기준 미달 샷 재생성 대기열 추가"

  stage_4_scene_connection:
    purpose: "씬 연결 및 전환 효과"
    inputs:
      - verified_videos
      - transition_plan (from 시나리오)
    outputs:
      - connected_video
    rag_queries:
      - "scene_transition_library → 전환 타입 기반"
    logic:
      - "전환 효과 적용"
      - "타이밍 조정"
      - "FFmpeg 기반 편집"

  stage_5_audio_sync:
    purpose: "오디오 동기화"
    inputs:
      - connected_video
      - music_design (from 사운드 크래프터)
      - sync_guide
    outputs:
      - final_video
    logic:
      - "음악 트랙 오버레이"
      - "씬 전환점 오디오 동기화"
      - "볼륨 자동 조정"
```

### 4.2 출력 스키마 설계

```python
class VideoMakerOutput(BaseModel):
    """비디오 메이커 출력 스키마"""

    # 메타데이터
    metadata: VideoMetadata
    class VideoMetadata(BaseModel):
        project_id: str
        total_duration: float
        total_shots: int
        platforms_used: list[str]
        total_cost: float
        generation_time: float

    # 생성된 비디오 세그먼트
    segments: list[VideoSegment]
    class VideoSegment(BaseModel):
        segment_id: str
        shot_number: int
        platform_used: str
        duration: float
        resolution: str
        frame_rate: int
        video_url: str
        thumbnail_url: str
        generation_prompt: str
        quality_score: float

    # 플랫폼별 통계
    platform_stats: PlatformStats
    class PlatformStats(BaseModel):
        veo_count: int
        veo_duration: float
        kling_count: int
        kling_duration: float
        sora_count: int
        sora_duration: float
        cost_breakdown: dict[str, float]

    # 품질 보고
    quality_report: QualityReport
    class QualityReport(BaseModel):
        overall_score: float
        segment_scores: dict[str, float]
        regenerated_segments: list[str]
        issues_found: list[str]

    # 최종 출력
    final_output: FinalOutput
    class FinalOutput(BaseModel):
        video_url: str
        video_with_audio_url: str | None
        preview_url: str
        download_formats: list[str]

    # 편집 정보
    edit_info: EditInfo
    class EditInfo(BaseModel):
        transitions_applied: list[TransitionInfo]
        audio_sync_points: list[SyncPoint]
        timeline_json: str  # 편집 프로그램 호환 타임라인

        class TransitionInfo(BaseModel):
            from_segment: str
            to_segment: str
            transition_type: str
            duration: float

        class SyncPoint(BaseModel):
            time_position: float
            audio_event: str
            video_event: str

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     shot_list + prompts     ┌─────────────────┐
│ 2.3 프롬프트    │ ─────────────────────────────► │ 3.2 비디오      │
│     연금술      │                               │     메이커      │
└─────────────────┘                               └────────┬────────┘
                                                           │
┌─────────────────┐     keyframe_pairs                     │
│ 3.1 비주얼      │ ───────────────────────────────────────│
│     리얼라이저   │                                        │
└─────────────────┘                                        │
                                                           │
┌─────────────────┐     music_design + sync_guide          │
│ 2.1 사운드      │ ───────────────────────────────────────│
│     크래프터     │                                        │
└─────────────────┘                                        │
                                                           │ final_video
                                                           ▼
                                                 ┌─────────────────┐
                                                 │ 4.1 퀄리티      │
                                                 │     디렉터      │
                                                 └─────────────────┘
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| shot_prompts | 프롬프트 연금술 | 플랫폼 배정 | generation_jobs | API 호출 |
| keyframe_pairs | 비주얼 리얼라이저 | I2V 입력 | i2v_requests | API 호출 |
| music_design | 사운드 크래프터 | 오디오 레이어 | audio_track | 최종 합성 |
| final_video | - | - | review_input | 퀄리티 디렉터 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 플랫폼 통합 조사

- [ ] Veo 3.1/4 API 완전 통합
- [ ] Kling 2.6 API 통합
- [ ] Sora 2 Pro API 통합 (출시 시)
- [ ] 플랫폼별 인증/과금 관리

### 6.2 I2V 최적화 조사

- [ ] Kling Start/End Frame 최적 설정
- [ ] Veo Scene Extension 활용법
- [ ] 키프레임 → I2V 워크플로우

### 6.3 편집 자동화 조사

- [ ] FFmpeg 기반 비디오 연결
- [ ] 씬 전환 효과 구현
- [ ] 오디오-비디오 동기화 알고리즘
- [ ] 타임라인 JSON 포맷 설계

### 6.4 품질/비용 최적화

- [ ] 샷 특성별 플랫폼 품질 비교
- [ ] 비용 최적화 알고리즘
- [ ] 배치 생성 효율화
- [ ] 실패 복구 전략

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 플랫폼 API 통합 | 3일 | API 클라이언트 |
| 2 | 샷-플랫폼 매핑 | 2일 | 선택 알고리즘 |
| 3 | I2V 워크플로우 | 2일 | I2V 파이프라인 |
| 4 | 씬 연결 시스템 | 2일 | 편집 기능 |
| 5 | 오디오 동기화 | 2일 | 동기화 기능 |
| 6 | 테스트 및 튜닝 | 3일 | 품질 검증 |

---

## 8. 참고 자료

### 기술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| Veo API Docs | 공식문서 | Google Veo 통합 |
| Kling API Guide | 가이드 | Kling 통합 |
| FFmpeg Documentation | 문서 | 비디오 편집 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| Google Veo | AI Studio | T2V/I2V |
| Kling AI | https://kling.ai/ | I2V 최적화 |
| FFmpeg | https://ffmpeg.org/ | 비디오 처리 |

---

## 9. Native Audio 통합 전략 (P0 보강)

> **Updated**: 2026-01-17 (컨설팅 피드백 반영)
> **Reference**: DIMENSION_APP_MACRO_PLANNING_2026.md Part 9.1

### 9.1 Native Audio 시대의 Video Maker 역할 변화

```yaml
video_maker_role_evolution:
  before:
    description: "영상 생성만 담당, 오디오는 별도 처리"
    workflow:
      - "T2V/I2V로 무음 영상 생성"
      - "사운드 크래프터에서 오디오 별도 생성"
      - "후반 작업에서 믹싱"

  after:
    description: "영상+오디오 통합 생성 조율"
    workflow:
      - "사운드 크래프터의 audio_strategy 수신"
      - "Native Audio 플랫폼 선택 시 오디오 프롬프트 통합"
      - "Separate 전략 시 무음 생성 후 믹싱 연동"
```

### 9.2 플랫폼별 Native Audio 지원 현황 (업데이트)

```yaml
platform_audio_capabilities:
  veo_3_1:
    native_audio: true
    release_date: "2025.10"
    audio_types:
      - "대화 (자동 립싱크)"
      - "효과음 (시각 이벤트 동기화)"
      - "앰비언트 (환경 매칭)"
      - "BGM (분위기 기반)"
    api_audio_params:
      audio_prompt: "string (영상 프롬프트에 통합)"
      audio_style: "cinematic | realistic | stylized"
    pricing: "$0.15-0.40/sec"

  kling_2_6:
    native_audio: true
    release_date: "2025.12"
    audio_types:
      - "대화 (감정 제어)"
      - "노래/랩 (음악 동기화)"
      - "효과음 (Foley 품질)"
      - "앰비언트"
    api_audio_params:
      voice_style: "whisper | normal | dramatic | singing"
      audio_coordination: true  # 리듬-시각 동기화
    pricing: "$0.07-0.14/sec"

  sora_2_pro:
    native_audio: true
    release_date: "2025.05"
    audio_types:
      - "대화"
      - "효과음"
    limitations: "음악 생성 미지원"
    pricing: "$0.15/sec"

  runway_gen4:
    native_audio: false
    workflow: "별도 오디오 생성 필요"
```

### 9.3 비디오 메이커 V2 파이프라인 (Native Audio 통합)

```yaml
video_maker_pipeline_v2:
  stage_1_shot_analysis:
    purpose: "샷 분석 + 오디오 전략 수신"
    inputs:
      - shot_list
      - keyframe_pairs
      - prompt_set
      - audio_strategy  # 사운드 크래프터에서 수신
    outputs:
      - platform_assignments (오디오 고려)
      - generation_queue
    logic:
      - "audio_strategy.primary_method 확인"
      - "Native Audio 필요 시 Veo/Kling 우선 배정"
      - "플랫폼별 오디오 지원 여부 확인"

  stage_2_prompt_integration:
    purpose: "영상+오디오 프롬프트 통합"
    inputs:
      - generation_queue
      - audio_strategy
    outputs:
      - integrated_prompts
    logic:
      - "Native 전략 시: 오디오 프롬프트를 영상 프롬프트에 통합"
      - "Separate 전략 시: 영상 프롬프트만 사용"
    example:
      video_prompt: "A woman walks through a rainy street at night"
      audio_prompt: "raindrops on umbrella, distant traffic, footsteps on wet pavement"
      integrated: "A woman walks through a rainy street at night, with the sound of raindrops on umbrella, distant traffic, footsteps on wet pavement"

  stage_3_parallel_generation:
    # 기존과 동일 (오디오 포함 영상 생성)

  stage_4_audio_handling:
    purpose: "오디오 후처리 (필요 시)"
    inputs:
      - generated_videos
      - audio_strategy
    outputs:
      - final_videos_with_audio
    logic:
      native_success:
        action: "검증 후 그대로 사용"
      native_quality_issue:
        action: "ElevenLabs/MM Audio로 보강"
      separate_bgm:
        action: "Suno BGM 레이어 믹싱"
```

### 9.4 샷-플랫폼 매핑 업데이트 (오디오 고려)

```yaml
shot_platform_mapping_v2:
  # 오디오 요구사항을 고려한 플랫폼 선택
  decision_factors:
    - motion_level
    - detail_requirement
    - audio_required  # 신규
    - audio_type  # 신규 (dialog, sfx, ambient, music)

  mappings:
    - scenario: "dialogue_closeup"
      audio_required: true
      audio_type: "dialog"
      platform_ranking:
        - platform: "kling_2_6"
          score: 0.95
          reasoning: "최고 얼굴 품질 + 자동 립싱크"
        - platform: "veo_3_1"
          score: 0.80
          reasoning: "좋은 대화 동기화"

    - scenario: "action_sequence_with_sfx"
      audio_required: true
      audio_type: "sfx"
      platform_ranking:
        - platform: "veo_3_1"
          score: 0.90
          reasoning: "효과음 타이밍 동기화 우수"
        - platform: "kling_2_6"
          score: 0.85
          reasoning: "Foley 품질 효과음"

    - scenario: "mv_dance"
      audio_required: true
      audio_type: "music"
      strategy: "hybrid"
      platform_ranking:
        - platform: "kling_2_6"
          score: 0.90
          reasoning: "Audio-Visual Coordination"
      bgm_source: "Suno (별도 생성)"

    - scenario: "ambient_establishing"
      audio_required: true
      audio_type: "ambient"
      platform_ranking:
        - platform: "veo_3_1"
          score: 0.95
          reasoning: "환경음 최적화"
```

### 9.5 업데이트된 출력 스키마 (오디오 정보 포함)

```python
class VideoMakerOutputV2(BaseModel):
    """Native Audio 통합 비디오 메이커 출력 스키마"""

    # 기존 필드 유지
    metadata: VideoMetadata
    segments: list[VideoSegment]
    platform_stats: PlatformStats
    quality_report: QualityReport
    final_output: FinalOutput

    # 신규: 오디오 통합 정보
    audio_integration: AudioIntegration
    class AudioIntegration(BaseModel):
        strategy_used: Literal["native", "separate", "hybrid"]

        native_audio_segments: list[NativeAudioSegment]
        class NativeAudioSegment(BaseModel):
            segment_id: str
            platform: str  # veo, kling
            audio_prompt_used: str
            audio_types_generated: list[str]  # dialog, sfx, ambient
            lip_sync_quality: float | None  # 대화 씬만
            audio_visual_sync_score: float

        separate_audio_layers: list[SeparateAudioLayer] | None
        class SeparateAudioLayer(BaseModel):
            layer_type: str  # bgm, voiceover
            source: str  # suno, elevenlabs
            start_time: float
            duration: float
            volume_level: float

        mixing_applied: MixingInfo
        class MixingInfo(BaseModel):
            layers_count: int
            ducking_applied: bool  # 대화 시 BGM 볼륨 감소
            sync_points: list[SyncPoint]

    # 편집 정보 확장
    edit_info: EditInfoV2
    class EditInfoV2(BaseModel):
        transitions_applied: list[TransitionInfo]
        audio_sync_points: list[SyncPoint]
        audio_tracks: list[AudioTrack]  # 신규

        class AudioTrack(BaseModel):
            track_name: str
            track_type: str  # native, bgm, sfx, voiceover
            source_platform: str
            volume_curve: list[float]

    evidence_refs: list[str]
```

### 9.6 사운드 크래프터-비디오 메이커 연동 흐름

```
┌─────────────────┐                    ┌─────────────────┐
│ 2.1 사운드      │   audio_strategy   │ 3.2 비디오      │
│     크래프터    │ ─────────────────► │     메이커      │
│                 │                    │                 │
│ - Tier 분석     │                    │ - 플랫폼 배정   │
│ - Native/Sep.   │                    │ - 프롬프트 통합 │
│ - 오디오 프롬프트 │                  │ - 생성 실행     │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │ audio_strategy                       │ generation_result
        ▼                                      ▼
┌──────────────────────────────────────────────────────┐
│ audio_strategy: {                                     │
│   primary_method: "native",                          │
│   native_config: {                                   │
│     platform: "kling",                               │
│     audio_prompt: "whispered dialogue, foley sfx",   │
│     sfx_cues: [...],                                 │
│   },                                                 │
│   separate_config: {                                 │
│     bgm_prompt: "subtle piano underscore",           │
│     generation_platform: "suno",                     │
│   }                                                  │
│ }                                                    │
└──────────────────────────────────────────────────────┘
```

---

## 10. Multi-Modal 레퍼런스 검색 지원 (P1 보강)

> **Reference**: DIMENSION_APP_MACRO_PLANNING_2026.md Part 9.3

### 10.1 비디오 레퍼런스 검색 통합

```yaml
multimodal_reference_integration:
  description: "영상/오디오 레퍼런스를 벡터 검색으로 제공"

  use_cases:
    - "유사 씬 영상 레퍼런스 검색"
    - "분위기 맞는 오디오 레퍼런스 검색"
    - "거장 스타일 영상 예시 제공"

  integration_points:
    stage_1_reference_retrieval:
      trigger: "샷 분석 시"
      query: "씬 설명 + 무드 + 거장 스타일"
      collections:
        - "dimension_video_embeddings (1408-D)"
        - "dimension_audio_embeddings (1024-D)"
      output: "참고 영상/오디오 URL 목록"

    stage_2_style_guidance:
      trigger: "프롬프트 생성 시"
      use: "검색된 레퍼런스 스타일 힌트 추출"
      output: "스타일 수정자 + 기법 설명"
```

### 10.2 Cross-Modal 검색 시나리오

```yaml
cross_modal_search:
  scenario_1:
    input: "긴장감 있는 추격씬 오디오"
    query_type: "audio_embedding"
    result: "유사 분위기 영상 클립 목록"
    application: "영상 스타일 참고"

  scenario_2:
    input: "봉준호 스타일 대화씬 영상"
    query_type: "video_embedding"
    result: "유사 구도/연출 영상 + 매칭 오디오"
    application: "연출 + 사운드 디자인 참고"
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 플랫폼 API 조사 |
| 2026-01-17 | Native Audio 통합 보강 (Part 9,10) | 완료 | 파이프라인 구현 |
| 2026-01-17 | 웹 리서치 완료 (AI Video API 2026) | 완료 | API 통합 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### 2026 AI Video Generation API 종합 분석

#### 1. 2026 플랫폼별 Elo 랭킹 (Artificial Analysis, Dec 2025)

| Rank | Model | Elo Score | Company | Native Audio |
|------|-------|-----------|---------|--------------|
| 1 | Runway Gen-4.5 | 1,247 | Runway | Yes |
| 2 | Google Veo 3 | 1,226 | Google DeepMind | Yes |
| 3 | Kling 2.5 Turbo Pro | 1,225 | Kuaishou | No |
| 4 | Google Veo 3.1 | 1,220 | Google DeepMind | Yes |
| 5 | Luma Ray 3 | 1,211 | Luma AI | Coming Soon |
| 6 | Hailuo 02 | 1,208 | MiniMax | No |
| 7 | OpenAI Sora 2 Pro | 1,206 | OpenAI | Yes |
| 8 | Seedance 1.0 Pro | 1,202 | ByteDance | No |
| 9 | Pika 2.2 | 1,195 | Pika Labs | Yes |
| 10 | PixVerse v4.5 | 1,190 | PixVerse | Yes |

#### 2. 플랫폼별 가격 및 사양

```yaml
platform_pricing_2026:
  runway_gen45:
    monthly: "$12 (Standard) - $76 (Unlimited)"
    per_credit: "~$0.01"
    max_length: "40 seconds"
    resolution: "4K supported"
    api_access: "Available, rolling out Dec 2025"

  veo_3_31:
    monthly: "$19.99-28.99 (Google AI Pro)"
    per_second: "$0.15-0.40"
    max_length: "8 seconds"
    resolution: "1080p (8 sec)"
    native_audio: "Synchronized dialogue, ambient, SFX"
    third_party: "fal.ai, Canva integration"

  kling_25_26:
    monthly: "$10/month"
    max_length: "2 minutes (best value!)"
    resolution: "1080p"
    strengths: "Motion physics, lip-sync (8+ languages)"
    api_access: "CometAPI, Kie.ai"

  sora_2_pro:
    monthly: "$20/month (ChatGPT Plus)"
    access: "Limited, via ReelMind (AIML API)"
    strengths: "Narrative storytelling, high realism"

  luma_ray3:
    monthly: "$9.99 (Lite) - $94.99 (Unlimited)"
    credits: "3,200 (Lite) - Unlimited (Power)"
    features: "HDR output, Reasoning model (world's first)"
    generation_speed: "< 30 seconds for 10-sec clip"

  pika_22:
    monthly: "$8-58/month"
    generation_time: "< 2 minutes (fastest)"
    max_length: "10 seconds"
    strengths: "Pikaffects, social media content"
```

#### 3. 용도별 최적 플랫폼 선택

```yaml
use_case_recommendations:
  premium_quality:
    platform: "Sora 2 Pro"
    cost: "~$4/video"
    when: "최고 품질 필요, 예산 여유"

  professional_work:
    platform: "Veo 3 or Runway Gen-4"
    when: "시네마틱 리얼리즘, 상업 콘텐츠"

  best_value:
    platform: "Kling AI 1.6/2.6"
    cost: "$0.35/video, $10/month"
    when: "장시간 영상, 예산 제한"

  developers:
    platform: "Luma Dream Machine"
    cost: "$0.20/video"
    when: "API 통합, 빠른 프로토타이핑"

  creative_features:
    platform: "Pika 2.1/2.2"
    when: "특수 효과, 소셜 미디어 콘텐츠"

  speed:
    platform: "Runway Gen-4 Turbo"
    when: "빠른 반복, 대량 생성"
```

#### 4. API 접근 경로

```yaml
api_access_routes:
  official_apis:
    runway: "runway.ml/api (pay-as-you-go)"
    luma: "lumalabs.ai/api"
    pika: "pika.art/api"

  third_party_aggregators:
    fal_ai:
      models: ["Veo 3", "Kling", "multiple others"]
      pricing: "Usage-based"
      features: "Fast/Pro variants, seed control"

    comet_api:
      models: ["Sora 2", "Kling", "Suno AI"]
      access: "Premium aggregator"

    aiml_api:
      runway_gen3_turbo: "$0.053/second"
      sora_turbo: "120 credits via ReelMind"

    canva_integration:
      models: ["Veo 3", "Dream Machine"]
      access: "Magic Studio feature"
```

#### 5. 2026 시장 동향

```yaml
market_trends_2026:
  market_size: "$946 million (2026), up from $788M (2025)"
  growth_rate: "20.3% CAGR through 2033"
  projected_2033: "$7 billion"

  regional_share:
    asia_pacific: "31%"

  technology_trends:
    native_audio: "Standard feature (Veo, Sora, Runway, Pika)"
    hdr_output: "Luma Ray 3 first"
    reasoning_models: "Understanding cause-effect"
    minute_plus_videos: "Multiple platforms supporting"

  hardware_trends:
    nvidia_rtx: "4K AI video on consumer hardware"
    inference_speed: "< 30 seconds for 10-sec clips"
```

#### 6. Crebit 공식 지원 모델 (3개)

```yaml
crebit_supported_models:
  # ============================================================
  # Crebit은 다음 3개 모델만 공식 지원
  # ============================================================

  veo_31:
    name: "Google Veo 3.1"
    primary_use: "대화/나레이션 중심 바이럴 영상"
    strengths:
      - "Native Audio: 대화 + 환경음 동시 생성"
      - "립싱크 정확도 높음"
      - "자연스러운 음성 합성"
    best_for:
      - "인터뷰/토크 장면"
      - "제품 설명 영상"
      - "교육 콘텐츠"
      - "바이럴 숏폼 (대화 중심)"
    api_access: "fal.ai"
    pricing: "$0.15-0.40/sec"
    max_duration: "8 sec"

  kling_26:
    name: "Kling 2.6"
    primary_use: "고화질 음성 없는 영상 (특히 추천)"
    strengths:
      - "2분 길이 지원 (최장)"
      - "뛰어난 모션 물리 시뮬레이션"
      - "고화질 시각 품질"
      - "가성비 최고"
    best_for:
      - "시네마틱 B-roll"
      - "풍경/환경 영상"
      - "음악 없는 무드 영상"
      - "액션/모션 중심 씬"
      - "후반 오디오 합성 예정 영상"
    api_access: "CometAPI, Kie.ai"
    pricing: "$0.07-0.14/sec"
    max_duration: "2 min"
    note: "음성 없는 고화질 영상에 특히 강력 추천"

  sora_max_2pro:
    name: "Sora Max 2 Pro"
    primary_use: "애니메이션 스타일 영상"
    strengths:
      - "스타일라이즈드 애니메이션"
      - "캐릭터 일관성"
      - "창의적 스토리텔링"
    best_for:
      - "애니메이션 스타일 콘텐츠"
      - "일러스트 기반 영상"
      - "만화/웹툰 스타일"
      - "캐릭터 중심 서사"
    api_access: "AIML API / ReelMind"
    pricing: "ChatGPT Plus $20/month"

# ============================================================
# 모델 선택 가이드
# ============================================================
model_selection_guide:
  dialogue_scene: "veo_31"           # 대화가 있으면 무조건 Veo
  silent_cinematic: "kling_26"       # 대화 없는 고화질 → Kling
  animation_style: "sora_max_2pro"   # 애니메이션 → Sora
  long_form: "kling_26"              # 30초+ 영상 → Kling (2분 지원)
  viral_short: "veo_31"              # 바이럴 숏폼 → Veo (오디오 포함)

# 자동 선택 로직 (Crebit 내부용)
auto_selection_logic:
  if: "scene.has_dialogue OR scene.requires_narration"
  then: "veo_31"
  elif: "scene.style == 'animation' OR scene.style == 'illustrated'"
  then: "sora_max_2pro"
  else: "kling_26"  # 기본값: 고화질 Kling
```

### Sources
- Artificial Analysis Video Arena Leaderboard (Dec 2025)
- AI Free Forever: 17 Best AI Video Generation Models
- MEXC News: AI Video Generators 2026 Tested
- MASV: Best AI Video Generator Comparison
- WaveSpeed AI: Best AI Video Generators 2026
