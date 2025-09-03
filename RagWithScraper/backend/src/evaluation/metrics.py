"""
Evaluation Metrics for RAG System.

This module provides metrics for evaluating the quality and performance of
Retrieval-Augmented Generation (RAG) system responses. It implements two main
evaluation approaches:

1. Semantic Similarity: Uses sentence transformers to calculate embedding-based
   similarity between texts (e.g., response and reference answer)
   
2. LLM-based Evaluation: Leverages an LLM (e.g., OpenAI's models) to assess
   response quality across multiple dimensions including factual accuracy,
   relevance, completeness, and context usage.

These metrics provide a comprehensive assessment of RAG system performance.
"""
from typing import Dict, Any, List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from openai import AsyncOpenAI
import os
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

# Initialize global clients
_sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")
_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using sentence transformers.
    
    This function generates embeddings for both input texts using the SentenceTransformer
    model and calculates their cosine similarity. The result is a score between 0 and 1,
    where higher values indicate greater semantic similarity.
    
    Args:
        text1 (str): First text to compare (e.g., generated response)
        text2 (str): Second text to compare (e.g., reference answer)
        
    Returns:
        float: Similarity score between 0 (completely different) and 1 (identical)
    """
    try:
        # Generate embeddings for both texts
        embedding1 = _sentence_transformer.encode([text1])[0]
        embedding2 = _sentence_transformer.encode([text2])[0]
        
        # Calculate cosine similarity between the embeddings
        similarity = cosine_similarity(
            embedding1.reshape(1, -1),
            embedding2.reshape(1, -1)
        )[0][0]
        
        return float(similarity)
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {str(e)}")
        return 0.0

async def evaluate_with_llm(
    question: str, 
    response: str, 
    context: List[str],
    model: str = "o3-mini"
) -> Dict[str, Any]:
    """
    Evaluate RAG response quality using an LLM as a judge.
    
    This function uses an OpenAI model to evaluate the quality of a generated response
    based on the original question and retrieved context. The evaluation covers multiple
    dimensions of response quality:
    
    1. Factual Accuracy: Whether the response contains correct information aligned with the context
    2. Relevance: How well the response addresses the original question
    3. Completeness: Whether the response covers all important aspects of the question
    4. Context Usage: How effectively the retrieved context was utilized in the response
    
    Args:
        question (str): The original user question
        response (str): The generated response from the RAG system
        context (List[str]): The retrieved context passages used to generate the response
        model (str): OpenAI model to use for evaluation (default: "o3-mini")
        
    Returns:
        Dict[str, Any]: Evaluation results dictionary containing:
            - scores: Dictionary of numerical scores (0-10) for each evaluation dimension
            - raw_response: The raw JSON response from the LLM
    """
    try:
        # Join context passages into a single text
        context_text = " ".join(context)
        
        # Create evaluation prompt for the LLM
        prompt = f"""Please evaluate this question-answer pair with the given context:

Question: {question}
Response: {response}
Context: {context_text}

Evaluate on the following criteria (score 0-10):
1. Factual Accuracy: Does the response align with facts in the context?
2. Relevance: How well does the response address the question?
3. Completeness: Does the response cover all important aspects?
4. Context Usage: How well does it use the provided context?

Return only the scores in JSON format like this:
{{"factual_accuracy": score, "relevance": score, "completeness": score, "context_usage": score}}"""

        # Send evaluation request to OpenAI
        completion = await _openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response and return scores
        scores = json.loads(completion.choices[0].message.content)
        return {
            "scores": scores,
            "raw_response": completion.choices[0].message.content
        }
        
    except Exception as e:
        logger.error(f"Error in LLM evaluation: {str(e)}")
        return {
            "scores": {
                "factual_accuracy": 0,
                "relevance": 0,
                "completeness": 0,
                "context_usage": 0
            },
            "raw_response": f"Evaluation failed: {str(e)}"
        } 