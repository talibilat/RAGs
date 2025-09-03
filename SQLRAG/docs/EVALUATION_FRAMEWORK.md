# Offline Evaluation Framework

This document describes the enhanced offline evaluation framework for the 9fin-agent SQL chat pipeline.

## Overview

The evaluation framework provides comprehensive metrics to assess the agent's performance across different types of questions, from simple factual lookups to complex analytical requests.

## Framework Components

### 1. Enhanced Evaluation Engine (`src/agent/eval/enhanced_evaluate.py`)

The enhanced evaluation framework provides:

- **Structured Results**: Uses `EvaluationResult` dataclass for consistent result formatting
- **Multiple Metrics**: Beyond just numeric recall, includes keyword coverage, citation analysis, and answer quality metrics
- **Question Type Analysis**: Groups results by question type for targeted insights
- **Error Handling**: Gracefully handles evaluation errors and provides detailed logging

### 2. Test Question Sets

#### Basic Questions (`examples/eval_questions.json`)
- Simple factual and aggregate queries
- Tests basic SQL generation and execution

#### Analyst Questions (`examples/analyst_questions.json`)
- Real-world analyst-style questions
- Includes factual lookups, strategic advice, and analytical frameworks
- Tests more complex reasoning and response generation

#### Validation Set (`examples/validation_set.json`)
- Questions with known expected numeric answers
- Used for validation and regression testing

## Metrics

### Numeric Recall
- Measures accuracy of numeric values in responses
- Uses approximate equality with configurable tolerance
- Only calculated when expected numbers are provided

### Keyword Coverage
- Measures how well responses address expected topics
- Calculates percentage of expected keywords found in answers
- Helps assess relevance and completeness

### Citation Analysis
- **Citation Rate**: Percentage of answers that include source references
- **Average Citations**: Mean number of citations per answer
- **Citation Quality**: Ensures proper source attribution

### Answer Quality
- **Answer Length**: Measures response comprehensiveness
- **Content Relevance**: Based on keyword coverage and expected content

## Question Types

The framework categorizes questions into types for targeted analysis:

- **factual_lookup**: Simple data retrieval questions
- **analytical_advice**: Strategic recommendations and advice
- **analytical_framework**: Structured analysis requests (SWOT, etc.)
- **unknown**: Default category for uncategorized questions

## Usage

### Command Line Interface

```bash
# Evaluate analyst questions with verbose output
make eval-analyst

# Evaluate basic questions with enhanced metrics
make eval-enhanced

# Run original simple evaluation
make eval

# Run validation set
make validate
```

### Programmatic Usage

```python
from src.agent.eval.enhanced_evaluate import run_enhanced_eval

results = run_enhanced_eval("examples/analyst_questions.json")
print(f"Overall citation rate: {results['overall_metrics']['citation_rate']}")
```

### Output Format

The framework provides both human-readable summaries and detailed JSON output:

```json
{
  "overall_metrics": {
    "total_questions": 3,
    "avg_numeric_recall": 1.0,
    "avg_keyword_coverage": 0.889,
    "citation_rate": 1.0,
    "avg_citation_count": 5.3,
    "avg_answer_length": 449
  },
  "question_type_metrics": {
    "factual_lookup": {
      "count": 1,
      "avg_numeric_recall": 1.0,
      "avg_keyword_coverage": 0.667,
      "citation_rate": 1.0
    }
  },
  "detailed_results": [...]
}
```

## Sample Results

### Analyst Questions Evaluation

```
=== EVALUATION SUMMARY ===
Total Questions: 3
Average Numeric Recall: 1.000
Average Keyword Coverage: 0.889
Citation Rate: 1.000
Average Citations per Answer: 5.3
Average Answer Length: 449 characters

=== BY QUESTION TYPE ===

FACTUAL_LOOKUP:
  Count: 1
  Avg Numeric Recall: 1.000
  Avg Keyword Coverage: 0.667
  Citation Rate: 1.000

ANALYTICAL_ADVICE:
  Count: 1
  Avg Keyword Coverage: 1.000
  Citation Rate: 1.000

ANALYTICAL_FRAMEWORK:
  Count: 1
  Avg Keyword Coverage: 1.000
  Citation Rate: 1.000
```

## Extending the Framework

### Adding New Question Types

1. Update the question JSON with `question_type` field
2. Add expected keywords and numbers as appropriate
3. The framework will automatically categorize and analyze by type

### Adding New Metrics

1. Extend the `EvaluationResult` dataclass
2. Implement calculation logic in `evaluate_single_question()`
3. Update the aggregate metrics calculation in `run_enhanced_eval()`

### Custom Evaluation Logic

The framework is designed to be extensible. You can:

- Override the `evaluate_single_question()` function for custom logic
- Add new question types and corresponding analysis
- Implement domain-specific metrics for financial analysis

## Best Practices

1. **Test Coverage**: Use a mix of question types to ensure comprehensive evaluation
2. **Expected Values**: Provide expected numbers and keywords for accurate assessment
3. **Regular Evaluation**: Run evaluations after significant changes to track performance
4. **Baseline Establishment**: Establish performance baselines for comparison
5. **Error Analysis**: Review failed evaluations to identify improvement areas

## Future Enhancements

Potential improvements to the framework:

- **Semantic Similarity**: Use embeddings to measure answer quality beyond keyword matching
- **Factual Accuracy**: Cross-reference answers with ground truth data
- **Response Time**: Measure and optimize query execution time
- **User Satisfaction**: Integrate human evaluation scores
- **A/B Testing**: Compare different prompt strategies or model versions
