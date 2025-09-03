import re

def generate_system_prompt():
    """
    Generate the system prompt for the assistant.
    """
    prompt = (
        "You are a helpful assistant that answers questions based on the provided context. "
        "Break down the question into small parts and answer each part separately. "
        "Do not use any external knowledge or make up information. "
        "If the answer is not in the context, say 'The answer is not found in the provided document.'."
    )
    return prompt

def extract_information_from_context(context, query):
    """
    Extract specific information (e.g., dates) from the context based on the query.
    """
    # Check if the query mentions "date"
    if "date" in query.lower():
        # Patterns to match different date formats
        date_patterns = [
            r'(\b\w+\s\d{1,2},\s\d{4}\b)',  # e.g., January 1, 2023
            r'(\b\d{1,2}/\d{1,2}/\d{4}\b)',  # e.g., 01/01/2023
            r'(\b\d{1,2}-\d{1,2}-\d{4}\b)',  # e.g., 01-01-2023
            r'(\b\d{4}-\d{1,2}-\d{1,2}\b)',  # e.g., 2023-01-01
            r'(\b\d{1,2}\s\w+\s\d{4}\b)'     # e.g., 1 January 2023
        ]

        # Loop through the context to find a date match
        for key, value in context.items():
            for pattern in date_patterns:
                match = re.search(pattern, str(value), re.IGNORECASE)  # Match date patterns in context value
                if match:
                    return match.group(1)  # Return the matched date
        return "Date not found in the provided context."  # If no date is found
    else:
        return "Information not found."  # If the query doesn't mention a date
