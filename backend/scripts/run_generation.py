"""Run Generation Pipeline.

This script connects:
1. Storyboard Cards → Shot Contracts
2. Shot Contracts → Prompt Contracts
3. Prompt Contracts → Gen Runs (batch)

Usage:
    python scripts/run_generation.py --storyboard data/storyboard.json
    python scripts/run_generation.py --storyboard data/derived_outputs.json
    python scripts/run_generation.py --capsule-run-id <run_id>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.generation_client import (
    GenProvider,
    ShotContract,
    run_generation_pipeline,
    create_shot_contracts_from_storyboard,
    shot_contract_to_prompt,
)
from app.models import CapsuleRun


def load_storyboard(path: str) -> List[Dict[str, Any]]:
    """Load storyboard cards from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle list of cards or derived outputs.
    if isinstance(data, list):
        if data and all(isinstance(item, dict) for item in data):
            for item in data:
                if item.get("guide_type") == "storyboard":
                    cards = item.get("storyboard_cards")
                    if isinstance(cards, list):
                        return cards
            for item in data:
                cards = item.get("storyboard_cards")
                if isinstance(cards, list):
                    return cards
        return data
    elif isinstance(data, dict):
        for key in ("storyboard_cards", "storyboard", "cards"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []
    return []


async def load_storyboard_from_capsule_run(run_id: str) -> List[Dict[str, Any]]:
    """Load storyboard cards from a capsule run summary."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise ValueError(f"Invalid capsule run id: {run_id}") from exc
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
        run = result.scalars().first()
    if not run:
        raise ValueError(f"Capsule run not found: {run_id}")
    summary = run.summary or {}
    if isinstance(summary, dict):
        cards = summary.get("storyboard_cards") or summary.get("storyboard")
        if isinstance(cards, list):
            return cards
        final_spec = summary.get("final_spec")
        if isinstance(final_spec, dict):
            cards = final_spec.get("storyboard")
            if isinstance(cards, list):
                return cards
    raise ValueError(f"No storyboard cards found in capsule run: {run_id}")


async def run_pipeline(
    storyboard_path: str = None,
    storyboard_cards: List[Dict[str, Any]] = None,
    capsule_run_id: str = None,
    provider: str = "mock",
    sequence_id: str = "seq-01",
    scene_id: str = "scene-01",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run the full generation pipeline."""
    print(f"\n{'='*60}")
    print(f"🎬 Generation Pipeline")
    print(f"{'='*60}")
    print(f"Provider: {provider}")
    print(f"Sequence: {sequence_id}")
    print(f"Scene: {scene_id}")
    print(f"Dry Run: {dry_run}")
    print(f"{'='*60}\n")
    
    await init_db()
    
    # Step 1: Load storyboard
    if capsule_run_id:
        print("📜 Loading storyboard from capsule run...")
        cards = await load_storyboard_from_capsule_run(capsule_run_id)
    elif storyboard_path:
        print("📜 Loading storyboard from file...")
        cards = load_storyboard(storyboard_path)
    elif storyboard_cards:
        cards = storyboard_cards
    else:
        # Demo storyboard
        print("📜 Using demo storyboard...")
        cards = [
            {
                "card_index": 1,
                "title": "Opening Shot",
                "description": "Wide establishing shot of rain-soaked street at night",
                "shot_type": "wide",
                "duration_sec": 5,
                "mood": "melancholy",
                "lighting": "low-key neon",
            },
            {
                "card_index": 2,
                "title": "Character Introduction",
                "description": "Medium shot of protagonist walking under umbrella",
                "shot_type": "medium",
                "duration_sec": 4,
                "mood": "contemplative",
                "lighting": "backlit rain",
            },
            {
                "card_index": 3,
                "title": "Close-up Moment",
                "description": "Close-up of face, rain drops on umbrella visible",
                "shot_type": "close-up",
                "duration_sec": 3,
                "mood": "introspective",
                "lighting": "soft diffused",
            },
        ]
    
    print(f"   Loaded {len(cards)} storyboard cards")
    
    # Step 2: Create shot contracts
    print("\n📋 Step 2: Creating Shot Contracts...")
    contracts = create_shot_contracts_from_storyboard(
        cards, sequence_id, scene_id
    )
    for contract in contracts:
        print(f"   {contract.shot_id}: {contract.shot_type}, {contract.duration_sec}s")
    
    # Step 3: Preview prompts
    print("\n✏️  Step 3: Generated Prompts:")
    for contract in contracts:
        prompt = shot_contract_to_prompt(contract)
        print(f"\n   [{contract.shot_id}]")
        print(f"   Prompt: {prompt.prompt[:100]}...")
        print(f"   Strategy: {prompt.strategy.value}")
    
    if dry_run:
        print("\n⏭️  Step 4: Skipped (dry run)")
        return {
            "status": "dry_run",
            "contracts": len(contracts),
            "prompts_generated": len(contracts),
        }
    
    # Step 4: Run generation
    print(f"\n🚀 Step 4: Running Generation (provider: {provider})...")
    gen_provider = GenProvider(provider)
    results, metrics = await run_generation_pipeline(
        cards,
        provider=gen_provider,
        sequence_id=sequence_id,
        scene_id=scene_id,
    )
    
    # Results summary
    print(f"\n{'='*60}")
    print("📊 Results")
    print(f"{'='*60}")
    for result in results:
        status_emoji = "✅" if result.status == "success" else "❌"
        print(f"   {status_emoji} {result.shot_id}: {result.status}")
        if result.output_url:
            print(f"      Output: {result.output_url}")
        if result.error:
            print(f"      Error: {result.error}")
    
    print(f"\n📈 Metrics:")
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    return {
        "status": "success",
        "results": [
            {
                "shot_id": r.shot_id,
                "status": r.status,
                "output_url": r.output_url,
                "iteration": r.iteration,
            }
            for r in results
        ],
        "metrics": metrics,
    }


async def main():
    parser = argparse.ArgumentParser(description="Run Generation Pipeline")
    parser.add_argument("--storyboard", "-s", help="Path to storyboard JSON")
    parser.add_argument("--capsule-run-id", help="Load storyboard from capsule run ID")
    parser.add_argument("--provider", "-p", default="mock", 
                        choices=["mock", "veo", "kling"],
                        help="Generation provider")
    parser.add_argument("--sequence-id", default="seq-01", help="Sequence ID")
    parser.add_argument("--scene-id", default="scene-01", help="Scene ID")
    parser.add_argument("--dry-run", "-n", action="store_true", 
                        help="Preview prompts without generating")
    
    args = parser.parse_args()
    
    await run_pipeline(
        storyboard_path=args.storyboard,
        capsule_run_id=args.capsule_run_id,
        provider=args.provider,
        sequence_id=args.sequence_id,
        scene_id=args.scene_id,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    asyncio.run(main())
