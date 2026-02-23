# AD Studio Masterpiece Official Pattern (MOP) - 2026 H2

작성일: 2026-02-23
결정사항: North Star Metric은 `creative_fill_rate`를 1순위로 고정한다. `continuity_score`는 품질 게이트로 유지한다.

> 참조: `AD_AMBIENT_CREATIVE_CANVAS_VISION_2026_H2.md` (상위 비전 문서)

## 1. Why This Pattern

- **OLD**: 시퀀스 연속성 중심 — "다음 씬을 추천해줘"라는 선형 워크플로. `continuity_score`가 유일한 북극성
- **NEW**: 비선형 영감 조립 중심 — "아무 때나 영감을 던지면 100분 블루프린트에 자동 배치". `creative_fill_rate`가 1순위
- **2026 현실**: Seedance 2.0 / Kling 3.0 / Veo 3로 멀티샷 일관성이 commodity화됨. 연속성은 엔진이 해결하는 인프라 문제
- **승부처**: "어떤 샷을 만들까"가 아니라 "일상의 영감을 어떻게 100분 블루프린트로 조립하는가"
- **연속성은 당연한 인프라지, 북극성이 아니다** — 창작의 진행도(fill_rate)가 감독에게 실질적 가치를 전달한다

## 2. MOP-v2 Architecture (5 Layers)

### 1. Contract Layer

- API 응답에 `creative_fill_rate` + `continuity_score` 모두 포함
- `fill_rate`는 Canvas state에서 실시간 계산: `filled_cells / total_cells`
- `continuity`는 Materialization Level 3→4 전환 시점에서 검증 (창작 단계에서는 강제하지 않음)

### 2. Intelligence Layer

- **Fragment Classification**: 타입 분류 + 메타데이터 추출 (STT, EXIF, URL preview)
- **Auto-Placement AI**: Canvas 상태 + Fragment + Project Context → 배치 결정 (p95 < 3s)
- **Gap Detection**: NarrativeTheoryKB 기반 빈 구간 분석 — Structural / Emotional / Visual / Rhythm 4가지 유형
- **Pattern Atoms**: 기존 패턴 추출/enrichment 유지 — Canvas 컨텍스트에서 재활용

### 3. Orchestration Layer

- **3 engines**: Kling 3.0, Seedance 2.0, Veo 3 **(Sora REMOVED)**
- **Sora 제거 사유**: 멀티샷 미지원, 권리 거부 과잉, commodity 상황에서 차별 가치 부재
- **Prompt Compiler**: 3-engine compilation (`DEFAULT_ENGINES = ["kling", "seedance", "veo"]`)
- **Engine success criterion**: continuity 게이트 통과 (Level 3→4 전환 시)

### 4. Experience Layer

- **Blueprint Canvas View**: 100분 sparse 타임라인 시각화 (5분 × 20셀 그리드)
- **Fill Rate Dashboard**: `creative_fill_rate` 추이 + gap visualization
- **Materialization Progress**: 각 셀의 Level 0(Memo) ~ 4(Video) 상태 표시
- **Continuity Badge**: 기존 밴드 정책 유지
  - `>= 80%`: green (정상)
  - `60 ~ 79%`: amber (경고 + 보정 제안)
  - `< 60%`: red (배포 보류)

### 5. Trust Layer

- `evidence_refs` 누락 금지 (유지)
- **Rights pre-screen on Fragment ingestion** (새로 추가) — Fragment 수집 시점에 IP 위험 조기 분류
- C2PA/SynthID provenance 정책 유지

## 3. Release Gate Policy (Hard Rule)

### Gate A (1순위): Fill Rate + Materialization

| 조건 | 결과 |
|------|------|
| `creative_fill_rate >= 0.30` | 프로젝트 진행 승인 |
| `materialization_velocity < 4h` | Fragment→Video 속도 기준 충족 |
| Gate A 미달 | 추가 Fragment 캡처 또는 Gap Suggestion 제안 |

### Gate B (2순위 → 품질 게이트): Continuity

| 조건 | 결과 |
|------|------|
| `continuity_score >= 0.80` | 정상 배포/확장 |
| `0.60 ~ 0.79` | 제한 롤아웃 + Council Negotiation 수정안 제시 |
| `< 0.60` | 배포 보류 |

> Gate B는 **Materialization Level 3→4 전환 시에만 적용**한다. Canvas 채우기 단계에서는 continuity를 강제하지 않는다 (창작 자유 보장).

### Gate C (유지): Speed

- Gate A + B 통과 이후에만 속도 최적화 승인
- 속도 개선은 `fill_rate` / `continuity` 회귀가 0임을 증명해야 함

## 4. 2026 H2 Roadmap (Canvas-Centric)

### 7월: Canvas Foundation

- Blueprint Canvas schema + API 확정
- Fragment Ingestion Pipeline 안정화 (p95 end-to-end < 5s)
- Auto-Placement v1 런치

### 8월: Intelligence Activation

- Gap Detection v1 + NarrativeTheoryKB 연동
- Pattern Atom enrichment → Canvas 컨텍스트 반영
- Ranking v3 적용 (`fill_rate_impact` 반영)

### 9월: Materialization Pipeline

- Progressive Materialization v1 (Level 0→4 full path, 양방향)
- 3-engine Prompt Compiler 안정화 (Sora adapter deprecated)
- Council 검증 지점 활성화 (Level 전환별)

### 10월: Channel Hardening

- Telegram Fragment UX 고도화 (사진/음성/텍스트 즉시 캡처)
- Web Canvas UI v2 (drag & drop, multi-select)
- Gap Suggestion v1 + adoption 추적

### 11월: Trust + Export

- Fragment-level rights pre-screen 자동화
- C2PA export에 Canvas provenance 포함
- Meta-Council + Theory KB 감사 정례화

### 12월: Scale Readiness

- `creative_fill_rate` 30%+ 달성 검증
- 대량 프로젝트 회귀 테스트
- 운영 런북/알림 최종 확정

## 5. Immediate Backlog (Now)

1. `scripts/verify_ad_studio_future.sh`에 `fill_rate` + `continuity` 패턴 검사 고정
2. AD Studio 결과 리포트에 `creative_fill_rate` + `continuity_score` 전/후 필수 표기
3. 릴리즈 노트 템플릿에 Gate A/B/C 기본 섹션 추가
4. Sora adapter deprecation 계획 수립 (`prompt_compiler.py` `DEFAULT_ENGINES` 업데이트)
5. Blueprint Canvas schema 초안 작성 (OpenClaw Memory 저장 구조)

## 6. External Evidence (Checked on 2026-02-23)

1. Seedance 2.0 official launch: https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0
2. Kling 3.0 launch: https://www.prnewswire.com/news-releases/kuaishou-launches-kling-ai-3-0-model-and-kling-ai-studio-for-global-creators-and-businesses-302490441.html
3. Google Veo API: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation
4. DeepMind Veo: https://deepmind.google/models/veo/
5. C2PA Specs: https://c2pa.org/specifications/
6. DeepMind SynthID: https://deepmind.google/models/synthid/
7. AD Ambient Creative Canvas Vision: `docs/AD_AMBIENT_CREATIVE_CANVAS_VISION_2026_H2.md`
8. AD Co-Director OS SSOT: `docs/AD_CO_DIRECTOR_OS_SSOT_2026_H2.md`
