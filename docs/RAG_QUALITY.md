# RAG Quality Evaluation Guide

> **Type**: Quality Standards (Static)
> **Status**: Active
> **Last Updated**: 2026-01-14
> **Related**: [RAG Reliability](./RAG_RELIABILITY.md) | [RAG Execution Plan](./RAG_NEXT_PHASE_PLAN_2026-01-11.md)

---

## 개요

RAG(Retrieval-Augmented Generation) 품질 평가 파이프라인:
- **Groundedness**: 응답이 소스에 근거하는 정도
- **Relevance**: 쿼리에 대한 응답의 관련성
- **Deflection**: 증거 부족 시 적절한 거부

---

## 평가 지표

| 지표 | 정의 | 기준 |
|------|------|------|
| Groundedness (Heuristic) | `min(1.0, evidence_count / 3)` | ≥ 0.6 |
| Relevance (Heuristic) | 키워드 매칭 비율 | ≥ 0.5 |
| Groundedness (LLM) | Gemini가 직접 평가 | ≥ 0.6 |
| Relevance (LLM) | Gemini가 직접 평가 | ≥ 0.5 |
| Deflection | 증거 < 2개 시 거부 | true/false |

---

## 운영 OKR 기준

### 주간 품질 리포트 통과 기준

| 지표 | 기준 | 등급 |
|------|------|------|
| Pass Rate | ≥ 70% | PASS |
| Pass Rate | 60-69% | WARNING |
| Pass Rate | < 60% | FAIL |
| Avg Groundedness | ≥ 0.6 | 정상 |
| Avg Relevance | ≥ 0.5 | 정상 |

### 알림 규칙

| 조건 | 액션 |
|------|------|
| Pass Rate < 70% | Slack 알림 + 원인 분석 |
| Pass Rate < 60% | 긴급 리뷰 |
| Groundedness < 0.5 | 데이터셋 점검 |

### 분기 OKR (Q1 2026)

| Objective | Key Result | 현재 |
|-----------|-----------|------|
| RAG 검색 품질 개선 | Pass Rate ≥ 80% | 87.5% ✅ |
| 소스 근거 신뢰도 | Avg Groundedness ≥ 0.7 | 0.62 ⚠️ |
| 검색 관련성 | Avg Relevance ≥ 0.6 | 0.27 ⚠️ |

> **참고**: Relevance가 낮은 것은 테스트 쿼리가 실제 인덱싱된 콘텐츠와 다르기 때문. 실 데이터 인제스션 후 재측정 필요.

---

## 실행 방법

### 0. 환경 변수

기본값에서는 LLM 평가가 비활성화되어 테스트가 skip될 수 있습니다.

```bash
export RAG_QUALITY_EVAL=1
```

### 1. 평가 케이스 확인

```bash
cat data/rag_eval/rag_quality_cases.json
```

### 2. 테스트 실행

```bash
cd backend
pytest tests/e2e/test_rag_quality.py -v
```

### 3. 품질 리포트 생성

```bash
# LLM 포함
python scripts/run_rag_quality_report.py

# LLM 없이 (빠르게)
python scripts/run_rag_quality_report.py --no-llm

# 커스텀 출력 경로
python scripts/run_rag_quality_report.py -o data/reports/custom.json
```

---

## 비용 & 시간 가이드

| 모드 | 케이스 당 시간 | 비용 |
|------|---------------|------|
| Heuristic Only | ~100ms | 무료 |
| LLM-as-Judge | ~2-3s | ~$0.001/case |

**참고**: 8개 케이스 기준
- Heuristic: ~2초
- LLM: ~20-30초, ~$0.01

---

## 리포트 구조

```json
{
  "generated_at": "2026-01-13T12:00:00",
  "summary": {
    "total_cases": 8,
    "passed": 6,
    "failed": 2,
    "pass_rate": 0.75,
    "overall_passed": true
  },
  "metrics": {
    "avg_groundedness_heuristic": 0.67,
    "avg_relevance_heuristic": 0.85
  },
  "details": [...]
}
```

---

## CI 자동화 (선택)

### GitHub Actions 예시

```yaml
# .github/workflows/rag-quality.yml
name: RAG Quality Check
on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 9시
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          cd backend
          pip install -r requirements.txt
          python scripts/run_rag_quality_report.py --no-llm
```

---

## 추가 리소스

- [llm_eval_harness.py](../backend/app/llm_eval_harness.py): 기존 평가 모듈
- [test_rag_quality.py](../backend/tests/e2e/test_rag_quality.py): E2E 테스트
- [rag_quality_cases.json](../data/rag_eval/rag_quality_cases.json): 평가 케이스
