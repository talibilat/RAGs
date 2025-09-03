import fitz
from tqdm.auto import tqdm
from spacy.lang.en import English

# Initialize the SpaCy NLP model and add the sentencizer to the pipeline
nlp = English()
nlp.add_pipe("sentencizer")

def text_formatter(text: str) -> str:
    """
    Performs basic formatting on the given text, such as replacing newlines and trimming spaces.
    
    Args:
        text (str): The input text that needs to be formatted.
    
    Returns:
        str: The formatted text.
    """
    cleaned_text = text.replace("\n", " ").strip()
    return cleaned_text




def open_and_read_pdf(pdf_path: str) -> list[dict]:
    """
    Opens a PDF file, extracts text content page by page, and collects statistics.

    Args:
        pdf_path (str): The file path to the PDF document.

    Returns:
        list[dict]: A list of dictionaries for each page with its text content and relevant statistics.
                    Includes page number, character count, word count, sentence count, and token count.
    """
    doc = fitz.open(pdf_path)  # Open the PDF document
    pages_and_texts = []

    for page_number, page in tqdm(enumerate(doc), desc="Reading PDF pages"):  
        text = page.get_text()  # Extract text from the page
        formatted_text = text_formatter(text)

        # Append page details including text and various counts
        pages_and_texts.append({
            "page_number": page_number,
            "page_char_count": len(formatted_text),
            "page_word_count": len(formatted_text.split(" ")),
            "page_sentence_count_raw": len(formatted_text.split(". ")),
            "page_token_count": len(formatted_text) // 4,
            "text": formatted_text
        })

    return pages_and_texts





def text_to_sentences(pages_and_texts: list[dict]) -> list[dict]:
    """
    Processes a list of dictionaries, each containing page text. Splits the text into sentences
    using the SpaCy NLP pipeline and counts the sentences.

    Args:
        pages_and_texts (list[dict]): A list of dictionaries, each having a 'text' key.
    
    Returns:
        list[dict]: The updated list of dictionaries, with sentences and SpaCy-based sentence counts added.
    """
    for item in tqdm(pages_and_texts, desc="Processing text into sentences"):
        # Use SpaCy's NLP pipeline to split the text into sentences
        item["sentences"] = list(nlp(item["text"]).sents)

        # Convert the sentences to strings
        item["sentences"] = [str(sentence) for sentence in item["sentences"]]

        # Add the sentence count to the dictionary
        item["page_sentence_count_spacy"] = len(item["sentences"])

    return pages_and_texts
