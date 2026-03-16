#!/usr/bin/env python
"""
Performance Benchmarking Script
Location: backend/scripts/benchmark.py
"""

import asyncio
import time
import argparse
from pathlib import Path
import sys
import json
import statistics

sys.path.append(str(Path(__file__).parent.parent))

from src.query.query_parser import QueryParser
from src.query.intent_classifier import IntentClassifier
from src.query.context_pruner import ContextPruner
from src.query.prompt_builder import PromptBuilder
from src.llm.router import LLMRouter
from src.scaledown.optimizer import PromptOptimizer
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Benchmark:
    """Run performance benchmarks"""
    
    def __init__(self):
        self.parser = QueryParser()
        self.classifier = IntentClassifier()
        self.pruner = ContextPruner()
        self.builder = PromptBuilder()
        self.router = LLMRouter()
        self.optimizer = PromptOptimizer()
        
    async def run_benchmark(self, queries: list, iterations: int = 5):
        """
        Run benchmark on queries
        """
        results = {
            "total_time": 0,
            "avg_time": 0,
            "min_time": float('inf'),
            "max_time": 0,
            "by_stage": {},
            "token_savings": []
        }
        
        stage_times = {
            "parse": [],
            "classify": [],
            "prune": [],
            "build": [],
            "optimize": [],
            "route": []
        }
        
        for i in range(iterations):
            logger.info(f"Iteration {i+1}/{iterations}")
            
            for query in queries:
                start_total = time.time()
                
                # Parse
                start = time.time()
                parsed = self.parser.parse(query)
                stage_times["parse"].append(time.time() - start)
                
                # Classify
                start = time.time()
                intent = self.classifier.classify(parsed, 7)
                stage_times["classify"].append(time.time() - start)
                
                # Prune
                start = time.time()
                context = await self.pruner.prune(query, 7, "science", intent)
                stage_times["prune"].append(time.time() - start)
                
                # Build
                start = time.time()
                prompt = self.builder.build(query, context, intent, 7)
                stage_times["build"].append(time.time() - start)
                
                # Optimize
                start = time.time()
                optimized = await self.optimizer.optimize(prompt)
                stage_times["optimize"].append(time.time() - start)
                
                # Route (mock - don't call actual LLM)
                start = time.time()
                stage_times["route"].append(time.time() - start)
                
                total_time = time.time() - start_total
                
                results["total_time"] += total_time
                results["min_time"] = min(results["min_time"], total_time)
                results["max_time"] = max(results["max_time"], total_time)
                
                if "savings_percentage" in optimized:
                    results["token_savings"].append(optimized["savings_percentage"])
        
        # Calculate averages
        num_ops = len(queries) * iterations
        results["avg_time"] = results["total_time"] / num_ops if num_ops > 0 else 0
        
        for stage, times in stage_times.items():
            if times:
                results["by_stage"][stage] = {
                    "avg": statistics.mean(times),
                    "min": min(times),
                    "max": max(times),
                    "total": sum(times)
                }
        
        if results["token_savings"]:
            results["avg_token_savings"] = statistics.mean(results["token_savings"])
            results["min_token_savings"] = min(results["token_savings"])
            results["max_token_savings"] = max(results["token_savings"])
        
        return results

async def main():
    parser = argparse.ArgumentParser(description="Run benchmarks")
    parser.add_argument("--queries", type=str, help="JSON file with test queries")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    
    args = parser.parse_args()
    
    # Default test queries
    test_queries = [
        "What is photosynthesis?",
        "How does the water cycle work?",
        "Explain the Pythagorean theorem",
        "What causes earthquakes?",
        "Who was the first president of India?",
        "How do you solve quadratic equations?",
        "What are the parts of a cell?",
        "Explain gravity in simple terms",
        "What is the capital of France?",
        "How does a computer work?"
    ]
    
    if args.queries:
        with open(args.queries, 'r') as f:
            data = json.load(f)
            test_queries = data.get("queries", test_queries)
    
    logger.info(f"Running benchmark with {len(test_queries)} queries, {args.iterations} iterations")
    
    benchmark = Benchmark()
    results = await benchmark.run_benchmark(test_queries, args.iterations)
    
    # Print results
    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    print(f"Total queries processed: {len(test_queries) * args.iterations}")
    print(f"Average time per query: {results['avg_time']*1000:.2f} ms")
    print(f"Min time: {results['min_time']*1000:.2f} ms")
    print(f"Max time: {results['max_time']*1000:.2f} ms")
    
    if "avg_token_savings" in results:
        print(f"Average token savings: {results['avg_token_savings']:.1f}%")
    
    print("\nStage breakdown:")
    for stage, stats in results["by_stage"].items():
        print(f"  {stage}: {stats['avg']*1000:.2f} ms avg")
    
    # Save results
    output_file = f"benchmark_results_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())