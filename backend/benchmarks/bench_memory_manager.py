"""Memory Manager Performance Benchmark.

Measures:
- Token estimation speed
- Context building speed (with varying message counts)
- Compression/summarization performance
"""
import time
from statistics import mean, stdev, median
from typing import Dict, Any, List

from app.agents.vivid_agent import MemoryManager
from app.agents.agent_types import AgentMessage, AgentRole, AgentState


def generate_conversation(n_messages: int, avg_chars_per_msg: int = 200) -> List[AgentMessage]:
    """Generate test conversation of specified size."""
    messages = []
    for i in range(n_messages):
        role = AgentRole.USER if i % 2 == 0 else AgentRole.ASSISTANT
        # Simulate realistic message content
        content = f"메시지 #{i}: " + ("테스트 내용입니다. " * (avg_chars_per_msg // 10))
        messages.append(AgentMessage(role=role, content=content))
    return messages


def bench_token_estimation(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark token estimation speed."""
    mm = MemoryManager()
    
    # Test texts of varying sizes
    test_texts = [
        "짧은 텍스트",  # ~5 chars
        "중간 길이의 테스트 텍스트입니다." * 5,  # ~75 chars
        "긴 텍스트입니다. " * 100,  # ~1000 chars
        "매우 긴 텍스트입니다. " * 500,  # ~5000 chars
    ]
    
    results = {}
    
    for text in test_texts:
        text_len = len(text)
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            mm.estimate_tokens(text)
            elapsed_us = (time.perf_counter() - start) * 1_000_000  # microseconds
            times.append(elapsed_us)
        
        results[f"{text_len}_chars"] = {
            "avg_us": round(mean(times), 2),
            "median_us": round(median(times), 2),
            "ops_per_sec": round(1_000_000 / mean(times), 0),
        }
    
    return {
        "iterations": iterations,
        "results_by_text_size": results,
    }


def bench_context_building(message_counts: List[int] = None) -> Dict[str, Any]:
    """Benchmark context building with varying message counts."""
    if message_counts is None:
        message_counts = [10, 50, 100, 200, 500]
    
    mm = MemoryManager()
    results = []
    
    for n_msgs in message_counts:
        messages = generate_conversation(n_msgs)
        state = AgentState(
            session_id="benchmark-session",
            messages=messages,
            summary="",
        )
        
        # Run multiple times for accuracy
        times = []
        for _ in range(10):
            start = time.perf_counter()
            context = mm.build_context(state, "System prompt for benchmarking")
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
        
        output_tokens = sum(mm.estimate_tokens(m.content) for m in context)
        
        results.append({
            "input_messages": n_msgs,
            "output_messages": len(context),
            "output_tokens": output_tokens,
            "avg_build_ms": round(mean(times), 2),
            "median_build_ms": round(median(times), 2),
        })
    
    return {
        "max_tokens_budget": mm.max_tokens,
        "results_by_message_count": results,
    }


def run_memory_benchmarks() -> Dict[str, Any]:
    """Run all memory manager benchmarks."""
    print("  Running token estimation benchmark...")
    token_results = bench_token_estimation()
    
    print("  Running context building benchmark...")
    context_results = bench_context_building()
    
    return {
        "token_estimation": token_results,
        "context_building": context_results,
    }


if __name__ == "__main__":
    print("Memory Manager Benchmarks")
    print("=" * 40)
    results = run_memory_benchmarks()
    
    print("\nToken Estimation:")
    for size, data in results["token_estimation"]["results_by_text_size"].items():
        print(f"  {size}: {data['avg_us']:.1f}µs ({data['ops_per_sec']:.0f} ops/sec)")
    
    print("\nContext Building:")
    for r in results["context_building"]["results_by_message_count"]:
        print(f"  {r['input_messages']} msgs -> {r['output_messages']} msgs: {r['avg_build_ms']:.2f}ms")
