"""Tool Execution Performance Benchmark.

Measures:
- ToolRegistry execution overhead
- Concurrent tool execution performance
"""
import asyncio
import time
from statistics import mean, stdev, median
from typing import Dict, Any, List

from app.agents.agent_types import (
    ToolRegistry,
    ToolSpec,
    ToolCall,
    ToolContext,
    ToolResult,
    ToolTaskState,
)


async def create_instant_tool() -> tuple:
    """Create an instant-returning tool for overhead testing."""
    async def handler(ctx: ToolContext, call: ToolCall) -> ToolResult:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.COMPLETED,
            output={"result": "instant"},
        )
    
    spec = ToolSpec(
        name="instant_bench_tool",
        description="Instant tool for benchmarking",
        input_schema={"type": "object", "properties": {}},
    )
    
    return spec, handler


async def bench_tool_execution_overhead(iterations: int = 100) -> Dict[str, Any]:
    """Benchmark ToolRegistry execution overhead."""
    spec, handler = await create_instant_tool()
    registry = ToolRegistry()
    registry.register(spec, handler)
    
    times: List[float] = []
    
    for i in range(iterations):
        call = ToolCall(
            id=f"bench-call-{i}",
            name="instant_bench_tool",
            arguments={},
        )
        
        start = time.perf_counter()
        await registry.execute(None, call)
        elapsed_us = (time.perf_counter() - start) * 1_000_000  # microseconds
        times.append(elapsed_us)
    
    return {
        "iterations": iterations,
        "avg_overhead_us": round(mean(times), 2),
        "median_overhead_us": round(median(times), 2),
        "std_overhead_us": round(stdev(times), 2) if len(times) > 1 else 0,
        "min_overhead_us": round(min(times), 2),
        "max_overhead_us": round(max(times), 2),
        "overhead_ms": round(mean(times) / 1000, 3),
    }


async def bench_concurrent_execution(concurrency_levels: List[int] = None) -> Dict[str, Any]:
    """Benchmark concurrent tool execution."""
    if concurrency_levels is None:
        concurrency_levels = [1, 5, 10, 20]
    
    spec, handler = await create_instant_tool()
    registry = ToolRegistry()
    registry.register(spec, handler)
    
    results = []
    
    for n_concurrent in concurrency_levels:
        calls = [
            ToolCall(
                id=f"concurrent-{i}",
                name="instant_bench_tool",
                arguments={},
            )
            for i in range(n_concurrent)
        ]
        
        # Measure concurrent execution time
        times = []
        for _ in range(10):  # 10 rounds
            start = time.perf_counter()
            await asyncio.gather(*[
                registry.execute(None, call) for call in calls
            ])
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
        
        results.append({
            "concurrent_calls": n_concurrent,
            "avg_total_ms": round(mean(times), 2),
            "avg_per_call_ms": round(mean(times) / n_concurrent, 3),
        })
    
    return {
        "results_by_concurrency": results,
    }


async def run_tool_benchmarks() -> Dict[str, Any]:
    """Run all tool execution benchmarks."""
    print("  Running tool execution overhead benchmark...")
    overhead_results = await bench_tool_execution_overhead()
    
    print("  Running concurrent execution benchmark...")
    concurrent_results = await bench_concurrent_execution()
    
    return {
        "execution_overhead": overhead_results,
        "concurrent_execution": concurrent_results,
    }


if __name__ == "__main__":
    print("Tool Execution Benchmarks")
    print("=" * 40)
    results = asyncio.run(run_tool_benchmarks())
    
    print("\nExecution Overhead:")
    overhead = results["execution_overhead"]
    print(f"  Average: {overhead['avg_overhead_us']:.1f}µs ({overhead['overhead_ms']:.3f}ms)")
    print(f"  Range: {overhead['min_overhead_us']:.1f}µs - {overhead['max_overhead_us']:.1f}µs")
    
    print("\nConcurrent Execution:")
    for r in results["concurrent_execution"]["results_by_concurrency"]:
        print(f"  {r['concurrent_calls']} calls: {r['avg_total_ms']:.2f}ms total, {r['avg_per_call_ms']:.3f}ms/call")
