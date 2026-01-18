#!/usr/bin/env python
"""Seed All Dimension RAG collections into Qdrant.

Indexes data into the following lacking collections:
- 3D: Image Style, Visual Guide (cinematography, visual DNA)
- 4D: Analysis Framework, VDG (thematic analysis, quality criteria)
- 5D: Video Generation, Camera Movement (veo templates)
- 6D: Sound/Music Design (sound design, music philosophy)
- AI: Persona Analysis, MBTI (psychology data)

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_all_dimension_rag.py

    # Seed specific dimension only
    python scripts/seed_all_dimension_rag.py --dimension 3D

    # Verify all collections
    python scripts/seed_all_dimension_rag.py --verify

2026 Best Practices Applied:
- Batch upsert for efficiency
- Rich content with structured metadata
- Consistent doc_id patterns for deduplication
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.tier1_dimension_rag import get_dimension_rag, DIMENSION_COLLECTIONS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Data paths
RAG_DOCS_DIR = Path(__file__).parent.parent / "data" / "rag_docs"
SOURCE_PACKS_DIR = Path(__file__).parent.parent.parent / "data" / "source_packs"
LOGIC_MATH_DIR = SOURCE_PACKS_DIR / "logic_math" / "vectors"

# =============================================================================
# Utility Functions
# =============================================================================

def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dict for content generation."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ", ".join(str(x) for x in v)))
        else:
            items.append((new_key, str(v)))
    return dict(items)


def extract_content_from_source_pack(data: dict) -> str:
    """Extract rich content from auteur source pack JSON."""
    content_parts = []

    # Basic info
    if "auteur" in data:
        content_parts.append(f"Auteur: {data['auteur']}")
    if "title" in data:
        content_parts.append(f"Title: {data['title']}")
    if "category" in data:
        content_parts.append(f"Category: {data['category']}")

    # Main content
    content = data.get("content", {})
    if content:
        flat = flatten_dict(content)
        for key, value in flat.items():
            if value and value != "None":
                content_parts.append(f"{key}: {value}")

    # VEO keywords
    if "veo_prompt_keywords" in data.get("content", {}):
        keywords = data["content"]["veo_prompt_keywords"]
        content_parts.append(f"VEO Keywords: {', '.join(keywords)}")

    return "\n".join(content_parts)


# =============================================================================
# 3D: Image Style, Visual Guide
# =============================================================================

def seed_3d_collection() -> int:
    """Seed 3D collection with cinematography and visual DNA data.

    Returns:
        Number of documents indexed
    """
    logger.info("\n🎨 Seeding 3D (Image Style, Visual Guide)...")
    rag = get_dimension_rag("3D")
    rag.ensure_collection()
    count = 0

    # Index cinematography techniques from all auteurs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Find cinematography files
        for json_file in auteur_dir.glob("*cinematography*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"3d_cinematography_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.3d.image",
                    "content_type": "cinematography",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "3D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Find visual DNA files
        for json_file in auteur_dir.glob("*visual_dna*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"3d_visual_dna_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.3d.image",
                    "content_type": "visual_dna",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "3D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Find lighting files
        for json_file in auteur_dir.glob("*lighting*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"3d_lighting_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.3d.image",
                    "content_type": "lighting",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "3D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    logger.info(f"  Total 3D documents: {count}")
    return count


# =============================================================================
# 4D: Analysis Framework, VDG
# =============================================================================

def seed_4d_collection() -> int:
    """Seed 4D collection with thematic analysis and quality criteria.

    Returns:
        Number of documents indexed
    """
    logger.info("\n📊 Seeding 4D (Analysis Framework, VDG)...")
    rag = get_dimension_rag("4D")
    rag.ensure_collection()
    count = 0

    # Index thematic analysis from auteurs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Find thematic analysis files
        for json_file in auteur_dir.glob("*thematic*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"4d_thematic_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "teaching.reference.analyze",
                    "content_type": "thematic_analysis",
                    "dataset_id": "film_analysis",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "4D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Find pacing/narrative files
        for json_file in auteur_dir.glob("*pacing*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"4d_pacing_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "teaching.reference.analyze",
                    "content_type": "pacing_narrative",
                    "dataset_id": "film_analysis",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "4D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    # Index quality criteria
    quality_path = RAG_DOCS_DIR / "quality" / "quality_criteria.json"
    if quality_path.exists():
        try:
            with open(quality_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Index main criteria
            criteria = data.get("criteria", {})
            for key, criterion in criteria.items():
                content = f"""
Quality Criterion: {criterion.get('name', key)}
Weight: {criterion.get('weight', 0)}
Description: {criterion.get('description', '')}

Sub-criteria:
"""
                for sub in criterion.get("sub_criteria", criterion.get("categories", {}).items() if isinstance(criterion.get("categories"), dict) else []):
                    if isinstance(sub, dict):
                        content += f"- {sub.get('name', '')}: {sub.get('description', '')}\n"
                    elif isinstance(sub, tuple):
                        content += f"- {sub[0]}: {sub[1]}\n"

                doc_id = f"4d_quality_{key}"
                metadata = {
                    "app_key": "teaching.reference.analyze",
                    "content_type": "quality_criteria",
                    "dataset_id": "film_analysis",
                    "criterion": key,
                    "source": "quality_criteria.json",
                    "dimension": "4D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ Quality: {criterion.get('name', key)}")
                    count += 1
        except Exception as e:
            logger.error(f"  ✗ Failed quality_criteria: {e}")

    logger.info(f"  Total 4D documents: {count}")
    return count


def seed_4d_bundle() -> int:
    """Seed full 4D stack (analysis + logic math vectors)."""
    total = 0
    total += seed_4d_collection()
    total += seed_logic_math_vectors()
    return total


# =============================================================================
# 4D: Logic Math Vectors (Gemini Video Analysis)
# =============================================================================

def seed_logic_math_vectors() -> int:
    """Seed logic_math vectors into 4D (Reference Analysis).

    These vectors represent quantitative scene logic extracted from video analysis.

    Returns:
        Number of documents indexed
    """
    logger.info("\n🧮 Seeding Logic Math Vectors (4D)...")
    rag = get_dimension_rag("4D")
    rag.ensure_collection()
    count = 0

    if not LOGIC_MATH_DIR.exists():
        logger.warning(f"  ⚠️ logic_math vectors not found at {LOGIC_MATH_DIR}")
        return 0

    for json_file in LOGIC_MATH_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            logic = data.get("logic_vector", {})
            metadata_info = data.get("metadata", {})

            camera = logic.get("camera_motion", {})
            composition = logic.get("composition", {})

            content = f"""
Logic Vector: {data.get('id', json_file.stem)}
Film: {metadata_info.get('film', '')} ({metadata_info.get('year', '')})
Scene: {metadata_info.get('scene', '')}
Duration: {metadata_info.get('duration_sec', '')} sec
Model: {metadata_info.get('model', '')} | FPS: {metadata_info.get('fps_sampled', '')}

Shot Length (ms):
- median: {logic.get('shot_length_ms', {}).get('median', '')}
- p25: {logic.get('shot_length_ms', {}).get('p25', '')}
- p75: {logic.get('shot_length_ms', {}).get('p75', '')}
- min/max: {logic.get('shot_length_ms', {}).get('min', '')}/{logic.get('shot_length_ms', {}).get('max', '')}

Cut Density: {logic.get('cut_density', '')}

Camera Motion:
- {', '.join(f"{k} {int(v*100)}%" for k, v in camera.items())}

Composition:
- {', '.join(f"{k} {int(v*100)}%" for k, v in composition.items())}

Color Entropy: {logic.get('color_entropy', '')}
Dominant Colors: {', '.join(logic.get('dominant_colors', []))}
Lighting Key: {logic.get('lighting_key', '')}
Aspect Ratio: {logic.get('aspect_ratio', '')}
Depth of Field: {logic.get('depth_of_field', '')}
Pacing Score: {logic.get('pacing_score', '')}

Tags: {', '.join(data.get('tags', []))}
            """.strip()

            doc_id = data.get("id", f"logic_{json_file.stem}")
            metadata = {
                "app_key": "teaching.reference.analyze",
                "content_type": data.get("content_type", "logic_vector"),
                "dataset_id": "video_ref",
                "auteur": data.get("auteur_key", ""),
                "film": metadata_info.get("film", ""),
                "year": metadata_info.get("year", ""),
                "scene": metadata_info.get("scene", ""),
                "source": json_file.name,
                "dimension": "4D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info(f"  ✓ Logic Vector: {json_file.name}")
                count += 1
        except Exception as e:
            logger.error(f"  ✗ Failed {json_file}: {e}")

    logger.info(f"  Total Logic Math documents: {count}")
    return count


# =============================================================================
# 5D: Video Generation, Camera Movement
# =============================================================================

def seed_5d_collection() -> int:
    """Seed 5D collection with VEO templates and camera movement data.

    Returns:
        Number of documents indexed
    """
    logger.info("\n🎬 Seeding 5D (Video Generation, Camera Movement)...")
    rag = get_dimension_rag("5D")
    rag.ensure_collection()
    count = 0

    # Index VEO prompt templates
    veo_path = RAG_DOCS_DIR / "origin" / "veo_prompt_templates.json"
    if veo_path.exists():
        try:
            with open(veo_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Index prompt structure
            structure = data.get("prompt_structure", {})
            components = structure.get("components", [])

            content = f"""
VEO Prompt Engineering Guide
Formula: {structure.get('formula', '')}

Components:
"""
            for comp in components:
                content += f"""
- {comp.get('name', '')} ({comp.get('priority', '')}): {comp.get('description', '')}
  Example: {comp.get('example', '')}
"""

            doc_id = "5d_veo_structure"
            metadata = {
                "app_key": "veo.video.generate",
                "content_type": "veo_structure",
                "source": "veo_prompt_templates.json",
                "dimension": "5D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info(f"  ✓ VEO: Prompt Structure")
                count += 1

            # Index templates
            templates = data.get("templates", {})
            for name, template in templates.items():
                content = f"""
VEO Template: {name}
Structure: {template.get('structure', '')}
Example: {template.get('example', '')}
"""
                doc_id = f"5d_veo_template_{name}"
                metadata = {
                    "app_key": "veo.video.generate",
                    "content_type": "veo_template",
                    "template_name": name,
                    "source": "veo_prompt_templates.json",
                    "dimension": "5D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ VEO Template: {name}")
                    count += 1

            # Index best practices
            practices = data.get("best_practices", [])
            content = "VEO Best Practices:\n\n"
            for p in practices:
                content += f"""
Practice: {p.get('practice', '')}
- Good: {p.get('good', '')}
- Bad: {p.get('bad', '')}
"""

            doc_id = "5d_veo_best_practices"
            metadata = {
                "app_key": "veo.video.generate",
                "content_type": "veo_best_practices",
                "source": "veo_prompt_templates.json",
                "dimension": "5D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info(f"  ✓ VEO: Best Practices")
                count += 1

        except Exception as e:
            logger.error(f"  ✗ Failed veo_prompt_templates: {e}")

    # Index camera movement from auteur packs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Check cinematography files for camera movement info
        for json_file in auteur_dir.glob("*cinematography*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content_data = data.get("content", {})
                camera_info = content_data.get("camera_movement_symbolism", content_data.get("camera_equipment", {}))

                if camera_info:
                    content = f"""
{data.get('auteur', auteur)} Camera Movement & Technique

"""
                    flat = flatten_dict(camera_info)
                    for key, value in flat.items():
                        if value and value != "None":
                            content += f"{key}: {value}\n"

                    # Add VEO keywords if present
                    keywords = content_data.get("veo_prompt_keywords", [])
                    if keywords:
                        content += f"\nVEO Keywords: {', '.join(keywords)}"

                    doc_id = f"5d_camera_{auteur}_{json_file.stem}"
                    metadata = {
                        "app_key": "veo.video.generate",
                        "content_type": "camera_movement",
                        "auteur": auteur,
                        "source": json_file.name,
                        "dimension": "5D",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info(f"  ✓ {auteur}: Camera Movement")
                        count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Index AI-specific files (temporal interpolation, volumetric texture)
        for json_file in auteur_dir.glob("*_ai*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"5d_ai_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "veo.video.generate",
                    "content_type": "ai_technique",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "5D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    # Index camera movement guidelines from rag_docs/veo/
    veo_camera_path = RAG_DOCS_DIR / "veo" / "veo_camera_movements.json"
    if veo_camera_path.exists():
        try:
            with open(veo_camera_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Index camera movements
            movements = data.get("camera_movements", {})
            for move_key, move_data in movements.items():
                keywords = move_data.get("prompt_keywords", [])
                content = f"""
Camera Movement: {move_key}
Keywords: {', '.join(keywords)}
Description: {move_data.get('description', '')}
Emotional Effect: {move_data.get('emotional_effect', '')}
Best For: {', '.join(move_data.get('best_for', []))}
"""
                doc_id = f"5d_camera_movement_{move_key}"
                metadata = {
                    "app_key": "veo.video.generate",
                    "content_type": "camera_movement_guide",
                    "movement_type": move_key,
                    "source": "veo_camera_movements.json",
                    "dimension": "5D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ VEO Camera: {move_key}")
                    count += 1

            # Index motion speeds
            speeds = data.get("motion_speeds", {})
            for speed_key, speed_data in speeds.items():
                keywords = speed_data.get("prompt_keywords", [])
                content = f"""
Motion Speed: {speed_key}
Keywords: {', '.join(keywords)}
Emotional Effect: {speed_data.get('emotional_effect', '')}
"""
                doc_id = f"5d_motion_speed_{speed_key}"
                metadata = {
                    "app_key": "veo.video.generate",
                    "content_type": "motion_speed",
                    "speed_type": speed_key,
                    "source": "veo_camera_movements.json",
                    "dimension": "5D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ VEO Speed: {speed_key}")
                    count += 1

            # Index VEO tips
            tips = data.get("veo_specific_tips", [])
            if tips:
                content = "VEO Camera Movement Tips:\n\n" + "\n".join(f"- {tip}" for tip in tips)
                doc_id = "5d_veo_camera_tips"
                metadata = {
                    "app_key": "veo.video.generate",
                    "content_type": "veo_tips",
                    "source": "veo_camera_movements.json",
                    "dimension": "5D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info("  ✓ VEO: Camera Tips")
                    count += 1

        except Exception as e:
            logger.error(f"  ✗ Failed veo_camera_movements: {e}")

    logger.info(f"  Total 5D documents: {count}")
    return count


# =============================================================================
# 6D: Sound/Music Design
# =============================================================================

def seed_6d_collection() -> int:
    """Seed 6D collection with sound design and music philosophy data.

    Returns:
        Number of documents indexed
    """
    logger.info("\n🎵 Seeding 6D (Sound/Music Design)...")
    rag = get_dimension_rag("6D")
    rag.ensure_collection()
    count = 0

    # Index sound design and music files from auteur packs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Find sound design files
        for json_file in auteur_dir.glob("*sound*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"6d_sound_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.6d.sound",
                    "content_type": "sound_design",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "6D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Find music philosophy files
        for json_file in auteur_dir.glob("*music*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"6d_music_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.6d.sound",
                    "content_type": "music_philosophy",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "6D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Find composer collaboration files
        for json_file in auteur_dir.glob("*composer*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content = extract_content_from_source_pack(data)
                doc_id = f"6d_composer_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.6d.sound",
                    "content_type": "composer_collaboration",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "6D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    # Index sound design principles from rag_docs/ambience/
    ambience_dir = RAG_DOCS_DIR / "ambience"
    if ambience_dir.exists():
        for json_file in ambience_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Index sound design layers
                sound_design = data.get("sound_design", {})
                layers = sound_design.get("layers", {})
                for layer_key, layer_data in layers.items():
                    examples = layer_data.get("examples", [])
                    content = f"""
Sound Layer: {layer_key}
Description: {layer_data.get('description', '')}
Examples: {', '.join(examples)}
"""
                    doc_id = f"6d_sound_layer_{layer_key}"
                    metadata = {
                        "app_key": "dimension.6d.sound",
                        "content_type": "sound_layer",
                        "layer_type": layer_key,
                        "source": json_file.name,
                        "dimension": "6D",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info(f"  ✓ Sound Layer: {layer_key}")
                        count += 1

                # Index sound functions
                functions = sound_design.get("functions", {})
                if functions:
                    content = "Sound Design Functions:\n\n"
                    for func_key, func_desc in functions.items():
                        content += f"- {func_key}: {func_desc}\n"

                    doc_id = "6d_sound_functions"
                    metadata = {
                        "app_key": "dimension.6d.sound",
                        "content_type": "sound_functions",
                        "source": json_file.name,
                        "dimension": "6D",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info("  ✓ Sound Functions")
                        count += 1

                # Index sound techniques
                techniques = sound_design.get("techniques", {})
                if techniques:
                    content = "Sound Design Techniques:\n\n"
                    for tech_key, tech_desc in techniques.items():
                        content += f"- {tech_key}: {tech_desc}\n"

                    doc_id = "6d_sound_techniques"
                    metadata = {
                        "app_key": "dimension.6d.sound",
                        "content_type": "sound_techniques",
                        "source": json_file.name,
                        "dimension": "6D",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info("  ✓ Sound Techniques")
                        count += 1

                # Index music genres
                genres = data.get("music_genres", {})
                for genre_key, genre_data in genres.items():
                    content = f"""
Music Genre: {genre_key}
Mood: {', '.join(genre_data.get('mood', []))}
Instruments: {', '.join(genre_data.get('instruments', []))}
Use Cases: {', '.join(genre_data.get('use_cases', []))}
"""
                    doc_id = f"6d_music_genre_{genre_key}"
                    metadata = {
                        "app_key": "dimension.6d.sound",
                        "content_type": "music_genre",
                        "genre": genre_key,
                        "source": json_file.name,
                        "dimension": "6D",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info(f"  ✓ Music Genre: {genre_key}")
                        count += 1

                # Index auteur sound signatures
                signatures = data.get("auteur_sound_signatures", {})
                for sig_key, sig_data in signatures.items():
                    content = f"""
Auteur Sound Signature: {sig_key}
Characteristics: {', '.join(sig_data.get('characteristics', []))}
Films: {', '.join(sig_data.get('films', []))}
"""
                    doc_id = f"6d_auteur_sound_{sig_key}"
                    metadata = {
                        "app_key": "dimension.6d.sound",
                        "content_type": "auteur_sound_signature",
                        "auteur": sig_key,
                        "source": json_file.name,
                        "dimension": "6D",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info(f"  ✓ Auteur Sound: {sig_key}")
                        count += 1

            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    logger.info(f"  Total 6D documents: {count}")
    return count


# =============================================================================
# AI: Persona Analysis, MBTI
# =============================================================================

def seed_ai_collection() -> int:
    """Seed AI collection with psychology and persona data.

    Returns:
        Number of documents indexed
    """
    logger.info("\n🧠 Seeding AI (Persona Analysis, MBTI)...")
    rag = get_dimension_rag("AI")
    rag.ensure_collection()
    count = 0

    # Index psychology data
    psych_dir = RAG_DOCS_DIR / "psychology"
    if psych_dir.exists():
        for json_file in psych_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle list of documents
                if isinstance(data, list):
                    for doc in data:
                        content = f"""
{doc.get('title', '')}

{doc.get('content', '')}
"""
                        doc_id = f"ai_psych_{doc.get('id', json_file.stem)}"
                        metadata = {
                            "app_key": "dimension.ai.persona",
                            "content_type": doc.get("dataset_id", "psychology"),
                            "dataset_tags": doc.get("dataset_tags", []),
                            "source": json_file.name,
                            "dimension": "AI",
                        }

                        if rag.index_document(doc_id, content, metadata):
                            logger.info(f"  ✓ Psychology: {doc.get('title', doc_id)[:50]}")
                            count += 1
                else:
                    # Handle single document
                    content = json.dumps(data, ensure_ascii=False, indent=2)
                    doc_id = f"ai_psych_{json_file.stem}"
                    metadata = {
                        "app_key": "dimension.ai.persona",
                        "content_type": "psychology",
                        "source": json_file.name,
                        "dimension": "AI",
                    }

                    if rag.index_document(doc_id, content, metadata):
                        logger.info(f"  ✓ Psychology: {json_file.name}")
                        count += 1

            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    # Index persona vectors from auteur packs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Find persona files in layer1
        layer1_dir = auteur_dir / "layer1_structured"
        if layer1_dir.exists():
            for json_file in layer1_dir.glob("*persona*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    persona = data.get("persona_vector", {})
                    if persona:
                        content = f"""
{data.get('auteur', auteur)} Persona Analysis

Tone: {', '.join(persona.get('tone', []))}
Interpretation Frame: {', '.join(persona.get('interpretation_frame', []))}

Emotion Arc:
"""
                        for e in persona.get("emotion_arc", []):
                            content += f"- t={e.get('t', 0)}: {e.get('label', '')} (valence {e.get('valence', 0)})\n"

                        tonal_shifts = persona.get("tonal_shifts", {})
                        if tonal_shifts:
                            content += "\nTonal Shifts:\n"
                            for k, v in tonal_shifts.items():
                                content += f"- {k}: {v}\n"

                        doc_id = f"ai_persona_{auteur}"
                        metadata = {
                            "app_key": "dimension.ai.persona",
                            "content_type": "persona_vector",
                            "auteur": auteur,
                            "source": json_file.name,
                            "dimension": "AI",
                        }

                        if rag.index_document(doc_id, content, metadata):
                            logger.info(f"  ✓ {auteur}: Persona Vector")
                            count += 1
                except Exception as e:
                    logger.error(f"  ✗ Failed {json_file}: {e}")

    logger.info(f"  Total AI documents: {count}")
    return count


# =============================================================================
# Verification
# =============================================================================

def verify_collections(dimensions: list[str] | None = None) -> dict[str, dict]:
    """Verify all dimension collections.

    Args:
        dimensions: List of dimensions to verify, or None for all

    Returns:
        Dict of dimension -> {count, sample_queries}
    """
    if dimensions is None:
        dimensions = ["3D", "4D", "5D", "6D", "AI"]

    results = {}

    for dim in dimensions:
        logger.info(f"\n📊 Verifying {dim} collection...")
        try:
            rag = get_dimension_rag(dim)
            stats = rag.get_collection_stats()

            if stats.get("available"):
                count = stats.get("points_count", 0)
                logger.info(f"  ✓ Documents: {count}")

                # Test search
                test_queries = {
                    "3D": "cinematography techniques composition",
                    "4D": "thematic analysis quality criteria",
                    "5D": "camera movement video generation",
                    "6D": "sound design music philosophy",
                    "AI": "MBTI personality persona",
                }

                query = test_queries.get(dim, "test")
                search_results = rag.search(query, limit=3, min_score=0.0)

                if search_results:
                    logger.info(f"  ✓ Search '{query[:30]}...' returned {len(search_results)} results")
                    for r in search_results[:2]:
                        logger.info(f"    - [{r['score']:.3f}] {r['doc_id'][:50]}")
                else:
                    logger.warning(f"  ✗ Search returned no results")

                results[dim] = {"count": count, "search_ok": len(search_results) > 0}
            else:
                logger.warning(f"  ✗ Collection unavailable: {stats.get('error', 'unknown')}")
                results[dim] = {"count": 0, "search_ok": False}

        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            results[dim] = {"count": 0, "search_ok": False, "error": str(e)}

    return results


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Seed all dimension RAG collections")
    parser.add_argument("--dimension", "-d", help="Seed only specific dimension (3D, 4D, 5D, 6D, AI)")
    parser.add_argument("--verify", "-v", action="store_true", help="Only verify existing data")
    args = parser.parse_args()

    logger.info("🚀 Dimension RAG Seeder - 2026 Edition")
    logger.info("=" * 60)

    # Verify only mode
    if args.verify:
        dims = [args.dimension] if args.dimension else None
        results = verify_collections(dims)

        logger.info("\n" + "=" * 60)
        logger.info("📈 Summary:")
        for dim, data in results.items():
            status = "✓" if data.get("search_ok") else "✗"
            logger.info(f"  {dim}: {data.get('count', 0)} docs {status}")
        return

    # Seed collections
    seeders = {
        "3D": seed_3d_collection,
        "4D": seed_4d_bundle,
        "5D": seed_5d_collection,
        "6D": seed_6d_collection,
        "AI": seed_ai_collection,
    }

    total_count = 0
    results = {}

    if args.dimension:
        if args.dimension not in seeders:
            logger.error(f"Invalid dimension: {args.dimension}. Valid: {list(seeders.keys())}")
            sys.exit(1)
        count = seeders[args.dimension]()
        results[args.dimension] = count
        total_count = count
    else:
        for dim, seeder in seeders.items():
            count = seeder()
            results[dim] = count
            total_count += count

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ Seeding Complete!")
    for dim, count in results.items():
        logger.info(f"  {dim}: {count} documents")
    logger.info(f"  Total: {total_count} documents")

    # Verify
    logger.info("\n" + "=" * 60)
    verify_collections(list(results.keys()))


if __name__ == "__main__":
    main()
