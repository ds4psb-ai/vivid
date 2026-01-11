#!/usr/bin/env python3
"""
Park Chan-wook NotebookLM Upload Automation

P4 Commit 1: Uploads Park Chan-wook source packs to NotebookLM
using the Playwright automation infrastructure.

Prerequisites:
1. Chrome with --remote-debugging-port=9223
2. Logged into NotebookLM in Chrome

Usage:
    python backend/scripts/upload_park_notebook.py

Output:
    - Creates NotebookLM notebook "박찬욱 Source Packs 2026"
    - Uploads 3 source files (JSON → Markdown conversion)
    - Prints notebook_id for NOTEBOOK_REGISTRY update
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logging_config import get_logger

logger = get_logger("park_upload")

# Source pack directory
SOURCE_DIR = Path(__file__).parent.parent.parent / "data" / "source_packs" / "park"


def convert_layer0_to_markdown(json_data: dict) -> str:
    """Convert Layer 0 shot analysis JSON to readable markdown."""
    lines = [
        f"# {json_data.get('auteur', '박찬욱')} - 샷 분석 (Layer 0)",
        "",
        f"> {json_data.get('description', '')}",
        "",
        "---",
        "",
    ]
    
    for chunk in json_data.get("chunks", []):
        meta = chunk.get("metadata", {})
        content = chunk.get("content", {})
        visual = content.get("visual_schema", {})
        audio = content.get("audio_schema", {})
        
        lines.append(f"## {meta.get('film_title', 'Unknown')} ({meta.get('film_year', '')})")
        lines.append("")
        lines.append(f"**Scene**: {meta.get('scene_range', 'N/A')} | **Phase**: {meta.get('temporal_phase', 'N/A')}")
        lines.append("")
        lines.append(f"> {content.get('transcript', '')}")
        lines.append("")
        lines.append("### Visual Schema")
        lines.append(f"- **Composition**: {visual.get('composition', 'N/A')}")
        lines.append(f"- **Lighting**: {visual.get('lighting', 'N/A')}")
        lines.append(f"- **Camera Motion**: {visual.get('camera_motion', 'N/A')}")
        lines.append(f"- **Blocking**: {visual.get('blocking', 'N/A')}")
        lines.append(f"- **Pacing**: {visual.get('pacing', 'N/A')}")
        if visual.get("color_palette"):
            colors = ", ".join(visual["color_palette"])
            lines.append(f"- **Palette**: {colors}")
        lines.append("")
        lines.append("### Audio Schema")
        lines.append(f"- **Sound Design**: {audio.get('sound_design', 'N/A')}")
        lines.append(f"- **Music Mood**: {audio.get('music_mood', 'N/A')}")
        lines.append("")
        if content.get("motifs"):
            motifs = ", ".join(content["motifs"])
            lines.append(f"**Motifs**: {motifs}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def convert_layer1_to_markdown(json_data: dict) -> str:
    """Convert Layer 1 logic/persona vectors JSON to readable markdown."""
    lines = [
        f"# {json_data.get('auteur', '박찬욱')} - Visual DNA (Layer 1)",
        "",
        f"> {json_data.get('description', '')}",
        "",
        "---",
        "",
    ]
    
    # Logic Vector
    logic = json_data.get("logic_vector", {})
    lines.append("## Cadence (편집 리듬)")
    cadence = logic.get("cadence", {})
    shot_length = cadence.get("shot_length_ms", {})
    lines.append(f"- **Median Shot Length**: {shot_length.get('median', 'N/A')}ms - {shot_length.get('signature', '')}")
    transitions = cadence.get("transition_types", {})
    for t_type, ratio in transitions.items():
        lines.append(f"- **{t_type}**: {int(ratio * 100)}%")
    lines.append("")
    
    # Composition
    lines.append("## Composition (구도)")
    comp = logic.get("composition", {})
    lines.append(f"- **Primary Strategy**: {comp.get('primary_strategy', 'N/A')}")
    lines.append(f"- **Symmetry Score**: {comp.get('symmetry_score', 'N/A')}")
    lines.append(f"- **Depth Usage**: {comp.get('depth_usage', 'N/A')}")
    if comp.get("signature_compositions"):
        lines.append(f"- **Signatures**: {', '.join(comp['signature_compositions'])}")
    lines.append("")
    
    # Camera Motion
    lines.append("## Camera Motion")
    cam = logic.get("camera_motion", {})
    for motion, ratio in cam.items():
        if motion != "signature":
            lines.append(f"- **{motion}**: {int(ratio * 100) if isinstance(ratio, float) else ratio}%")
    if cam.get("signature"):
        lines.append(f"- **Signature**: {cam['signature']}")
    lines.append("")
    
    # Rendering Specs
    lines.append("## Rendering Specs")
    render = logic.get("rendering_specs", {})
    lines.append(f"- **Lens**: {render.get('lens', 'N/A')}")
    lines.append(f"- **Film Stock**: {render.get('film_stock', 'N/A')}")
    lines.append(f"- **Color Process**: {render.get('color_process', 'N/A')}")
    lines.append(f"- **Lighting Style**: {render.get('lighting_style', 'N/A')}")
    if render.get("texture_prompts"):
        lines.append(f"- **Textures**: {', '.join(render['texture_prompts'])}")
    lines.append("")
    
    # Persona Vector
    persona = json_data.get("persona_vector", {})
    lines.append("---")
    lines.append("")
    lines.append("## Persona (페르소나)")
    if persona.get("tone"):
        lines.append(f"**Tone**: {', '.join(persona['tone'])}")
    lines.append("")
    lines.append("### Emotion Arc")
    for point in persona.get("emotion_arc", []):
        lines.append(f"- **t={point.get('t')}**: {point.get('label')} (valence: {point.get('valence')})")
    lines.append("")
    if persona.get("interpretation_frame"):
        lines.append(f"**Interpretation Frame**: {', '.join(persona['interpretation_frame'])}")
    lines.append("")
    
    # Pattern Rules
    patterns = json_data.get("pattern_rules", [])
    if patterns:
        lines.append("---")
        lines.append("")
        lines.append("## Pattern Rules (패턴 규칙)")
        for pattern in patterns:
            lines.append(f"### {pattern.get('name', 'Unknown')}")
            lines.append(f"{pattern.get('description', '')}")
            lines.append(f"- **When**: {pattern.get('application_condition', 'N/A')}")
            lines.append("")
    
    return "\n".join(lines)


async def upload_park_notebook():
    """Create Park Chan-wook notebook and upload all sources."""
    
    # Import Playwright client
    try:
        from app.rag.notebooklm_playwright import PlaywrightNotebookLMClient
    except ImportError as e:
        logger.error(f"Playwright not available: {e}")
        print("❌ Playwright not installed. Run: pip install playwright")
        return None
    
    # Verify source files exist
    if not SOURCE_DIR.exists():
        logger.error(f"Source directory not found: {SOURCE_DIR}")
        print(f"❌ Source directory not found: {SOURCE_DIR}")
        return None
    
    # Load and convert sources
    sources = []
    
    # Layer 0: Shot Analysis
    layer0_path = SOURCE_DIR / "layer0_raw" / "shot_analysis_chunks.json"
    if layer0_path.exists():
        with open(layer0_path, encoding="utf-8") as f:
            layer0_data = json.load(f)
        sources.append({
            "title": "Layer 0 - Shot Analysis",
            "content": convert_layer0_to_markdown(layer0_data)
        })
        print(f"✓ Loaded Layer 0: {layer0_path.name}")
    
    # Layer 1: Logic/Persona Vectors
    layer1_path = SOURCE_DIR / "layer1_structured" / "logic_persona_vectors.json"
    if layer1_path.exists():
        with open(layer1_path, encoding="utf-8") as f:
            layer1_data = json.load(f)
        sources.append({
            "title": "Layer 1 - Visual DNA",
            "content": convert_layer1_to_markdown(layer1_data)
        })
        print(f"✓ Loaded Layer 1: {layer1_path.name}")
    
    # Layer 2: Variation Guide (already markdown)
    layer2_path = SOURCE_DIR / "layer2_synthesized" / "variation_guide_ko.md"
    if layer2_path.exists():
        sources.append({
            "title": "Layer 2 - Style Variation Guide",
            "content": layer2_path.read_text(encoding="utf-8")
        })
        print(f"✓ Loaded Layer 2: {layer2_path.name}")
    
    if not sources:
        print("❌ No source files found")
        return None
    
    print(f"\n✓ Prepared {len(sources)} sources for upload")
    
    # Connect to Chrome via CDP
    print("\n🔄 Connecting to Chrome (CDP port 9223)...")
    
    try:
        client = PlaywrightNotebookLMClient(cdp_port=9223)
        await client.connect()
        print("✓ Connected to Chrome")
    except Exception as e:
        logger.error(f"CDP connection failed: {e}")
        print(f"""
❌ Cannot connect to Chrome. Please:
1. Close Chrome completely
2. Run: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
      --remote-debugging-port=9223 --user-data-dir=/tmp/chrome-debug-9223
3. Login to NotebookLM at https://notebooklm.google.com/
4. Re-run this script
""")
        return None
    
    try:
        # Step 1: Create notebook
        print("\n🔄 Creating 박찬욱 notebook...")
        notebook_id = await client.create_notebook("박찬욱 Source Packs 2026")
        print(f"✓ Created notebook: {notebook_id}")
        
        # Step 2: Upload sources one by one
        print(f"\n🔄 Uploading {len(sources)} sources...")
        uploaded = []
        
        for i, source in enumerate(sources, 1):
            title = source["title"]
            content = source["content"]
            
            print(f"  [{i}/{len(sources)}] Uploading: {title}")
            
            try:
                source_id = await client.add_text_source(notebook_id, title, content)
                uploaded.append({"title": title, "source_id": source_id})
                print(f"      ✓ Source ID: {source_id or 'ui_added'}")
                
                # Wait between uploads to avoid rate limiting
                if i < len(sources):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.warning(f"Failed to upload {title}: {e}")
                print(f"      ⚠ Failed: {e}")
        
        # Step 3: Summary
        print(f"\n{'='*60}")
        print("📊 UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Notebook ID: {notebook_id}")
        print(f"Sources Uploaded: {len(uploaded)}/{len(sources)}")
        print(f"\n{'='*60}")
        print("📝 REGISTRY UPDATE (copy to tier0_notebooklm.py)")
        print(f"{'='*60}")
        print(f'''
    "DNA_박찬욱": {{
        "notebook_id": "{notebook_id}",
        "display_name": "박찬욱 Source Packs 2026",
        "dimension": "AD",
        "category": "auteur",
        "description": "박찬욱 감독의 대칭 구도, 강렬한 색채, 정밀한 프레이밍",
        "source_count": {len(uploaded)},
    }},
''')
        
        return notebook_id
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await client.close()
        print("\n✓ Closed Chrome connection")


async def main():
    print("="*60)
    print("🎬 박찬욱 NotebookLM Upload Automation")
    print("="*60)
    
    notebook_id = await upload_park_notebook()
    
    if notebook_id:
        print(f"\n✅ SUCCESS! Notebook ID: {notebook_id}")
        print("\nNext steps:")
        print("1. Update NOTEBOOK_REGISTRY in tier0_notebooklm.py")
        print("2. Test query: hybrid_query('박찬욱 대칭 구도', auteur_key='park')")
        return 0
    else:
        print("\n❌ FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
