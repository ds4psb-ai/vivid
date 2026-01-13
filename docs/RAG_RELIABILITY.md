# RAG Reliability Guide

> **Status**: Production  
> **Last Updated**: 2026-01-11  
> **Based on**: 2025 RAG Best Practices Research

## Overview

Vivid의 Hybrid RAG 시스템 신뢰도 확보를 위한 가이드입니다.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ L0: Semantic Cache (pgvector + Memory LRU)                  │
│     Target: 30-50% cache hit rate                           │
├─────────────────────────────────────────────────────────────┤
│ L1: NotebookLM Playwright (거장 DNA)                         │
│     Circuit Breaker: 3 failures → 60s cooldown              │
├─────────────────────────────────────────────────────────────┤
│ L2: Vertex AI RAG (VDG + BM25/Vector RRF)                   │
├─────────────────────────────────────────────────────────────┤
│ L3: Google Search Grounding (실시간 정보)                    │
└─────────────────────────────────────────────────────────────┘
```

## Reliability Patterns

### 1. Circuit Breaker

NotebookLM RPC가 불안정할 때 빠른 실패 및 폴백:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=3, recovery_timeout=60)
async def query_notebooklm(query: str, auteur_key: str):
    return await _playwright_query(query, auteur_key)
```

| State | 동작 |
|-------|------|
| Closed | 정상 요청 처리 |
| Open | 즉시 실패, Vertex AI 폴백 |
| Half-Open | 테스트 요청 허용 |

### 2. Multi-Layer Caching

| Layer | 저장소 | TTL | 용도 |
|-------|--------|-----|------|
| L1 | In-Memory LRU | 1h | Hot queries |
| L2 | PostgreSQL + pgvector | 1-7d | Persistent |

**pgvector 인덱스** (조회 10x 가속):
```sql
CREATE INDEX idx_semantic_cache_embedding 
ON rag_semantic_cache 
USING ivfflat (query_embedding vector_cosine_ops) 
WITH (lists = 100);
```

### 3. Fallback Chain

```
Query
  │
  ├─ L0: Cache Hit? → Return
  │
  ├─ L1: NotebookLM
  │      ├─ RPC 성공 → Return
  │      ├─ RPC 실패 → UI Fallback
  │      └─ Circuit Open → Skip
  │
  ├─ L2: Vertex AI RAG
  │      └─ BM25 + Vector RRF
  │
  └─ L3: Google Search (CRAG pattern)
         └─ confidence < 0.5 시 자동 활성화
```

## App RAG Configuration

### RAG Mode 선택 가이드

| Mode | 조건 | 예시 앱 |
|------|------|---------|
| `always` | 항상 RAG 필요 | AD, Story, QC |
| `auteur_only` | 거장 키 있을 때만 | 1D, 2D, 3D, VEO |
| `never` | RAG 불필요 | AI, Sound |

### YAML 설정

```yaml
capabilities:
  - name: rag
    enabled: true
    config:
      mode: auteur_only
      auteur_mode: true
      confidence_threshold: 0.7
      cache_ttl: 3600
      retrieval:
        strategy: hybrid  # hybrid | vector | keyword
        top_k: 10
        rrf_k: 60
```

### TTL Override Precedence (P6-4)

캐시 TTL은 다음 우선순위로 결정됩니다:

| 순위 | 소스 | 예시 |
|------|------|------|
| 1 | 함수 인자 `cache_ttl` | `cache.set(..., cache_ttl=7200)` |
| 2 | YAML `capabilities.rag.config.cache_ttl` | `cache_ttl: 3600` |
| 3 | 동적 계산 `_calculate_ttl()` | auteur=7일, grounded=1일, default=1시간 |

> **P6 참고**: `semantic_cache.set()`에서 `cache_ttl` 인자가 명시되면 YAML/동적 계산을 무시합니다.

## Monitoring

### Key Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Cache Hit Rate | 30-50% | < 20% |
| NotebookLM Latency | < 15s | > 30s |
| Circuit Open Events | 0/day | > 3/hour |

### Log Patterns

```bash
# 성공
[HybridRAG] SEMANTIC_CACHE HIT | query='...' | confidence=0.95
[NotebookLM-Playwright] Got answer via UI after 5s (250 chars)

# 폴백
[NotebookLM-Playwright] RPC query failed. Trying UI fallback...
[HybridRAG] NotebookLM circuit open, falling back to Vertex AI
```

## Observability & SLOs (2025 Best Practices)

### PromQL Queries for Grafana

#### Latency Percentiles

```promql
# p50 RAG Latency by Dimension (e2e)
histogram_quantile(0.50, sum(rate(rag_query_latency_ms_bucket[5m])) by (le, dimension))

# p95 RAG Latency by Dimension (e2e)
histogram_quantile(0.95, sum(rate(rag_query_latency_ms_bucket[5m])) by (le, dimension))

# p99 RAG Latency (overall)
histogram_quantile(0.99, sum(rate(rag_query_latency_ms_bucket[5m])) by (le))
```

#### Cache-Hit vs Live Latency (Medium Fix)

```promql
# p95 Cache HIT Latency (semantic_cache strategy only)
# NOTE: Filter by strategy label when available in rag_query_latency_ms
# Use semantic_cache_latency_ms for more precise cache-only timing:
histogram_quantile(0.95, sum(rate(rag_semantic_cache_latency_ms_bucket{operation="get"}[5m])) by (le))

# p95 Stage Latency by Operation (separate from e2e)
histogram_quantile(0.95, sum(rate(rag_stage_latency_ms_bucket[5m])) by (le, stage))
```

#### Error Rate

```promql
# Error Rate by Dimension (errors per second)
sum(rate(rag_errors_total[5m])) by (dimension, error_type)

# Error Ratio (%)
sum(rate(rag_errors_total[5m])) / sum(rate(rag_query_total[5m])) * 100
```

#### Cache Performance

```promql
# Cache Hit Rate (%)
sum(rate(rag_semantic_cache_ops_total{result=~"exact|semantic"}[5m])) 
  / sum(rate(rag_semantic_cache_ops_total{operation="get"}[5m])) * 100

# Cache Hit by Type
sum(rate(rag_semantic_cache_ops_total{operation="get"}[5m])) by (result)
```

#### Circuit Breaker

```promql
# Circuit Open Events
sum(increase(rag_circuit_breaker_state_total{state="open"}[1h]))

# Backend Failures by Service
sum(rate(rag_circuit_breaker_failures_total[5m])) by (backend)
```

### SLO Targets

| SLO | Target | Alert Threshold |
|-----|--------|-----------------|
| p95 Latency (cache hit) | < 500ms | > 1s |
| p95 Latency (live RAG) | < 5s | > 10s |
| Error Rate | < 1% | > 5% |
| Cache Hit Rate | 30-50% | < 20% |
| Circuit Open | < 3/day | > 5/hour |

### Grafana Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ROW 1: Global Status                                        │
├───────────────┬───────────────┬─────────────────────────────┤
│ Error Rate %  │ Cache Hit %   │ p95 Latency (overall)       │
│ (stat panel)  │ (gauge)       │ (time series)               │
├───────────────┴───────────────┴─────────────────────────────┤
│ ROW 2: Latency Details                                      │
├─────────────────────────────────────────────────────────────┤
│ p50/p95/p99 Latency by Dimension (time series + heatmap)    │
├─────────────────────────────────────────────────────────────┤
│ ROW 3: Components                                           │
├───────────────┬───────────────┬─────────────────────────────┤
│ NotebookLM    │ Vertex AI     │ Cache Ops                   │
│ (circuit/err) │ (latency)     │ (hit/miss breakdown)        │
├───────────────┴───────────────┴─────────────────────────────┤
│ ROW 4: Alerts & Events                                      │
│ Circuit Breaker State Changes (annotations)                 │
└─────────────────────────────────────────────────────────────┘
```

### Histogram Bucket Configuration (Optimized)

```python
# metrics.py - 권장 bucket (long-tail 커버)
_rag_latency = Histogram(
    "rag_query_latency_ms",
    "RAG query latency (ms)",
    ["dimension"],
    buckets=[25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000]
)
```

---

## Grafana Dashboard Import

### JSON File Location
[`config/grafana/rag_overview.json`](file:///Users/ted/vivid/config/grafana/rag_overview.json)

### Import Steps
1. Open Grafana → Dashboards → Import
2. Upload JSON file or paste contents
3. Select Prometheus datasource for `${DS_PROMETHEUS}`
4. Click Import

### Dashboard Panels (15)
| Row | Panel | Type |
|-----|-------|------|
| Global Status | Error Rate % | stat |
| | Cache Hit Rate % | gauge |
| | p95 Latency | timeseries |
| Latency Details | Latency by Dimension (p50/p95) | timeseries |
| | Stage Latency (p95) | timeseries |
| Router Decisions | Strategy Distribution | piechart |
| | Score Distribution | histogram |
| | Cache Hit Types | barchart |
| Errors | Errors by Dimension | timeseries |
| | Circuit Breaker Events | stat |
| | Backend Failures | timeseries |

---

## Related Files

- [hybrid_rag.py](file:///Users/ted/vivid/backend/app/rag/hybrid_rag.py)
- [tier0_notebooklm.py](file:///Users/ted/vivid/backend/app/rag/tier0_notebooklm.py)
- [semantic_cache.py](file:///Users/ted/vivid/backend/app/rag/semantic_cache.py)
- [metrics.py](file:///Users/ted/vivid/backend/app/rag/metrics.py)


