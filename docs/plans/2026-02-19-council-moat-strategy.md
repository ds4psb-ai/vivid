# Council 해자 구축 전략 — SSOT/Runbook 보강 + 구현 로드맵

> **Date**: 2026-02-19
> **Author**: VIVID Tiger Team
> **Status**: Design — 사용자 검증 완료
> **전제**: 타당성 보고서(`2026-02-19-model-council-feasibility-report.md`)와 아이디어북(`2026-02-19-model-council-creative-ideas.md`)을 기반으로, 코드베이스 현실과 대조하여 해자 전략을 구체화한다.

---

## Part 1: 외부 비판 평가 (코드 근거 기반)

### 비판 요약

외부 전문가의 핵심 주장: "MVP 세트(6+9+3)만으로는 ChatGPT에 씬 설명 붙여넣는 것과 다를 바 없다. 해자가 없다."

### 인정하는 부분

1. `pattern_atoms`에 실제 명작 데이터가 0건이면, Council이 채우는 `expected_effect`나 `anti_pattern`이 모델 사전학습 지식에만 의존하는 것은 사실
2. 자기강화 플라이휠은 초기 데이터가 있어야 회전을 시작한다
3. "인프라 먼저 → 차별화 데이터"라는 2단계 구조 자체는 합리적

### 반박하는 부분 (코드 근거)

| 전문가 주장 | 실제 코드 현실 | 근거 파일 |
|------------|--------------|----------|
| "명작 DB/RAG 없으면 교과서 수준 답변" | Qdrant 4-컬렉션 구조 + `PatternExtractionService` 이미 구축. 빈 것은 인프라가 아니라 데이터 | `qdrant_collections.py`, `pattern_extraction_service.py` |
| "유저 행동 데이터 누적이 없다" | Thompson Sampling + EnhancedRewardService가 acceptance/edit/rejection 보상 루프 실행 중 | `experiment_service.py`, `enhanced_reward_service.py` |
| "Council만으로는 차별화 불가" | Council은 단독 제품이 아님. `final_score_v2` 수식(7변수) + KPI 슬라이딩 윈도우 위에 올라가는 지능 레이어 | `recommendation_service.py`, `kpi_service.py` |
| "100개 명작 씬이라도 있어야" | **Council 자체가 enrichment 도구**. 현재 `extract()`는 빈도 통계만 산출. Council이 `expected_effect`/`anti_pattern`을 채우는 것이 첫 번째 해자 | `pattern_extraction_service.py:43` |
| "ChatGPT랑 다를 게 없다" | ChatGPT는 단일 모델 일회성 답변. VIVID는 ① 패턴 Qdrant 축적 ② A/B 실험 검증 ③ 권리 게이트 법적 안전 ④ evidence_refs 근거 추적 | 전체 Foundry 모듈 |

### 전문가가 모르는 핵심

구독 토큰 전략(OpenClaw→Opus, Agent0→Codex)으로 Council 비용이 사실상 무료다. "비용 대비 효과"라는 프레이밍 자체가 성립하지 않는다.

---

## Part 2: 진짜 해자 6가지 (코드 연결)

### 해자 1: Council-Bootstrapped Pattern Seeding (데이터 부트스트랩)

**문제**: `pattern_extraction_service.py:43`의 `extract()`는 빈도 통계만 산출. SSOT §6.5.1의 `expected_effect`, `anti_pattern`, `preconditions` 필드가 비어있음.

**전략**: Council 자체를 명작 데이터 enrichment 도구로 사용.

- Step 3 (Feature Extraction) 후 Gemini가 뽑은 통계 atom을 Council에 투입
- Opus: `expected_effect` + `anti_pattern` 생성 (시네마틱 이론 근거)
- Codex: `execution_template`의 최적 범위를 코퍼스 통계로 보정
- **50개의 Council-enriched atom이 1,000개의 bare atom보다 가치가 높다**

**코드 변경점**: `pattern_extraction_service.py`의 `extract()` 리턴 후, 새로운 `council_enrich()` 단계 추가.

---

### 해자 2: Disagreement → Experiment Priority (플라이휠)

**문제**: `experiment_service.py:78`에서 Thompson Sampling이 변종을 탐색하지만, 어떤 실험이 정보 가치가 높은지 우선순위가 없음.

**전략**: Council 불일치를 Thompson의 탐색 부스터로 연결.

- 3모델 점수 max-min 차이 > 0.3 → exploration rate 상향
- 불일치가 큰 곳 = 가장 배울 게 많은 곳 → 먼저 실험
- 합의된 곳은 실험 불필요 → 비용 절약

**코드 변경점**: `experiment_service.py`의 `assign()` + `record_feedback()`에 `council_disagreement` 파라미터 ~20줄.

---

### 해자 3: Negotiation Council (경계선 구출)

**문제**: `recommendation_service.py:87`에서 `continuity_score < 0.60`이면 무조건 `hold`. 사용자는 왜 탈락했고 어떻게 고치는지 모름.

**전략**: Negotiation Council을 경계선(0.55~0.65)에서 발동.

- Council이 "0:43 지점에 반응 샷 삽입" 같은 구체적 수정안을 합의
- "rejected" → "fixable with specific action" 전환
- 이것이 사용자가 "오 이건 다르다" 느끼는 순간

**코드 변경점**: `recommendation_service.py` 분기 추가 + 신규 `council/negotiation_council.py`.

---

### 해자 4: Meta-Council KPI (자가 진화)

**문제**: `kpi_service.py`가 latency/continuity/pattern_reuse만 추적. Council 자체의 건강 상태를 모름.

**전략**: Meta-Council을 KPI 확장으로 구현.

- `council_diversity_score`: 3모델이 매번 같은 답이면 Council 무의미
- `council_bias_drift`: 특정 모델이 항상 소수의견이면 재조정 필요
- 기존 `SlidingWindow` 인프라 위에 바로 올림

**코드 변경점**: `kpi_service.py`에 `record_council_session()` + KPI 필드 추가 ~30줄.

---

### 해자 5: Retrospective → Prompt Compiler 자동 보정

**전략**: 생성 후 Council이 원래 의도 vs 결과 gap을 분석 → `prompt_compiler.py`와 `engine_constraint_schemas.py`에 피드백.

- "Veo에서 dolly_in 요청했는데 zoom_in 나옴" → 다음부터 프롬프트 자동 보정
- 시간이 갈수록 프롬프트 품질이 올라가는 누적 효과

**코드 변경점**: 신규 `council/retrospective_council.py` + `prompt_compiler.py` 피드백 인터페이스.

---

### 해자 6: Director Persona as RAG Vector Modifier

**전략**: Director's Council(Idea 1)을 새 UI가 아닌 검색 벡터 변조로 구현.

- "봉준호 스타일" 선택 시 Qdrant 검색에서 공간/계급 패턴 가중치 부스트
- 새 인프라 불필요, 기존 `retrieval_service.py` + Qdrant payload filter 활용

**코드 변경점**: `retrieval_service.py`에 `director_persona` 파라미터 + PERSONA_BOOST 매핑 ~40줄.

---

## Part 3: SSOT 보강안 (AD_CO_DIRECTOR_OS_SSOT 변경 사항)

### 3-1. 신규 §6.6: Model Council Integration Layer

```
### 6.6.1 역할 배치
| 모델 | 역할 | 질문 유형 | 호출 경로 |
|------|------|----------|----------|
| Gemini 3 Pro | Visual Parser | "What" | AD Core 직접 호출 |
| Opus 4.6 | Deep Analyst | "Why" | OpenClaw 구독 토큰 |
| Codex 5.3 | Data Analyst | "How much" | Agent0 구독 토큰 |
| Gemini Flash | Synthesizer | 종합 | AD Core 직접 호출 |

### 6.6.2 적용 지점 (선택적, 전면 적용 금지)
- P0: Pattern Atom Enrichment (§6.5.3 step 4)
- P0: Gate B OR-gate (§6.4)
- P1: continuity_score 3축 분리 (§7)
- P2: Borderline Negotiation (§7.2 확장)

### 6.6.3 Provider Port
Council도 D-09(Provider Port 추상화)를 준수한다.
구현체: OpenClawCouncilProvider / DirectAPICouncilProvider
분기 Switch Drill(D-10) 대상에 포함.

### 6.6.4 비용 원칙
- 구독 토큰 우선, API 직접 과금은 fallback
- 전면 적용 금지 — P0 게이트만 Council 사용
- Synthesizer는 항상 최저가 모델(Flash)

### 6.6.5 해자 전략 연결
- 해자 1 (Bootstrap): §6.5.3 step 4에서 Council enrichment
- 해자 2 (Flywheel): §9 실험 엔진에 불일치 기반 우선순위
- 해자 3 (Negotiation): §7.2 경계선 협상
- 해자 4 (Meta): §12 KPI에 Council 건강 지표
- 해자 5 (Retrospective): §10 Prompt Compiler 피드백 루프
- 해자 6 (Director): §8 검색 계층에 페르소나 벡터 변조
```

### 3-2. §6.5.3 step 4 수정: Council-Enriched Pattern Mining

```
Step 4: Pattern Mining (Council-Enriched)
├── 통계 추출 (기존): PatternExtractionService.extract()
│   → atom_id, frequency, confidence (변경 없음)
└── Council Enrichment (신규): CouncilService.enrich()
    ├── Gemini: pattern_type 검증 + preconditions 초안
    ├── Opus: expected_effect + anti_pattern 생성
    ├── Codex: execution_template 정량 보정
    └── Synthesizer: confidence_tier 분류
```

### 3-3. §7.2 확장: Borderline Negotiation Protocol

기존:
- `< 0.60` → 자동 탈락
- `0.60 <= x < 0.80` → 제한 노출
- `>= 0.80` → 기본 추천군

보강:
- `< 0.55` → 자동 탈락
- `0.55 <= x < 0.65` → **Negotiation Council 발동**
  - 3모델이 구체적 수정안 합의
  - 수정 후 예상 점수와 함께 사용자에게 제시
- `0.65 <= x < 0.80` → 제한 노출 (기존)
- `>= 0.80` → 기본 추천군 (기존)

### 3-4. §12 KPI 추가: Council 건강 지표

```
- council_diversity_score (주간): 3모델 의견 다양성. < 0.2이면 역할 재설계
- council_bias_drift (주간): 특정 모델 소수의견 빈도. > 0.7이면 가중치 재조정
- synthesizer_fidelity (주간): Synthesizer가 3개 응답을 실제 종합하는지 vs 1개 복사
- council_outcome_correlation (월간): Council 합의 vs 실제 사용자 만족도 상관
```

### 3-5. §11 Wave 타임라인 수정

```
Wave 1 (Day 3-9) 추가:
- pattern_atoms payload에 council_metadata 스키마 사전 정의
- council_provider.py Port 계약 + Contract Test
- OpenClaw→Opus, Agent0→Codex 호출 경로 검증

Wave 2 (Day 10-16) 추가:
- Day 10-11: council.py 골격 + provider 연결
- Day 12-13: Pattern Extraction Council Enrichment (P0-1)
- Day 13-14: Gate B 3모델 OR-gate (P0-2)
- Day 14-15: continuity_score 3축 분리 (P1)
- Day 15-16: Council ON/OFF A/B 실험 시작
```

---

## Part 4: Runbook 보강안 (30DAY_TIGER_RUNBOOK 변경 사항)

### 4-1. Day 0-2 추가: Council 전제조건

```
- [ ] OpenClaw workspace에서 Opus 4.6 호출 성공 확인
- [ ] Agent0 worker에서 Codex 5.3 dispatch 성공 확인
- [ ] council_provider.py Port 계약 초안 + Contract Test Suite
- [ ] pattern_atoms Qdrant 컬렉션에 council_metadata payload 스키마
- [ ] Kill switch: AD_COUNCIL_ENABLED (AD_FOUNDRY_ENABLED과 독립)
```

### 4-2. Day 3-9 추가: Council-Bootstrapped Seeding

```
Day 5-7: Council Enrichment 파이프라인 구축 (Masterpiece Ingestion과 병렬)
  - public domain / CC0 클립 50개 선정 (장르별 5개 × 10장르)
  - PatternExtractionService.extract() → bare atom
  - CouncilService.enrich() → expected_effect/anti_pattern/execution_template
  - 목표: Day 9까지 Council-enriched atom 최소 200개

Day 7-9: enriched atom 품질 검수
  - Meta-Council 감사 1회 실행
  - diversity_score, synthesizer_fidelity 기준값 설정
```

### 4-3. Day 10-16 추가: Council 본격 투입

```
Day 10-11: Council Core
  - council.py: asyncio.gather(gemini, opus, codex) 병렬 호출
  - council_synthesizer.py: 합의/불일치 → confidence_tier
  - council_config.py: 모델/역할/가중치 설정

Day 12-13: P0 통합
  - pattern_extraction_service.py → Council enrichment
  - rights_service.py → Gate B 3모델 OR-gate

Day 14-15: P1 통합
  - recommendation_service.py → continuity_score 3축 분리
  - Borderline Negotiation (0.55~0.65) 프로토타입

Day 15-16: A/B 실험
  - experiment_key: "council_on" vs "council_off"
  - council_disagreement 기반 실험 우선순위
  - 성공 기준: Council-enriched accept_rate > baseline +10%
```

### 4-4. Day 17-23 추가: Retrospective + Meta-Council

```
Day 17-19: Retrospective Council
  - 생성 결과물 vs 의도 gap 분석 파이프라인
  - prompt_compiler.py 피드백 루프 연결
  - engine_constraint_schemas.py 자동 보정 시작

Day 20-22: Meta-Council Weekly Run
  - kpi_service.py에 council_diversity/bias_drift/synthesizer_fidelity
  - 첫 번째 주간 감사 실행
  - 결과에 따라 모델 역할/가중치 조정
```

### 4-5. Day 24-30 추가: Council 런치 게이트

```
- [ ] Council-enriched pattern_atoms 1,000+
- [ ] Council ON/OFF A/B에서 ON accept_rate +10%
- [ ] Gate B Council false-negative 0건
- [ ] Borderline Negotiation 피드백 50건+
- [ ] Meta-Council 감사 2회+, diversity_score > 0.3
- [ ] Council Provider Switch Drill 1회
```

### 4-6. §6 지표 보강

```
- Council-enriched atoms: 1,000+
- Council ON accept_rate uplift: +10%
- council_diversity_score: > 0.3
- Negotiation "fixable" 전환율: 30%+
- Retrospective prompt 보정 건수: 50+
```

---

## Part 5: 구현 우선순위 (코드 수준)

### Tier 1: 즉시 구현 (~20-50줄)

| ID | 아이디어 | 변경 파일 | 변경량 |
|----|---------|----------|--------|
| 6 | Disagreement-as-Signal | `experiment_service.py` | ~20줄 |
| 11 | Meta-Council KPI | `kpi_service.py` | ~30줄 |

### Tier 2: 중간 규모 (신규 모듈 1-2개)

| ID | 아이디어 | 변경 파일 | 신규 파일 |
|----|---------|----------|----------|
| 9 | Negotiation Council | `recommendation_service.py` | `council/negotiation_council.py` |
| 1 | Director Persona | `retrieval_service.py` | — |
| 7 | Retrospective | `prompt_compiler.py` | `council/retrospective_council.py` |

### Tier 3: 장기 (데이터 축적 전제)

| ID | 아이디어 | 전제 조건 | 적합 시점 |
|----|---------|----------|----------|
| 3 | Audience Simulation | A/B 데이터 500건+ | Day 30+ |
| 4 | Temporal Scale | 시대별 pattern_atoms | Ingestion 완료 후 |
| 5 | Style Fusion | 감독별 패턴 충분 | Day 17+ (비동기) |
| 10 | Cross-Era | 시대별 레퍼런스 클립 | Ingestion 완료 후 |
| 2 | Adversarial Red Team | Gate B 강화로 대체 가능 | 별도 구현 불필요 |
| 8 | Council as Curriculum | Council 세션 100+ | Day 30+ |

---

## 핵심 메시지

외부 전문가는 "명작 DB 없으면 해자가 없다"고 했다. **반은 맞고 반은 틀리다.**

맞는 부분: 데이터 없는 Council은 교과서를 읽어주는 것에 그친다.

틀린 부분: 우리에겐 이미 데이터를 적재하고 실험하고 학습하는 **인프라**가 있다. Council은 그 인프라 위에서 데이터의 **품질**을 올리는 지능 레이어다. ChatGPT는 이 인프라가 없다.

**진짜 전략**: Council을 "검증 도구"로만 쓰지 말고, **데이터 enrichment + 플라이휠 가속 + 경계선 UX 차별화 + 자가 진화**의 4가지 축으로 동시에 활용한다. 이것이 VIVID만의 해자다.

---

## Sources

### VIVID Internal
- `docs/AD_CO_DIRECTOR_OS_SSOT_2026_H2.md` — 상위 SSoT
- `docs/AD_30DAY_TIGER_RUNBOOK_2026-02.md` — 30일 런북
- `docs/reports/2026-02-19-model-council-feasibility-report.md` — 타당성 보고서
- `docs/reports/2026-02-19-model-council-creative-ideas.md` — 아이디어북

### Foundry 코드 (근거)
- `backend/app/features/original_ip_foundry/pattern_extraction_service.py`
- `backend/app/features/original_ip_foundry/experiment_service.py`
- `backend/app/features/original_ip_foundry/recommendation_service.py`
- `backend/app/features/original_ip_foundry/kpi_service.py`
- `backend/app/features/original_ip_foundry/retrieval_service.py`
- `backend/app/features/original_ip_foundry/prompt_compiler.py`

### 학술 (타당성 보고서 공유)
→ `docs/reports/2026-02-19-model-council-feasibility-report.md` Sources 참조
