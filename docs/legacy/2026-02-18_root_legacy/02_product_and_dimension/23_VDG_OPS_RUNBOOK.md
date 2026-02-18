# VDG Ops Runbook (운영 매뉴얼)

> **작성일**: 2026-01-19
> **상태**: Production Ready
> **담당**: 자동화 (Celery Beat)

---

## 1. 시스템 개요

### 1.1 VDG 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        VDG Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Ops 영역 - 내부 운영]                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Outlier      │───▶│ VDG Analysis │───▶│ Drift        │       │
│  │ Discovery    │    │ (Gemini)     │    │ Detection    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                             │                    │                │
│                             ▼                    ▼                │
│                      ┌──────────────┐    ┌──────────────┐       │
│                      │ Self-Healing │◀───│ PSI Monitor  │       │
│                      │ (Auto-fix)   │    │ (Weekly)     │       │
│                      └──────────────┘    └──────────────┘       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Lab 영역 - 사용자]                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Lab Items    │───▶│ Pattern      │───▶│ Remix        │       │
│  │ (완료된 VDG) │    │ Discovery    │    │ Suggestion   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Ops vs Lab 분리

| 영역 | 용도 | 데이터 | 영향 범위 |
|------|------|--------|----------|
| **Ops** | 내부 운영/모니터링 | 모든 상태 (pending, analyzing, failed 포함) | Admin only |
| **Lab** | 사용자 패턴 해석 | `completed` 상태만 | 일반 사용자 |

**핵심**: Ops의 장애/재분석이 Lab 사용자 경험에 영향 없음

---

## 2. 자동화 스케줄 (Celery Beat)

### 2.1 실행 일정

| 태스크 | 주기 | 시간 (UTC) | 설명 |
|--------|------|-----------|------|
| `run_stuck_recovery` | **매 15분** | */15 | stuck 항목 복구 (15분 임계값) |
| `run_reanalysis_queue` | **매 30분** | */30 | 재분석 큐 처리 (backoff 적용) |
| `send_drift_report` | 매일 | 00:00 | 일일 drift 리포트 |
| `run_ml_drift_report` | 매주 월요일 | 00:00 | PSI 기반 drift 리포트 |
| `refresh_baseline` | 매월 1일 | 01:00 | Baseline 갱신 |

> ⚠️ **Beat 스케줄러 필수**: 위 태스크들은 `-B` 플래그로 Beat 실행 시에만 작동

### 2.2 스케줄 설정 위치

```python
# backend/app/workers/celery_app.py
celery_app.conf.beat_schedule = {
    "vdg-stuck-recovery": {
        "task": "app.workers.vdg_tasks.run_stuck_recovery",
        "schedule": crontab(minute="*/15"),  # 매 15분
        "kwargs": {"threshold_minutes": 15, "limit": 100},
    },
    "vdg-reanalysis-queue": {
        "task": "app.workers.vdg_tasks.run_reanalysis_queue",
        "schedule": crontab(minute="*/30"),  # 매 30분
    },
    "vdg-ml-drift-weekly": {
        "task": "app.workers.vdg_tasks.run_ml_drift_report",
        "schedule": crontab(hour=0, minute=0, day_of_week=1),  # 월요일 00:00 UTC
    },
    ...
}
```

> 🚨 **CRITICAL**: Worker 시작 시 `-B` 플래그 필수!
> ```bash
> celery -A app.workers.celery_app worker -B -Q vdg,maintenance ...
> ```

---

## 3. Health Score 모니터링

### 3.1 Health Score 공식

```
Health Score = 100 - (stuck_penalty + drift_penalty + failure_penalty)

- stuck_penalty: min(stuck_count × 5, 30)      # 최대 30점 감점
- drift_penalty: min(drifted_count × 10, 30)   # 최대 30점 감점
- failure_penalty: min(permanent_count × 10, 40) # 최대 40점 감점
```

### 3.2 상태 해석

| Score | 상태 | 의미 | 조치 |
|-------|------|------|------|
| 80-100 | 🟢 Green | 정상 | 없음 |
| 60-79 | 🟡 Yellow | 주의 | 모니터링 강화 |
| 0-59 | 🔴 Red | 심각 | 즉시 확인 필요 |

### 3.3 Prometheus 메트릭

```
vdg_health_score                    # 0-100 종합 점수
vdg_ml_drift_psi{feature_name}      # 피처별 PSI
vdg_ml_drift_overall                # 전체 drift 여부 (1/0)
vdg_stuck_items_total               # stuck 항목 수
vdg_failed_permanent_items_total    # 영구 실패 항목 수
vdg_recovery_success_total          # 복구 성공 누적
vdg_recovery_failure_total          # 복구 실패 누적
vdg_recovery_batch_size             # 복구 배치 크기 분포
```

### 3.4 실시간 Health Score 업데이트 (하드닝)

**이전**: 주 1회 (ML Drift Report 시)
**현재**: 매시간 (Stuck Recovery 후 즉시 갱신)

```python
# vdg_tasks.py - run_stuck_recovery_task
drift_stats = await drift_svc.get_drift_statistics()
update_drift_metrics(drift_stats)
health_score = calculate_vdg_health_score(health_stats)
record_recovery_batch(recovered_count, failed_permanent_count)
```

**효과**:
- Grafana 대시보드 실시간 반영
- 장애 발생 시 즉시 Health Score 하락
- 복구 완료 시 즉시 Health Score 회복

---

## 4. PSI 기반 Self-Healing

### 4.1 PSI 임계값 및 자동 대응

| PSI 범위 | 심각도 | 자동 조치 |
|----------|--------|----------|
| < 0.1 | None | 없음 |
| 0.1 - 0.2 | Low | Slack 알림 (모니터링) |
| 0.2 - 0.25 | Medium | Slack 알림 + 수동 버튼 |
| ≥ 0.25 | High | **자동 재분석 100건** |

### 4.2 Anti-Loop 보호 (하드닝)

**문제**: 매주 같은 항목이 반복 재분석될 위험

**해결**: 최근 7일 내 재분석된 항목 자동 제외

```python
# vdg_self_healing.py - 재분석 대상 선택 시
or_(
    OutlierItem.last_retry_at.is_(None),        # 한번도 재분석 안됨
    OutlierItem.last_retry_at < 7일_전_cutoff,   # 7일 이상 경과
)
```

**효과**:
- 같은 항목 무한 재분석 방지
- 새로 분석된 항목 우선 처리
- 시스템 리소스 낭비 방지

### 4.3 Circuit Breaker

```
연속 5회 실패 (30분 내) → OPEN (차단)
    ↓ 5분 대기
HALF_OPEN (테스트)
    ↓ 1회 성공
CLOSED (정상)
```

**목적**: 연쇄 장애 방지 (runaway remediation 차단)

### 4.3 코드 위치

```
backend/app/services/vdg_self_healing.py
├── CircuitBreaker          # 차단기 로직
├── VDGSelfHealingService   # 자동 대응 서비스
└── handle_slack_interaction # Slack 버튼 핸들러
```

---

## 5. 문제 해결 가이드

### 5.1 Baseline 없음 (no_baseline)

**증상**: Drift report에서 `"error": "no_baseline"` 반환

**원인**: 30개 이상의 완료된 VDG 분석 결과 없음

**해결**:
```bash
# 현재 완료된 분석 수 확인
SELECT COUNT(*) FROM outlier_items
WHERE analysis_status = 'completed'
AND vdg_feature_vector IS NOT NULL;

# 30개 이상이면 수동 baseline 생성
python -c "
from app.services.vdg_baseline_service import VDGBaselineService
# ... create_all_baselines()
"
```

**자동 해결**: 30개 이상 누적되면 다음 주 월요일에 자동 생성됨

### 5.2 stuck 항목 급증

**증상**: `vdg_stuck_items_total` > 10

**원인**:
- Gemini API 장애
- 네트워크 타임아웃
- 대용량 영상 처리 지연
- **httpx 시스템 프록시 상속** (2026-01-23 수정) - `trust_env=True`로 Railway 프록시 DNS 해석 실패
- **배포/재시작 시 백그라운드 태스크 중단** - `analyzing` 상태로 영구 stuck

**자동 복구 (v1.5 Beat + Self-Healing)**:
- `analyzing` 상태가 **15분 이상** stuck되면 Beat 스케줄러가 자동 복구
- `vdg_stuck_recovery.py`에서 `STUCK_THRESHOLD_MINUTES = 15` 적용
- ⚠️ **Beat 스케줄러 필수** - Worker 시작 시 `-B` 플래그 없으면 자동 복구 작동 안함

**해결**:
```bash
# stuck 항목 확인
SELECT id, video_url, stuck_at
FROM outlier_items
WHERE analysis_status = 'analyzing'
AND stuck_at < NOW() - INTERVAL '15 minutes';

# 수동 리셋 (self-healing 트리거)
UPDATE outlier_items
SET analysis_status = 'pending', stuck_at = NULL
WHERE analysis_status = 'analyzing'
AND stuck_at < NOW() - INTERVAL '15 minutes';

# 또는 API 호출
curl -X POST /api/v1/admin/vdg/recover-stuck
```

### 5.2.1 TikTok/YouTube 다운로드 실패 ⭐ NEW (2026-01-23)

**증상**:
- TikTok: `SocksHTTPSConnection: No address associated with hostname`
- YouTube: `No frames were processed (0/N)`

**원인**: httpx 클라이언트가 시스템 프록시(`HTTP_PROXY`, `ALL_PROXY`)를 상속하여 Railway 네트워크에서 DNS 해석 실패

**수정 (v1.4)**:
```python
# app/utils/http_client.py
return httpx.AsyncClient(
    trust_env=False,  # 시스템 프록시 상속 비활성화
    ...
)
```

**확인**:
```python
# Railway 환경에서 프록시 체크
import os
print(os.getenv("HTTP_PROXY"), os.getenv("HTTPS_PROXY"), os.getenv("ALL_PROXY"))
# 모두 None이어야 정상
```


### 5.3 Circuit Breaker OPEN

**증상**: Self-healing이 작동하지 않음

**원인**: 연속 5회 self-healing 실패

**해결**:
1. Slack 알림 확인 (실패 원인)
2. 근본 원인 해결 (Gemini API, DB 등)
3. 5분 후 자동으로 HALF_OPEN 전환
4. 또는 서비스 재시작으로 초기화

### 5.4 TikTok 댓글 추출 실패 (comments_failed) ⭐ NEW

**증상**: `comments_failed` 또는 `comments_pending_review` 상태로 멈춤

**원인**:
- TikTok 쿠키 만료 또는 부재
- Railway 서버에 로컬 브라우저 없음 (`browser_cookie3` 실패)
- `TIKTOK_COOKIE_BASE64` 환경변수 미설정 또는 만료

**자동 복구 (Self-Healing v5.0.8)**:
- `tiktok_extractor.py` / `comment_extractor.py`에서 자동 쿠키 재생성
- `vdg_reanalysis_queue.py`에서 30분마다 재시도 (5/15/45분 backoff)

**수동 복구**:
```bash
# 1. 쿠키 강제 갱신
POST /api/v1/admin/cookies/force-bootstrap

# 2. 쿠키 상태 확인
GET /api/v1/admin/cookies/status

# 3. Railway 환경변수 업데이트 (쿠키 만료 시)
cat backend/tiktok_cookies_auto.json | base64 | tr -d '\n'
# → Railway Dashboard에서 TIKTOK_COOKIE_BASE64 업데이트
```

### 5.5 유효한 analysis_status 값 ⭐ NEW (2026-01-26)

> 🚨 **CRITICAL**: 존재하지 않는 상태값을 사용하면 Worker가 픽업하지 않습니다!

**유효한 상태값 (코드 기준)**:

| 상태 | 설명 | Worker 픽업 |
|------|------|-------------|
| `pending` | 분석 대기 | ✅ 픽업됨 |
| `analyzing` | 분석 중 | ❌ (진행 중) |
| `completed` | 분석 완료 | ❌ (완료) |
| `failed` | 일시적 실패 (재시도 가능) | ✅ 재시도 |
| `failed_permanent` | 영구 실패 | ❌ |
| `comments_failed` | 댓글 추출 실패 | ✅ 자동 재시도 |
| `comments_pending_review` | 댓글 검토 대기 | ✅ 자동 재시도 |

**⚠️ 존재하지 않는 상태값:**
- ❌ `pending_reanalysis` - 존재하지 않음! `pending`으로 설정해야 함
- ❌ `reanalyzing` - 존재하지 않음!

**재분석 트리거 방법:**
```sql
-- ✅ 올바른 방법: pending으로 설정
UPDATE outlier_items
SET analysis_status = 'pending', retry_count = 0
WHERE id = '<item_id>';

-- ❌ 잘못된 방법: 없는 상태값 사용
UPDATE outlier_items
SET analysis_status = 'pending_reanalysis' -- Worker가 픽업 안 함!
WHERE id = '<item_id>';
```

### 5.6 VDG 데이터 있는데 failed 상태 ⭐ NEW (2026-01-26)

**증상**: `analysis_status = 'failed_permanent'`인데 `remix_nodes.gemini_analysis`에 VDG 데이터 존재

**원인**:
- VDG 분석은 성공했으나 post-processing (hook 클러스터링 등) 중 에러 발생
- 에러 핸들링에서 상태를 `failed_permanent`로 마킹

**진단:**
```sql
-- VDG 데이터 존재 확인
SELECT
    oi.id,
    oi.title,
    oi.analysis_status,
    rn.gemini_analysis IS NOT NULL as has_vdg,
    rn.gemini_analysis->'semantic'->'hook_genome'->>'hook_summary' as hook_summary
FROM outlier_items oi
LEFT JOIN remix_nodes rn ON oi.promoted_to_node_id = rn.id
WHERE oi.analysis_status = 'failed_permanent'
AND rn.gemini_analysis IS NOT NULL;
```

**해결:**
```sql
-- VDG 데이터가 있으면 completed로 수정
UPDATE outlier_items
SET analysis_status = 'completed', last_error = NULL
WHERE id = '<item_id>';

-- 그 후 hook 클러스터링 수동 실행 (Railway 콘솔)
python -c "
import asyncio
from app.database import async_session_maker
from app.services.hook_clustering import assign_hook_cluster_to_outlier

async def fix():
    async with async_session_maker() as db:
        await assign_hook_cluster_to_outlier(
            db=db,
            outlier_id='<item_id>',
            hook_summary='<hook_summary from VDG>',
            hook_type='<hook_type>',
            hook_attributes={...}
        )
asyncio.run(fix())
"
```

---

## 6. Slack 알림 채널

### 6.1 알림 종류

| 알림 | 채널 | 심각도 |
|------|------|--------|
| Drift 감지 | #vdg-alerts | warning/critical |
| Self-healing 완료 | #vdg-alerts | info |
| Circuit Breaker 열림 | #vdg-alerts | critical |

### 6.2 Interactive Buttons

| 버튼 | Action ID | 기능 |
|------|-----------|------|
| 재분석 | `vdg_reanalyze_{feature}` | 해당 피처 관련 항목 재분석 |
| 무시 | `vdg_dismiss_{feature}` | 알림 닫기 |
| Baseline 갱신 | `vdg_baseline_refresh` | 즉시 baseline 갱신 |

---

## 7. Grafana 대시보드

### 7.1 Import 방법

```bash
# 대시보드 파일 위치
backend/monitoring/grafana/vdg_ml_drift_dashboard.json

# Grafana UI에서
1. Dashboard → Import
2. Upload JSON file
3. Prometheus datasource 선택
```

### 7.2 주요 패널

| 패널 | 설명 |
|------|------|
| Health Score | 종합 건강 점수 (0-100) |
| PSI by Feature | 피처별 PSI 값 |
| Self-Healing Activity | 자동 복구 활동 |
| Analysis Performance | 분석 소요 시간 분포 |

---

## 8. 데이터베이스 테이블

### 8.1 VDG 관련 테이블

```sql
-- 분석 항목 (Ops + Lab 공용)
outlier_items
├── analysis_status   -- pending/analyzing/completed/failed_*
├── vdg_feature_vector -- JSONB (6개 피처)
├── retry_count       -- 재시도 횟수 (max 3)
└── stuck_at          -- stuck 감지 시간

-- Drift 감지 (Ops only)
vdg_drift_baselines   -- 피처별 baseline 분포
vdg_drift_reports     -- 주간 drift 리포트
```

### 8.2 인덱스

```sql
-- 성능 최적화 인덱스 (이미 존재)
ix_outlier_items_analysis_status
ix_vdg_drift_baselines_feature_active
```

---

## 9. 긴급 연락처

| 상황 | 담당 | 조치 |
|------|------|------|
| Drift Critical | #vdg-alerts | Slack 알림 자동 |
| 시스템 장애 | 온콜 담당자 | PagerDuty |
| 기능 문의 | 개발팀 | Slack #dev |

---

## 10. Postmortem: Beat 스케줄러 미실행 사건 (2026-01-26)

### 🚨 사건 요약

**증상**: VDG 분석 아이템들이 "analyzing" 상태에서 몇 시간~며칠 stuck
**기간**: ~1주일
**근본 원인**: Celery Worker 시작 명령에 `-B` 플래그 누락 → Beat 스케줄러 미실행

### 영향

```
Stuck Recovery Task (15분마다) ─┐
                                ├─ 둘 다 Celery Beat 필요
Reanalysis Queue Task (30분마다)─┘

Beat 없이는 → 두 태스크 모두 실행 안됨 → 아이템 영원히 stuck
```

### 교훈

1. **`-B` 플래그는 필수** - Beat 스케줄러 없이 Worker만 실행하면 모든 자동화가 작동하지 않음
2. **문서화 부재** - Railway 배포 가이드에 `-B` 필수성이 명시되지 않았음
3. **모니터링 부재** - Beat 스케줄러 실행 여부를 확인하는 alert 없었음

### 수정 사항

| 항목 | 이전 | 이후 |
|------|------|------|
| Railway 시작 명령 | `worker -Q ...` | `worker -B -Q ...` |
| Stuck 감지 임계값 | 30분 | **15분** |
| 문서화 | 미흡 | `27_WORKER_ARCHITECTURE.md` 경고 추가 |

### 재발 방지

- [ ] Railway Worker 헬스체크에 "Beat 실행 중" 확인 추가
- [ ] Grafana alert: "15분간 stuck_recovery 실행 기록 없음" 추가

---

## 11. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-26 | 1.6 | **§5.5/5.6 추가**: 유효한 analysis_status 값 문서화, VDG 데이터 있는데 failed 상태 트러블슈팅 |
| 2026-01-26 | 1.5 | **P0 Postmortem**: Beat 스케줄러 미실행 사건 기록, stuck 감지 30분→15분 단축 |
| 2026-01-23 | 1.4 | **P0 Fixes**: `trust_env=False` httpx 시스템 프록시 차단, Self-healing 30분 타임아웃 'analyzing' 복구 |
| 2026-01-21 | 1.3 | **TikTok Self-Healing**: 쿠키 자동 복구, comments_failed 재시도 문서화 |
| 2026-01-19 | 1.2 | **하드닝**: Anti-Loop 보호, 실시간 Health Score, Recovery 메트릭 |
| 2026-01-19 | 1.1 | Health Score, Self-Healing 추가 |
| 2026-01-19 | 1.0 | 초기 문서 작성 |
