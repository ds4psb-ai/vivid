"""Ingest pattern atoms from shot corpus into Qdrant foundry_pattern_atoms collection.

Reads the shot corpus, groups by director, runs PatternExtractionService.extract()
per director, and auto-upserts to foundry_pattern_atoms.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Extract patterns without upserting")
    parser.add_argument("--data-path", default="data/foundry/seed_shot_corpus.json")
    args = parser.parse_args()

    data_path = Path(args.data_path)
    if not data_path.exists():
        print(f"ERROR: {data_path} not found", flush=True)
        sys.exit(1)

    with open(data_path) as f:
        shots = json.load(f)

    print(f"Loaded {len(shots)} shots", flush=True)

    # Group by director
    by_director: dict[str, list[dict]] = defaultdict(list)
    for shot in shots:
        by_director[shot["director"]].append(shot)

    print(f"Directors: {list(by_director.keys())}", flush=True)

    # Extract patterns per director using PatternExtractionService
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService

    service = PatternExtractionService(qdrant_store=None)
    all_results = []

    for director, director_shots in sorted(by_director.items()):
        result = service.extract(
            project_id=f"seed_{director}",
            scene_id=f"corpus_{director}",
            shots=director_shots,
        )
        all_results.append(result)
        print(
            f"  {director}: {len(director_shots)} shots -> "
            f"{len(result['pattern_atoms'])} atoms, "
            f"{len(result['transition_rules'])} transition rules",
            flush=True,
        )

    total_atoms = sum(len(r["pattern_atoms"]) for r in all_results)
    print(f"Total pattern atoms extracted: {total_atoms}", flush=True)

    if args.dry_run:
        print(f"DRY RUN: {total_atoms} atoms extracted, skipping Qdrant upsert", flush=True)
        return

    # Real ingestion
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qdrant_models
        from app.config import settings
        import hashlib

        api_key = settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None
        client = QdrantClient(url=settings.QDRANT_URL, api_key=api_key, timeout=30)

        points = []
        for result in all_results:
            project_id = result["project_id"]
            for atom in result["pattern_atoms"]:
                text = f"{atom['camera_angle']} {atom['camera_movement']} {atom['shot_size']} {atom['emotion_tone']} {atom['transition']}"
                h = hashlib.sha384(text.encode()).digest()
                vector = [((b - 128) / 128.0) for b in h]

                point_id = hashlib.md5(f"{project_id}:{atom['atom_id']}".encode()).hexdigest()
                payload = {**atom, "project_id": project_id, "scene_id": result["scene_id"]}
                points.append(qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                ))

        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(collection_name="foundry_pattern_atoms", points=batch)
            print(f"Upserted {min(i + batch_size, len(points))}/{len(points)}", flush=True)

        print(f"SUCCESS: {len(points)} atoms ingested into foundry_pattern_atoms", flush=True)
    except Exception as e:
        print(f"ERROR: Ingestion failed: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
