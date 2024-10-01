from tqdm.auto import tqdm
import re

def split_list(input_list: list, slice_size: int) -> list[list[str]]:
    """
    Splits the input list into sublists of size slice_size (or as close as possible).

    Args:
        input_list (list): The list of sentences to be split.
        slice_size (int): The size of each chunk.

    Returns:
        list[list[str]]: A list of sublists, where each sublist contains a chunk of sentences.
    
    Example:
        A list of 17 sentences would be split into two sublists: [[10 sentences], [7 sentences]].
    """
    return [input_list[i:i + slice_size + 2 ] for i in range(0, len(input_list), slice_size)]




def process_sentence_chunks(pages_and_texts: list[dict], chunk_size: int) -> list[dict]:
    """
    Processes the text on each page by splitting sentences into chunks of a given size.

    Args:
        pages_and_texts (list[dict]): A list of dictionaries, where each dictionary contains 
                                      a 'sentences' key with the list of sentences for that page.
        chunk_size (int): The number of sentences per chunk. Default is 10.

    Returns:
        list[dict]: The updated list of dictionaries with 'sentence_chunks' and 'num_chunks' keys added.
    """
    for item in tqdm(pages_and_texts, desc="Splitting sentences into chunks"):
        # Split sentences into chunks
        item["sentence_chunks"] = split_list(input_list=item["sentences"], slice_size=chunk_size)
        
        # Store the number of chunks
        item["num_chunks"] = len(item["sentence_chunks"])

    return pages_and_texts




def join_and_clean_chunk(sentence_chunk: list[str]) -> str:
    """
    Joins a list of sentences into a single string and performs basic cleaning.

    Args:
        sentence_chunk (list[str]): A list of sentences to be joined and cleaned.
    
    Returns:
        str: The joined and cleaned sentence chunk.
    """
    # Join sentences into a single string and replace multiple spaces with one
    joined_sentence_chunk = " ".join(sentence_chunk).replace("  ", " ").strip()
    
    # Add a space after full stops if followed by a capital letter
    cleaned_chunk = re.sub(r'\.([A-Z])', r'. \1', joined_sentence_chunk)
    
    return cleaned_chunk



def process_chunks(pages_and_texts: list[dict]) -> list[dict]:
    """
    Processes sentence chunks for each page and generates statistics for each chunk.

    Args:
        pages_and_texts (list[dict]): A list of dictionaries where each dictionary contains 
                                      'sentence_chunks' for each page.

    Returns:
        list[dict]: A list of dictionaries with chunk details like page number, sentence chunk, 
                    character count, word count, and token count.
    """
    pages_and_chunks = []

    for item in tqdm(pages_and_texts, desc="Processing sentence chunks"):
        for sentence_chunk in item["sentence_chunks"]:
            chunk_dict = {
                "page_number": item["page_number"],
                "sentence_chunk": join_and_clean_chunk(sentence_chunk),
                "chunk_char_count": len(join_and_clean_chunk(sentence_chunk)),
                "chunk_word_count": len(join_and_clean_chunk(sentence_chunk).split(" ")),
                "chunk_token_count": len(join_and_clean_chunk(sentence_chunk)) / 4  # Approximate token count
            }
            pages_and_chunks.append(chunk_dict)

    return pages_and_chunks
