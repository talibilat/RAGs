from __future__ import annotations
"""Enhanced offline evaluation framework for the SQL chat pipeline."""
import json
import argparse
import re
import logging
from statistics import mean
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from agent.chat_sql import answer_question

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Structured result for a single question evaluation."""
    question: str
    answer: str
    question_type: str
    expected_numbers: List[float]
    expected_keywords: List[str]
    numeric_recall: Optional[float]
    keyword_coverage: float
    citation_count: int
    has_citations: bool
    answer_length: int
    contains_expected_keywords: bool


def extract_numbers(text: str) -> List[float]:
    """Extract all numeric values from text."""
    return [float(x.replace(',', '')) for x in re.findall(r"[-+]?\d[\d,]*\.?\d*", text)]


def extract_keywords(text: str) -> List[str]:
    """Extract potential keywords from text (simplified approach)."""
    # Convert to lowercase and split on common delimiters
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    return [word for word in words if word not in stop_words and len(word) > 2]


def approx_equal(a: float, b: float, tol: float = 1e-6, rel: float = 0.02) -> bool:
    """Check if two numbers are approximately equal."""
    if a == b:
        return True
    if abs(a - b) <= tol:
        return True
    return abs(a - b) <= rel * max(abs(a), abs(b))


def calculate_numeric_recall(expected: List[float], got: List[float]) -> Optional[float]:
    """Calculate recall for numeric values."""
    if not expected:
        return None
    hits = sum(1 for e in expected if any(approx_equal(e, g) for g in got))
    return hits / len(expected)


def calculate_keyword_coverage(expected_keywords: List[str], answer_text: str) -> float:
    """Calculate what percentage of expected keywords appear in the answer."""
    if not expected_keywords:
        return 1.0
    
    answer_lower = answer_text.lower()
    found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
    return found_keywords / len(expected_keywords)


def evaluate_single_question(question_data: Dict[str, Any]) -> EvaluationResult:
    """Evaluate a single question and return structured results."""
    question = question_data["question"]
    expected_numbers = question_data.get("expected_numbers", [])
    expected_keywords = question_data.get("expected_keywords", [])
    question_type = question_data.get("question_type", "unknown")
    
    logger.info(f"Evaluating question: {question}")
    
    try:
        answer = answer_question(question)
        got_numbers = extract_numbers(answer)
        numeric_recall = calculate_numeric_recall(expected_numbers, got_numbers)
        keyword_coverage = calculate_keyword_coverage(expected_keywords, answer)
        citation_count = len(re.findall(r"\[\d+\]", answer))
        has_citations = citation_count > 0
        answer_length = len(answer)
        contains_expected_keywords = keyword_coverage > 0
        
        return EvaluationResult(
            question=question,
            answer=answer,
            question_type=question_type,
            expected_numbers=expected_numbers,
            expected_keywords=expected_keywords,
            numeric_recall=numeric_recall,
            keyword_coverage=keyword_coverage,
            citation_count=citation_count,
            has_citations=has_citations,
            answer_length=answer_length,
            contains_expected_keywords=contains_expected_keywords
        )
    except Exception as e:
        logger.error(f"Error evaluating question '{question}': {e}")
        return EvaluationResult(
            question=question,
            answer=f"ERROR: {str(e)}",
            question_type=question_type,
            expected_numbers=expected_numbers,
            expected_keywords=expected_keywords,
            numeric_recall=None,
            keyword_coverage=0.0,
            citation_count=0,
            has_citations=False,
            answer_length=0,
            contains_expected_keywords=False
        )


def run_enhanced_eval(examples_path: str) -> Dict[str, Any]:
    """Run enhanced evaluation on a set of questions."""
    with open(examples_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for question_data in data:
        result = evaluate_single_question(question_data)
        results.append(result)

    # Calculate aggregate metrics
    numeric_recalls = [r.numeric_recall for r in results if r.numeric_recall is not None]
    avg_numeric_recall = mean(numeric_recalls) if numeric_recalls else None
    
    keyword_coverages = [r.keyword_coverage for r in results]
    avg_keyword_coverage = mean(keyword_coverages)
    
    citation_rate = sum(1 for r in results if r.has_citations) / len(results)
    avg_citation_count = mean(r.citation_count for r in results)
    avg_answer_length = mean(r.answer_length for r in results)
    
    # Group by question type
    type_metrics = {}
    for result in results:
        qtype = result.question_type
        if qtype not in type_metrics:
            type_metrics[qtype] = {
                "count": 0,
                "numeric_recalls": [],
                "keyword_coverages": [],
                "citation_rates": []
            }
        
        type_metrics[qtype]["count"] += 1
        if result.numeric_recall is not None:
            type_metrics[qtype]["numeric_recalls"].append(result.numeric_recall)
        type_metrics[qtype]["keyword_coverages"].append(result.keyword_coverage)
        type_metrics[qtype]["citation_rates"].append(1 if result.has_citations else 0)
    
    # Calculate averages for each type
    for qtype, metrics in type_metrics.items():
        metrics["avg_numeric_recall"] = mean(metrics["numeric_recalls"]) if metrics["numeric_recalls"] else None
        metrics["avg_keyword_coverage"] = mean(metrics["keyword_coverages"])
        metrics["citation_rate"] = mean(metrics["citation_rates"])

    return {
        "overall_metrics": {
            "total_questions": len(results),
            "avg_numeric_recall": avg_numeric_recall,
            "avg_keyword_coverage": avg_keyword_coverage,
            "citation_rate": citation_rate,
            "avg_citation_count": avg_citation_count,
            "avg_answer_length": avg_answer_length
        },
        "question_type_metrics": type_metrics,
        "detailed_results": [
            {
                "question": r.question,
                "question_type": r.question_type,
                "answer": r.answer,
                "numeric_recall": r.numeric_recall,
                "keyword_coverage": r.keyword_coverage,
                "citation_count": r.citation_count,
                "has_citations": r.has_citations,
                "answer_length": r.answer_length,
                "contains_expected_keywords": r.contains_expected_keywords
            }
            for r in results
        ]
    }


def main():
    """Main entry point for enhanced evaluation."""
    ap = argparse.ArgumentParser(description="Enhanced evaluation framework for SQL chat pipeline")
    ap.add_argument("--examples", type=str, required=True, help="Path to JSON file with test questions")
    ap.add_argument("--output", type=str, help="Path to save detailed results (optional)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = ap.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    results = run_enhanced_eval(args.examples)
    
    # Print summary
    print("=== EVALUATION SUMMARY ===")
    overall = results["overall_metrics"]
    print(f"Total Questions: {overall['total_questions']}")
    print(f"Average Numeric Recall: {overall['avg_numeric_recall']:.3f}" if overall['avg_numeric_recall'] else "Average Numeric Recall: N/A")
    print(f"Average Keyword Coverage: {overall['avg_keyword_coverage']:.3f}")
    print(f"Citation Rate: {overall['citation_rate']:.3f}")
    print(f"Average Citations per Answer: {overall['avg_citation_count']:.1f}")
    print(f"Average Answer Length: {overall['avg_answer_length']:.0f} characters")
    
    print("\n=== BY QUESTION TYPE ===")
    for qtype, metrics in results["question_type_metrics"].items():
        print(f"\n{qtype.upper()}:")
        print(f"  Count: {metrics['count']}")
        if metrics['avg_numeric_recall'] is not None:
            print(f"  Avg Numeric Recall: {metrics['avg_numeric_recall']:.3f}")
        print(f"  Avg Keyword Coverage: {metrics['avg_keyword_coverage']:.3f}")
        print(f"  Citation Rate: {metrics['citation_rate']:.3f}")
    
    # Save detailed results if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {args.output}")
    
    # Print full JSON for programmatic use
    print("\n=== FULL RESULTS (JSON) ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
