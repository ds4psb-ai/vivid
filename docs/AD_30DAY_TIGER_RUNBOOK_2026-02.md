# AD Co-Director + Original-IP Foundry 30-Day Tiger Runbook (2026-02)

> Version: 1.0  
> Owner: VIVID Product / Platform  
> Scope: 30일 내 Launch Candidate 확보

---

## 1) 목적

90일 플랜을 30일로 압축해, 다음 3가지를 동시에 달성한다.

1. 연속성 중심 조감독 추천 시스템 가동
2. Masterpiece Pattern 데이터 자산 축적(패턴 원자화)
3. 합법 재창조를 위한 Rights Graph + clone_risk 게이트 운영

---

## 2) 운영 모델 (Codex 5.3 + Opus 4.6 풀가동)

### 2.1 역할 분리

- **Codex 5.3 Terminal Lane**
  - 코드 구현/테스트 생성/리팩터 자동화
  - 반복 작업(계약 테스트/스키마 동기화/스크립트 보강) 집중
- **Opus 4.6 Review Lane**
  - 아키텍처/리스크/권리 정책 검토
  - 랭킹 수식/실험 설계/문서 SSOT 품질 점검

### 2.2 1일 실행 루프

1. 09:00-09:20: KPI 브리핑(continuity, pattern reuse, clone risk, p95)
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

### Day 3-9: Foundation
- Rights Graph + pre/post gate
- Qdrant 4-컬렉션
- OpenClaw/Agent0 포트 연결
- Masterpiece ingestion v0 (1,000 클립)

### Day 10-16: Intelligence
- Pattern Atom 추출
- ranking v2 (pattern_affinity, clone_risk)
- A/B + Thompson 운영 시작

### Day 17-23: B2C 채널
- Telegram/WebChat 안정화
- Kakao adapter 베타
- 이벤트 유실/중복 모니터링

### Day 24-30: Launch
- Vendor switch drill
- near-duplicate 차단 자동화
- 런북/권리분쟁 대응서 완성
- 파일럿 유료/LOI 확보

---

## 4) 저장소 전략 (질문 답변)

### 결론

**지금은 새 프로젝트를 파지 말고 VIVID 안에서 만드는 게 맞다.**

### 이유

1. 30일 내 출시에서 기존 인증/크레딧/UI/모니터링 자산 재사용이 필수
2. 새 프로젝트는 CI/CD/권한/운영 도구를 다시 세팅해야 해 속도 손실 큼
3. 벤더 락인 우려는 “레포 분리”가 아니라 Port/Adapter/Contract Test로 해소 가능

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

---

## 5.1 A-Prime 운영 규약 (옵션 A 실전판)

“플래그 없이 바로 붙인다” 대신, **최소 브레이크**만 둔 운영 규약.

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

- 추천 API p95 < 2.5s
- 검색 p95 < 900ms
- continuity >= 0.80 추천 비율 60%+
- pattern_atoms 10,000+
- pattern_reuse_rate 25%+
- pattern 적용군 continuity uplift +0.08+
- 유료 파일럿 또는 LOI 확보

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
10. Qdrant update vectors API (ordering/wait): https://api.qdrant.tech/v-1-14-x/api-reference/points/update-vectors
11. Qdrant update points API (ordering/wait): https://api.qdrant.tech/v-1-14-x/api-reference/points/set-payload
12. Qdrant points concepts: https://qdrant.tech/documentation/concepts/points/
13. Taskiq docs: https://taskiq-python.github.io/
14. Taskiq package: https://pypi.org/project/taskiq/
15. C2PA specification 2.2: https://spec.c2pa.org/specifications/specifications/2.2/specs/C2PA_Specification.html
16. C2PA open-source docs: https://opensource.contentauthenticity.org/docs/
17. EU AI Act timeline: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
