"""Run benchmark evaluation on the AssetBrain copilot."""

import sys
import os
import json
import time

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.copilot import query_with_rag
from backend.config import DATA_DIR

def load_benchmark():
    """Load benchmark questions."""
    benchmark_path = DATA_DIR / "benchmark.json"
    with open(benchmark_path, "r") as f:
        return json.load(f)

def run_benchmark(limit=None):
    """Run benchmark evaluation."""
    benchmark = load_benchmark()
    questions = benchmark.get("benchmark_questions", [])

    if limit:
        questions = questions[:limit]

    print("=" * 70)
    print(f"Running AssetBrain Benchmark ({len(questions)} questions)")
    print("=" * 70)
    print()

    results = []
    total_time = 0

    for i, q in enumerate(questions, 1):
        qid = q["id"]
        question = q["question"]
        expected_sources = set(q.get("expected_sources", []))

        print(f"[{i}/{len(questions)}] {qid}: {question[:60]}...")

        try:
            start = time.time()
            result = query_with_rag(question, top_k=10)
            elapsed = time.time() - start
            total_time += elapsed

            # Extract source filenames from citations
            found_sources = set()
            for citation in result.get("citations", []):
                source = citation.get("source", "")
                found_sources.add(source)

            # Calculate source coverage
            if expected_sources:
                matched = expected_sources & found_sources
                coverage = len(matched) / len(expected_sources) * 100
            else:
                coverage = 0

            results.append({
                "id": qid,
                "question": question,
                "confidence": result.get("confidence", "UNKNOWN"),
                "latency_ms": result.get("latency_ms", 0),
                "sources_found": len(found_sources),
                "expected_sources": len(expected_sources),
                "source_coverage": coverage,
                "matched_sources": list(matched) if expected_sources else [],
                "answer_preview": result.get("answer", "")[:200]
            })

            print(f"  Confidence: {result.get('confidence')}")
            print(f"  Latency: {result.get('latency_ms'):.0f}ms")
            print(f"  Sources: {len(found_sources)}/{len(expected_sources)} ({coverage:.0f}% coverage)")
            print()

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "id": qid,
                "question": question,
                "error": str(e)
            })
            print()

        # Rate limiting pause between questions
        if i < len(questions):
            time.sleep(2)

    # Summary
    print("=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    if successful:
        avg_coverage = sum(r["source_coverage"] for r in successful) / len(successful)
        avg_latency = sum(r["latency_ms"] for r in successful) / len(successful)
        high_confidence = sum(1 for r in successful if r["confidence"] == "HIGH")

        print(f"Questions answered: {len(successful)}/{len(questions)}")
        print(f"Failed: {len(failed)}")
        print(f"Average source coverage: {avg_coverage:.1f}%")
        print(f"Average latency: {avg_latency:.0f}ms")
        print(f"HIGH confidence answers: {high_confidence}/{len(successful)} ({high_confidence/len(successful)*100:.0f}%)")
        print(f"Total time: {total_time:.1f}s")

    # Detailed results
    print("\n" + "=" * 70)
    print("DETAILED RESULTS")
    print("=" * 70)

    for r in results:
        print(f"\n{r['id']}: {r['question'][:60]}...")
        if "error" in r:
            print(f"  ✗ ERROR: {r['error']}")
        else:
            print(f"  Confidence: {r['confidence']}")
            print(f"  Source coverage: {r['source_coverage']:.0f}% ({r['sources_found']}/{r['expected_sources']})")
            if r.get("matched_sources"):
                print(f"  Matched: {', '.join(r['matched_sources'][:3])}")
            print(f"  Answer: {r['answer_preview']}...")

    # Save results
    output_path = DATA_DIR / "benchmark_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "questions_total": len(questions),
            "questions_answered": len(successful),
            "questions_failed": len(failed),
            "avg_source_coverage": avg_coverage if successful else 0,
            "avg_latency_ms": avg_latency if successful else 0,
            "high_confidence_count": high_confidence if successful else 0,
            "results": results
        }, f, indent=2)

    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    # Parse arguments
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    if limit:
        print(f"Running first {limit} questions only\n")

    run_benchmark(limit=limit)
