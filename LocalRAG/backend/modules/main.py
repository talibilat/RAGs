
import sys
import os
import time
from modules.pdf_processing import text_formatter, open_and_read_pdf, text_to_sentences
from modules.text_chunking import process_sentence_chunks, process_chunks
from modules.embedding import create_embeddings
from modules.retrieval import retrieve_relevant_resources, print_top_results_and_scores
from modules.query_processing import answer_query
from modules.utils import load_config, embedding_model, save_embeddings, load_embeddings, clean_text

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# Load configuration
config = load_config('config.yaml')

# Load the embedding model globally to avoid loading it multiple times
embed_model = embedding_model(device="cpu")

def process_pdf_and_create_embeddings(pdf_path, config):
    """
    This function processes the PDF, chunks the text, and creates embeddings.
    """
    # Extract text from PDF
    raw_text = text_formatter(pdf_path)

    # Preprocess and chunk text
    preprocessed_text = open_and_read_pdf(raw_text)
    processed_text = text_to_sentences(preprocessed_text)
    chunks_list = process_sentence_chunks(processed_text, config["chunk_size"])
    chunks = process_chunks(chunks_list)
    
    print(f"Total number of chunks: {len(chunks)}")

    # Creating embeddings on CPU
    start_time = time.time()
    embeddings = create_embeddings(chunks, embed_model)
    print(f"Time taken to create embeddings: {time.time() - start_time:.2f} seconds")
    
    # Save embeddings for later use
    save_embeddings(embeddings, 'data/embeddings.csv')

    return chunks, embeddings

def load_saved_embeddings(csv_path):
    """
    Load pre-saved embeddings from a CSV file.
    """
    return load_embeddings(csv_path)

def query_contract(query, tensor_embeddings, pages_and_chunks, n_resources_to_return=3):
    """
    Process the query and retrieve answers based on embeddings.
    """
    # Retrieve and print top results
    retrieved_data = print_top_results_and_scores(query=query,
                                embeddings=tensor_embeddings,
                                pages_and_chunks=pages_and_chunks,
                                embed_model=embed_model,
                                n_resources_to_return=n_resources_to_return)
    
    # Answer the query
    answer = answer_query(query, retrieved_data, config)

    return answer
