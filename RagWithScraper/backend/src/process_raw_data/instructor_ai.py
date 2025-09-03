import os
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
import dotenv

dotenv.load_dotenv()

# Initialize the OpenAI client with instructor patching.
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4o")
client = instructor.patch(OpenAI(api_key=api_key))

class FAQItem(BaseModel):
    """Model for FAQ item with question and answer."""
    question: str = Field(..., description="The question from the FAQ")
    answer: str = Field(..., description="The answer to the question")
    is_faq: bool = Field(..., description="Whether this content is truly a FAQ item")
    confidence: float = Field(..., description="Confidence score between 0-1 of this being a FAQ item")

class FAQPage(BaseModel):
    """Model for a page containing FAQ items."""
    url: str = Field(..., description="URL of the page")
    title: str = Field(..., description="Title of the page")
    is_faq_page: bool = Field(..., description="Whether this page contains FAQ content")
    faq_items: List[FAQItem] = Field(default=[], description="List of FAQ items found on the page")

def extract_faq_from_content(url: str, title: str, content: str) -> FAQPage:
    """
    Extract FAQ items from page content using the patched OpenAI client.
    
    Args:
        url: The URL of the page.
        title: The title of the page.
        content: The content (markdown or HTML) of the page.
        
    Returns:
        FAQPage object containing the extracted FAQ items.
    """
    try:
        # Use OpenAI to extract FAQ content.
        faq_page = client.chat.completions.create(
            model=model,
            response_model=FAQPage,
            messages=[
                {"role": "system", "content": """You are an AI assistant that extracts FAQ context from html or markdown file.
                                             You are not allowed to change anything in the text. 
                                             You will be given an html or markdown webpage which should contain one question and one detailed answer
                                             Your Task:
                                             You have to identify one question and one detailed answer and respond without changing any word from it
                                             You need to strictly determine if a page is a true FAQ page with proper questions and detailed answers.
                                             Pages that only contain links should NOT be considered FAQ pages.
                                             A true FAQ page should have clearly formatted questions followed by comprehensive answers that provide value."""
                                             },
                {"role": "user", "content": f"Extract FAQ content from this page:\n\nURL: {url}\nTitle: {title}\n\nContent:\n{content}"}
            ]
        )
        return faq_page
    except Exception as e:
        # Return an empty FAQPage upon error.
        return FAQPage(url=url, title=title, is_faq_page=False, faq_items=[])