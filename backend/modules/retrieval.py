import torch
from sentence_transformers import SentenceTransformer, util
from timeit import default_timer as timer
from modules.utils import cosine_similarity_tensor

def retrieve_relevant_resources(query: str,
                                embeddings: torch.tensor,
                                model: SentenceTransformer,
                                n_resources_to_return: int = 5,
                                print_time: bool = True):
    """
    Embeds a query using the model and retrieves the top-k relevant embeddings based on
    dot product, cosine similarity, and Euclidean distance.

    Args:
    - query: The search query from the user.
    - embeddings: The pre-saved embeddings of the document.
    - model: The SentenceTransformer model to embed the query.
    - n_resources_to_return: Number of top results to return.
    - print_time: Whether to print the time taken for computation.

    Returns:
    - scores, indices: Top-k dot product scores and their indices.
    - scores_cos, indices_cos: Top-k cosine similarity scores and their indices.
    - scores_e, indices_e: Top-k Euclidean similarity scores and their indices.
    """

    # Embed the query using the SentenceTransformer model
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Calculate similarity scores using dot product, cosine similarity, and Euclidean similarity
    start_time = timer()
    dot_scores = util.dot_score(query_embedding, embeddings)[0]
    cos_score = util.cos_sim(query_embedding, embeddings)[0]
    euc_score = util.euclidean_sim(query_embedding, embeddings)[0]
    end_time = timer()

    # Optionally print time taken to calculate the scores
    if print_time:
        print(f"[INFO] Time taken to get scores on {len(embeddings)} embeddings: {end_time - start_time:.5f} seconds.")

    # Get the top-k results for each similarity measure
    scores, indices = torch.topk(input=dot_scores, k=n_resources_to_return)
    scores_cos, indices_cos = torch.topk(input=cos_score, k=n_resources_to_return)
    scores_e, indices_e = torch.topk(input=euc_score, k=n_resources_to_return)

    return scores, indices, scores_cos, indices_cos, scores_e, indices_e


def print_top_results_and_scores(query: str,
                                 embeddings: torch.tensor,
                                 pages_and_chunks: list[dict],
                                 embed_model: SentenceTransformer,
                                 n_resources_to_return: int = 3):
    """
    Takes a query, retrieves the most relevant resources, and prints out the top results 
    based on dot product similarity, along with the relevant sentence chunks.

    Args:
    - query: The search query from the user.
    - embeddings: The pre-saved embeddings of the document.
    - pages_and_chunks: List of dictionaries containing the document's sentence chunks and page numbers.
    - embed_model: The SentenceTransformer model to embed the query.
    - n_resources_to_return: Number of top results to return.
    
    Returns:
    - result: A dictionary containing the top results, with sentence chunks and page numbers.
    """

    # Retrieve the top scores and indices for dot product, cosine, and Euclidean similarity
    scores, indices, scores_cos, indices_cos, scores_e, indices_e = retrieve_relevant_resources(
        query=query,
        embeddings=embeddings,
        model=embed_model,
        n_resources_to_return=n_resources_to_return
    )
    
    result = {}  # Initialize the result dictionary to store the top results

    print("Results of Dot product:")
    # Loop through the top-k dot product results
    for i, (score, index) in enumerate(zip(scores, indices)):
        # Add each result to the result dictionary
        result[i] = {
            "result_number": i,  # The rank of the result
            "score": f"Score: {score:.4f}",  # Score rounded to 4 decimal places
            "sentence_chunk": pages_and_chunks[index]["sentence_chunk"],  # The relevant sentence chunk
            "page_number": f"Page number: {pages_and_chunks[index]['page_number']}"  # The corresponding page number
        }

    # Return the result dictionary, which contains the top sentence chunks and scores
    return result
