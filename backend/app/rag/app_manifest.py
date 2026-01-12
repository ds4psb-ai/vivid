"""
App-level RAG Manifest 정의.

각 앱(1D-6D, QC, AD, AI, VEO)에 대한 RAG 설정 매니페스트.
- 사용할 차원 RAG 컬렉션
- 검색 파라미터
- 증폭(amplification) 규칙

Usage:
    from app.rag.app_manifest import APP_MANIFESTS, AppRAGManifest

    manifest = APP_MANIFESTS.get("dimension.aesthetic.direct")
    if manifest:
        print(manifest.dimensions)  # ["1D", "AD"]
        print(manifest.search_limit)  # 5
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AppRAGManifest:
    """앱별 RAG 설정 매니페스트.

    Attributes:
        app_key: 고유 앱 식별자 (예: "dimension.aesthetic.direct")
        dimensions: 검색할 차원 목록 (예: ["1D", "AD"])
        search_limit: 각 차원에서 검색할 최대 문서 수
        min_score: 최소 유사도 점수 (0-1)
        amplify_with_history: 이전 단계 이력을 컨텍스트에 포함할지
        prompt_injection_template: RAG 결과를 프롬프트에 주입하는 템플릿
        fallback_enabled: RAG 실패 시 폴백 동작 활성화
        metadata_filters: 추가 메타데이터 필터 조건
    """

    app_key: str
    dimensions: List[str] = field(default_factory=lambda: ["1D"])
    search_limit: int = 5
    min_score: float = 0.5
    amplify_with_history: bool = True
    prompt_injection_template: str = ""
    fallback_enabled: bool = True
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    # P1: Dataset-level routing
    dataset_candidates: List[str] = field(default_factory=list)
    dataset_selection_rules: Dict[str, List[str]] = field(default_factory=dict)
    max_datasets: int = 2
    default_dataset: str = ""  # Fallback dataset when no rules match

    def __post_init__(self):
        """검증 및 기본값 설정."""
        if not self.app_key:
            raise ValueError("app_key is required")

        # 기본 프롬프트 템플릿
        if not self.prompt_injection_template:
            self.prompt_injection_template = """
## Reference Context (Retrieved from Knowledge Base)
{rag_results}

Use the above context to enhance your response quality and consistency.
"""


# 앱별 RAG 매니페스트 정의
APP_MANIFESTS: Dict[str, AppRAGManifest] = {
    # ========================================
    # Original Dimensions (1D-4D)
    # ========================================
    "teaching.prompt.generate": AppRAGManifest(
        app_key="teaching.prompt.generate",
        dimensions=["1D", "VEO"],
        search_limit=5,
        min_score=0.6,
        amplify_with_history=True,
        prompt_injection_template="""
## Veo Prompt Style Guidelines (Retrieved)
{rag_results}

Apply these guidelines to generate a cinematic Veo prompt.
""",
    ),

    "teaching.storyboard.create": AppRAGManifest(
        app_key="teaching.storyboard.create",
        dimensions=["2D", "1D"],
        search_limit=5,
        min_score=0.55,
        amplify_with_history=True,
        prompt_injection_template="""
## Storyboard & Narrative Guidelines (Retrieved)
{rag_results}

Use these narrative frameworks for storyboard structure.
""",
    ),

    "teaching.image.generate": AppRAGManifest(
        app_key="teaching.image.generate",
        dimensions=["3D", "AD"],
        search_limit=5,
        min_score=0.6,
        amplify_with_history=True,
        prompt_injection_template="""
## Visual Style Guidelines (Retrieved)
{rag_results}

Apply these aesthetic principles to the image prompt.
""",
    ),

    "teaching.reference.analyze": AppRAGManifest(
        app_key="teaching.reference.analyze",
        dimensions=["4D", "QC"],
        search_limit=5,
        min_score=0.55,
        amplify_with_history=True,
        prompt_injection_template="""
## Analysis Framework (Retrieved)
{rag_results}

Use this framework for comprehensive reference analysis.
""",
    ),

    # ========================================
    # Extended Dimensions (5D-6D)
    # ========================================
    "dimension.video.generate": AppRAGManifest(
        app_key="dimension.video.generate",
        dimensions=["5D", "VEO", "1D"],
        search_limit=5,
        min_score=0.6,
        amplify_with_history=True,
        prompt_injection_template="""
## Video Generation & Camera Movement Guidelines (Retrieved)
{rag_results}

Apply these cinematic principles to video generation.
""",
    ),

    "dimension.audio.generate": AppRAGManifest(
        app_key="dimension.audio.generate",
        dimensions=["6D"],
        search_limit=5,
        min_score=0.55,
        amplify_with_history=True,
        prompt_injection_template="""
## Sound Design & Music Guidelines (Retrieved)
{rag_results}

Use these audio principles for sound generation.
""",
    ),

    # ========================================
    # Meta Dimensions (QC, AD, AI, VEO)
    # ========================================
    "dimension.quality.check": AppRAGManifest(
        app_key="dimension.quality.check",
        dimensions=["QC", "4D"],
        search_limit=5,
        min_score=0.6,
        amplify_with_history=True,
        prompt_injection_template="""
## Quality Standards & VDG Criteria (Retrieved)
{rag_results}

Apply these quality standards for evaluation.
""",
    ),

    "dimension.aesthetic.direct": AppRAGManifest(
        app_key="dimension.aesthetic.direct",
        dimensions=["AD", "1D", "3D"],
        search_limit=7,  # 더 많은 레퍼런스 필요
        min_score=0.55,
        amplify_with_history=True,
        prompt_injection_template="""
## Auteur Style Guidelines & Aesthetic Theory (Retrieved)
{rag_results}

Channel these masters' visual languages and aesthetic principles.
Include specific shot compositions, color palettes, and mood references.
""",
        metadata_filters={
            "content_type": ["auteur_style", "aesthetic_theory", "visual_guide"],
        },
    ),

    "dimension.persona.analyze": AppRAGManifest(
        app_key="dimension.persona.analyze",
        dimensions=["AI"],
        search_limit=7,  # 더 많은 심리학 레퍼런스
        min_score=0.45,  # 심리학 이론은 넓은 범위 허용
        amplify_with_history=True,  # 이전 대화 맥락 중요
        prompt_injection_template="""
## 심리학적 분석 프레임워크 (Retrieved Knowledge)
{rag_results}

## 적용 지침
- 위의 심리학 이론/프레임워크를 바탕으로 사용자의 답변을 분석하세요.
- 학술 용어는 쉬운 표현으로 바꾸되, 분석의 깊이는 유지하세요.
- 이론의 핵심 개념을 자연스럽게 탐색하는 질문을 생성하세요.
- 사용자가 자신의 무의식/잠재의식을 스스로 발견하도록 유도하세요.
""",
    ),

    "veo.video.generate": AppRAGManifest(
        app_key="veo.video.generate",
        dimensions=["VEO", "5D", "1D"],
        search_limit=7,
        min_score=0.6,
        amplify_with_history=True,
        prompt_injection_template="""
## Veo 3.1 Prompt Templates & Video Style Guidelines (Retrieved)
{rag_results}

Apply these Veo-specific prompt patterns and cinematic techniques.
Include camera movements, transitions, and visual effects guidance.
""",
        metadata_filters={
            "content_type": ["veo_template", "video_style", "camera_movement"],
        },
    ),

    # ========================================
    # Sound & Story Dimensions
    # ========================================
    "dimension.sound.craft": AppRAGManifest(
        app_key="dimension.sound.craft",
        dimensions=["6D", "SOUND"],
        search_limit=5,
        min_score=0.5,
        amplify_with_history=True,
        prompt_injection_template="""
## Sound Design & Music Guidelines (Retrieved)
{rag_results}

Apply these audio principles for sound generation.
""",
    ),

    "dimension.story.architect": AppRAGManifest(
        app_key="dimension.story.architect",
        dimensions=["STORY", "2D"],
        search_limit=5,
        min_score=0.55,
        amplify_with_history=True,
        prompt_injection_template="""
## Story Structure & Narrative Guidelines (Retrieved)
{rag_results}

Use these narrative frameworks for story architecture.
""",
    ),

    # P1: Persona Analyzer with dataset routing
    "dimension.persona.analyze": AppRAGManifest(
        app_key="dimension.persona.analyze",
        dimensions=["AI"],
        search_limit=5,
        min_score=0.5,
        amplify_with_history=True,
        # P1: Dataset routing configuration
        dataset_candidates=["psych_core", "mbti", "attachment", "enneagram"],
        dataset_selection_rules={
            r"mbti|성격|유형|intj|enfp|infp|entj": ["mbti"],
            r"애착|불안|회피|안정|관계|의존": ["attachment"],
            r"에니어그램|1번|2번|3번|4번|5번|6번|7번|8번|9번": ["enneagram"],
        },
        max_datasets=2,
        default_dataset="psych_core",  # Fallback to core psychology
        prompt_injection_template="""
## Psychology & Personality Context (Retrieved)
{rag_results}

Apply these psychological frameworks to enhance persona analysis.
""",
    ),
}


def get_manifest(app_key: str) -> Optional[AppRAGManifest]:
    """앱 키로 매니페스트 조회.

    Args:
        app_key: 앱 식별자

    Returns:
        AppRAGManifest or None if not found
    """
    return APP_MANIFESTS.get(app_key)


def get_dimensions_for_app(app_key: str) -> List[str]:
    """앱에서 사용하는 차원 목록 반환.

    Args:
        app_key: 앱 식별자

    Returns:
        차원 목록 (기본: ["1D"])
    """
    manifest = APP_MANIFESTS.get(app_key)
    return manifest.dimensions if manifest else ["1D"]


def list_apps_by_dimension(dimension: str) -> List[str]:
    """특정 차원을 사용하는 모든 앱 목록 반환.

    Args:
        dimension: 차원 ID (예: "AD", "VEO")

    Returns:
        해당 차원을 사용하는 앱 키 목록
    """
    return [
        app_key for app_key, manifest in APP_MANIFESTS.items()
        if dimension in manifest.dimensions
    ]
