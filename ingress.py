import sqlite3
import time
import traceback
import streamlit as st
from constant import SECTION_KEYWORDS
import traceback
from db_helper import insert_file_metadata
from inference import process_all_files_in_section
from app import select_section
from document_processor import DocumentProcessor

process_document = DocumentProcessor()


# async def ingress_file_doc(file_name:str, file_path:str, section = ""):
#     section, table_name = select_section()

#     table_name = next((key for key, value in SECTION_KEYWORDS.items() if value == section), None)
#     print(f"Table name: {table_name}")
#     if not table_name:
#         print("No table mapping found for section")
#         return

#     try:
#         conn = sqlite3.connect("files.db", check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(f"SELECT file_name FROM {table_name} WHERE file_name = ?", (file_name,))
#         existing_file = cursor.fetchone()

#         if existing_file:
#             return f"File '{file_name}' already exists in the '{section}' section."
#         else:
#             text_content = []
#             with fitz.open(file_path) as pdf:
#                 for page in pdf:
#                     text_content.append(page.get_text())
#                 text_content = " ".join(text_content)
#             insert_file_metadata(file_name, table_name, text_content)
#             return await process_all_files_in_section(file_name, table_name, text_content)

#     except Exception as e:
#         traceback.print_exc()
#         return f"Error processing files: {e}"
#     finally:
#         conn.close()


async def ingress_file_doc(file_name: str, file_path: str = None, web_links: list = None, section = ""):
    section, table_name = select_section()
    try:
        # Map section to table name
        table_name = next((key for key, value in SECTION_KEYWORDS.items() if value == section), None)
        if not table_name:
            return {"error": "No table mapping found for the given section."}

        # Connect to the database
        conn = sqlite3.connect("files.db", check_same_thread=False)
        cursor = conn.cursor()

        # Check if the file or web link already exists
        if file_path:
            cursor.execute(f"SELECT file_name FROM {table_name} WHERE file_name = ?", (file_name,))
            if cursor.fetchone():
                placeholder = st.sidebar.empty()
                placeholder.write(f"File '{file_name}' already exists in the '{section}' section.")
                time.sleep(5)
                placeholder.empty()
                
        elif web_links:
            for link in web_links:
                cursor.execute(f"SELECT file_name FROM {table_name} WHERE file_name = ?", (link,))
                if cursor.fetchone():
                    placeholder = st.sidebar.empty()
                    placeholder.write(f"Web link '{link}' already exists in the '{section}' section.")
                    time.sleep(5)
                    placeholder.empty()

        # Process file content
        text_content = []
        if file_path:
            if file_path.endswith(".pdf"):
                text_content.append(process_document.extract_text_from_pdf(file_path))
            elif file_path.endswith(".txt"):
                text_content.append(process_document.extract_txt_content(file_path))
            else:
                return {"error": "Unsupported file format."}

        # Process web links
        if web_links:
            for link in web_links:
                web_content = process_document.process_webpage(link)
                if web_content:
                    text_content.append(web_content)

        # Insert metadata into the database
        for content in text_content:
            insert_file_metadata(file_name or link, table_name, content)

        # Further processing
        results = []
        for content in text_content:
            result = await process_all_files_in_section(file_name or link, table_name, content)
            results.append(result)
            placeholder = st.empty()
            placeholder.write(f"File {file_name} has been processed and inserted successfully")
            time.sleep(5)
            placeholder.empty()

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        conn.close()





