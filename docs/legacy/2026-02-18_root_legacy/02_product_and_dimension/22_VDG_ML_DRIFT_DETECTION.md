# VDG ML Drift Detection (P2 + P3 Self-Healing)

> **작성일**: 2026-01-19 (P3 업데이트)
> **커밋**: 697bae49
> **상태**: ✅ P2 완료, ✅ P3 완료 (Self-Healing + Health Score)

---

## 1. 개요

### 1.1 목적
VDG 분석 결과의 통계적 분포 변화(Drift)를 감지하여 모델 품질 저하를 조기에 발견합니다.

### 1.2 Drift 유형 비교

| 유형 | 설명 | 구현 상태 |
|------|------|----------|
| **Operational Drift** | 시스템 장애 (stuck, failure, retry) | ✅ P0~P1 완료 |
| **ML Model Drift** | 통계적 분포 변화 (PSI, KL Divergence) | ✅ P2 완료 |

### 1.3 왜 지금 해야 하는가?
- 91%의 ML 모델이 시간에 따라 성능 저하 (MIT & Harvard 연구)
- "Day One" 원칙: 모니터링은 배포 후가 아닌 처음부터 시작
- Baseline 확보: 지금 시작해야 나중에 drift 발생 시 비교 기준 존재

---

## 2. PSI 임계값 (업계 표준)

```
PSI < 0.1   → 정상 (No significant change)
0.1 ≤ PSI < 0.2 → 주의 (Moderate change, 모니터링 강화)
PSI ≥ 0.2  → 심각 (Significant change, 재분석/재학습 필요)
```

**PSI 공식**:
```
PSI = Σ (Current% - Reference%) × ln(Current% / Reference%)
```

---

## 3. 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     VDG ML Drift Detection                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ VDG Analysis │───▶│ Feature      │───▶│ outlier_items│      │
│  │ (Gemini)     │    │ Extractor    │    │ .vdg_feature │      │
│  └──────────────┘    └──────────────┘    │ _vector      │      │
│                                          └──────────────┘      │
│                                                 │               │
│                                                 ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Baseline     │◀───│ Histogram    │◀───│ 14일 데이터   │      │
│  │ Service      │    │ Distribution │    │ 수집         │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ vdg_drift_   │    │ Drift        │    │ Evidently AI │      │
│  │ baselines    │───▶│ Detector     │───▶│ / Manual PSI │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Celery Beat  │───▶│ Prometheus   │───▶│ Slack/Discord│      │
│  │ (Weekly)     │    │ Metrics      │    │ Alert        │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 추적 Feature 목록

| Feature | 설명 | 출처 |
|---------|------|------|
| `hook_score` | 훅 품질 점수 (0-1) | hook_analysis.score |
| `entity_count` | 감지된 엔티티 수 | entity_tracks |
| `text_density` | 텍스트 오버레이 수 | text_geometries |
| `scene_change_rate` | 씬 전환 빈도 (scenes/sec) | scenes / duration |
| `duration_seconds` | 영상 길이 | duration_seconds |
| `visual_complexity` | 시각적 복잡도 (0-1) | 가중 합산 |

---

## 5. 구현 상세

### 5.1 Database Schema

```sql
-- vdg_drift_baselines: Feature 분포 Baseline 저장
CREATE TABLE vdg_drift_baselines (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    feature_name VARCHAR(100) NOT NULL,
    baseline_distribution JSONB NOT NULL,  -- {bins, counts, mean, std, min, max}
    sample_count INT NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- vdg_drift_reports: Drift 감지 결과 히스토리
CREATE TABLE vdg_drift_reports (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    overall_drifted BOOLEAN DEFAULT FALSE,
    drifted_feature_count INT DEFAULT 0,
    total_feature_count INT DEFAULT 0,
    results JSONB  -- 상세 결과
);

-- outlier_items 확장
ALTER TABLE outlier_items ADD COLUMN vdg_feature_vector JSONB;
```

### 5.2 주요 파일

| 파일 | 설명 |
|------|------|
| `alembic/versions/drift003_vdg_ml_drift_baseline.py` | Migration |
| `app/models/vdg_drift.py` | VDGDriftBaseline, VDGDriftReport 모델 |
| `app/services/vdg_feature_extractor.py` | Feature 추출 로직 |
| `app/services/vdg_baseline_service.py` | Baseline CRUD |
| `app/services/vdg_ml_drift_detector.py` | PSI/KL 감지 (Evidently AI) |
| `app/workers/vdg_tasks.py` | Celery Beat 태스크 |
| `app/metrics/vdg_drift_metrics.py` | Prometheus 메트릭 |

### 5.3 Celery Beat 스케줄

| 태스크 | 스케줄 | 설명 |
|--------|--------|------|
| `vdg-ml-drift-weekly-report` | 월요일 00:00 UTC | 주간 drift 리포트 |
| `vdg-baseline-monthly-refresh` | 매월 1일 01:00 UTC | Baseline 갱신 |

### 5.4 Prometheus 메트릭

```python
# Gauges (현재 상태)
vdg_ml_drift_psi{feature_name="hook_score"}         # PSI 점수
vdg_ml_drift_detected{feature_name="hook_score"}    # 1=drifted, 0=stable
vdg_ml_drift_severity{feature_name="hook_score"}    # 0~3 (none/low/med/high)
vdg_baseline_sample_count{feature_name="hook_score"} # Baseline 샘플 수
vdg_ml_drift_overall                                # 전체 drift 상태
vdg_ml_drift_feature_count                          # Drift된 feature 수

# Counter (누적)
vdg_ml_drift_report_total{status="drifted|stable|error"}
```

---

## 6. 사용 예시

### 6.1 Feature 추출

```python
from app.services.vdg_feature_extractor import get_feature_extractor

extractor = get_feature_extractor()
features = extractor.extract_features(vdg_result)
# {'hook_score': 0.85, 'entity_count': 5, 'text_density': 3, ...}

quality_score = extractor.calculate_quality_score(features)
# 0.72
```

### 6.2 Baseline 생성

```python
from app.services.vdg_baseline_service import VDGBaselineService

async with async_session_maker() as db:
    service = VDGBaselineService(db)
    result = await service.create_all_baselines(period_days=14)
    # {'created_count': 6, 'baselines': [...]}
```

### 6.3 Drift 감지

```python
from app.services.vdg_ml_drift_detector import get_drift_detector

detector = get_drift_detector()
results = detector.detect_drift(reference_df, current_df)
# {
#   'overall_drifted': True,
#   'drifted_count': 2,
#   'results': [{'feature_name': 'hook_score', 'drift_score': 0.23, ...}]
# }
```

### 6.4 수동 PSI 계산

```python
import numpy as np
from app.services.vdg_ml_drift_detector import get_drift_detector

detector = get_drift_detector()
psi = detector.calculate_psi_manual(reference_values, current_values)
# 0.18 (moderate drift)
```

---

## 7. 미완료 작업

### 7.1 Admin API 엔드포인트

```python
# app/routers/admin_drift.py (생성 필요)

@router.get("/admin/vdg/ml-drift/status")
async def get_ml_drift_status():
    """현재 ML drift 상태 조회"""

@router.get("/admin/vdg/ml-drift/history")
async def get_ml_drift_history(days: int = 30):
    """ML drift 히스토리 조회"""

@router.post("/admin/vdg/ml-drift/refresh-baseline")
async def refresh_baseline(period_days: int = 14):
    """Baseline 수동 갱신"""

@router.post("/admin/vdg/ml-drift/run-detection")
async def run_drift_detection():
    """수동 drift 감지 실행"""
```

### 7.2 테스트

```python
# tests/test_vdg_ml_drift.py (생성 필요)

class TestVDGFeatureExtractor:
    def test_extract_features_from_vdg_result()
    def test_extract_features_handles_missing_fields()
    def test_visual_complexity_normalization()
    def test_quality_score_calculation()

class TestVDGMLDriftDetector:
    def test_detect_drift_with_sufficient_data()
    def test_detect_drift_insufficient_data_error()
    def test_psi_calculation_no_drift()
    def test_psi_calculation_with_drift()
    def test_severity_thresholds()

class TestVDGBaselineService:
    async def test_create_baseline()
    async def test_deactivate_old_baselines()
    async def test_get_baseline_dataframe()
```

### 7.3 VDG 분석 연동

VDG 분석 완료 시 `vdg_feature_vector` 컬럼 자동 저장 로직 추가 필요:

```python
# 기존 VDG 분석 완료 로직에 추가
from app.services.vdg_feature_extractor import get_feature_extractor

extractor = get_feature_extractor()
features = extractor.extract_features(vdg_result)
quality_score = extractor.calculate_quality_score(features)

# OutlierItem 업데이트
item.vdg_feature_vector = features
item.vdg_quality_score = quality_score  # 기존 컬럼 활용
```

---

## 8. 참고 자료

### 8.1 리서치 소스
- [Fiddler AI - Benefits of Early Monitoring](https://www.fiddler.ai/blog/3-benefits-of-model-monitoring-and-explainable-ai-before-deployment)
- [Evidently AI - Data Drift Detection](https://www.evidentlyai.com/blog/data-drift-detection-large-datasets)
- [Datadog - ML Monitoring Best Practices](https://www.datadoghq.com/blog/ml-model-monitoring-in-production-best-practices/)

### 8.2 도구 문서
- [Evidently AI Documentation](https://docs.evidentlyai.com/)
- [Prometheus Python Client](https://prometheus.github.io/client_python/)

---

## 9. P3: Self-Healing (구현 완료) ⭐ NEW

### 9.1 개요

| 단계 | 설명 | 상태 |
|------|------|------|
| P3-A | Grafana 대시보드 구축 | ✅ 완료 |
| P3-B | 자동 재분석 트리거 (PSI ≥ 0.25) | ✅ 완료 |
| P3-C | A/B 테스트와 drift 연동 | 📋 계획 |
| P3-D | WhyLabs/Arize 평가 (Enterprise 스케일 시) | 📋 계획 |

### 9.2 Self-Healing 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     VDG Self-Healing System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ ML Drift     │───▶│ Self-Healing │───▶│ CircuitBreaker│      │
│  │ Detector     │    │ Service      │    │ (5 fail/30min)│      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                                   │
│         ▼                   ▼                                   │
│  ┌──────────────┐    ┌──────────────────────────────────┐      │
│  │ PSI Score    │    │ Action by Severity                │      │
│  │ Analysis     │    │ ─────────────────────────────────│      │
│  └──────────────┘    │ PSI < 0.1  → No action           │      │
│                      │ 0.1 ≤ PSI < 0.2 → Alert only     │      │
│                      │ 0.2 ≤ PSI < 0.25 → Alert + Manual│      │
│                      │ PSI ≥ 0.25 → Auto Reanalysis ⚡   │      │
│                      └──────────────────────────────────┘      │
│                                   │                             │
│                                   ▼                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Grafana      │    │ Slack/Discord│    │ Reanalysis   │      │
│  │ Dashboard    │    │ Actions      │    │ Queue        │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 PSI 임계값 → 자동 액션

| PSI 범위 | Severity | 자동 액션 |
|----------|----------|-----------|
| < 0.1 | none | 아무 것도 안 함 |
| 0.1 ~ 0.2 | low | 알림 전송 (모니터링 강화) |
| 0.2 ~ 0.25 | medium | 알림 + 수동 재분석 버튼 |
| **≥ 0.25** | **high** | **🔧 자동 재분석 트리거** |

### 9.4 주요 파일

| 파일 | 설명 |
|------|------|
| `app/services/vdg_self_healing.py` | 🆕 Self-Healing 서비스 + Circuit Breaker |
| `monitoring/grafana/vdg_ml_drift_dashboard.json` | 🆕 Grafana 대시보드 |
| `tests/test_vdg_self_healing.py` | 🆕 Self-Healing 테스트 |
| `app/workers/vdg_tasks.py` | 🔄 ML Drift Report에 Self-Healing 통합 |

### 9.5 Circuit Breaker 패턴

연속 실패 시 자동 복구 중단으로 cascading failure 방지:

```python
from app.services.vdg_self_healing import CircuitBreaker

cb = CircuitBreaker(
    failure_threshold=5,      # 5번 실패 시 OPEN
    recovery_timeout_minutes=5, # 5분 후 HALF_OPEN
    window_minutes=30,        # 30분 윈도우
)

# States: CLOSED → OPEN → HALF_OPEN → CLOSED
```

### 9.6 사용 예시

```python
from app.services.vdg_self_healing import VDGSelfHealingService

async with async_session_maker() as db:
    service = VDGSelfHealingService(db)

    # Drift 감지 결과로 자동 복구
    result = await service.process_drift_results(
        drift_results,
        auto_heal=True  # PSI ≥ 0.25 시 자동 재분석
    )

    # 결과
    # {
    #     "status": "completed",
    #     "actions_taken": 2,
    #     "total_items_affected": 150,
    #     "circuit_breaker_state": "closed",
    #     "actions": [...]
    # }
```

### 9.7 Grafana 대시보드 (P3-A)

대시보드 위치: `monitoring/grafana/vdg_ml_drift_dashboard.json`

**패널 구성:**
- 🚨 Self-Healing Status (Overall Drift, Drifted Features, Stuck Items, Auto-Healed)
- 📊 PSI by Feature (시계열 + 바 차트)
- 🔄 Self-Healing Activity (복구 액션, 파이프라인 헬스)
- ⏱️ Analysis Performance (Duration p50/p90/p99, Completion Status)
- 📬 Alerts & Reports (발송된 알림, 리포트 히스토리)

**Import 방법:**
```bash
# Grafana UI에서 Import
1. Dashboard → Import
2. Upload JSON file 또는 내용 붙여넣기
3. Prometheus datasource 선택
```

### 9.8 Slack Interactive Buttons

수동 재분석 트리거를 위한 Slack 버튼:

```python
# 지원 액션
vdg_reanalyze_{feature_name}  # 특정 feature 재분석
vdg_dismiss_{feature_name}    # 알림 무시
vdg_baseline_refresh          # Baseline 갱신
```

### 9.9 테스트

```bash
# Self-Healing 테스트 실행
python -m pytest tests/test_vdg_self_healing.py -v

# 전체 ML Drift 테스트
python -m pytest tests/test_vdg_ml_drift.py tests/test_vdg_self_healing.py -v
```

---

## 10. 다음 단계 (P4)

| 단계 | 설명 |
|------|------|
| P4-A | A/B 테스트와 drift 연동 |
| P4-B | WhyLabs/Arize 평가 (Enterprise 스케일 시) |
| P4-C | Auto-rollback (심각한 drift 시 이전 모델로 롤백) |

---

## 11. 참고 자료 (Self-Healing)

- [2026 Kubernetes Playbook: AI at Scale, Self-Healing Clusters](https://www.fairwinds.com/blog/2026-kubernetes-playbook-ai-self-healing-clusters-growth)
- [Kill the Pager: Auto-Remediation Guide](https://medium.com/@anudeepballa7/kill-the-pager-a-practical-guide-to-auto-remediation-and-self-healing-systems-f1507343f9f2)
- [MLOps: Model Drift Detection and Automated Retraining](https://enhancedmlops.com/advanced-ml-model-monitoring-drift-detection-explainability-and-automated-retraining/)
- [Boxkite ML Drift Monitoring](https://github.com/boxkite-ml/boxkite)
