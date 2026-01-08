import json
import os
import glob
from pathlib import Path

def convert_json_to_markdown(json_path, output_dir):
    """
    Converts a Vivid JSON source pack into a formatted Markdown document
    optimized for NotebookLM ingestion.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return

    # Extract metadata
    title = data.get("title", "Untitled Document")
    auteur = data.get("auteur", "Unknown Auteur")
    category = data.get("category", "General")
    version = data.get("version", "1.0")
    source_id = data.get("source_id", "unknown_id")

    # Start building Markdown content
    md_lines = []
    
    # Header
    md_lines.append(f"# {title}")
    md_lines.append(f"**Auteur:** {auteur} | **Category:** {category} | **ID:** {source_id}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Process Content keys
    content = data.get("content", {})
    
    # Helper to process nested dictionaries recursively or flatten lists
    def process_content_value(value, level=2):
        text_lines = []
        if isinstance(value, dict):
            for k, v in value.items():
                # Format key as header
                header_prefix = "#" * level
                clean_key = k.replace("_", " ").title()
                text_lines.append(f"{header_prefix} {clean_key}")
                text_lines.append("")
                text_lines.extend(process_content_value(v, level + 1))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                     text_lines.extend(process_content_value(item, level))
                else:
                    text_lines.append(f"- {item}")
            text_lines.append("")
        elif isinstance(value, str):
            text_lines.append(value)
            text_lines.append("")
        elif isinstance(value, (int, float, bool)):
            text_lines.append(str(value))
            text_lines.append("")
        return text_lines

    # Special handling for specific top-level keys to ensure logical flow
    # 1. Main Content Areas
    for key, value in content.items():
        if key == "veo_prompt_keywords": 
            continue # Process this last or separately
        
        # Determine Header Level
        # Top level content keys get H2
        clean_key = key.replace("_", " ").title()
        md_lines.append(f"## {clean_key}")
        md_lines.append("")
        md_lines.extend(process_content_value(value, level=3))
        md_lines.append("")

    # 2. VEO Prompt Keywords (Important for RAG retrieval context)
    if "veo_prompt_keywords" in content:
        md_lines.append("## VEO Prompt Keywords")
        md_lines.append("> Use these keywords to generate video style prompts.")
        md_lines.append("")
        
        keywords = content["veo_prompt_keywords"]
        if isinstance(keywords, list):
            for k in keywords:
                md_lines.append(f"- {k}")
        else:
            md_lines.append(str(keywords))
        md_lines.append("")

    # 3. Sources Section (at the bottom)
    sources = data.get("sources", [])
    if sources:
        md_lines.append("---")
        md_lines.append("## References & Sources")
        for source in sources:
            name = source.get("name", "Unknown")
            topic = source.get("topic", "General")
            md_lines.append(f"- **{name}**: {topic}")

    # Write to output file
    output_subdir = os.path.join(output_dir, auteur.lower().replace(" ", "_"))
    os.makedirs(output_subdir, exist_ok=True)
    
    output_filename = f"{Path(json_path).stem}.md"
    output_path = os.path.join(output_subdir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    
    print(f"Converted: {output_path}")

def main():
    base_dir = "/Users/ted/vivid/data/source_packs"
    output_dir = "/Users/ted/vivid/data/source_packs_converted"
    
    # Get all JSON files in subdirectories
    json_files = glob.glob(os.path.join(base_dir, "*", "*.json"))
    
    print(f"Found {len(json_files)} JSON source packs.")
    
    for json_file in json_files:
        convert_json_to_markdown(json_file, output_dir)
        
    print(f"\nAll files converted. Output directory: {output_dir}")

if __name__ == "__main__":
    main()
