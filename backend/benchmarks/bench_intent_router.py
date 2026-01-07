"""Intent Router Performance Benchmark.

Measures:
- Keyword-based classification speed
- Hybrid classification speed (with LLM fallback)
- Cache hit ratio
"""
import time
from statistics import mean, stdev, median
from typing import Dict, Any, List

from app.agents.intent_router import (
    classify_intent,
    classify_intent_hybrid,
    get_cache_stats,
)


# Test messages covering various intents
TEST_MESSAGES: List[str] = [
    # Prompt generation
    "프롬프트 만들어줘",
    "영상 프롬프트 생성해줘",
    "이 컨셉으로 프롬프트 작성해줘",
    
    # Storyboard
    "스토리보드 작성해줘",
    "장면 구성 도와줘",
    "씬별로 나눠줘",
    
    # Image generation
    "이미지 만들어줘",
    "참고 이미지 생성해줘",
    "비주얼 컨셉 그려줘",
    
    # Video generation
    "영상 만들어줘",
    "비디오 생성해줘",
    "Veo로 영상 생성",
    
    # General chat
    "안녕하세요",
    "도움이 필요해요",
    "어떻게 사용하나요?",
    
    # Complex messages (longer)
    "이번 영상은 한국의 전통 문화를 현대적으로 재해석한 컨셉인데요, 프롬프트를 만들어주세요.",
    "밤하늘에 별이 쏟아지는 장면을 담은 뮤직비디오를 만들고 싶어요. 스토리보드부터 시작해주세요.",
    "미래 도시의 네온 조명이 반사되는 비 오는 거리 장면을 이미지로 먼저 보고 싶어요.",
]


def bench_keyword_classification(iterations: int = 3) -> Dict[str, Any]:
    """Benchmark keyword-based classification speed."""
    all_times: List[float] = []
    
    for _ in range(iterations):
        for msg in TEST_MESSAGES:
            start = time.perf_counter()
            classify_intent(msg)
            elapsed_ms = (time.perf_counter() - start) * 1000
            all_times.append(elapsed_ms)
    
    return {
        "method": "keyword",
        "total_classifications": len(all_times),
        "avg_ms": round(mean(all_times), 3),
        "median_ms": round(median(all_times), 3),
        "std_ms": round(stdev(all_times), 3) if len(all_times) > 1 else 0,
        "min_ms": round(min(all_times), 3),
        "max_ms": round(max(all_times), 3),
    }


def bench_hybrid_classification(iterations: int = 1) -> Dict[str, Any]:
    """Benchmark hybrid classification with LLM fallback."""
    # Note: This may make actual API calls for low-confidence cases
    all_times: List[float] = []
    
    for _ in range(iterations):
        for msg in TEST_MESSAGES:
            start = time.perf_counter()
            classify_intent_hybrid(msg)
            elapsed_ms = (time.perf_counter() - start) * 1000
            all_times.append(elapsed_ms)
    
    cache_stats = get_cache_stats()
    
    return {
        "method": "hybrid",
        "total_classifications": len(all_times),
        "avg_ms": round(mean(all_times), 3),
        "median_ms": round(median(all_times), 3),
        "min_ms": round(min(all_times), 3),
        "max_ms": round(max(all_times), 3),
        "cache_size": cache_stats.get("size", 0),
        "cache_maxsize": cache_stats.get("maxsize", 0),
    }


def run_intent_benchmarks() -> Dict[str, Any]:
    """Run all intent router benchmarks."""
    print("  Running keyword classification benchmark...")
    keyword_results = bench_keyword_classification()
    
    print("  Running hybrid classification benchmark...")
    hybrid_results = bench_hybrid_classification()
    
    return {
        "keyword": keyword_results,
        "hybrid": hybrid_results,
    }


if __name__ == "__main__":
    print("Intent Router Benchmarks")
    print("=" * 40)
    results = run_intent_benchmarks()
    
    print("\nKeyword Classification:")
    for k, v in results["keyword"].items():
        print(f"  {k}: {v}")
    
    print("\nHybrid Classification:")
    for k, v in results["hybrid"].items():
        print(f"  {k}: {v}")
