import sqlite3
import fitz
import tempfile


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

        text_content = result[0]  # Assume the content is already plain text
        print(f"Retrieved text content: {text_content}...")  # Print a snippet for debugging

        # Save the text to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix=file_name, mode="w", encoding="utf-8")
        temp_file.write(text_content)
        temp_file.close()

        return temp_file.name, text_content  # Return the file path and content

    except Exception as e:
        print(f"Error retrieving text content: {e}")
        raise
    finally:
        conn.close()
