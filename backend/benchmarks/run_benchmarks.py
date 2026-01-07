"""P3 Benchmark Runner.

Runs all benchmarks and produces a summary report.

Usage:
    cd /Users/ted/vivid/backend
    source venv/bin/activate
    python -m benchmarks.run_benchmarks
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from benchmarks.bench_intent_router import run_intent_benchmarks
from benchmarks.bench_memory_manager import run_memory_benchmarks
from benchmarks.bench_tool_execution import run_tool_benchmarks


def format_summary(results: dict) -> str:
    """Format benchmark results as a readable summary."""
    lines = [
        "=" * 60,
        "CHOKKI AGENT PERFORMANCE BENCHMARK RESULTS",
        f"Timestamp: {results['timestamp']}",
        "=" * 60,
        "",
    ]
    
    # Intent Router
    lines.append("📍 INTENT ROUTER")
    lines.append("-" * 40)
    intent = results["benchmarks"]["intent_router"]
    lines.append(f"  Keyword classification: {intent['keyword']['avg_ms']:.3f}ms avg")
    lines.append(f"  Hybrid classification:  {intent['hybrid']['avg_ms']:.3f}ms avg")
    lines.append(f"  Cache size: {intent['hybrid']['cache_size']}/{intent['hybrid']['cache_maxsize']}")
    lines.append("")
    
    # Memory Manager
    lines.append("🧠 MEMORY MANAGER")
    lines.append("-" * 40)
    memory = results["benchmarks"]["memory_manager"]
    for size, data in memory["token_estimation"]["results_by_text_size"].items():
        lines.append(f"  Token est ({size}): {data['avg_us']:.1f}µs ({data['ops_per_sec']:.0f} ops/sec)")
    lines.append("")
    for r in memory["context_building"]["results_by_message_count"]:
        lines.append(f"  Context build ({r['input_messages']} msgs): {r['avg_build_ms']:.2f}ms")
    lines.append("")
    
    # Tool Execution
    lines.append("🔧 TOOL EXECUTION")
    lines.append("-" * 40)
    tool = results["benchmarks"]["tool_execution"]
    lines.append(f"  Overhead: {tool['execution_overhead']['overhead_ms']:.3f}ms")
    for r in tool["concurrent_execution"]["results_by_concurrency"]:
        lines.append(f"  Concurrent ({r['concurrent_calls']}): {r['avg_per_call_ms']:.3f}ms/call")
    lines.append("")
    
    # Performance Summary
    lines.append("=" * 60)
    lines.append("PERFORMANCE SUMMARY")
    lines.append("=" * 60)
    
    # Check against targets
    targets = {
        "keyword_classification_ms": 5.0,
        "hybrid_classification_cached_ms": 10.0,
        "token_estimation_ops_per_sec": 10000,
        "context_build_100msgs_ms": 50.0,
        "tool_overhead_ms": 1.0,
    }
    
    checks = [
        ("Keyword classification <5ms", intent['keyword']['avg_ms'] < targets["keyword_classification_ms"]),
        ("Token est >10K ops/sec", 
         any(d['ops_per_sec'] >= targets["token_estimation_ops_per_sec"] 
             for d in memory["token_estimation"]["results_by_text_size"].values())),
        ("Tool overhead <1ms", tool['execution_overhead']['overhead_ms'] < targets["tool_overhead_ms"]),
    ]
    
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        lines.append(f"  {status} {check_name}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


async def main():
    """Run all benchmarks and save results."""
    print("=" * 60)
    print("CHOKKI AGENT PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "benchmarks": {},
    }
    
    # Run benchmarks
    print("1. Intent Router Benchmarks")
    results["benchmarks"]["intent_router"] = run_intent_benchmarks()
    print()
    
    print("2. Memory Manager Benchmarks")
    results["benchmarks"]["memory_manager"] = run_memory_benchmarks()
    print()
    
    print("3. Tool Execution Benchmarks")
    results["benchmarks"]["tool_execution"] = await run_tool_benchmarks()
    print()
    
    # Save JSON results
    output_dir = Path(__file__).parent
    json_path = output_dir / "benchmark_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {json_path}")
    
    # Print summary
    print()
    summary = format_summary(results)
    print(summary)
    
    # Save summary
    summary_path = output_dir / "benchmark_summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary)
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
