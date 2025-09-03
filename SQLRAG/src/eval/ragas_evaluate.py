from __future__ import annotations
"""RAGAS-enhanced evaluation framework for the SQL chat pipeline."""
import json
import argparse
import logging
import re
from statistics import mean
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    ContextRelevance,
    context_recall,
    answer_correctness,
    answer_similarity
)

from agent.chat_sql import answer_question


logger = logging.getLogger(__name__)


@dataclass
class RAGASEvaluationResult:
    """Structured result for RAGAS evaluation."""
    question: str
    context: str
    ground_truth: str
    generated_answer: str
    question_type: str
    difficulty: str
    category: str
    ragas_metrics: Dict[str, float]
    traditional_metrics: Dict[str, Any]


def extract_numbers(text: str) -> List[float]:
    """Extract all numeric values from text."""
    return [float(x.replace(',', '')) for x in re.findall(r"[-+]?\d[\d,]*\.?\d*", text)]


def extract_keywords(text: str) -> List[str]:
    """Extract potential keywords from text."""
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    return [word for word in words if word not in stop_words and len(word) > 2]


def calculate_traditional_metrics(expected_numbers: List[float], expected_keywords: List[str], answer: str) -> Dict[str, Any]:
    """Calculate traditional evaluation metrics."""
    got_numbers = extract_numbers(answer)
    
    # Numeric recall
    numeric_recall = None
    if expected_numbers:
        hits = sum(1 for e in expected_numbers if any(abs(e - g) <= max(abs(e) * 0.02, 0.01) for g in got_numbers))
        numeric_recall = hits / len(expected_numbers)
    
    # Keyword coverage
    keyword_coverage = 0.0
    if expected_keywords:
        answer_lower = answer.lower()
        found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
        keyword_coverage = found_keywords / len(expected_keywords)
    
    # Citation analysis
    citation_count = len(re.findall(r"\[\d+\]", answer))
    has_citations = citation_count > 0
    
    return {
        "numeric_recall": numeric_recall,
        "keyword_coverage": keyword_coverage,
        "citation_count": citation_count,
        "has_citations": has_citations,
        "answer_length": len(answer),
        "contains_expected_keywords": keyword_coverage > 0
    }


def prepare_ragas_dataset(evaluation_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare data in RAGAS format."""
    ragas_data = []
    
    for item in evaluation_data:
        question = item["question"]
        context = item["context"]
        ground_truth = item["ground_truth"]
        
        try:
            generated_answer = answer_question(question)
        except Exception as e:
            logger.error(f"Error generating answer for '{question}': {e}")
            generated_answer = f"ERROR: {str(e)}"
        
        ragas_data.append({
            "user_input": question,
            "response": generated_answer,
            "retrieved_contexts": [context],  # RAGAS expects list of contexts
            "ground_truth": ground_truth,
            "reference": ground_truth  # Required for context_recall metric
        })
    
    # Convert to RAGAS Dataset format
    from ragas import EvaluationDataset
    return EvaluationDataset.from_pandas(pd.DataFrame(ragas_data))


def run_ragas_evaluation(evaluation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run RAGAS evaluation on the dataset."""
    logger.info("Preparing RAGAS dataset...")
    ragas_df = prepare_ragas_dataset(evaluation_data)
    
    logger.info("Running RAGAS evaluation...")
    
    # Define RAGAS metrics
    metrics = [
        faithfulness,
        answer_relevancy,
        ContextRelevance(),
        context_recall,
        answer_correctness,
        answer_similarity
    ]
    
    # Run evaluation
    results = evaluate(ragas_df, metrics)
    
    return results


def evaluate_single_question(question_data: Dict[str, Any]) -> RAGASEvaluationResult:
    """Evaluate a single question and return structured results."""
    question = question_data["question"]
    context = question_data["context"]
    ground_truth = question_data["ground_truth"]
    expected_numbers = question_data.get("expected_numbers", [])
    expected_keywords = question_data.get("expected_keywords", [])
    question_type = question_data.get("question_type", "unknown")
    difficulty = question_data.get("difficulty", "unknown")
    category = question_data.get("category", "unknown")
    
    logger.info(f"Evaluating question: {question}")
    
    try:
        generated_answer = answer_question(question)
        traditional_metrics = calculate_traditional_metrics(expected_numbers, expected_keywords, generated_answer)
        
        return RAGASEvaluationResult(
            question=question,
            context=context,
            ground_truth=ground_truth,
            generated_answer=generated_answer,
            question_type=question_type,
            difficulty=difficulty,
            category=category,
            ragas_metrics={},  # Will be filled by RAGAS evaluation
            traditional_metrics=traditional_metrics
        )
    except Exception as e:
        logger.error(f"Error evaluating question '{question}': {e}")
        return RAGASEvaluationResult(
            question=question,
            context=context,
            ground_truth=ground_truth,
            generated_answer=f"ERROR: {str(e)}",
            question_type=question_type,
            difficulty=difficulty,
            category=category,
            ragas_metrics={},
            traditional_metrics={
                "numeric_recall": None,
                "keyword_coverage": 0.0,
                "citation_count": 0,
                "has_citations": False,
                "answer_length": 0,
                "contains_expected_keywords": False
            }
        )


def run_comprehensive_eval(examples_path: str) -> Dict[str, Any]:
    """Run comprehensive evaluation with both traditional and RAGAS metrics."""
    with open(examples_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} evaluation questions")
    
    # Run traditional evaluation
    traditional_results = []
    for question_data in data:
        result = evaluate_single_question(question_data)
        traditional_results.append(result)
    
    # Run RAGAS evaluation
    logger.info("Starting RAGAS evaluation...")
    ragas_results = run_ragas_evaluation(data)
    
    # Combine results
    combined_results = []
    for i, traditional_result in enumerate(traditional_results):
        # Extract RAGAS metrics for this specific question
        ragas_metrics = {}
        try:
            if hasattr(ragas_results, 'to_pandas'):
                ragas_df = ragas_results.to_pandas()
                if i < len(ragas_df):
                    for col in ragas_df.columns:
                        if col not in ['user_input', 'response', 'retrieved_contexts', 'ground_truth']:
                            ragas_metrics[col] = ragas_df.iloc[i][col]
        except Exception as e:
            logger.warning(f"Could not extract RAGAS metrics: {e}")
        
        traditional_result.ragas_metrics = ragas_metrics
        combined_results.append(traditional_result)
    
    # Calculate aggregate metrics
    traditional_metrics = [r.traditional_metrics for r in combined_results]
    
    numeric_recalls = [m["numeric_recall"] for m in traditional_metrics if m["numeric_recall"] is not None]
    avg_numeric_recall = mean(numeric_recalls) if numeric_recalls else None
    
    keyword_coverages = [m["keyword_coverage"] for m in traditional_metrics]
    avg_keyword_coverage = mean(keyword_coverages)
    
    citation_rate = sum(1 for m in traditional_metrics if m["has_citations"]) / len(traditional_metrics)
    avg_citation_count = mean(m["citation_count"] for m in traditional_metrics)
    avg_answer_length = mean(m["answer_length"] for m in traditional_metrics)
    
    # Group by question type and difficulty
    type_metrics = {}
    difficulty_metrics = {}
    category_metrics = {}
    
    for result in combined_results:
        # Question type metrics
        qtype = result.question_type
        if qtype not in type_metrics:
            type_metrics[qtype] = {
                "count": 0,
                "numeric_recalls": [],
                "keyword_coverages": [],
                "citation_rates": [],
                "ragas_scores": {}
            }
        
        type_metrics[qtype]["count"] += 1
        if result.traditional_metrics["numeric_recall"] is not None:
            type_metrics[qtype]["numeric_recalls"].append(result.traditional_metrics["numeric_recall"])
        type_metrics[qtype]["keyword_coverages"].append(result.traditional_metrics["keyword_coverage"])
        type_metrics[qtype]["citation_rates"].append(1 if result.traditional_metrics["has_citations"] else 0)
        
        # Aggregate RAGAS scores by type
        for metric, score in result.ragas_metrics.items():
            if metric not in type_metrics[qtype]["ragas_scores"]:
                type_metrics[qtype]["ragas_scores"][metric] = []
            if isinstance(score, (int, float)):
                type_metrics[qtype]["ragas_scores"][metric].append(score)
        
        # Difficulty metrics
        diff = result.difficulty
        if diff not in difficulty_metrics:
            difficulty_metrics[diff] = {
                "count": 0,
                "keyword_coverages": [],
                "citation_rates": []
            }
        difficulty_metrics[diff]["count"] += 1
        difficulty_metrics[diff]["keyword_coverages"].append(result.traditional_metrics["keyword_coverage"])
        difficulty_metrics[diff]["citation_rates"].append(1 if result.traditional_metrics["has_citations"] else 0)
        
        # Category metrics
        cat = result.category
        if cat not in category_metrics:
            category_metrics[cat] = {
                "count": 0,
                "keyword_coverages": [],
                "citation_rates": []
            }
        category_metrics[cat]["count"] += 1
        category_metrics[cat]["keyword_coverages"].append(result.traditional_metrics["keyword_coverage"])
        category_metrics[cat]["citation_rates"].append(1 if result.traditional_metrics["has_citations"] else 0)
    
    # Calculate averages for each grouping
    for metrics_dict in [type_metrics, difficulty_metrics, category_metrics]:
        for key, metrics in metrics_dict.items():
            if "numeric_recalls" in metrics and metrics["numeric_recalls"]:
                metrics["avg_numeric_recall"] = mean(metrics["numeric_recalls"])
            if "keyword_coverages" in metrics:
                metrics["avg_keyword_coverage"] = mean(metrics["keyword_coverages"])
            if "citation_rates" in metrics:
                metrics["citation_rate"] = mean(metrics["citation_rates"])
            if "ragas_scores" in metrics:
                for metric, scores in metrics["ragas_scores"].items():
                    if scores:
                        metrics[f"avg_{metric}"] = mean(scores)
    
    # Overall RAGAS metrics
    overall_ragas = {}
    try:
        if hasattr(ragas_results, 'to_pandas'):
            ragas_df = ragas_results.to_pandas()
            for col in ragas_df.columns:
                if col not in ['user_input', 'response', 'retrieved_contexts', 'ground_truth', 'reference']:
                    try:
                        overall_ragas[col] = ragas_df[col].mean()
                    except:
                        pass
    except Exception as e:
        logger.warning(f"Could not extract overall RAGAS metrics: {e}")
    
    return {
        "overall_metrics": {
            "total_questions": len(combined_results),
            "avg_numeric_recall": avg_numeric_recall,
            "avg_keyword_coverage": avg_keyword_coverage,
            "citation_rate": citation_rate,
            "avg_citation_count": avg_citation_count,
            "avg_answer_length": avg_answer_length,
            "ragas_metrics": overall_ragas
        },
        "question_type_metrics": type_metrics,
        "difficulty_metrics": difficulty_metrics,
        "category_metrics": category_metrics,
        "detailed_results": [
            {
                "question": r.question,
                "question_type": r.question_type,
                "difficulty": r.difficulty,
                "category": r.category,
                "context": r.context,
                "ground_truth": r.ground_truth,
                "generated_answer": r.generated_answer,
                "traditional_metrics": r.traditional_metrics,
                "ragas_metrics": r.ragas_metrics
            }
            for r in combined_results
        ]
    }


def main():
    """Main entry point for RAGAS-enhanced evaluation."""
    ap = argparse.ArgumentParser(description="RAGAS-enhanced evaluation framework for SQL chat pipeline")
    ap.add_argument("--examples", type=str, required=True, help="Path to JSON file with test questions")
    ap.add_argument("--output", type=str, help="Path to save detailed results (optional)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = ap.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    results = run_comprehensive_eval(args.examples)
    
    # Print summary
    print("=== RAGAS-ENHANCED EVALUATION SUMMARY ===")
    overall = results["overall_metrics"]
    print(f"Total Questions: {overall['total_questions']}")
    print(f"Average Numeric Recall: {overall['avg_numeric_recall']:.3f}" if overall['avg_numeric_recall'] else "Average Numeric Recall: N/A")
    print(f"Average Keyword Coverage: {overall['avg_keyword_coverage']:.3f}")
    print(f"Citation Rate: {overall['citation_rate']:.3f}")
    print(f"Average Citations per Answer: {overall['avg_citation_count']:.1f}")
    print(f"Average Answer Length: {overall['avg_answer_length']:.0f} characters")
    
    if overall.get('ragas_metrics'):
        print("\n=== RAGAS METRICS ===")
        for metric, score in overall['ragas_metrics'].items():
            print(f"{metric}: {score:.3f}")
    
    print("\n=== BY QUESTION TYPE ===")
    for qtype, metrics in results["question_type_metrics"].items():
        print(f"\n{qtype.upper()}:")
        print(f"  Count: {metrics['count']}")
        if metrics.get('avg_numeric_recall') is not None:
            print(f"  Avg Numeric Recall: {metrics['avg_numeric_recall']:.3f}")
        print(f"  Avg Keyword Coverage: {metrics['avg_keyword_coverage']:.3f}")
        print(f"  Citation Rate: {metrics['citation_rate']:.3f}")
        
        # Print RAGAS metrics for this type
        if metrics.get('ragas_scores'):
            print("  RAGAS Metrics:")
            for metric, scores in metrics['ragas_scores'].items():
                if scores:
                    avg_score = mean(scores)
                    print(f"    {metric}: {avg_score:.3f}")
    
    print("\n=== BY DIFFICULTY ===")
    for diff, metrics in results["difficulty_metrics"].items():
        print(f"\n{diff.upper()}:")
        print(f"  Count: {metrics['count']}")
        print(f"  Avg Keyword Coverage: {metrics['avg_keyword_coverage']:.3f}")
        print(f"  Citation Rate: {metrics['citation_rate']:.3f}")
    
    print("\n=== BY CATEGORY ===")
    for cat, metrics in results["category_metrics"].items():
        print(f"\n{cat.upper()}:")
        print(f"  Count: {metrics['count']}")
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
