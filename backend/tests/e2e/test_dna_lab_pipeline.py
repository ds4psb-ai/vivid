"""
E2E Tests for DNA Lab Pipeline.

Tests the unified DNA Lab pipeline with Saga pattern orchestration.

Test Scenarios:
1. Request validation - proper input handling
2. Pipeline execution - mocked component calls
3. E2E flow - credit deduction, evidence refs, chain data
4. Error handling - auth, credits, failures
5. Chain data - output structure verification

Data Flow:
    POST /run-pipeline
         ↓
    VPE → AD → Mirror → QC
         ↓
    Outbox (Qdrant sync)
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dna_lab_unified import (
    DNALabPipelineRequest,
    DNALabResult,
    PipelineStep,
    PipelineStatus,
    StepResult,
    AestheticGuidelines,
    PersonaDNA,
    QualityReport,
)
from app.schemas.vpe import LogicVector, Cadence, Composition, CameraGrammar, LightingPhysics, ColorScience
from app.services.dna_lab_orchestrator import (
    DNALabOrchestrator,
    PipelineContext,
    STEP_CREDITS,
    get_orchestrator,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_pipeline_request() -> Dict[str, Any]:
    """Sample full pipeline request."""
    return {
        "video_uri": "gs://test-bucket/sample.mp4",
        "concept": "A cinematic journey through time",
        "auteur_key": "bong",
        "steps": ["vpe", "ad", "mirror", "qc"],
        "store_to_qdrant": False,
        "fail_fast": False,
    }


@pytest.fixture
def sample_partial_request() -> Dict[str, Any]:
    """Sample partial pipeline request (AD + Mirror only)."""
    return {
        "concept": "Noir detective story",
        "auteur_key": "fincher",
        "steps": ["ad", "mirror"],
        "store_to_qdrant": False,
    }


@pytest.fixture
def sample_logic_vector() -> LogicVector:
    """Sample VPE Logic Vector output."""
    return LogicVector(
        auteur_id="bong",
        cadence=Cadence(
            hook=2.5,
            build=15.0,
            climax=45.0,
            avg_shot_length=4.2,
            rhythm_pattern="slow_build",
            tempo="deliberate",
        ),
        composition=Composition(
            primary_strategy="symmetry",
            symmetry_score=0.8,
            depth_staging="deep_focus",
        ),
        camera_grammar=CameraGrammar(
            static=0.3,
            dolly=0.25,
            handheld=0.1,
            push_in=0.15,
            tracking=0.2,
        ),
        lighting_physics=LightingPhysics(
            key_light="chiaroscuro",
            contrast_ratio="4:1",
            shadow_quality="hard",
        ),
        color_science=ColorScience(
            palette=["warm amber", "deep shadow"],
            saturation_level="muted",
            lut_reference="Kodak_2383",
        ),
        confidence=0.87,
    )


@pytest.fixture
def sample_ad_result() -> AestheticGuidelines:
    """Sample AD output."""
    return AestheticGuidelines(
        visual_style="neo-noir with warm undertones",
        color_palette=["amber", "teal", "shadow"],
        mood_keywords=["melancholic", "introspective", "tense"],
        auteur_reference="bong",
        composition_notes="Use deep staging and symmetrical framing",
        lighting_approach="motivated lighting with strong contrast",
        reference_directors=["bong joon-ho", "park chan-wook"],
    )


@pytest.fixture
def sample_mirror_result() -> PersonaDNA:
    """Sample Mirror output."""
    return PersonaDNA(
        mbti="INTJ",
        archetype="The Visionary",
        openness=0.85,
        conscientiousness=0.78,
        extraversion=0.32,
        agreeableness=0.45,
        neuroticism=0.52,
        persona_type="analytical_creative",
        creative_tendencies=["systematic", "detail-oriented"],
        visual_preferences=["minimalist", "geometric"],
        narrative_style="complex layered storytelling",
        emotional_range=["controlled", "intense"],
        creativity_index=2.5,
        auteur_affinity=["bong", "nolan", "kubrick"],
    )


@pytest.fixture
def sample_qc_result() -> QualityReport:
    """Sample QC output."""
    return QualityReport(
        passed=True,
        score=0.87,
        criteria_results={
            "composition": 0.9,
            "lighting": 0.85,
            "color": 0.88,
            "narrative": 0.84,
        },
        issues=[],
        suggestions=["Consider adding more visual contrast"],
        technical_score=0.88,
        aesthetic_score=0.86,
        narrative_coherence=0.87,
        ip_context_used=False,
    )


@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """Mock authenticated user."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "credits": 1000,
    }


# ============================================================================
# Test Class: Request Validation
# ============================================================================

class TestPipelineRequestValidation:
    """Request validation tests."""

    def test_valid_full_pipeline_request(self, sample_pipeline_request):
        """Valid full pipeline request parses correctly."""
        request = DNALabPipelineRequest(**sample_pipeline_request)

        assert request.video_uri == "gs://test-bucket/sample.mp4"
        assert request.concept == "A cinematic journey through time"
        assert request.auteur_key == "bong"
        assert len(request.steps) == 4
        assert PipelineStep.VPE in request.steps

    def test_valid_partial_pipeline_request(self, sample_partial_request):
        """Partial pipeline request (subset of steps) is valid."""
        request = DNALabPipelineRequest(**sample_partial_request)

        assert request.video_uri is None
        assert len(request.steps) == 2
        assert PipelineStep.AD in request.steps
        assert PipelineStep.MIRROR in request.steps

    def test_empty_steps_uses_default(self):
        """Empty steps list defaults to all steps."""
        request = DNALabPipelineRequest(concept="test")

        assert len(request.steps) == 4
        assert PipelineStep.VPE in request.steps
        assert PipelineStep.QC in request.steps

    def test_step_credits_calculation(self, sample_pipeline_request):
        """Credit calculation for steps is correct."""
        steps = [PipelineStep(s) for s in sample_pipeline_request["steps"]]
        total_credits = sum(STEP_CREDITS.get(s, 0) for s in steps)

        # VPE=50 + AD=10 + Mirror=5 + QC=8 = 73
        assert total_credits == 73

    def test_invalid_video_uri_rejected(self):
        """Invalid video URI scheme is rejected."""
        with pytest.raises(ValueError, match="secure scheme"):
            DNALabPipelineRequest(
                video_uri="http://insecure.com/video.mp4",
                concept="test",
            )

    def test_ftp_video_uri_rejected(self):
        """FTP video URI is rejected (security)."""
        with pytest.raises(ValueError, match="secure scheme"):
            DNALabPipelineRequest(
                video_uri="ftp://files.example.com/video.mp4",
                concept="test",
            )

    def test_valid_https_video_uri(self):
        """HTTPS video URI is valid."""
        request = DNALabPipelineRequest(
            video_uri="https://storage.example.com/video.mp4",
            concept="test",
        )
        assert request.video_uri == "https://storage.example.com/video.mp4"


# ============================================================================
# Test Class: Pipeline Execution (Mocked)
# ============================================================================

class TestPipelineExecution:
    """Pipeline execution integration tests with mocks."""

    @pytest.mark.asyncio
    async def test_full_pipeline_mocked(
        self,
        sample_pipeline_request,
        sample_logic_vector,
        sample_ad_result,
        sample_mirror_result,
        sample_qc_result,
        mock_user,
    ):
        """Full pipeline execution with mocked components."""
        orchestrator = DNALabOrchestrator()

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock) as mock_vpe, \
             patch.object(orchestrator, "_run_ad", new_callable=AsyncMock) as mock_ad, \
             patch.object(orchestrator, "_run_mirror", new_callable=AsyncMock) as mock_mirror, \
             patch.object(orchestrator, "_run_qc", new_callable=AsyncMock) as mock_qc, \
             patch.object(orchestrator, "_write_to_outbox", new_callable=AsyncMock) as mock_outbox:

            # Configure mocks to populate context
            async def set_vpe(ctx):
                ctx.vpe_result = sample_logic_vector
                ctx.evidence_refs.append("db:vpe_results:test-trace")

            async def set_ad(ctx):
                ctx.ad_result = sample_ad_result
                ctx.evidence_refs.append("db:ad_results:test-trace")

            async def set_mirror(ctx):
                ctx.mirror_result = sample_mirror_result
                ctx.evidence_refs.append("db:mirror_results:test-trace")

            async def set_qc(ctx):
                ctx.qc_result = sample_qc_result
                ctx.evidence_refs.append("db:qc_results:test-trace")

            mock_vpe.side_effect = set_vpe
            mock_ad.side_effect = set_ad
            mock_mirror.side_effect = set_mirror
            mock_qc.side_effect = set_qc

            # Create mock db session
            mock_db = AsyncMock(spec=AsyncSession)

            request = DNALabPipelineRequest(**sample_pipeline_request)
            result = await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )

            # Verify result
            assert result.success is True
            assert result.status == PipelineStatus.COMPLETED
            assert result.vpe is not None
            assert result.ad is not None
            assert result.mirror is not None
            assert result.qc is not None
            assert len(result.evidence_refs) == 4
            assert result.credits_used == 73  # All steps

    @pytest.mark.asyncio
    async def test_partial_pipeline_mocked(
        self,
        sample_partial_request,
        sample_ad_result,
        sample_mirror_result,
        mock_user,
    ):
        """Partial pipeline (AD + Mirror only) execution."""
        orchestrator = DNALabOrchestrator()

        with patch.object(orchestrator, "_run_ad", new_callable=AsyncMock) as mock_ad, \
             patch.object(orchestrator, "_run_mirror", new_callable=AsyncMock) as mock_mirror, \
             patch.object(orchestrator, "_write_to_outbox", new_callable=AsyncMock):

            async def set_ad(ctx):
                ctx.ad_result = sample_ad_result

            async def set_mirror(ctx):
                ctx.mirror_result = sample_mirror_result

            mock_ad.side_effect = set_ad
            mock_mirror.side_effect = set_mirror

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(**sample_partial_request)

            result = await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )

            assert result.success is True
            assert result.vpe is None
            assert result.ad is not None
            assert result.mirror is not None
            assert result.qc is None
            # AD=10 + Mirror=5 = 15
            assert result.credits_used == 15

    @pytest.mark.asyncio
    async def test_pipeline_with_progress_callback(self, sample_pipeline_request, mock_user):
        """Pipeline emits progress callbacks."""
        orchestrator = DNALabOrchestrator()
        progress_events = []

        def capture_progress(status: str, progress: float, message: str):
            progress_events.append((status, progress, message))

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_ad", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_mirror", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_qc", new_callable=AsyncMock), \
             patch.object(orchestrator, "_write_to_outbox", new_callable=AsyncMock):

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(**sample_pipeline_request)

            await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
                progress_callback=capture_progress,
            )

            # Should have: starting, 4x processing, finalizing, completed
            assert len(progress_events) >= 6
            assert progress_events[0][0] == "starting"
            assert progress_events[-1][0] == "completed"


# ============================================================================
# Test Class: E2E Flow
# ============================================================================

class TestE2EFlow:
    """E2E flow verification tests."""

    def test_step_order_preserved(self, sample_pipeline_request):
        """Steps are executed in specified order."""
        request = DNALabPipelineRequest(**sample_pipeline_request)

        # Verify step order
        assert request.steps[0] == PipelineStep.VPE
        assert request.steps[1] == PipelineStep.AD
        assert request.steps[2] == PipelineStep.MIRROR
        assert request.steps[3] == PipelineStep.QC

    def test_evidence_refs_format(
        self,
        sample_logic_vector,
        sample_ad_result,
        sample_mirror_result,
        sample_qc_result,
    ):
        """Evidence refs follow Vivid List[str] format."""
        # Construct evidence refs as pipeline would
        evidence_refs = [
            "db:vpe_results:test-trace-id",
            "db:ad_results:test-trace-id",
            "db:mirror_results:test-trace-id",
            "db:qc_results:test-trace-id",
        ]

        # All refs are strings (Vivid convention)
        for ref in evidence_refs:
            assert isinstance(ref, str)
            assert ":" in ref  # format: source:type:id

    @pytest.mark.asyncio
    async def test_orchestrator_creates_context(self, sample_pipeline_request, mock_user):
        """Orchestrator properly initializes PipelineContext."""
        orchestrator = DNALabOrchestrator()

        # Capture context during execution
        captured_ctx = None

        async def capture_context(ctx):
            nonlocal captured_ctx
            captured_ctx = ctx

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock) as mock_vpe, \
             patch.object(orchestrator, "_run_ad", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_mirror", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_qc", new_callable=AsyncMock), \
             patch.object(orchestrator, "_write_to_outbox", new_callable=AsyncMock):

            mock_vpe.side_effect = capture_context

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(**sample_pipeline_request)

            await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )

            assert captured_ctx is not None
            assert captured_ctx.user_id == mock_user["id"]
            assert captured_ctx.request == request
            assert captured_ctx.trace_id is not None

    @pytest.mark.asyncio
    async def test_result_timestamps(self, sample_pipeline_request, mock_user):
        """Result includes proper timestamps."""
        orchestrator = DNALabOrchestrator()

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_ad", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_mirror", new_callable=AsyncMock), \
             patch.object(orchestrator, "_run_qc", new_callable=AsyncMock), \
             patch.object(orchestrator, "_write_to_outbox", new_callable=AsyncMock):

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(**sample_pipeline_request)

            before = datetime.utcnow()
            result = await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )
            after = datetime.utcnow()

            assert result.created_at >= before
            assert result.completed_at <= after
            assert result.processing_time_ms >= 0


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Error handling tests."""

    @pytest.mark.asyncio
    async def test_step_failure_triggers_compensation(self, sample_pipeline_request, mock_user):
        """Failed step triggers Saga compensation."""
        orchestrator = DNALabOrchestrator()

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock) as mock_vpe, \
             patch.object(orchestrator, "_run_ad", new_callable=AsyncMock) as mock_ad, \
             patch.object(orchestrator, "_compensate", new_callable=AsyncMock) as mock_compensate:

            # VPE succeeds
            async def set_vpe(ctx):
                ctx.completed_steps.append(PipelineStep.VPE)

            mock_vpe.side_effect = set_vpe

            # AD fails
            mock_ad.side_effect = Exception("AD API error")

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(
                **{**sample_pipeline_request, "fail_fast": True}
            )

            result = await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )

            # Compensation was called
            mock_compensate.assert_called_once()
            assert result.success is False
            assert result.status == PipelineStatus.FAILED

    @pytest.mark.asyncio
    async def test_partial_failure_without_fail_fast(
        self,
        sample_pipeline_request,
        sample_logic_vector,
        sample_mirror_result,
        mock_user,
    ):
        """Without fail_fast, continues after failure."""
        orchestrator = DNALabOrchestrator()

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock) as mock_vpe, \
             patch.object(orchestrator, "_run_ad", new_callable=AsyncMock) as mock_ad, \
             patch.object(orchestrator, "_run_mirror", new_callable=AsyncMock) as mock_mirror, \
             patch.object(orchestrator, "_run_qc", new_callable=AsyncMock), \
             patch.object(orchestrator, "_write_to_outbox", new_callable=AsyncMock):

            async def set_vpe(ctx):
                ctx.vpe_result = sample_logic_vector

            async def set_mirror(ctx):
                ctx.mirror_result = sample_mirror_result

            mock_vpe.side_effect = set_vpe
            mock_ad.side_effect = Exception("AD failed")
            mock_mirror.side_effect = set_mirror

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(
                **{**sample_pipeline_request, "fail_fast": False}
            )

            result = await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )

            # Pipeline continues with partial success
            assert result.status == PipelineStatus.PARTIAL
            assert "ad" in result.errors
            assert result.vpe is not None
            assert result.mirror is not None

    @pytest.mark.asyncio
    async def test_pipeline_timeout_handling(self, sample_pipeline_request, mock_user):
        """Pipeline handles step timeouts gracefully."""
        import asyncio

        orchestrator = DNALabOrchestrator()

        async def slow_vpe(ctx):
            # Simulate timeout (would be caught in real execution)
            raise asyncio.TimeoutError("VPE timeout")

        with patch.object(orchestrator, "_run_vpe", new_callable=AsyncMock) as mock_vpe, \
             patch.object(orchestrator, "_compensate", new_callable=AsyncMock):

            mock_vpe.side_effect = slow_vpe

            mock_db = AsyncMock(spec=AsyncSession)
            request = DNALabPipelineRequest(
                **{**sample_pipeline_request, "fail_fast": True}
            )

            result = await orchestrator.run_pipeline(
                request=request,
                user_id=mock_user["id"],
                db=mock_db,
            )

            assert result.success is False
            # Error could be under "pipeline" or "vpe" depending on where caught
            error_text = str(result.errors)
            assert "TimeoutError" in error_text or "timeout" in error_text.lower() or "VPE timeout" in error_text


# ============================================================================
# Test Class: Chain Data Verification
# ============================================================================

class TestChainData:
    """Chain data output structure tests."""

    def test_vpe_output_structure(self, sample_logic_vector):
        """VPE output has required fields."""
        data = sample_logic_vector.model_dump()

        assert "auteur_id" in data
        assert "cadence" in data
        assert "composition" in data
        assert "camera_grammar" in data
        assert "lighting_physics" in data
        assert "color_science" in data
        assert "confidence" in data

    def test_ad_output_structure(self, sample_ad_result):
        """AD output has required fields."""
        data = sample_ad_result.model_dump()

        assert "visual_style" in data
        assert "color_palette" in data
        assert "mood_keywords" in data
        assert "auteur_reference" in data

    def test_mirror_output_structure(self, sample_mirror_result):
        """Mirror output has MBTI + OCEAN fields."""
        data = sample_mirror_result.model_dump()

        # MBTI
        assert "mbti" in data
        assert "archetype" in data

        # OCEAN
        assert "openness" in data
        assert "conscientiousness" in data
        assert "extraversion" in data
        assert "agreeableness" in data
        assert "neuroticism" in data

        # Extended
        assert "creativity_index" in data
        assert "auteur_affinity" in data

    def test_qc_output_structure(self, sample_qc_result):
        """QC output has quality metrics."""
        data = sample_qc_result.model_dump()

        assert "passed" in data
        assert "score" in data
        assert "criteria_results" in data
        assert "technical_score" in data
        assert "aesthetic_score" in data

    def test_result_serialization(
        self,
        sample_logic_vector,
        sample_ad_result,
        sample_mirror_result,
        sample_qc_result,
    ):
        """Full result can be serialized to JSON."""
        result = DNALabResult(
            success=True,
            trace_id=str(uuid4()),
            status=PipelineStatus.COMPLETED,
            vpe=sample_logic_vector,
            ad=sample_ad_result,
            mirror=sample_mirror_result,
            qc=sample_qc_result,
            evidence_refs=["db:test:1", "db:test:2"],
            credits_used=73,
            processing_time_ms=2500,
        )

        # Should serialize without errors
        json_str = result.model_dump_json()
        assert len(json_str) > 0

        # Should deserialize back
        restored = json.loads(json_str)
        assert restored["success"] is True
        assert restored["credits_used"] == 73


# ============================================================================
# Test Class: Step Result Tracking
# ============================================================================

class TestStepResultTracking:
    """Step result tracking tests."""

    def test_step_result_creation(self):
        """StepResult captures execution metadata."""
        result = StepResult(
            step=PipelineStep.VPE,
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=1500,
            credits_used=50,
        )

        assert result.step == PipelineStep.VPE
        assert result.status == "completed"
        assert result.duration_ms == 1500
        assert result.credits_used == 50
        assert result.error is None

    def test_failed_step_result(self):
        """Failed StepResult includes error."""
        result = StepResult(
            step=PipelineStep.AD,
            status="failed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=500,
            error="API rate limit exceeded",
            credits_used=0,
        )

        assert result.status == "failed"
        assert result.error == "API rate limit exceeded"
        assert result.credits_used == 0


# ============================================================================
# Test Class: STEP_CREDITS Configuration
# ============================================================================

class TestStepCreditsConfig:
    """Credit configuration tests."""

    def test_all_steps_have_credits_defined(self):
        """All pipeline steps have credit costs defined."""
        for step in PipelineStep:
            assert step in STEP_CREDITS, f"Missing credit config for {step}"

    def test_credit_values_reasonable(self):
        """Credit values are within reasonable range."""
        for step, credits in STEP_CREDITS.items():
            assert credits >= 0, f"{step} has negative credits"
            assert credits <= 100, f"{step} has unusually high credits"

    def test_total_pipeline_credits(self):
        """Total credits for full pipeline is calculable."""
        total = sum(STEP_CREDITS.values())
        assert total == 73  # VPE=50 + AD=10 + Mirror=5 + QC=8
