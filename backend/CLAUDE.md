# Backend CLAUDE.md

> **Prompty.co.kr** - Dual AI 티키타카 워크플로우 가이드 플랫폼
> FastAPI + Python 3.11 + SQLAlchemy 2.0 async

---

## Quick Commands

```bash
source venv/bin/activate && uvicorn app.main:app --reload --port 8100
alembic upgrade head      # DB 마이그레이션
pytest --tb=short -q      # 테스트
ruff check --fix .        # 린트
```

---

## 핵심 철학

```
LOCAL PROJECT FOLDER (SSoT)
projects/{project-name}/
├── reference/source.mp4     ← 원본 영상
├── docs/ANALYSIS.md         ← Gemini 출력
├── prompts/IMAGE_PROMPTS.md ← Claude 정제
├── generated/images/        ← 생성 이미지
└── STATE.md                 ← 진행 상태 (핵심!)
         ↑
     Dual AI 티키타카
     Gemini ↔ Claude
```

- Prompty 백엔드 = STATE.md 동기화 + Critique 기록 저장
- AI API 직접 호출 ❌ → 가이드만 제공 ✅

---

## Prompty 디렉토리 구조

```
app/
├── routers/prompty/           # Prompty API
│   ├── __init__.py            # 라우터 통합
│   ├── templates.py           # GET/POST 템플릿
│   ├── projects.py            # 프로젝트 CRUD
│   ├── critique.py            # Critique 저장/조회
│   └── guide.py               # 워크플로우 가이드
├── models_prompty.py          # 4개 테이블
│   ├── PromptyTemplate
│   ├── PromptyProject
│   ├── PromptyCritique
│   └── PromptyGuideLog
└── scripts/
    └── seed_prompty_templates.py  # 시드 데이터
```

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/templates` | 템플릿 목록 |
| GET | `/api/templates/{id}` | 템플릿 상세 |
| POST | `/api/projects` | 프로젝트 생성 |
| GET | `/api/guide/{project_id}` | 현재 워크플로우 상태 |
| POST | `/api/guide/{project_id}/advance` | 다음 스텝 진행 |
| POST | `/api/critique` | Critique 저장 |
| GET | `/api/critique/{project_id}` | Critique 이력 |
| GET | `/api/critique/{project_id}/{step_id}` | 특정 스텝 Critique |

---

## Critique 판정 기준

```python
PASSING_SCORE = 85  # PASS
REVISE_MIN = 60     # REVISE (60-84)
# < 60 = REJECT

# 판정 로직
def get_verdict(score: int) -> str:
    if score >= 85:
        return "PASS"
    elif score >= 60:
        return "REVISE"
    return "REJECT"
```

---

## 4-Stage 워크플로우

```python
STAGES = [
    {"id": "stage1", "name": "ANALYZE", "tool": "Gemini CLI"},
    {"id": "stage2", "name": "IMAGE", "tool": "NanoBanana/MJ"},
    {"id": "stage3", "name": "VIDEO", "tool": "Kling/Veo"},
    {"id": "stage4", "name": "ASSEMBLY", "tool": "CapCut"},
]
```

---

## 새 기능 추가 체크리스트

### Prompty 라우터 추가
1. `routers/prompty/my_feature.py` 생성
2. `routers/prompty/__init__.py`에 포함
3. 인증: `Depends(get_current_user)`
4. 테스트 작성

### STATE.md 동기화 (Phase 4)
```python
@router.post("/{project_id}/sync")
async def sync_state_from_local(
    project_id: UUID,
    state_md_content: str,  # STATE.md 파일 내용
):
    """로컬 STATE.md → DB 동기화"""
    parsed = parse_state_md(state_md_content)
    return {"synced": True}
```

---

## SSoT 참조

```
viral-video-automation/templates/
├── CRITIQUE_IMAGE.md    # 이미지 5가지 평가 기준
├── CRITIQUE_VIDEO.md    # 영상 5가지 평가 기준
├── CRITIQUE_SELFLOOP.md # Self-Loop 티키타카 흐름
└── MODE_TIKITAKA.md     # 98% 품질까지 반복
```

---

## 마이그레이션 현황

```
042_add_prompty_tables.py  → 4개 테이블
043_add_jsonb_indexes.py   → JSONB GIN 인덱스
```
