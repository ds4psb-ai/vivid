#!/usr/bin/env python
"""NotebookLM Studio 산출물 배치 생성 스크립트.

거장별 Audio Overview, Infographic, Mind Map 등을 사전 생성하여 저장.

Usage:
    cd backend
    source venv/bin/activate
    
    # 전체 생성 (모든 거장 × 모든 유형)
    python scripts/generate_studio_artifacts.py --full
    
    # 특정 거장만 생성
    python scripts/generate_studio_artifacts.py --auteur bong
    
    # 특정 유형만 생성
    python scripts/generate_studio_artifacts.py --type audio
    
    # 저장소 상태 확인
    python scripts/generate_studio_artifacts.py --stats
    
    # 만료된 산출물 정리
    python scripts/generate_studio_artifacts.py --cleanup

Cron 설정 (월 1회):
    0 4 1 * * cd /app/backend && python scripts/generate_studio_artifacts.py --refresh
"""
import argparse
import asyncio
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

AUTEUR_NOTEBOOKS = {
    "bong": "auteur_bong",
    "epoch": "auteur_epoch", 
    "abyss": "auteur_abyss",
    "wong": "auteur_wong",
    "voltage": "auteur_voltage",
    "park": "auteur_park",
    "azure": "auteur_azure",
}

AUTEUR_NAMES = {
    "bong": "강주노",
    "epoch": "크리스토퍼 테오 에포크",
    "abyss": "드니 빌뇌브",
    "wong": "왕가위",
    "voltage": "쿠엔틴 타란티노",
    "park": "박찬욱",
    "azure": "소라 아주르 마코토",
}

# Generation topics for each artifact type
AUDIO_TOPICS = [
    "{name}의 영화 미학과 시각적 스타일 분석",
]

INFOGRAPHIC_TOPICS = [
    "{name} 감독의 시각적 DNA 요약",
]

MIND_MAP_TOPICS = [
    "{name} 영화 세계관 구조",
]


# =============================================================================
# Generation Functions
# =============================================================================

async def generate_audio_overview(
    auteur_key: str,
    topic: str,
    dry_run: bool = False,
) -> Dict[str, any]:
    """거장별 Audio Overview 생성."""
    from app.rag.artifact_storage import get_artifact_storage, ArtifactType
    
    storage = get_artifact_storage()
    auteur_name = AUTEUR_NAMES.get(auteur_key, auteur_key)
    focus_topic = topic.format(name=auteur_name)
    
    # Check if already exists
    existing = await storage.get_artifact(
        auteur_key=auteur_key,
        artifact_type=ArtifactType.AUDIO,
        focus_topic=focus_topic,
    )
    if existing:
        logger.info(f"  [SKIP] Audio already exists: {focus_topic[:40]}...")
        return {"status": "skipped", "artifact_id": existing.artifact_id}
    
    if dry_run:
        logger.info(f"  [DRY] Would generate audio: {focus_topic[:40]}...")
        return {"status": "dry_run"}
    
    try:
        # Call NotebookLM MCP to generate audio overview
        from app.rag.tier0_notebooklm import get_notebooklm_service
        
        service = get_notebooklm_service()
        notebook_key = AUTEUR_NOTEBOOKS.get(auteur_key)
        
        if not notebook_key:
            logger.warning(f"  [ERR] No notebook configured for: {auteur_key}")
            return {"status": "error", "message": "No notebook configured"}
        
        # Generate audio overview (this calls MCP)
        result = await service.create_audio_overview(
            notebook_key=notebook_key,
            format_code=1,  # Deep Dive
            language="ko",
        )
        
        if result and result.get("audio_bytes"):
            artifact = await storage.store_audio_overview(
                auteur_key=auteur_key,
                audio_bytes=result["audio_bytes"],
                focus_topic=focus_topic,
                notebook_id=notebook_key,
            )
            logger.info(f"  [DONE] Audio generated: {artifact.artifact_id[:8]}...")
            return {"status": "success", "artifact_id": artifact.artifact_id}
        else:
            logger.warning(f"  [ERR] Audio generation returned no data")
            return {"status": "error", "message": "No audio data returned"}
            
    except Exception as e:
        logger.error(f"  [ERR] Audio generation failed: {e}")
        return {"status": "error", "message": str(e)}


async def generate_infographic(
    auteur_key: str,
    topic: str,
    dry_run: bool = False,
) -> Dict[str, any]:
    """거장별 Infographic 생성."""
    from app.rag.artifact_storage import get_artifact_storage, ArtifactType
    
    storage = get_artifact_storage()
    auteur_name = AUTEUR_NAMES.get(auteur_key, auteur_key)
    focus_topic = topic.format(name=auteur_name)
    
    # Check if already exists
    existing = await storage.get_artifact(
        auteur_key=auteur_key,
        artifact_type=ArtifactType.INFOGRAPHIC,
        focus_topic=focus_topic,
    )
    if existing:
        logger.info(f"  [SKIP] Infographic already exists: {focus_topic[:40]}...")
        return {"status": "skipped", "artifact_id": existing.artifact_id}
    
    if dry_run:
        logger.info(f"  [DRY] Would generate infographic: {focus_topic[:40]}...")
        return {"status": "dry_run"}
    
    try:
        from app.rag.tier0_notebooklm import get_notebooklm_service
        
        service = get_notebooklm_service()
        notebook_key = AUTEUR_NOTEBOOKS.get(auteur_key)
        
        if not notebook_key:
            return {"status": "error", "message": "No notebook configured"}
        
        result = await service.create_infographic(
            notebook_key=notebook_key,
            prompt=focus_topic,
            orientation_code=1,  # Square
            detail_level_code=2,  # Standard
        )
        
        if result and result.get("image_bytes"):
            artifact = await storage.store_infographic(
                auteur_key=auteur_key,
                image_bytes=result["image_bytes"],
                focus_topic=focus_topic,
                notebook_id=notebook_key,
            )
            logger.info(f"  [DONE] Infographic generated: {artifact.artifact_id[:8]}...")
            return {"status": "success", "artifact_id": artifact.artifact_id}
        else:
            return {"status": "error", "message": "No image data returned"}
            
    except Exception as e:
        logger.error(f"  [ERR] Infographic generation failed: {e}")
        return {"status": "error", "message": str(e)}


async def generate_mind_map(
    auteur_key: str,
    topic: str,
    dry_run: bool = False,
) -> Dict[str, any]:
    """거장별 Mind Map 생성."""
    from app.rag.artifact_storage import get_artifact_storage, ArtifactType
    
    storage = get_artifact_storage()
    auteur_name = AUTEUR_NAMES.get(auteur_key, auteur_key)
    focus_topic = topic.format(name=auteur_name)
    
    # Check if already exists
    existing = await storage.get_artifact(
        auteur_key=auteur_key,
        artifact_type=ArtifactType.MIND_MAP,
        focus_topic=focus_topic,
    )
    if existing:
        logger.info(f"  [SKIP] Mind map already exists: {focus_topic[:40]}...")
        return {"status": "skipped", "artifact_id": existing.artifact_id}
    
    if dry_run:
        logger.info(f"  [DRY] Would generate mind map: {focus_topic[:40]}...")
        return {"status": "dry_run"}
    
    try:
        from app.rag.tier0_notebooklm import get_notebooklm_service
        
        service = get_notebooklm_service()
        notebook_key = AUTEUR_NOTEBOOKS.get(auteur_key)
        
        if not notebook_key:
            return {"status": "error", "message": "No notebook configured"}
        
        result = await service.generate_mind_map(
            notebook_key=notebook_key,
        )
        
        if result and result.get("mind_map_json"):
            artifact = await storage.store_mind_map(
                auteur_key=auteur_key,
                mind_map_json=result["mind_map_json"],
                focus_topic=focus_topic,
                notebook_id=notebook_key,
            )
            logger.info(f"  [DONE] Mind map generated: {artifact.artifact_id[:8]}...")
            return {"status": "success", "artifact_id": artifact.artifact_id}
        else:
            return {"status": "error", "message": "No mind map data returned"}
            
    except Exception as e:
        logger.error(f"  [ERR] Mind map generation failed: {e}")
        return {"status": "error", "message": str(e)}


async def generate_artifacts_for_auteur(
    auteur_key: str,
    artifact_types: Optional[List[str]] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """거장별 모든 산출물 생성."""
    auteur_name = AUTEUR_NAMES.get(auteur_key, auteur_key)
    logger.info(f"\n🎬 Generating artifacts for: {auteur_name}")
    
    stats = {"success": 0, "skipped": 0, "error": 0}
    types_to_generate = artifact_types or ["audio", "infographic", "mind_map"]
    
    # Audio Overview
    if "audio" in types_to_generate:
        for topic in AUDIO_TOPICS:
            result = await generate_audio_overview(auteur_key, topic, dry_run)
            stats[result.get("status", "error")] = stats.get(result.get("status", "error"), 0) + 1
            await asyncio.sleep(5)  # Rate limit
    
    # Infographic
    if "infographic" in types_to_generate:
        for topic in INFOGRAPHIC_TOPICS:
            result = await generate_infographic(auteur_key, topic, dry_run)
            stats[result.get("status", "error")] = stats.get(result.get("status", "error"), 0) + 1
            await asyncio.sleep(3)
    
    # Mind Map
    if "mind_map" in types_to_generate:
        for topic in MIND_MAP_TOPICS:
            result = await generate_mind_map(auteur_key, topic, dry_run)
            stats[result.get("status", "error")] = stats.get(result.get("status", "error"), 0) + 1
            await asyncio.sleep(3)
    
    return stats


async def generate_full(
    artifact_types: Optional[List[str]] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """모든 거장 × 모든 유형 생성."""
    total_stats = {"success": 0, "skipped": 0, "error": 0, "dry_run": 0}
    
    for auteur_key in AUTEUR_KEYS:
        stats = await generate_artifacts_for_auteur(auteur_key, artifact_types, dry_run)
        for key, value in stats.items():
            total_stats[key] = total_stats.get(key, 0) + value
    
    return total_stats


def print_stats():
    """저장소 통계 출력."""
    from app.rag.artifact_storage import get_artifact_storage
    
    storage = get_artifact_storage()
    stats = storage.get_stats()
    
    print("\n" + "=" * 50)
    print("📦 Studio Artifact Storage Statistics")
    print("=" * 50)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n📋 Recent Artifacts:")
    artifacts = storage.list_artifacts(limit=5)
    for i, artifact in enumerate(artifacts, 1):
        print(f"  {i}. [{artifact.artifact_type.value}] {artifact.auteur_key}: {artifact.focus_topic[:40]}...")


def cleanup_expired():
    """만료된 산출물 정리."""
    from app.rag.artifact_storage import get_artifact_storage
    
    storage = get_artifact_storage()
    count = storage.cleanup_expired()
    print(f"✓ Cleaned up {count} expired artifacts")


# =============================================================================
# Main
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Generate NotebookLM Studio Artifacts")
    parser.add_argument("--full", action="store_true", help="Full generation (all auteurs × all types)")
    parser.add_argument("--auteur", type=str, help="Generate for specific auteur (e.g., 'bong')")
    parser.add_argument("--type", type=str, choices=["audio", "infographic", "mind_map", "all"],
                       help="Generate specific artifact type")
    parser.add_argument("--refresh", action="store_true", help="Refresh expired artifacts")
    parser.add_argument("--stats", action="store_true", help="Show storage statistics")
    parser.add_argument("--cleanup", action="store_true", help="Clean up expired artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()
    
    print("🎨 Studio Artifact Generator")
    print("=" * 50)
    
    if args.stats:
        print_stats()
        return
    
    if args.cleanup:
        cleanup_expired()
        return
    
    artifact_types = None
    if args.type and args.type != "all":
        artifact_types = [args.type]
    
    if args.auteur:
        if args.auteur not in AUTEUR_KEYS:
            print(f"Unknown auteur: {args.auteur}")
            print(f"Available: {', '.join(AUTEUR_KEYS)}")
            sys.exit(1)
        stats = await generate_artifacts_for_auteur(args.auteur, artifact_types, args.dry_run)
        print(f"\n✅ Generation complete: {stats}")
        return
    
    if args.full or args.refresh:
        stats = await generate_full(artifact_types, args.dry_run)
        print(f"\n✅ Full generation complete:")
        print(f"   Success:  {stats.get('success', 0)}")
        print(f"   Skipped:  {stats.get('skipped', 0)}")
        print(f"   Errors:   {stats.get('error', 0)}")
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
