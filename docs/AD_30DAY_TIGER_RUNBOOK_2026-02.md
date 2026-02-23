# AD Co-Director + Original-IP Foundry 30-Day Tiger Runbook (2026-02)

> Version: 2.0 (Ambient Canvas)
> Owner: VIVID Product / Platform
> Date: 2026-02-23
> Scope: 30일 내 Launch Candidate 확보
> 참조: [Ambient Creative Canvas OS — Vision Document](AD_AMBIENT_CREATIVE_CANVAS_VISION_2026_H2.md) (상위 Why 문서)

---

## 1) 목적

90일 플랜을 30일로 압축해, 다음 3가지를 동시에 달성한다.

1. **Canvas + Fragment**: Blueprint Canvas 가동 + Fragment Ingestion Pipeline 운영화 + Auto-Placement 70%+ 수락률
2. **Materialization + 3 Engines**: Progressive Materialization 경로 확보 + 3엔진(Kling 3.0, Seedance 2.0, Veo 3.1) Prompt Compiler 안정화 (Sora 제거)
3. **Rights + Continuity Gate**: Rights Graph + clone_risk 게이트 운영 + continuity를 품질 게이트로 유지

---

## 2) 운영 모델 (Codex 5.3 + Opus 4.6 풀가동)

### 2.1 역할 분리

- **Codex 5.3 xhigh Terminal Lane**
  - 코드 구현/테스트 생성/리팩터 자동화
  - 반복 작업(계약 테스트/스키마 동기화/스크립트 보강) 집중
  - Cinema Grammar KB 인덱싱/파싱 + 이론 vs 실전 정량 교차검증 (Agent0 dispatch)
- **Opus 4.6 Review Lane**
  - 아키텍처/리스크/권리 정책 검토
  - 랭킹 수식/실험 설계/문서 SSOT 품질 점검

### 2.2 1일 실행 루프

1. 09:00-09:20: KPI 브리핑(continuity, pattern reuse, clone risk, p95, **`creative_fill_rate`**, **`fragment_capture_rate`**, **`auto_placement_accuracy`**)
2. 09:20-12:30: 병렬 구현 스프린트 A
3. 13:30-16:30: 병렬 구현 스프린트 B
4. 16:30-17:30: 통합 테스트 + 회귀 확인
5. 17:30-18:00: 다음날 우선순위 고정

### 2.3 병렬 규칙

- 하루 2회 머지 윈도우(점심/저녁)
- 기능 플래그 기본 ON/OFF
- 머지 조건: 계약 테스트 + 핵심 스모크 테스트 통과

---

## 3) 30일 타임라인

### Day 0-2: War-Room
- 팀 역할/승인권자/온콜 확정
- Channel/Memory/Worker 계약 테스트 파이프라인 구축
- **Council 전제조건**: OpenClaw→Opus 4.6 호출 검증, Agent0→Codex 5.3 dispatch 검증
- **Council Port 계약**: `council_provider.py` 초안 + Contract Test Suite
- **Cinema Grammar KB 범위 확정**: EditingGrammarKB / NarrativeTheoryKB / StylePatternKB 소스 수집 목록 확정 (§SSOT 2-H)
- **Kill switch**: `AD_COUNCIL_ENABLED` 환경변수 (`AD_FOUNDRY_ENABLED`과 독립)
- **Blueprint Canvas schema design**: 셀 구조(5min × 20셀 그리드), Fragment 임베딩 포맷, Canvas state 영구 저장 스키마
- **Fragment Ingestion Pipeline contract**: ChannelEvent v1 → FragmentClassifier → Auto-Placement 계약 정의
- **Auto-Placement AI contract**: input: Fragment + Canvas state → output: suggested_cell + confidence 인터페이스 확정
- **Canvas state persistence contract**: OpenClaw Memory 기반 Canvas 상태 영구 저장/조회 계약

### Day 3-9: Foundation
- Rights Graph + pre/post gate
- Qdrant 4-컬렉션
- OpenClaw/Agent0 포트 연결
- Masterpiece ingestion v0 (1,000 클립)
- **Council-Bootstrapped Seeding** (Ingestion과 병렬):
  - CC0 클립 50개 선정 (장르별 5개 × 10장르)
  - `PatternExtractionService.extract()` → bare atom
  - `CouncilService.enrich()` → expected_effect/anti_pattern/execution_template
  - 목표: Day 9까지 Council-enriched atom 200+
- **Enriched atom 품질 검수**: Meta-Council 감사 1회, diversity/fidelity 기준값 설정
- **Cinema Grammar KB 인프라** (Council Seeding과 병렬):
  - VPS 1-3에 OpenClaw KB 인스턴스 배포 (EditingGrammar/Narrative/Style 각 1대)
  - Codex 5.3 xhigh로 KB 텍스트 파싱/구조화 배치 시작 (Agent0 orchestrated)
  - 목표: Day 9까지 EditingGrammarKB 규칙 50+ 인덱싱
- **Qdrant 5th collection `blueprint_fragments`**: Fragment 임베딩 + placement metadata 저장 컬렉션 구축
- **Fragment Ingestion Pipeline v0**: Telegram → FragmentClassifier → basic Auto-Placement (규칙 기반 초기 배치)
- **Blueprint Canvas MVP**: Web UI sparse grid view + 수동 Fragment 배치 기능
- **Sora adapter 제거**: Prompt Compiler에서 Sora adapter deprecation, `DEFAULT_ENGINES: ["kling", "seedance", "veo"]`

### Day 10-16: Intelligence
- Pattern Atom 추출
- ranking v2 → **ranking v3** 업그레이드:
  - continuity 가중치 0.40→0.20 하향
  - **NEW** `fill_rate_impact` 가중치 0.15 신설
  - `pattern_affinity` 가중치 0.10→0.15 상향
- A/B + Thompson 운영 시작
- **Council Core 구현** (Day 10-11):
  - `council.py`: asyncio.gather(gemini, opus, codex) 병렬
  - `council_synthesizer.py`: 합의/불일치 → confidence_tier
  - `council_config.py`: 모델/역할/가중치 설정
- **P0 통합** (Day 12-13):
  - `pattern_extraction_service.py` → Council enrichment 연결
  - `rights_service.py` → Gate B 3모델 OR-gate
- **P1 통합** (Day 14-15):
  - `recommendation_service.py` → continuity_score 3축 분리
  - Borderline Negotiation (0.55~0.65) 프로토타입
- **Theory Validation 활성화** (Day 14):
  - Pattern Atom `theory_layer` 필드 활성화
  - Council enrichment에 Theory Validation 단계 추가 (Codex xhigh + KB 교차검증)
  - 3단 분류 (Invariant/Power Mutation/Dead Rule) 첫 배치 실행
- **A/B 실험** (Day 15-16):
  - experiment_key: "council_on" vs "council_off"
  - council_disagreement 기반 실험 우선순위 로직
  - 성공 기준: Council-enriched accept_rate > baseline +10%
  - CoachingSource A/B/C 실험 설계 준비 (A=Empirical, C=Fused 우선)
- **Progressive Materialization v0**: Level 0→1→2 경로 구현 (Memo→Storyboard→KeyVisual), Level 3→4는 Day 17+ 이후 활성화
- **Gap Detection v0**: 구조적 gap만 우선 감지 (Structural Gap), NarrativeTheoryKB 통합
- **Seedance 2.0 adapter 업데이트**: lens switch, camera path, **12 multimodal refs** (`@image1`~`@image9`, `@video1`~`@video3`, `@audio1`~`@audio3`), 해상도 2K, 길이 ~20초 파라미터 반영, Dual-Branch Diffusion Transformer 활용
- **Kling 3.0 adapter 업데이트**: **Smart Storyboard** (AI 자동 분할) + **Custom Storyboard** (수동 샷 제어), `multi_shot`/`multi_prompt[index/prompt/duration]`/`cfg_scale(0~1)`/`element_list` API params, Pro/Standard 모델 선택, Native 4K, 3~15초, 네이티브 오디오(다국어)

### Day 17-23: B2C 채널 + Canvas UX
- Telegram/WebChat 안정화
- Kakao adapter 베타
- 이벤트 유실/중복 모니터링
- **Retrospective Council** (Day 17-19):
  - 생성 결과물 vs 의도 gap 분석 파이프라인
  - `prompt_compiler.py` 피드백 루프 연결
  - `engine_constraint_schemas.py` 자동 보정 시작
- **Theory KB 첫 감사** (Day 19-20):
  - 이론 vs 실전 교차검증 결과 첫 리뷰
  - Dead Rule / Power Mutation 첫 분류 결과 검토
  - KB 인덱싱 커버리지 확인 (EditingGrammar 100+, Narrative 50+, Style 30+ 목표)
- **Meta-Council Weekly Run** (Day 20-22):
  - `kpi_service.py`에 council_diversity/bias_drift/synthesizer_fidelity 추가
  - theory_alignment_avg / power_mutation_ratio / dead_rule_prune_count 추가
  - 첫 번째 주간 감사 실행
  - 결과에 따라 모델 역할/가중치 조정
- **CoachingSource A/B/C 실험** (Day 22-23, 데이터 충분 시):
  - A(Empirical) vs B(Theory) vs C(Fused) 비교 시작
  - 성공 기준: C > A by +10%, C > B by +5%, B > A by any margin
- **Telegram Fragment UX**: 빠른 캡처 — photo/text/voice → auto-classify → auto-place (5초 내 Canvas 반영)
- **Web Canvas UI**: 인터랙티브 그리드, 드래그-드롭 Fragment 배치, materialization level 인디케이터 시각화
- **Gap Suggestion v0**: NarrativeTheoryKB 기반 구조적 gap 제안 기능 (Structural Gap 우선)
- **Progressive Materialization Level 2→3→4 경로 활성화**: KeyVisual→Prompt→Video 변환 파이프라인 연결

### Day 24-30: Launch
- Vendor switch drill + **Council Provider Switch Drill 1회**
- near-duplicate 차단 자동화
- 런북/권리분쟁 대응서 완성
- 파일럿 유료/LOI 확보
- **Council 런치 게이트 확인**:
  - [ ] Council-enriched pattern_atoms 1,000+
  - [ ] Council ON/OFF A/B에서 ON accept_rate +10%
  - [ ] Gate B Council false-negative 0건
  - [ ] Borderline Negotiation 피드백 50건+
  - [ ] Meta-Council 감사 2회+, diversity_score > 0.3
- **Cinema Grammar KB 런치 게이트** (§SSOT 2-H):
  - [ ] EditingGrammarKB 인덱싱 완료 (규칙 100+)
  - [ ] NarrativeTheoryKB 인덱싱 완료 (개념 50+)
  - [ ] StylePatternKB 인덱싱 완료 (패턴 30+)
  - [ ] Theory-validated atoms 500+ (theory_layer 포함)
  - [ ] theory_alignment 평균 > 0.5 (Invariant 패턴 기준)
  - [ ] CoachingSource C > A uplift 확인
  - [ ] VPS 1-3 KB 검색 p95 < 500ms
- **Canvas 런치 게이트**:
  - [ ] `creative_fill_rate >= 0.30` 파일럿 프로젝트 달성
  - [ ] `fragment_capture_rate` 모니터링 대시보드 구축 (목표: 5+/day per project)
  - [ ] `auto_placement_accuracy` 트래킹 (목표: 70%+)
  - [ ] Canvas state consistency audit 완료 (OpenClaw Memory ↔ Qdrant `blueprint_fragments` 동기화 검증)

---

## 4) 저장소 전략 (질문 답변)

### 결론

**지금은 새 프로젝트를 파지 말고 VIVID 안에서 만드는 게 맞다.**

### 이유

1. 30일 내 출시에서 기존 인증/크레딧/UI/모니터링 자산 재사용이 필수
2. 새 프로젝트는 CI/CD/권한/운영 도구를 다시 세팅해야 해 속도 손실 큼
3. 벤더 락인 우려는 "레포 분리"가 아니라 Port/Adapter/Contract Test로 해소 가능

### 단, 이렇게 만든다

- 코드 경계: `backend/app/features/original_ip_foundry/*`
- 채널/메모리/워커는 인터페이스로 격리
- 30일 후 스핀아웃 판단 체크리스트 운영

### 스핀아웃 조건 (30일 이후)

- 배포 주기 독립 필요(주 3회+)
- 트래픽 격리 필요(메인 대비 30%+)
- 팀/권한/비용센터 분리 필요

---

## 5) Quality Gate

1. `continuity_score < 0.60` 자동 차단
2. clone_risk 임계치 초과 자동 차단
3. evidence_refs 누락 배포 금지
4. rights false-negative 0건 유지
5. **`creative_fill_rate < 0.15`** 프로젝트 경고 — Canvas 채움 비율이 최소 기준 미달 시 프로젝트 정체 알림
6. **`auto_placement_accuracy < 0.50`** 알고리즘 재검토 트리거 — 자동 배치 수락률 50% 미만 시 배치 로직 점검
7. **`fragment_capture_rate < 2/day`** 프로젝트 stale 경고 — Fragment 수집이 일 2건 미만 시 프로젝트 비활성 경고

---

## 5.1 A-Prime 운영 규약 (옵션 A 실전판)

"플래그 없이 바로 붙인다" 대신, **최소 브레이크**만 둔 운영 규약.

1. 환경변수 Kill Switch(`AD_FOUNDRY_ENABLED`)를 운영자가 즉시 변경 가능해야 한다.
2. 내부/파일럿 계정 allowlist가 기본값이며, 전체 공개는 Day 24 이후 승인제로 진행한다.
3. 초기 3일은 read-only 모드(추천 생성/조회만, 파괴적 write 금지)로 운영한다.
4. Foundry 배치 큐와 기존 수강생 기능 큐를 분리해 성능 간섭을 차단한다.
5. 장애 기준(응답지연/오류율/권리게이트 이상) 초과 시 10분 내 비활성화한다.
6. Qdrant 쓰기 경로는 `revision + wait=true + ordering=strong`을 기본값으로 한다.
7. Worker Port는 `Agent0` 기본, `Taskiq` 대체 구현체를 항상 유지한다.

## 5.2 Day 0~2 구현 체크 (코드 반영 기준)

- [x] Guardrail 4종(킬스위치/allowlist/쓰기보호/네임스페이스) 적용
- [x] Foundry 공통 관측성(`foundry.audit`) 필드 고정
- [x] 권리 평가 API (`/foundry/rights/evaluate-assets`) 추가
- [x] 패턴 추출 API (`/foundry/patterns/extract`) 추가
- [x] continuity 우선 추천 API (`/foundry/recommendations/next-scene`) 추가
- [x] 실험 배정/피드백/요약 API (`/foundry/experiments/*`) 추가
- [x] 메모리 정규화 + 이중검색 API (`/foundry/memory/normalize`, `/foundry/retrieval/query`) 추가
- [x] C2PA 호환 provenance export API (`/foundry/provenance/export-c2pa`) 추가
- [x] 운영 문서: `ORIGINAL_IP_FOUNDRY_OPERATIONS_RUNBOOK_2026-02.md` 연결

---

## 6) 지표 목표 (Day 30)

### 6.1 핵심 지표

- 추천 API p95 < 2.5s
- 검색 p95 < 900ms
- continuity >= 0.80 추천 비율 60%+
- pattern_atoms 10,000+
- pattern_reuse_rate 25%+
- pattern 적용군 continuity uplift +0.08+
- 유료 파일럿 또는 LOI 확보
- **`creative_fill_rate` 30%+** (프로젝트당)
- **`fragment_capture_rate` 5+/day** (프로젝트당)
- **`auto_placement_accuracy` 70%+**
- **`materialization_velocity` < 4h** (Fragment→Video 평균 소요)
- **`gap_suggestion_adoption` 40%+** (Gap 제안 수락률)

### 6.2 Council 해자 지표

- Council-enriched atoms: 1,000+ (bare atom과 별도 카운트)
- Council ON accept_rate uplift: +10% vs OFF baseline
- council_diversity_score: > 0.3
- Negotiation "fixable" 전환율: 30%+ (경계선 후보 중)
- Retrospective prompt 보정 건수: 50+
- Council Provider Switch Drill: 완료 1회
- EditingGrammarKB 인덱싱 규칙 수: 100+
- Theory-validated atoms: 500+ (theory_layer 포함)
- Power Mutation 태깅률: top-100 패턴 중 20%+
- CoachingSource C > A uplift 확인

---

## 7) 리스크 대응

1. 벤더 기능 급변
- 대응: 분기 Switch Drill + Provider Port

2. 데이터 품질 편차
- 대응: 패턴 추출 검수셋/주간 prune

3. 권리 이슈
- 대응: source_license 강제 + pre/post gate + provenance audit

4. 동시성 쓰기 충돌
- 대응: Qdrant 조건부(optimistic revision) 업데이트 + 충돌 시 재시도 큐

5. 워커 스케일 병목
- 대응: Worker Port를 통해 Agent0 ↔ Taskiq 전환 드릴 정례화

6. **Fragment Ingestion 과부하**
- 대량 미디어 동시 업로드 시 FragmentClassifier 병목 발생 가능
- 대응: 큐 기반 비동기 처리 + rate limit (프로젝트당 분당 10건)

7. **Auto-Placement 품질 저하**
- 초기 데이터 부족으로 배치 정확도 낮음 (콜드스타트)
- 대응: 수동 배치 fallback UI 제공 + 감독 피드백 루프 가속 (수락/거부 즉시 학습)

8. **Canvas 상태 불일치**
- OpenClaw Memory와 Qdrant `blueprint_fragments` 간 동기화 드리프트 발생 가능
- 대응: 주기적 reconciliation job (15분 주기) + 불일치 감지 시 Slack 알림 + 수동 동기화 트리거

---

## 8) 외부 근거 (2026-02-18)

1. OpenAI Codex CLI docs: https://developers.openai.com/codex/cli/
2. OpenAI Codex background mode: https://developers.openai.com/codex/background/
3. OpenAI Codex settings: https://developers.openai.com/codex/cli/settings/
4. OpenAI Codex update (gpt-5.3-codex): https://help.openai.com/en/articles/6825453-chatgpt-rlease-notes
5. Claude Code changelog (Opus 4.6 + memory): https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
6. OpenClaw memory docs: https://docs.openclaw.ai/concepts/memory
7. Agent0 projects/memory: https://www.agent-zero.ai/p/docs/projects/ , https://www.agent-zero.ai/p/docs/memory/
8. Qdrant multivector: https://qdrant.tech/documentation/tutorials-search-engineering/using-multivector-representations/
9. MovieBench (CVPR 2025): https://openaccess.thecvf.com/content/CVPR2025/html/Wu_MovieBench_A_Hierarchical_Movie_Level_Dataset_for_Long_Video_Generation_CVPR_2025_paper.html
10. Qdrant update vectors API (ordering/wait): https://api.qdrant.tech/master/api-reference/points/update-vectors
11. Qdrant update points API (ordering/wait): https://api.qdrant.tech/master/api-reference/points/set-payload
12. Qdrant points concepts: https://qdrant.tech/documentation/concepts/points/
13. Taskiq docs: https://taskiq-python.github.io/
14. Taskiq package: https://pypi.org/project/taskiq/
15. C2PA specification 2.2: https://spec.c2pa.org/specifications/specifications/2.3/specs/C2PA_Specification.html
16. C2PA open-source docs: https://opensource.contentauthenticity.org/docs/
17. EU AI Act timeline: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai

### Cinema Grammar & LLM 연구

18. Shen et al. 2025 — Narrative theory LLM adaptation: https://aclanthology.org/2025.conll-1.13.pdf
19. L-Storyboard 2025 — Shot-level language representation: https://arxiv.org/abs/2505.12237
20. Cinema Multiverse Lounge (CHI 2025) — Multi-agent film appreciation: https://dl.acm.org/doi/10.1145/3706598.3713641
21. FilmAgent (SIGGRAPH Asia 2024) — Multi-agent film automation: https://arxiv.org/abs/2501.12909
22. Continuity editing computational model (AAAI): https://cdn.aaai.org/ojs/9288/9288-13-12816-1-2-20201228.pdf
