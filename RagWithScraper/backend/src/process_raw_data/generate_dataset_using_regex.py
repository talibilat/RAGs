import os
import json
import re
import pprint
from typing import List
from instructor_ai import FAQPage 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.logger import setup_logger


logger = setup_logger(name="extract_faq_from_content", log_to_file=True)

def extract_faqs_from_pages_regex(folder_path: str = "data/pages") -> List[dict]:
    """
    Scan the specified folder for JSON files, extract URL, title, and content (using the 'markdown'
    field if available, otherwise 'html') from each file's metadata, and run OpenAI extraction 
    to obtain FAQPage objects.
    
    Returns:
        A list of FAQPage objects.
    """
    faq_pages = []
    if not os.path.exists(folder_path):
        logger.error(f"Folder '{folder_path}' does not exist.")
        return faq_pages

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".json"):
            continue
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                page_data = json.load(f)
            metadata = page_data.get("metadata", {})
            url = metadata.get("url", "")
            title = metadata.get("title", "")
            content = page_data.get("markdown")
            content = re.sub(r'\[Skip to main content\].*?\n', '', content)
            content = re.sub(r'## Related articles[\s\S]*$', '', content)
            if not (url and title and content):
                logger.warning(f"Missing URL, title or content in file: {file_path}")
                continue
            logger.info(f"Processing file: {file_path}")            
            faq_page = {
                        "page_url": url,
                        "page_title": title,
                        "question": title,
                        "answer": content,
                        "confidence": 'N/A'
                    }
            faq_pages.append(faq_page)
        
        except Exception as e:
            logger.error(f"Error processing file '{file_path}': {e}")
    return faq_pages

extract_faqs_from_pages_regex()