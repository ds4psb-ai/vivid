# App Create Command

입력: $ARGUMENTS (앱 ID, 예: my-app)

---

## 목적
새로운 Dimension 앱을 생성합니다. YAML 설정, 백엔드 라우터, 프론트엔드 패널을 자동 생성합니다.

---

## 워크플로우

### 1. 앱 ID 확인

```bash
# 기존 앱 확인
ls config/apps/content/dimensions/
```

### 2. YAML 설정 생성 (SSoT)

경로: `config/apps/content/dimensions/$ARGUMENTS.yaml`

```yaml
$schema: "vivid-app/v2"

metadata:
  name: $ARGUMENTS
  type: dimension
  version: "1.0.0"
  bounded_context: content

display:
  name_ko: "앱 한글명"
  name_en: "App Name"
  icon: "🆕"
  description: "앱 설명"

capabilities:
  - name: execution
    enabled: true
    config:
      credit_cost: 5
      capsule_key: "$ARGUMENTS.generate"
      endpoint: "/api/dimension/$ARGUMENTS/generate"

  - name: rag
    enabled: true
    config:
      mode: auteur_only  # auteur_only | always | never

extensions:
  dimension:
    tool_type: generation  # generation | analysis
    supports_streaming: true

keywords:
  patterns:
    - "$ARGUMENTS"
```

### 3. Backend 라우터 생성

경로: `backend/app/routers/dimension/$ARGUMENTS.py`

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_current_user

router = APIRouter(prefix="/$ARGUMENTS", tags=["$ARGUMENTS"])

class Request(BaseModel):
    topic: str
    style: str = "default"

class Response(BaseModel):
    result: str
    evidence_refs: list[str] = []
    credit_cost: int

@router.post("/generate", response_model=Response)
async def generate(request: Request, user = Depends(get_current_user)):
    return Response(
        result="...",
        evidence_refs=[],
        credit_cost=5
    )
```

### 4. 라우터 등록

`backend/app/routers/dimension/__init__.py`에 추가:
```python
from . import $ARGUMENTS
```

### 5. Frontend 패널 생성 (선택)

경로: `frontend/src/components/dimension/{AppName}Panel.tsx`

### 6. 입력 스키마 등록

`frontend/src/lib/dimension-input-schemas.ts`에 추가

---

## 체크리스트

- [ ] `config/apps/content/dimensions/$ARGUMENTS.yaml` 생성
- [ ] `backend/app/routers/dimension/$ARGUMENTS.py` 생성
- [ ] `backend/app/routers/dimension/__init__.py` 등록
- [ ] `backend/app/agents/dimension_tools.py` 도구 등록
- [ ] `frontend/src/lib/dimension-input-schemas.ts` 업데이트
- [ ] 테스트 작성
- [ ] Backend pytest 실행
- [ ] Frontend build 확인

---

## 크레딧 비용 기준

| 앱 유형 | 권장 비용 |
|---------|----------|
| 단순 생성 | 5 |
| 분석/검증 | 8 |
| 복잡한 생성 | 10 |
| 외부 API (VEO) | 200 |

---

## 관련 문서

- `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` - 전체 가이드
- `config/apps/README.md` - YAML 스키마
- `.claude/agents/app-creator.md` - 앱 생성 서브에이전트
