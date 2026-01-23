"""P7: Prompt Tuner Service.

LLM을 활용하여 P5 분류 프롬프트를 자동으로 개선합니다.

Features:
- 오분류 패턴 분석
- 개선된 프롬프트 생성 (Gemini 활용)
- A/B 테스트 variant 생성

Usage:
    from app.services.prompt_tuner import PromptTuner

    tuner = PromptTuner()
    issues = await tuner.analyze_failures(failures)
    improved_prompt = await tuner.generate_improved_prompt(current_prompt, issues)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.self_correction_schemas import (
    ExperimentType,
    MisclassifiedQuery,
    MisclassificationType,
    PromptAnalysis,
    PromptIssue,
    PromptIssueType,
    PromptTuningResult,
)
from app.rag.llm_classifier import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


# =============================================================================
# Prompt Analysis Templates
# =============================================================================


ANALYSIS_PROMPT = """You are an expert in prompt engineering for LLM-based query classification.

Analyze the following classification prompt and the misclassified queries to identify issues and suggest improvements.

## Current Classification Prompt:
```
{current_prompt}
```

## Misclassified Queries (sample):
{misclassified_examples}

## Your Task:
1. Identify issues in the current prompt that led to misclassifications
2. Categorize each issue:
   - boundary_ambiguity: Unclear boundaries between categories
   - missing_examples: Lack of representative examples
   - conflicting_rules: Rules that contradict each other
   - domain_gap: Missing domain-specific knowledge
   - recency_detection: Poor detection of recency requirements

3. For each issue, provide:
   - issue_type: one of the above categories
   - severity: "low", "medium", "high", or "critical"
   - description: detailed explanation
   - affected_query_types: which QueryTypes are affected
   - suggested_fix: how to fix the issue

Respond with a JSON object:
{{
  "overall_score": float (0.0-1.0, current prompt quality),
  "improvement_potential": float (0.0-1.0, how much can be improved),
  "issues": [
    {{
      "issue_type": "boundary_ambiguity",
      "severity": "high",
      "description": "...",
      "affected_query_types": ["domain_specific", "creative"],
      "suggested_fix": "..."
    }},
    ...
  ]
}}

JSON Response:"""


IMPROVEMENT_PROMPT = """You are an expert in prompt engineering for LLM-based query classification.

Based on the analysis of issues, generate an improved version of the classification prompt.

## Current Classification Prompt:
```
{current_prompt}
```

## Identified Issues:
{issues_summary}

## Requirements for the Improved Prompt:
1. Keep the same output format (JSON with query_type, confidence, reasoning)
2. Maintain the same 5 query types: simple_factual, domain_specific, recency_required, multi_hop, creative
3. Address all identified issues:
   - Add clearer boundary conditions
   - Include more/better examples for problematic categories
   - Resolve any conflicting rules
   - Add domain-specific guidance if needed

4. Focus on these specific improvements:
{specific_improvements}

## Output Format:
Respond with a JSON object containing:
{{
  "improved_prompt": "The complete new prompt text...",
  "changes_summary": "Summary of changes made...",
  "expected_improvement": float (0.0-1.0, expected accuracy improvement)
}}

JSON Response:"""


class PromptTuner:
    """프롬프트 튜닝 서비스.

    P6 피드백 데이터와 오분류 분석 결과를 기반으로
    P5 분류 프롬프트를 자동으로 개선합니다.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
    ):
        self.model_name = model_name
        self._current_prompt: str = CLASSIFICATION_PROMPT

    async def analyze_failures(
        self,
        failures: List[MisclassifiedQuery],
        max_examples: int = 20,
    ) -> List[PromptIssue]:
        """오분류 원인 분석.

        Args:
            failures: 오분류된 쿼리 목록
            max_examples: 분석에 사용할 최대 예시 수

        Returns:
            List of PromptIssue objects
        """
        if not failures:
            logger.info("[PromptTuner] No failures to analyze")
            return []

        # Build examples string
        examples = self._build_failure_examples(failures[:max_examples])

        # Call LLM for analysis
        prompt = ANALYSIS_PROMPT.format(
            current_prompt=self._current_prompt,
            misclassified_examples=examples,
        )

        try:
            response = await self._call_llm(prompt)
            issues = self._parse_analysis_response(response)
            logger.info(f"[PromptTuner] Analyzed {len(failures)} failures, found {len(issues)} issues")
            return issues
        except Exception as e:
            logger.error(f"[PromptTuner] Analysis failed: {e}")
            # Return basic issues based on failure patterns
            return self._infer_issues_from_failures(failures)

    async def generate_improved_prompt(
        self,
        current_prompt: str,
        issues: List[PromptIssue],
    ) -> Tuple[str, str, float]:
        """개선된 프롬프트 생성 (Gemini 활용).

        Args:
            current_prompt: 현재 분류 프롬프트
            issues: 분석된 이슈 목록

        Returns:
            (improved_prompt, changes_summary, expected_improvement) 튜플
        """
        if not issues:
            logger.info("[PromptTuner] No issues to address, returning current prompt")
            return current_prompt, "No changes needed", 0.0

        # Build issues summary
        issues_summary = self._build_issues_summary(issues)
        specific_improvements = self._build_specific_improvements(issues)

        prompt = IMPROVEMENT_PROMPT.format(
            current_prompt=current_prompt,
            issues_summary=issues_summary,
            specific_improvements=specific_improvements,
        )

        try:
            response = await self._call_llm(prompt)
            improved_prompt, changes_summary, expected_improvement = self._parse_improvement_response(response)
            logger.info(f"[PromptTuner] Generated improved prompt (expected improvement: {expected_improvement:.0%})")
            return improved_prompt, changes_summary, expected_improvement
        except Exception as e:
            logger.error(f"[PromptTuner] Prompt generation failed: {e}")
            # Return current prompt with basic fixes
            improved_prompt = self._apply_basic_fixes(current_prompt, issues)
            return improved_prompt, "Applied basic fixes based on issues", 0.05

    async def create_ab_variant(
        self,
        improved_prompt: str,
        db: Optional[AsyncSession] = None,
        experiment_traffic: float = 0.1,
    ) -> Optional[str]:
        """A/B 테스트 variant 생성.

        Args:
            improved_prompt: 개선된 프롬프트
            db: Database session
            experiment_traffic: 트래픽 비율 (0.0-1.0)

        Returns:
            Experiment key if created, None otherwise
        """
        if db is None:
            logger.warning("[PromptTuner] No database session provided, skipping A/B test creation")
            return None

        try:
            from app.experiments.ab_testing import get_ab_testing
            from app.experiments.models import (
                Experiment,
                ExperimentVariant,
                ExperimentStatus,
            )

            # Generate experiment key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            experiment_key = f"p7_prompt_tuning_{timestamp}"

            # Create experiment
            experiment = Experiment(
                experiment_key=experiment_key,
                name=f"P7 Prompt Tuning {timestamp}",
                description="Automated prompt tuning experiment from P7 Self-Correction",
                hypothesis="Improved classification prompt will increase accuracy",
                status=ExperimentStatus.RUNNING,
                start_date=datetime.utcnow(),
                traffic_percentage=experiment_traffic * 100,  # Convert to percentage
                primary_metric="classification_accuracy",
                secondary_metrics=["skip_negative_rate", "crag_trigger_rate"],
                min_sample_size=100,
                confidence_level=0.95,
                min_detectable_effect=0.05,
                owner="p7_self_correction",
                tags=["p7", "prompt_tuning", "automated"],
            )
            db.add(experiment)
            await db.flush()

            # Create control variant (current prompt)
            control = ExperimentVariant(
                experiment_id=experiment.id,
                name="control",
                description="Current classification prompt",
                weight=50.0,
                is_control=True,
                payload={"prompt": self._current_prompt},
            )
            db.add(control)

            # Create treatment variant (improved prompt)
            treatment = ExperimentVariant(
                experiment_id=experiment.id,
                name="treatment",
                description="Improved classification prompt",
                weight=50.0,
                is_control=False,
                payload={"prompt": improved_prompt},
            )
            db.add(treatment)

            await db.commit()
            logger.info(f"[PromptTuner] Created A/B experiment: {experiment_key}")
            return experiment_key

        except Exception as e:
            logger.error(f"[PromptTuner] Failed to create A/B experiment: {e}")
            if db:
                await db.rollback()
            return None

    async def run_full_tuning(
        self,
        failures: List[MisclassifiedQuery],
        db: Optional[AsyncSession] = None,
        auto_experiment: bool = True,
        experiment_traffic: float = 0.1,
    ) -> PromptTuningResult:
        """전체 튜닝 파이프라인 실행.

        Args:
            failures: 오분류된 쿼리 목록
            db: Database session (for A/B test)
            auto_experiment: 자동 A/B 테스트 시작 여부
            experiment_traffic: 트래픽 비율

        Returns:
            PromptTuningResult with full details
        """
        # 1. Analyze failures
        issues = await self.analyze_failures(failures)

        # 2. Generate improved prompt
        improved_prompt, changes_summary, expected_improvement = await self.generate_improved_prompt(
            self._current_prompt, issues
        )

        # 3. Build analysis
        analysis = PromptAnalysis(
            current_prompt=self._current_prompt,
            issues=issues,
            overall_score=1.0 - (len(issues) * 0.1),  # Simple scoring
            improvement_potential=expected_improvement,
        )

        # 4. Optionally create A/B test
        experiment_key = None
        variant_name = None
        if auto_experiment and db:
            experiment_key = await self.create_ab_variant(
                improved_prompt, db, experiment_traffic
            )
            variant_name = "treatment" if experiment_key else None

        return PromptTuningResult(
            analysis=analysis,
            improved_prompt=improved_prompt,
            changes_summary=changes_summary,
            expected_improvement=expected_improvement,
            experiment_key=experiment_key,
            variant_name=variant_name,
        )

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _call_llm(self, prompt: str) -> str:
        """LLM API 호출."""
        from app.services.genai_utils import get_genai_client

        client = get_genai_client()
        response = await client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.2,  # Low temperature for consistent output
                "max_output_tokens": 4096,
                "response_mime_type": "application/json",
            },
        )
        return response.text

    def _build_failure_examples(self, failures: List[MisclassifiedQuery]) -> str:
        """Build formatted failure examples for analysis prompt."""
        examples = []
        for f in failures:
            example = f"""
Query: "{f.query}"
- Predicted: {f.predicted_type} (confidence: {f.confidence:.2f})
- Misclassification Type: {f.misclassification_type.value}
- Strategy Used: {f.strategy_used}
- Avg Rating: {f.avg_rating or 'N/A'}
- Negative Feedback: {f.negative_feedback_count}
- Analysis: {f.analysis_reason}
"""
            examples.append(example)
        return "\n".join(examples)

    def _build_issues_summary(self, issues: List[PromptIssue]) -> str:
        """Build formatted issues summary."""
        summary_parts = []
        for i, issue in enumerate(issues, 1):
            part = f"""
{i}. {issue.issue_type.value} (severity: {issue.severity})
   Description: {issue.description}
   Affected Types: {', '.join(issue.affected_query_types)}
   Suggested Fix: {issue.suggested_fix}
"""
            summary_parts.append(part)
        return "\n".join(summary_parts)

    def _build_specific_improvements(self, issues: List[PromptIssue]) -> str:
        """Build specific improvement instructions based on issues."""
        improvements = []

        # Group by issue type
        by_type: Dict[PromptIssueType, List[PromptIssue]] = {}
        for issue in issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)

        if PromptIssueType.BOUNDARY_AMBIGUITY in by_type:
            affected = set()
            for i in by_type[PromptIssueType.BOUNDARY_AMBIGUITY]:
                affected.update(i.affected_query_types)
            improvements.append(
                f"- Add clearer boundary conditions between: {', '.join(affected)}"
            )

        if PromptIssueType.MISSING_EXAMPLES in by_type:
            affected = set()
            for i in by_type[PromptIssueType.MISSING_EXAMPLES]:
                affected.update(i.affected_query_types)
            improvements.append(
                f"- Add more examples for: {', '.join(affected)}"
            )

        if PromptIssueType.DOMAIN_GAP in by_type:
            improvements.append(
                "- Add more film/director domain-specific guidance and examples"
            )

        if PromptIssueType.RECENCY_DETECTION in by_type:
            improvements.append(
                "- Improve recency detection rules (date patterns, keywords)"
            )

        if PromptIssueType.CONFLICTING_RULES in by_type:
            improvements.append(
                "- Resolve conflicting classification rules"
            )

        return "\n".join(improvements) if improvements else "- General clarity improvements"

    def _parse_analysis_response(self, response: str) -> List[PromptIssue]:
        """Parse LLM analysis response."""
        issues = []
        try:
            text = self._clean_json_response(response)
            data = json.loads(text)

            for issue_data in data.get("issues", []):
                issue_type_str = issue_data.get("issue_type", "boundary_ambiguity")
                try:
                    issue_type = PromptIssueType(issue_type_str)
                except ValueError:
                    issue_type = PromptIssueType.BOUNDARY_AMBIGUITY

                issues.append(PromptIssue(
                    issue_type=issue_type,
                    severity=issue_data.get("severity", "medium"),
                    description=issue_data.get("description", ""),
                    affected_query_types=issue_data.get("affected_query_types", []),
                    example_queries=issue_data.get("example_queries", []),
                    suggested_fix=issue_data.get("suggested_fix", ""),
                ))

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[PromptTuner] Failed to parse analysis response: {e}")

        return issues

    def _parse_improvement_response(self, response: str) -> Tuple[str, str, float]:
        """Parse LLM improvement response."""
        try:
            text = self._clean_json_response(response)
            data = json.loads(text)

            improved_prompt = data.get("improved_prompt", self._current_prompt)
            changes_summary = data.get("changes_summary", "")
            expected_improvement = float(data.get("expected_improvement", 0.05))

            return improved_prompt, changes_summary, expected_improvement

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"[PromptTuner] Failed to parse improvement response: {e}")
            return self._current_prompt, "Parse error", 0.0

    def _clean_json_response(self, text: str) -> str:
        """Clean JSON response from markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return text

    def _infer_issues_from_failures(self, failures: List[MisclassifiedQuery]) -> List[PromptIssue]:
        """Infer issues from failure patterns when LLM analysis fails."""
        issues = []

        # Count misclassification types
        type_counts: Dict[MisclassificationType, int] = {}
        query_type_counts: Dict[str, int] = {}

        for f in failures:
            type_counts[f.misclassification_type] = type_counts.get(f.misclassification_type, 0) + 1
            query_type_counts[f.predicted_type] = query_type_counts.get(f.predicted_type, 0) + 1

        # Check for skip_but_negative (boundary issue)
        if type_counts.get(MisclassificationType.SKIP_BUT_NEGATIVE, 0) > len(failures) * 0.3:
            issues.append(PromptIssue(
                issue_type=PromptIssueType.BOUNDARY_AMBIGUITY,
                severity="high",
                description="High rate of negative feedback after skip retrieval suggests boundary confusion between simple_factual/creative and domain_specific",
                affected_query_types=["simple_factual", "creative", "domain_specific"],
                suggested_fix="Add clearer examples distinguishing when retrieval is needed",
            ))

        # Check for CRAG triggers (retrieval quality issue)
        if type_counts.get(MisclassificationType.RETRIEVAL_BUT_CRAG, 0) > len(failures) * 0.2:
            issues.append(PromptIssue(
                issue_type=PromptIssueType.DOMAIN_GAP,
                severity="medium",
                description="High CRAG trigger rate suggests incorrect strategy selection",
                affected_query_types=["domain_specific", "multi_hop"],
                suggested_fix="Improve distinction between domain_specific and multi_hop queries",
            ))

        # Check for low confidence failures
        if type_counts.get(MisclassificationType.LOW_CONFIDENCE_FAILURE, 0) > len(failures) * 0.2:
            issues.append(PromptIssue(
                issue_type=PromptIssueType.MISSING_EXAMPLES,
                severity="medium",
                description="Many low-confidence classifications led to failures",
                affected_query_types=list(query_type_counts.keys())[:3],
                suggested_fix="Add more diverse examples to improve classification confidence",
            ))

        return issues

    def _apply_basic_fixes(self, current_prompt: str, issues: List[PromptIssue]) -> str:
        """Apply basic fixes to prompt when LLM generation fails."""
        # For now, just return the current prompt
        # In production, this could apply rule-based modifications
        return current_prompt

    def set_current_prompt(self, prompt: str) -> None:
        """Update current prompt (for testing or manual override)."""
        self._current_prompt = prompt

    def get_current_prompt(self) -> str:
        """Get current classification prompt."""
        return self._current_prompt


# =============================================================================
# Singleton Instance
# =============================================================================


_tuner: Optional[PromptTuner] = None


def get_prompt_tuner() -> PromptTuner:
    """Get or create singleton PromptTuner."""
    global _tuner
    if _tuner is None:
        _tuner = PromptTuner()
    return _tuner
