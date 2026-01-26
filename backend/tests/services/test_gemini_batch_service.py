"""Tests for Gemini Batch API Service.

Batch API는 비실시간 작업을 50% 저렴하게 처리합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.gemini_batch_service import (
    GeminiBatchService,
    BatchRequest,
    BatchResponse,
    BatchJob,
    BatchJobStatus,
    BatchModel,
    BATCH_PRICING_PER_1M_TOKENS,
    get_batch_service,
    batch_generate,
    batch_evaluate_rag,
)


class TestBatchRequest:
    """BatchRequest 데이터 클래스 테스트."""

    def test_create_with_defaults(self):
        """기본값으로 생성."""
        req = BatchRequest(prompt="Hello, world!")
        assert req.prompt == "Hello, world!"
        assert req.system_instruction is None
        assert req.generation_config is None
        assert req.request_id  # Auto-generated
        assert req.metadata == {}

    def test_create_with_all_fields(self):
        """모든 필드 지정."""
        req = BatchRequest(
            prompt="Test prompt",
            system_instruction="Be helpful",
            generation_config={"temperature": 0.7},
            request_id="test-123",
            metadata={"key": "value"},
        )
        assert req.prompt == "Test prompt"
        assert req.system_instruction == "Be helpful"
        assert req.generation_config == {"temperature": 0.7}
        assert req.request_id == "test-123"
        assert req.metadata == {"key": "value"}


class TestBatchResponse:
    """BatchResponse 데이터 클래스 테스트."""

    def test_success_response(self):
        """성공 응답."""
        resp = BatchResponse(
            request_id="req-1",
            success=True,
            content="Generated text",
            usage={"input": 100, "output": 50},
        )
        assert resp.success is True
        assert resp.content == "Generated text"
        assert resp.error is None

    def test_failure_response(self):
        """실패 응답."""
        resp = BatchResponse(
            request_id="req-1",
            success=False,
            error="Rate limit exceeded",
        )
        assert resp.success is False
        assert resp.content is None
        assert resp.error == "Rate limit exceeded"


class TestBatchJob:
    """BatchJob 데이터 클래스 테스트."""

    def test_create_job(self):
        """배치 작업 생성."""
        job = BatchJob(
            job_id="batch_abc123",
            name="jobs/batch_abc123",
            model="gemini-3-flash-preview",
            status=BatchJobStatus.PENDING,
            total_requests=10,
        )
        assert job.job_id == "batch_abc123"
        assert job.status == BatchJobStatus.PENDING
        assert job.total_requests == 10
        assert job.completed_requests == 0
        assert job.failed_requests == 0
        assert job.results == []


class TestBatchPricing:
    """Batch pricing 테스트 (50% 할인)."""

    def test_pricing_exists_for_all_models(self):
        """모든 BatchModel에 대해 pricing 존재."""
        for model in BatchModel:
            assert model.value in BATCH_PRICING_PER_1M_TOKENS

    def test_pricing_is_half_of_standard(self):
        """Batch 가격이 standard의 50%인지 확인."""
        # Standard pricing for Gemini 3.0 Flash (2x batch pricing)
        standard_3_flash = {"input": 0.50, "output": 3.0}
        batch_3_flash = BATCH_PRICING_PER_1M_TOKENS["gemini-3-flash-preview"]

        # Batch is 50% off
        assert batch_3_flash["input"] == standard_3_flash["input"] / 2
        assert batch_3_flash["output"] == standard_3_flash["output"] / 2


class TestGeminiBatchService:
    """GeminiBatchService 테스트."""

    def test_singleton_instance(self):
        """싱글톤 인스턴스 테스트."""
        service1 = get_batch_service()
        service2 = get_batch_service()
        assert service1 is service2

    def test_estimate_cost(self):
        """비용 추정 테스트."""
        service = GeminiBatchService(api_key="test-key")

        # Use longer prompts to ensure non-zero cost
        requests = [
            BatchRequest(prompt="x" * 1000),  # ~250 tokens
            BatchRequest(prompt="y" * 1000),  # ~250 tokens
        ]

        estimate = service.estimate_cost(requests, "gemini-3-flash-preview")

        assert "estimated_input_tokens" in estimate
        assert "batch_cost_usd" in estimate
        assert "standard_cost_usd" in estimate
        assert "savings_usd" in estimate
        assert estimate["savings_percent"] == 50.0
        # With sufficient tokens, batch should be cheaper than standard
        assert estimate["batch_cost_usd"] < estimate["standard_cost_usd"] or estimate["batch_cost_usd"] == 0

    def test_estimate_cost_shows_savings(self):
        """비용 추정이 50% 절감을 보여주는지 확인."""
        service = GeminiBatchService(api_key="test-key")

        # 1MB of text (roughly 250K tokens)
        requests = [BatchRequest(prompt="x" * 1000) for _ in range(1000)]

        estimate = service.estimate_cost(requests, "gemini-3-flash-preview")

        # Savings should be significant
        assert estimate["savings_usd"] > 0
        assert estimate["savings_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_create_batch_job_validates_input(self):
        """배치 작업 생성 시 입력 검증."""
        service = GeminiBatchService(api_key="test-key")

        # Empty requests should fail
        with pytest.raises(ValueError, match="At least one request required"):
            await service.create_batch_job([])

    @pytest.mark.asyncio
    async def test_create_batch_job_normalizes_dicts(self):
        """dict 형태 요청을 BatchRequest로 변환."""
        service = GeminiBatchService(api_key="test-key")

        # Mock the client
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_batch_job = MagicMock()
            mock_batch_job.name = "jobs/test-batch-123"
            mock_client.batches.create.return_value = mock_batch_job
            mock_get_client.return_value = mock_client

            job = await service.create_batch_job(
                requests=[
                    {"prompt": "Test 1", "system": "System instruction"},
                    {"prompt": "Test 2"},
                ],
                model="gemini-3-flash-preview",
            )

            assert job.total_requests == 2
            assert job.status == BatchJobStatus.PENDING


class TestBatchConvenienceFunctions:
    """편의 함수 테스트."""

    @pytest.mark.asyncio
    async def test_batch_generate_basic(self):
        """batch_generate 기본 동작."""
        with patch('app.services.gemini_batch_service.get_batch_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            # Mock job creation and completion
            mock_job = BatchJob(
                job_id="batch_123",
                name="jobs/batch_123",
                model="gemini-3-flash-preview",
                status=BatchJobStatus.COMPLETED,
                total_requests=2,
                completed_requests=2,
                results=[
                    BatchResponse(request_id="0", success=True, content="Result 1"),
                    BatchResponse(request_id="1", success=True, content="Result 2"),
                ],
            )
            mock_service.create_batch_job = AsyncMock(return_value=mock_job)
            mock_service.wait_for_completion = AsyncMock(return_value=mock_job)

            results = await batch_generate(
                prompts=["Prompt 1", "Prompt 2"],
                system_instruction="Be helpful",
            )

            assert results == ["Result 1", "Result 2"]

    @pytest.mark.asyncio
    async def test_batch_evaluate_rag_parses_json(self):
        """batch_evaluate_rag이 JSON 응답을 파싱."""
        with patch('app.services.gemini_batch_service.get_batch_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service

            # Mock job with JSON responses
            mock_job = BatchJob(
                job_id="batch_eval",
                name="jobs/batch_eval",
                model="gemini-3-flash-preview",
                status=BatchJobStatus.COMPLETED,
                total_requests=1,
                completed_requests=1,
                results=[
                    BatchResponse(
                        request_id="0",
                        success=True,
                        content='{"faithfulness": 0.9, "relevancy": 0.8}',
                    ),
                ],
            )
            mock_service.create_batch_job = AsyncMock(return_value=mock_job)
            mock_service.wait_for_completion = AsyncMock(return_value=mock_job)

            results = await batch_evaluate_rag(
                samples=[
                    {"question": "Q1", "answer": "A1", "contexts": ["C1"]},
                ],
                evaluation_prompt_template="Evaluate: {question} {answer} {contexts}",
            )

            assert len(results) == 1
            assert results[0]["faithfulness"] == 0.9
            assert results[0]["relevancy"] == 0.8


class TestRAGEvaluationBatchIntegration:
    """RAG 평가 파이프라인의 Batch API 통합 테스트."""

    @pytest.mark.asyncio
    async def test_evaluate_batch_with_gemini_imports(self):
        """evaluate_batch_with_gemini 메서드가 존재하고 import 가능."""
        from app.rag.evaluation import RAGEvaluationPipeline

        pipeline = RAGEvaluationPipeline()
        assert hasattr(pipeline, 'evaluate_batch_with_gemini')

    def test_build_evaluation_prompt(self):
        """평가 프롬프트 빌드 테스트."""
        from app.rag.evaluation import RAGEvaluationPipeline, EvaluationSample

        pipeline = RAGEvaluationPipeline()
        sample = EvaluationSample(
            question="강주노 감독의 특징은?",
            answer="비선형 서사와 계급 갈등을 다룹니다.",
            contexts=["강주노는 기생충으로 아카데미상을 받았습니다."],
        )

        prompt = pipeline._build_evaluation_prompt(sample)

        assert "강주노" in prompt
        assert "비선형 서사" in prompt
        assert "기생충" in prompt
        assert "faithfulness" in prompt.lower()

    def test_parse_evaluation_response_valid_json(self):
        """유효한 JSON 응답 파싱."""
        from app.rag.evaluation import RAGEvaluationPipeline

        pipeline = RAGEvaluationPipeline()

        # Plain JSON
        scores = pipeline._parse_evaluation_response(
            '{"faithfulness": 0.85, "answer_relevancy": 0.9, "context_precision": 0.75}'
        )
        assert scores["faithfulness"] == 0.85
        assert scores["answer_relevancy"] == 0.9
        assert scores["context_precision"] == 0.75

    def test_parse_evaluation_response_markdown_json(self):
        """마크다운 코드 블록 내 JSON 파싱."""
        from app.rag.evaluation import RAGEvaluationPipeline

        pipeline = RAGEvaluationPipeline()

        # JSON in markdown code block
        scores = pipeline._parse_evaluation_response(
            '```json\n{"faithfulness": 0.8, "answer_relevancy": 0.7, "context_precision": 0.6}\n```'
        )
        assert scores["faithfulness"] == 0.8

    def test_parse_evaluation_response_invalid(self):
        """잘못된 응답은 기본값 반환."""
        from app.rag.evaluation import RAGEvaluationPipeline

        pipeline = RAGEvaluationPipeline()

        # Invalid response
        scores = pipeline._parse_evaluation_response("This is not JSON")
        assert scores["faithfulness"] == 0.0
        assert scores["answer_relevancy"] == 0.0
        assert scores["context_precision"] == 0.0

    def test_parse_evaluation_response_clamps_values(self):
        """범위 초과 값은 0-1로 클램핑."""
        from app.rag.evaluation import RAGEvaluationPipeline

        pipeline = RAGEvaluationPipeline()

        # Out of range values
        scores = pipeline._parse_evaluation_response(
            '{"faithfulness": 1.5, "answer_relevancy": -0.5, "context_precision": 0.5}'
        )
        assert scores["faithfulness"] == 1.0  # Clamped to 1.0
        assert scores["answer_relevancy"] == 0.0  # Clamped to 0.0
        assert scores["context_precision"] == 0.5


class TestBatchJobStatus:
    """BatchJobStatus enum 테스트."""

    def test_all_statuses_defined(self):
        """모든 상태 정의."""
        assert BatchJobStatus.PENDING.value == "pending"
        assert BatchJobStatus.RUNNING.value == "running"
        assert BatchJobStatus.COMPLETED.value == "completed"
        assert BatchJobStatus.FAILED.value == "failed"
        assert BatchJobStatus.CANCELLED.value == "cancelled"
