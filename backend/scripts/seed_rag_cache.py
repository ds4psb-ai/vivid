#!/usr/bin/env python
"""RAG Semantic Cache 사전 시딩 스크립트.

거장 DNA 및 자주 묻는 질문을 미리 캐싱하여 API 호출을 90%+ 절감.

Usage:
    cd backend
    source venv/bin/activate
    
    # 전체 시딩 (최초 실행)
    python scripts/seed_rag_cache.py --full
    
    # 특정 거장만 시딩
    python scripts/seed_rag_cache.py --auteur bong
    
    # 캐시 상태 확인
    python scripts/seed_rag_cache.py --stats
    
    # 캐시 갱신 (만료된 항목만)
    python scripts/seed_rag_cache.py --refresh
    
    # 검증
    python scripts/seed_rag_cache.py --verify

Cron 설정 (주 1회):
    0 3 * * 0 cd /app/backend && python scripts/seed_rag_cache.py --refresh
"""
import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

AUTEUR_KEYS = ["bong", "epoch", "abyss", "wong", "voltage", "park", "azure"]

AUTEUR_NAMES = {
    "bong": "강주노",
    "epoch": "크리스토퍼 테오 에포크",
    "abyss": "드니 빌뇌브",
    "wong": "왕가위",
    "voltage": "쿠엔틴 타란티노",
    "park": "박찬욱",
    "azure": "소라 아주르 마코토",
}

# Question templates for auteur DNA
AUTEUR_QUESTION_TEMPLATES = {
    "visual_style": "{name}의 시각적 특징과 영상 스타일은 무엇인가요?",
    "camera_work": "{name}의 카메라 워크와 촬영 기법 특징을 설명해주세요.",
    "color_palette": "{name}의 색채 팔레트와 색감 사용 특징은?",
    "editing_rhythm": "{name}의 편집 스타일과 리듬감을 분석해주세요.",
    "motifs": "{name} 영화에 자주 등장하는 모티프와 상징은?",
    "signature_scene": "{name}의 대표적인 장면 연출 기법은?",
    "sound_design": "{name} 영화의 사운드 디자인 특징은?",
    "narrative_structure": "{name}의 서사 구조와 스토리텔링 방식은?",
    "character_dynamics": "{name} 영화의 캐릭터 관계와 역학은?",
    "thematic_elements": "{name} 감독의 주요 주제와 철학은?",
}

# Dimension-specific questions
DIMENSION_QUESTIONS = {
    "1D": [
        "효과적인 영상 프롬프트 작성법을 알려주세요.",
        "시네마틱한 프롬프트의 핵심 요소는?",
        "AI 영상 생성을 위한 프롬프트 팁은?",
    ],
    "2D": [
        "스토리보드 작성 가이드를 알려주세요.",
        "효과적인 씬 구성 방법은?",
        "시각적 연출을 위한 스토리보드 팁은?",
    ],
    "AD": [
        "미학적 감독의 역할은 무엇인가요?",
        "시각적 일관성을 유지하는 방법은?",
        "색 보정과 그레이딩 원칙은?",
    ],
    "QC": [
        "영상 품질 검수 기준은?",
        "시네마틱 품질의 핵심 지표는?",
    ],
}

# Comparison questions (for variety)
COMPARISON_QUESTIONS = [
    "강주노와 테오 에포크의 연출 스타일 비교",
    "왕가위와 박찬욱의 색감 사용 비교",
    "빌뇌브와 테오 에포크의 SF 영화 스타일 비교",
    "타란티노와 박찬욱의 폭력 묘사 비교",
    "소라 아주르와 강주노의 공간 활용 비교",
]


# =============================================================================
# Seeding Functions
# =============================================================================

async def seed_auteur_questions(auteur_key: str, dry_run: bool = False) -> Dict[str, int]:
    """거장별 질문 시딩.
    
    Returns:
        {"seeded": N, "skipped": N, "failed": N}
    """
    from app.rag.hybrid_rag import hybrid_query
    from app.rag.semantic_cache import get_semantic_cache
    
    auteur_name = AUTEUR_NAMES.get(auteur_key, auteur_key)
    cache = get_semantic_cache()
    
    stats = {"seeded": 0, "skipped": 0, "failed": 0}
    
    logger.info(f"\n🎬 Seeding: {auteur_name} ({auteur_key})")
    
    for template_key, template in AUTEUR_QUESTION_TEMPLATES.items():
        query = template.format(name=auteur_name)
        
        # Check if already cached
        cached = await cache.get(query, auteur_key=auteur_key)
        if cached:
            logger.info(f"  [SKIP] {template_key}: already cached")
            stats["skipped"] += 1
            continue
        
        if dry_run:
            logger.info(f"  [DRY] Would seed: {template_key}")
            stats["seeded"] += 1
            continue
        
        try:
            # Execute hybrid query (NotebookLM + Vertex AI)
            result = await hybrid_query(
                query=query,
                auteur_key=auteur_key,
                use_google_search=False,  # Pure DNA only
            )
            
            # Cache if confidence is sufficient
            if result.confidence >= 0.5:
                await cache.set(
                    query=query,
                    response=result,
                    auteur_key=auteur_key,
                )
                logger.info(
                    f"  [SEED] {template_key}: "
                    f"confidence={result.confidence:.2f}, "
                    f"strategy={result.strategy_used}"
                )
                stats["seeded"] += 1
            else:
                logger.warning(
                    f"  [LOW] {template_key}: confidence={result.confidence:.2f}"
                )
                stats["failed"] += 1
            
            # Rate limit: wait between API calls
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"  [ERR] {template_key}: {e}")
            stats["failed"] += 1
    
    return stats


async def seed_dimension_questions(dimension: str, dry_run: bool = False) -> Dict[str, int]:
    """차원별 질문 시딩."""
    from app.rag.hybrid_rag import hybrid_query
    from app.rag.semantic_cache import get_semantic_cache
    
    cache = get_semantic_cache()
    questions = DIMENSION_QUESTIONS.get(dimension, [])
    
    stats = {"seeded": 0, "skipped": 0, "failed": 0}
    
    logger.info(f"\n📐 Seeding dimension: {dimension}")
    
    for query in questions:
        cached = await cache.get(query, dimension=dimension)
        if cached:
            logger.info(f"  [SKIP] '{query[:40]}...': already cached")
            stats["skipped"] += 1
            continue
        
        if dry_run:
            logger.info(f"  [DRY] Would seed: '{query[:40]}...'")
            stats["seeded"] += 1
            continue
        
        try:
            result = await hybrid_query(
                query=query,
                dimension=dimension,
                use_google_search=True,
            )
            
            if result.confidence >= 0.4:
                await cache.set(
                    query=query,
                    response=result,
                    dimension=dimension,
                )
                logger.info(f"  [SEED] '{query[:40]}...': confidence={result.confidence:.2f}")
                stats["seeded"] += 1
            else:
                stats["failed"] += 1
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"  [ERR] '{query[:40]}...': {e}")
            stats["failed"] += 1
    
    return stats


async def seed_comparison_questions(dry_run: bool = False) -> Dict[str, int]:
    """비교 질문 시딩."""
    from app.rag.hybrid_rag import hybrid_query
    from app.rag.semantic_cache import get_semantic_cache
    
    cache = get_semantic_cache()
    stats = {"seeded": 0, "skipped": 0, "failed": 0}
    
    logger.info(f"\n🔀 Seeding comparison questions")
    
    for query in COMPARISON_QUESTIONS:
        cached = await cache.get(query)
        if cached:
            logger.info(f"  [SKIP] '{query[:40]}...': already cached")
            stats["skipped"] += 1
            continue
        
        if dry_run:
            logger.info(f"  [DRY] Would seed: '{query[:40]}...'")
            stats["seeded"] += 1
            continue
        
        try:
            result = await hybrid_query(
                query=query,
                use_google_search=True,
            )
            
            if result.confidence >= 0.4:
                await cache.set(query=query, response=result)
                logger.info(f"  [SEED] '{query[:40]}...': confidence={result.confidence:.2f}")
                stats["seeded"] += 1
            else:
                stats["failed"] += 1
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"  [ERR] '{query[:40]}...': {e}")
            stats["failed"] += 1
    
    return stats


async def seed_full(dry_run: bool = False) -> Dict[str, int]:
    """전체 시딩 실행."""
    total_stats = {"seeded": 0, "skipped": 0, "failed": 0}
    
    # Seed all auteurs
    for auteur_key in AUTEUR_KEYS:
        stats = await seed_auteur_questions(auteur_key, dry_run=dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]
    
    # Seed dimensions
    for dimension in DIMENSION_QUESTIONS.keys():
        stats = await seed_dimension_questions(dimension, dry_run=dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]
    
    # Seed comparisons
    stats = await seed_comparison_questions(dry_run=dry_run)
    for key in total_stats:
        total_stats[key] += stats[key]
    
    return total_stats


async def refresh_cache() -> Dict[str, int]:
    """캐시 갱신 (만료된 항목 재시딩)."""
    from app.rag.semantic_cache import get_semantic_cache
    
    cache = get_semantic_cache()
    stats = {"refreshed": 0, "still_valid": 0}
    
    logger.info("\n🔄 Refreshing expired cache entries...")
    
    # Get current cache stats
    current_stats = cache.get_stats()
    logger.info(f"Current cache size: {current_stats['memory_size']}")
    
    # In a full implementation, we'd iterate over DB entries
    # For now, just run full seed which will skip already cached
    seed_stats = await seed_full(dry_run=False)
    
    stats["refreshed"] = seed_stats["seeded"]
    stats["still_valid"] = seed_stats["skipped"]
    
    return stats


async def verify_cache() -> bool:
    """캐시 검증."""
    from app.rag.semantic_cache import get_semantic_cache
    
    cache = get_semantic_cache()
    
    logger.info("\n🔍 Verifying cache...")
    
    # Test queries
    test_queries = [
        ("강주노의 시각적 특징", "bong"),
        ("스토리보드 작성 가이드", None),
    ]
    
    success = True
    for query, auteur_key in test_queries:
        cached = await cache.get(query, auteur_key=auteur_key)
        if cached:
            logger.info(f"  ✓ '{query[:30]}...': HIT (confidence={cached.confidence:.2f})")
        else:
            logger.warning(f"  ✗ '{query[:30]}...': MISS")
            success = False
    
    # Print stats
    stats = cache.get_stats()
    logger.info(f"\n📊 Cache Stats:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    return success


def print_stats():
    """현재 캐시 통계 출력."""
    from app.rag.semantic_cache import get_semantic_cache
    
    cache = get_semantic_cache()
    stats = cache.get_stats()
    
    print("\n" + "=" * 50)
    print("📊 Semantic Cache Statistics")
    print("=" * 50)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🔝 Top Cached Entries:")
    top_entries = cache.get_top_entries(5)
    for i, entry in enumerate(top_entries, 1):
        print(f"  {i}. [{entry['hit_count']} hits] {entry['query']}")


# =============================================================================
# Main
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Seed RAG Semantic Cache")
    parser.add_argument("--full", action="store_true", help="Full seeding (all auteurs + dimensions)")
    parser.add_argument("--auteur", type=str, help="Seed specific auteur (e.g., 'bong')")
    parser.add_argument("--dimension", type=str, help="Seed specific dimension (e.g., 'AD')")
    parser.add_argument("--refresh", action="store_true", help="Refresh expired entries")
    parser.add_argument("--verify", action="store_true", help="Verify cache integrity")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be seeded without executing")
    args = parser.parse_args()
    
    print("🌱 RAG Semantic Cache Seeder")
    print("=" * 50)
    
    if args.stats:
        print_stats()
        return
    
    if args.verify:
        success = await verify_cache()
        sys.exit(0 if success else 1)
    
    if args.refresh:
        stats = await refresh_cache()
        print(f"\n✅ Refresh complete: {stats}")
        return
    
    if args.auteur:
        if args.auteur not in AUTEUR_KEYS:
            print(f"Unknown auteur: {args.auteur}")
            print(f"Available: {', '.join(AUTEUR_KEYS)}")
            sys.exit(1)
        stats = await seed_auteur_questions(args.auteur, dry_run=args.dry_run)
        print(f"\n✅ Seeding complete: {stats}")
        return
    
    if args.dimension:
        if args.dimension not in DIMENSION_QUESTIONS:
            print(f"Unknown dimension: {args.dimension}")
            print(f"Available: {', '.join(DIMENSION_QUESTIONS.keys())}")
            sys.exit(1)
        stats = await seed_dimension_questions(args.dimension, dry_run=args.dry_run)
        print(f"\n✅ Seeding complete: {stats}")
        return
    
    if args.full:
        stats = await seed_full(dry_run=args.dry_run)
        print(f"\n✅ Full seeding complete:")
        print(f"   Seeded:  {stats['seeded']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Failed:  {stats['failed']}")
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
