# Dimension Apps 거시적 기획 문서 (2026)

> **Version**: 1.1 (컨설팅 피드백 반영)
> **Last Updated**: 2026-01-17
> **Purpose**: 10개 Dimension 앱 고도화 및 실제 기능 구현을 위한 거시적 설계
> **Target Output**: 3분 애니메이션 MV, 3분 AI 숏드라마, 1분 AI 숏폼

---

## Executive Summary

이 문서는 Crebit Studio의 10개 Dimension 앱을 **2026년 최신 AI 비디오 생성 기술**과 **거장의 수학적 로직 데이터베이스**를 기반으로 고도화하기 위한 거시적 기획을 담고 있습니다.

### 핵심 철학

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CREBIT STUDIO 핵심 철학                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  "거장의 DNA를 수학적으로 분석하고,                                           │
│   사용자의 페르소나와 융합하여,                                               │
│   환각률 최소의 고품질 AI 콘텐츠를 생성한다"                                   │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  거장 DNA    │ +  │  사용자 DNA  │ =  │  창작물 DNA  │                   │
│  │ (학술 데이터)│    │  (페르소나)  │    │  (고품질)    │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 목표 콘텐츠 유형

| 유형 | 길이 | 복잡도 | 우선순위 | 예상 완성도 |
|------|------|--------|----------|-------------|
| **AI 숏폼** | 30초~1분 | 단일 씬 | P0 | 2026 Q1 |
| **AI 애니메이션 MV** | 3분 | 멀티 씬 (20-30 shots) | P1 | 2026 Q2 |
| **AI 숏드라마** | 3분 | 캐릭터 일관성 + 대화 | P2 | 2026 Q3 |
| **AI 장편 (Future)** | 10분+ | 다중 캐릭터 + 내러티브 | P3 | 2026 Q4~ |

---

## Part 1: 2026 AI 비디오 생성 도구 랜드스케이프

### 1.1 주요 플랫폼 비교 분석

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    2026 AI Video Generation Landscape                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Veo 3.1    │  │  Kling 2.6  │  │  Sora 2 Pro │  │  Runway G4  │        │
│  │  (Google)   │  │  (ByteDance)│  │  (OpenAI)   │  │  (Runway)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│        │               │               │               │                    │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    Feature Comparison Matrix                     │       │
│  ├──────────────┬──────────┬──────────┬──────────┬──────────┐      │       │
│  │ Feature      │ Veo 3.1  │ Kling 2.6│ Sora 2   │ Runway G4│      │       │
│  ├──────────────┼──────────┼──────────┼──────────┼──────────┤      │       │
│  │ Max Duration │ 8s+Scene │ 10s      │ 25s      │ 10s      │      │       │
│  │ Resolution   │ 4K       │ 1080p    │ 1080p    │ 4K       │      │       │
│  │ Audio Sync   │ Native   │ Native   │ Native   │ Separate │      │       │
│  │ Char. Consist│ 3-ref    │ I2V best │ Cameos   │ 1-ref    │      │       │
│  │ Camera Ctrl  │ Medium   │ High     │ High     │ High     │      │       │
│  │ Physics      │ Good     │ Excellent│ Excellent│ Good     │      │       │
│  │ Cost/sec     │ $0.15-40 │ $0.07-14 │ $0.20+   │ $0.05+   │      │       │
│  └──────────────┴──────────┴──────────┴──────────┴──────────┘      │       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Google Veo 3.1 심층 분석

**Sources**: [Google Developers Blog](https://developers.googleblog.com/introducing-veo-3-1-and-new-creative-capabilities-in-the-gemini-api/), [DeepMind](https://deepmind.google/models/veo/)

#### 핵심 강점
- **Ingredients to Video**: 최대 3개 레퍼런스 이미지로 캐릭터/배경 일관성 유지
- **Scene Extension**: 이전 클립 마지막 1초 기반으로 연속 생성 (1분+ 가능)
- **4K Upscaling**: State-of-the-art 업스케일링
- **Native Vertical**: 9:16 네이티브 지원 (숏폼 최적화)
- **Audio Generation**: 대화 동기화 + 네이티브 오디오

#### 권장 사용 시나리오
```python
VEO_USE_CASES = {
    "establishing_shots": {
        "description": "분위기 설정 와이드 샷",
        "duration": "5-8s",
        "reason": "시네마틱 일관성, 대기감 표현"
    },
    "atmospheric_scenes": {
        "description": "감성적 롱테이크",
        "duration": "5-8s",
        "reason": "연속 생성으로 긴 테이크 가능"
    },
    "audio_sync_scenes": {
        "description": "대화/내레이션 동기화",
        "duration": "4-8s",
        "reason": "네이티브 오디오 생성"
    },
}
```

### 1.3 Kling 2.6 심층 분석

**Sources**: [Kling AI](https://www.klingai.com/global/), [WaveSpeed Guide](https://wavespeed.ai/blog/posts/kling-2-0-complete-guide-2026/)

#### 핵심 강점
- **Image-to-Video 최강**: 정적 이미지 → 고품질 비디오 변환
- **모션 컨트롤**: 자연스러운 물리 시뮬레이션, 무게감/관성 표현
- **캐릭터 일관성**: 왜곡/변형 최소화
- **Voice Control**: 음성, 대화, 나레이션, 노래, 랩 지원
- **가격 경쟁력**: $0.07-0.14/초 (오디오 포함)

#### 권장 사용 시나리오
```python
KLING_USE_CASES = {
    "extreme_closeups": {
        "description": "얼굴, 손, 음식 클로즈업",
        "duration": "5s",
        "reason": "정적/슬로모션 샷에서 최고 품질"
    },
    "texture_detail": {
        "description": "질감이 중요한 샷",
        "duration": "5s",
        "reason": "디테일 보존력 우수"
    },
    "minimal_motion": {
        "description": "미세한 움직임 샷",
        "duration": "5-10s",
        "reason": "미니멀 모션에서 왜곡 최소"
    },
}
```

### 1.4 OpenAI Sora 2 Pro 심층 분석

**Sources**: [OpenAI Sora 2](https://openai.com/index/sora-2/), [WaveSpeed Guide](https://wavespeed.ai/blog/posts/openai-sora-2-complete-guide-2026/)

#### 핵심 강점
- **25초 스토리보드**: Pro 사용자 웹에서 25초 영상 생성
- **Physics Accuracy**: 물리 법칙 준수 (농구 리바운드 등)
- **Character Cameos**: 실제 인물/동물/캐릭터 삽입 및 재사용
- **Remix 기능**: 기존 영상 부분 수정
- **Synchronized Audio**: 자연스러운 대화 타이밍

#### 권장 사용 시나리오
```python
SORA_USE_CASES = {
    "action_sequences": {
        "description": "액션, 격투, 빠른 움직임",
        "duration": "5-15s",
        "reason": "복잡한 모션에서 시간적 일관성 최고"
    },
    "dynamic_camera": {
        "description": "다이나믹 카메라 워크",
        "duration": "5-15s",
        "reason": "복잡한 카메라 움직임 처리"
    },
    "transitions_montage": {
        "description": "전환, 몽타주 시퀀스",
        "duration": "10-25s",
        "reason": "연속적 씬 전환에 강함"
    },
}
```

### 1.5 도구 선택 휴리스틱 (Shot-Level Decision Tree)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AI Video Tool Selection Heuristic                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Shot Analysis                                                               │
│       │                                                                      │
│       ├─► Motion Level?                                                      │
│       │   ├─► Static/Slow (0-20%) ──────────► KLING                         │
│       │   ├─► Medium (20-60%) ──────────────► VEO                           │
│       │   └─► High/Action (60-100%) ────────► SORA                          │
│       │                                                                      │
│       ├─► Shot Type?                                                         │
│       │   ├─► Extreme Close-up ─────────────► KLING                         │
│       │   ├─► Close-up / Medium ────────────► KLING or VEO                  │
│       │   ├─► Wide / Establishing ──────────► VEO                           │
│       │   └─► Action / Dynamic ─────────────► SORA                          │
│       │                                                                      │
│       ├─► Audio Requirement?                                                 │
│       │   ├─► Dialogue Sync ────────────────► VEO or SORA                   │
│       │   ├─► BGM Only ─────────────────────► ANY (post-process)            │
│       │   └─► Voice/Singing ────────────────► KLING 2.6                     │
│       │                                                                      │
│       └─► Duration?                                                          │
│           ├─► <5s ──────────────────────────► KLING                         │
│           ├─► 5-10s ────────────────────────► VEO                           │
│           └─► 10-25s ───────────────────────► SORA                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: 거장의 수학적 로직 데이터베이스 설계

### 2.1 데이터베이스 계층 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Master DNA Database Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Tier 0: 거장 DNA (NotebookLM)                                              │
│  ├── 영화 거장 5인: 봉준호, 놀란, 빌뇌브, 왕가위, 타란티노                    │
│  ├── 애니메이션 거장: 미야자키 하야오, 신카이 마코토, 오시이 마모루           │
│  └── 음악 거장: 한스 짐머, 조 히사이시, 류이치 사카모토                       │
│                                                                              │
│  Tier 1: 학술 데이터 (Qdrant Hybrid)                                        │
│  ├── 미학 논문: 황금비, Rule of Thirds, 색채 이론                            │
│  ├── 음악 이론: BPM-감정 매핑, 장르 수학적 패턴                               │
│  ├── 영화 분석: Mise-en-scène, 몽타주 이론, 카메라 문법                       │
│  └── 심리학: 감정 반응, 시청자 인지, 내러티브 심리                            │
│                                                                              │
│  Tier 2: 작품 분석 데이터 (Qdrant)                                          │
│  ├── 명장면 분석: 조명, 구도, 색감, 카메라 워크                               │
│  ├── OST 분석: BPM, 키, 코드 진행, 악기 편성                                 │
│  └── 스토리 구조: 3막 구조, 기승전결, 히어로 저니                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 영상 미학 수학적 로직 데이터 스키마

**Sources**: [No Film School](https://nofilmschool.com/2013/12/mathematical-breakdown-cinematography-there-will-be-blood), [Wolfcrow](https://wolfcrow.com/the-three-important-composition-and-framing-conventions-in-cinematography/)

```yaml
# RAG Collection: dimension_aesthetic_master
aesthetic_master_schema:
  composition_rules:
    golden_ratio:
      value: 1.618
      application: "주요 피사체 배치, 프레임 분할"
      use_cases: ["face_placement", "horizon_line", "leading_lines"]
      scientific_evidence: "limited (2024 연구: 17%만 인식)"

    rule_of_thirds:
      grid: "3x3"
      power_points: ["top_left", "top_right", "bottom_left", "bottom_right"]
      origin: "John Thomas Smith (18세기)"
      adoption_rate: "~80% of professional cinematographers"

    center_framing:
      use_cases: ["symmetry", "confrontation", "power_dynamic"]
      auteurs: ["Wes Anderson", "Stanley Kubrick", "Bong Joon-ho"]

  lighting_patterns:
    three_point:
      components: ["key", "fill", "back"]
      ratio_key_fill: "2:1 to 8:1"
      mood_mapping:
        "1:1": "flat, documentary"
        "2:1": "natural, subtle"
        "4:1": "dramatic, film noir"
        "8:1": "extreme contrast, horror"

    rembrandt:
      description: "Triangle of light on shadow side of face"
      mood: "intimate, artistic, classical"

    split_lighting:
      description: "Half face lit, half in shadow"
      mood: "duality, conflict, mystery"

  color_theory:
    temperature:
      warm: { kelvin: "2700-4000K", mood: "intimate, nostalgic, passion" }
      neutral: { kelvin: "4000-5500K", mood: "natural, documentary" }
      cool: { kelvin: "5500-8000K", mood: "isolation, technology, sadness" }

    color_harmony:
      complementary: "대비, 긴장감"
      analogous: "조화, 안정감"
      triadic: "활기, 균형"

    auteur_palettes:
      bong_joon_ho: ["muted_greens", "browns", "strategic_red_accents"]
      wong_kar_wai: ["neon_blues", "saturated_reds", "greens"]
      villeneuve: ["desaturated", "monochromatic", "amber_teal"]
```

### 2.3 음악 수학적 로직 데이터 스키마

**Sources**: [Nature Scientific Reports 2025](https://www.nature.com/articles/s41598-025-92679-1), [PMC Research](https://pmc.ncbi.nlm.nih.gov/articles/PMC4971092/)

```yaml
# RAG Collection: dimension_sound_master
sound_master_schema:
  tempo_emotion_mapping:
    research_basis: "2025 EEG Study (Scientific Reports)"

    classifications:
      largo: { bpm: "40-60", emotion: "grave, solemn, profound sadness" }
      adagio: { bpm: "66-76", emotion: "slow, contemplative, melancholy" }
      andante: { bpm: "76-108", emotion: "walking pace, natural, conversational" }
      moderato: { bpm: "108-120", emotion: "moderate, balanced, stable" }
      allegro: { bpm: "120-168", emotion: "fast, joyful, energetic" }
      presto: { bpm: "168-200", emotion: "very fast, urgent, intense" }
      prestissimo: { bpm: "200+", emotion: "extremely fast, frantic, chaos" }

    physiological_connection:
      human_heartbeat: "60-100 bpm"
      optimal_processing: "~75 bpm (자율 신경 공명)"

    emotional_shift_percentages:
      "90→120 bpm":
        happiness: "+14.3%"
        sadness: "-37.7%"
        tension: "+15.9%"
        amusement: "+16.0%"
        surprise: "+11.9%"

  mode_emotion:
    major: { valence: "positive", arousal: "variable", associations: ["happy", "triumphant", "hopeful"] }
    minor: { valence: "negative", arousal: "variable", associations: ["sad", "mysterious", "tense"] }
    dorian: { valence: "ambiguous", associations: ["jazzy", "contemplative", "bittersweet"] }
    phrygian: { valence: "dark", associations: ["exotic", "flamenco", "tension"] }

  visual_bpm_sync:
    description: "씬-음악 BPM 동기화 가이드"
    rules:
      high_bpm_120plus:
        visuals: "빠른 컷, 액션, 역동적 움직임"
        lyrics: "짧고 펀치있는 가사"
        cut_frequency: "1-2초 당 1컷"

      mid_bpm_80_110:
        visuals: "대화, 감정 씬, 걷기"
        lyrics: "흐르는 듯한 verse"
        cut_frequency: "3-5초 당 1컷"

      low_bpm_under_80:
        visuals: "명상, 상실, 긴장"
        lyrics: "sparse, weighted lines"
        cut_frequency: "5-10초 당 1컷"

  genre_formulas:
    jpop_anime_opening:
      structure: "Soft Intro → Driving Verse → Build-up Pre-Chorus → Explosive Chorus → Emotional Bridge → Key-up Final Chorus"
      vibe: ["youth burning forward", "believing in the future", "running toward a goal"]
      bpm_range: "130-180"
      key: "Major (G, D, A common)"

    kpop:
      structure: "Hook Intro → Verse → Pre-Chorus → Drop Chorus → Post-Chorus → Bridge → Final Chorus"
      characteristics: ["catchy hooks", "dance break", "rap verse"]
      bpm_range: "100-140"

    cinematic_score:
      structure: "Theme Statement → Development → Tension Build → Climax → Resolution"
      orchestration: ["strings base", "brass for power", "woodwinds for color", "percussion for rhythm"]
      dynamics: "pp to fff range"
```

### 2.4 거장 DNA 상세 스키마

```yaml
# RAG Collection: dimension_auteur_dna
auteur_dna_schema:
  bong_joon_ho:
    signature_elements:
      visual_style:
        - "수직성(Verticality)으로 사회 계층 표현"
        - "대칭적 정면 샷으로 긴장감 증폭"
        - "롱테이크로 캐릭터 감정 포착"
        - "Muted 색감 + 전략적 빨강 악센트"

      thematic_concerns:
        - "계급 갈등과 사회 불평등"
        - "장르 혼합 (스릴러+코미디+드라마)"
        - "갑작스러운 톤 변화"
        - "사회적 메시지의 장르적 포장"

      camera_grammar:
        signature_shots: ["high-angle for powerlessness", "low-angle for power", "one-point perspective"]
        movement: "motivated camera movement, rarely static"
        lens_preference: "wide for environment, close for emotion"

      collaboration:
        dp: "Hong Kyung-pyo"
        composer: "Jung Jae-il"

  christopher_nolan:
    signature_elements:
      visual_style:
        - "IMAX 대형 포맷"
        - "Practical effects over CGI"
        - "Non-linear narrative structure"
        - "Blue-teal color grading"

      thematic_concerns:
        - "시간의 조작과 인식"
        - "정체성과 기억"
        - "과학적 개념의 서사화"

      technical_preferences:
        film_format: "70mm IMAX, 35mm"
        aspect_ratios: ["2.39:1 anamorphic", "1.43:1 IMAX"]
        practical_preference: "real explosions, minimal green screen"

  shinkai_makoto:
    signature_elements:
      visual_style:
        - "Hyper-realistic backgrounds"
        - "光의 표현 (lens flares, god rays)"
        - "구름과 하늘의 미학"
        - "도시 풍경의 시적 묘사"

      color_palette:
        dawn_dusk: "orange, pink, purple gradients"
        night: "deep blue, cyan accents"
        day: "bright, saturated blues"

      emotional_themes:
        - "거리와 그리움 (distance and longing)"
        - "운명적 만남"
        - "시간을 초월한 사랑"

  miyazaki_hayao:
    signature_elements:
      visual_style:
        - "Hand-drawn animation purity"
        - "Flight and movement fluidity"
        - "자연과 환경의 경외"
        - "디테일한 일상 묘사 (ma의 미학)"

      character_design:
        heroines: "strong, independent, complex"
        villains: "nuanced, often redeemable"
        creatures: "imaginative, often cute yet powerful"

      thematic_concerns:
        - "환경주의"
        - "반전 메시지"
        - "성장과 자아 발견"
        - "노동의 가치"
```

### 2.5 캐릭터 일관성 기술 데이터베이스

**Sources**: [ByteDance StoryMem](https://the-decoder.com/bytedances-storymem-gives-ai-video-models-a-memory-so-characters-stop-shapeshifting-between-scenes/), [CrePal Guide](https://crepal.ai/blog/aivideo/how-to-keep-characters-consistent-in-ai-videos-2025/)

```yaml
# RAG Collection: dimension_character_consistency
character_consistency_techniques:
  reference_image_strategy:
    minimum_images: 6
    maximum_images: 10
    image_types:
      required:
        - "neutral front-facing expression"
        - "3/4 profile view"
        - "full body standing"
      recommended:
        - "key emotional expressions (3-4)"
        - "different lighting conditions"
        - "key poses from storyboard"

    wardrobe_guidelines:
      prefer: ["simple silhouettes", "solid colors", "minimal patterns"]
      avoid: ["busy patterns", "reflective textures", "frequent changes"]
      anchors: ["distinctive accessory", "signature color", "unique hairstyle"]

  technical_approaches:
    storymem_method:
      description: "키프레임을 메모리 뱅크에 저장, RoPE 인코딩으로 과거 이벤트로 처리"
      improvement: "기본 모델 대비 28.7% 향상"

    prompt_engineering:
      structure: "immutable traits first → mutable traits → action"
      immutable: ["age range", "ethnicity", "hair color/length", "body type"]
      mutable: ["expression", "pose", "lighting", "background"]

    lighting_consistency:
      rule: "단일 주광원 방향 유지"
      reason: "광원 변경 시 identity wobble 발생"

  platform_specific:
    veo_ingredients:
      max_refs: 3
      features: ["identity preservation", "background reuse", "object continuity"]

    runway_gen4:
      max_refs: 1
      features: ["cross-scene consistency", "lighting adaptation"]

    ltx_studio:
      features: ["storyboard-wide persistence", "outfit modification", "automatic shadow adjustment"]
```

---

## Part 3: 10개 Dimension 앱 상세 기획

### 앱 개요 매트릭스

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      10 Dimension Apps Overview Matrix                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────┬────────────────┬──────────┬───────────┬───────────┬──────────┐  │
│  │ ID    │ 앱 이름         │ Dimension│ 단계      │ RAG 필요  │ 우선순위 │  │
│  ├───────┼────────────────┼──────────┼───────────┼───────────┼──────────┤  │
│  │ 1.1   │ 심연의 거울     │ AI       │ 0-Entry   │ 심리/MBTI │ P0       │  │
│  │ 1.2   │ 레퍼런스 해석기 │ 4D       │ 1-Analyze │ 거장 DNA  │ P0       │  │
│  │ 1.3   │ 시나리오 생성기 │ Story    │ 2-Write   │ 구조/장르 │ P0       │  │
│  │ 2.1   │ 사운드 크래프터 │ Sound    │ 3-Audio   │ 음악이론  │ P1       │  │
│  │ 2.2   │ 스토리보드 스케치│ 2D       │ 3-Visual  │ 구도/연출 │ P1       │  │
│  │ 2.3   │ 프롬프트 연금술 │ 1D       │ 3-Prompt  │ 프롬프트DB│ P0       │  │
│  │ 3.1   │ 비주얼 리얼라이저│ 3D       │ 4-Image   │ 스타일DB  │ P1       │  │
│  │ 3.2   │ 비디오 메이커   │ VEO      │ 5-Video   │ 모션/도구 │ P0       │  │
│  │ 4.1   │ 퀄리티 디렉터   │ QC       │ 6-Review  │ QC기준    │ P1       │  │
│  │ 5.1   │ 미학 디렉터     │ AD       │ Cross-cut │ 미학논문  │ P0       │  │
│  └───────┴────────────────┴──────────┴───────────┴───────────┴──────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### App 1.1: 심연의 거울 (Abyss Mirror)

#### 개요
사용자의 창작 DNA를 분석하여 개인화된 페르소나 프로필을 생성합니다.

#### 기능 상세

```yaml
app_1_1_abyss_mirror:
  purpose: "사용자 창작 DNA 분석 및 페르소나 구축"

  stages:
    intro:
      description: "초기 인사 및 분석 방향 설정"
      inputs: ["subject", "analysis_focus"]

    deep_dive:
      description: "심층 대화를 통한 취향 발굴"
      techniques: ["projective_questions", "preference_mapping", "conflict_exploration"]

    synthesis:
      description: "수집된 데이터 종합 분석"
      outputs: ["personality_profile", "creative_tendencies", "auteur_affinity"]

    dna_generation:
      description: "최종 창작 DNA 문서 생성"
      format: "structured_json + narrative_summary"

  rag_requirements:
    collections:
      - name: "dimension_ai_contexts"
        content: ["MBTI 유형별 창작 성향", "애착 유형", "사주 오행 창작 해석"]
      - name: "dimension_psych_core"
        content: ["심리학 기반 창작자 유형", "동기 이론", "창작 블록 패턴"]

  data_curation_needed:
    priority: "P0"
    datasets:
      - id: "mbti_creative_profiles"
        description: "16 MBTI 유형별 창작 성향, 강점, 약점, 추천 장르"
        source: "학술 논문 + 창작자 인터뷰 분석"
        size: "~50 documents"

      - id: "auteur_personality_mapping"
        description: "거장 감독/작곡가의 성격 유형 분석"
        source: "전기, 인터뷰, 작품 분석"
        size: "~30 documents"

      - id: "creative_block_patterns"
        description: "창작 블록 유형 및 해결 전략"
        source: "심리학 연구, 창작론"
        size: "~20 documents"

  output_schema:
    persona_dna:
      core_identity:
        mbti_type: "string"
        dominant_traits: "list[string]"
        creative_archetype: "string"  # e.g., "The Perfectionist Storyteller"

      aesthetic_preferences:
        visual_taste: "object"  # color, composition, mood
        narrative_preference: "object"  # genre, structure, themes
        audio_preference: "object"  # genre, tempo, mood

      auteur_affinity:
        primary_auteur: "string"
        affinity_score: "float"
        reasoning: "string"
        secondary_matches: "list[object]"

      creative_dna_prompt:
        description: "다른 앱에서 사용할 DNA 프롬프트 문자열"
        example: "perfectionist storyteller with visual minimalism preference, drawn to psychological depth and ambiguous endings, influenced by Bong Joon-ho's social commentary and Wong Kar-wai's emotional color palette"
```

---

### App 1.2: 레퍼런스 해석기 (Reference Decoder)

#### 개요
영상 레퍼런스를 전문가 수준으로 분석하여 조명, 색감, 구도, 카메라 워크, 연출 기법을 추출합니다.

#### 기능 상세

```yaml
app_1_2_reference_decoder:
  purpose: "영상 레퍼런스 전문 분석"

  input_types:
    - "video_url (YouTube, Vimeo)"
    - "image_files"
    - "video_files"
    - "text_description (분석하고 싶은 씬 설명)"

  analysis_dimensions:
    composition:
      elements: ["framing", "rule_of_thirds", "golden_ratio", "symmetry", "leading_lines"]
      output: "구도 분석 + 재현 가이드"

    lighting:
      elements: ["key_light_direction", "fill_ratio", "color_temperature", "quality", "pattern"]
      output: "조명 셋업 가이드 + 무드 해석"

    color_grading:
      elements: ["dominant_colors", "color_harmony", "saturation", "contrast", "lut_suggestion"]
      output: "색감 분석 + LUT 추천"

    camera_work:
      elements: ["shot_type", "lens_focal_length", "movement", "speed", "motivation"]
      output: "카메라 언어 해석 + 재현 프롬프트"

    mise_en_scene:
      elements: ["set_design", "props", "costume", "actor_blocking", "depth_staging"]
      output: "씬 구성 분석"

    sound_design:
      elements: ["diegetic_sound", "score_mood", "silence_use", "sound_symbolism"]
      output: "사운드 레이어 분석"

  rag_requirements:
    collections:
      - name: "dimension_4d_contexts"
        content: ["영화 기법 용어집", "카메라 문법", "조명 패턴"]
      - name: "dimension_auteur_dna"
        content: ["거장별 시그니처 기법", "작품별 분석"]

  data_curation_needed:
    priority: "P0"
    datasets:
      - id: "cinematography_techniques"
        description: "시네마토그래피 기법 사전 (500+ 기법)"
        source: "Cinematography textbooks, ASC publications"
        size: "~500 documents"

      - id: "famous_scene_analysis"
        description: "명장면 분석 DB (구도, 조명, 색감 분해)"
        source: "Every Frame a Painting, StudioBinder, academic papers"
        size: "~200 documents"

      - id: "camera_movement_semantics"
        description: "카메라 움직임의 의미론"
        content: |
          - Push-In: 깨달음, 강렬한 감정
          - Pull-Out: 씬 종료, 고립감
          - Dolly Zoom: 충격, 현실 왜곡
          - Tracking: 동행, 따라감
        size: "~30 documents"

  output_schema:
    reference_analysis:
      composition_guide:
        grid_overlay: "string (thirds/golden/center)"
        focal_points: "list[{x, y, element}]"
        recreate_prompt: "string"

      lighting_guide:
        setup_description: "string"
        key_light: "{direction, intensity, color_temp}"
        fill_ratio: "string"
        mood_keywords: "list[string]"

      color_guide:
        dominant_palette: "list[hex_colors]"
        mood: "string"
        lut_suggestion: "string"
        ai_prompt_keywords: "list[string]"

      camera_guide:
        shot_type: "string"
        lens_equivalent: "string (e.g., 35mm)"
        movement: "string"
        prompt_for_ai: "string"

      auteur_match:
        closest_auteur: "string"
        similarity_aspects: "list[string]"
        differentiators: "list[string]"
```

---

### App 1.3: 시나리오 생성기 (Scenario Generator)

#### 개요
페르소나 DNA와 레퍼런스 분석을 결합하여 타겟 길이에 맞는 시나리오를 생성합니다.

#### 기능 상세

```yaml
app_1_3_scenario_generator:
  purpose: "DNA + 스타일 융합 시나리오 생성"

  input_requirements:
    required:
      - concept: "콘텐츠 컨셉/주제"
      - duration: "목표 길이 (30s, 1min, 3min)"

    optional:
      - persona_dna: "App 1.1 결과물"
      - reference_analysis: "App 1.2 결과물"
      - genre: "장르 선택"
      - structure: "구조 선택"

  narrative_structures:
    short_form_30s:
      structure: "Hook → Escalation → Payoff"
      shot_count: 3-5

    short_form_1min:
      structure: "Setup → Conflict → Resolution"
      shot_count: 8-12

    mv_3min:
      structure: "Intro → Verse → Chorus → Bridge → Climax → Outro"
      shot_count: 20-30

    drama_3min:
      structure: "Hook → Setup → Rising → Climax → Resolution"
      shot_count: 15-25

  rag_requirements:
    collections:
      - name: "dimension_story_structures"
        content: ["3막 구조", "히어로 저니", "기승전결", "숏폼 구조"]
      - name: "dimension_genre_conventions"
        content: ["장르별 관습", "서브장르 혼합", "트로프 DB"]

  data_curation_needed:
    priority: "P0"
    datasets:
      - id: "story_structures_db"
        description: "내러티브 구조 패턴 DB"
        content:
          - "3막 구조 변형들"
          - "숏폼 특화 구조 (Hook-Escalate-Payoff)"
          - "MV 구조 (verse-chorus mapping)"
          - "미니 드라마 구조"
        size: "~50 documents"

      - id: "genre_conventions"
        description: "장르별 관습 및 기대 요소"
        genres: ["drama", "thriller", "comedy", "horror", "romance", "action", "fantasy", "sci-fi"]
        per_genre: ["character_archetypes", "plot_beats", "visual_conventions", "sound_conventions"]
        size: "~80 documents"

      - id: "viral_shortform_analysis"
        description: "바이럴 숏폼 구조 분석"
        source: "TikTok/Reels/Shorts 바이럴 콘텐츠 분석"
        elements: ["hook_techniques", "retention_patterns", "cta_methods"]
        size: "~100 documents"

  output_schema:
    scenario:
      metadata:
        title: "string"
        logline: "string (1-2 sentences)"
        genre: "string"
        duration: "int (seconds)"
        mood: "string"

      synopsis: "string (200-500 chars)"

      characters:
        - name: "string"
          role: "string"
          arc: "string"
          visual_dna: "string (for character consistency)"

      scenes:
        - scene_number: "int"
          duration: "int (seconds)"
          location: "string"
          action: "string"
          dialogue: "string (optional)"
          visual_notes: "string"
          audio_notes: "string"

      shot_list_ready: "boolean"
```

---

### App 2.1: 사운드 크래프터 (Sound Crafter)

#### 개요
시나리오/스토리보드에 맞는 BGM, 효과음, 보이스 프롬프트를 생성합니다.

#### 기능 상세

```yaml
app_2_1_sound_crafter:
  purpose: "AI 음악/사운드 프롬프트 생성"

  target_platforms:
    bgm_generation:
      - name: "Suno"
        features: ["full song", "instrumental", "vocal"]
        prompt_style: "natural language + metatags"

      - name: "Udio"
        features: ["instrumental focus", "genre accuracy"]
        prompt_style: "technical + style keywords"

    voice_generation:
      - name: "ElevenLabs"
        features: ["narration", "character voices", "multilingual"]

      - name: "Kling 2.6 Audio"
        features: ["sync with video", "dialogue", "singing"]

  sound_types:
    bgm:
      output: "Full music prompt for AI generation"
      includes: ["genre", "tempo", "mood", "instruments", "structure"]

    sfx:
      output: "Sound effect descriptions for sync"
      includes: ["timing", "type", "intensity", "layer"]

    narration:
      output: "Voice-over script + delivery notes"
      includes: ["text", "emotion", "pacing", "voice_characteristics"]

    lyrics:
      output: "Full lyrics with metatags"
      includes: ["verses", "chorus", "bridge", "performance_notes"]

  rag_requirements:
    collections:
      - name: "dimension_sound_master"
        content: ["BPM-감정 매핑", "장르 수학적 패턴", "Visual BPM Sync"]
      - name: "dimension_music_theory"
        content: ["코드 진행", "악기 편성", "믹싱 가이드"]

  data_curation_needed:
    priority: "P1"
    datasets:
      - id: "bpm_emotion_database"
        description: "BPM별 감정 반응 연구 데이터"
        source: "2025 Scientific Reports EEG Study + 추가 연구"
        size: "~30 documents"

      - id: "genre_formulas"
        description: "장르별 음악 공식"
        genres: ["jpop_anime", "kpop", "cinematic_score", "lo-fi", "edm", "rock", "ballad"]
        per_genre: ["structure", "bpm_range", "key_preferences", "instrument_palette", "reference_songs"]
        size: "~70 documents"

      - id: "suno_udio_prompt_db"
        description: "Suno/Udio 프롬프트 예시 및 결과 분석"
        content: ["successful_prompts", "failure_patterns", "metatag_usage"]
        size: "~100 documents"

      - id: "famous_ost_analysis"
        description: "명곡 OST 분석 (영화/애니메이션)"
        content: ["bpm", "key", "chord_progression", "instrumentation", "scene_sync_analysis"]
        size: "~50 documents"

  output_schema:
    sound_package:
      bgm_prompts:
        suno_prompt: "string (with metatags)"
        udio_prompt: "string"
        style_keywords: "list[string]"
        bpm: "int"
        key: "string"
        duration: "int (seconds)"

      sfx_cues:
        - timecode: "string (MM:SS)"
          description: "string"
          intensity: "1-10"
          layer: "foreground/background"

      narration_scripts:
        - section: "string"
          text: "string"
          delivery: "string"
          voice_notes: "string"

      lyrics:
        full_lyrics: "string (with metatags)"
        suno_format: "string"
        udio_format: "string"
        topic_analysis: "string"
```

---

### App 2.2: 스토리보드 스케치 (Storyboard Sketcher)

#### 개요
시나리오를 시각적 스토리보드 컷으로 변환합니다.

#### 기능 상세

```yaml
app_2_2_storyboard_sketcher:
  purpose: "시나리오 → 시각적 스토리보드 변환"

  output_format:
    visual_storyboard:
      panels_per_row: 3
      panel_content:
        - sketch_prompt: "AI 이미지 생성용 프롬프트"
        - action_description: "액션 설명"
        - dialogue: "대사 (있는 경우)"
        - camera_notes: "카메라 앵글/움직임"
        - duration: "예상 길이"

  sketch_styles:
    rough_sketch: "빠른 구도 확인용 (흑백 선화)"
    color_rough: "색감 방향 포함 러프"
    detailed_concept: "상세 컨셉 아트 스타일"

  rag_requirements:
    collections:
      - name: "dimension_2d_contexts"
        content: ["스토리보드 레이아웃", "카메라 앵글", "액션 라인"]
      - name: "dimension_composition"
        content: ["구도 법칙", "시선 유도", "화면 분할"]

  data_curation_needed:
    priority: "P1"
    datasets:
      - id: "storyboard_conventions"
        description: "스토리보드 표기법 및 관습"
        content: ["arrow_meanings", "panel_layouts", "annotation_standards"]
        size: "~20 documents"

      - id: "shot_transition_language"
        description: "샷 전환 시각 언어"
        transitions: ["cut", "dissolve", "wipe", "fade", "match_cut", "j_cut", "l_cut"]
        size: "~15 documents"

  output_schema:
    storyboard:
      panels:
        - panel_number: "int"
          scene_reference: "int"
          shot_type: "string"
          composition: "string"
          action: "string"
          dialogue: "string"
          camera_movement: "string"
          duration: "float (seconds)"
          ai_prompt: "string"
          notes: "string"
```

---

### App 2.3: 프롬프트 연금술 (Prompt Alchemy)

#### 개요
일반 언어를 AI가 이해하는 전문 프롬프트로 변환합니다.

#### 기능 상세

```yaml
app_2_3_prompt_alchemy:
  purpose: "자연어 → AI 전문 프롬프트 변환"

  target_platforms:
    image:
      - "Midjourney"
      - "DALL-E 3"
      - "Stable Diffusion"
      - "Imagen 3"

    video:
      - "Veo 3.1"
      - "Kling 2.6"
      - "Sora 2"
      - "Runway Gen-4"

    audio:
      - "Suno"
      - "Udio"
      - "ElevenLabs"

  prompt_components:
    subject: "주요 피사체/캐릭터"
    action: "동작/상태"
    environment: "배경/환경"
    lighting: "조명"
    color: "색감"
    camera: "카메라 설정"
    style: "스타일/레퍼런스"
    technical: "기술적 설정 (해상도, 비율 등)"
    negative: "제외할 요소"

  rag_requirements:
    collections:
      - name: "dimension_1d_contexts"
        content: ["플랫폼별 프롬프트 패턴", "키워드 효과", "파라미터 가이드"]

  data_curation_needed:
    priority: "P0"
    datasets:
      - id: "platform_prompt_guides"
        description: "플랫폼별 프롬프트 가이드"
        platforms: ["midjourney", "dalle", "sd", "veo", "kling", "sora", "suno", "udio"]
        per_platform: ["syntax", "keywords", "parameters", "examples", "anti_patterns"]
        size: "~80 documents"

      - id: "style_keyword_database"
        description: "스타일 키워드 효과 DB"
        categories: ["art_movements", "artists", "cinematographers", "genres", "techniques"]
        per_keyword: ["effect_description", "platform_compatibility", "combination_tips"]
        size: "~500 documents"

      - id: "prompt_engineering_research"
        description: "프롬프트 엔지니어링 연구"
        content: ["word_order_effects", "emphasis_techniques", "negative_prompt_strategies"]
        size: "~30 documents"

  output_schema:
    prompt_package:
      original_input: "string"

      image_prompts:
        midjourney: "string"
        dalle: "string"
        sd: "string"

      video_prompts:
        veo: "string"
        kling: "string"
        sora: "string"

      variations:
        - style_variant: "string"
          prompt: "string"

      tips: "list[string]"
```

---

### App 3.1: 비주얼 리얼라이저 (Visual Realizer)

#### 개요
키프레임/컨셉 아트를 고품질로 생성합니다.

#### 기능 상세

```yaml
app_3_1_visual_realizer:
  purpose: "고품질 키프레임/컨셉 아트 생성"

  generation_modes:
    keyframe: "비디오 생성용 키프레임"
    concept_art: "스타일 확정용 컨셉 아트"
    character_sheet: "캐릭터 일관성용 시트"
    environment_art: "배경/환경 설정"

  style_presets:
    anime:
      variants: ["ghibli", "shinkai", "trigger", "kyoani", "modern_anime"]
    realistic:
      variants: ["cinematic", "documentary", "portrait", "landscape"]
    stylized:
      variants: ["graphic", "illustration", "painterly", "minimalist"]

  character_consistency:
    dna_generation: "캐릭터 Visual DNA 프롬프트 생성"
    reference_pack: "6-10장 레퍼런스 이미지 생성"
    style_lock: "스타일 일관성 유지"

  rag_requirements:
    collections:
      - name: "dimension_3d_contexts"
        content: ["스타일별 프롬프트", "품질 키워드", "캐릭터 일관성 기법"]

  data_curation_needed:
    priority: "P1"
    datasets:
      - id: "anime_style_database"
        description: "애니메이션 스타일 분류 DB"
        studios: ["ghibli", "trigger", "kyoani", "bones", "mappa", "wit", "ufotable"]
        per_studio: ["color_palette", "linework", "shading", "character_design", "background_style"]
        size: "~70 documents"

      - id: "character_dna_templates"
        description: "캐릭터 DNA 템플릿"
        archetypes: ["protagonist", "antagonist", "mentor", "sidekick", "love_interest"]
        per_archetype: ["visual_traits", "expression_range", "pose_vocabulary"]
        size: "~50 documents"

  output_schema:
    visual_package:
      keyframes:
        - frame_id: "string"
          image_url: "string"
          prompt_used: "string"

      character_dna:
        name: "string"
        visual_dna_prompt: "string"
        style_prompt: "string"
        full_prompt: "string"
        reference_images: "list[string]"

      style_guide:
        color_palette: "list[hex]"
        lighting_direction: "string"
        key_visual_elements: "list[string]"
```

---

### App 3.2: 비디오 메이커 (Video Maker)

#### 개요
키프레임/프롬프트를 AI 비디오로 변환합니다.

#### 기능 상세

```yaml
app_3_2_video_maker:
  purpose: "AI 비디오 생성 (Veo/Kling/Sora 통합)"

  generation_modes:
    text_to_video:
      description: "텍스트 프롬프트 → 비디오"
      platforms: ["veo", "sora", "kling"]

    image_to_video:
      description: "키프레임 → 비디오"
      platforms: ["kling", "veo", "runway"]
      best_for: "캐릭터 일관성 유지"

    video_to_video:
      description: "기존 비디오 스타일 변환"
      platforms: ["runway", "kling"]

  tool_selection_heuristic:
    implemented: true
    logic: |
      1. Motion Level 분석
      2. Shot Type 분석
      3. Audio 요구사항 확인
      4. Duration 확인
      5. 최적 도구 추천

  scene_extension:
    description: "Scene Extension으로 긴 시퀀스 생성"
    method: "이전 클립 마지막 1초 기반 연속 생성"
    max_duration: "60s+ (연속 생성)"

  rag_requirements:
    collections:
      - name: "dimension_veo_contexts"
        content: ["Veo 프롬프트 패턴", "도구 선택 가이드", "모션 분석"]

  data_curation_needed:
    priority: "P0"
    datasets:
      - id: "ai_video_tool_comparison"
        description: "AI 비디오 도구 심층 비교"
        tools: ["veo", "kling", "sora", "runway", "pika", "haiper"]
        per_tool: ["strengths", "weaknesses", "best_use_cases", "pricing", "prompt_tips"]
        size: "~60 documents"

      - id: "shot_tool_mapping"
        description: "샷 유형별 최적 도구 매핑"
        shot_types: ["closeup", "medium", "wide", "action", "dialogue", "establishing"]
        per_shot: ["recommended_tool", "reason", "alternative", "prompt_template"]
        size: "~30 documents"

      - id: "motion_analysis_guide"
        description: "모션 분석 가이드"
        motion_levels: ["static", "subtle", "moderate", "dynamic", "action"]
        per_level: ["characteristics", "recommended_tools", "prompt_keywords"]
        size: "~20 documents"

  output_schema:
    video_package:
      shots:
        - shot_id: "string"
          video_url: "string"
          duration: "float"
          tool_used: "string"
          prompt_used: "string"

      timeline:
        total_duration: "float"
        shot_sequence: "list[shot_id]"

      export_ready:
        assembled_video: "string (url)"
        audio_synced: "boolean"
```

---

### App 4.1: 퀄리티 디렉터 (Quality Director)

#### 개요
생성된 콘텐츠의 품질을 검수하고 개선점을 제안합니다.

#### 기능 상세

```yaml
app_4_1_quality_director:
  purpose: "AI 콘텐츠 품질 검수 및 개선 제안"

  quality_dimensions:
    visual_consistency:
      checks:
        - "캐릭터 일관성 (얼굴, 의상, 체형)"
        - "스타일 일관성 (색감, 조명)"
        - "배경 일관성"
      scoring: "1-10"

    motion_quality:
      checks:
        - "움직임 자연스러움"
        - "물리 법칙 준수"
        - "왜곡/변형 없음"
      scoring: "1-10"

    narrative_coherence:
      checks:
        - "스토리 흐름"
        - "장면 전환"
        - "페이싱"
      scoring: "1-10"

    audio_sync:
      checks:
        - "립싱크 정확도"
        - "BGM 동기화"
        - "효과음 타이밍"
      scoring: "1-10"

    technical_quality:
      checks:
        - "해상도 적절성"
        - "노이즈 수준"
        - "압축 아티팩트"
      scoring: "1-10"

  rag_requirements:
    collections:
      - name: "dimension_qc_contexts"
        content: ["품질 기준", "일반적 문제점", "해결 방법"]

  data_curation_needed:
    priority: "P1"
    datasets:
      - id: "ai_video_quality_standards"
        description: "AI 비디오 품질 기준"
        content: ["industry_standards", "common_artifacts", "quality_thresholds"]
        size: "~30 documents"

      - id: "common_ai_artifacts"
        description: "AI 생성 콘텐츠 일반적 문제점"
        categories: ["character_morphing", "hand_issues", "physics_breaks", "temporal_inconsistency"]
        per_category: ["description", "detection_method", "fix_suggestions"]
        size: "~50 documents"

  output_schema:
    quality_report:
      overall_score: "float (1-10)"

      dimension_scores:
        visual_consistency: "float"
        motion_quality: "float"
        narrative_coherence: "float"
        audio_sync: "float"
        technical_quality: "float"

      issues:
        - severity: "critical/major/minor"
          category: "string"
          timestamp: "string (if applicable)"
          description: "string"
          fix_suggestion: "string"

      recommendations:
        - priority: "1-5"
          action: "string"
          expected_improvement: "string"
```

---

### App 5.1: 미학 디렉터 (Aesthetic Director)

#### 개요
거장의 미학을 프로젝트 전체에 적용합니다.

#### 기능 상세

```yaml
app_5_1_aesthetic_director:
  purpose: "거장 미학 프로젝트 전체 적용"

  application_scope:
    project_wide: "전체 프로젝트 스타일 가이드"
    scene_specific: "씬별 미학 적용"
    cross_reference: "다른 앱 결과물 미학 정렬"

  aesthetic_domains:
    visual:
      elements: ["color_palette", "composition", "lighting", "camera_language"]

    narrative:
      elements: ["thematic_concerns", "genre_conventions", "tonal_consistency"]

    audio:
      elements: ["score_style", "sound_design_philosophy", "silence_usage"]

  auteur_matching:
    description: "사용자 컨셉 + 페르소나에 맞는 거장 매칭"
    output: "추천 거장 + 적용 가이드"

  rag_requirements:
    collections:
      - name: "dimension_ad_contexts"
        content: ["미학 이론", "거장 스타일", "적용 가이드"]
      - name: "dimension_auteur_dna"
        content: ["거장별 상세 DNA", "작품 분석"]

  data_curation_needed:
    priority: "P0"
    datasets:
      - id: "aesthetic_theory_database"
        description: "미학 이론 학술 DB"
        theories: ["golden_ratio", "color_theory", "gestalt_principles", "film_grammar"]
        per_theory: ["academic_source", "practical_application", "examples"]
        size: "~50 documents"

      - id: "auteur_style_guides"
        description: "거장별 스타일 가이드 (실무 적용)"
        auteurs: ["bong", "nolan", "villeneuve", "wongkarwai", "tarantino", "miyazaki", "shinkai"]
        per_auteur: ["color_lut", "composition_rules", "camera_preferences", "audio_approach"]
        size: "~70 documents"

      - id: "cross_medium_aesthetics"
        description: "매체별 미학 적용 가이드"
        media: ["short_film", "mv", "animation", "documentary"]
        size: "~20 documents"

  output_schema:
    aesthetic_package:
      style_guide:
        primary_auteur: "string"
        secondary_influences: "list[string]"

        visual_direction:
          color_palette: "list[hex]"
          lut_suggestion: "string"
          composition_rules: "list[string]"
          lighting_approach: "string"

        narrative_direction:
          thematic_focus: "list[string]"
          tonal_guidelines: "string"
          genre_conventions: "list[string]"

        audio_direction:
          score_style: "string"
          sound_design_notes: "string"
          reference_composers: "list[string]"

      per_scene_guidelines:
        - scene_id: "int"
          specific_notes: "string"
          auteur_technique_to_apply: "string"
```

---

## Part 4: 통합 프로덕션 워크플로우

### 4.1 3분 애니메이션 MV 워크플로우

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    3-Minute Animation MV Production Workflow                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 0: Foundation (심연의 거울 + 미학 디렉터)                             │
│  ├── 사용자 페르소나 분석                                                    │
│  ├── 거장 매칭                                                               │
│  └── 프로젝트 스타일 가이드 생성                                              │
│                                                                              │
│  Phase 1: Concept (레퍼런스 해석기 + 시나리오 생성기)                         │
│  ├── MV 컨셉 정의                                                            │
│  ├── 레퍼런스 분석 (1-3개)                                                   │
│  └── 3분 시나리오 생성 (20-30 shots)                                         │
│                                                                              │
│  Phase 2: Audio (사운드 크래프터)                                            │
│  ├── 곡 스타일 결정                                                          │
│  ├── Suno/Udio 프롬프트 생성                                                 │
│  ├── BGM 생성 (3분)                                                          │
│  └── BPM 기반 샷 타이밍 조정                                                 │
│                                                                              │
│  Phase 3: Visual Prep (스토리보드 스케치 + 프롬프트 연금술 + 비주얼 리얼라이저)│
│  ├── 스토리보드 생성                                                         │
│  ├── 캐릭터 DNA 생성                                                         │
│  ├── 캐릭터 레퍼런스 팩 생성 (6-10장)                                        │
│  └── 키프레임 생성                                                           │
│                                                                              │
│  Phase 4: Video Production (비디오 메이커)                                   │
│  ├── 샷별 도구 선택 (휴리스틱 적용)                                          │
│  ├── 샷 생성 (20-30 shots)                                                   │
│  ├── Scene Extension으로 연결                                                │
│  └── 1차 어셈블리                                                            │
│                                                                              │
│  Phase 5: Review & Polish (퀄리티 디렉터)                                    │
│  ├── 품질 검수                                                               │
│  ├── 문제 샷 재생성                                                          │
│  ├── 오디오 싱크                                                             │
│  └── 최종 익스포트                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 3분 AI 숏드라마 워크플로우

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    3-Minute AI Short Drama Production Workflow               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 0: Foundation                                                         │
│  ├── 페르소나 분석 (심연의 거울)                                              │
│  └── 거장 스타일 매칭 (미학 디렉터) - 드라마 거장 추천                         │
│                                                                              │
│  Phase 1: Script                                                             │
│  ├── 컨셉 입력                                                               │
│  ├── 시나리오 생성 (시나리오 생성기) - 대화 포함                              │
│  └── 캐릭터 설정 (2-3명)                                                     │
│                                                                              │
│  Phase 2: Character Design                                                   │
│  ├── 캐릭터 DNA 생성 (비주얼 리얼라이저)                                      │
│  ├── 캐릭터 레퍼런스 팩 (캐릭터당 6-10장)                                     │
│  └── 의상/헤어/소품 일관성 확보                                               │
│                                                                              │
│  Phase 3: Storyboard & Audio                                                 │
│  ├── 스토리보드 생성 (스토리보드 스케치)                                      │
│  ├── 대화 스크립트 정리                                                       │
│  └── 사운드 패키지 생성 (사운드 크래프터)                                     │
│                                                                              │
│  Phase 4: Video Production                                                   │
│  ├── Image-to-Video 중심 (캐릭터 일관성)                                     │
│  ├── 대화 씬: Kling 2.6 Voice Control                                        │
│  ├── 액션 씬: Sora 2                                                         │
│  └── 분위기 씬: Veo 3.1                                                      │
│                                                                              │
│  Phase 5: Post & QC                                                          │
│  ├── 품질 검수 (퀄리티 디렉터)                                                │
│  ├── 립싱크 확인                                                              │
│  ├── 음향 믹싱                                                               │
│  └── 컬러 그레이딩 확인                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 1분 숏폼 워크플로우

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    1-Minute Short-form Production Workflow                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: Quick Concept (10 min)                                            │
│  ├── 바이럴 훅 설정 (시나리오 생성기 - 숏폼 모드)                             │
│  └── 30초 구조: Hook → Escalation → Payoff                                  │
│                                                                              │
│  Phase 2: Rapid Prototyping (20 min)                                        │
│  ├── 프롬프트 생성 (프롬프트 연금술)                                          │
│  ├── 3-5샷 스토리보드                                                        │
│  └── 키프레임 생성 (비주얼 리얼라이저)                                        │
│                                                                              │
│  Phase 3: Video Gen (30 min)                                                │
│  ├── 도구 선택 (휴리스틱)                                                    │
│  ├── 3-5샷 생성                                                              │
│  └── 어셈블리                                                                │
│                                                                              │
│  Phase 4: Quick Polish (10 min)                                             │
│  ├── BGM 추가 (Suno 또는 저작권 프리)                                        │
│  ├── 텍스트 오버레이                                                         │
│  └── 플랫폼별 포맷 익스포트 (9:16)                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 5: 데이터 큐레이션 로드맵

### 5.1 우선순위별 데이터셋

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Data Curation Roadmap by Priority                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  P0 - Critical (Week 1-2)                                                   │
│  ├── platform_prompt_guides (프롬프트 연금술)                                │
│  ├── ai_video_tool_comparison (비디오 메이커)                                │
│  ├── auteur_style_guides (미학 디렉터)                                       │
│  ├── story_structures_db (시나리오 생성기)                                   │
│  └── cinematography_techniques (레퍼런스 해석기)                             │
│                                                                              │
│  P1 - Important (Week 3-4)                                                  │
│  ├── bpm_emotion_database (사운드 크래프터)                                  │
│  ├── genre_formulas (사운드 크래프터)                                        │
│  ├── anime_style_database (비주얼 리얼라이저)                                │
│  ├── ai_video_quality_standards (퀄리티 디렉터)                              │
│  └── famous_scene_analysis (레퍼런스 해석기)                                 │
│                                                                              │
│  P2 - Nice to Have (Week 5-6)                                               │
│  ├── mbti_creative_profiles (심연의 거울)                                    │
│  ├── viral_shortform_analysis (시나리오 생성기)                              │
│  ├── suno_udio_prompt_db (사운드 크래프터)                                   │
│  └── famous_ost_analysis (사운드 크래프터)                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 데이터 소스 및 수집 방법

| 데이터셋 | 소스 | 수집 방법 | 예상 크기 |
|----------|------|----------|----------|
| platform_prompt_guides | 공식 문서, 커뮤니티 | 크롤링 + 정제 | ~80 docs |
| cinematography_techniques | ASC, 교재 | 수동 큐레이션 | ~500 docs |
| auteur_style_guides | 학술 논문, 분석 영상 | 수동 큐레이션 | ~70 docs |
| bpm_emotion_database | 학술 논문 | 논문 수집 | ~30 docs |
| anime_style_database | 팬 위키, 분석 | 수동 큐레이션 | ~70 docs |

---

## Part 6: 기술 구현 가이드

### 6.1 RAG 컬렉션 구조

```python
# Qdrant Collections 설계
DIMENSION_COLLECTIONS = {
    "dimension_1d_contexts": {
        "purpose": "프롬프트 엔지니어링",
        "vector_dim": 384,
        "datasets": ["platform_prompt_guides", "style_keyword_database"]
    },
    "dimension_2d_contexts": {
        "purpose": "스토리보드/구도",
        "vector_dim": 384,
        "datasets": ["storyboard_conventions", "composition_rules"]
    },
    "dimension_3d_contexts": {
        "purpose": "이미지 생성",
        "vector_dim": 384,
        "datasets": ["anime_style_database", "character_dna_templates"]
    },
    "dimension_4d_contexts": {
        "purpose": "레퍼런스 분석",
        "vector_dim": 384,
        "datasets": ["cinematography_techniques", "famous_scene_analysis"]
    },
    "dimension_ad_contexts": {
        "purpose": "미학 디렉터",
        "vector_dim": 384,
        "datasets": ["aesthetic_theory_database", "auteur_style_guides"]
    },
    "dimension_ai_contexts": {
        "purpose": "페르소나/심리",
        "vector_dim": 384,
        "datasets": ["mbti_creative_profiles", "creative_psychology"]
    },
    "dimension_qc_contexts": {
        "purpose": "품질 검수",
        "vector_dim": 384,
        "datasets": ["ai_video_quality_standards", "common_ai_artifacts"]
    },
    "dimension_veo_contexts": {
        "purpose": "비디오 생성",
        "vector_dim": 384,
        "datasets": ["ai_video_tool_comparison", "shot_tool_mapping"]
    },
    "dimension_sound_contexts": {
        "purpose": "사운드 생성",
        "vector_dim": 384,
        "datasets": ["bpm_emotion_database", "genre_formulas", "suno_udio_prompt_db"]
    },
    "dimension_auteur_dna": {
        "purpose": "거장 DNA",
        "vector_dim": 384,
        "datasets": ["auteur_style_guides", "famous_scene_analysis"]
    },
}
```

### 6.2 앱 간 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         App Data Flow Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │ 1.1 심연의 거울 │──────────────────────────────────────┐                │
│  │ (Persona DNA)   │                                      │                │
│  └────────┬────────┘                                      │                │
│           │ persona_dna                                   │                │
│           ▼                                               ▼                │
│  ┌─────────────────┐    reference_analysis    ┌─────────────────┐         │
│  │ 1.2 레퍼런스    │◄──────────────────────────│ 5.1 미학 디렉터 │         │
│  │ 해석기          │                          │ (Style Guide)   │         │
│  └────────┬────────┘                          └────────┬────────┘         │
│           │                                            │                   │
│           │ reference_analysis                         │ style_guide      │
│           ▼                                            │                   │
│  ┌─────────────────┐                                   │                   │
│  │ 1.3 시나리오    │◄──────────────────────────────────┘                   │
│  │ 생성기          │                                                       │
│  └────────┬────────┘                                                       │
│           │ scenario                                                        │
│           ├──────────────────────────┬───────────────────┐                 │
│           ▼                          ▼                   ▼                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ 2.1 사운드      │    │ 2.2 스토리보드  │    │ 2.3 프롬프트    │        │
│  │ 크래프터        │    │ 스케치          │    │ 연금술          │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                  │
│           │ sound_package        │ storyboard           │ prompts         │
│           ▼                      ▼                      ▼                  │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    3.1 비주얼 리얼라이저                         │      │
│  │                    (Keyframes + Character DNA)                   │      │
│  └────────────────────────────────┬────────────────────────────────┘      │
│                                   │                                        │
│                                   │ keyframes + character_dna             │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    3.2 비디오 메이커                             │      │
│  │                    (AI Video Generation)                         │      │
│  └────────────────────────────────┬────────────────────────────────┘      │
│                                   │                                        │
│                                   │ video_shots                           │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    4.1 퀄리티 디렉터                             │      │
│  │                    (Quality Review)                              │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: 성공 메트릭 및 KPI

### 7.1 앱별 성공 메트릭

| 앱 | 메트릭 | 목표 |
|-----|--------|------|
| 심연의 거울 | 페르소나 정확도 (사용자 피드백) | 4.5/5.0 |
| 레퍼런스 해석기 | 분석 완성도 (요소 커버리지) | 90%+ |
| 시나리오 생성기 | 시나리오 채택률 | 70%+ |
| 사운드 크래프터 | BGM 생성 성공률 | 80%+ |
| 스토리보드 스케치 | 키프레임 채택률 | 75%+ |
| 프롬프트 연금술 | 생성 품질 만족도 | 4.0/5.0 |
| 비주얼 리얼라이저 | 캐릭터 일관성 점수 | 8.0/10 |
| 비디오 메이커 | 샷 채택률 (재생성 없이) | 60%+ |
| 퀄리티 디렉터 | 문제 감지 정확도 | 85%+ |
| 미학 디렉터 | 스타일 일관성 점수 | 8.5/10 |

### 7.2 프로덕션 메트릭

| 콘텐츠 유형 | 메트릭 | 목표 |
|-------------|--------|------|
| 1분 숏폼 | 총 제작 시간 | < 2시간 |
| 3분 MV | 총 제작 시간 | < 8시간 |
| 3분 숏드라마 | 총 제작 시간 | < 12시간 |
| 전체 | 환각률 (잘못된 정보) | < 5% |
| 전체 | 캐릭터 일관성 (씬 간) | 85%+ |

---

## Part 8: 후속 연구 주제

### 8.1 각 앱별 상세 연구 필요 항목

이 문서를 바탕으로 각 앱에 대해 다음의 개별 연구가 필요합니다:

1. **심연의 거울**: MBTI-창작 성향 학술 연구 조사
2. **레퍼런스 해석기**: 영화 분석 방법론 학술 조사
3. **시나리오 생성기**: 숏폼 내러티브 구조 연구
4. **사운드 크래프터**: Suno/Udio 프롬프트 엔지니어링 심층 조사
5. **스토리보드 스케치**: 애니메이션 스토리보드 관습 조사
6. **프롬프트 연금술**: 2026 AI 이미지/비디오 프롬프트 최신 기법
7. **비주얼 리얼라이저**: 캐릭터 일관성 최신 기술 (StoryMem 등)
8. **비디오 메이커**: Veo 4 / Sora 3 예상 기능 및 대비
9. **퀄리티 디렉터**: AI 콘텐츠 품질 평가 프레임워크
10. **미학 디렉터**: 거장별 상세 미학 분석 (5-10인)

---

## Part 9: 2026 기술 보강 (컨설팅 피드백 반영)

> **Updated**: 2026-01-17 (Web Research + MCP Context7 기반)

### 9.1 Native Audio Default 전략 (P0 보강)

#### 배경
2025년 하반기 Veo 3.1과 Kling 2.6의 **Native Audio Generation** 기능이 출시되면서,
기존 "영상 생성 후 오디오 별도 생성" 워크플로우가 근본적으로 변화했습니다.

#### 2026년 Native Audio 지원 현황

| 플랫폼 | Native Audio | 출시일 | 지원 오디오 유형 |
|--------|-------------|--------|-----------------|
| **Veo 3.1** | ✅ 네이티브 | 2025.10 | 대화, 효과음, 앰비언트, BGM |
| **Kling 2.6** | ✅ 네이티브 | 2025.12 | 대화, 노래, 랩, 효과음, 앰비언트 |
| **Sora 2 Pro** | ✅ 네이티브 | 2025.05 | 대화, 효과음 |
| **Runway Gen-4** | ❌ 별도 | - | - |
| **Suno** | 🎵 음악 전용 | - | 작곡, 보컬 (영상 미지원) |

#### Native Audio 핵심 기술 특징

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

  kling_2_6:
    strengths:
      - "Audio-Visual Coordination (리듬-시각 동기화)"
      - "Voice control: 속삭임 → 드라마틱 스크림 제어"
      - "Multilingual dialogue (한/영 지원)"
      - "Singing/Rap performance"
      - "Foley-quality sound effects"
    api_access: "Kling API, Kie.ai"
    pricing: "$0.07-0.14/sec"

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

#### App 2.1 사운드 크래프터 보강 방향

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

    tier_2_separate_bgm:
      description: "BGM만 별도 생성"
      tools:
        - "Suno (작곡 + 보컬)"
        - "Udio (인스트루멘탈)"
      use_cases:
        - "MV 메인 트랙"
        - "테마곡 필요 시"
        - "저작권 귀속 명확화 필요 시"

    tier_3_post_enhancement:
      description: "후반 보정"
      tools:
        - "ElevenLabs (내레이션 재녹음)"
        - "MM Audio v2 (효과음 보강)"
      use_cases:
        - "Native 품질 불충분 시"
        - "특정 보이스 필요 시"

  new_output_schema:
    audio_strategy:
      primary_method: "native | separate | hybrid"
      native_config:
        platform: "veo | kling"
        audio_prompt: "string (영상 프롬프트에 통합)"
      separate_config:
        bgm_prompt: "string (Suno/Udio용)"
        voice_scripts: "list[object]"
```

---

### 9.2 Prop & Background Consistency (P0 보강)

#### 배경
기존 캐릭터 일관성만 다루던 App 3.1 비주얼 리얼라이저를
**소품(Prop)과 배경(Location)** 일관성까지 확장해야 합니다.

#### 2026년 Entity Consistency 기술 현황

| 기술 | 개발사 | 지원 엔티티 | 성능 |
|------|--------|------------|------|
| **StoryMem** | ByteDance | 캐릭터, 배경 | 기본 대비 +28.7% 향상 |
| **VideoMemory** | 연구 논문 | 캐릭터, 소품, 배경 | Prop 0.58, BG 0.72 점수 |
| **IC-LoRA** | Diffusion | 스타일, 오브젝트 | 범용 LoRA 적용 |
| **Veo 3.1 Ingredients** | Google | 캐릭터, 배경, 오브젝트 | 최대 3개 레퍼런스 |

#### StoryMem 핵심 메커니즘

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

#### VideoMemory Prop/Background 평가 메트릭

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

#### App 3.1 비주얼 리얼라이저 보강 방향

```yaml
app_3_1_visual_realizer_v2:
  entity_types:
    characters:
      existing: true
      dna_fields: ["face", "body_type", "costume", "hair", "accessories"]

    props:
      new: true
      dna_fields: ["shape", "color", "texture", "size", "material"]
      examples: ["마법 지팡이", "빈티지 카메라", "특정 차량", "무기"]

    backgrounds:
      new: true
      dna_fields: ["location_type", "lighting_condition", "atmosphere", "key_elements"]
      examples: ["주인공의 방", "카페 외관", "우주선 브릿지"]

  memory_bank_integration:
    description: "StoryMem 스타일 메모리 뱅크 도입"
    implementation:
      keyframe_storage:
        per_entity: "캐릭터/소품/배경별 키프레임 저장"
        max_frames: 10
      retrieval:
        method: "시맨틱 유사도 기반 검색"
        trigger: "새 샷 생성 시 관련 엔티티 자동 주입"

  reference_pack_generation:
    character:
      count: "6-10 images"
      angles: ["front", "3/4 left", "3/4 right", "profile", "back"]
      expressions: ["neutral", "happy", "sad", "angry", "surprised"]

    prop:
      count: "3-5 images"
      angles: ["front", "45°", "detail closeup"]
      lighting: ["neutral", "dramatic"]

    background:
      count: "3-5 images"
      times: ["day", "dusk", "night"] # if applicable
      weather: ["clear", "cloudy"] # if applicable

  consistency_scoring:
    automated_check:
      method: "DINOv2 similarity scoring"
      threshold:
        character: 0.7
        prop: 0.6
        background: 0.65
      action_on_fail: "재생성 권장 플래그"
```

---

### 9.3 Multi-Modal Embedding 확장 (P1 보강)

#### 배경
현재 RAG 컬렉션이 `vector_dim: 384` 텍스트 임베딩만 사용하고 있어,
영상/오디오 자체를 벡터화하는 기능이 없습니다.

#### 2026년 Multi-Modal Embedding 현황

| 모델 | 개발사 | 지원 모달리티 | 차원 | 특징 |
|------|--------|-------------|------|------|
| **ImageBind** | Meta AI | 6개 (이미지, 텍스트, 오디오, 깊이, 열화상, IMU) | 1024-D | Cross-modal 검색 가능 |
| **VLM2Vec-V2** | 연구 논문 | 비디오, 이미지, 문서 | 다양 | 2025.07 최신 |
| **Vertex AI Multimodal** | Google | 이미지, 비디오, 텍스트 | 1408-D | 프로덕션 레디 |
| **CLIP** | OpenAI | 이미지, 텍스트 | 512/768-D | 기초 모델 |
| **SigLIP 2 / EVA-CLIP** | 연구 | 이미지, 텍스트, (오디오) | 다양 | 2025 최신 |

#### ImageBind 상세 스펙

```yaml
imagebind_specs:
  modalities: 6
  embedding_dimension: 1024

  input_requirements:
    image: "224x224 pixels"
    audio: "2-second clips @ 16kHz"
    video: "frame sequences (treated as images)"
    text: "tokenized sentences"
    depth: "depth maps"
    thermal: "thermal imagery"

  key_features:
    unified_space: "모든 모달리티가 동일한 벡터 공간"
    cross_modal_retrieval: "오디오 → 이미지, 이미지 → 오디오 검색 가능"
    open_source: "연구/상업 사용 가능"

  use_cases:
    - "레퍼런스 영상으로 유사 씬 검색"
    - "BGM으로 어울리는 영상 씬 추천"
    - "영상 분위기와 매칭되는 사운드 검색"
```

#### Vertex AI Video Embedding 스펙

```yaml
vertex_ai_multimodal:
  api: "multimodalembedding@001"
  embedding_dimension: 1408

  video_modes:
    essential:
      max_embeddings_per_min: 4
      interval: ">= 15 seconds"
    standard:
      max_embeddings_per_min: 8
      interval: "8-15 seconds"
    plus:
      max_embeddings_per_min: 15
      interval: "4-8 seconds"

  output_format:
    videoEmbeddings:
      - startOffsetSec: 0
        endOffsetSec: 10
        embedding: [float * 1408]
      - startOffsetSec: 10
        endOffsetSec: 20
        embedding: [float * 1408]
```

#### RAG 컬렉션 확장 설계

```python
# 확장된 Qdrant Collections 설계
DIMENSION_COLLECTIONS_V2 = {
    # 기존 텍스트 기반 (384-D)
    "dimension_1d_contexts": {
        "purpose": "프롬프트 엔지니어링",
        "vector_dim": 384,
        "datasets": ["platform_prompt_guides", "style_keyword_database"]
    },
    # ... (기존 컬렉션들)

    # 🆕 멀티모달 확장 컬렉션
    "dimension_video_embeddings": {
        "purpose": "영상 레퍼런스 시맨틱 검색",
        "vector_dim": 1408,  # Vertex AI Multimodal
        "model": "multimodalembedding@001",
        "fields": {
            "video_embedding": "dense_vector[1408]",
            "text_description": "string",
            "source_url": "string",
            "scene_type": "string",
            "auteur": "string",
            "timestamp_range": "object"
        },
        "use_cases": [
            "레퍼런스 영상 유사 씬 검색",
            "거장 작품 시각적 유사도 매칭",
            "스타일 일관성 검증"
        ]
    },

    "dimension_audio_embeddings": {
        "purpose": "오디오 레퍼런스 시맨틱 검색",
        "vector_dim": 1024,  # ImageBind
        "model": "imagebind-huge",
        "fields": {
            "audio_embedding": "dense_vector[1024]",
            "text_description": "string",
            "bpm": "int",
            "genre": "string",
            "mood": "string",
            "duration_sec": "float"
        },
        "use_cases": [
            "분위기 매칭 BGM 검색",
            "OST 스타일 유사도 매칭",
            "영상-오디오 cross-modal 검색"
        ]
    },

    "dimension_scene_multimodal": {
        "purpose": "씬 단위 멀티모달 통합 인덱스",
        "vector_dim": 1024,  # ImageBind unified
        "model": "imagebind-huge",
        "fields": {
            "visual_embedding": "dense_vector[1024]",
            "audio_embedding": "dense_vector[1024]",
            "text_embedding": "dense_vector[1024]",
            "scene_metadata": "object"
        },
        "use_cases": [
            "완성 씬 유사도 비교",
            "영상+오디오 통합 검색",
            "QC 자동화 (예상 vs 실제 비교)"
        ]
    }
}
```

#### 크로스-모달 검색 파이프라인

```python
# 크로스-모달 검색 예시
class CrossModalSearch:
    """멀티모달 RAG 검색 파이프라인."""

    async def search_by_audio(
        self,
        audio_file: bytes,
        target_modality: str = "video",
        top_k: int = 5
    ) -> List[SearchResult]:
        """오디오로 비디오 검색 (Audio → Video).

        Example:
            - 입력: 잔잔한 피아노 BGM
            - 출력: 분위기 맞는 영상 레퍼런스들
        """
        audio_embedding = await self.imagebind.encode_audio(audio_file)

        if target_modality == "video":
            results = await self.qdrant.search(
                collection="dimension_scene_multimodal",
                vector=audio_embedding,
                vector_name="visual_embedding",  # cross-modal
                top_k=top_k
            )
        return results

    async def search_by_video_frame(
        self,
        frame: Image,
        target_modality: str = "audio",
        top_k: int = 5
    ) -> List[SearchResult]:
        """영상 프레임으로 오디오 검색 (Video → Audio).

        Example:
            - 입력: 액션 씬 키프레임
            - 출력: 어울리는 BGM 추천
        """
        visual_embedding = await self.imagebind.encode_image(frame)

        if target_modality == "audio":
            results = await self.qdrant.search(
                collection="dimension_audio_embeddings",
                vector=visual_embedding,
                vector_name="audio_embedding",  # cross-modal
                top_k=top_k
            )
        return results
```

---

### 9.4 DAG 기반 워크플로우 확장 계획

#### 배경
현재 Vivid는 이미 **DAG 기반 워크플로우**를 구현하고 있습니다.
컨설팅 피드백에서 권고한 "Swarm Architecture"는 실제로 불필요하며,
현재 구조에서 **조건부 라우팅**과 **LLM 기반 인텐트 분석**만 추가하면 됩니다.

#### 현재 아키텍처 분석

```yaml
current_vivid_architecture:
  type: "DAG (Directed Acyclic Graph)"

  existing_capabilities:
    dag_builder:
      file: "app/workflow/dag_builder.py"
      features:
        - "can_consume/can_provide 기반 자동 의존성 추론"
        - "Kahn's Algorithm 위상 정렬"
        - "비호환 도구 검증"
        - "필수 선행 도구 자동 추가"

    executor:
      file: "app/workflow/executor.py"
      features:
        - "DAG 기반 실행"
        - "HITL 체크포인트"
        - "일시정지/재개"
        - "상태 영속화"

    types:
      file: "app/workflow/types.py"
      dataclasses:
        - "DataType (18개 타입)"
        - "ToolCapability"
        - "DAGNode"
        - "DAGEdge"
        - "ExecutableDAG"

  gap_analysis:
    missing_1: "조건부 엣지 (ConditionalEdge)"
    missing_2: "LLM 기반 라우팅 (현재 키워드 기반)"
    missing_3: "실시간 상태 스트리밍"
```

#### 확장 계획: Phase 1 - ConditionalEdge

```python
# app/workflow/types.py 확장
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Literal

@dataclass
class ConditionalEdge:
    """조건부 엣지 - 상태 기반 라우팅.

    LangGraph의 add_conditional_edges 패턴 참고.

    Example:
        >>> edge = ConditionalEdge(
        ...     from_node_id="classify_intent",
        ...     condition=lambda state: state["intent_type"],
        ...     route_map={
        ...         "reference_analysis": "reference_decoder",
        ...         "story_generation": "scenario_generator",
        ...         "image_generation": "visual_realizer",
        ...     },
        ...     default_route="prompt_alchemy"
        ... )
    """
    from_node_id: str
    condition: Callable[[Dict[str, Any]], str]
    route_map: Dict[str, str]  # condition_result → target_node_id
    default_route: str = "end"

@dataclass
class RouterNode(DAGNode):
    """LLM 기반 라우팅 노드.

    IntentAnalyzer를 LLM으로 업그레이드.

    Example:
        >>> router = RouterNode(
        ...     node_id="smart_router",
        ...     tool_id="llm_router",
        ...     routing_prompt="사용자 의도 분류: ...",
        ...     possible_routes=["reference", "story", "image", "video"],
        ... )
    """
    routing_prompt: str = ""
    possible_routes: List[str] = None
    llm_model: str = "gemini-2.5-flash"
```

#### 확장 계획: Phase 2 - LLM 기반 IntentAnalyzer

```python
# app/workflow/dag_builder.py 확장
class IntentAnalyzerV2:
    """LLM 기반 의도 분석기 (Phase 3 구현).

    기존 키워드 기반 → Gemini LLM 기반으로 업그레이드.
    """

    def __init__(
        self,
        registry: Optional[ToolCapabilityRegistry] = None,
        llm_model: str = "gemini-2.5-flash",
    ) -> None:
        self._registry = registry or get_tool_registry()
        self._llm_model = llm_model

    async def analyze(
        self,
        intent: str,
        user_context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None,
    ) -> ToolRecommendation:
        """LLM 기반 의도 분석 및 도구 추천.

        Args:
            intent: 사용자 의도 (자연어)
            user_context: 사용자 컨텍스트 (auteur_key 등)
            available_tools: 사용 가능한 도구 목록

        Returns:
            ToolRecommendation:
                - primary_tools: 메인 도구 목록
                - optional_tools: 선택적 도구
                - workflow_type: "linear" | "parallel" | "conditional"
                - confidence: 0.0-1.0
        """
        # 도구 역량 정보 수집
        tool_descriptions = self._get_tool_descriptions(available_tools)

        prompt = f"""
사용자 의도: {intent}
사용자 컨텍스트: {user_context}

사용 가능한 도구:
{tool_descriptions}

다음을 분석해주세요:
1. 어떤 도구들이 필요한가?
2. 도구 실행 순서는?
3. 병렬 실행 가능한 부분은?
4. 조건부 분기가 필요한 부분은?

JSON 형식으로 응답:
"""

        response = await self._call_llm(prompt)
        return self._parse_recommendation(response)
```

#### 확장 계획: Phase 3 - Compound Orchestration

```yaml
compound_orchestration:
  description: "쿼리 복잡도에 따른 적응형 오케스트레이션"

  routing_strategy:
    simple_query:
      condition: "단일 도구로 해결 가능"
      pattern: "Direct Tool Call"
      example: "이 이미지 분석해줘"

    moderate_query:
      condition: "2-3개 도구 순차 실행"
      pattern: "Linear DAG"
      example: "레퍼런스 분석하고 시나리오 써줘"

    complex_query:
      condition: "다중 도구 + 조건부 분기"
      pattern: "Conditional DAG"
      example: "3분 MV 만들어줘 (전체 파이프라인)"

    iterative_query:
      condition: "사용자 피드백 기반 반복"
      pattern: "HITL Loop"
      example: "마음에 들 때까지 수정"

  implementation_phases:
    phase_1:
      target: "ConditionalEdge 타입 추가"
      complexity: "낮음"
      timeline: "1주"

    phase_2:
      target: "IntentAnalyzerV2 (LLM 기반)"
      complexity: "중간"
      timeline: "2주"

    phase_3:
      target: "Compound Orchestration 로직"
      complexity: "중간"
      timeline: "2주"

    phase_4:
      target: "실시간 상태 스트리밍 통합"
      complexity: "중간-높음"
      timeline: "3주"
```

---

### 9.5 Suno AI 통합 전략

#### 배경
뮤직비디오(MV) 및 음악 콘텐츠 생성에서 **Suno AI**가 핵심 도구로 권장됩니다.

#### Suno AI 2026년 현황

```yaml
suno_ai_2026:
  capabilities:
    text_to_song: "텍스트 프롬프트 → 풀 송 생성"
    hum_to_song: "허밍/멜로디 → 편곡"
    style_transfer: "기존 곡 스타일 변환"
    stem_separation: "보컬/인스트루멘탈 분리"
    voice_covers: "AI 보이스 커버"

  strengths:
    - "가장 자연스러운 AI 보컬"
    - "다양한 장르 지원 (K-pop, J-pop, EDM, Rock 등)"
    - "가사 + 멜로디 동시 생성"
    - "Metatag 기반 정교한 제어"

  limitations:
    - "영상 생성 미지원 (음악 전용)"
    - "저작권 논란 (학습 데이터)"
    - "상업적 사용 시 라이선스 확인 필요"

  prompt_structure:
    metatags:
      - "[Intro]"
      - "[Verse]"
      - "[Pre-Chorus]"
      - "[Chorus]"
      - "[Bridge]"
      - "[Outro]"
      - "[Instrumental]"
      - "(whispered)"
      - "(shouted)"
      - "(harmonizing)"
```

#### Suno + Native Audio 하이브리드 워크플로우

```yaml
hybrid_audio_workflow:
  use_case: "3분 애니메이션 MV"

  step_1_bgm_generation:
    tool: "Suno"
    output: "3분 풀 트랙 (보컬 + 인스트루멘탈)"
    deliverables:
      - "master_track.mp3"
      - "instrumental_track.mp3"
      - "vocal_track.mp3"

  step_2_bpm_analysis:
    tool: "Sound Crafter"
    output: "BPM 기반 샷 타이밍 가이드"
    deliverables:
      - "timing_cues.json"
      - "beat_markers.json"

  step_3_video_generation:
    tool: "Video Maker (Kling 2.6)"
    config:
      audio_mode: "instrumental_only"  # 인스트루멘탈 트랙 동기화
      native_audio: false  # BGM은 Suno에서 가져옴
      sfx_generation: true  # 효과음은 Native로 생성

  step_4_audio_assembly:
    tool: "Post-production"
    layers:
      - "Suno BGM (master_track)"
      - "Native SFX (from Kling)"
      - "Optional: ElevenLabs narration"
```

---

## Appendix A: 용어집

| 용어 | 정의 |
|------|------|
| **DNA** | Digital Narrative Architecture - 창작 성향/스타일의 구조화된 표현 |
| **BPM** | Beats Per Minute - 음악 템포 단위 |
| **I2V** | Image-to-Video - 이미지에서 비디오 생성 |
| **T2V** | Text-to-Video - 텍스트에서 비디오 생성 |
| **RRF** | Reciprocal Rank Fusion - 다중 검색 결과 융합 방법 |
| **HITL** | Human-in-the-Loop - 인간 개입 워크플로우 |
| **Mise-en-scène** | 프레임 내 모든 시각적 요소의 배치 |
| **Auteur** | 영화 감독을 작품의 저자로 보는 이론 및 해당 감독 |

---

## Appendix B: 참고 자료

### Web Sources
- [Google Developers Blog - Veo 3.1](https://developers.googleblog.com/introducing-veo-3-1-and-new-creative-capabilities-in-the-gemini-api/)
- [Google Cloud - Veo 3.1 Prompting Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1)
- [Google DeepMind - Veo](https://deepmind.google/models/veo/)
- [Kling AI Guide](https://wavespeed.ai/blog/posts/kling-2-0-complete-guide-2026/)
- [Kuaishou - Kling 2.6 Press Release](https://ir.kuaishou.com/news-releases/news-release-details/kling-ai-launches-video-26-model-simultaneous-audio-visual)
- [OpenAI Sora 2](https://openai.com/index/sora-2/)
- [Nature Scientific Reports - Music Tempo & Emotion](https://www.nature.com/articles/s41598-025-92679-1)
- [ByteDance StoryMem](https://the-decoder.com/bytedances-storymem-gives-ai-video-models-a-memory-so-characters-stop-shapeshifting-between-scenes/)
- [StoryMem Project Page](https://kevin-thu.github.io/StoryMem/)
- [No Film School - Cinematography Mathematics](https://nofilmschool.com/2013/12/mathematical-breakdown-cinematography-there-will-be-blood)
- [arXiv - Generative AI for Film Creation Survey](https://arxiv.org/html/2504.08296v1)

### Academic Sources (2025-2026)
- Lake Forest College Eukaryon Journal - Bong Joon-ho Analysis (March 2024)
- UVM ScholarWorks - Genre Analysis Thesis
- PMC - Music Tempo Emotional Response Studies
- arXiv:2512.19539 - StoryMem: Multi-shot Long Video Storytelling with Memory (2025)
- arXiv:2601.03655 - VideoMemory: Toward Consistent Video Generation via Memory (2026)
- arXiv:2507.04590 - VLM2Vec-V2: Advancing Multimodal Embedding for Videos (2025)
- Meta AI - ImageBind: One Embedding Space To Bind Them All
- Google Vertex AI - Multimodal Embeddings Documentation

### MCP/Context7 Sources
- LangGraph Documentation - Multi-agent Orchestration Patterns
- LangGraph - Conditional Edges and State Management

---

## Part 10: P0 Infrastructure 구현 현황

> **Updated**: 2026-01-17

### 10.1 P0 구현 상태 요약

| Component | 상태 | 위치 | 테스트 |
|-----------|------|------|--------|
| **Multi-Modal RAG** | ✅ 완료 | `app/rag/multi_rag/` | 24 passed |
| **Multi-RAG Router** | ✅ 완료 | `app/rag/router/` | 25 passed |
| **Dynamic DAG Planner** | ✅ 완료 | `app/workflow/` | 69 passed |
| **HITL Checkpoint System** | ✅ 완료 | `app/workflow/executor.py` | 포함 |

### 10.2 Multi-Modal RAG (Named Vectors)

```
app/rag/multi_rag/
├── types.py              # Modality, ContentType, VectorConfig, CollectionSchema
├── embedders/
│   ├── base.py           # BaseMultiModalEmbedder + BM25 Sparse
│   └── gemini_embedder.py # Gemini text-embedding-004 (768D)
├── collection_manager.py  # Qdrant Named Vectors + Circuit Breaker
├── retriever.py          # CrossModalRetriever + RRF Fusion
├── service.py            # MultiModalRAGService API
└── __init__.py
```

**핵심 기능**:
- 4개 Named Vectors: text_embed, image_embed, audio_embed, video_embed
- 768D 통합 임베딩 공간
- Hybrid Search (Dense + BM25 Sparse)
- Cross-Modal 검색 (텍스트 → 이미지/비디오)
- Dimension별 컬렉션 자동 생성

### 10.3 Multi-RAG Router (Intelligent Source Selection)

```
app/rag/router/
├── types.py              # RAGSourceType, QueryIntent, RouteDecision
├── registry.py           # RAGSourceRegistry (Composable Pattern)
├── intelligent_router.py # 2-Stage Hybrid Router
├── orchestrator.py       # Parallel Query + RRF Fusion
└── backends/
    ├── base.py           # RAGSourceBackend Protocol
    ├── notebooklm.py     # Tier0 거장 DNA
    ├── multimodal_qdrant.py # multi_rag/ 연동
    └── user_history.py   # PostgreSQL 작업 히스토리
```

**핵심 기능**:
- 8개 소스 타입 지원 (AUTEUR_DNA, MULTIMODAL_DIMENSION, USER_HISTORY 등)
- 2단계 Hybrid Routing:
  1. Rule-based Pre-filter (키워드, 컨텍스트)
  2. LLM-based Selection (복잡 쿼리용)
- 병렬 쿼리 실행 (asyncio.gather)
- RRF (Reciprocal Rank Fusion) 결과 융합
- evidence_refs 자동 생성

**사용법**:
```python
from app.rag.router import multi_rag_query

result = await multi_rag_query(
    query="봉준호 감독의 계단 상징",
    dimension="4D",
    auteur_key="bong",
)
# result.documents, result.sources_used, result.evidence_refs
```

### 10.4 Dynamic DAG Planner (Workflow V2)

```
app/workflow/
├── types.py              # DataType, ToolCapability, DAGNode, ConditionalEdge
├── registry.py           # ToolCapabilityRegistry
├── dag_builder.py        # DynamicDAGBuilder + IntentAnalyzerV2
└── executor.py           # HITLWorkflowExecutor + HITLWorkflowExecutorV2
```

**V2 확장 타입**:
- ConditionalEdge: 상태 기반 동적 라우팅
- RouterNode: LLM 기반 라우팅 노드
- WorkflowState: LangGraph StateGraph 패턴
- ExecutableDAGV2: 조건부 엣지 포함

### 10.5 References

- [LlamaIndex RouterQueryEngine](https://docs.llamaindex.ai/en/stable/examples/low_level/router/)
- [LangChain Multi-Source Knowledge Router](https://docs.langchain.com/oss/python/langchain/multi-agent/router-knowledge-base)
- [RAGRouter Paper](https://arxiv.org/abs/2505.23052)
- [LangGraph Conditional Edges](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)

---

**Document Status**: Draft v1.2 (P0 구현 완료)
**Next Review**: After individual app research completion
**Owner**: Crebit Studio Development Team

### Changelog

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0 | 2026-01-17 | 초기 거시적 기획 문서 작성 |
| 1.1 | 2026-01-17 | Part 9 추가: Native Audio, Prop/BG Consistency, Multi-Modal Embedding, DAG 확장 계획, Suno AI 통합 전략 |
| 1.2 | 2026-01-17 | Part 10 추가: P0 Infrastructure 구현 현황 (Multi-Modal RAG, Multi-RAG Router, Dynamic DAG, HITL) |
