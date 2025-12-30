"""
NotebookLM Enterprise API 업로드 스크립트

사전 요구 사항:
1. Google Cloud 프로젝트 생성
2. NotebookLM API 활성화
3. 서비스 계정 생성 및 키 다운로드
4. 환경 변수: GOOGLE_APPLICATION_CREDENTIALS

사용법:
    python notebooklm_upload.py --project-id YOUR_PROJECT_ID
"""

import os
import json
import argparse
from pathlib import Path

# Google Cloud 클라이언트는 환경에 따라 설치 필요
# pip install google-cloud-notebooklm (Enterprise API 클라이언트)

# 현재 Enterprise API가 공개됐지만 클라이언트 라이브러리가 
# 아직 공식 PyPI에 없을 수 있음. REST API 직접 호출 필요할 수 있음.

SOURCE_PACK_DIR = Path(__file__).parent.parent.parent / "data" / "source_packs" / "bong"


def load_layer_files():
    """Load all layer files from the source pack directory."""
    layers = {}
    
    # Layer 0: Raw evidence
    layer0_path = SOURCE_PACK_DIR / "layer0_raw" / "shot_analysis_chunks.json"
    if layer0_path.exists():
        with open(layer0_path, "r", encoding="utf-8") as f:
            layers["layer0_raw"] = json.load(f)
    
    # Layer 1: Structured knowledge
    layer1_path = SOURCE_PACK_DIR / "layer1_structured" / "logic_persona_vectors.json"
    if layer1_path.exists():
        with open(layer1_path, "r", encoding="utf-8") as f:
            layers["layer1_structured"] = json.load(f)
    
    # Layer 2: Synthesized guides
    layer2_path = SOURCE_PACK_DIR / "layer2_synthesized" / "variation_guide_ko.md"
    if layer2_path.exists():
        with open(layer2_path, "r", encoding="utf-8") as f:
            layers["layer2_synthesized"] = f.read()
    
    return layers


def convert_to_notebooklm_format(layers: dict) -> list:
    """
    Convert layer files to NotebookLM source format.
    
    NotebookLM sources can be:
    - Google Docs/Slides (via URL)
    - Web URLs
    - Raw text
    - PDF (file upload)
    """
    sources = []
    
    # Layer 0: JSON을 포맷된 텍스트로 변환
    if "layer0_raw" in layers:
        layer0_text = format_layer0_as_text(layers["layer0_raw"])
        sources.append({
            "type": "raw_text",
            "title": "봉준호 클러스터 - Layer 0: Raw Evidence",
            "content": layer0_text,
            "metadata": {
                "layer": "layer0_raw",
                "cluster_id": "CL_BONG_01"
            }
        })
    
    # Layer 1: JSON을 포맷된 텍스트로 변환
    if "layer1_structured" in layers:
        layer1_text = format_layer1_as_text(layers["layer1_structured"])
        sources.append({
            "type": "raw_text",
            "title": "봉준호 클러스터 - Layer 1: Logic & Persona Vectors",
            "content": layer1_text,
            "metadata": {
                "layer": "layer1_structured",
                "cluster_id": "CL_BONG_01"
            }
        })
    
    # Layer 2: Markdown은 직접 사용 가능
    if "layer2_synthesized" in layers:
        sources.append({
            "type": "raw_text",
            "title": "봉준호 클러스터 - Layer 2: 오마주 변주 가이드",
            "content": layers["layer2_synthesized"],
            "metadata": {
                "layer": "layer2_synthesized",
                "cluster_id": "CL_BONG_01"
            }
        })
    
    return sources


def format_layer0_as_text(data: dict) -> str:
    """Format Layer 0 JSON as readable text for NotebookLM."""
    lines = []
    lines.append("# 봉준호 클러스터 - 원본 영상 분석 결과 (Layer 0)")
    lines.append("")
    lines.append(f"클러스터 ID: {data.get('cluster_id', 'N/A')}")
    lines.append(f"감독: {data.get('auteur', 'N/A')}")
    lines.append(f"생성일: {data.get('generated_at', 'N/A')}")
    lines.append("")
    
    # Chunks
    chunks = data.get("chunks", [])
    lines.append(f"## 샷 분석 청크 (총 {len(chunks)}개)")
    lines.append("")
    
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        content = chunk.get("content", {})
        
        lines.append(f"### {meta.get('film_title', 'Unknown')} - {meta.get('temporal_phase', 'N/A')}")
        lines.append(f"- **청크 ID**: {chunk.get('chunk_id', 'N/A')}")
        lines.append(f"- **씬 범위**: {meta.get('scene_range', 'N/A')}")
        lines.append(f"- **대사/설명**: {content.get('transcript', 'N/A')}")
        lines.append("")
        
        visual = content.get("visual_schema", {})
        lines.append(f"#### 시각 분석")
        lines.append(f"- 구도: {visual.get('composition', 'N/A')}")
        lines.append(f"- 조명: {visual.get('lighting', 'N/A')}")
        lines.append(f"- 카메라: {visual.get('camera_motion', 'N/A')}")
        lines.append(f"- 페이싱: {visual.get('pacing', 'N/A')}")
        lines.append("")
        
        motifs = content.get("motifs", [])
        if motifs:
            lines.append(f"#### 모티프: {', '.join(motifs)}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Motif Registry
    registry = data.get("motif_registry", {})
    recurring = registry.get("recurring_motifs", [])
    if recurring:
        lines.append("## 반복 모티프 레지스트리")
        lines.append("")
        for motif in recurring:
            lines.append(f"### {motif.get('name', 'N/A')}")
            lines.append(f"- **의미**: {motif.get('semantic_meaning', 'N/A')}")
            lines.append(f"- **빈도**: {motif.get('frequency', 'N/A')}")
            lines.append(f"- **등장**: {', '.join(motif.get('occurrences', []))}")
            lines.append("")
    
    return "\n".join(lines)


def format_layer1_as_text(data: dict) -> str:
    """Format Layer 1 JSON as readable text for NotebookLM."""
    lines = []
    lines.append("# 봉준호 클러스터 - 구조화 지식 (Layer 1)")
    lines.append("")
    lines.append(f"클러스터 ID: {data.get('cluster_id', 'N/A')}")
    lines.append(f"감독: {data.get('auteur', 'N/A')}")
    lines.append("")
    
    # Logic Vector
    logic = data.get("logic_vector", {})
    lines.append("## Logic Vector (수학적 로직)")
    lines.append("")
    lines.append(f"**Logic ID**: {logic.get('logic_id', 'N/A')}")
    lines.append(f"**설명**: {logic.get('description', 'N/A')}")
    lines.append("")
    
    cadence = logic.get("cadence", {})
    lines.append("### 케이던스 (Cadence)")
    shot_len = cadence.get("shot_length_ms", {})
    lines.append(f"- 샷 길이 중앙값: {shot_len.get('median', 'N/A')}ms")
    lines.append(f"- 특징: {shot_len.get('signature', 'N/A')}")
    lines.append("")
    
    cut_density = cadence.get("cut_density", {})
    lines.append("### 컷 밀도 (Temporal Phase별)")
    for phase, density in cut_density.items():
        lines.append(f"- {phase.upper()}: {density}")
    lines.append("")
    
    composition = logic.get("composition", {})
    lines.append("### 구도 (Composition)")
    lines.append(f"- 주요 전략: {composition.get('primary_strategy', 'N/A')}")
    lines.append(f"- 대칭 점수: {composition.get('symmetry_score', 'N/A')}")
    lines.append(f"- 심도: {composition.get('depth_usage', 'N/A')}")
    sig_comp = composition.get("signature_compositions", [])
    if sig_comp:
        lines.append(f"- 시그니처 구도: {', '.join(sig_comp)}")
    lines.append("")
    
    camera = logic.get("camera_motion", {})
    lines.append("### 카메라 움직임")
    lines.append(f"- 특징: {camera.get('signature', 'N/A')}")
    lines.append(f"- 스태틱: {camera.get('static', 0)*100:.0f}%")
    lines.append(f"- 돌리: {camera.get('dolly', 0)*100:.0f}%")
    lines.append(f"- 핸드헬드: {camera.get('handheld', 0)*100:.0f}%")
    lines.append("")
    
    # Persona Vector
    persona = data.get("persona_vector", {})
    lines.append("## Persona Vector (예술적 페르소나)")
    lines.append("")
    lines.append(f"**Persona ID**: {persona.get('persona_id', 'N/A')}")
    lines.append(f"**설명**: {persona.get('description', 'N/A')}")
    lines.append("")
    
    tone = persona.get("tone", [])
    lines.append(f"### 톤: {', '.join(tone)}")
    lines.append("")
    
    lines.append("### 감정 곡선 (Emotion Arc)")
    emotion_arc = persona.get("emotion_arc", [])
    for point in emotion_arc:
        lines.append(f"- t={point.get('t', 0)}: {point.get('label', 'N/A')} (valence={point.get('valence', 0)}, arousal={point.get('arousal', 0)})")
    lines.append("")
    
    frames = persona.get("interpretation_frame", [])
    lines.append(f"### 해석 프레임: {', '.join(frames)}")
    lines.append("")
    
    # Pattern Rules
    rules = data.get("pattern_rules", [])
    if rules:
        lines.append("## 패턴 규칙")
        lines.append("")
        for rule in rules:
            lines.append(f"### {rule.get('name', 'N/A')}")
            lines.append(f"- **설명**: {rule.get('description', 'N/A')}")
            lines.append(f"- **적용 조건**: {rule.get('application_condition', 'N/A')}")
            lines.append("")
    
    # Fusion Formula
    fusion = data.get("fusion_formula", {})
    lines.append("## Fusion 공식")
    lines.append(f"- **공식**: `{fusion.get('formula', 'N/A')}`")
    thresholds = fusion.get("thresholds", {})
    lines.append(f"- **동일 클러스터**: D <= {thresholds.get('same_cluster', 'N/A')}")
    lines.append(f"- **클러스터 분기**: D >= {thresholds.get('split_cluster', 'N/A')}")
    lines.append("")
    
    return "\n".join(lines)


def export_as_text_files(sources: list, output_dir: Path):
    """Export sources as text files for manual upload."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, source in enumerate(sources):
        filename = f"{i+1:02d}_{source['title'].replace(' ', '_').replace(':', '').replace('-', '_')}.txt"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {source['title']}\n\n")
            f.write(source['content'])
        
        print(f"✓ Exported: {filepath}")
    
    print(f"\n총 {len(sources)}개 파일 생성 완료!")
    print(f"위치: {output_dir}")


def upload_to_notebooklm_api(sources: list, project_id: str, notebook_title: str):
    """
    Upload sources to NotebookLM via Enterprise API.
    
    NOTE: 이 함수는 Enterprise API 클라이언트가 설치된 환경에서만 작동합니다.
    현재 Google Cloud NotebookLM API가 활성화된 프로젝트가 필요합니다.
    """
    try:
        # Enterprise API 클라이언트 임포트 시도
        # 실제 패키지 이름은 Google Cloud 문서 참조 필요
        # from google.cloud import notebooklm
        print("⚠️  NotebookLM Enterprise API 클라이언트가 필요합니다.")
        print("   현재는 텍스트 파일 내보내기만 지원됩니다.")
        print("   수동 업로드를 위해 --export-only 옵션을 사용하세요.")
        return False
    except ImportError:
        print("❌ google-cloud-notebooklm 패키지가 설치되지 않았습니다.")
        return False


def main():
    parser = argparse.ArgumentParser(description="NotebookLM Source Pack Uploader")
    parser.add_argument("--project-id", help="Google Cloud Project ID")
    parser.add_argument("--notebook-title", default="봉준호 클러스터 분석", help="Notebook title")
    parser.add_argument("--export-only", action="store_true", help="Export as text files only")
    parser.add_argument("--output-dir", default="./notebooklm_upload", help="Output directory for text files")
    
    args = parser.parse_args()
    
    print("📦 Loading source pack layers...")
    layers = load_layer_files()
    print(f"   Loaded {len(layers)} layers")
    
    print("\n🔄 Converting to NotebookLM format...")
    sources = convert_to_notebooklm_format(layers)
    print(f"   Prepared {len(sources)} sources")
    
    if args.export_only or not args.project_id:
        print("\n📁 Exporting as text files for manual upload...")
        output_dir = Path(args.output_dir)
        export_as_text_files(sources, output_dir)
        
        print("\n📋 수동 업로드 안내:")
        print("   1. https://notebooklm.google.com 접속")
        print("   2. '새 노트북' 생성 → 제목: '봉준호 클러스터 분석'")
        print("   3. '소스 추가' → '텍스트 붙여넣기'")
        print("   4. 각 .txt 파일의 내용을 순서대로 붙여넣기")
        print("   5. 모든 소스 추가 후 '개요 노트' 생성")
    else:
        print("\n☁️  Uploading to NotebookLM API...")
        success = upload_to_notebooklm_api(sources, args.project_id, args.notebook_title)
        if not success:
            print("\n💡 텍스트 파일로 내보내려면 --export-only 옵션을 사용하세요.")


if __name__ == "__main__":
    main()
