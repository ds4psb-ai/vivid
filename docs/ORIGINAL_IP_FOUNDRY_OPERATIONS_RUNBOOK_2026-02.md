# Original-IP Foundry Operations Runbook (2026-02)

> 목적: A-Prime 운영 규약 기반으로 Foundry를 빠르게 배포하되, 장애/오용 시 10분 내 차단·복구한다.

---

## 1) 즉시 전환 가능한 운영 플래그

```bash
AD_FOUNDRY_ENABLED=true|false
AD_FOUNDRY_WRITE_ENABLED=true|false
AD_FOUNDRY_ACCESS_SCOPE=internal|authenticated|public
AD_FOUNDRY_ALLOWLIST=comma,separated,emails
AD_FOUNDRY_READONLY_SAFE_PATHS=/api/v1/foundry/...,/api/v1/foundry/provenance/export-c2pa,/api/v1/foundry/workers/dispatch,/api/v1/foundry/workers/jobs
```

- **긴급 차단(권장 1순위)**: `AD_FOUNDRY_ENABLED=false`
- **쓰기 차단(2순위)**: `AD_FOUNDRY_WRITE_ENABLED=false`
- **접근 축소(3순위)**: `AD_FOUNDRY_ACCESS_SCOPE=internal` + allowlist 최소화

---

## 2) 단계적 공개 규약

1. **Stage R (Read-only)**  
   - `WRITE_ENABLED=false`  
   - 읽기/추천/평가용 POST만 허용 (safe path whitelist)
2. **Stage W (Limited write)**  
   - 운영 KPI 통과 시 `WRITE_ENABLED=true`  
   - 내부 승인 플로우 유지
3. **Stage GA (Authenticated public)**  
   - `ACCESS_SCOPE=authenticated`  
   - 로그인 사용자에게 공개

---

## 2.1 Qdrant 동시성 제어 규약

Foundry 패턴/전이 룰 업서트는 아래 규약을 따른다.

1. payload에 `revision` 필드 유지 (optimistic concurrency)
2. 요청에 `expected_revision`을 포함해 충돌 감지
3. Qdrant write는 `wait=true`, `ordering=strong` 사용
4. 충돌 시 즉시 실패 처리(`status=conflict`) 후 재시도 큐 전송

---

## 2.2 Worker Port 전환 규약 (Agent0 ↔ Taskiq ↔ Temporal)

1. 기본 실행체는 `Agent0WorkerProvider`
2. 병목/장애 시 `TaskiqWorkerProvider` 또는 `TemporalWorkerProvider`로 전환 가능해야 함
3. 분기별 1회 스위치 드릴에서 아래 3개 검증:
   - dispatch_job 성공
   - status 조회 가능
   - cancel 흐름 정상
4. status/cancel은 `tenant_id + project_id` 스코프 파라미터를 필수로 전달한다.
5. 스코프 불일치 시 API는 403(`tenant scope mismatch` 또는 `project scope mismatch`)를 반환해야 한다.

---

## 3) 관측성 스키마 (필수)

`foundry.audit` 로그에 아래 필드를 고정한다.

- `path`
- `method`
- `user`
- `model`
- `input_type`
- `latency_ms`
- `status_code`
- `failure_code`
- `block_reason`

오류/차단 시 `failure_code`, `block_reason` 누락 금지.
권장: C2PA export 호출은 `input_type=provenance`로 고정해 추적한다.

---

## 4) 사고 대응 10분 플레이북

### 0~2분
- 증상 확인: 5xx 급증, 403 급증, 권리 게이트 오판, 지연 p95 급등
- 즉시 `AD_FOUNDRY_ENABLED=false` 적용

### 2~5분
- `foundry.audit` 최근 100건 확인
- 차단 사유 상위 3개, 실패 코드 상위 3개 추출

### 5~10분
- 원인 분류: 권리정책/데이터/모델/라우팅/인증
- 임시 조치:
  - 정책 오판: `ACCESS_SCOPE=internal`로 축소
  - 품질 저하: 추천 endpoint hold 강제
  - 과부하: 배치 큐/실시간 분리 확인

---

## 5) GA 직전 체크리스트

- [ ] `/api/v1/foundry/health` 정상
- [ ] `/api/v1/foundry/status`에서 접근/쓰기 플래그 기대값 확인
- [ ] `/api/v1/foundry/workers/providers`에서 active provider 확인
- [ ] `/api/v1/foundry/workers/jobs/{job_id}` status 조회 시 tenant/project 스코프 강제 확인
- [ ] 권리 평가 응답에 `decision/reason_codes/per_asset` 포함
- [ ] 추천 응답에 `continuity_score/rights_decision/recommendation_rationale` 포함
- [ ] A/B 이벤트 집계에서 variant별 accept/edit/reject rate 노출
- [ ] `/api/v1/foundry/provenance/export-c2pa` 응답에 `spec_version/manifest/compliance` 포함
- [ ] 장애 롤백 리허설 1회 완료
