# modules/utils.py
from sentence_transformers import SentenceTransformer
import yaml
import torch
import numpy as np
import pandas as pd

device = "cuda" if torch.cuda.is_available() else "cpu"


def load_config(config_path):
    """
    Load configuration from a YAML file.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config



def embedding_model(device="cpu"):
    """
    Initialising the model
    """
    return SentenceTransformer("all-mpnet-base-v2", device=device, tokenizer_kwargs={'clean_up_tokenization_spaces': True})



def save_embeddings(embeddings, filepath):
    """
    Save embeddings to a file.
    """
    df_embeds = pd.DataFrame(embeddings)
    df_embeds.to_csv(filepath, index=False)
    # with open(filepath, 'wb') as f:
    #     pickle.dump(embeddings, f)



def load_embeddings(csv_path: str):
    """
    Utility function to load embeddings and convert them to a tensor.
    
    Args:
        csv_path (str): The path to the CSV file containing text chunks and embeddings.
    
    Returns:
        pages_and_chunks (list of dict): List of dictionaries where each dict contains a text chunk and its corresponding embedding.
        embeddings (torch.Tensor): Tensor of embeddings converted from NumPy arrays.
    """
    # Load the CSV file into a DataFrame
    text_chunks_and_embedding_df = pd.read_csv(csv_path)
    
    # Convert embedding column back to NumPy array
    text_chunks_and_embedding_df["embedding"] = text_chunks_and_embedding_df["embedding"].apply(
        lambda x: np.fromstring(x.strip("[]"), sep=" ")
    )
    
    # Convert DataFrame to list of dicts
    pages_and_chunks = text_chunks_and_embedding_df.to_dict(orient="records")
    
    # Convert embeddings to torch tensor and move to device
    embeddings = torch.tensor(
        np.array(text_chunks_and_embedding_df["embedding"].tolist()), 
        dtype=torch.float32).to(device)
    
    return pages_and_chunks, embeddings

def cosine_similarity_tensor(tensor1: torch.Tensor, tensor2: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """
    Compute cosine similarity between two tensors.
    
    Args:
    tensor1 (torch.Tensor): First input tensor. Shape can be (n, d) or (d,).
    tensor2 (torch.Tensor): Second input tensor. Shape can be (m, d) or (d,).
    eps (float): Small value to avoid division by zero. Default is 1e-8.
    
    Returns:
    torch.Tensor: Cosine similarity. Shape will be (n, m), (n,), or (,) depending on input shapes.
    """
    # Ensuring both tensors are at least 2D
    if tensor1.dim() == 1:
        tensor1 = tensor1.unsqueeze(0)
    if tensor2.dim() == 1:
        tensor2 = tensor2.unsqueeze(0)
    
    # Compute dot product
    dot_product = torch.mm(tensor1, tensor2.t())
    
    # Compute L2 norms
    norm1 = torch.sqrt(torch.sum(tensor1 ** 2, dim=1)).unsqueeze(1)
    norm2 = torch.sqrt(torch.sum(tensor2 ** 2, dim=1)).unsqueeze(0)
    
    # Compute cosine similarity
    cos_sim = dot_product / (norm1 * norm2 + eps)
    
    # If both inputs were 1D, return a scalar
    if tensor1.size(0) == 1 and tensor2.size(0) == 1:
        return cos_sim.item()
    
    print(cos_sim.squeeze().shape)
    
    return cos_sim.squeeze()

def clean_text(data):
    """
    Recursively cleans all strings within a nested dictionary by removing non-breaking spaces (\xa0) 
    and other artifacts, and replaces them with regular spaces.
    
    Args:
        data (dict): The dictionary containing the text to be cleaned.
    
    Returns:
        dict: The cleaned dictionary with non-breaking spaces replaced by regular spaces.
    """
    # Traverse the dictionary
    for key, value in data.items():
        if isinstance(value, dict):  # If the value is another dictionary, apply the function recursively
            data[key] = clean_text(value)
        elif isinstance(value, str):  # If the value is a string, clean it
            # Replace non-breaking spaces with regular spaces
            data[key] = value.replace(u'\xa0', u' ')
    return data