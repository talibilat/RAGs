from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm


# Function to process embeddings one by one (non-batched)
def create_embeddings(pages_and_chunks: list[dict], model: SentenceTransformer) -> list[dict]:
    """
    Creates embeddings for each sentence chunk in the dataset one by one.

    Args:
        pages_and_chunks (list[dict]): List of dictionaries with 'sentence_chunk'.
        model (SentenceTransformer): The embedding model to use.

    Returns:
        list[dict]: Updated list with 'embedding' for each chunk.
    """
    for item in tqdm(pages_and_chunks, desc="Creating embeddings:"):
        item["embedding"] = model.encode(item["sentence_chunk"])
    return pages_and_chunks
