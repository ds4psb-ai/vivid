# RAG Quality Command

입력: $ARGUMENTS (옵션: --no-llm, --dimension 4D)

---

## 목적
RAG 시스템의 품질을 평가하고 리포트를 생성합니다.

---

## 워크플로우

### 1. RAG 상태 확인

```bash
# Qdrant 상태 확인
curl -s http://localhost:6333/collections | jq .

# 인덱스 문서 수
curl -s http://localhost:6333/collections/dimension_rag/points/count | jq .
```

### 2. 품질 리포트 실행

```bash
cd backend && source venv/bin/activate
python scripts/run_rag_quality_report.py $ARGUMENTS
```

### 3. 평가 메트릭

| 메트릭 | 설명 | 목표 |
|--------|------|------|
| Groundedness | 응답이 검색 결과에 기반 | >= 0.8 |
| Relevancy | 검색 결과가 쿼리와 관련 | >= 0.7 |
| Completeness | 필요 정보 포함 | >= 0.7 |
| Coverage | evidence_refs 커버리지 | >= 0.6 |

---

## 수동 검증

### 하이브리드 쿼리 테스트

```python
from app.rag.hybrid_rag import hybrid_query

result = await hybrid_query(
    query="봉준호 스타일 서스펜스",
    dimension="AD",
    auteur_key="bong",
    top_k=5,
)

print(f"Confidence: {result.confidence}")
print(f"Strategy: {result.strategy_used}")
print(f"Sources: {len(result.notebooklm_sources)}")
```

### evidence_refs 검증

```bash
# evidence_refs 형식 검사
grep -rn "evidence_refs.*\[{" backend/app/ --include="*.py"

# 올바른 형식 확인
grep -rn "evidence_refs.*List\[str\]" backend/app/ --include="*.py"
```

---

## 문제 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| 검색 결과 없음 | 인덱스 미생성 | `python scripts/seed_aesthetic_rag.py` |
| 낮은 confidence | 쿼리 불일치 | top_k 증가, threshold 조정 |
| Tier0 실패 | CDP 연결 문제 | Chrome 9222 포트 확인 |

---

## 인제스션 스크립트

```bash
# Video Reference 인제스션
python scripts/ingest_video_reference.py --input ../data/source_packs/video_refs.json

# Image Grid 인제스션
python scripts/ingest_image_grid.py --input ../data/source_packs/grids.json
```

---

## 출력 형식

```markdown
# RAG Quality Report

## 요약
- 총 문서: X개
- 평균 Groundedness: 0.XX
- 평균 Relevancy: 0.XX

## Dimension별 현황
| Dimension | 문서 수 | 평균 점수 |
|-----------|---------|-----------|
| 4D | X | 0.XX |
| 3D | X | 0.XX |

## 개선 필요 항목
1. 설명

## 권장 조치
1. [ ] 조치 항목
```

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `app/rag/hybrid_rag.py` | 하이브리드 RAG |
| `app/rag/tier1_dimension_rag.py` | Qdrant 인덱싱 |
| `scripts/run_rag_quality_report.py` | 품질 평가 CLI |
| `docs/RAG_QUALITY.md` | 품질 평가 가이드 |
