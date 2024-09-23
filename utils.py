import re

def clean_text(text):
    """Clean and preprocess text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text)
    return text

def format_response(response):
    """Format the chatbot response for better readability."""
    sentences = re.split(r'(?<=[.!?])\s+', response)
    formatted_response = '\n'.join(sentences)
    return formatted_response
