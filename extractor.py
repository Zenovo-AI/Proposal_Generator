import sqlite3
import fitz
import tempfile
from charset_normalizer import detect

def decode_file_content(file_content):
    """
    Detect and decode file content to a string.
    Args:
        file_content (bytes): The raw binary content of the file.
    Returns:
        str: Decoded text content.
    """
    # Detect encoding
    detected = detect(file_content)
    encoding = detected['encoding']

    if encoding:
        return file_content.decode(encoding)
    else:
        raise ValueError("Failed to detect encoding")
    

def extract_pdf_from_db(file_name, section):
    """
    Retrieve and save text content from the database to a temporary file.

    Args:
        file_name (str): Name of the file in the database.
        section (str): Section/table where the file is stored.

    Returns:
        Tuple[str, str]: Path to the saved temporary text file and its content.
    """
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    try:
        # Retrieve the text content from the database
        cursor.execute(f"SELECT file_content FROM {section} WHERE file_name = ?", (file_name,))
        result = cursor.fetchone()

        if not result:
            raise ValueError(f"File '{file_name}' not found in section '{section}'.")

        file_content = result[0]  # Retrieve file content

        # Decode file content
        if isinstance(file_content, bytes):
            file_content = decode_file_content(file_content)

        # Save the text to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix=file_name, mode="w", encoding="utf-8")
        temp_file.write(file_content)
        temp_file.close()

        return temp_file.name, file_content

    except Exception as e:
        print(f"Error retrieving text content: {e}")
        raise
    finally:
        conn.close()

