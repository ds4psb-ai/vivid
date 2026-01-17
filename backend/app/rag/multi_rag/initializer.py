"""Multi-RAG System Initializer (P0 2026).

시스템 시작 시 기본 RAG 소스 등록.

Features:
    - 기본 거장 DNA 소스 등록 (NotebookLM)
    - 차원별 지식 소스 등록 (Qdrant)
    - 사용자 히스토리 소스 등록

Usage:
    from app.rag.multi_rag.initializer import initialize_multi_rag

    # 서버 시작 시 호출
    await initialize_multi_rag()

    # 또는 동기 초기화 (lifespan에서)
    initialize_multi_rag_sync()
"""
from __future__ import annotations

import logging
from typing import List

from app.rag.multi_rag.registry import get_registry, RAGSourceRegistry
from app.rag.multi_rag.types import RAGSourceSpec, RAGSourceType

logger = logging.getLogger(__name__)


# =============================================================================
# Default Source Specifications
# =============================================================================

# 거장 DNA 소스 (NotebookLM)
AUTEUR_DNA_SOURCES: List[RAGSourceSpec] = [
    RAGSourceSpec(
        source_id="notebooklm_bong",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="봉준호 DNA",
        description="봉준호 감독의 연출 철학, 계단 상징, 계급 표현",
        keywords=["봉준호", "bong", "기생충", "살인의추억", "옥자", "계단", "계급"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_봉준호"},
        auteur_keys=["bong", "봉준호"],
    ),
    RAGSourceSpec(
        source_id="notebooklm_wong",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="왕가위 DNA",
        description="왕가위 감독의 감성적 영상미, 시간과 기억",
        keywords=["왕가위", "wong", "화양연화", "중경삼림", "아비정전"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_왕가위"},
        auteur_keys=["wong", "왕가위"],
    ),
    RAGSourceSpec(
        source_id="notebooklm_nolan",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="크리스토퍼 놀란 DNA",
        description="놀란 감독의 시간 조작, 논리적 서사, IMAX 촬영",
        keywords=["놀란", "nolan", "인셉션", "인터스텔라", "다크나이트", "테넷", "시간"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_크리스토퍼놀란"},
        auteur_keys=["nolan", "놀란", "크리스토퍼놀란"],
    ),
    RAGSourceSpec(
        source_id="notebooklm_villeneuve",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="드니 빌뇌브 DNA",
        description="빌뇌브 감독의 스케일, SF 철학, 시각적 웅장함",
        keywords=["빌뇌브", "villeneuve", "듄", "도착", "블레이드러너", "시카리오"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_드니빌뇌브"},
        auteur_keys=["villeneuve", "빌뇌브", "드니빌뇌브"],
    ),
    RAGSourceSpec(
        source_id="notebooklm_tarantino",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="쿠엔틴 타란티노 DNA",
        description="타란티노 감독의 대화, 비선형 서사, 폭력의 미학",
        keywords=["타란티노", "tarantino", "펄프픽션", "킬빌", "장고"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_쿠엔틴타란티노"},
        auteur_keys=["tarantino", "타란티노"],
    ),
    RAGSourceSpec(
        source_id="notebooklm_park",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="박찬욱 DNA",
        description="박찬욱 감독의 복수 서사, 미장센, 색채 미학",
        keywords=["박찬욱", "park", "올드보이", "친절한금자씨", "아가씨"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_박찬욱"},
        auteur_keys=["park", "박찬욱"],
    ),
    RAGSourceSpec(
        source_id="notebooklm_shinkai",
        source_type=RAGSourceType.AUTEUR_DNA,
        display_name="신카이 마코토 DNA",
        description="신카이 감독의 빛과 하늘, 청춘 로맨스, 애니메이션",
        keywords=["신카이", "shinkai", "너의이름은", "날씨의아이", "초속5센티미터"],
        priority=10,
        latency_ms_avg=3000,
        backend_type="notebooklm",
        connection_config={"notebook_id": "DNA_신카이"},
        auteur_keys=["shinkai", "신카이"],
    ),
]

# 차원별 지식 소스 (Qdrant)
DIMENSION_SOURCES: List[RAGSourceSpec] = [
    RAGSourceSpec(
        source_id="qdrant_1d",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="1D 프롬프트 지식",
        description="텍스트 프롬프트 작성 가이드, 스타일 키워드",
        keywords=["프롬프트", "prompt", "텍스트", "키워드", "스타일"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "1D"},
        dimensions=["1D"],
    ),
    RAGSourceSpec(
        source_id="qdrant_2d",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="2D 스토리보드 지식",
        description="스토리보드 제작, 컷 구성, 장면 전환",
        keywords=["스토리보드", "storyboard", "컷", "shot", "장면"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "2D"},
        dimensions=["2D"],
    ),
    RAGSourceSpec(
        source_id="qdrant_3d",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="3D 이미지 지식",
        description="이미지 생성, 시각적 스타일, 구도",
        keywords=["이미지", "image", "비주얼", "visual", "구도"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "3D"},
        dimensions=["3D"],
    ),
    RAGSourceSpec(
        source_id="qdrant_4d",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="4D 분석 지식",
        description="레퍼런스 분석, 구도, 조명, 색감, 연출 기법",
        keywords=["분석", "analysis", "레퍼런스", "reference", "구도", "조명"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "4D"},
        dimensions=["4D"],
    ),
    RAGSourceSpec(
        source_id="qdrant_ad",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="AD 미학 지식",
        description="미학 디렉팅, 스타일 가이드, 시각적 일관성",
        keywords=["미학", "aesthetic", "스타일", "style", "디렉팅"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "AD"},
        dimensions=["AD"],
    ),
    RAGSourceSpec(
        source_id="qdrant_story",
        source_type=RAGSourceType.DIMENSION_KNOWLEDGE,
        display_name="스토리 지식",
        description="시나리오 작성, 서사 구조, 캐릭터 개발",
        keywords=["스토리", "story", "시나리오", "서사", "캐릭터"],
        priority=8,
        latency_ms_avg=500,
        backend_type="qdrant",
        connection_config={"dimension": "STORY"},
        dimensions=["STORY"],
    ),
]

# 사용자 히스토리 소스
USER_HISTORY_SOURCE = RAGSourceSpec(
    source_id="user_history",
    source_type=RAGSourceType.USER_HISTORY,
    display_name="사용자 작업 히스토리",
    description="사용자의 과거 작업 결과 및 컨텍스트",
    keywords=["이전", "previous", "과거", "history", "비슷한", "similar"],
    priority=6,
    latency_ms_avg=200,
    backend_type="postgres",
    connection_config={},
)


# =============================================================================
# Initialization Functions
# =============================================================================

def initialize_multi_rag_sync() -> None:
    """Multi-RAG 시스템 동기 초기화.

    서버 시작 시 lifespan에서 호출합니다.
    기본 RAG 소스들을 레지스트리에 등록합니다.

    Note:
        이 함수는 동기 함수로, 백엔드 인스턴스를 lazy하게 생성합니다.
        실제 연결은 첫 쿼리 시점에 이루어집니다.
    """
    registry = get_registry()

    logger.info("[MultiRAG] Initializing Multi-RAG system...")

    # 1. 거장 DNA 소스 등록
    from app.rag.multi_rag.backends import NotebookLMAdapter

    for spec in AUTEUR_DNA_SOURCES:
        try:
            notebook_id = spec.connection_config.get("notebook_id", "")
            adapter = NotebookLMAdapter(notebook_id=notebook_id)
            registry.register_sync(spec, adapter)
        except Exception as e:
            logger.warning(f"[MultiRAG] Failed to register {spec.source_id}: {e}")

    # 2. 차원별 지식 소스 등록
    from app.rag.multi_rag.backends import QdrantAdapter

    for spec in DIMENSION_SOURCES:
        try:
            dimension = spec.connection_config.get("dimension", "1D")
            adapter = QdrantAdapter(dimension=dimension)
            registry.register_sync(spec, adapter)
        except Exception as e:
            logger.warning(f"[MultiRAG] Failed to register {spec.source_id}: {e}")

    # 3. 사용자 히스토리 소스 등록
    from app.database import get_db_context
    from app.rag.multi_rag.backends import UserHistoryAdapter

    try:
        adapter = UserHistoryAdapter(db_factory=get_db_context)
        registry.register_sync(USER_HISTORY_SOURCE, adapter)
    except Exception as e:
        logger.warning(f"[MultiRAG] Failed to register user_history: {e}")

    # 통계 로깅
    stats = registry.stats()
    logger.info(
        f"[MultiRAG] Initialization completed | "
        f"total={stats['total']} | "
        f"auteur_dna={stats.get('type_auteur_dna', 0)} | "
        f"dimension={stats.get('type_dimension', 0)} | "
        f"user_history={stats.get('type_user_history', 0)}"
    )


async def initialize_multi_rag() -> None:
    """Multi-RAG 시스템 비동기 초기화.

    동기 초기화 후 헬스 체크를 수행합니다.
    """
    # 동기 초기화
    initialize_multi_rag_sync()

    # 헬스 체크 (선택적)
    registry = get_registry()
    try:
        health = await registry.check_all_health()
        healthy_count = sum(1 for v in health.values() if v)
        logger.info(
            f"[MultiRAG] Health check completed: "
            f"{healthy_count}/{len(health)} sources healthy"
        )
    except Exception as e:
        logger.warning(f"[MultiRAG] Health check failed: {e}")


def get_default_sources() -> List[RAGSourceSpec]:
    """기본 소스 스펙 목록 반환 (테스트용).

    Returns:
        모든 기본 RAGSourceSpec 리스트
    """
    return [
        *AUTEUR_DNA_SOURCES,
        *DIMENSION_SOURCES,
        USER_HISTORY_SOURCE,
    ]
