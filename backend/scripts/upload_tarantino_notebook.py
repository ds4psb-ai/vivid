#!/usr/bin/env python3
"""
Tarantino NotebookLM Upload Automation

Day 3: Uploads 11 Tarantino source packs to NotebookLM
using the Playwright automation infrastructure.

Prerequisites:
1. Chrome with --remote-debugging-port=9223
2. Logged into NotebookLM in Chrome

Usage:
    python backend/scripts/upload_tarantino_notebook.py

Output:
    - Creates NotebookLM notebook "Quentin Tarantino Source Packs 2026"
    - Uploads 11 source markdown files
    - Prints notebook_id for NOTEBOOK_REGISTRY update
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logging_config import get_logger

logger = get_logger("tarantino_upload")

# Source files to upload
TARANTINO_SOURCES = [
    "01_tarantino_visual_dna.md",
    "02_tarantino_cinematography_techniques.md",
    "03_tarantino_editing_narrative.md",
    "04_tarantino_violence_aesthetics.md",
    "05_tarantino_music_needle_drop.md",
    "06_tarantino_dialogue_style.md",
    "07_tarantino_chapter_structure.md",
    "08_tarantino_reservoir_dogs.md",
    "09_tarantino_visual_motifs.md",
    "10_tarantino_actor_ensemble.md",
    "11_tarantino_kinetic_motion_ai.md",
]

SOURCE_DIR = Path(__file__).parent.parent.parent / "data" / "notebooklm_ready" / "tarantino"


async def upload_tarantino_notebook():
    """Create Tarantino notebook and upload all 11 sources."""
    
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
    
    missing = [f for f in TARANTINO_SOURCES if not (SOURCE_DIR / f).exists()]
    if missing:
        logger.error(f"Missing source files: {missing}")
        print(f"❌ Missing files: {missing}")
        return None
    
    print(f"✓ Found {len(TARANTINO_SOURCES)} source files in {SOURCE_DIR}")
    
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
        print("\n🔄 Creating Tarantino notebook...")
        notebook_id = await client.create_notebook("Quentin Tarantino Source Packs 2026")
        print(f"✓ Created notebook: {notebook_id}")
        
        # Step 2: Upload sources one by one
        print(f"\n🔄 Uploading {len(TARANTINO_SOURCES)} sources...")
        uploaded = []
        
        for i, filename in enumerate(TARANTINO_SOURCES, 1):
            filepath = SOURCE_DIR / filename
            content = filepath.read_text(encoding="utf-8")
            title = filename.replace(".md", "").replace("_", " ").title()
            
            print(f"  [{i}/{len(TARANTINO_SOURCES)}] Uploading: {title}")
            
            try:
                source_id = await client.add_text_source(notebook_id, title, content)
                uploaded.append({"title": title, "source_id": source_id})
                print(f"      ✓ Source ID: {source_id or 'ui_added'}")
                
                # Wait between uploads to avoid rate limiting
                if i < len(TARANTINO_SOURCES):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.warning(f"Failed to upload {filename}: {e}")
                print(f"      ⚠ Failed: {e}")
        
        # Step 3: Summary
        print(f"\n{'='*60}")
        print("📊 UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Notebook ID: {notebook_id}")
        print(f"Sources Uploaded: {len(uploaded)}/{len(TARANTINO_SOURCES)}")
        print(f"\n{'='*60}")
        print("📝 REGISTRY UPDATE (copy to tier0_notebooklm.py)")
        print(f"{'='*60}")
        print(f'''
    "DNA_쿠엔틴타란티노": {{
        "notebook_id": "{notebook_id}",
        "display_name": "Quentin Tarantino Source Packs 2026",
        "dimension": "AD",
        "category": "auteur",
        "description": "쿠엔틴 타란티노의 트렁크 샷, 대화 중심, 그라인드하우스 미학",
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
    print("🎬 Tarantino NotebookLM Upload Automation")
    print("="*60)
    
    notebook_id = await upload_tarantino_notebook()
    
    if notebook_id:
        print(f"\n✅ SUCCESS! Notebook ID: {notebook_id}")
        print("\nNext steps:")
        print("1. Update NOTEBOOK_REGISTRY in tier0_notebooklm.py")
        print("2. Test query: hybrid_query('타란티노 트렁크 샷', auteur_key='tarantino')")
        return 0
    else:
        print("\n❌ FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
