# RAG 데이터 큐레이터 가이드

> **버전**: 1.0
> **작성일**: 2026-01-16
> **대상**: RAG 데이터 적재 담당자, NotebookLM 운영자
> **목적**: 고품질 RAG 지식베이스 구축을 위한 단일 진실 문서

---

## 목차

1. [개요](#1-개요)
2. [2026 RAG Best Practices](#2-2026-rag-best-practices)
3. [Vivid RAG 아키텍처](#3-vivid-rag-아키텍처)
4. [NotebookLM (Tier0) 운영](#4-notebooklm-tier0-운영)
5. [Qdrant (Tier1) 운영](#5-qdrant-tier1-운영)
6. [데이터 수집 및 전처리](#6-데이터-수집-및-전처리)
7. [청킹 전략](#7-청킹-전략)
8. [메타데이터 태깅](#8-메타데이터-태깅)
9. [품질 검증](#9-품질-검증)
10. [운영 체크리스트](#10-운영-체크리스트)

---

## 1. 개요

### 1.1 RAG의 역할

RAG (Retrieval-Augmented Generation)는 LLM의 환각을 방지하고 **검증된 지식 기반 응답**을 생성합니다.

```
사용자 쿼리 → 검색 (Retrieval) → 컨텍스트 주입 → LLM 생성 → 응답 + 출처
```

### 1.2 큐레이터의 책임

| 책임 영역 | 설명 |
|----------|------|
| **소스 선별** | 신뢰할 수 있는 출처만 선택 |
| **데이터 정제** | 노이즈 제거, 일관된 형식 적용 |
| **청킹** | 의미 단위로 문서 분할 |
| **메타데이터** | 검색 가능한 태그 부여 |
| **품질 검증** | 검색 정확도 지속 모니터링 |

---

## 2. 2026 RAG Best Practices

### 2.1 핵심 원칙 (Industry Standard)

| 원칙 | 설명 | 효과 |
|------|------|------|
| **Semantic Chunking** | 고정 크기 X, 의미 단위 O | 컨텍스트 보존 |
| **Hybrid Search** | Dense + BM25 + Cross-Encoder | +26~31% NDCG |
| **Metadata Filtering** | 검색 전 메타데이터로 필터링 | 정확도 향상 |
| **Quality over Quantity** | 소수의 검증된 소스 > 대량의 미검증 소스 | 환각 방지 |
| **Single Source of Truth** | 중복 제거, 최신 버전만 유지 | 일관성 보장 |

### 2.2 피해야 할 안티패턴

```
❌ 무분별한 소스 업로드 ("일단 다 넣어보자")
❌ 고정 크기 청킹 (512 토큰 고정)
❌ 메타데이터 없이 적재
❌ 검색 품질 미측정
❌ 오래된 문서 방치
```

---

## 3. Vivid RAG 아키텍처

### 3.1 2-Tier 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Hybrid RAG                           │
├────────────────────────────┬────────────────────────────────┤
│      Tier0: NotebookLM     │      Tier1: Qdrant + BM25     │
│      (거장 지식베이스)      │      (하이브리드 검색)         │
├────────────────────────────┼────────────────────────────────┤
│ • Google Gemini 기반       │ • Dense Vector (Gemini)       │
│ • 문서 그라운딩            │ • Sparse Vector (BM25)        │
│ • 자동 인용               │ • RRF 융합                    │
│ • CDP 프로토콜            │ • 메타데이터 필터링            │
└────────────────────────────┴────────────────────────────────┘
```

### 3.2 Tier별 역할

| Tier | 시스템 | 용도 | 데이터 유형 |
|------|--------|------|-------------|
| **Tier0** | NotebookLM | 거장 스타일 분석, 심층 QA | PDF, 영상, 논문 |
| **Tier1** | Qdrant | 실시간 검색, 다차원 필터링 | 청크된 텍스트, 메타데이터 |

### 3.3 데이터 흐름

```python
# 1. Tier0 (NotebookLM) - 심층 분석용
raw_sources = ["봉준호_인터뷰.pdf", "기생충_분석.mp4"]
notebooklm.add_sources(notebook_id, raw_sources)

# 2. Tier1 (Qdrant) - 실시간 검색용
chunks = chunk_document(raw_sources, strategy="semantic")
embeddings = embed_chunks(chunks)
qdrant.upsert(collection="auteur_knowledge", points=embeddings)
```

---

## 4. NotebookLM (Tier0) 운영

### 4.1 노트북 구조 (권장)

```
vivid-rag/
├── 거장_봉준호/           # 거장별 노트북
│   ├── 인터뷰_영상
│   ├── 논문_PDF
│   └── 분석_문서
├── 거장_놀란/
├── 거장_빌뇌브/
├── 영화_기법/             # 도메인별 노트북
│   ├── 촬영_기법
│   ├── 조명_기법
│   └── 편집_기법
└── 레퍼런스_분석/
    ├── 4D_영상분석
    └── 3D_스타일참조
```

### 4.2 소스 추가 가이드라인

#### 지원 형식

| 형식 | 권장 | 주의사항 |
|------|------|----------|
| **PDF** | ⭐ 최우선 | 텍스트 기반, 깨끗한 레이아웃 |
| **Google Docs** | 좋음 | 실시간 동기화 가능 |
| **YouTube** | 좋음 | 자막 품질에 의존 |
| **Website URL** | 보통 | 사이트 구조에 따라 다름 |
| **Plain Text** | 좋음 | 구조화된 텍스트 |

#### 큐레이션 3단계 (Curate → Learn → Act)

```
1. CURATE (선별)
   - 무작위 업로드 금지
   - 신뢰할 수 있는 출처만 선택
   - 중복 제거

2. LEARN (학습)
   - NotebookLM 요약 검토
   - 키워드 확인
   - 잘못된 해석 수정

3. ACT (활용)
   - 테스트 쿼리 실행
   - 인용 정확도 확인
   - 필요시 소스 조정
```

### 4.3 노트북 운영 명령어 (MCP)

```python
# 노트북 목록
mcp__notebooklm-mcp__notebook_list()

# 소스 추가 (URL)
mcp__notebooklm-mcp__notebook_add_url(
    notebook_id="xxx",
    url="https://example.com/article"
)

# 소스 추가 (텍스트)
mcp__notebooklm-mcp__notebook_add_text(
    notebook_id="xxx",
    text="분석할 텍스트...",
    title="봉준호 스타일 분석"
)

# 쿼리 테스트
mcp__notebooklm-mcp__notebook_query(
    notebook_id="xxx",
    query="봉준호 감독의 트래킹 샷 특징은?"
)
```

---

## 5. Qdrant (Tier1) 운영

### 5.1 컬렉션 구조

```python
# 컬렉션 생성
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="auteur_knowledge",
    vectors_config={
        "dense": VectorParams(size=768, distance=Distance.COSINE),
    },
    sparse_vectors_config={
        "sparse": {"index": {"on_disk": False}},
    },
)
```

### 5.2 Dimension별 컬렉션

| 컬렉션명 | Dimension | 용도 |
|----------|-----------|------|
| `auteur_style_hints` | AD, Story | 거장 스타일 힌트 |
| `video_reference` | 4D | 영상 분석 레퍼런스 |
| `visual_style` | 3D | 비주얼 스타일 참조 |
| `prompt_examples` | 1D, 2D | 프롬프트 예시 |

### 5.3 데이터 적재

```python
from app.rag.ingestion import RagIngestionService

ingestion = RagIngestionService()

# 문서 청킹 + 임베딩 + 업서트
await ingestion.ingest_document(
    file_path="data/bong_style_analysis.pdf",
    collection="auteur_style_hints",
    dimension="AD",
    auteur_key="bong",
    metadata={
        "source": "학술논문",
        "year": 2024,
        "language": "ko",
    },
)
```

---

## 6. 데이터 수집 및 전처리

### 6.1 소스 품질 기준

| 등급 | 기준 | 예시 |
|------|------|------|
| **A (최우선)** | 공식 출처, 검증된 내용 | 감독 인터뷰, 학술 논문, 공식 다큐멘터리 |
| **B (권장)** | 신뢰할 수 있는 2차 출처 | 유명 평론가 분석, 공인된 미디어 |
| **C (제한적)** | 비공식 출처 | 팬 분석, 블로그 (검증 필요) |
| **D (제외)** | 미검증 출처 | 익명 게시물, 출처 불명 |

### 6.2 전처리 파이프라인

```python
def preprocess_document(raw_text: str) -> str:
    """문서 전처리 파이프라인."""

    # 1. 인코딩 정규화
    text = raw_text.encode("utf-8", errors="ignore").decode("utf-8")

    # 2. 불필요한 요소 제거
    text = remove_headers_footers(text)
    text = remove_page_numbers(text)
    text = remove_watermarks(text)

    # 3. 공백 정규화
    text = re.sub(r"\s+", " ", text).strip()

    # 4. 특수문자 처리
    text = normalize_punctuation(text)

    return text
```

### 6.3 PDF 추출 품질 체크

```python
def validate_pdf_extraction(extracted_text: str) -> dict:
    """PDF 추출 품질 검증."""

    issues = []

    # 깨진 문자 체크
    if re.search(r"[�□■▲▼◆◇○●]", extracted_text):
        issues.append("깨진 문자 발견")

    # 줄바꿈 이상 체크
    if extracted_text.count("\n") > len(extracted_text) / 50:
        issues.append("과도한 줄바꿈")

    # 의미 없는 문자열 체크
    if re.search(r"(\w)\1{10,}", extracted_text):
        issues.append("반복 문자열")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "char_count": len(extracted_text),
    }
```

---

## 7. 청킹 전략

### 7.1 Semantic Chunking (권장)

고정 크기가 아닌 **의미 단위**로 분할:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def semantic_chunk(text: str, dimension: str) -> list[str]:
    """의미 단위 청킹."""

    # Dimension별 최적 설정
    CHUNK_CONFIGS = {
        "AD": {"chunk_size": 1000, "overlap": 200},  # 분석 텍스트
        "4D": {"chunk_size": 800, "overlap": 150},   # 영상 스크립트
        "Story": {"chunk_size": 1200, "overlap": 250},  # 시나리오
        "default": {"chunk_size": 1000, "overlap": 200},
    }

    config = CHUNK_CONFIGS.get(dimension, CHUNK_CONFIGS["default"])

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["overlap"],
        separators=["\n\n", "\n", "。", ".", " ", ""],
        length_function=len,
    )

    return splitter.split_text(text)
```

### 7.2 청킹 품질 검증

```python
def validate_chunks(chunks: list[str]) -> dict:
    """청크 품질 검증."""

    stats = {
        "count": len(chunks),
        "avg_length": sum(len(c) for c in chunks) / len(chunks),
        "min_length": min(len(c) for c in chunks),
        "max_length": max(len(c) for c in chunks),
    }

    issues = []

    # 너무 짧은 청크
    short_chunks = [c for c in chunks if len(c) < 100]
    if short_chunks:
        issues.append(f"짧은 청크 {len(short_chunks)}개 (<100자)")

    # 너무 긴 청크
    long_chunks = [c for c in chunks if len(c) > 2000]
    if long_chunks:
        issues.append(f"긴 청크 {len(long_chunks)}개 (>2000자)")

    return {**stats, "issues": issues, "valid": len(issues) == 0}
```

---

## 8. 메타데이터 태깅

### 8.1 필수 메타데이터

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `dimension` | string | 관련 Dimension | `"AD"`, `"4D"` |
| `auteur_key` | string | 거장 키 (선택) | `"bong"`, `"nolan"` |
| `source_type` | string | 소스 유형 | `"interview"`, `"paper"`, `"analysis"` |
| `language` | string | 언어 | `"ko"`, `"en"` |
| `year` | int | 작성 연도 | `2024` |
| `confidence` | float | 신뢰도 | `0.95` |

### 8.2 태깅 예시

```python
metadata = {
    # 필수
    "dimension": "AD",
    "source_type": "interview",
    "language": "ko",

    # 선택 (있으면 검색 품질 향상)
    "auteur_key": "bong",
    "year": 2024,
    "topics": ["mise-en-scene", "tracking-shot", "symmetry"],

    # 출처 추적용
    "source_url": "https://...",
    "source_title": "봉준호 감독 인터뷰",
    "ingested_at": "2026-01-16T10:00:00Z",
}
```

### 8.3 메타데이터 필터링 활용

```python
# Qdrant 쿼리 시 메타데이터 필터
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="auteur_style_hints",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="dimension", match=MatchValue(value="AD")),
            FieldCondition(key="auteur_key", match=MatchValue(value="bong")),
        ]
    ),
    limit=10,
)
```

---

## 9. 품질 검증

### 9.1 검색 품질 메트릭

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| **Recall@K** | > 80% | 관련 문서 중 검색된 비율 |
| **Precision@K** | > 70% | 검색 결과 중 관련 문서 비율 |
| **NDCG** | > 0.75 | 순위 품질 |
| **MRR** | > 0.6 | 첫 관련 결과 순위 |

### 9.2 품질 테스트 쿼리

```python
TEST_QUERIES = [
    # 거장 스타일
    {"query": "봉준호 감독의 트래킹 샷 특징", "expected_auteur": "bong"},
    {"query": "놀란 감독의 시간 구조", "expected_auteur": "nolan"},

    # 기법 검색
    {"query": "시네마틱 조명 기법", "expected_dimension": "AD"},
    {"query": "스토리보드 작성법", "expected_dimension": "2D"},

    # 복합 쿼리
    {"query": "봉준호 스타일 서스펜스 장면 연출", "expected_topics": ["bong", "suspense"]},
]

async def run_quality_test(queries: list[dict]) -> dict:
    """RAG 품질 테스트 실행."""
    results = []

    for q in queries:
        rag_result = await hybrid_query(q["query"])

        # 기대값과 비교
        is_correct = validate_result(rag_result, q)
        results.append({"query": q["query"], "correct": is_correct})

    accuracy = sum(r["correct"] for r in results) / len(results)
    return {"accuracy": accuracy, "details": results}
```

### 9.3 정기 품질 리포트

```bash
# /rag-quality 슬래시 커맨드로 품질 리포트 생성
/rag-quality --dimension AD --auteur bong

# 출력 예시:
# ========== RAG Quality Report ==========
# Dimension: AD
# Auteur: bong
# Total Documents: 156
# Recall@10: 0.85
# Precision@10: 0.78
# NDCG: 0.82
# ========================================
```

---

## 10. 운영 체크리스트

### 10.1 새 데이터 적재 시

- [ ] 소스 품질 등급 확인 (A/B 등급만 적재)
- [ ] 중복 문서 확인
- [ ] 전처리 파이프라인 실행
- [ ] Semantic Chunking 적용
- [ ] 메타데이터 태깅 완료
- [ ] 청크 품질 검증 통과
- [ ] 테스트 쿼리 실행 및 결과 확인
- [ ] 기존 인덱스와 일관성 확인

### 10.2 주간 점검

- [ ] 검색 품질 메트릭 확인 (Recall, Precision, NDCG)
- [ ] 오래된 문서 확인 (1년 이상)
- [ ] 중복 문서 제거
- [ ] NotebookLM 소스 상태 확인
- [ ] Qdrant 컬렉션 상태 확인

### 10.3 월간 점검

- [ ] 전체 품질 리포트 생성
- [ ] 저품질 문서 식별 및 제거
- [ ] 새로운 거장/기법 데이터 수집 계획
- [ ] 임베딩 모델 업데이트 검토

---

## 11. 참고 자료

| 문서 | 경로 | 설명 |
|------|------|------|
| RAG 아키텍처 | `docs/RAG_ARCHITECTURE.md` | 기술 아키텍처 상세 |
| 앱 개발자 가이드 | `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | RAG 연동 코드 |
| Hybrid RAG 코드 | `backend/app/rag/hybrid_rag.py` | 하이브리드 검색 구현 |
| RAG Presets | `backend/app/rag/rag_presets.py` | 거장 스타일 힌트 |

---

## 12. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2026-01-16 | 초기 버전 (2026 Best Practices 반영) |
