"""Dual Capsule Registry

8개의 실제 API 캡슐 정의:
- NotebookLM RAG (4개): 지식 기반 분석
- Teaching Capsule (4개): 콘텐츠 생성

이 레지스트리는 프론트엔드 노드 팔레트 및 파이프라인 실행에서 사용됩니다.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class CapsuleCategory(str, Enum):
    """캡슐 카테고리"""
    NOTEBOOKLM = "notebooklm"
    TEACHING = "teaching"


class PortType(str, Enum):
    """포트 데이터 타입"""
    TEXT = "text"
    JSON = "json"
    NOTEBOOK_ID = "notebook_id"
    SOURCE_IDS = "source_ids"
    AUDIO_URL = "audio_url"
    SCENES = "scenes"
    IMAGE_PARAMS = "image_params"


@dataclass
class PortSpec:
    """노드 입/출력 포트 스펙"""
    id: str
    type: PortType
    label: str
    required: bool = True
    description: Optional[str] = None


@dataclass
class CapsuleSpec:
    """캡슐 노드 스펙"""
    id: str
    display_name: str
    category: CapsuleCategory
    icon: str
    description: str
    endpoint: str
    credit_cost: int
    input_ports: List[PortSpec]
    output_ports: List[PortSpec]


# =============================================================================
# NotebookLM RAG Capsules (4개)
# =============================================================================

NLM_NOTEBOOK_CREATE = CapsuleSpec(
    id="nlm.notebook.create",
    display_name="📓 노트북 생성",
    category=CapsuleCategory.NOTEBOOKLM,
    icon="notebook",
    description="NotebookLM Enterprise에서 새 노트북을 생성합니다",
    endpoint="/api/v1/agent/tool/create_notebook",
    credit_cost=1,
    input_ports=[
        PortSpec(id="title", type=PortType.TEXT, label="제목", description="노트북 제목"),
    ],
    output_ports=[
        PortSpec(id="notebook_id", type=PortType.NOTEBOOK_ID, label="노트북 ID"),
    ],
)

NLM_SOURCES_ADD = CapsuleSpec(
    id="nlm.sources.add",
    display_name="📎 소스 추가",
    category=CapsuleCategory.NOTEBOOKLM,
    icon="paperclip",
    description="노트북에 텍스트, URL, Drive 문서를 추가합니다",
    endpoint="/api/v1/agent/tool/add_sources",
    credit_cost=2,
    input_ports=[
        PortSpec(id="notebook_id", type=PortType.NOTEBOOK_ID, label="노트북 ID"),
        PortSpec(id="sources", type=PortType.JSON, label="소스 배열"),
    ],
    output_ports=[
        PortSpec(id="source_ids", type=PortType.SOURCE_IDS, label="소스 ID 목록"),
        PortSpec(id="source_content", type=PortType.TEXT, label="소스 내용 요약", required=False),
    ],
)

NLM_AUDIO_GENERATE = CapsuleSpec(
    id="nlm.audio.generate",
    display_name="🎙️ 오디오 오버뷰",
    category=CapsuleCategory.NOTEBOOKLM,
    icon="microphone",
    description="AI 오디오 오버뷰(팟캐스트 스타일)를 생성합니다",
    endpoint="/api/v1/agent/tool/generate_audio_overview",
    credit_cost=5,
    input_ports=[
        PortSpec(id="notebook_id", type=PortType.NOTEBOOK_ID, label="노트북 ID"),
        PortSpec(id="focus", type=PortType.TEXT, label="강조 주제", required=False),
    ],
    output_ports=[
        PortSpec(id="audio_url", type=PortType.AUDIO_URL, label="오디오 URL"),
        PortSpec(id="status", type=PortType.TEXT, label="상태"),
    ],
)

NLM_NOTEBOOKS_LIST = CapsuleSpec(
    id="nlm.notebooks.list",
    display_name="📋 노트북 목록",
    category=CapsuleCategory.NOTEBOOKLM,
    icon="list",
    description="최근 노트북 목록을 조회합니다",
    endpoint="/api/v1/agent/tool/list_notebooks",
    credit_cost=0,
    input_ports=[
        PortSpec(id="page_size", type=PortType.TEXT, label="페이지 크기", required=False),
    ],
    output_ports=[
        PortSpec(id="notebooks", type=PortType.JSON, label="노트북 목록"),
    ],
)


# =============================================================================
# Teaching Capsules (4개)
# =============================================================================

TEACHING_PROMPT_GENERATE = CapsuleSpec(
    id="teaching.prompt.generate",
    display_name="✨ Veo 프롬프트",
    category=CapsuleCategory.TEACHING,
    icon="wand",
    description="영상 주제/스타일로 Veo 비디오 생성 프롬프트를 만듭니다",
    endpoint="/api/v1/teaching/prompt/generate",
    credit_cost=2,
    input_ports=[
        PortSpec(id="topic", type=PortType.TEXT, label="주제"),
        PortSpec(id="style", type=PortType.TEXT, label="스타일", required=False),
        PortSpec(id="mood", type=PortType.TEXT, label="분위기", required=False),
        PortSpec(id="duration", type=PortType.TEXT, label="길이", required=False),
    ],
    output_ports=[
        PortSpec(id="prompt", type=PortType.TEXT, label="프롬프트"),
        PortSpec(id="negative_prompt", type=PortType.TEXT, label="네거티브 프롬프트"),
        PortSpec(id="technical", type=PortType.JSON, label="기술 설정"),
    ],
)

TEACHING_STORYBOARD_CREATE = CapsuleSpec(
    id="teaching.storyboard.create",
    display_name="🎬 스토리보드",
    category=CapsuleCategory.TEACHING,
    icon="film",
    description="스토리 컨셉으로 씬 단위 스토리보드를 생성합니다",
    endpoint="/api/v1/teaching/storyboard/create",
    credit_cost=3,
    input_ports=[
        PortSpec(id="concept", type=PortType.TEXT, label="컨셉"),
        PortSpec(id="scene_count", type=PortType.TEXT, label="씬 개수", required=False),
    ],
    output_ports=[
        PortSpec(id="scenes", type=PortType.SCENES, label="씬 목록"),
    ],
)

TEACHING_IMAGE_GENERATE = CapsuleSpec(
    id="teaching.image.generate",
    display_name="🖼️ 이미지 프롬프트",
    category=CapsuleCategory.TEACHING,
    icon="image",
    description="이미지 설명으로 AI 이미지 생성 프롬프트를 만듭니다",
    endpoint="/api/v1/teaching/image/generate",
    credit_cost=2,
    input_ports=[
        PortSpec(id="description", type=PortType.TEXT, label="설명"),
        PortSpec(id="style", type=PortType.TEXT, label="스타일", required=False),
        PortSpec(id="aspect_ratio", type=PortType.TEXT, label="종횡비", required=False),
    ],
    output_ports=[
        PortSpec(id="prompt", type=PortType.TEXT, label="프롬프트"),
        PortSpec(id="parameters", type=PortType.IMAGE_PARAMS, label="파라미터"),
    ],
)

TEACHING_REFERENCE_ANALYZE = CapsuleSpec(
    id="teaching.reference.analyze",
    display_name="🔍 레퍼런스 분석",
    category=CapsuleCategory.TEACHING,
    icon="search",
    description="영상 레퍼런스의 시네마틱 요소를 분석합니다",
    endpoint="/api/v1/teaching/reference/analyze",
    credit_cost=3,
    input_ports=[
        PortSpec(id="video_description", type=PortType.TEXT, label="영상 설명"),
        PortSpec(id="focus_areas", type=PortType.JSON, label="분석 초점", required=False),
    ],
    output_ports=[
        PortSpec(id="analysis", type=PortType.JSON, label="분석 결과"),
        PortSpec(id="recommendations", type=PortType.JSON, label="추천사항"),
        PortSpec(id="insights", type=PortType.TEXT, label="인사이트 요약"),
    ],
)


# =============================================================================
# Registry
# =============================================================================

ALL_CAPSULES: List[CapsuleSpec] = [
    # NotebookLM RAG
    NLM_NOTEBOOK_CREATE,
    NLM_SOURCES_ADD,
    NLM_AUDIO_GENERATE,
    NLM_NOTEBOOKS_LIST,
    # Teaching
    TEACHING_PROMPT_GENERATE,
    TEACHING_STORYBOARD_CREATE,
    TEACHING_IMAGE_GENERATE,
    TEACHING_REFERENCE_ANALYZE,
]

CAPSULE_BY_ID: Dict[str, CapsuleSpec] = {c.id: c for c in ALL_CAPSULES}

CAPSULES_BY_CATEGORY: Dict[CapsuleCategory, List[CapsuleSpec]] = {
    CapsuleCategory.NOTEBOOKLM: [c for c in ALL_CAPSULES if c.category == CapsuleCategory.NOTEBOOKLM],
    CapsuleCategory.TEACHING: [c for c in ALL_CAPSULES if c.category == CapsuleCategory.TEACHING],
}


def get_capsule(capsule_id: str) -> Optional[CapsuleSpec]:
    """캡슐 ID로 스펙 조회"""
    return CAPSULE_BY_ID.get(capsule_id)


def get_capsule_endpoint(capsule_id: str) -> Optional[str]:
    """캡슐 ID로 API 엔드포인트 조회"""
    capsule = get_capsule(capsule_id)
    return capsule.endpoint if capsule else None


def list_capsules(category: Optional[CapsuleCategory] = None) -> List[CapsuleSpec]:
    """캡슐 목록 조회 (카테고리 필터 옵션)"""
    if category:
        return CAPSULES_BY_CATEGORY.get(category, [])
    return ALL_CAPSULES


def to_frontend_schema() -> Dict[str, Any]:
    """프론트엔드용 캡슐 스키마 변환"""
    return {
        "capsules": [
            {
                "id": c.id,
                "display_name": c.display_name,
                "category": c.category.value,
                "icon": c.icon,
                "description": c.description,
                "credit_cost": c.credit_cost,
                "input_ports": [
                    {"id": p.id, "type": p.type.value, "label": p.label, "required": p.required}
                    for p in c.input_ports
                ],
                "output_ports": [
                    {"id": p.id, "type": p.type.value, "label": p.label, "required": p.required}
                    for p in c.output_ports
                ],
            }
            for c in ALL_CAPSULES
        ],
        "categories": [cat.value for cat in CapsuleCategory],
    }
