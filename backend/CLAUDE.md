# Backend CLAUDE.md

> **Prompty.co.kr** - Dual AI Tikitaka Workflow Guide Platform
> FastAPI + Python 3.11 + SQLAlchemy 2.0 async

---

## Quick Commands

```bash
source venv/bin/activate && uvicorn app.main:app --reload --port 8100
alembic upgrade head      # DB migration
pytest --tb=short -q      # Tests
ruff check --fix .        # Lint
```

---

## Core Philosophy

```
LOCAL PROJECT FOLDER (SSoT)
projects/{project-name}/
├── reference/source.mp4     ← Source video
├── docs/ANALYSIS.md         ← Gemini output
├── prompts/IMAGE_PROMPTS.md ← Claude refinement
├── generated/images/        ← Generated images
└── STATE.md                 ← Progress state (core!)
         ↑
     Dual AI Tikitaka
     Gemini ↔ Claude
```

- Prompty backend = STATE.md sync + Critique record storage
- Direct AI API calls: NO → Provide guidance only: YES

---

## Prompty Directory Structure

```
app/
├── routers/prompty/           # Prompty API
│   ├── __init__.py            # Router integration
│   ├── templates.py           # GET/POST templates
│   ├── projects.py            # Project CRUD
│   ├── critique.py            # Critique save/query
│   └── guide.py               # Workflow guide
├── models_prompty.py          # 4 tables
│   ├── PromptyTemplate
│   ├── PromptyProject
│   ├── PromptyCritique
│   └── PromptyGuideLog
└── scripts/
    └── seed_prompty_templates.py  # Seed data
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/templates` | Template list |
| GET | `/api/templates/{id}` | Template detail |
| POST | `/api/projects` | Create project |
| GET | `/api/guide/{project_id}` | Current workflow state |
| POST | `/api/guide/{project_id}/advance` | Advance to next step |
| POST | `/api/critique` | Save critique |
| GET | `/api/critique/{project_id}` | Critique history |
| GET | `/api/critique/{project_id}/{step_id}` | Specific step critique |

---

## Critique Scoring Criteria

```python
PASSING_SCORE = 85  # PASS
REVISE_MIN = 60     # REVISE (60-84)
# < 60 = REJECT

# Scoring logic
def get_verdict(score: int) -> str:
    if score >= 85:
        return "PASS"
    elif score >= 60:
        return "REVISE"
    return "REJECT"
```

---

## 4-Stage Workflow

```python
STAGES = [
    {"id": "stage1", "name": "ANALYZE", "tool": "Gemini CLI"},
    {"id": "stage2", "name": "IMAGE", "tool": "NanoBanana/MJ"},
    {"id": "stage3", "name": "VIDEO", "tool": "Kling/Veo"},
    {"id": "stage4", "name": "ASSEMBLY", "tool": "CapCut"},
]
```

---

## New Feature Checklist

### Adding a Prompty Router
1. Create `routers/prompty/my_feature.py`
2. Include in `routers/prompty/__init__.py`
3. Auth: `Depends(get_current_user)`
4. Write tests

### STATE.md Sync (Phase 4)
```python
@router.post("/{project_id}/sync")
async def sync_state_from_local(
    project_id: UUID,
    state_md_content: str,  # STATE.md file content
):
    """Sync local STATE.md to DB"""
    parsed = parse_state_md(state_md_content)
    return {"synced": True}
```

---

## SSoT References

```
viral-video-automation/templates/
├── CRITIQUE_IMAGE.md    # Image evaluation criteria (5 dimensions)
├── CRITIQUE_VIDEO.md    # Video evaluation criteria (5 dimensions)
├── CRITIQUE_SELFLOOP.md # Self-Loop tikitaka flow
└── MODE_TIKITAKA.md     # Iterate until 98% quality
```

---

## Migration Status

```
042_add_prompty_tables.py  → 4 tables
043_add_jsonb_indexes.py   → JSONB GIN indexes
```
