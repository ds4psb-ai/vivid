import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def _run(cmd: List[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the sample pipeline in order (data/)."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run with DB writes. Default runs --dry-run where supported.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    data_dir = root / "data"
    python = sys.executable
    dry_run = not args.execute

    steps: List[Tuple[str, List[str], bool]] = [
        (
            "raw_assets",
            [
                python,
                "backend/scripts/ingest_raw_assets.py",
                "--input",
                str(data_dir / "raw_assets.json"),
            ],
            True,
        ),
        (
            "video_segments",
            [
                python,
                "backend/scripts/ingest_video_structured.py",
                "--input",
                str(data_dir / "video_segments.json"),
                "--default-prompt-version",
                "gemini-video-v1",
                "--default-model-version",
                "gemini-3-pro-2025-12",
            ],
            True,
        ),
        (
            "notebook_library",
            [
                python,
                "backend/scripts/ingest_notebook_library.py",
                "--input",
                str(data_dir / "notebooks.json"),
            ],
            True,
        ),
        (
            "notebook_assets",
            [
                python,
                "backend/scripts/ingest_notebook_assets.py",
                "--input",
                str(data_dir / "notebook_assets.json"),
            ],
            True,
        ),
        (
            "derived_insights",
            [
                python,
                "backend/scripts/ingest_derived_insights.py",
                "--input",
                str(data_dir / "derived_insights.json"),
                "--default-output-language",
                "en",
                "--default-prompt-version",
                "nlm-guide-v1",
                "--default-model-version",
                "notebooklm-2025-12",
            ],
            True,
        ),
        (
            "pattern_candidates",
            [
                python,
                "backend/scripts/ingest_pattern_candidates.py",
                "--input",
                str(data_dir / "pattern_candidates.json"),
            ],
            True,
        ),
        (
            "pattern_promotion",
            [
                python,
                "backend/scripts/promote_patterns.py",
                "--note",
                "sample promotion",
            ],
            True,
        ),
        (
            "capsule_pattern_version",
            [
                python,
                "backend/scripts/update_capsule_pattern_version.py",
            ],
            True,
        ),
        (
            "template_seed",
            [
                python,
                "backend/scripts/seed_template_from_evidence.py",
                "--notebook-id",
                "nlb-sample-auteur",
                "--slug",
                "sample-auteur-template",
                "--title",
                "Sample Auteur Template",
                "--capsule-key",
                "auteur.bong-joon-ho",
                "--capsule-version",
                "1.0.1",
                "--tags",
                "sample,auteur",
            ],
            False,
        ),
        (
            "pipeline_report",
            [
                python,
                "backend/scripts/pipeline_report.py",
            ],
            False,
        ),
    ]

    for name, cmd, supports_dry_run in steps:
        if dry_run and supports_dry_run:
            cmd = [*cmd, "--dry-run"]
        if dry_run and not supports_dry_run:
            print(f"- skip {name}: requires --execute")
            continue
        _run(cmd)


if __name__ == "__main__":
    main()
