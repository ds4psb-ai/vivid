# App 1.1: 심연의 거울 (Abyss Mirror) 상세 연구

> **Status**: 연구 진행 중
> **Priority**: P0
> **Dimension**: AI (Persona)

---

## 1. 현재 상태 분석

### 1.1 기존 구현

```python
# 파일 위치
file_path = "backend/app/routers/dimension/aesthetic.py"

# 엔드포인트
endpoints = [
    "POST /dimension/persona/analyze",
    "POST /dimension/persona/analyze/stream",
]

# 현재 기능
current_features = [
    "기본 페르소나 분석",
    "단계별 분석 (intro, deep_dive, synthesis, dna_generation)",
    "MBTI 연동 가능",
    "사주 정보 입력 가능",
]
```

### 1.2 현재 한계점

| 한계점 | 영향 | 해결 방향 |
|--------|------|----------|
| 심리학 기반 데이터 부족 | 분석 깊이 제한 | 학술 데이터 수집 |
| MBTI-창작 성향 연결 약함 | 실용성 저하 | 연구 기반 매핑 구축 |
| 거장 매칭 로직 미약 | 개인화 부족 | 거장 DNA + 성격 매핑 |

---

## 2. 핵심 연구 주제

### 2.1 MBTI와 창작 성향 연구

**연구 질문**:
- 각 MBTI 유형별 창작 성향은 어떻게 다른가?
- 특정 MBTI 유형이 특정 장르에 더 적합한가?
- MBTI와 거장 감독들의 상관관계는?

**조사 대상**:
1. MBTI 유형별 창작자 분석 연구
2. 창작 심리학 학술 논문
3. 거장 감독/작곡가 성격 분석 자료

### 2.2 창작 심리학 연구

**연구 질문**:
- 창작 동기 유형은 어떻게 분류되는가?
- 창작 블록의 유형과 해결 전략은?
- 페르소나와 작품 스타일의 상관관계는?

**조사 대상**:
1. 창작 동기 이론 (Amabile, Csikszentmihalyi 등)
2. Flow 이론과 창작
3. 예술가 심리 연구

### 2.3 거장-성격 매핑 연구

**연구 질문**:
- 각 거장의 성격 유형은?
- 성격과 작품 스타일의 상관관계는?
- 사용자 성격과 거장 스타일 궁합은?

**조사 대상**:
1. 거장 전기 및 인터뷰
2. 작품 분석을 통한 성격 추론
3. 팬덤/비평계 분석

---

## 3. RAG 데이터 요구사항

### 3.1 데이터셋: mbti_creative_profiles

```yaml
id: mbti_creative_profiles
description: "16 MBTI 유형별 창작 성향 프로필"
source: "학술 논문 + 창작자 인터뷰 분석"
size: ~50 documents

schema:
  mbti_type:
    type: string
    enum: ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
           "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]

  creative_strengths:
    type: list[string]
    example: ["conceptual depth", "visual imagination", "narrative structure"]

  creative_challenges:
    type: list[string]
    example: ["perfectionism", "starting projects", "finishing projects"]

  preferred_genres:
    type: list[string]
    example: ["psychological thriller", "sci-fi", "documentary"]

  preferred_roles:
    type: list[string]
    example: ["director", "writer", "editor", "composer"]

  auteur_affinity:
    type: list[object]
    schema:
      auteur: string
      affinity_score: float (0-1)
      reason: string

  creative_process:
    type: object
    schema:
      ideation_style: string  # "intuitive", "research-based", "collaborative"
      workflow_preference: string  # "structured", "organic", "deadline-driven"
      revision_approach: string  # "perfectionist", "iterative", "one-take"

  motivation_type:
    type: string
    enum: ["intrinsic", "extrinsic", "mixed"]

  example_creators:
    type: list[string]
    description: "이 유형의 유명 창작자 예시"
```

### 3.2 데이터셋: auteur_personality_mapping

```yaml
id: auteur_personality_mapping
description: "거장 감독/작곡가의 성격 유형 및 작품 스타일 분석"
source: "전기, 인터뷰, 작품 분석"
size: ~30 documents

schema:
  auteur_key:
    type: string
    example: "bong_joon_ho"

  name_ko:
    type: string
    example: "봉준호"

  name_en:
    type: string
    example: "Bong Joon-ho"

  field:
    type: string
    enum: ["film_director", "animator", "composer", "cinematographer"]

  estimated_mbti:
    type: string
    confidence: float (0-1)
    source: string  # 추정 근거

  personality_traits:
    type: list[string]
    example: ["perfectionist", "socially conscious", "genre-defying"]

  creative_philosophy:
    type: string
    description: "창작 철학 요약"

  signature_themes:
    type: list[string]
    example: ["class divide", "dark humor", "moral ambiguity"]

  working_style:
    type: object
    schema:
      collaboration_preference: string
      revision_approach: string
      production_speed: string

  compatible_mbti:
    type: list[string]
    description: "이 거장 스타일과 잘 맞는 MBTI 유형"

  key_quotes:
    type: list[string]
    description: "창작 철학을 보여주는 인용구"
```

### 3.3 데이터셋: creative_block_patterns

```yaml
id: creative_block_patterns
description: "창작 블록 유형 및 해결 전략"
source: "심리학 연구, 창작론"
size: ~20 documents

schema:
  block_type:
    type: string
    example: "perfectionism_paralysis"

  description:
    type: string

  symptoms:
    type: list[string]

  common_triggers:
    type: list[string]

  affected_mbti_types:
    type: list[string]

  resolution_strategies:
    type: list[object]
    schema:
      strategy: string
      description: string
      effectiveness: float (0-1)

  prevention_tips:
    type: list[string]

  related_auteurs:
    type: list[string]
    description: "이 블록을 극복한 거장 예시"
```

---

## 4. 기능 고도화 설계

### 4.1 분석 단계 고도화

```yaml
analysis_stages_v2:
  stage_0_greeting:
    purpose: "라포 형성 및 분석 방향 설정"
    duration: "1-2 exchanges"
    techniques: ["warm_welcome", "expectation_setting"]

  stage_1_surface_exploration:
    purpose: "표면적 취향 탐색"
    duration: "3-5 exchanges"
    techniques: ["favorite_works", "genre_preferences", "role_models"]
    rag_query: "사용자 언급 작품/장르 기반 초기 프로파일링"

  stage_2_deep_dive:
    purpose: "깊은 성향 탐색"
    duration: "5-7 exchanges"
    techniques:
      - "projective_questions"  # "이 장면을 본다면 어떤 감정?"
      - "hypothetical_scenarios"  # "만약 영화를 만든다면?"
      - "conflict_exploration"  # "가장 싫어하는 작품 스타일은?"
    rag_query: "심리학 기반 질문 패턴"

  stage_3_pattern_recognition:
    purpose: "패턴 도출 및 가설 검증"
    duration: "2-3 exchanges"
    techniques:
      - "pattern_reflection"  # "~한 경향이 보이는데, 맞나요?"
      - "mbti_correlation"  # MBTI 유형 추론
    rag_query: "MBTI-창작 성향 매핑"

  stage_4_synthesis:
    purpose: "종합 분석 및 거장 매칭"
    duration: "1-2 exchanges"
    output:
      - "personality_profile"
      - "creative_dna"
      - "auteur_affinity"
      - "recommended_workflow"
```

### 4.2 출력 스키마 고도화

```python
class PersonaDNA(BaseModel):
    """고도화된 페르소나 DNA 스키마"""

    # Core Identity
    core_identity: CoreIdentity
    class CoreIdentity(BaseModel):
        mbti_type: str
        mbti_confidence: float  # 0-1
        dominant_traits: list[str]
        creative_archetype: str  # "The Perfectionist Storyteller" 등
        archetype_description: str

    # Aesthetic Preferences
    aesthetic_preferences: AestheticPreferences
    class AestheticPreferences(BaseModel):
        visual_taste: VisualTaste
        narrative_preference: NarrativePreference
        audio_preference: AudioPreference

        class VisualTaste(BaseModel):
            color_preference: str  # "warm", "cool", "muted", "vibrant"
            composition_style: str  # "symmetrical", "dynamic", "minimalist"
            lighting_mood: str  # "high_key", "low_key", "natural"

        class NarrativePreference(BaseModel):
            preferred_genres: list[str]
            story_structure: str  # "linear", "non_linear", "circular"
            theme_interests: list[str]
            pacing_preference: str  # "slow_burn", "fast_paced", "varied"

        class AudioPreference(BaseModel):
            music_genres: list[str]
            tempo_preference: str  # "slow", "medium", "fast"
            mood_preference: str

    # Auteur Affinity
    auteur_affinity: AuteurAffinity
    class AuteurAffinity(BaseModel):
        primary_auteur: AuteurMatch
        secondary_matches: list[AuteurMatch]

        class AuteurMatch(BaseModel):
            auteur_key: str
            auteur_name: str
            affinity_score: float  # 0-1
            matching_aspects: list[str]
            differentiating_aspects: list[str]
            recommended_techniques: list[str]

    # Creative Process Profile
    creative_process: CreativeProcess
    class CreativeProcess(BaseModel):
        ideation_style: str
        workflow_preference: str
        collaboration_style: str
        potential_blocks: list[str]
        block_prevention_tips: list[str]

    # DNA Prompt (다른 앱에서 사용)
    creative_dna_prompt: str
    # 예: "perfectionist storyteller with visual minimalism preference,
    #      drawn to psychological depth and ambiguous endings..."

    # Evidence
    evidence_refs: list[str]  # RAG 근거
```

---

## 5. 조사 필요 항목 체크리스트

### 5.1 학술 연구 조사

- [ ] MBTI와 창의성 연구 논문 수집
- [ ] 창작 심리학 핵심 이론 정리
- [ ] Flow 이론과 창작 과정 연구
- [ ] 예술가 성격 유형 연구

### 5.2 거장 분석 조사

- [ ] 봉준호 성격/창작 철학 분석
- [ ] 크리스토퍼 놀란 성격/창작 철학 분석
- [ ] 드니 빌뇌브 성격/창작 철학 분석
- [ ] 왕가위 성격/창작 철학 분석
- [ ] 타란티노 성격/창작 철학 분석
- [ ] 미야자키 하야오 성격/창작 철학 분석
- [ ] 신카이 마코토 성격/창작 철학 분석

### 5.3 경쟁 서비스 분석

- [ ] MBTI 기반 창작 추천 서비스 조사
- [ ] 창작자 페르소나 분석 도구 조사
- [ ] AI 기반 성격 분석 서비스 벤치마킹

---

## 6. 예상 구현 일정

| Phase | 작업 | 기간 | 산출물 |
|-------|------|------|--------|
| 1 | 학술 자료 수집 | 3일 | 논문/자료 목록 |
| 2 | 데이터 정제 및 구조화 | 2일 | YAML/JSON 데이터 |
| 3 | Qdrant 컬렉션 구축 | 1일 | 벡터 DB 적재 |
| 4 | 분석 로직 고도화 | 3일 | 코드 업데이트 |
| 5 | 테스트 및 튜닝 | 2일 | 테스트 결과 |

---

## 7. 참고 자료

### 학술 자료 (수집 예정)

| 자료명 | 유형 | 핵심 내용 |
|--------|------|----------|
| Amabile's Creativity Research | 논문 | 창작 동기 이론 |
| Csikszentmihalyi's Flow Theory | 저서 | Flow와 창작 |
| MBTI Manual | 가이드 | MBTI 유형 상세 |

### 참고 서비스

| 서비스 | URL | 참고 포인트 |
|--------|-----|-------------|
| 16Personalities | https://www.16personalities.com/ | MBTI 설명 방식 |

---

## 8. Part 9/10 기술 연계 (2026 보강)

### 8.1 TieredContext 통합

페르소나 데이터가 전체 워크플로우에 전파되도록 TieredContext를 활용합니다.

```yaml
tiered_context_integration:
  purpose: "페르소나 데이터를 전체 세션에 공유"

  session_level_data:
    description: "세션 전역 데이터 (모든 단계에서 접근 가능)"
    stored_data:
      - "mbti_type: INFP"
      - "creative_style: visual_storyteller"
      - "auteur_affinity: [bong, wong]"
      - "strength_areas: [emotional_depth, visual_metaphor]"
      - "growth_areas: [pacing, dialogue]"

  propagation_to_apps:
    scenario_generator:
      receives: ["creative_style", "strength_areas"]
      uses_for: "서사 구조 추천, 강점 활용 씬 배치"

    storyboard_sketcher:
      receives: ["visual_preference", "auteur_affinity"]
      uses_for: "비주얼 스타일 힌트"

    aesthetic_director:
      receives: ["auteur_affinity", "creative_style"]
      uses_for: "거장 스타일 블렌딩 비율 조정"

  implementation:
    code_example: |
      ctx = TieredContext(session_id=session_id)
      ctx.set_session("persona", persona_result)
      # 다른 앱에서 접근
      persona = ctx.resolve(step_id, "persona")
```

### 8.2 캐릭터 메모리 뱅크 연동 (Part 9.2)

페르소나 분석 결과를 기반으로 캐릭터 레퍼런스 팩을 생성합니다.

```yaml
character_generation_from_persona:
  workflow:
    step_1:
      action: "페르소나 분석 완료"
      output: "creative_profile"

    step_2:
      action: "사용자-캐릭터 투영 분석"
      determines:
        - "주인공과의 동일시 정도"
        - "선호 캐릭터 아키타입"
        - "감정 표현 스타일"

    step_3:
      action: "캐릭터 시드 생성 (선택적)"
      output:
        - "character_description: 외형, 성격 묘사"
        - "expression_range: 감정 표현 범위"
        - "visual_reference_hints: 참고 이미지 키워드"

  integration_with_storyboard:
    data_flow:
      - "페르소나 → 캐릭터 시드"
      - "캐릭터 시드 → 스토리보드 스케처"
      - "스토리보드 → 캐릭터 메모리 뱅크 구축"
    benefit: "사용자 페르소나 반영된 캐릭터 일관성"
```

### 8.3 Multi-RAG Router 연동

페르소나 분석 시 Multi-RAG Router를 통해 관련 데이터를 수집합니다.

```yaml
rag_integration:
  query_routing:
    mbti_creative_patterns:
      source: "MULTIMODAL_DIMENSION"
      collection: "creative_psychology"
      query: "INFP 유형의 창작 성향"

    auteur_affinity_matching:
      source: "AUTEUR_DNA"
      backend: "NotebookLM"
      query: "감성적 시각 표현 거장 스타일"

    user_history_reference:
      source: "USER_HISTORY"
      backend: "PostgreSQL"
      query: "이전 작업 패턴 분석"

  evidence_refs_generation:
    example: |
      evidence_refs = [
          "rag:creative_psychology:mbti:infp_visual_pattern",
          "rag:auteur_dna:bong:emotional_storytelling",
          "db:user_sessions:prev_analysis_id"
      ]
```

### 8.4 수정된 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Abyss Mirror V2 + TieredContext                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Input (MBTI, 창작 성향 질문)                                           │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                   Persona Analyzer                          │            │
│  │   - MBTI 기반 창작 성향 분석                                 │            │
│  │   - 거장 친화도 매칭                                         │            │
│  │   - Multi-RAG 쿼리 (AUTEUR_DNA, USER_HISTORY)               │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                   TieredContext                              │            │
│  │   SessionContext (전역)                                      │            │
│  │   ├── persona: PersonaResult                                │            │
│  │   ├── auteur_affinity: list[str]                            │            │
│  │   └── creative_profile: CreativeProfile                     │            │
│  └─────────────────────────────────────────────────────────────┘            │
│     │                                                                        │
│     ├──────────────────┬──────────────────┬────────────────────┐            │
│     ▼                  ▼                  ▼                    ▼            │
│ ┌─────────┐      ┌─────────┐      ┌─────────────┐      ┌───────────┐       │
│ │Scenario │      │Storyboard│     │  Aesthetic  │      │  Quality  │       │
│ │Generator│      │Sketcher │      │  Director   │      │  Director │       │
│ │(구조힌트)│      │(비주얼)  │      │(스타일블렌딩)│      │(평가기준) │       │
│ └─────────┘      └─────────┘      └─────────────┘      └───────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 연구 진행 로그

| 날짜 | 작업 | 결과 | 다음 단계 |
|------|------|------|----------|
| 2026-01-17 | 연구 문서 초안 작성 | 완료 | 학술 자료 수집 시작 |
| 2026-01-17 | Part 9/10 기술 연계 (TieredContext, 캐릭터 메모리 뱅크, Multi-RAG) | 완료 | 페르소나-창작 매핑 구현 |
| 2026-01-17 | 웹 리서치 완료 (MBTI-창작 연구, 페르소나 분석) | 완료 | 창작 잠재력 공식 구현 |

---

## 웹 리서치 결과 (2026-01-17)

### MBTI와 창의성 연구 핵심 발견

#### 1. MBTI-CI (Creativity Index) 공식

```yaml
mbti_creativity_formula:
  formula: "3SN + JP - EI - 0.5TF"
  interpretation:
    high_creativity_types:
      - INFP: "가장 창의적 (직관 + 감정 + 인식)"
      - ENFP: "열정적 창작자"
      - INTP: "논리적 혁신가"
      - ENTP: "아이디어 발전가"
    components:
      SN: "감각-직관 (가장 큰 가중치 3x)"
      JP: "판단-인식 (인식형이 창의적)"
      EI: "외향-내향 (내향이 약간 유리)"
      TF: "사고-감정 (약한 영향)"

  key_insight: |
    직관(N)과 인식(P) 유형이 창의성과 가장 강하게 상관
    - N: 추상적 사고, 가능성 탐구
    - P: 유연성, 열린 결말 선호
```

#### 2. 창작 스타일별 MBTI 매핑

```yaml
creative_style_mbti_mapping:
  visionary_storyteller:
    types: ["INFP", "ENFP"]
    strengths:
      - "감정적 깊이"
      - "캐릭터 내면 탐구"
      - "상징적 표현"
    recommended_tools:
      - "auteur: 봉준호, 왕가위"
      - "tone: emotional, introspective"

  logical_architect:
    types: ["INTP", "INTJ"]
    strengths:
      - "복잡한 플롯 구조"
      - "세계관 설계"
      - "논리적 일관성"
    recommended_tools:
      - "auteur: 노란, 빌뇌브"
      - "tone: cerebral, precise"

  dramatic_director:
    types: ["ENTJ", "ENFJ"]
    strengths:
      - "대규모 서사"
      - "캐릭터 성장 아크"
      - "감정적 고조"
    recommended_tools:
      - "auteur: 스필버그, 카메론"
      - "tone: epic, emotional"

  experimental_artist:
    types: ["ENTP", "ISTP"]
    strengths:
      - "장르 혼합"
      - "비선형 서사"
      - "기술적 혁신"
    recommended_tools:
      - "auteur: 타란티노, 가이 리치"
      - "tone: dynamic, unconventional"
```

#### 3. AI 페르소나 분석 도구 현황

```yaml
ai_persona_tools:
  limitations:
    - "MBTI 기반 창작 도구는 아직 미성숙"
    - "대부분 단순 성격 테스트 수준"
    - "창작 스타일 매핑은 수동 설계 필요"

  crebit_opportunity:
    - "MBTI → 창작 스타일 자동 매핑"
    - "거장 DNA와 연결"
    - "개인화된 창작 가이드 제공"
```

#### 4. Crebit Abyss Mirror 구현 권장

```yaml
crebit_abyss_implementation:
  persona_analysis:
    input:
      - "MBTI 유형 (필수)"
      - "창작 선호도 설문 (선택)"
      - "좋아하는 영화/감독 (선택)"

    output:
      creativity_index:
        formula: "3*SN + JP - EI - 0.5*TF"
        range: "-4.5 to +4.5"

      creative_profile:
        primary_style: "visionary | architect | dramatic | experimental"
        strengths: ["list of creative strengths"]
        recommended_auteurs: ["matched auteur keys"]
        narrative_preferences: ["preferred story structures"]

  tiered_context_integration:
    session_context:
      user_mbti: "stored at session level"
      creativity_index: "calculated once, reused"
      auteur_affinity: "matched auteurs"

    step_context_inheritance:
      all_apps_receive: "persona-based defaults"
      scenario_generator: "narrative structure hints"
      aesthetic_director: "auteur style weights"
```

### Sources
- MBTI-CI Research: 3SN+JP-EI-.5TF Creativity Formula
- Psychology of Creativity: MBTI Type Distribution Studies
