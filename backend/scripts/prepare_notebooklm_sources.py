#!/usr/bin/env python3
"""
NotebookLM 대규모 소스 업로드 준비 스크립트
600개 소스 용량을 최대한 활용하기 위해 데이터를 개별 청크로 분리
"""
import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "notebooklm_sources"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_json(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거"""
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']:
        name = name.replace(char, '_')
    return name

def save_source(filename: str, content: dict | str, category: str):
    """소스를 개별 파일로 저장"""
    category_dir = OUTPUT_DIR / category
    category_dir.mkdir(exist_ok=True)
    
    if isinstance(content, dict):
        text = json.dumps(content, ensure_ascii=False, indent=2)
    else:
        text = content
    
    with open(category_dir / filename, "w", encoding="utf-8") as f:
        f.write(text)
    
    return str(category_dir / filename)

def chunk_video_segments():
    """비디오 세그먼트를 개별 소스로 분리"""
    segments = load_json(DATA_DIR / "bong_video_segments.json")
    sources = []
    
    for seg in segments:
        filename = f"{seg['segment_id']}.json"
        
        # 풍부한 컨텍스트 추가
        enriched = {
            **seg,
            "_source_type": "video_segment",
            "_cluster_id": "CL_BONG_01",
            "_description": f"봉준호 - {seg.get('source_id', '')} - {seg.get('scene_id', '')}",
        }
        
        path = save_source(filename, enriched, "video_segments")
        sources.append(path)
    
    print(f"✅ Video Segments: {len(sources)}개")
    return sources

def chunk_derived_insights():
    """파생 인사이트를 개별 소스로 분리"""
    insights = load_json(DATA_DIR / "bong_derived_insights.json")
    sources = []
    
    for i, insight in enumerate(insights):
        guide_type = insight.get("guide_type", "report")
        source_id = insight.get("source_id", f"insight_{i}")
        filename = f"{source_id}_{guide_type}.json"
        
        enriched = {
            **insight,
            "_source_type": "derived_insight",
            "_cluster_id": "CL_BONG_01",
        }
        
        path = save_source(filename, enriched, "derived_insights")
        sources.append(path)
        
        # 추가: 각 비트 개별 소스
        if "beats" in insight:
            for beat in insight["beats"]:
                beat_filename = f"{source_id}_beat_{beat['beat_id']}.json"
                beat_enriched = {
                    "source_id": source_id,
                    "beat": beat,
                    "_source_type": "beat_detail",
                    "_cluster_id": "CL_BONG_01",
                }
                path = save_source(beat_filename, beat_enriched, "beats")
                sources.append(path)
        
        # 추가: 각 샷 개별 소스 (스토리보드)
        if "shots" in insight:
            for shot in insight["shots"]:
                shot_filename = f"{source_id}_shot_{shot['shot_number']}.json"
                shot_enriched = {
                    "source_id": source_id,
                    "shot": shot,
                    "_source_type": "shot_detail",
                    "_cluster_id": "CL_BONG_01",
                }
                path = save_source(shot_filename, shot_enriched, "shots")
                sources.append(path)
    
    print(f"✅ Derived Insights: {len(sources)}개")
    return sources

def chunk_patterns():
    """패턴을 개별 소스로 분리"""
    patterns = load_json(DATA_DIR / "bong_pattern_candidates.json")
    sources = []
    
    for i, pattern in enumerate(patterns):
        safe_name = sanitize_filename(pattern['pattern_name'])
        filename = f"pattern_{safe_name}.json"
        
        enriched = {
            **pattern,
            "_source_type": "pattern_candidate",
            "_cluster_id": "CL_BONG_01",
        }
        
        path = save_source(filename, enriched, "patterns")
        sources.append(path)
    
    print(f"✅ Patterns: {len(sources)}개")
    return sources

def chunk_ideal_guides():
    """Ideal 가이드를 개별 소스로 분리"""
    ideal_dir = DATA_DIR / "ideal"
    sources = []
    
    for json_file in ideal_dir.glob("bong_*.json"):
        data = load_json(json_file)
        
        enriched = {
            **data,
            "_source_type": "ideal_guide",
            "_cluster_id": "CL_BONG_01",
        }
        
        path = save_source(json_file.name, enriched, "ideal_guides")
        sources.append(path)
        
        # 세부 항목 분리
        if "thematic_obsessions" in data:
            for obsession in data["thematic_obsessions"]:
                safe_name = sanitize_filename(obsession['theme'])
                filename = f"obsession_{safe_name}.json"
                path = save_source(filename, {
                    "auteur": data.get("auteur"),
                    "obsession": obsession,
                    "_source_type": "thematic_obsession",
                }, "obsessions")
                sources.append(path)
        
        if "signature_techniques" in data:
            # Visual techniques
            for tech in data["signature_techniques"].get("visual", []):
                safe_name = sanitize_filename(tech['name'])
                filename = f"tech_visual_{safe_name}.json"
                path = save_source(filename, {
                    "auteur": data.get("auteur"),
                    "technique": tech,
                    "category": "visual",
                    "_source_type": "signature_technique",
                }, "techniques")
                sources.append(path)
            
            # Narrative techniques
            for tech in data["signature_techniques"].get("narrative", []):
                safe_name = sanitize_filename(tech['name'])
                filename = f"tech_narrative_{safe_name}.json"
                path = save_source(filename, {
                    "auteur": data.get("auteur"),
                    "technique": tech,
                    "category": "narrative",
                    "_source_type": "signature_technique",
                }, "techniques")
                sources.append(path)
    
    print(f"✅ Ideal Guides: {len(sources)}개")
    return sources

def chunk_raw_assets():
    """Raw Assets를 개별 소스로 분리"""
    assets = load_json(DATA_DIR / "bong_raw_assets.json")
    sources = []
    
    for asset in assets:
        filename = f"asset_{asset['source_id']}.json"
        
        enriched = {
            **asset,
            "_source_type": "raw_asset",
            "_cluster_id": "CL_BONG_01",
        }
        
        path = save_source(filename, enriched, "raw_assets")
        sources.append(path)
    
    print(f"✅ Raw Assets: {len(sources)}개")
    return sources

def chunk_existing_derived():
    """이미 추출된 derived 데이터도 소스로 추가"""
    derived_dir = DATA_DIR / "derived" / "bong"
    sources = []
    
    if derived_dir.exists():
        for json_file in derived_dir.glob("*.json"):
            data = load_json(json_file)
            
            enriched = {
                **data,
                "_source_type": "extracted_knowledge",
                "_extracted_from": "NotebookLM",
            }
            
            path = save_source(f"extracted_{json_file.name}", enriched, "extracted")
            sources.append(path)
    
    print(f"✅ Extracted Knowledge: {len(sources)}개")
    return sources

def create_manifest(all_sources: list):
    """업로드 매니페스트 생성"""
    manifest = {
        "created_at": datetime.now().isoformat(),
        "cluster_id": "CL_BONG_01",
        "director": "봉준호",
        "total_sources": len(all_sources),
        "sources_by_category": {},
        "files": []
    }
    
    for path in all_sources:
        path_obj = Path(path)
        category = path_obj.parent.name
        
        if category not in manifest["sources_by_category"]:
            manifest["sources_by_category"][category] = 0
        manifest["sources_by_category"][category] += 1
        
        manifest["files"].append({
            "path": path,
            "category": category,
            "filename": path_obj.name
        })
    
    with open(OUTPUT_DIR / "upload_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 Manifest saved: {OUTPUT_DIR / 'upload_manifest.json'}")
    return manifest

def main():
    print("=" * 60)
    print("NotebookLM 대규모 소스 준비")
    print("=" * 60)
    
    all_sources = []
    
    # 1. Video Segments
    all_sources.extend(chunk_video_segments())
    
    # 2. Derived Insights (+ beats, shots)
    all_sources.extend(chunk_derived_insights())
    
    # 3. Patterns
    all_sources.extend(chunk_patterns())
    
    # 4. Ideal Guides (+ obsessions, techniques)
    all_sources.extend(chunk_ideal_guides())
    
    # 5. Raw Assets
    all_sources.extend(chunk_raw_assets())
    
    # 6. Already extracted
    all_sources.extend(chunk_existing_derived())
    
    # Create manifest
    manifest = create_manifest(all_sources)
    
    print("=" * 60)
    print(f"📊 총 소스 수: {len(all_sources)}개")
    print(f"📁 카테고리별:")
    for cat, count in manifest["sources_by_category"].items():
        print(f"   - {cat}: {count}개")
    print("=" * 60)
    print(f"\n✅ 모든 소스가 {OUTPUT_DIR}에 준비되었습니다.")
    print("NotebookLM에 수동으로 업로드하거나 API를 사용하세요.")

if __name__ == "__main__":
    main()
