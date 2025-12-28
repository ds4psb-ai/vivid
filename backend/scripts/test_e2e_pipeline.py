"""E2E Integration Test.

Tests the full pipeline:
1. VideoSegments → Source Pack (Stage 2)
2. Source Pack → NotebookLM Guide (Stage 4)
3. Guide → Storyboard Cards (Stage 8)
4. Storyboard → Shot Contracts → Generation (Stage 10)

Usage:
    python scripts/test_e2e_pipeline.py --source-id bong-2019-parasite
    python scripts/test_e2e_pipeline.py --demo
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import VideoSegment
from app.source_pack import build_source_pack
from app.notebooklm_client import (
    generate_story_beats,
    generate_storyboard_cards,
    run_notebooklm_analysis,
)
from app.generation_client import (
    GenProvider,
    run_generation_pipeline,
    create_shot_contracts_from_storyboard,
)
from sqlalchemy import select


async def fetch_segments(source_id: str, limit: int = 10) -> List[VideoSegment]:
    """Fetch segments from DB."""
    async with AsyncSessionLocal() as db:
        query = select(VideoSegment)
        if source_id:
            query = query.where(VideoSegment.source_id == source_id)
        query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


def guide_to_storyboard(
    source_pack: Dict[str, Any],
    capsule_id: str,
    summary: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate story beats and storyboard cards from NotebookLM output."""
    guide = summary.get("guide", {})
    claims = summary.get("claims", [])
    story_beats = generate_story_beats(source_pack, capsule_id, guide, claims)
    storyboard_cards = generate_storyboard_cards(
        source_pack,
        capsule_id,
        guide,
        claims,
        story_beats,
    )
    return {"story_beats": story_beats, "storyboard_cards": storyboard_cards}


async def run_e2e_test(
    source_id: str = None,
    capsule_id: str = "auteur.bong-joon-ho",
    temporal_phase: str = "HOOK",
    use_demo: bool = False,
) -> Dict[str, Any]:
    """Run full E2E integration test."""
    print(f"\n{'='*70}")
    print(f"🧪 E2E INTEGRATION TEST")
    print(f"{'='*70}")
    print(f"Source ID: {source_id or '(demo)'}")
    print(f"Capsule ID: {capsule_id}")
    print(f"Temporal Phase: {temporal_phase}")
    print(f"{'='*70}\n")
    
    start_time = datetime.utcnow()
    results = {
        "stages": {},
        "success": True,
        "errors": [],
    }
    
    await init_db()
    
    # ─────────────────────────────────────────────────────────────────────
    # Stage 2: VideoSegments → Source Pack
    # ─────────────────────────────────────────────────────────────────────
    print("📊 Stage 2: Fetching VideoSegments...")
    try:
        if use_demo:
            # Create demo segment-like data
            class DemoSegment:
                segment_id = "demo-seg-001"
                source_id = "demo-source"
                work_id = "demo-work"
                scene_id = "demo-scene"
                shot_id = "demo-shot"
                time_start = "00:00:00"
                time_end = "00:00:30"
            segments = [DemoSegment()]
        else:
            segments = await fetch_segments(source_id)
        
        print(f"   ✅ Found {len(segments)} segments")
        results["stages"]["stage_2"] = {"status": "success", "segments": len(segments)}
        
        # Build source pack
        cluster_id = f"CL_{capsule_id.split('.')[-1].upper()}"
        if hasattr(segments[0], 'segment_id'):
            source_pack = build_source_pack(
                segments,
                cluster_id=cluster_id,
                temporal_phase=temporal_phase,
            )
        else:
            source_pack = {
                "pack_id": f"sp_{cluster_id}_{temporal_phase}_demo",
                "cluster_id": cluster_id,
                "temporal_phase": temporal_phase,
                "segment_refs": [],
                "source_count": len(segments),
            }
        print(f"   ✅ Source Pack ID: {source_pack.get('pack_id')}")
        
    except Exception as e:
        print(f"   ❌ Stage 2 failed: {e}")
        results["stages"]["stage_2"] = {"status": "failed", "error": str(e)}
        results["success"] = False
        results["errors"].append(f"Stage 2: {e}")
        return results
    
    # ─────────────────────────────────────────────────────────────────────
    # Stage 4: Source Pack → NotebookLM Guide
    # ─────────────────────────────────────────────────────────────────────
    print("\n🧠 Stage 4: Running NotebookLM Analysis...")
    try:
        summary, evidence_refs = run_notebooklm_analysis(source_pack, capsule_id)
        
        has_logic = bool(summary.get("logic_vector"))
        has_persona = bool(summary.get("persona_vector"))
        has_guide = bool(summary.get("guide"))
        claims_count = len(summary.get("claims", []))
        token_usage = summary.get("token_usage", {}).get("total", 0)
        
        print(f"   ✅ Logic Vector: {has_logic}")
        print(f"   ✅ Persona Vector: {has_persona}")
        print(f"   ✅ Guide: {has_guide}")
        print(f"   ✅ Claims: {claims_count}")
        print(f"   ✅ Tokens: {token_usage}")
        
        results["stages"]["stage_4"] = {
            "status": "success",
            "logic_vector": has_logic,
            "persona_vector": has_persona,
            "guide": has_guide,
            "claims": claims_count,
            "tokens": token_usage,
        }
        
    except Exception as e:
        print(f"   ❌ Stage 4 failed: {e}")
        results["stages"]["stage_4"] = {"status": "failed", "error": str(e)}
        results["success"] = False
        results["errors"].append(f"Stage 4: {e}")
        return results
    
    # ─────────────────────────────────────────────────────────────────────
    # Stage 8: Guide → Storyboard Cards
    # ─────────────────────────────────────────────────────────────────────
    print("\n📜 Stage 8: Converting Guide to Storyboard...")
    try:
        narrative = guide_to_storyboard(source_pack, capsule_id, summary)
        story_beats = narrative.get("story_beats", [])
        storyboard_cards = narrative.get("storyboard_cards", [])
        print(f"   ✅ Generated {len(story_beats)} story beats")
        print(f"   ✅ Generated {len(storyboard_cards)} storyboard cards")
        for card in storyboard_cards[:3]:
            shot_label = card.get("shot") or card.get("shot_type") or card.get("card_id") or "shot"
            note = card.get("note") or card.get("description") or card.get("summary") or ""
            print(f"      - {shot_label}: {note}")
        
        results["stages"]["stage_8"] = {
            "status": "success",
            "beats": len(story_beats),
            "cards": len(storyboard_cards),
        }
        
    except Exception as e:
        print(f"   ❌ Stage 8 failed: {e}")
        results["stages"]["stage_8"] = {"status": "failed", "error": str(e)}
        results["success"] = False
        results["errors"].append(f"Stage 8: {e}")
        return results
    
    # ─────────────────────────────────────────────────────────────────────
    # Stage 10: Storyboard → Generation
    # ─────────────────────────────────────────────────────────────────────
    print("\n🎬 Stage 10: Running Generation Pipeline...")
    try:
        gen_results, metrics = await run_generation_pipeline(
            storyboard_cards,
            provider=GenProvider.MOCK,
            sequence_id=f"seq-{temporal_phase.lower()}",
            scene_id=f"scene-{capsule_id.split('.')[-1]}",
        )
        
        success_count = metrics.get("success_count", 0)
        total_shots = metrics.get("total_shots", 0)
        success_rate = metrics.get("success_rate", 0)
        
        print(f"   ✅ Generated: {success_count}/{total_shots} shots")
        print(f"   ✅ Success Rate: {success_rate * 100:.0f}%")
        print(f"   ✅ Duration: {metrics.get('pipeline_duration_sec', 0):.2f}s")
        
        for result in gen_results[:3]:
            status_emoji = "✅" if result.status == "success" else "❌"
            print(f"      {status_emoji} {result.shot_id}: {result.output_url or result.error}")
        
        results["stages"]["stage_10"] = {
            "status": "success",
            "shots_generated": success_count,
            "total_shots": total_shots,
            "success_rate": success_rate,
            "outputs": [r.output_url for r in gen_results if r.output_url],
        }
        
    except Exception as e:
        print(f"   ❌ Stage 10 failed: {e}")
        results["stages"]["stage_10"] = {"status": "failed", "error": str(e)}
        results["success"] = False
        results["errors"].append(f"Stage 10: {e}")
        return results
    
    # ─────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    results["duration_sec"] = elapsed
    
    print(f"\n{'='*70}")
    if results["success"]:
        print("✅ E2E TEST PASSED!")
    else:
        print("❌ E2E TEST FAILED!")
        for error in results["errors"]:
            print(f"   - {error}")
    print(f"{'='*70}")
    print(f"Total Duration: {elapsed:.2f}s")
    print(f"Stages Completed: {len([s for s in results['stages'].values() if s.get('status') == 'success'])}/4")
    
    return results


async def main():
    parser = argparse.ArgumentParser(description="E2E Integration Test")
    parser.add_argument("--source-id", "-s", help="Source ID for segments")
    parser.add_argument("--capsule-id", "-c", default="auteur.bong-joon-ho")
    parser.add_argument("--temporal-phase", "-p", default="HOOK")
    parser.add_argument("--demo", action="store_true", help="Use demo data")
    
    args = parser.parse_args()
    
    results = await run_e2e_test(
        source_id=args.source_id,
        capsule_id=args.capsule_id,
        temporal_phase=args.temporal_phase,
        use_demo=args.demo,
    )
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
