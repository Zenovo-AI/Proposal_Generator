import fitz 
import logging
import trafilatura
from utils import clean_text
import logging

logging.basicConfig(level=logging.INFO)


class DocumentProcessor:
    SECTION_KEYWORDS = {
        "Request for Proposal (RFP) Document",
        "Terms of Reference (ToR)",
        "Technical Evaluation Criteria",
        "Company and Team Profiles",
        "Environmental and Social Standards",
        "Project History and Relevant Experience",
        "Budget and Financial Documents",
        "Additional Requirements and Compliance Documents"
    }

    def __init__(self):
        pass
    
    # Helper function to read text from a TXT file
    def extract_txt_content(self, file_path):
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error reading TXT file: {e}")

    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF using PyMuPDF.
        """
        text_content = []
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text_content.append(page.get_text())
            text_content = " ".join(text_content)
        return text_content


    def process_webpage(self, url):
        """
        Processes a webpage to extract and clean its content.

        Args:
            url (str): The URL of the webpage.

        Returns:
            str: Cleaned text content from the webpage, or None if processing fails.
        """
        try:
            # Fetch the webpage content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                logging.error(f"Failed to fetch webpage: {url}")
                return None

            # Extract meaningful text
            web_page = trafilatura.extract(downloaded)
            if not web_page:
                logging.error(f"Failed to extract content from webpage: {url}")
                return None

            # Clean and return the text
            cleaned_text = clean_text(web_page)
            return cleaned_text

        except Exception as e:
            logging.error(f"Error processing webpage {url}: {e}")
            return None