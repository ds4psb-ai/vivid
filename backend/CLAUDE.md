# Backend CLAUDE.md

> FastAPI + Python 3.11 + SQLAlchemy 2.0 async

---

## Quick Commands

```bash
# 서버 실행
source venv/bin/activate && uvicorn app.main:app --reload --port 8100

# 테스트
pytest --tb=short -q

# 특정 테스트
pytest -v tests/path/to/test.py

# DB 마이그레이션
alembic upgrade head

# 린트
ruff check --fix .

# 타입 체크
pyright
```

---

## 코딩 스타일

- **들여쓰기**: 4 spaces
- **네이밍**: snake_case
- **타입 힌트**: 필수
- **Docstring**: Google style

```python
def process_item(item_id: str, options: dict[str, Any] | None = None) -> ItemResponse:
    """Process an item with given options.

    Args:
        item_id: The unique identifier of the item.
        options: Optional processing options.

    Returns:
        Processed item response.

    Raises:
        ItemNotFoundError: If item doesn't exist.
    """
```

---

## 디렉토리 구조

```
app/
├── main.py                    # App bootstrap, 40+ routers
├── config.py                  # Pydantic settings
├── dimension_adapter.py       # Dimension 핸들러 (16개 함수)
├── routers/                   # API endpoints
│   ├── dimension/             # Dimension 앱 (디렉토리, 13개 모듈)
│   │   ├── _base.py           # 공통 유틸
│   │   ├── classic.py         # 1D~4D 기본 앱
│   │   ├── aesthetic.py       # 미학 디렉터
│   │   ├── mirror.py          # 심연의 거울
│   │   ├── story.py           # 스토리 아키텍트
│   │   ├── sound.py           # 사운드 크래프터
│   │   ├── quality.py         # 퀄리티 디렉터
│   │   └── veo.py             # Veo 비디오
│   ├── run_token.py           # Run-Token 관리
│   ├── humancloud.py          # Human Cloud (Layer 2)
│   ├── fork.py                # Fork 수익분배
│   ├── telemetry.py           # 텔레메트리 (Layer 4)
│   └── sandbox.py             # 샌드박스 실행
├── services/                  # 비즈니스 로직
│   ├── capsule_executor.py
│   ├── credit_service.py
│   ├── humancloud_service.py  # Human Cloud 서비스
│   ├── fork_revenue_service.py # Fork 수익분배
│   ├── sandbox_executor.py    # 샌드박스 실행
│   └── telemetry_service.py   # 텔레메트리 서비스
├── agents/                    # AI Agent 시스템
│   ├── vivid_agent.py
│   ├── dimension_tools.py
│   └── humancloud_tools.py
├── rag/                       # RAG 시스템
│   ├── hybrid_rag.py          # 하이브리드 RAG (메인)
│   ├── tier0_notebooklm.py    # NotebookLM Playwright
│   ├── tier1_dimension_rag.py # Qdrant + BM25
│   └── semantic_cache.py      # 시맨틱 캐시
├── models/                    # SQLAlchemy 모델
├── models_telemetry.py        # 4-Layer 텔레메트리 모델
├── models_settlement.py       # Fork 정산 모델
├── schemas/                   # Pydantic 스키마
└── fixtures/                  # SSoT 데이터
    └── dimension_capsules.py
```

---

## Vivid 핵심 규칙

### 1. evidence_refs 타입
```python
# ✅ 올바름 - List[str]
evidence_refs = ["db:capsule_runs:uuid", "db:rag_docs:4D:video_ref:doc_id"]

# ❌ 틀림 - dict 배열
evidence_refs = [{"source": "...", "ref_id": "..."}]
```

### 2. Run-Token 흐름
```python
# 표준 흐름
token = await run_token_service.issue(user_id, app_id, credits)
result = await capsule_executor.execute(token, params)
await run_token_service.deduct(token) or refund(token)

# ❌ 금지 - 직접 호출
await credit_service.reserve_credits(...)  # 금지
await credit_service.commit_credits(...)   # 금지
```

### 3. Sealed Capsule 원칙
- 모든 LLM 호출은 캡슐 내부에서
- raw prompt 외부 노출 금지
- 결과만 클라이언트에 반환

---

## 새 기능 추가 체크리스트

### 새 Dimension Tool
1. `routers/dimension/*.py` - 엔드포인트 추가 (관련 모듈 선택)
2. `dimension_adapter.py` - 핸들러 구현 (`run_xxx()` 함수)
3. `agents/dimension_tools.py` - 도구 등록
4. `fixtures/dimension_capsules.py` - 크레딧 비용 추가

### 새 API Route
1. `routers/my_feature.py` 생성
2. `main.py`에 라우터 포함
3. `Depends(get_current_user)` 인증 적용
4. 테스트 작성

---

## 테스트 가이드

```python
# 기본 테스트 구조
@pytest.mark.asyncio
async def test_feature_success(db_session, test_user):
    # Arrange
    ...
    # Act
    result = await service.process(...)
    # Assert
    assert result.success
```

### 필수 테스트 파일
| 변경 영역 | 테스트 파일 |
|-----------|-------------|
| Dimension | `tests/routers/test_dimension_sse.py` |
| Credits | `tests/test_kelly_credit_service.py` |
| Agent | `tests/agents/test_vivid_agent_integration.py` |

---

## 에러 처리 패턴

```python
from fastapi import HTTPException

async def process_with_token(token_id: str):
    try:
        token = await get_token(token_id)
        result = await execute(token)
        await deduct_credits(token)
        return result
    except InsufficientCreditsError:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    except TokenExpiredError:
        await refund_credits(token)
        raise HTTPException(status_code=400, detail="Token expired")
    except Exception as e:
        await refund_credits(token)  # 항상 롤백
        raise
```
