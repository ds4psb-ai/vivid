#!/usr/bin/env python3
"""
Real vs Ideal Mock Data Comparison Script

Purpose: Compare actual NotebookLM outputs against ideal benchmarks
to measure quality gaps and guide prompt engineering improvements.

Usage:
    python compare_real_vs_ideal.py --real data/bong_derived_insights.json --ideal data/ideal/bong_ideal_homage_guide.json
"""

import argparse
import json
from pathlib import Path
from typing import Any

# Field coverage requirements by guide type
REQUIRED_FIELDS = {
    "homage": ["visual_language", "color_palette", "camera_motion", "thematic_motifs"],
    "beat_sheet": ["beats", "transitions", "tonal_markers"],
    "storyboard": ["shots", "sequence_info", "editing_notes"],
    "persona": ["artistic_philosophy", "thematic_obsessions", "signature_techniques"],
}


def load_json(path: str) -> dict:
    """Load JSON file"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_nested_items(data: Any, depth: int = 0) -> int:
    """Count total items in nested structure"""
    if isinstance(data, dict):
        return sum(count_nested_items(v, depth + 1) for v in data.values()) + len(data)
    elif isinstance(data, list):
        return sum(count_nested_items(item, depth + 1) for item in data) + len(data)
    else:
        return 1


def calculate_field_coverage(real: dict, ideal: dict) -> dict:
    """Calculate how many ideal fields are present in real data"""
    ideal_fields = set(ideal.keys())
    real_fields = set(real.keys())
    
    covered = ideal_fields & real_fields
    missing = ideal_fields - real_fields
    extra = real_fields - ideal_fields
    
    coverage_ratio = len(covered) / len(ideal_fields) if ideal_fields else 0
    
    return {
        "coverage_ratio": coverage_ratio,
        "covered_fields": list(covered),
        "missing_fields": list(missing),
        "extra_fields": list(extra),
    }


def calculate_depth_score(real: dict, ideal: dict) -> dict:
    """Compare structural depth between real and ideal"""
    real_depth = count_nested_items(real)
    ideal_depth = count_nested_items(ideal)
    
    depth_ratio = real_depth / ideal_depth if ideal_depth else 0
    
    return {
        "real_item_count": real_depth,
        "ideal_item_count": ideal_depth,
        "depth_ratio": depth_ratio,
        "assessment": "adequate" if depth_ratio > 0.7 else "needs_improvement",
    }


def calculate_specificity_score(real: dict, ideal: dict) -> dict:
    """Measure specificity of content (string length proxy)"""
    def total_string_length(data: Any) -> int:
        if isinstance(data, str):
            return len(data)
        elif isinstance(data, dict):
            return sum(total_string_length(v) for v in data.values())
        elif isinstance(data, list):
            return sum(total_string_length(item) for item in data)
        return 0
    
    real_length = total_string_length(real)
    ideal_length = total_string_length(ideal)
    
    specificity_ratio = real_length / ideal_length if ideal_length else 0
    
    return {
        "real_content_length": real_length,
        "ideal_content_length": ideal_length,
        "specificity_ratio": specificity_ratio,
        "assessment": "detailed" if specificity_ratio > 0.5 else "too_brief",
    }


def generate_improvement_suggestions(comparison: dict) -> list[str]:
    """Generate actionable improvement suggestions"""
    suggestions = []
    
    if comparison["field_coverage"]["coverage_ratio"] < 0.8:
        missing = comparison["field_coverage"]["missing_fields"][:3]
        suggestions.append(f"Prompt 개선: 누락 필드 추가 요청 - {', '.join(missing)}")
    
    if comparison["depth"]["depth_ratio"] < 0.5:
        suggestions.append("Prompt 개선: 더 상세한 하위 구조 요청 (예시 제공)")
    
    if comparison["specificity"]["specificity_ratio"] < 0.3:
        suggestions.append("Prompt 개선: 구체적인 설명 요청 (숫자, 이름, 타임코드 등)")
    
    if not suggestions:
        suggestions.append("품질 양호 - 현재 프롬프트 유지")
    
    return suggestions


def compare(real_path: str, ideal_path: str, guide_type: str | None = None) -> dict:
    """Run full comparison"""
    real_data = load_json(real_path)
    ideal_data = load_json(ideal_path)
    
    # Handle array of records - filter by guide_type if specified
    if isinstance(real_data, list):
        if guide_type:
            matching = [r for r in real_data if r.get("guide_type") == guide_type]
            real_data = matching[0] if matching else {}
        else:
            real_data = real_data[0] if real_data else {}
    
    comparison = {
        "real_file": real_path,
        "ideal_file": ideal_path,
        "guide_type_filter": guide_type,
        "field_coverage": calculate_field_coverage(real_data, ideal_data),
        "depth": calculate_depth_score(real_data, ideal_data),
        "specificity": calculate_specificity_score(real_data, ideal_data),
    }
    
    # Calculate overall quality score (0-100)
    quality_score = (
        comparison["field_coverage"]["coverage_ratio"] * 40 +
        min(comparison["depth"]["depth_ratio"], 1.0) * 30 +
        min(comparison["specificity"]["specificity_ratio"], 1.0) * 30
    )
    
    comparison["quality_score"] = round(quality_score, 1)
    comparison["improvement_suggestions"] = generate_improvement_suggestions(comparison)
    
    return comparison


def print_report(comparison: dict):
    """Print human-readable comparison report"""
    print("\n" + "=" * 60)
    print("📊 REAL vs IDEAL 비교 리포트")
    print("=" * 60)
    
    print(f"\n📁 Real: {comparison['real_file']}")
    print(f"📁 Ideal: {comparison['ideal_file']}")
    if comparison.get("guide_type_filter"):
        print(f"🏷️  Guide Type: {comparison['guide_type_filter']}")
    
    print(f"\n🎯 Quality Score: {comparison['quality_score']}/100")
    
    fc = comparison["field_coverage"]
    print(f"\n📋 Field Coverage: {fc['coverage_ratio']:.0%}")
    if fc["missing_fields"]:
        print(f"   ❌ Missing: {', '.join(fc['missing_fields'][:5])}")
    if fc["extra_fields"]:
        print(f"   ➕ Extra: {', '.join(fc['extra_fields'][:5])}")
    
    depth = comparison["depth"]
    print(f"\n📐 Structural Depth: {depth['depth_ratio']:.0%}")
    print(f"   Real: {depth['real_item_count']} items | Ideal: {depth['ideal_item_count']} items")
    
    spec = comparison["specificity"]
    print(f"\n📝 Specificity: {spec['specificity_ratio']:.0%}")
    print(f"   Real: {spec['real_content_length']} chars | Ideal: {spec['ideal_content_length']} chars")
    
    print("\n💡 개선 제안:")
    for i, suggestion in enumerate(comparison["improvement_suggestions"], 1):
        print(f"   {i}. {suggestion}")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Compare real vs ideal mock data")
    parser.add_argument("--real", required=True, help="Path to real data JSON")
    parser.add_argument("--ideal", required=True, help="Path to ideal data JSON")
    parser.add_argument("--guide-type", dest="guide_type", help="Filter real data by guide_type (e.g., homage, story, storyboard, persona)")
    parser.add_argument("--output", help="Output JSON path (optional)")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    
    args = parser.parse_args()
    
    comparison = compare(args.real, args.ideal, args.guide_type)
    
    if not args.quiet:
        print_report(comparison)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Report saved to: {args.output}")
    
    return comparison


if __name__ == "__main__":
    main()
