"""Ingest seed shot corpus into Qdrant foundry_shot_corpus collection."""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate without upserting")
    parser.add_argument("--data-path", default="data/foundry/seed_shot_corpus.json")
    args = parser.parse_args()

    data_path = Path(args.data_path)
    if not data_path.exists():
        print(f"ERROR: {data_path} not found", flush=True)
        sys.exit(1)

    with open(data_path) as f:
        shots = json.load(f)

    print(f"Loaded {len(shots)} shots", flush=True)

    # Validate
    required_fields = {"shot_id", "shot_size", "camera_angle", "camera_movement", "emotion_tone", "transition_to_next", "director"}
    for i, shot in enumerate(shots):
        missing = required_fields - set(shot.keys())
        if missing:
            print(f"ERROR: Shot {i} missing fields: {missing}", flush=True)
            sys.exit(1)

    if args.dry_run:
        print(f"DRY RUN: {len(shots)} shots validated OK", flush=True)
        # Print director distribution
        from collections import Counter
        dist = Counter(s["director"] for s in shots)
        for director, count in dist.most_common():
            print(f"  {director}: {count} shots", flush=True)
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
        for shot in shots:
            # Create a simple text embedding placeholder (384d zero vector for now)
            text = f"{shot['shot_size']} {shot['camera_angle']} {shot['camera_movement']} {shot['emotion_tone']} {shot['transition_to_next']}"
            # Use hash-based pseudo-vector for deterministic results
            h = hashlib.sha384(text.encode()).digest()
            vector = [((b - 128) / 128.0) for b in h]

            point_id = hashlib.md5(shot["shot_id"].encode()).hexdigest()
            points.append(qdrant_models.PointStruct(
                id=point_id,
                vector=vector,
                payload=shot,
            ))

        # Batch upsert
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(collection_name="foundry_shot_corpus", points=batch)
            print(f"Upserted {min(i + batch_size, len(points))}/{len(points)}", flush=True)

        print(f"SUCCESS: {len(points)} shots ingested into foundry_shot_corpus", flush=True)
    except Exception as e:
        print(f"ERROR: Ingestion failed: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
