# App 2.1: 사운드 크래프터 (Sound Crafter) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: Sound

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/sound.py"

# 엔드포인트
endpoints = [
    "POST /dimension/sound/craft",
    "POST /dimension/sound/craft/stream",
    "POST /dimension/sound/brief",
    "POST /dimension/sound/brief/stream",
]

# 현재 기능
current_features = [
    "BGM 생성 가이드 (sound_craft)",
    "사운드 브리프 생성 (sound_brief)",
    "SSE 스트리밍 지원",
    "Suno/Udio 프롬프트 생성",
]

# 현재 입력 스키마
SoundCraftRequest = {
    "concept": "str",           # 비디오 컨셉
    "scenario": "str",          # 시나리오 (선택)
    "auteur_key": "str",        # 거장 키
    "duration": "int",          # 목표 길이 (초)
    "style": "str",             # 음악 스타일
    "tempo": "str",             # 템포 (slow/medium/fast)
    "model": "str",             # AI 모델
}
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| BPM-감정 과학적 근거 부족 | 감정 동기화 부정확 | 음악심리학 연구 기반 매핑 |
| 장르별 악기 조합 미흡 | 스타일 다양성 제한 | 악기-장르 DB 구축 |
| 씬별 음악 변화 미흡 | 일관된 BGM만 생성 | 비트 시트 연동 음악 설계 |
| 거장 음악 스타일 DB 부족 | 거장 특색 반영 약함 | 작곡가 DNA 데이터 구축 |

---

## 2. 핵심 연구 주제

### 2.1 음악 심리학 연구

**연구 질문**:
- BPM과 감정 반응의 상관관계는?
- 조성(Key)과 감정의 상관관계는?
- 악기별 감정 연상(Emotional Association)은?

**조사 대상**:
1. 음악 심리학 학술 논문 (2020-2026)
2. Spotify/Apple Music 플레이리스트 분석
3. 영화 음악 분석 연구

### 2.2 영화 작곡가 DNA 연구

**연구 질문**:
- 한스 짐머의 시그니처 사운드 요소는?
- 조 히사이시의 미니멀리즘 접근법은?
- 각 작곡가의 오케스트레이션 스타일은?

**조사 대상**:
1. 영화 작곡가 인터뷰/마스터클래스
2. 영화 사운드트랙 분석
3. 음악 이론 적용 사례

### 2.3 씬-음악 동기화 연구

**연구 질문**:
- 영화 씬 타입별 음악 패턴은?
- 음악 큐 포인트(Music Cue Point) 규칙은?
- 감정 전환 시 음악 처리 기법은?

**조사 대상**:
1. 영화 스코어링 기법
2. 미키마우싱 vs 언더스코어링
3. 현대 영화 음악 트렌드

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: bpm_emotion_mapping

```yaml
id: bpm_emotion_mapping
description: "BPM과 감정의 과학적 매핑 데이터"
source: "음악심리학 논문, EEG 연구 (2025)"
size: ~100 documents

schema:
  bpm_range:
    type: object
    schema:
      min: int
      max: int

  primary_emotion:
    type: string
    example: "tension"

  secondary_emotions:
    type: list[string]
    example: ["anxiety", "excitement", "anticipation"]

  valence:
    type: float
    description: "감정가 (-1: 부정, +1: 긍정)"

  arousal:
    type: float
    description: "각성 수준 (0: 낮음, 1: 높음)"

  scientific_evidence:
    type: object
    schema:
      study_name: string
      year: int
      sample_size: int
      methodology: string
      key_finding: string

  genre_associations:
    type: list[object]
    schema:
      genre: string
      typical_bpm: int
      emotion_fit: float

  use_cases:
    type: list[object]
    schema:
      scene_type: string
      recommended_bpm: int
      example_films: list[string]

# 예시 데이터 (2025 EEG 연구 기반)
bpm_emotion_data:
  - bpm_range: {min: 40, max: 60}
    primary_emotion: "contemplation"
    secondary_emotions: ["sadness", "peace", "introspection"]
    valence: -0.2
    arousal: 0.2
    scientific_evidence:
      study_name: "Neural Correlates of Tempo Perception in Film Music"
      year: 2025
      sample_size: 120
      methodology: "EEG + self-report"
      key_finding: "느린 템포는 DMN(Default Mode Network) 활성화"
    use_cases:
      - scene_type: "reflection_moment"
        recommended_bpm: 50
        example_films: ["Interstellar (docking)", "Up (opening)"]

  - bpm_range: {min: 60, max: 80}
    primary_emotion: "calm"
    secondary_emotions: ["comfort", "nostalgia", "warmth"]
    valence: 0.3
    arousal: 0.3

  - bpm_range: {min: 80, max: 100}
    primary_emotion: "neutral_focus"
    secondary_emotions: ["curiosity", "mild_tension"]
    valence: 0.0
    arousal: 0.5

  - bpm_range: {min: 100, max: 120}
    primary_emotion: "energy"
    secondary_emotions: ["motivation", "determination", "excitement"]
    valence: 0.4
    arousal: 0.7

  - bpm_range: {min: 120, max: 140}
    primary_emotion: "excitement"
    secondary_emotions: ["joy", "thrill", "anticipation"]
    valence: 0.6
    arousal: 0.85

  - bpm_range: {min: 140, max: 180}
    primary_emotion: "intensity"
    secondary_emotions: ["urgency", "panic", "exhilaration"]
    valence: 0.0
    arousal: 0.95
```

### 3.2 데이터셋: key_emotion_mapping

```yaml
id: key_emotion_mapping
description: "조성(Key)과 감정의 매핑 데이터"
source: "음악 이론, 심리학 연구"
size: ~24 documents (12 장조 + 12 단조)

schema:
  key:
    type: string
    example: "C_major"

  mode:
    type: string
    enum: ["major", "minor"]

  emotional_character:
    type: string
    description: "전통적 감정 특성"

  modern_associations:
    type: list[string]
    description: "현대 영화 음악에서의 용도"

  brightness_score:
    type: float
    description: "밝기 점수 (0: 어두움, 1: 밝음)"

  tension_score:
    type: float
    description: "긴장도 점수 (0: 이완, 1: 긴장)"

  famous_examples:
    type: list[object]
    schema:
      piece: string
      composer: string
      film: string (optional)
      usage: string

  genre_affinity:
    type: list[object]
    schema:
      genre: string
      affinity_score: float

# 예시 데이터
key_emotion_data:
  - key: "C_major"
    mode: "major"
    emotional_character: "순수, 단순, 결백"
    modern_associations: ["hope", "innocence", "new_beginning"]
    brightness_score: 0.9
    tension_score: 0.1
    famous_examples:
      - piece: "Imagine"
        composer: "John Lennon"
        usage: "희망과 평화의 메시지"
      - piece: "Toy Story Main Theme"
        composer: "Randy Newman"
        film: "Toy Story"
        usage: "순수한 우정과 모험"

  - key: "A_minor"
    mode: "minor"
    emotional_character: "우수, 그리움, 부드러운 슬픔"
    modern_associations: ["nostalgia", "longing", "bittersweet"]
    brightness_score: 0.3
    tension_score: 0.4
    famous_examples:
      - piece: "Summer"
        composer: "Joe Hisaishi"
        film: "기쿠지로의 여름"
        usage: "그리움과 여름의 기억"

  - key: "D_minor"
    mode: "minor"
    emotional_character: "우울, 심각, 운명적"
    modern_associations: ["doom", "fate", "dark_power"]
    brightness_score: 0.15
    tension_score: 0.75
    famous_examples:
      - piece: "Requiem K.626"
        composer: "Mozart"
        usage: "죽음과 엄숙함"
      - piece: "Dark Knight Main Theme"
        composer: "Hans Zimmer"
        film: "The Dark Knight"
        usage: "암울하고 위협적인 분위기"
```

### 3.3 데이터셋: composer_dna_database

```yaml
id: composer_dna_database
description: "영화/게임 작곡가 DNA 프로필"
source: "작품 분석, 인터뷰, 마스터클래스"
size: ~30 documents

schema:
  composer_key:
    type: string
    example: "hans_zimmer"

  name_ko:
    type: string
    example: "한스 짐머"

  name_en:
    type: string
    example: "Hans Zimmer"

  signature_elements:
    type: list[object]
    schema:
      element: string
      description: string
      usage: string

  preferred_keys:
    type: list[string]
    description: "선호 조성"

  typical_bpm_range:
    type: object
    schema:
      min: int
      max: int
      typical: int

  orchestration_style:
    type: object
    schema:
      primary_instruments: list[string]
      signature_combinations: list[string]
      texture_preference: string  # "dense", "sparse", "layered"

  rhythmic_patterns:
    type: list[object]
    schema:
      pattern_name: string
      description: string
      example_track: string

  harmonic_language:
    type: object
    schema:
      chord_progressions: list[string]
      modal_preferences: list[string]
      tension_techniques: list[string]

  production_techniques:
    type: list[string]
    description: "사운드 디자인 특징"

  compatible_genres:
    type: list[string]

  notable_works:
    type: list[object]
    schema:
      title: string
      year: int
      key_tracks: list[string]
      style_notes: string

  suno_prompt_template:
    type: string
    description: "Suno AI용 스타일 프롬프트"

  udio_prompt_template:
    type: string
    description: "Udio AI용 스타일 프롬프트"

# 예시 데이터
composer_profiles:
  - composer_key: "hans_zimmer"
    name_ko: "한스 짐머"
    signature_elements:
      - element: "Braaam"
        description: "저음 황동 섹션의 스타카토 히트"
        usage: "긴장, 위협, 공포의 순간"
      - element: "Tick-Tock Rhythm"
        description: "시계 소리 기반 퍼커션 패턴"
        usage: "시간 압박, 긴급함 (Dunkirk, Interstellar)"
      - element: "Layered Synth Pads"
        description: "신스 패드와 오케스트라의 블렌딩"
        usage: "공간감, 서사시적 분위기"
    preferred_keys: ["D_minor", "C_minor", "G_minor"]
    typical_bpm_range: {min: 60, max: 140, typical: 90}
    orchestration_style:
      primary_instruments: ["brass_section", "strings", "synth_bass", "percussion"]
      signature_combinations: ["french_horns+cello", "synth+orchestra", "ethnic_percussion+strings"]
      texture_preference: "layered"
    rhythmic_patterns:
      - pattern_name: "Ostinato Build"
        description: "반복 리프가 점진적으로 레이어 추가"
        example_track: "Time (Inception)"
    suno_prompt_template: "Epic cinematic orchestral, Hans Zimmer style, dramatic brass, layered synths, building tension, {bpm} BPM, {key}"

  - composer_key: "joe_hisaishi"
    name_ko: "조 히사이시"
    signature_elements:
      - element: "Minimalist Piano"
        description: "단순하고 반복적인 피아노 멜로디"
        usage: "서정적, 그리움, 순수함"
      - element: "Waltz Time"
        description: "3/4 박자의 우아한 리듬"
        usage: "판타지, 마법, 날아오르는 장면"
      - element: "Accordion Texture"
        description: "프랑스 뮈제트 스타일 아코디언"
        usage: "유럽 분위기, 노스탤지어"
    preferred_keys: ["A_minor", "C_major", "D_major"]
    typical_bpm_range: {min: 70, max: 130, typical: 100}
    suno_prompt_template: "Minimalist piano, Joe Hisaishi style, Ghibli-inspired, gentle strings, nostalgic, {bpm} BPM, {key}"
```

### 3.4 데이터셋: scene_music_patterns

```yaml
id: scene_music_patterns
description: "씬 타입별 음악 패턴 및 큐 포인트"
source: "영화 음악 분석, 스코어링 가이드"
size: ~50 documents

schema:
  scene_type:
    type: string
    example: "chase_sequence"

  description:
    type: string

  music_requirements:
    type: object
    schema:
      bpm_range: object  # {min, max}
      key_preference: list[string]
      intensity_curve: string  # "ascending", "descending", "oscillating"
      dynamics: string  # "pp", "mp", "mf", "ff"

  instrument_recommendations:
    type: list[object]
    schema:
      instrument: string
      role: string  # "lead", "rhythm", "accent"
      usage_notes: string

  cue_point_rules:
    type: list[object]
    schema:
      trigger: string  # "action_start", "emotion_shift", "cut"
      music_response: string
      timing: string  # "anticipate", "sync", "delay"

  transition_techniques:
    type: list[object]
    schema:
      from_state: string
      to_state: string
      technique: string

  example_analysis:
    type: list[object]
    schema:
      film: string
      scene_description: string
      composer: string
      technique_used: string

# 예시 데이터
scene_patterns:
  - scene_type: "chase_sequence"
    description: "추격 장면 - 높은 에너지, 지속적 긴장"
    music_requirements:
      bpm_range: {min: 130, max: 180}
      key_preference: ["D_minor", "E_minor", "G_minor"]
      intensity_curve: "ascending_with_peaks"
      dynamics: "ff"
    instrument_recommendations:
      - instrument: "percussion_ensemble"
        role: "rhythm"
        usage_notes: "드라이빙 비트, 16분음표 하이햇"
      - instrument: "brass_stabs"
        role: "accent"
        usage_notes: "액센트 포인트, 스타카토"
      - instrument: "string_tremolo"
        role: "texture"
        usage_notes: "긴장감 레이어"
    cue_point_rules:
      - trigger: "near_miss"
        music_response: "sudden_accent"
        timing: "sync"
      - trigger: "corner_turn"
        music_response: "key_change"
        timing: "anticipate"
    example_analysis:
      - film: "Mad Max: Fury Road"
        scene_description: "War Rig 추격전"
        composer: "Tom Holkenborg"
        technique_used: "constant 8th note ostinato + brass hits"

  - scene_type: "romantic_confession"
    description: "고백/로맨틱 순간 - 취약함, 감정적 절정"
    music_requirements:
      bpm_range: {min: 60, max: 80}
      key_preference: ["C_major", "F_major", "A_major"]
      intensity_curve: "gradual_build_to_peak"
      dynamics: "p_to_mf"
    instrument_recommendations:
      - instrument: "solo_piano"
        role: "lead"
        usage_notes: "단순 멜로디, 공간 활용"
      - instrument: "strings_sustained"
        role: "support"
        usage_notes: "점진적 진입, 클라이맥스 강조"
```

### 3.5 데이터셋: instrument_genre_mapping

```yaml
id: instrument_genre_mapping
description: "악기-장르-감정 삼중 매핑"
source: "음악 이론, 편곡 가이드"
size: ~80 documents

schema:
  instrument_id:
    type: string
    example: "french_horn"

  instrument_name_ko:
    type: string
    example: "프렌치 호른"

  family:
    type: string
    enum: ["strings", "brass", "woodwinds", "percussion", "keyboard", "electronic", "ethnic"]

  emotional_associations:
    type: list[object]
    schema:
      emotion: string
      intensity: float
      usage_context: string

  genre_affinity:
    type: list[object]
    schema:
      genre: string
      affinity_score: float
      typical_role: string

  register_characteristics:
    type: object
    schema:
      low: string   # 감정적 특성
      mid: string
      high: string

  combination_synergies:
    type: list[object]
    schema:
      partner_instrument: string
      combined_effect: string
      example_usage: string

  production_notes:
    type: string
    description: "AI 음악 생성 시 주의사항"

# 예시 데이터
instrument_data:
  - instrument_id: "french_horn"
    instrument_name_ko: "프렌치 호른"
    family: "brass"
    emotional_associations:
      - emotion: "heroism"
        intensity: 0.9
        usage_context: "주인공 테마, 승리의 순간"
      - emotion: "nobility"
        intensity: 0.85
        usage_context: "왕실, 기사, 고귀한 캐릭터"
      - emotion: "longing"
        intensity: 0.7
        usage_context: "부드럽게 연주 시, 그리움"
    genre_affinity:
      - genre: "epic_adventure"
        affinity_score: 0.95
        typical_role: "heroic_melody"
      - genre: "fantasy"
        affinity_score: 0.9
        typical_role: "magical_moment"
    register_characteristics:
      low: "웅장함, 위협, 어두운 힘"
      mid: "영웅적, 고귀함, 서사시적"
      high: "밝음, 승리, 환희"
    combination_synergies:
      - partner_instrument: "cello"
        combined_effect: "서사시적 웅장함"
        example_usage: "Lord of the Rings - Fellowship Theme"
```

---

## 4. 기능 고도화 설계

### 4.1 분석 파이프라인 고도화

```yaml
sound_craft_pipeline_v2:
  stage_1_scene_analysis:
    purpose: "씬별 감정 분석 및 음악 요구사항 도출"
    inputs:
      - scenario (with beat_sheet)
      - emotional_curve
    outputs:
      - scene_music_requirements: list[SceneMusicReq]
    rag_queries:
      - "scene_music_patterns → scene_type 기반"
      - "bpm_emotion_mapping → emotional_value 기반"

  stage_2_composer_style_match:
    purpose: "거장/작곡가 스타일 매칭"
    inputs:
      - auteur_key
      - genre
      - mood_preference
    outputs:
      - composer_style_guide
      - instrument_palette
    rag_queries:
      - "composer_dna_database → auteur 연결 작곡가"
      - "instrument_genre_mapping → genre 기반"

  stage_3_music_structure_design:
    purpose: "음악 구조 및 전환 설계"
    inputs:
      - scene_music_requirements
      - composer_style_guide
      - total_duration
    outputs:
      - music_sections: list[MusicSection]
      - transition_points: list[Transition]
    logic:
      - "각 섹션의 BPM, Key, 악기 결정"
      - "섹션 간 전환 기법 선택"

  stage_4_prompt_generation:
    purpose: "AI 음악 생성 프롬프트 생성"
    inputs:
      - music_sections
      - composer_style_guide
      - target_platform  # "suno", "udio", "soundraw"
    outputs:
      - section_prompts: list[MusicPrompt]
    logic:
      - "플랫폼별 프롬프트 형식 적용"
      - "작곡가 스타일 템플릿 활용"
```

### 4.2 출력 스키마 고도화

```python
class SoundDesignOutput(BaseModel):
    """고도화된 사운드 디자인 출력 스키마"""

    # 메타데이터
    metadata: SoundMetadata
    class SoundMetadata(BaseModel):
        total_duration: int
        target_platform: str  # "suno", "udio", "soundraw"
        composer_style: str
        overall_mood: str
        bpm_range: tuple[int, int]
        key_signature: str

    # 음악 구조
    music_structure: MusicStructure
    class MusicStructure(BaseModel):
        total_sections: int
        sections: list[MusicSection]

        class MusicSection(BaseModel):
            section_number: int
            time_range: str  # "0:00-0:30"
            duration_seconds: int
            scene_reference: str  # 연결된 씬
            emotional_target: str
            bpm: int
            key: str
            intensity: float  # 0-1
            instruments: list[str]
            rhythm_pattern: str
            harmonic_notes: str

    # 전환 포인트
    transitions: list[Transition]
    class Transition(BaseModel):
        from_section: int
        to_section: int
        time_position: str
        technique: str  # "crossfade", "hard_cut", "key_change", "tempo_shift"
        duration_seconds: float
        notes: str

    # 플랫폼별 프롬프트
    prompts: PlatformPrompts
    class PlatformPrompts(BaseModel):
        suno: list[SunoPrompt]
        udio: list[UdioPrompt]

        class SunoPrompt(BaseModel):
            section_number: int
            prompt: str
            style_tags: list[str]
            negative_tags: list[str]
            duration: int
            generation_notes: str

        class UdioPrompt(BaseModel):
            section_number: int
            prompt: str
            genre_hint: str
            mood_hint: str
            generation_notes: str

    # 타임라인 동기화 가이드
    sync_guide: SyncGuide
    class SyncGuide(BaseModel):
        cue_points: list[CuePoint]

        class CuePoint(BaseModel):
            time_position: str
            visual_event: str
            audio_response: str
            sync_precision: str  # "tight", "loose", "anticipate"

    # 근거
    evidence_refs: list[str]
```

---

## 5. 통합 설계

### 5.1 다른 앱과의 연동

```
┌─────────────────┐     scenario + beat_sheet     ┌─────────────────┐
│ 1.3 시나리오    │ ─────────────────────────────► │ 2.1 사운드      │
│     생성기      │                                │     크래프터    │
└─────────────────┘                                └────────┬────────┘
                                                            │
┌─────────────────┐     auteur_style                        │
│ 5.1 미학        │ ────────────────────────────────────────│
│     디렉터      │                                         │
└─────────────────┘                                         │
                                                            │ music_design
                                                            │ + sync_guide
                                                            ▼
                                                  ┌─────────────────┐
                                                  │ 3.2 비디오      │
                                                  │     메이커      │
                                                  └─────────────────┘
                                                    (Veo 오디오 동기화)
```

### 5.2 데이터 흐름

| 입력 | 소스 앱 | 변환 | 출력 | 대상 앱 |
|------|---------|------|------|---------|
| beat_sheet | 시나리오 생성기 | 씬별 음악 요구사항 | scene_music_reqs | 내부 처리 |
| emotional_curve | 시나리오 생성기 | BPM/Key 매핑 | bpm_key_plan | 내부 처리 |
| auteur_style | 미학 디렉터 | 작곡가 스타일 | composer_template | 프롬프트 생성 |
| music_design | - | - | audio_guide | 비디오 메이커 |

---

## 6. 조사 필요 항목 체크리스트

### 6.1 음악 심리학 조사

- [ ] BPM-감정 상관관계 연구 논문 수집
- [ ] 조성-감정 매핑 연구 정리
- [ ] 악기별 감정 연상 연구 분석
- [ ] 영화 음악 효과 연구 정리

### 6.2 작곡가 DNA 조사

- [ ] 한스 짐머 스타일 분석 (10개 작품)
- [ ] 조 히사이시 스타일 분석 (10개 작품)
- [ ] 엔니오 모리코네 스타일 분석
- [ ] 존 윌리엄스 스타일 분석
- [ ] 류이치 사카모토 스타일 분석

### 6.3 AI 음악 플랫폼 조사

- [ ] Suno 최신 프롬프트 가이드 (2026)
- [ ] Udio 스타일 태그 시스템 분석
- [ ] Soundraw 파라미터 분석
- [ ] 플랫폼별 최적 프롬프트 패턴 정리

### 6.4 통합 조사

- [ ] 비디오-오디오 동기화 기법
- [ ] Veo 네이티브 오디오 활용법
- [ ] 음악 생성 품질 평가 메트릭

---

## 7. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | BPM-감정 데이터 수집 | 2일 | 매핑 테이블 |
| 2 | 작곡가 DNA 분석 | 3일 | 프로필 10+ |
| 3 | 씬-음악 패턴 정리 | 2일 | 패턴 DB |
| 4 | Qdrant 컬렉션 구축 | 1일 | 벡터 적재 |
| 5 | 파이프라인 고도화 | 3일 | 코드 업데이트 |
| 6 | 테스트 및 튜닝 | 2일 | 품질 검증 |

---

## 8. 참고 자료

### 학술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| Music Psychology (2025) | 논문 | BPM-감정 EEG 연구 |
| Film Music Theory | 저서 | 영화 음악 작곡법 |
| Hans Zimmer MasterClass | 강의 | 영화 음악 접근법 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| Suno | https://suno.com/ | AI 음악 생성 |
| Udio | https://udio.com/ | AI 음악 생성 |
| Soundraw | https://soundraw.io/ | 커스텀 음악 생성 |

---

## 9. Native Audio Default 전략 (P0 보강)

> **Updated**: 2026-01-17 (컨설팅 피드백 반영)
> **Reference**: DIMENSION_APP_MACRO_PLANNING_2026.md Part 9.1

### 9.1 패러다임 전환: Separate → Native Audio

2025년 하반기 Veo 3.1과 Kling 2.6의 **Native Audio Generation** 기능 출시로
기존 "영상 생성 후 오디오 별도 생성" 워크플로우가 근본적으로 변화했습니다.

```yaml
workflow_paradigm_shift:
  before:
    - "Generate silent video"
    - "Create audio separately (Suno, ElevenLabs)"
    - "Manual lip-sync adjustment"
    - "Audio mixing in post-production"
    - "Timeline: Days to weeks"

  after:
    - "Single-pass audio-visual generation"
    - "Automatic lip-sync"
    - "Pre-mixed audio with balanced levels"
    - "Timeline: Minutes"
```

### 9.2 2026년 Native Audio 플랫폼 현황

| 플랫폼 | Native Audio | 출시일 | 지원 오디오 유형 |
|--------|-------------|--------|-----------------|
| **Veo 3.1** | ✅ 네이티브 | 2025.10 | 대화, 효과음, 앰비언트, BGM |
| **Kling 2.6** | ✅ 네이티브 | 2025.12 | 대화, 노래, 랩, 효과음, 앰비언트 |
| **Sora 2 Pro** | ✅ 네이티브 | 2025.05 | 대화, 효과음 |
| **Runway Gen-4** | ❌ 별도 | - | - |
| **Suno** | 🎵 음악 전용 | - | 작곡, 보컬 (영상 미지원) |

### 9.3 Native Audio 플랫폼별 특징

```yaml
native_audio_capabilities:
  veo_3_1:
    strengths:
      - "Rich synchronized audio from natural conversations"
      - "Lip-sync with AI-generated characters"
      - "Ambient noise matching environment"
      - "Sound effects timed to visual events"
    api_access: "Vertex AI, Gemini API"
    pricing: "$0.15-0.40/sec"
    best_for: ["cinematic_narrative", "atmospheric_establishing", "long_takes"]

  kling_2_6:
    strengths:
      - "Audio-Visual Coordination (리듬-시각 동기화)"
      - "Voice control: 속삭임 → 드라마틱 스크림 제어"
      - "Multilingual dialogue (한/영 지원)"
      - "Singing/Rap performance"
      - "Foley-quality sound effects"
    api_access: "Kling API, Kie.ai"
    pricing: "$0.07-0.14/sec"
    best_for: ["music_video", "singing_scene", "action_effects"]
```

### 9.4 사운드 크래프터 V2 전략

```yaml
app_2_1_sound_crafter_v2:
  priority_change:
    old: "Suno/Udio 프롬프트 생성 중심"
    new: "Native Audio 우선, 별도 생성은 보완"

  generation_strategy:
    tier_1_native_audio:
      description: "영상과 함께 생성 (기본)"
      tools:
        - "Veo 3.1 (대화/앰비언트)"
        - "Kling 2.6 (보이스/노래/효과음)"
      use_cases:
        - "대화 씬 (립싱크 필요)"
        - "효과음 타이밍이 중요한 씬"
        - "앰비언트/분위기 씬"
      output: "native_audio_prompt (영상 프롬프트에 통합)"

    tier_2_separate_bgm:
      description: "BGM만 별도 생성"
      tools:
        - "Suno (작곡 + 보컬)"
        - "Udio (인스트루멘탈)"
      use_cases:
        - "MV 메인 트랙"
        - "테마곡 필요 시"
        - "저작권 귀속 명확화 필요 시"
      output: "suno_prompt, udio_prompt"

    tier_3_post_enhancement:
      description: "후반 보정"
      tools:
        - "ElevenLabs (내레이션 재녹음)"
        - "MM Audio v2 (효과음 보강)"
      use_cases:
        - "Native 품질 불충분 시"
        - "특정 보이스 필요 시"
      output: "enhancement_guide"
```

### 9.5 업데이트된 출력 스키마

```python
class SoundDesignOutputV2(BaseModel):
    """Native Audio 통합 사운드 디자인 출력 스키마"""

    # 기존 필드 유지
    metadata: SoundMetadata
    music_structure: MusicStructure
    transitions: list[Transition]

    # 신규: 오디오 전략 (Native Audio 우선)
    audio_strategy: AudioStrategy
    class AudioStrategy(BaseModel):
        primary_method: Literal["native", "separate", "hybrid"]

        # Native Audio 설정
        native_config: NativeAudioConfig | None
        class NativeAudioConfig(BaseModel):
            platform: Literal["veo", "kling"]
            audio_prompt: str  # 영상 프롬프트에 통합
            voice_style: str | None
            ambience_description: str
            sfx_cues: list[SFXCue]

            class SFXCue(BaseModel):
                time_position: str  # "0:05"
                event: str  # "문 닫히는 소리"
                intensity: str  # "subtle", "prominent"

        # 별도 생성 설정 (BGM 등)
        separate_config: SeparateAudioConfig | None
        class SeparateAudioConfig(BaseModel):
            bgm_prompt: str | None  # Suno/Udio용
            voice_scripts: list[VoiceScript] | None
            generation_platform: str  # "suno", "udio", "elevenlabs"

    # 플랫폼별 프롬프트 (기존)
    prompts: PlatformPrompts

    # 근거
    evidence_refs: list[str]
```

### 9.6 씬 유형별 권장 오디오 전략

| 씬 유형 | 권장 전략 | 플랫폼 | 이유 |
|---------|----------|--------|------|
| 대화 씬 | Native | Kling 2.6 | 자동 립싱크, 감정 표현 |
| 액션 씬 | Native | Kling 2.6 | 실시간 효과음 동기화 |
| MV 댄스 | Hybrid | Kling + Suno | 댄스 영상 Native + BGM 별도 |
| 내레이션 | Native | Veo 3.1 | 앰비언트와 자연스러운 믹싱 |
| 앰비언트 | Native | Veo 3.1 | 환경음 최적화 |
| 테마곡 | Separate | Suno | 저작권 명확화, 재사용 |

---

## 10. Suno AI 통합 전략 (BGM 전문)

> **Reference**: DIMENSION_APP_MACRO_PLANNING_2026.md Part 9.5

### 10.1 Suno AI 역할 재정의

Native Audio 시대에서 Suno AI의 역할:
- ❌ 모든 오디오 생성 → ✅ **BGM/테마곡 전문 생성**
- ❌ 효과음 생성 → ✅ **Native Audio에 위임**
- ✅ **MV 메인 트랙 작곡**
- ✅ **저작권 귀속 필요 시**

### 10.2 Suno + Native Audio 하이브리드 워크플로우

```yaml
hybrid_workflow:
  mv_production:
    step_1:
      tool: "Suno"
      action: "BGM 메인 트랙 생성"
      output: "audio_track.mp3, bpm, key, duration"

    step_2:
      tool: "Kling 2.6"
      action: "영상 + 댄스 동기화"
      input: "Suno audio + storyboard"
      mode: "Audio-Visual Coordination"
      output: "video_with_sync.mp4"

    step_3:
      tool: "Post-processing"
      action: "BGM 오버레이 + 믹싱"
      output: "final_mv.mp4"

  dialog_scene_with_theme:
    step_1:
      tool: "Kling 2.6 Native"
      action: "대화 씬 + 실시간 오디오"
      output: "dialog_scene.mp4"

    step_2:
      tool: "Suno"
      action: "언더스코어 BGM 생성"
      style: "subtle orchestral, supporting"

    step_3:
      tool: "Audio mixing"
      action: "Dialog + BGM 레이어 믹싱"
```

### 10.3 Suno 프롬프트 템플릿 V2

```yaml
suno_prompt_templates:
  mv_dance_track:
    template: |
      [Genre] {genre}, K-pop influenced
      [Mood] {mood}, energetic, catchy
      [BPM] {bpm}
      [Structure] Intro(8bar) - Verse(16bar) - Chorus(16bar) - Verse - Chorus - Bridge(8bar) - Outro(8bar)
      [Instruments] {instruments}
      [Vocal] {vocal_style}
      [Key] {key}
    example: |
      [Genre] Electronic Dance Pop, K-pop influenced
      [Mood] Euphoric, summer vibes, catchy
      [BPM] 128
      [Structure] Standard pop structure with powerful drop
      [Instruments] Synth leads, punchy drums, bass drops
      [Vocal] Female, bright, powerful chorus
      [Key] C Major

  underscore_bgm:
    template: |
      [Genre] Cinematic Underscore, {style}
      [Mood] {emotion}, supporting not dominating
      [Tempo] {tempo}
      [Instruments] {instruments}
      [Dynamics] Subtle to moderate, leaving space for dialogue
      [Duration] {duration} seconds
    example: |
      [Genre] Cinematic Underscore, Joe Hisaishi style
      [Mood] Nostalgic, warm, bittersweet
      [Tempo] Slow, 68 BPM
      [Instruments] Solo piano, soft strings
      [Dynamics] pp to mp, gentle crescendos
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | BPM-감정 연구 수집 |
| 2026-01-17 | Native Audio 전략 보강 (Part 9,10) | 완료 | Tier별 구현 |
| 2026-01-17 | 웹 리서치 완료 (Suno AI, Native Audio 2026) | 완료 | 오디오 통합 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### AI 오디오 생성 및 Native Audio 종합 분석

#### 1. Suno AI (음악 생성 선두)

```yaml
suno_ai_specs:
  market_position: "AI 음악 생성 시장 선두"

  api_access:
    official: "제한적 (B2B 중심)"
    third_party:
      comet_api:
        pricing: "$0.144/generation"
        features: "전체 기능 접근"
      kie_ai:
        pricing: "크레딧 기반"
        features: "Suno + 기타 음악 AI"

  capabilities:
    - "텍스트 → 풀 트랙 생성 (2-4분)"
    - "장르, 템포, 분위기 제어"
    - "보컬 포함 가능"
    - "스타일 참조"

  use_case_for_crebit:
    - "배경음악 자동 생성"
    - "씬 분위기 기반 음악 제작"
    - "Native Audio fallback (post-processing)"
```

#### 2. Native Audio 플랫폼 비교 (2026)

```yaml
native_audio_platforms:
  veo_31:
    native_audio: true
    capabilities:
      - "대화 + 환경음 + 음악 통합"
      - "립싱크 자동화"
      - "4K 해상도 지원"
    duration: "4-8초"
    pricing: "$0.15-0.40/sec"

  kling_26:
    native_audio: true
    capabilities:
      - "8+ 언어 립싱크"
      - "노래/랩 지원"
      - "감정 톤 제어"
    duration: "최대 2분"
    pricing: "~$0.07-0.14/sec"
    strengths: "가성비 최고, 음악 씬에 특화"

  sora_2:
    native_audio: true
    capabilities:
      - "자연스러운 대화"
      - "환경 사운드"
      - "감정 뉘앙스"
    access: "제한적 (ChatGPT Plus)"

  runway_gen45:
    native_audio: true
    capabilities:
      - "Multi-shot 오디오 연속성"
      - "음향 효과 제어"
    release: "Dec 2025"
```

#### 3. Native Audio vs Post Audio 전략

```yaml
audio_strategy_decision:
  use_native_audio_when:
    - "대화 씬 (립싱크 필수)"
    - "환경 사운드가 씬의 핵심"
    - "음악과 시각이 동기화 필요"
    - "빠른 프로토타이핑"

  use_post_audio_when:
    - "정밀한 오디오 제어 필요"
    - "특정 음악 트랙 사용"
    - "다국어 더빙"
    - "기존 영상에 오디오 추가"

  hybrid_approach:
    step1: "Native Audio로 기본 생성"
    step2: "품질 평가 (자동)"
    step3_if_needed: "Suno/ElevenLabs로 보강"
```

#### 4. Crebit Sound Crafter 구현 권장

```yaml
crebit_sound_implementation:
  tiered_audio_strategy:
    tier1_native_first:
      platforms: ["Veo 3.1", "Kling 2.6"]
      use_when: "dialogue_scene OR ambient_critical"
      prompt_template: |
        [Visual]: {scene_description}
        [Dialogue]: {character_dialogue}
        [Ambient]: {environment_sounds}
        [Mood]: {emotional_tone}

    tier2_suno_enhancement:
      trigger: "music_scene OR soundtrack_needed"
      api: "CometAPI/Kie.ai"
      prompt_template: |
        Genre: {genre}
        Tempo: {bpm} BPM
        Mood: {mood}
        Duration: {duration}s

    tier3_elevenlabs_voice:
      trigger: "narration OR specific_voice"
      use_case: "보이스오버, 캐릭터 음성"

  audio_quality_metrics:
    sync_score: "립싱크 정확도"
    audio_clarity: "음질 (노이즈, 왜곡)"
    mood_match: "씬 분위기 매칭"

  pipeline_integration:
    input:
      - scene_script
      - mood_keywords
      - music_preferences
    output:
      - audio_track: "generated or sourced"
      - sync_markers: "timestamp alignment"
      - quality_report: "자동 평가"
```

### Sources
- Suno AI API Documentation (via CometAPI)
- Veo 3.1 Native Audio Specs (Google)
- Kling 2.6 Audio Features (Kuaishou)
- AI Music Generation Market Analysis 2025
