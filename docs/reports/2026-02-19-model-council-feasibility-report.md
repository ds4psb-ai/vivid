# VIVID Model Council 도입 타당성 보고서

> **Date**: 2026-02-19
> **Author**: VIVID Tiger Team
> **Status**: Draft for Review
> **Scope**: Gemini 3 Pro + Claude Opus 4.6 + Codex 5.3 → 3-Model Council 아키텍처 도입 분석

---

## Executive Summary

VIVID의 Original-IP Foundry(SSOT §6)는 **Gemini 3 Pro + TwelveLabs + CV 룰셋**으로 레퍼런스 영상/명작을 분석하고, 그 결과를 **Pattern Atom**으로 정형화하여 **Qdrant 4-컬렉션**에 축적한다 (§6.5). 추천은 `continuity_score` 하드게이트(§7, D-01)를 거치고, 생성물은 **Rights Graph + Gate A/B/C**(§6.4)를 통과해야 퍼블리시된다.

본 보고서는 Perplexity가 2026년 2월 출시한 **Model Council 패턴** — 3개 모델 동시 쿼리 후 synthesizer가 합의/불일치를 종합 — 을 이 SSOT 파이프라인에 이식할 경우의 효과, 비용, 리스크를 분석한다.

**핵심 결론**: Council은 **새로운 레이어를 추가하는 것이 아니다**. SSOT §6.5.3의 Feature Extraction 단계에서 Gemini가 장면 역할/감정곡선/서사 기능을 뽑고, TwelveLabs가 임베딩을 만들고, CV가 정량값을 측정한 **이후** — 그 산출물을 Opus와 Codex가 **읽고 보완**하는 것이다. Pattern Mining(§6.5.3 step 4)과 Packaging(step 5) 단계에 Council이 들어간다.

**신체 비유**:

| 역할 | VIVID 시스템 (SSOT 참조) | 하는 일 |
|------|-------------------------|--------|
| **눈 (Eyes)** | Gemini 3 Pro + TwelveLabs + CV (§6.5.3 step 3) | 영상을 보고 장면 역할, 감정곡선, 서사 기능, 임베딩, 구도/무브/편집 정량값을 추출 |
| **기억 (Memory)** | Qdrant 4-컬렉션 (§6.5.5) + Pattern Atom 축적 | `shot_corpus`, `pattern_atoms`, `transition_rules`, `rights_constraints`에 패턴 누적 |
| **연상 (Association)** | 4-pass 검색 (§6.5.5) + HybridSearch | Dense ANN → payload 필터 → pattern rerank → transition rerank |
| **손 (Hands)** | **Codex 5.3** (Council 신규) | 코퍼스 통계 산출 — `execution_template`의 최적 샷 길이/앵글/무브 파라미터를 데이터에서 계산 |
| **뇌 (Brain)** | **Opus 4.6** (Council 신규) | `expected_effect`와 `anti_pattern` 판단 — "왜 이 패턴이 관객에게 작동하는가"를 시네마틱 이론에 근거해 서술 |

---

## 1. Model Council이란 무엇인가

### 1.1 Perplexity의 구현

Perplexity는 2026년 2월 10일 **Model Council**을 Max/Enterprise 구독자에게 출시했다.

**메커니즘**:
1. 사용자 질의를 **Claude Opus 4.6, GPT 5.2, Gemini 3 Pro** 3개 모델에 동시 전송
2. 각 모델이 독립적으로 응답 생성
3. **Synthesizer 모델**이 3개 응답을 분석하여 합의점/불일치점을 구조화된 테이블로 종합
4. 최종 응답은 합의된 사실 + 불일치 영역의 명시적 표기

> Source: [Perplexity Blog — Introducing Model Council](https://www.perplexity.ai/hub/blog/introducing-model-council)

### 1.2 학술적 근거

| 연구 | 핵심 발견 | VIVID 시사점 |
|------|----------|-------------|
| **ICE** (Iterative Consensus Ensemble, 2025) | 3개 LLM이 반복 비평 → **정확도 27% 향상** (60.2% → 74.03%) | 반복 비평 라운드는 latency 부담. VIVID는 **1-round parallel** 후 synthesizer가 적합 |
| **Compound Inference Scaling Laws** (Chen et al., NeurIPS 2024) | Voting 성능은 **비단조적** — easy query에서 향상, hard query에서 오히려 하락 | VIVID의 continuity 판단은 "hard query" 영역 → **단순 majority vote 부적합**, synthesizer 필수 |
| **Mixture of Agents** (Wang et al., 2024) | 이종 LLM 레이어 쌓기로 AlpacaEval 65.8% 달성 | 2-layer MoA는 과도. VIVID는 **1-layer 3-model parallel이 최적** |
| **L-Storyboard** (arXiv 2505.12237) | 샷→언어 변환 후 LLM이 Shot Sequence Ordering 수행. StoryFlow로 발산→수렴 전환 | VIVID Pattern Atom의 `execution_template`과 직접 매핑 가능 |
| **Language Model Council** (NAACL 2025) | 20개 LLM 위원회 → 인간 랭킹 Spearman 상관 **0.92**. 최적점: ~50 예시 + 9 판정관 | 주관적 태스크에서 앙상블이 개별 모델 편향을 효과적으로 중화 |
| **Self-MoA** (arXiv 2502.00674) | 단일 최고 모델 다중 샘플링 > 다중 모델 MoA (AlpacaEval **+6.6%**) | **반론**: 객관적 태스크에서 유효. VIVID의 다차원 판단에는 이종 모델 Council이 더 적합 |
| **CineTechBench** (NeurIPS 2025) | 7개 시네마틱 차원 공식화 (Scale/Angle/Composition/Motion/Lighting/Color/Focal). 구세대 모델 벤치마크 | 차원별 **오류 패턴이 모델마다 다름**을 보여줌 → Council의 비상관 오류 교차 보정 근거 |
| **A-HMAD** (ACL Findings 2025) | 에이전트별 신뢰도 가중 debate → 표준 토론 대비 **+4-6%** | VIVID synthesizer에 신뢰도 가중 방식 채택 근거 |

> Sources:
> - [ICE Paper — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0010482525310820)
> - [Scaling Laws — arXiv 2403.02419](https://arxiv.org/abs/2403.02419)
> - [L-Storyboard — arXiv 2505.12237](https://arxiv.org/abs/2505.12237)
> - [Language Model Council — NAACL 2025](https://aclanthology.org/2025.naacl-long.617.pdf)
> - [Self-MoA — arXiv 2502.00674](https://arxiv.org/abs/2502.00674)
> - [CineTechBench — NeurIPS 2025](https://arxiv.org/abs/2505.15145)
> - [A-HMAD — ACL Findings 2025](https://aclanthology.org/2025.findings-acl.606.pdf)

---

## 2. 3-Model 역할 분담 설계

### 2.1 모델별 강점 매핑

OpenClaw와 Agent0 모두 모델을 지정할 수 있으므로, 각 모델의 고유 강점에 맞춰 **역할 특화** 배치가 가능하다.

| 축 | Gemini 3 Pro | Claude Opus 4.6 | Codex 5.3 |
|----|-------------|-----------------|-----------|
| **핵심 역할** | 시각 파싱 (Visual Parser) | 심층 판단 (Deep Analyst) | 정량 분석 (Data Analyst) |
| **질문 유형** | "무엇이 보이는가?" | "왜 이것이 작동하는가?" | "얼마나 효과적인가?" |
| **컨텍스트 윈도우** | 2M tokens (비디오 직접 입력) | 1M tokens (장문 맥락 분석) | 제한적 (코드/데이터 특화) |
| **SWE-Bench** | N/A | **80.8%** | 78.2% |
| **모호한 태스크** | 비전 특화 | **안정적** — 맥락 이해 후 올바른 판단 | 약함 — 상세 설명 필요 |
| **속도** | 보통 | 보통 | **25% 빠름** |
| **데이터 패턴 분석** | 시각 데이터 | 직관적 판단 | **강함** — 통계 생성/비교 |
| **Video-MMMU** | **87.6%** (1위) | N/A | N/A |
| **BrowseComp** | N/A | **84.0%** (+16.2pp vs 4.5) | N/A |
| **BigLaw Bench** | N/A | **90.2%** (법률 추론 1위) | N/A |
| **Terminal-Bench 2.0** | N/A | 65.4% | **75.1-77.3%** (SOTA) |
| **OSWorld** | N/A | 42% | **64.7%** |
| **Humanity's Last Exam** | N/A | **40.0%** (no tools) | N/A |

> Sources:
> - [Opus 4.6 vs Codex 5.3 — Interconnects.ai](https://www.interconnects.ai/p/opus-46-vs-codex-53)
> - [Gemini 3 Pro Benchmarks — Vellum](https://www.vellum.ai/blog/google-gemini-3-benchmarks)
> - [Claude Opus 4.6 Benchmarks — Vellum](https://www.vellum.ai/blog/claude-opus-4-6-benchmarks)
> - [GPT-5.3 Codex — DataCamp](https://www.datacamp.com/blog/gpt-5-3-codex)

### 2.2 Council 최적 배치 원칙

```
┌─────────────────────────────────────────────────────┐
│              VIVID Model Council                     │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Gemini   │  │  Opus    │  │  Codex   │          │
│  │ 3 Pro    │  │  4.6     │  │  5.3     │          │
│  │          │  │          │  │          │          │
│  │ "What"   │  │  "Why"   │  │ "How     │          │
│  │ 시각 파싱 │  │ 서사 판단 │  │  much"   │          │
│  │          │  │          │  │ 정량 분석 │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│       └──────────────┼──────────────┘                │
│                      ▼                               │
│            ┌──────────────┐                          │
│            │ Synthesizer  │                          │
│            │ (Gemini Pro) │                          │
│            │              │                          │
│            │ consensus /  │                          │
│            │ divergence   │                          │
│            │ → confidence │                          │
│            │   tier       │                          │
│            └──────────────┘                          │
└─────────────────────────────────────────────────────┘
```

**Synthesizer 모델 선택**: Gemini Pro (비용 효율 + 구조화 출력 안정성). Synthesizer의 역할은 "판단"이 아니라 "종합"이므로 가장 비싼 모델일 필요 없다.

---

## 3. VIVID 파이프라인별 Council 적용

### 3.1 Council의 위치: SSOT §6.5.3 파이프라인 내부

SSOT §6.5.3은 패턴 추출 파이프라인을 6단계로 정의한다:

```
1. Ingest & Rights Gate → 2. Temporal Segmentation → 3. Feature Extraction
→ 4. Pattern Mining → 5. Packaging → 6. Serving
```

Council은 **step 3 이후, step 4-5에 개입**한다. Step 3에서 Gemini + TwelveLabs + CV가 추출한 결과물을 Opus와 Codex가 읽고, Pattern Atom의 나머지 필드(`expected_effect`, `anti_pattern`, `execution_template` 최적값)를 채운다.

```
Step 3: Feature Extraction (변경 없음)
├── Gemini 3 Pro  → 장면 역할, 감정곡선, 서사 기능
├── TwelveLabs    → 멀티모달 임베딩, 샷 검색 키
└── CV 룰셋      → 구도, 무브, 편집 리듬 정량값
         │
         │ 텍스트화된 피처 (Gemini 추출 결과 + 임베딩 + 정량값)
         ▼
Step 4: Pattern Mining — 여기에 Council 적용
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Gemini   │  │  Opus    │  │  Codex   │
│ 3 Pro    │  │  4.6     │  │  5.3     │
│          │  │          │  │          │
│ pattern_ │  │ expected │  │ execution│
│ type 분류│  │ _effect  │  │ _template│
│ + pre-   │  │ + anti_  │  │ 정량화   │
│ conditions│  │ pattern  │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     └──────────────┼──────────────┘
                    ▼
          ┌──────────────┐
          │ Synthesizer  │ → confidence_tier 분류
          └──────────────┘
                    │
                    ▼
Step 5: Packaging → pattern_atoms + transition_rules + anti_patterns
```

**핵심 전제: Opus와 Codex는 영상을 볼 수 없다.** Step 3의 비주얼 추출(shot_scale, camera_motion, lighting 등)은 Gemini + TwelveLabs + CV가 단독 수행한다. Council이 개입하는 것은 그 **텍스트 산출물을 해석하고 보강**하는 단계다.

### 3.2 적용 우선순위

| SSOT 참조 | 파이프라인 | Council 역할 | **우선순위** |
|-----------|-----------|-------------|------------|
| §6.5.3 step 4-5 | Pattern Atom 완성 | Opus: `expected_effect`/`anti_pattern`, Codex: `execution_template` 정량화 | **P0** |
| §6.4 Gate B | Post-gen 권리 검증 | 3모델 OR-gate (시각/서사/법적) | **P0** |
| §7 D-01 | continuity_score 산출 | Opus: 서사 연속성, Codex: 리듬 통계 보정 | **P1** |
| §6.5.4 | final_score_v2 각 항목 | 앙상블 평균 | **P2** |
| §10 | Prompt Compiler | 룰 기반으로 충분 — Council 불필요 | N/A |

### 3.3 P0-1: Pattern Atom 완성 (§6.5.1 + §6.5.3)

SSOT §6.5.1의 Pattern Atom 스키마를 기준으로, 각 모델이 채우는 필드를 명시한다:

| Pattern Atom 필드 | 누가 채우는가 | 어떻게 |
|-------------------|-------------|--------|
| `pattern_type` | **Gemini** (step 3에서 이미 추출) + Council 검증 | Gemini가 분류한 결과를 Opus가 맥락 검증. "이 composition 분류가 서사 맥락에서 맞는가?" |
| `preconditions` | **Gemini** (초안) + **Opus** (보강) | Gemini가 감정/공간/인물 조건 초안 → Opus가 시네마틱 이론(Bordwell, 봉준호 공간론 등)에 근거해 빠진 전제조건 보완 |
| `execution_template` | **Gemini + CV** (초안) + **Codex** (정량 최적화) | step 3의 샷 길이/앵글/무브 값을 Codex가 코퍼스(MovieNet 92K 태그, CineScale 792K 프레임) 통계와 비교하여 최적 범위를 계산 |
| `expected_effect` | **Opus** (주도) | "왜 이 dolly-in + CU 조합이 서스펜스를 만드는가" — 1M context에 시네마틱 이론 논문을 대량 투입하여 관객 체감 효과를 서술 |
| `anti_pattern` | **Opus** (주도) + Gemini (보조) | "이 기법을 남용하면 연속성이 훼손되는 조건"을 Opus가 서사 감각으로 감지. Gemini는 시각적으로 정상이라 놓치는 남용을 Opus가 잡음 |
| `source_license`, `provenance_trace` | Rights Graph (Council 불필요) | 기존 §6.4 Gate A가 처리 |

**구체적 예시 — "dolly-in to CU" 패턴**:

```json
{
  "pattern_type": "camera_motion",           // Gemini 분류, Opus 검증
  "preconditions": {
    "emotion_state": "tension_building",     // Opus: 봉준호 공간론 참조
    "character_count": 1,
    "space": "confined_or_intimate"           // Opus: 공간 제약 조건 추가
  },
  "execution_template": {
    "shot_scale": "MS → CU",
    "camera_motion": "dolly_in",
    "duration_range": [2.4, 4.0],            // Codex: MovieNet p25-p75 범위
    "recommended_transition": "dissolve",     // Codex: 성공률 67% > cut 45%
    "rhythm_pattern": "deceleration"
  },
  "expected_effect": "관객의 시선을 강제로 인물 내면으로 끌어들임. 이전 LS에서의 고립감과 대비되어 친밀도 급상승",  // Opus
  "anti_pattern": "dolly_in 후 즉시 cut away하면 감정 해소 없이 끊김. 최소 1.5s hold 필요",  // Opus
  "council_metadata": {
    "consensus_rate": 0.92,
    "confidence_tier": "high",
    "models": ["gemini_3_pro", "opus_4_6", "codex_5_3"]
  }
}
```

**시네마틱 논문/데이터셋 연계** (Shot Grammar Canonicalization §6.5.2):

| 데이터셋 | 규모 | Council 활용 |
|---------|------|-------------|
| **CineScale** | 792K frames, 7 shot scale | Codex가 `execution_template`의 shot_scale 분포 통계를 이 데이터셋에서 산출 |
| **MovieNet** | 1,100 movies, 92K tags | Codex가 `pattern_type` ground truth + transition 성공률 계산. Opus가 태그 간 서사 관계 해석 |
| **MovieBench** | CVPR 2025, scene/shot hierarchy | 계층적 주석(movie→scene→shot)이 4-pass 검색 구조(§6.5.5)와 동형 |
| **MultiShotMaster** | arXiv 2025 | 멀티샷 제어 가능 생성의 품질 기준 → Pattern Atom 완성도 검증에 활용 |

### 3.4 P0-2: Post-gen Gate B (§6.4 Rights Enforcement)

**현재 위험**: 단일 모델 판단 → false-negative(위반인데 통과) 가능성.

**Council 적용** — SSOT §6.4의 Gate B를 3축 OR-gate로 확장:

| 모델 | 검증 축 | SSOT 연결 |
|------|--------|----------|
| **Gemini** | 시각적 유사도 — 색상 팔레트, 구도, 캐릭터 실루엣, 로고 | `blocked_elements` (§6.3) 시각 매칭 |
| **Opus** | 서사/대사 구조 유사도 — 문체, 플롯 패턴, 고유 세계관 요소 | `provenance_trace` (§6.3) 서사 체인 검증 |
| **Codex** | 법적 금칙요소 패턴 매칭 — 등록 상표, 고유 명사, 보호 캐릭터 명칭 DB 대조 | `rights_constraints` 컬렉션 (§6.5.5) 대조 |

**게이트 규칙**: `OR-gate` — 하나라도 위반 감지 시 차단

KPI `clone_risk 차단 누락 0건`(§12)과 `권리 증빙 누락 0건`에 **가장 직접적으로 기여**:
- 단일 모델은 시각/서사/법적 3개 축 중 하나를 놓칠 확률이 존재
- 3모델 OR-gate는 false-negative 확률이 **곱셈으로 감소**

### 3.5 P1: continuity_score 보강 (§7 D-01)

**현재** (SSOT §7.1): `final_score_v2`에서 `continuity` 가중치 0.40 (최대).
하드게이트: `< 0.60` 탈락, `≥ 0.80` 기본 추천군.

**Council 적용**: continuity_score 내부를 3축으로 분리

| 모델 | 판단 축 | 기여 |
|------|---------|------|
| **Gemini** | 시각 연속성 — 조명/색온도/프레임 내 캐릭터 위치 | step 3에서 이미 추출한 피처 활용 |
| **Opus** | 서사 연속성 — 캐릭터 동기 흐름, 감정 곡선, 씬 간 정보 브리지 | D-01이 말하는 "연속성"의 핵심. 시각보다 **서사 연속성이 더 중요한 게이트** |
| **Codex** | 리듬 연속성 — 샷 길이 분포, 전환 템포의 통계적 정상 범위 | 코퍼스 통계 기반 정밀 보정 |

**합의 규칙**:
- 3모델 모두 ≥ 0.80 → `high_confidence` (자동 추천, §7.2)
- 2/3 ≥ 0.80 → `medium_confidence` (추천 가능, 주석 표기)
- 불일치 → Human QC 큐 라우팅

---

## 4. 비용 분석

### 4.1 모델별 토큰 단가 (2026-02 기준, 구독 토큰 경유)

OpenClaw와 Agent0를 통해 구독 토큰으로 호출하므로, API 직접 과금 대비 비용 절감이 가능하다.

| 모델 | Input ($/M tokens) | Output ($/M tokens) | 비고 |
|------|-------------------|--------------------|----|
| Gemini 3 Pro (≤200K) | $2.00 | $12.00 | 캐싱 75% 할인, 배치 50% 할인 |
| Gemini 3 Pro (>200K) | $4.00 | $18.00 | 비디오 입력 시 프레임당 토큰 추가 |
| Claude Opus 4.6 (≤200K) | $5.00 | $25.00 | 프롬프트 캐싱 90% 절감, 배치 50% |
| Claude Opus 4.6 (>200K) | $10.00 | $37.50 | Fast Mode: $30/$150 |
| GPT-5.2 (Codex 5.3 참고) | $1.75 | $14.00 | Codex 5.3 API 가격 미공개, 구독 전용 |
| Gemini Flash (Synthesizer) | $0.08 | $0.30 | Flash Lite 기준, 종합에 충분 |
| **구독 경유 절감** | **~60-80% 절감 추정** | | OpenClaw/Agent0 구독 내 크레딧 |

> Sources: [LLM Pricing — CloudIDR](https://www.cloudidr.com/blog/llm-pricing-comparison-2026), [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)

### 4.2 파이프라인별 호출 비용 시뮬레이션

**가정**: Pattern Atom 추출 1건 = 입력 ~5K tokens, 출력 ~2K tokens (모델당)

| 적용 지점 | 단일 모델 (현재) | Council (3모델) | 증가율 | 비용 정당성 |
|-----------|-----------------|----------------|--------|-----------|
| Pattern Extraction (1건) | Gemini 1회 | Gemini + Opus + Codex + Synthesizer | **~4x** | pattern_reuse_rate 35%+ 달성 가속 |
| Gate B (1건) | 단일 모델 1회 | 3모델 + Synthesizer | **~4x** | 법적 리스크 0건 = **무한대 ROI** |
| continuity_score (1건) | 단일 모델 1회 | 3모델 + Synthesizer | **~4x** | 추천 품질 직결 |

### 4.3 구독 토큰 전략의 핵심

> **Ted의 핵심 인사이트**: OpenClaw와 Agent0 각각에서 모델을 지정할 수 있다. 구독 토큰으로 Opus/Codex/Gemini를 호출하면, API 직접 과금 대비 60-80% 절감이 가능하다. Council의 비용 장벽이 사실상 제거된다.

**전략**:
- OpenClaw 워크스페이스에서 Opus 4.6 호출 (서사 분석)
- Agent0 워커에서 Codex 5.3 호출 (정량 분석)
- AD Core에서 Gemini 3 Pro 직접 호출 (시각 파싱, 기존 인프라)
- Synthesizer는 Gemini Flash (가장 저렴, 구조화 종합에 충분)

---

## 5. Scaling Law 주의사항

### 5.1 비단조 성능 곡선 (Chen et al., NeurIPS 2024)

**핵심 발견**: LLM voting 성능은 호출 수가 늘어날수록 **단조 증가하지 않는다**.

- **Easy queries**: 호출 수 증가 → 성능 증가
- **Hard queries**: 호출 수 증가 → 성능 **감소**
- **혼합 태스크**: 비단조적 (peak 이후 하락)

**VIVID에 대한 시사점**:
1. continuity_score 판단은 **hard query** 범주 → 단순 majority vote 사용 금지
2. 최적 호출 수는 **3개** (이종 모델, 역할 분리) — 동일 모델 반복 호출보다 효과적
3. **Synthesizer가 핵심** — vote가 아니라 **structured merge**가 필요

> Source: [arXiv 2403.02419](https://arxiv.org/abs/2403.02419)

### 5.2 Council ≠ Voting

| 패턴 | 메커니즘 | VIVID 적합성 |
|------|---------|-------------|
| **Majority Voting** | 동일 모델 N회 → 다수결 | 부적합 — hard query에서 성능 하락 |
| **Best-of-N** | N회 생성 → reward model 선택 | 부분 적합 — reward model 필요 |
| **MoA (Mixture of Agents)** | 레이어별 다른 모델 | 과도 — 2+ layer latency 부담 |
| **Model Council** | 이종 3모델 + synthesizer | **최적** — 역할 분리 + 1-round + structured merge |
| **ICE** | 반복 비평 (multi-round) | P2 검토 — latency vs accuracy 트레이드오프 |

---

## 6. 아키텍처 설계: SSOT 정합

### 6.1 코드 위치

D-09 ("Provider Port 추상화")와 D-10 ("2주 이내 대체 가능성 리허설") 원칙을 준수한다. SSOT §3.3에 따라 VIVID 모노레포 내부의 Foundry 수직 슬라이스에 배치한다.

```
backend/app/features/original_ip_foundry/
  └── council/                      # NEW directory
        ├── council.py              # asyncio.gather(gemini, opus, codex)
        ├── council_synthesizer.py  # 합의/불일치 → confidence_tier 분류
        ├── council_provider.py     # Provider Port 계약 준수 (§5.4)
        └── council_config.py       # 모델/역할/가중치 설정
```

### 6.2 Provider Port 확장 (§5.4 갈아끼우기 규칙 준수)

기존 Memory Port, Worker Port, Channel Port에 **Council Port**를 추가한다:

```python
# council_provider.py — §5.4 Contract 패턴 준수
class CouncilProvider(Protocol):
    """Council도 Port로 추상화 — 모델 교체 시 이 파일만 수정

    Switch Drill (D-10): 분기 1회 OpenClaw↔DirectAPI 전환 리허설 대상
    """

    async def query_visual(self, input: CouncilInput) -> ModelResponse:
        """시각 파싱 (기본: Gemini 3 Pro)"""
        ...

    async def query_narrative(self, input: CouncilInput) -> ModelResponse:
        """서사 판단 (기본: Opus 4.6 via OpenClaw)"""
        ...

    async def query_quantitative(self, input: CouncilInput) -> ModelResponse:
        """정량 분석 (기본: Codex 5.3 via Agent0)"""
        ...

    async def synthesize(self, responses: list[ModelResponse]) -> CouncilVerdict:
        """종합 판단 (기본: Gemini Flash)"""
        ...

class OpenClawCouncilProvider(CouncilProvider):
    """OpenClaw(Opus) + Agent0(Codex) 구독 토큰 경유 구현"""
    ...

class DirectAPICouncilProvider(CouncilProvider):
    """API 직접 호출 fallback — Switch Drill 대상"""
    ...
```

### 6.3 Foundry 내 영향 범위

| Foundry 파일 (§4.3 구현체) | 변경 사항 | 영향도 |
|--------------------------|----------|--------|
| `pattern_extraction_service.py` | step 4 Pattern Mining → Council 기반으로 확장 | 높음 |
| `rights_service.py` | Gate B (§6.4) → 3모델 OR-gate 추가 | 높음 |
| `recommendation_service.py` | `continuity_score` → Council 호출 옵션 추가 | 중간 |
| `worker_runtime.py` | Agent0에 Codex 호출 dispatch (§5.2) | 낮음 |
| `qdrant_pattern_store.py` | `council_metadata` payload 필드 추가 (§6.5.5) | 낮음 |

---

## 7. 차세대 멀티샷 모델 전용 Frame-to-Text 패턴 공식

### 7.1 Council이 만드는 새로운 패턴 포맷

현재 VIVID의 Pattern Atom은 **단일 모델 관점**의 패턴이다. Council을 적용하면 **다관점 합의 패턴**이 된다:

```json
{
  "pattern_id": "council_pat_001",
  "pattern_type": "camera_motion",
  "confidence_tier": "high",
  "council_consensus": {
    "visual": {
      "model": "gemini_3_pro",
      "scene_role": "escalation",
      "camera_motion": "dolly_in_to_CU",
      "frame_composition": "rule_of_thirds_left"
    },
    "narrative": {
      "model": "opus_4_6",
      "why_it_works": "관객의 시선을 강제로 인물 내면으로 끌어들임. 이전 LS에서의 고립감과 대비되어 친밀도 급상승",
      "emotion_arc_position": "conflict → escalation transition",
      "anti_pattern": "dolly_in 후 즉시 cut away하면 감정 해소 없이 끊김"
    },
    "quantitative": {
      "model": "codex_5_3",
      "optimal_duration_sec": 3.2,
      "optimal_duration_std": 0.8,
      "dolly_speed_percentile": "p60-p75 of MovieNet corpus",
      "transition_to_next": "dissolve (67% success rate) > cut (45%)",
      "statistical_confidence": 0.89
    }
  },
  "execution_template": {
    "shot_scale": "MS → CU",
    "camera_motion": "dolly_in",
    "duration_range": [2.4, 4.0],
    "recommended_transition": "dissolve",
    "rhythm_pattern": "deceleration"
  },
  "preconditions": {
    "emotion_state": "tension_building",
    "character_count": 1,
    "space": "confined_or_intimate"
  },
  "source_license": "derived_pattern",
  "provenance_trace": {
    "source_clips": ["movienet:1234", "cinescale:5678"],
    "extraction_method": "council_v1",
    "consensus_round": 1,
    "agreement_rate": 0.92
  }
}
```

### 7.2 Frame-to-Text Prompt 공식 (멀티샷 생성 엔진용)

Council 기반 Pattern Atom을 Veo 3 / Kling 3.0 / Seedance 2.0 / Sora 2 프롬프트로 컴파일할 때:

```
[Shot {N}]
Scale: {execution_template.shot_scale}
Camera: {execution_template.camera_motion}
Duration: {quantitative.optimal_duration_sec}s
Rhythm: {execution_template.rhythm_pattern}
Emotional Intent: {narrative.emotion_arc_position}
Why: {narrative.why_it_works}  ← Opus가 생성한 "왜" 설명이 프롬프트 품질을 올린다
Transition to Shot {N+1}: {quantitative.recommended_transition}
Anti-pattern Warning: {narrative.anti_pattern}
```

**핵심 차별화**: 기존 frame-to-text는 "무엇을" 기술하는 데 그치지만, Council 패턴은 **"왜 이렇게 해야 하는가"**(Opus)와 **"통계적으로 최적인 파라미터"**(Codex)까지 포함한다. 이것이 멀티샷 생성 엔진의 프롬프트에 들어가면 **의도 있는 프롬프트**가 된다.

### 7.3 시네마틱 기법 논문 ↔ Council 연계

| 시네마틱 이론/데이터 | Gemini 역할 | Opus 역할 | Codex 역할 |
|-------------------|-----------|----------|-----------|
| Bordwell의 영화 스타일 분석 | 프레임 내 시각 요소 식별 | 스타일이 서사에 기여하는 방식 해석 | 스타일 요소의 빈도/분포 정량화 |
| Hitchcock의 서스펜스 공식 | 샷 스케일/앵글 변화 감지 | "관객이 아는데 인물이 모르는" 구조 판단 | 서스펜스 빌드업 최적 타이밍 통계 |
| 봉준호의 공간 연출 (계단/높이 차) | 프레임 내 수직/수평 위치 분석 | 계급 은유로서의 공간 해석 | 수직 구도 패턴의 관객 반응 통계 |
| L-Storyboard (2025) | 샷→L-Storyboard 변환 | StoryFlow 수렴 판단 | Shot Sequence Ordering 최적화 |

---

## 8. 리스크와 완화

| 리스크 | 심각도 | 완화 방안 |
|--------|--------|----------|
| **Latency 증가** (3모델 병렬 + synthesizer) | 중간 | `asyncio.gather` 병렬 실행. Synthesizer는 Flash(가장 빠른 모델). p95 목표 유지 가능 |
| **비용 3-4x** | 중간 | 구독 토큰 경유로 60-80% 절감. 전면이 아닌 P0 게이트만 선택 적용 |
| **모델 간 출력 형식 불일치** | 높음 | 각 모델에 **동일 JSON schema** 강제. Pydantic 검증 레이어 |
| **Synthesizer 판단 오류** | 중간 | Synthesizer는 "판단"이 아닌 "종합"만 수행. 불일치 시 confidence_tier 낮춤 → human review |
| **OpenClaw/Agent0 API 불안정** | 낮음 | D-09 Provider Port로 fallback 보장. DirectAPI 구현체 상시 유지 |
| **Hard query 성능 하락** (Scaling Law) | 높음 | Vote 아닌 Council 패턴 사용 (structured merge). 역할 분리로 각 모델이 "easy 영역"만 담당 |
| **모델 업데이트로 Council 불안정** | 중간 | D-10 Vendor Switch Drill에 Council 모델 교체 리허설 포함 |

---

## 9. SSOT 30일 로드맵 내 삽입 위치 (§11 기준)

SSOT §11의 4-Wave 구조에 Council을 자연스럽게 끼운다:

### Wave 1 (Day 3-9) — 사전 준비

Council 자체는 아직 붙이지 않는다. Wave 1에서 **Council의 전제 조건**을 세팅한다:

- Qdrant 4-컬렉션 구축 (§6.5.5) — `pattern_atoms`에 `council_metadata` payload 스키마 미리 정의
- `council_provider.py` Port 계약 초안 + Contract Test Suite 작성
- OpenClaw Workspace에 Opus 4.6 호출 경로 검증, Agent0에 Codex 5.3 dispatch 검증

### Wave 2 (Day 10-16) — Intelligence Activation (Council 본격 투입)

| Day | 태스크 | 담당 | SSOT 연결 |
|-----|--------|------|----------|
| 10-11 | `council.py` + `council_provider.py` 골격 구현 | Codex 5.3 코드 생성 | §5.4 Port 패턴 |
| 11-12 | OpenClaw/Agent0 경유 모델 호출 연결 | Platform | §5.1-5.2 역할 경계 |
| 12-13 | Pattern Extraction step 4에 Council 통합 (P0-1) | Opus 4.6 아키텍처 검토 | §6.5.3 step 4 |
| 13-14 | Gate B에 3모델 OR-gate 통합 (P0-2) | Legal Ops 검증 | §6.4 Gate B |
| 14-15 | continuity_score 3축 분리 (P1) | AD Studio | §7 D-01 |
| 15-16 | A/B: Council ON/OFF 비교 실험 셋업 | QA | §9 실험 엔진 |

### 성공 기준 (Day 16, §12 KPI 연동)

- [ ] Council 경유 Pattern Atom 추출 1,000건+ 완료 (§12: pattern_atoms 누적 10,000+ 중 일부)
- [ ] Gate B Council false-negative 테스트: 기존 단일 모델 대비 감소 확인 (§12: clone_risk 차단 누락 0건)
- [ ] continuity_score Council vs 단일 모델 A/B 실험 시작 (§12: continuity ≥ 0.80 비율 70%+)
- [ ] p95 latency: Council 적용 파이프라인에서 < 3.5s (§12: 추천 API p95 < 2.5s + 1s 허용)

---

## 10. 결론 및 권고

### 10.1 Do (실행)

1. **P0 즉시 적용**: Pattern Atom Feature Extraction + Post-gen Gate B
   - 이 두 곳은 Council의 ROI가 가장 높다
   - 특히 Gate B는 법적 리스크 0건 = 비용 제한 없는 투자 영역

2. **구독 토큰 전략 확정**: OpenClaw(Opus) + Agent0(Codex) + Direct(Gemini)
   - API 직접 과금 대비 60-80% 절감으로 Council 비용 장벽 제거

3. **Synthesizer는 Gemini Flash**: 가장 저렴하고 빠른 모델로 "종합만" 수행

### 10.2 Don't (금지)

1. **전면 적용 금지**: 모든 API 호출에 Council을 붙이면 비용만 3배, 효과는 비례하지 않음
2. **Majority Vote 사용 금지**: Scaling Law 연구가 hard query에서 성능 하락을 증명함
3. **ICE(반복 비평) 초기 도입 금지**: latency 부담. 추후 P2로 검토

### 10.3 Watch (모니터링)

1. Council 적용 전후 **pattern_reuse_rate** 변화
2. Gate B **false-negative 0건** 유지 여부
3. p95 latency 변화 (예산: +1s)
4. 모델별 합의율 추적 → 특정 모델이 항상 소수 의견이면 역할 재조정 필요

---

## Sources

### Model Council & Ensemble
- [Perplexity — Introducing Model Council](https://www.perplexity.ai/hub/blog/introducing-model-council)
- [긱뉴스 — 퍼플렉시티 모델 카운슬](https://news.hada.io/topic?id=26438)
- [디자인 나침반 — 여러 AI의 답을 합치기](https://designcompass.org/2026/02/11/perplexity-model-council-synthesizing-responses-from-multiple-ais/)
- [ICE Paper — Computers in Biology and Medicine (2025)](https://www.sciencedirect.com/science/article/abs/pii/S0010482525310820)
- [Scaling Laws — arXiv 2403.02419 (NeurIPS 2024)](https://arxiv.org/abs/2403.02419)
- [Mixture of Agents — arXiv 2406.04692 (ICLR 2025 Spotlight)](https://arxiv.org/abs/2406.04692)
- [Self-MoA — arXiv 2502.00674](https://arxiv.org/abs/2502.00674)
- [Language Model Council — NAACL 2025](https://aclanthology.org/2025.naacl-long.617.pdf)
- [Debate vs Vote (A-HMAD) — ACL Findings 2025](https://aclanthology.org/2025.findings-acl.606.pdf)

### Cinematographic Datasets & Papers
- [CineTechBench — NeurIPS 2025, arXiv 2505.15145](https://arxiv.org/abs/2505.15145)
- [CineScale — 792K frames](https://www.sciencedirect.com/science/article/pii/S2352340921002869)
- [CineScale2 — angle/level](https://www.sciencedirect.com/science/article/pii/S2352340923007126)
- [MovieNet — ECCV 2020](https://movienet.github.io/projects/eccv20movienet.html)
- [MovieBench — CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Wu_MovieBench_A_Hierarchical_Movie_Level_Dataset_for_Long_Video_Generation_CVPR_2025_paper.html)
- [MultiShotMaster — arXiv 2512.03041](https://arxiv.org/html/2512.03041v1)
- [L-Storyboard — arXiv 2505.12237](https://arxiv.org/abs/2505.12237)
- [Film Editing Patterns (FEP) — ACM TOMM 2018](https://inria.hal.science/hal-01950718)
- [Cinematographic Camera Diffusion — arXiv 2402.16143](https://arxiv.org/html/2402.16143v1)
- [Camera Trajectory Survey — arXiv 2506.00974](https://arxiv.org/html/2506.00974v1)
- [Video-MME — CVPR 2025](https://arxiv.org/abs/2405.21075)
- [Graph-VideoAgent — arXiv 2501.15953](https://arxiv.org/html/2501.15953v1)

### Model Comparison
- [Opus 4.6 vs Codex 5.3 — Interconnects.ai](https://www.interconnects.ai/p/opus-46-vs-codex-53)
- [Opus 4.6 vs Codex 5.3 — Every.to](https://every.to/vibe-check/codex-vs-opus)

### VIVID Internal
- `docs/AD_CO_DIRECTOR_OS_SSOT_2026_H2.md` — 상위 SSoT (본 보고서의 모든 §N 참조는 이 문서)
- `backend/app/features/original_ip_foundry/` — Foundry 구현체 (§4.3 스냅샷)
- `backend/app/rag/` — HybridSearch + GraphRAG 구현체

### Komission 레퍼런스 (자매 프로젝트, 검증된 아키텍처)
- `komission/backend/app/services/clustering.py` — PatternClusteringService (9차원 유사도, 투표 기반 aggregated_dna)
- `komission/backend/app/schemas/vdg_base.py` — CANONICAL_FIELDS (27필드 SSoT)
- `komission/backend/app/services/incremental_dna_aggregator.py` — 투표 기반 패턴 DNA 축적
- `komission/backend/app/services/vdg_schema_normalizer.py` — VDG 스키마 정규화
