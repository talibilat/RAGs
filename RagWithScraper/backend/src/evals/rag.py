import os
import sys
import time
import tqdm
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from datasets import Dataset
from ragas import RunConfig, evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    answer_correctness,
    answer_similarity
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI

# Add the src directory to the Python path to enable imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, src_dir)

# Import local utilities
from utils.logger import setup_logger
from utils.retriever_client import retrieve_similar_documents

# Load environment variables
import dotenv
dotenv.load_dotenv()

# Set up logger and paths
logger = setup_logger(name="RAG Evaluation", log_to_file=True)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
csv_path = os.path.join(project_root, "data/test/voy_faqs.csv")
results_dir = os.path.join(project_root, "results")

# Ensure results directory exists
os.makedirs(results_dir, exist_ok=True)

# Constants
LIMIT = 5
EVAL_EMBEDDING_MODELS = ['openai']

# Load test data
try:
    logger.info(f"Loading test data from {csv_path}")
    df = pd.read_csv(csv_path)
    QUESTIONS = df["question"].to_list()
    GROUND_TRUTH = df["answer"].tolist()
    logger.info(f"Loaded {len(QUESTIONS)} questions for evaluation")
except Exception as e:
    logger.error(f"Error loading test data: {str(e)}")
    raise

def get_rag_chain(model: str, embedding_type: str) -> RunnableSequence:
    """
    Create a basic RAG chain

    Args:
        model (str): Chat completion model to use
        embedding_type (str): Type of embedding to use ("hf" or "openai")

    Returns:
        RunnableSequence: A RAG chain
    """
    try:
        # Generate context using the retriever, and pass the user question through
        retrieve = {
            "context": lambda x: "\n\n".join([doc['answer'] for doc in retrieve_similar_documents(x, embedding_type, LIMIT)]),
            "question": RunnablePassthrough(),
        }

        template = """Answer the question based only on the following context if there is no relevant content retrieved then answer that you don't know:
        {context}

        Question: {question}
        """
        
        # Defining the chat prompt
        prompt = ChatPromptTemplate.from_template(template)
        
        # Defining the model to be used for chat completion
        llm = ChatOpenAI(temperature=0, model=model)
        
        # Parse output as a string
        parse_output = StrOutputParser()

        # Naive RAG chain
        rag_chain = (
            retrieve 
            | prompt 
            | llm 
            | parse_output
        )
        
        return rag_chain
    except Exception as e:
        logger.error(f"Error creating RAG chain for model {model}: {str(e)}")
        raise

def evaluate_models():
    """
    Evaluate different models using RAGAS metrics
    """
    all_results = {}
    
    # Create a list to store detailed results for each question
    detailed_results = []
    
    for model in ["gpt-4o"]:
        for embedding_type in EVAL_EMBEDDING_MODELS:
            start_time = time.time()
            logger.info(f"Starting evaluation for model: {model} with {embedding_type} embeddings")
            
            try:
                data = {
                    "question": QUESTIONS,
                    "ground_truth": GROUND_TRUTH,
                    "contexts": [],
                    "answer": []
                }

                rag_chain = get_rag_chain(model, embedding_type)

                success_count = 0
                error_count = 0
                
                for i, question in enumerate(tqdm.tqdm(QUESTIONS, desc=f"Processing questions for {model} with {embedding_type}")):
                    try:
                        # Get contexts first
                        contexts = retrieve_similar_documents(question, embedding_type, LIMIT)
                        context_texts = [doc['answer'] for doc in contexts]
                        data["contexts"].append(context_texts)
                        
                        # Generate answer
                        answer = rag_chain.invoke(question)
                        data["answer"].append(answer)
                        
                        # Store detailed results
                        detailed_results.append({
                            'model': model,
                            'embedding_type': embedding_type,
                            'question': question,
                            'ground_truth': GROUND_TRUTH[i],
                            'retrieved_contexts': '\n'.join(context_texts),
                            'generated_answer': answer,
                            'success': True
                        })
                        
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error processing question '{question}': {str(e)}")
                        error_count += 1
                        # Add empty results for failed questions
                        data["answer"].append("")
                        data["contexts"].append([])
                        
                        # Store failed attempt details
                        detailed_results.append({
                            'model': model,
                            'embedding_type': embedding_type,
                            'question': question,
                            'ground_truth': GROUND_TRUTH[i],
                            'retrieved_contexts': '',
                            'generated_answer': '',
                            'success': False,
                            'error': str(e)
                        })

                # RAGAS evaluation
                dataset = Dataset.from_dict(data)
                run_config = RunConfig(max_workers=4, max_wait=180)
                
                result = evaluate(
                    dataset=dataset,
                    metrics=[faithfulness, answer_relevancy],
                    run_config=run_config,
                    raise_exceptions=False,
                )
                
                elapsed_time = time.time() - start_time
                
                # Calculate mean scores if metrics are lists
                faithfulness_score = float(result['faithfulness']) if isinstance(result['faithfulness'], (int, float)) else float(sum(result['faithfulness']) / len(result['faithfulness']))
                answer_relevancy_score = float(result['answer_relevancy']) if isinstance(result['answer_relevancy'], (int, float)) else float(sum(result['answer_relevancy']) / len(result['answer_relevancy']))
                
                # Update metrics in detailed results
                for item in detailed_results:
                    if item['model'] == model and item['embedding_type'] == embedding_type:
                        item.update({
                            'faithfulness_score': faithfulness_score,
                            'answer_relevancy_score': answer_relevancy_score,
                            'time_taken': elapsed_time
                        })
                
                # Log results
                logger.info(f"Results for {model} with {embedding_type} embeddings:")
                logger.info(f"- Success rate: {success_count}/{len(QUESTIONS)} ({success_count/len(QUESTIONS)*100:.2f}%)")
                logger.info(f"- Error rate: {error_count}/{len(QUESTIONS)} ({error_count/len(QUESTIONS)*100:.2f}%)")
                logger.info(f"- Time taken: {elapsed_time:.2f} seconds")
                logger.info(f"- Metrics: Faithfulness={faithfulness_score:.3f}, Answer Relevancy={answer_relevancy_score:.3f}")
                
                all_results[f"{model}_{embedding_type}"] = {
                    "metrics": {
                        "faithfulness": faithfulness_score,
                        "answer_relevancy": answer_relevancy_score
                    },
                    "success_rate": success_count/len(QUESTIONS),
                    "error_rate": error_count/len(QUESTIONS),
                    "time_taken": elapsed_time
                }
                
            except Exception as e:
                logger.error(f"Error evaluating model {model} with {embedding_type}: {str(e)}")
                continue
    
    # Save detailed results to CSV
    results_df = pd.DataFrame(detailed_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(results_dir, f'detailed_results_{timestamp}.csv')
    results_df.to_csv(csv_path, index=False)
    logger.info(f"Detailed results saved to {csv_path}")
    
    return all_results

def visualize_results(results: dict):
    """
    Create and save visualizations of the evaluation results
    
    Args:
        results (dict): Dictionary containing evaluation results for each model
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create performance comparison plots
        metrics_data = {
            'Model': [],
            'Metric': [],
            'Score': []
        }
        
        for model in results:
            # Add metrics scores
            metrics_data['Model'].append(model)
            metrics_data['Model'].append(model)
            metrics_data['Model'].append(model)
            
            metrics_data['Metric'].extend(['Faithfulness', 'Answer Relevancy', 'Success Rate'])
            
            metrics_data['Score'].append(results[model]['metrics']['faithfulness'])
            metrics_data['Score'].append(results[model]['metrics']['answer_relevancy'])
            metrics_data['Score'].append(results[model]['success_rate'])
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(metrics_data)
        
        # Create plot
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='Model', y='Score', hue='Metric')
        plt.title('Model Performance Comparison')
        plt.xlabel('Model + Embedding Type')
        plt.ylabel('Score')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Metrics', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Save the plot
        plot_path = os.path.join(results_dir, f'rag_evaluation_{timestamp}.png')
        plt.savefig(plot_path, bbox_inches='tight', dpi=300)
        plt.close()
        
        # Create timing comparison
        plt.figure(figsize=(8, 5))
        times = [results[model]['time_taken'] for model in results]
        plt.bar(results.keys(), times)
        plt.title('Execution Time Comparison')
        plt.xlabel('Model + Embedding Type')
        plt.ylabel('Time (seconds)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the timing plot
        timing_plot_path = os.path.join(results_dir, f'timing_comparison_{timestamp}.png')
        plt.savefig(timing_plot_path, bbox_inches='tight', dpi=300)
        plt.close()
        
        logger.info(f"Visualizations saved to {plot_path} and {timing_plot_path}")
        
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        raise

def main():
    """
    Main function to run the evaluation
    """
    try:
        logger.info("Starting RAG evaluation")
        results = evaluate_models()
        visualize_results(results)
        logger.info("RAG evaluation completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()