from typing import List
import pandas as pd
from loguru import logger
from instructor_ai import FAQPage 
import os
import sys
import dotenv

# Load environment variables
dotenv.load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.logger import setup_logger
# from src.process_raw_data.extract_faq_from_content import extract_faqs_from_pages
from src.process_raw_data.generate_dataset_using_regex import extract_faqs_from_pages_regex

logger = setup_logger(name="save_faq_to_csv", log_to_file=True)

def save_faqs_to_csv(faq_pages: List[dict], output_path: str):
    """
    Save extracted FAQ items into a CSV file.
    
    Args:
        faq_pages: List of dictionaries containing FAQ data.
        output_path: Path to save the CSV file.
    """
    logger.info(f"Saving FAQ items to CSV: {output_path}")
    logger.info(f"Received {len(faq_pages)} FAQ pages to process")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    rows = []
    for page in faq_pages:
        # Handle both dictionary and FAQPage object formats
        if isinstance(page, dict):
            logger.debug(f"Processing dictionary FAQ: {page['page_title']}")
            rows.append({
                "page_url": page["page_url"],
                "page_title": page["page_title"],
                "question": page["question"],
                "answer": page["answer"],
                "confidence": page["confidence"]
            })
        else:
            # Original FAQPage object handling
            logger.debug(f"Processing FAQ items from page: {page.page_url}")
            if page.is_faq_page:
                for item in page.faq_items:
                    if item.is_faq:
                        rows.append({
                            "page_url": page.page_url,
                            "page_title": page.page_title,
                            "question": item.question,
                            "answer": item.answer,
                            "confidence": item.confidence
                        })
            else:
                logger.debug(f"Skipping non-FAQ page: {page.page_url}")
    
    if rows:
        df = pd.DataFrame(rows)
        logger.info(f"Created DataFrame with {len(df)} rows and columns: {', '.join(df.columns)}")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(rows)} FAQ items to {output_path}")
    else:
        logger.warning("No FAQ items found to save to CSV")

if __name__ == "__main__":
    logger.info("Starting FAQ extraction and CSV creation process")
    faq_pages = extract_faqs_from_pages_regex()
    logger.info(f"Extracted {len(faq_pages)} FAQ pages")
    
    # Construct output path using environment variables
    output_path = os.path.join(
        os.getenv('DATA_DIR', 'data'),
        os.getenv('FAQS_DIR', 'faqs'),
        os.getenv('CSV_FILENAME', 'faqs_regex.csv')
    )
    save_faqs_to_csv(faq_pages, output_path)