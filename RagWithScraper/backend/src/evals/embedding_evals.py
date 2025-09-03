import os
import sys
import tqdm
import pandas as pd
from datasets import Dataset
from ragas import RunConfig, evaluate
from ragas.metrics import context_precision, context_recall


# Add the src directory to the Python path to enable imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, src_dir)

# Import utilities
from utils.logger import setup_logger
from utils.retriever_client import retrieve_similar_documents

# Set up logger
logger = setup_logger(name="Evals Embeddings", log_to_file=True)

# Set up logger and paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
csv_path = os.path.join(project_root, "data/test/voy_faqs.csv")

# Loading Variables
df = pd.read_csv(csv_path)
LIMIT = 5
EVAL_EMBEDDING_MODELS = ['openai']
QUESTIONS = df["question"].to_list()
GROUND_TRUTH = df["answer"].tolist()






all_results = []
for model in EVAL_EMBEDDING_MODELS:
    data = {"question": [], "ground_truth": [], "contexts": []}
    data["question"] = QUESTIONS
    data["ground_truth"] = GROUND_TRUTH
    for question in QUESTIONS:
        data["contexts"].append(
            [doc['answer'] for doc in retrieve_similar_documents(question, model, LIMIT)])

    # RAGAS expects a Dataset object
    dataset = Dataset.from_dict(data)
    # RAGAS runtime settings to avoid hitting OpenAI rate limits
    run_config = RunConfig(max_workers=4, max_wait=180)
    result = evaluate(
        dataset=dataset,
        metrics=[context_precision, context_recall],
        run_config=run_config,
        raise_exceptions=False,
    )
    print(f"Result for the {model} model: {result}")



