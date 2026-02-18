# Foundry Rally Sprint 3+4 — Council Core + Feedback Loop + C2PA

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the Model Council inference layer (3-model parallel query + synthesizer), add human feedback UI to the dashboard, and upgrade C2PA from demo to production-grade manifest.

**Architecture:** Council is a new `council/` sub-package inside `backend/app/features/original_ip_foundry/` with 4 files: provider port, orchestrator, synthesizer, and config. The frontend adds Accept/Edit/Reject interactions to the existing RecommendationFeedPanel. C2PA gets cryptographic hash binding via `hashlib` (no external SDK yet).

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy 2.0 async / Pydantic v2 / pytest | Next.js 16 / React 19 / TypeScript / Tailwind

**Constraints:**
- NO OTEL auto-instrumentation (causes Railway server hang)
- NO Redis dependency (`REDIS_ENABLED=False`)
- `print(flush=True)` for Railway stdout
- `evidence_refs` always `List[str]`
- All LLM calls inside sealed capsules
- Council models are called via OpenClaw (Opus) + Agent0 (Codex) + Direct (Gemini) — subscription tokens, cost not a concern

---

## Sprint 3: Council Core (Week 3)

---

### Task 1: Council Provider Port + Config

**Files:**
- Create: `backend/app/features/original_ip_foundry/council/__init__.py`
- Create: `backend/app/features/original_ip_foundry/council/council_config.py`
- Create: `backend/app/features/original_ip_foundry/council/council_provider.py`
- Create: `backend/tests/services/test_foundry_council_provider.py`

**Step 1: Create council package `__init__.py`**

```python
"""Model Council — 3-model parallel inference layer for Foundry."""
```

**Step 2: Write council_config.py**

```python
"""Council configuration — model roles, weights, and timeouts."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CouncilModelRole:
    name: str
    provider: str          # "gemini" | "openclaw" | "agent0" | "direct"
    model_id: str
    role: str              # "visual" | "narrative" | "quantitative" | "synthesizer"
    weight: float = 1.0
    timeout_sec: float = 30.0


DEFAULT_COUNCIL_ROLES: list[CouncilModelRole] = [
    CouncilModelRole(
        name="gemini_visual",
        provider="gemini",
        model_id="gemini-3-pro",
        role="visual",
        weight=1.0,
        timeout_sec=30.0,
    ),
    CouncilModelRole(
        name="opus_narrative",
        provider="openclaw",
        model_id="claude-opus-4-6",
        role="narrative",
        weight=1.2,  # Opus weighted higher for subjective tasks
        timeout_sec=45.0,
    ),
    CouncilModelRole(
        name="codex_quantitative",
        provider="agent0",
        model_id="gpt-5.3-codex",
        role="quantitative",
        weight=1.0,
        timeout_sec=20.0,
    ),
    CouncilModelRole(
        name="gemini_synthesizer",
        provider="gemini",
        model_id="gemini-2.0-flash",
        role="synthesizer",
        weight=1.0,
        timeout_sec=15.0,
    ),
]


CONFIDENCE_TIERS = {
    "high": 0.80,      # 3/3 agree above this
    "medium": 0.60,    # 2/3 agree above this
    "low": 0.0,        # disagreement → human QC
}
```

**Step 3: Write council_provider.py with Protocol + InMemory implementation**

```python
"""Council Provider Port — SSOT §5.4 contract pattern."""
from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from dataclasses import dataclass, field
import uuid


@dataclass
class CouncilInput:
    task_type: str              # "pattern_mining" | "rights_gate" | "continuity"
    context: dict[str, Any]     # extracted features from step 3
    corpus_stats: dict[str, Any] | None = None
    cinema_theory: str | None = None


@dataclass
class ModelResponse:
    model_name: str
    role: str
    output: dict[str, Any]
    confidence: float = 0.0
    latency_ms: float = 0.0


@dataclass
class CouncilVerdict:
    verdict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    consensus_rate: float = 0.0
    confidence_tier: str = "low"
    merged_output: dict[str, Any] = field(default_factory=dict)
    per_model: list[ModelResponse] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)


@runtime_checkable
class CouncilProvider(Protocol):
    """Council Port — model swap via this interface only.

    Switch Drill (D-10): quarterly OpenClaw <-> DirectAPI rehearsal target.
    """

    async def query_visual(self, input: CouncilInput) -> ModelResponse:
        """Visual parsing (default: Gemini 3 Pro)."""
        ...

    async def query_narrative(self, input: CouncilInput) -> ModelResponse:
        """Narrative judgment (default: Opus 4.6 via OpenClaw)."""
        ...

    async def query_quantitative(self, input: CouncilInput) -> ModelResponse:
        """Quantitative analysis (default: Codex 5.3 via Agent0)."""
        ...

    async def synthesize(self, responses: list[ModelResponse]) -> CouncilVerdict:
        """Merge 3 responses into verdict with confidence_tier."""
        ...


class InMemoryCouncilProvider:
    """Test/development implementation — deterministic mock responses."""

    async def query_visual(self, input: CouncilInput) -> ModelResponse:
        return ModelResponse(
            model_name="gemini_visual_mock",
            role="visual",
            output={"pattern_type": input.context.get("pattern_type", "unknown"),
                    "preconditions": input.context.get("preconditions", {})},
            confidence=0.85,
            latency_ms=50.0,
        )

    async def query_narrative(self, input: CouncilInput) -> ModelResponse:
        return ModelResponse(
            model_name="opus_narrative_mock",
            role="narrative",
            output={"expected_effect": "Mock narrative effect",
                    "anti_pattern": "Mock anti-pattern warning"},
            confidence=0.80,
            latency_ms=100.0,
        )

    async def query_quantitative(self, input: CouncilInput) -> ModelResponse:
        return ModelResponse(
            model_name="codex_quantitative_mock",
            role="quantitative",
            output={"execution_template": input.context.get("execution_template", {}),
                    "optimal_duration_range": [2.5, 4.0]},
            confidence=0.90,
            latency_ms=30.0,
        )

    async def synthesize(self, responses: list[ModelResponse]) -> CouncilVerdict:
        confidences = [r.confidence for r in responses]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        high_count = sum(1 for c in confidences if c >= 0.80)

        if high_count == len(confidences):
            tier = "high"
        elif high_count >= len(confidences) * 0.66:
            tier = "medium"
        else:
            tier = "low"

        merged = {}
        for r in responses:
            merged.update(r.output)

        return CouncilVerdict(
            consensus_rate=avg_confidence,
            confidence_tier=tier,
            merged_output=merged,
            per_model=responses,
            disagreements=[],
        )
```

**Step 4: Write failing contract tests**

```python
import pytest
from app.features.original_ip_foundry.council.council_provider import (
    CouncilProvider, InMemoryCouncilProvider, CouncilInput, ModelResponse, CouncilVerdict,
)


class TestCouncilProviderContract:
    """All council implementations must pass these shape tests."""

    @pytest.fixture
    def provider(self):
        return InMemoryCouncilProvider()

    @pytest.fixture
    def sample_input(self):
        return CouncilInput(
            task_type="pattern_mining",
            context={"pattern_type": "camera_motion", "preconditions": {"emotion": "tension"}},
        )

    @pytest.mark.asyncio
    async def test_query_visual_returns_model_response(self, provider, sample_input):
        result = await provider.query_visual(sample_input)
        assert isinstance(result, ModelResponse)
        assert result.role == "visual"
        assert "pattern_type" in result.output

    @pytest.mark.asyncio
    async def test_query_narrative_returns_model_response(self, provider, sample_input):
        result = await provider.query_narrative(sample_input)
        assert isinstance(result, ModelResponse)
        assert result.role == "narrative"
        assert "expected_effect" in result.output

    @pytest.mark.asyncio
    async def test_query_quantitative_returns_model_response(self, provider, sample_input):
        result = await provider.query_quantitative(sample_input)
        assert isinstance(result, ModelResponse)
        assert result.role == "quantitative"
        assert "execution_template" in result.output

    @pytest.mark.asyncio
    async def test_synthesize_returns_verdict(self, provider, sample_input):
        responses = [
            await provider.query_visual(sample_input),
            await provider.query_narrative(sample_input),
            await provider.query_quantitative(sample_input),
        ]
        verdict = await provider.synthesize(responses)
        assert isinstance(verdict, CouncilVerdict)
        assert verdict.confidence_tier in ("high", "medium", "low")
        assert 0.0 <= verdict.consensus_rate <= 1.0
        assert len(verdict.per_model) == 3

    @pytest.mark.asyncio
    async def test_provider_satisfies_protocol(self, provider):
        assert isinstance(provider, CouncilProvider)

    @pytest.mark.asyncio
    async def test_verdict_has_unique_id(self, provider, sample_input):
        responses = [await provider.query_visual(sample_input)]
        v1 = await provider.synthesize(responses)
        v2 = await provider.synthesize(responses)
        assert v1.verdict_id != v2.verdict_id

    @pytest.mark.asyncio
    async def test_high_confidence_tier(self, provider, sample_input):
        # All mocks return >= 0.80 confidence
        responses = [
            await provider.query_visual(sample_input),
            await provider.query_narrative(sample_input),
            await provider.query_quantitative(sample_input),
        ]
        verdict = await provider.synthesize(responses)
        assert verdict.confidence_tier == "high"

    @pytest.mark.asyncio
    async def test_empty_responses_produces_low_tier(self, provider):
        verdict = await provider.synthesize([])
        assert verdict.confidence_tier == "low"
```

**Step 5: Run tests**

```bash
cd /Users/ted/vivid/backend && source venv/bin/activate && pytest tests/services/test_foundry_council_provider.py -v
```

**Step 6: Commit**

```bash
git add backend/app/features/original_ip_foundry/council/ backend/tests/services/test_foundry_council_provider.py
git commit -m "feat(council): add Provider Port + InMemory implementation with contract tests"
```

---

### Task 2: Council Orchestrator

**Files:**
- Create: `backend/app/features/original_ip_foundry/council/council_orchestrator.py`
- Create: `backend/tests/services/test_foundry_council_orchestrator.py`
- Reference: `backend/app/features/original_ip_foundry/council/council_provider.py`
- Reference: `backend/app/features/original_ip_foundry/foundry_observability.py`

**Step 1: Write council_orchestrator.py**

```python
"""Council Orchestrator — asyncio.gather 3-model parallel + synthesize."""
from __future__ import annotations
import asyncio
import time
import json
from typing import Any

from .council_provider import CouncilProvider, CouncilInput, CouncilVerdict, ModelResponse
from .council_config import DEFAULT_COUNCIL_ROLES


class CouncilOrchestrator:
    """Run 3-model Council query and synthesize verdict.

    Architecture: §6.5.3 step 4 (Pattern Mining) insertion point.
    All 3 queries run in parallel via asyncio.gather.
    Synthesizer runs sequentially after all 3 complete.
    """

    def __init__(self, provider: CouncilProvider) -> None:
        self._provider = provider

    async def run(
        self,
        *,
        task_type: str,
        context: dict[str, Any],
        corpus_stats: dict[str, Any] | None = None,
        cinema_theory: str | None = None,
    ) -> CouncilVerdict:
        council_input = CouncilInput(
            task_type=task_type,
            context=context,
            corpus_stats=corpus_stats,
            cinema_theory=cinema_theory,
        )

        start = time.monotonic()

        # Phase 1: 3-model parallel query
        visual_task = asyncio.create_task(
            self._safe_query(self._provider.query_visual, council_input, "visual")
        )
        narrative_task = asyncio.create_task(
            self._safe_query(self._provider.query_narrative, council_input, "narrative")
        )
        quantitative_task = asyncio.create_task(
            self._safe_query(self._provider.query_quantitative, council_input, "quantitative")
        )

        responses = await asyncio.gather(visual_task, narrative_task, quantitative_task)
        valid_responses = [r for r in responses if r is not None]

        # Phase 2: Synthesize
        verdict = await self._provider.synthesize(valid_responses)

        elapsed_ms = (time.monotonic() - start) * 1000

        # Structured log for Railway stdout
        print(json.dumps({
            "event": "council.run",
            "task_type": task_type,
            "models_queried": len(responses),
            "models_responded": len(valid_responses),
            "consensus_rate": verdict.consensus_rate,
            "confidence_tier": verdict.confidence_tier,
            "latency_ms": round(elapsed_ms, 1),
            "disagreements": verdict.disagreements,
        }), flush=True)

        return verdict

    async def _safe_query(
        self,
        query_fn,
        council_input: CouncilInput,
        role: str,
    ) -> ModelResponse | None:
        """Run query with error handling — never let one model failure break the Council."""
        try:
            return await query_fn(council_input)
        except Exception as exc:
            print(json.dumps({
                "event": "council.query_failed",
                "role": role,
                "error": str(exc),
            }), flush=True)
            return None
```

**Step 2: Write tests**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.features.original_ip_foundry.council.council_orchestrator import CouncilOrchestrator
from app.features.original_ip_foundry.council.council_provider import (
    InMemoryCouncilProvider, CouncilInput, ModelResponse, CouncilVerdict,
)


class TestCouncilOrchestrator:

    @pytest.fixture
    def orchestrator(self):
        return CouncilOrchestrator(provider=InMemoryCouncilProvider())

    @pytest.mark.asyncio
    async def test_run_returns_verdict(self, orchestrator):
        verdict = await orchestrator.run(
            task_type="pattern_mining",
            context={"pattern_type": "camera_motion"},
        )
        assert isinstance(verdict, CouncilVerdict)
        assert len(verdict.per_model) == 3

    @pytest.mark.asyncio
    async def test_run_all_roles_queried(self, orchestrator):
        verdict = await orchestrator.run(
            task_type="pattern_mining",
            context={},
        )
        roles = {r.role for r in verdict.per_model}
        assert roles == {"visual", "narrative", "quantitative"}

    @pytest.mark.asyncio
    async def test_run_with_one_model_failure(self):
        provider = InMemoryCouncilProvider()
        provider.query_narrative = AsyncMock(side_effect=RuntimeError("timeout"))
        orchestrator = CouncilOrchestrator(provider=provider)

        verdict = await orchestrator.run(
            task_type="pattern_mining",
            context={},
        )
        # Should still succeed with 2/3 models
        assert len(verdict.per_model) == 2

    @pytest.mark.asyncio
    async def test_run_with_all_failures(self):
        provider = InMemoryCouncilProvider()
        provider.query_visual = AsyncMock(side_effect=RuntimeError("fail"))
        provider.query_narrative = AsyncMock(side_effect=RuntimeError("fail"))
        provider.query_quantitative = AsyncMock(side_effect=RuntimeError("fail"))
        orchestrator = CouncilOrchestrator(provider=provider)

        verdict = await orchestrator.run(
            task_type="pattern_mining",
            context={},
        )
        assert len(verdict.per_model) == 0
        assert verdict.confidence_tier == "low"

    @pytest.mark.asyncio
    async def test_run_passes_context_to_all_models(self):
        provider = InMemoryCouncilProvider()
        provider.query_visual = AsyncMock(return_value=ModelResponse(
            model_name="test", role="visual", output={}, confidence=0.9
        ))
        provider.query_narrative = AsyncMock(return_value=ModelResponse(
            model_name="test", role="narrative", output={}, confidence=0.9
        ))
        provider.query_quantitative = AsyncMock(return_value=ModelResponse(
            model_name="test", role="quantitative", output={}, confidence=0.9
        ))
        orchestrator = CouncilOrchestrator(provider=provider)

        await orchestrator.run(
            task_type="rights_gate",
            context={"asset_id": "test123"},
            cinema_theory="Bordwell framework",
        )

        for mock in [provider.query_visual, provider.query_narrative, provider.query_quantitative]:
            call_args = mock.call_args[0][0]
            assert call_args.task_type == "rights_gate"
            assert call_args.context["asset_id"] == "test123"

    @pytest.mark.asyncio
    async def test_run_task_types(self, orchestrator):
        for task_type in ["pattern_mining", "rights_gate", "continuity"]:
            verdict = await orchestrator.run(task_type=task_type, context={})
            assert isinstance(verdict, CouncilVerdict)
```

**Step 3: Run tests**

```bash
pytest tests/services/test_foundry_council_orchestrator.py -v
```

**Step 4: Commit**

```bash
git add backend/app/features/original_ip_foundry/council/council_orchestrator.py backend/tests/services/test_foundry_council_orchestrator.py
git commit -m "feat(council): add orchestrator with asyncio.gather parallel query"
```

---

### Task 3: Council Synthesizer — Structured Merge

**Files:**
- Create: `backend/app/features/original_ip_foundry/council/council_synthesizer.py`
- Create: `backend/tests/services/test_foundry_council_synthesizer.py`

**Step 1: Write council_synthesizer.py**

Dedicated synthesizer logic that replaces InMemoryCouncilProvider's naive merge with:
- Confidence-weighted field merging
- Disagreement detection (when models assign different `pattern_type`)
- Automatic `confidence_tier` classification
- Structured `council_metadata` for Qdrant payload

**Step 2: Write tests (~15 tests)**

Test cases:
- All 3 agree → high confidence
- 2/3 agree → medium confidence
- All disagree → low confidence + disagreements list populated
- Weighted merge: Opus output weighted 1.2x for narrative fields
- Empty responses → graceful degradation
- Mixed task types produce different merge strategies

**Step 3: Run tests, commit**

```bash
pytest tests/services/test_foundry_council_synthesizer.py -v
git add backend/app/features/original_ip_foundry/council/council_synthesizer.py backend/tests/services/test_foundry_council_synthesizer.py
git commit -m "feat(council): add structured synthesizer with confidence tiering"
```

---

### Task 4: Council API Endpoint

**Files:**
- Modify: `backend/app/features/original_ip_foundry/foundry_router.py`
- Create: `backend/tests/services/test_foundry_council_api.py`

**Step 1: Add Council endpoint to foundry_router.py**

Add `POST /api/v1/foundry/council/query` endpoint:

```python
@router.post("/council/query")
async def council_query(
    request: CouncilQueryRequest,
    # auth: depends
) -> CouncilQueryResponse:
    """Run Model Council on given context.

    Inputs: task_type, context, corpus_stats (optional), cinema_theory (optional)
    Returns: CouncilVerdict with consensus_rate, confidence_tier, merged_output
    """
    provider = InMemoryCouncilProvider()  # swap via config later
    orchestrator = CouncilOrchestrator(provider=provider)
    verdict = await orchestrator.run(
        task_type=request.task_type,
        context=request.context,
        corpus_stats=request.corpus_stats,
        cinema_theory=request.cinema_theory,
    )
    return CouncilQueryResponse(
        verdict_id=verdict.verdict_id,
        consensus_rate=verdict.consensus_rate,
        confidence_tier=verdict.confidence_tier,
        merged_output=verdict.merged_output,
        per_model=[...],
        disagreements=verdict.disagreements,
    )
```

**Step 2: Add Pydantic request/response schemas**

**Step 3: Write API tests**

**Step 4: Run tests, commit**

```bash
pytest tests/services/test_foundry_council_api.py -v
git add backend/app/features/original_ip_foundry/foundry_router.py backend/tests/services/test_foundry_council_api.py
git commit -m "feat(council): add POST /foundry/council/query API endpoint"
```

---

### Task 5: Wire Council into Pattern Extraction

**Files:**
- Modify: `backend/app/features/original_ip_foundry/pattern_extraction_service.py`
- Create: `backend/tests/services/test_foundry_pattern_council_integration.py`

**Step 1: Add `council_enrich` method to PatternExtractionService**

After existing `extract()` generates base pattern atoms, optionally call Council to fill:
- `expected_effect` (from Opus narrative response)
- `anti_pattern` (from Opus narrative response)
- `execution_template` optimal values (from Codex quantitative response)
- `council_metadata` (consensus_rate, confidence_tier, models list)

**Step 2: Feature flag `AD_FOUNDRY_COUNCIL_ENABLED` (default: False)**

Add to `config.py`. When False, pattern extraction works exactly as before.

**Step 3: Write integration tests**

- Test: council disabled → no council_metadata in output
- Test: council enabled → expected_effect populated
- Test: council partial failure → graceful degradation, base pattern still returned

**Step 4: Run tests, commit**

```bash
pytest tests/services/test_foundry_pattern_council_integration.py -v
git add backend/app/features/original_ip_foundry/pattern_extraction_service.py backend/app/config.py backend/tests/services/test_foundry_pattern_council_integration.py
git commit -m "feat(council): wire Council into pattern extraction step 4"
```

---

### Task 6: Frontend — Council Types + API Methods

**Files:**
- Modify: `frontend/src/lib/api.ts`

**Step 1: Add Council types and API method**

```typescript
// Types
export interface CouncilQueryRequest {
  task_type: "pattern_mining" | "rights_gate" | "continuity";
  context: Record<string, unknown>;
  corpus_stats?: Record<string, unknown>;
  cinema_theory?: string;
}

export interface CouncilModelResult {
  model_name: string;
  role: string;
  output: Record<string, unknown>;
  confidence: number;
  latency_ms: number;
}

export interface CouncilQueryResponse {
  verdict_id: string;
  consensus_rate: number;
  confidence_tier: "high" | "medium" | "low";
  merged_output: Record<string, unknown>;
  per_model: CouncilModelResult[];
  disagreements: string[];
}

// API method
async queryFoundryCouncil(request: CouncilQueryRequest): Promise<CouncilQueryResponse> {
  return this.post("/api/v1/foundry/council/query", request);
}
```

**Step 2: Verify build**

```bash
cd /Users/ted/vivid/frontend && npm run build
```

**Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(council): add Council types and API method to frontend"
```

---

### Sprint 3 Checkpoint

```bash
cd /Users/ted/vivid/backend && source venv/bin/activate && pytest --tb=short -q
cd /Users/ted/vivid/frontend && npm run build
```

---

## Sprint 4: Feedback Loop + C2PA + Dashboard Enhancement (Week 4)

---

### Task 7: Backend — Feedback Event Recording

**Files:**
- Modify: `backend/app/features/original_ip_foundry/foundry_router.py`
- Reference: `backend/app/features/original_ip_foundry/experiment_service.py` (line 116: `record_feedback`)
- Create: `backend/tests/services/test_foundry_feedback_api.py`

**Step 1: Add dedicated feedback endpoint**

```python
@router.post("/recommendations/{recommendation_id}/feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    request: RecommendationFeedbackRequest,
) -> RecommendationFeedbackResponse:
    """Record accept/edit/reject for a specific recommendation.

    Wires into experiment_service.record_feedback for Thompson Sampling.
    """
```

Request schema:
```python
class RecommendationFeedbackRequest(BaseModel):
    decision: Literal["accepted", "edited", "rejected"]
    edit_details: str | None = None   # what was changed if "edited"
    tenant_id: str
    project_id: str
    experiment_key: str | None = None
    variant_id: str | None = None
```

**Step 2: Write tests (8 tests)**

- accept → reward 1.0 recorded
- edit → reward 0.5 recorded
- reject → reward 0.0 recorded
- missing tenant_id → 422
- feedback updates experiment stats
- duplicate feedback → idempotent
- edit_details saved when decision is "edited"
- unknown recommendation_id → 404

**Step 3: Run tests, commit**

```bash
pytest tests/services/test_foundry_feedback_api.py -v
git add backend/app/features/original_ip_foundry/foundry_router.py backend/tests/services/test_foundry_feedback_api.py
git commit -m "feat(feedback): add recommendation feedback API endpoint"
```

---

### Task 8: Frontend — Feedback Interaction UI

**Files:**
- Modify: `frontend/src/components/dimension/foundry/RecommendationFeedPanel.tsx`
- Modify: `frontend/src/lib/api.ts` (add feedback types/method)

**Step 1: Add feedback types to api.ts**

```typescript
export interface RecommendationFeedbackRequest {
  decision: "accepted" | "edited" | "rejected";
  edit_details?: string;
  tenant_id: string;
  project_id: string;
  experiment_key?: string;
  variant_id?: string;
}

async submitRecommendationFeedback(
  recommendationId: string,
  request: RecommendationFeedbackRequest
): Promise<{ success: boolean }> {
  return this.post(`/api/v1/foundry/recommendations/${recommendationId}/feedback`, request);
}
```

**Step 2: Add Accept/Edit/Reject buttons to RecommendationFeedPanel**

For each candidate in the ranked list, add 3 action buttons below the scores:
- Green "Accept" button → calls `submitRecommendationFeedback` with decision: "accepted"
- Amber "Edit" button → opens inline textarea for edit notes → calls with "edited"
- Rose "Reject" button → calls with "rejected"

After feedback: show toast/badge indicating feedback was recorded, disable buttons for that candidate.

**Step 3: Verify build**

```bash
cd /Users/ted/vivid/frontend && npm run build
```

**Step 4: Commit**

```bash
git add frontend/src/components/dimension/foundry/RecommendationFeedPanel.tsx frontend/src/lib/api.ts
git commit -m "feat(feedback): add Accept/Edit/Reject interaction to recommendation panel"
```

---

### Task 9: C2PA Production Upgrade

**Files:**
- Modify: `backend/app/features/original_ip_foundry/c2pa_export_service.py`
- Create: `backend/tests/services/test_foundry_c2pa_production.py`

**Step 1: Add cryptographic hash binding**

Upgrade from detached-only to include:
- `hashlib.sha256` content hash of the manifest assertions
- `claim_signature` field with HMAC-SHA256 using `AD_FOUNDRY_C2PA_SECRET` from config
- `binding.alg` and `binding.hash` fields per C2PA 2.2 spec
- Remove the "detached manifest only" warning when binding is present

**Step 2: Add `AD_FOUNDRY_C2PA_SECRET` to config.py**

```python
AD_FOUNDRY_C2PA_SECRET: str = ""  # Empty = detached mode, set for signed mode
```

**Step 3: Write tests (10 tests)**

- Without secret → detached mode, warning present
- With secret → signed mode, no "detached" warning
- Hash is deterministic for same input
- Hash changes when any assertion changes
- Claim signature verifiable with same secret
- Ingredients properly hashed
- EU AI Act compliance fields always present
- Empty provenance → warning about legal review
- Multiple ingredients → each gets unique instance_id
- Export round-trip: export → verify hash → pass

**Step 4: Run tests, commit**

```bash
pytest tests/services/test_foundry_c2pa_production.py -v
git add backend/app/features/original_ip_foundry/c2pa_export_service.py backend/app/config.py backend/tests/services/test_foundry_c2pa_production.py
git commit -m "feat(c2pa): upgrade to production manifest with HMAC-SHA256 binding"
```

---

### Task 10: Council Panel for Dashboard

**Files:**
- Create: `frontend/src/components/dimension/foundry/CouncilPanel.tsx`
- Modify: `frontend/src/components/dimension/foundry/index.ts`
- Modify: `frontend/src/app/dimension/foundry/page.tsx`
- Modify: `frontend/src/components/dimension/foundry/demo-data.ts`

**Step 1: Add demo data for Council**

```typescript
export const DEMO_COUNCIL_REQUEST: CouncilQueryRequest = {
  task_type: "pattern_mining",
  context: {
    pattern_type: "camera_motion",
    camera_motion: "dolly_in",
    shot_scale: "MS_to_CU",
    emotion_state: "tension_building",
  },
};

export const DEMO_COUNCIL_RESPONSE: CouncilQueryResponse = {
  verdict_id: "demo-verdict-001",
  consensus_rate: 0.92,
  confidence_tier: "high",
  merged_output: {
    pattern_type: "camera_motion",
    expected_effect: "Forces audience gaze into character's inner world...",
    anti_pattern: "Cutting away immediately after dolly-in breaks emotion...",
    execution_template: { duration_range: [2.4, 4.0], transition: "dissolve" },
  },
  per_model: [
    { model_name: "gemini_3_pro", role: "visual", output: {}, confidence: 0.88, latency_ms: 320 },
    { model_name: "opus_4_6", role: "narrative", output: {}, confidence: 0.92, latency_ms: 890 },
    { model_name: "codex_5_3", role: "quantitative", output: {}, confidence: 0.95, latency_ms: 210 },
  ],
  disagreements: [],
};
```

**Step 2: Build CouncilPanel**

- "Run Council" button that calls `api.queryFoundryCouncil()`
- Shows 3 model responses side-by-side with role badges (Visual/Narrative/Quantitative)
- Confidence bars per model
- Consensus rate + confidence tier badge at top
- Disagreements section (if any)

**Step 3: Add to page.tsx — expand to 3-column grid on xl**

```tsx
<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 p-6 max-w-[1400px] mx-auto">
  <RightsStatusPanel />
  <PatternLibraryPanel />
  <CouncilPanel />
  <RecommendationFeedPanel />
  <ExperimentResultsPanel />
</div>
```

**Step 4: Verify build, commit**

```bash
cd /Users/ted/vivid/frontend && npm run build
git add frontend/src/components/dimension/foundry/ frontend/src/app/dimension/foundry/page.tsx
git commit -m "feat(council): add Council panel to Foundry dashboard"
```

---

### Task 11: Director's Council Prototype (Creative Idea #1)

**Files:**
- Create: `backend/app/features/original_ip_foundry/council/director_personas.py`
- Modify: `backend/app/features/original_ip_foundry/council/council_config.py`
- Create: `backend/tests/services/test_foundry_director_council.py`

**Step 1: Define director persona prompts**

```python
DIRECTOR_PERSONAS = {
    "bong": {
        "name": "Bong Joon-ho",
        "system_prompt": "You are Bong Joon-ho analyzing a scene. Focus on: vertical space as class metaphor, dark comedy timing, genre-mixing tension...",
        "specialty": ["spatial_hierarchy", "genre_subversion", "dark_comedy"],
    },
    "hitchcock": {
        "name": "Alfred Hitchcock",
        "system_prompt": "You are Hitchcock analyzing a scene. Focus on: audience information asymmetry (they know, character doesn't), POV shots, suspense building...",
        "specialty": ["suspense", "pov", "audience_psychology"],
    },
    "kubrick": {
        "name": "Stanley Kubrick",
        "system_prompt": "You are Kubrick analyzing a scene. Focus on: symmetrical composition, one-point perspective, obsessive detail, cold precision...",
        "specialty": ["symmetry", "one_point_perspective", "precision"],
    },
    "wong_kar_wai": {
        "name": "Wong Kar-wai",
        "system_prompt": "You are Wong Kar-wai analyzing a scene. Focus on: color saturation, temporal displacement, incomplete memory, romantic melancholy...",
        "specialty": ["color", "time", "memory", "melancholy"],
    },
}
```

**Step 2: Add `POST /api/v1/foundry/council/director-review` endpoint**

Input: scene context + list of 3 director keys
Output: 3 director-persona reviews + synthesized "coaching summary"

**Step 3: Write tests**

- Default 3 directors return persona-specific analysis
- Custom director selection works
- Invalid director key → 422
- Synthesizer summarizes across 3 perspectives

**Step 4: Run tests, commit**

```bash
pytest tests/services/test_foundry_director_council.py -v
git add backend/app/features/original_ip_foundry/council/ backend/tests/services/test_foundry_director_council.py
git commit -m "feat(council): Director's Council prototype with persona prompts"
```

---

### Task 12: Full Verification + Deploy

**Step 1: Run full backend tests**

```bash
cd /Users/ted/vivid/backend && source venv/bin/activate && pytest --tb=short -q
```

**Step 2: Run frontend build**

```bash
cd /Users/ted/vivid/frontend && npm run build
```

**Step 3: Push to main**

```bash
git push origin main
```

**Step 4: Deploy**

```bash
# Frontend → Vercel API
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token')
curl -s -X POST "https://api.vercel.com/v13/deployments?skipAutoDetectionConfirmation=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"crebit","project":"crebit","gitSource":{"type":"github","org":"ds4psb-ai","repo":"vivid","ref":"main"},"target":"production"}'

# Backend → Railway
cd /Users/ted/vivid/backend && railway up --service vivid --detach
```

---

## Task Dependency Graph

```
Sprint 3 (Council Core)
========================
T1 (Provider Port)     ──┐
                         ├── T2 depends on T1
T2 (Orchestrator)      ──┤
                         ├── T3 depends on T1
T3 (Synthesizer)       ──┘
T4 (Council API)       ── depends on T1+T2+T3
T5 (Pattern Integration)── depends on T4
T6 (Frontend Types)    ── independent (can parallel with T4-T5)

Sprint 4 (Feedback + C2PA + Dashboard)
========================================
T7 (Feedback API)      ── independent
T8 (Feedback UI)       ── depends on T7
T9 (C2PA Upgrade)      ── independent
T10 (Council Panel)    ── depends on T6
T11 (Director Council) ── depends on T1+T2
T12 (Deploy)           ── depends on all

Parallelizable groups:
- Group A: T1 → T2 → T3 → T4 → T5 (Council pipeline, sequential)
- Group B: T6 (frontend, parallel with Group A after T1)
- Group C: T7 → T8 (feedback pipeline)
- Group D: T9 (C2PA, fully independent)
- Group E: T10 (Council Panel, depends on T6)
- Group F: T11 (Director Council, depends on T1+T2)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| OpenClaw/Agent0 API unavailable | InMemoryCouncilProvider always available as fallback. Feature flag `AD_FOUNDRY_COUNCIL_ENABLED` |
| Council latency exceeds p95 budget | asyncio.gather parallel execution + per-model timeout. Synthesizer uses Flash (fastest) |
| Model output format inconsistency | Pydantic validation on all ModelResponse.output. Schema mismatch → confidence_tier downgrade |
| C2PA secret leak | Secret in Railway env var only, never in code. Empty = safe detached mode |
| Feedback spam | Rate limit per tenant_id, idempotent feedback per recommendation_id |

---

## Success Criteria (Sprint 4 Exit)

- [ ] `POST /foundry/council/query` returns verdict with 3 model responses
- [ ] Council wired into pattern extraction (behind feature flag)
- [ ] Accept/Edit/Reject buttons functional in dashboard
- [ ] Feedback events recorded and visible in experiment summary
- [ ] C2PA export includes HMAC-SHA256 binding when secret configured
- [ ] Director's Council returns persona-specific reviews for 3+ directors
- [ ] All backend tests pass, frontend build clean
- [ ] Deployed to Vercel + Railway
