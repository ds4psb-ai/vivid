#!/usr/bin/env python3
"""Source Pack → Vertex AI RAG 동기화 스크립트.

Source Pack JSON 파일들을 Vertex AI RAG 코퍼스에 업로드하여
NotebookLM 의존성 없이 자체 RAG 시스템 구축.

Usage:
    # 전체 동기화
    python scripts/sync_source_packs_to_vertex.py
    
    # 특정 거장만
    python scripts/sync_source_packs_to_vertex.py --auteur bong
    
    # 드라이런 (실제 업로드 없음)
    python scripts/sync_source_packs_to_vertex.py --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path
SCRIPT_DIR = Path(__file__).parent.parent
BACKEND_DIR = SCRIPT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Source Pack 디렉토리
SOURCE_PACKS_DIR = SCRIPT_DIR / "data" / "source_packs"

# 거장별 코퍼스 매핑
AUTEUR_CORPUS_MAPPING = {
    "bong": "auteur_bong",
    "epoch": "auteur_epoch",
    "abyss": "auteur_abyss",
    "wong": "auteur_wong",
    "voltage": "auteur_voltage",
    "park": "auteur_park",
    "azure": "auteur_azure",
}


async def load_source_pack(file_path: Path) -> Optional[Dict[str, Any]]:
    """Source Pack JSON 파일 로드."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.warning(f"Failed to load {file_path}: {e}")
        return None


async def prepare_chunks_for_vertex(
    source_pack: Dict[str, Any],
    auteur_key: str,
    file_name: str,
) -> List[Dict[str, Any]]:
    """Source Pack 데이터를 Vertex AI 청크 형식으로 변환."""
    chunks = []
    
    # 제목과 설명 추출
    title = source_pack.get("title", file_name)
    description = source_pack.get("description", "")
    
    # 메타데이터 준비
    base_metadata = {
        "auteur": auteur_key,
        "source_file": file_name,
        "category": source_pack.get("category", "general"),
    }
    
    # 청크로 분할
    if "content" in source_pack:
        # 단일 콘텐츠
        chunks.append({
            "content": f"{title}\n\n{source_pack['content']}",
            "metadata": base_metadata,
        })
    
    if "sections" in source_pack:
        # 섹션별 분할
        for i, section in enumerate(source_pack["sections"]):
            section_title = section.get("title", f"Section {i+1}")
            section_content = section.get("content", "")
            chunks.append({
                "content": f"{title} - {section_title}\n\n{section_content}",
                "metadata": {**base_metadata, "section": section_title},
            })
    
    if "techniques" in source_pack:
        # 기법 목록
        for tech in source_pack["techniques"]:
            tech_name = tech.get("name", "Unknown")
            tech_desc = tech.get("description", "")
            tech_examples = tech.get("examples", [])
            
            content = f"{title} - {tech_name}\n\n{tech_desc}"
            if tech_examples:
                content += f"\n\nExamples:\n" + "\n".join(f"- {e}" for e in tech_examples[:5])
            
            chunks.append({
                "content": content,
                "metadata": {**base_metadata, "technique": tech_name},
            })
    
    if "shots" in source_pack:
        # 샷 분석 (layer0)
        for shot in source_pack.get("shots", [])[:20]:  # 최대 20개
            shot_desc = shot.get("description", "")
            shot_analysis = shot.get("analysis", "")
            chunks.append({
                "content": f"{title} - Shot Analysis\n\n{shot_desc}\n\n{shot_analysis}",
                "metadata": {**base_metadata, "type": "shot_analysis"},
            })
    
    return chunks


async def upload_to_vertex_rag(
    chunks: List[Dict[str, Any]],
    corpus_name: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """청크를 Vertex AI RAG 코퍼스에 업로드."""
    if dry_run:
        logger.info(f"[DRY-RUN] Would upload {len(chunks)} chunks to {corpus_name}")
        return {"uploaded": 0, "status": "dry_run"}
    
    try:
        from app.rag.tier0_vertex_rag import get_vertex_rag_service
        
        service = get_vertex_rag_service()
        
        # 청크 업로드
        uploaded = 0
        for chunk in chunks:
            try:
                await service.add_text_chunk(
                    corpus_name=corpus_name,
                    content=chunk["content"],
                    metadata=chunk["metadata"],
                )
                uploaded += 1
            except Exception as e:
                logger.warning(f"Failed to upload chunk: {e}")
        
        return {"uploaded": uploaded, "status": "success"}
        
    except ImportError:
        logger.error("Vertex RAG service not available")
        return {"uploaded": 0, "status": "error", "error": "service_unavailable"}


async def sync_auteur(
    auteur_key: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """특정 거장의 Source Pack 동기화."""
    auteur_dir = SOURCE_PACKS_DIR / auteur_key
    
    if not auteur_dir.exists():
        logger.warning(f"Auteur directory not found: {auteur_dir}")
        return {"auteur": auteur_key, "status": "not_found"}
    
    corpus_name = AUTEUR_CORPUS_MAPPING.get(auteur_key, f"auteur_{auteur_key}")
    
    total_chunks = 0
    total_files = 0
    
    for json_file in auteur_dir.glob("*.json"):
        # layer0, layer1 등 제외
        if any(x in str(json_file) for x in ["layer0", "layer1", "layer2", "layer3"]):
            continue
        
        logger.info(f"Processing: {json_file.name}")
        
        source_pack = await load_source_pack(json_file)
        if not source_pack:
            continue
        
        chunks = await prepare_chunks_for_vertex(
            source_pack, auteur_key, json_file.stem
        )
        
        if chunks:
            result = await upload_to_vertex_rag(chunks, corpus_name, dry_run)
            total_chunks += result.get("uploaded", 0)
            total_files += 1
    
    logger.info(f"[{auteur_key}] Synced {total_files} files, {total_chunks} chunks")
    
    return {
        "auteur": auteur_key,
        "files": total_files,
        "chunks": total_chunks,
        "corpus": corpus_name,
        "status": "success",
    }


async def sync_all(dry_run: bool = False) -> List[Dict[str, Any]]:
    """모든 거장 Source Pack 동기화."""
    results = []
    
    for auteur_key in AUTEUR_CORPUS_MAPPING.keys():
        result = await sync_auteur(auteur_key, dry_run)
        results.append(result)
    
    return results


async def main():
    parser = argparse.ArgumentParser(description="Sync Source Packs to Vertex AI RAG")
    parser.add_argument("--auteur", help="Specific auteur to sync (e.g., bong)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload")
    parser.add_argument("--list", action="store_true", help="List available Source Packs")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Source Pack → Vertex AI RAG Sync")
    logger.info("=" * 60)
    
    if args.list:
        # Source Pack 목록 출력
        for auteur_dir in sorted(SOURCE_PACKS_DIR.iterdir()):
            if auteur_dir.is_dir():
                json_files = list(auteur_dir.glob("*.json"))
                print(f"{auteur_dir.name}: {len(json_files)} files")
        return
    
    if args.auteur:
        result = await sync_auteur(args.auteur, args.dry_run)
        print(json.dumps(result, indent=2))
    else:
        results = await sync_all(args.dry_run)
        print(json.dumps(results, indent=2))
    
    logger.info("Sync complete!")


if __name__ == "__main__":
    asyncio.run(main())
