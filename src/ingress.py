import fitz
import streamlit as st
import sqlite3
import streamlit as st
import traceback
from src.constant import SECTION_KEYWORDS
from src.document_processor import DocumentProcessor
from src.db_helper import insert_file_metadata, delete_file, initialize_database, reload_session_state, get_uploaded_sections
import time
from src.rag.inference import process_all_files_in_section



async def ingress_file_doc(file_name:str, file_path:str, section = ""):

    # Sidebar for section selection and file upload
    sections = list(SECTION_KEYWORDS.values())
    uploaded_sections = get_uploaded_sections(SECTION_KEYWORDS)
    default_section = uploaded_sections[0] if uploaded_sections else sections[0]
    print(default_section)
    section = default_section

    table_name = next((key for key, value in SECTION_KEYWORDS.items() if value == section), None)
    print(f"Table name: {table_name}")
    if not table_name:
        print("No table mapping found for section")
        return

    try:
        conn = sqlite3.connect("files.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(f"SELECT file_name FROM {table_name} WHERE file_name = ?", (file_name,))
        existing_file = cursor.fetchone()

        if existing_file:
            return f"File '{file_name}' already exists in the '{section}' section."
        else:
            text_content = []
            with fitz.open(file_path) as pdf:
                for page in pdf:
                    text_content.append(page.get_text())
                text_content = " ".join(text_content)
            insert_file_metadata(file_name, table_name, text_content)
            return await process_all_files_in_section(file_name, table_name, text_content)

    except Exception as e:
        return f"Error processing files: {e}"
        traceback.print_exc()
    finally:
        conn.close()

        
    


        
        
        
# def ingress_file_s(file_name:str, file_path:str):
#     initialize_session_state()

#     # Sidebar for section selection and file upload
#     sections = list(SECTION_KEYWORDS.values())
#     uploaded_sections = get_uploaded_sections(SECTION_KEYWORDS)
#     default_section = uploaded_sections[0] if uploaded_sections else sections[0]
    

#     section = st.sidebar.selectbox("Select a document section:", options=sections, index=sections.index(default_section))
#     table_name = next((key for key, value in SECTION_KEYWORDS.items() if value == section), None)

#     if not table_name:
#         st.error("No table mapping found for section")
#         return

#     uploaded_files = st.sidebar.file_uploader(f"Upload files to the '{section}' section", type=["pdf", "txt"], accept_multiple_files=True)

#     if uploaded_files:
#         with st.spinner("Processing and uploading files..."):
#             try:
#                 for file in uploaded_files:
#                     conn = sqlite3.connect("files.db", check_same_thread=False)
#                     cursor = conn.cursor()
#                     cursor.execute(f"SELECT file_name FROM {table_name} WHERE file_name = ?", (file.name,))
#                     existing_file = cursor.fetchone()

#                     if existing_file:
#                         st.sidebar.info(f"File '{file.name}' already exists in the '{section}' section.")
#                     else:
#                         file_content = file.read()
#                         insert_file_metadata(file.name, table_name, file_content)
#                         placeholder = st.empty()
#                         placeholder.success(f"File '{file.name}' uploaded successfully!")
#                         time.sleep(5)
#                         placeholder.empty()

#             except Exception as e:
#                 st.error(f"Error processing files: {e}")
#                 traceback.print_exc()
#             finally:
#                 conn.close()

#     # Chatbot interface
#     st.header("Chat with the Bot")
#     user_input = st.text_input("Ask your question:")

#     if st.button("Send"):
#         with st.spinner("Processing all files in the selected section..."):
#             try:
#                 process_all_files_in_section(table_name)
#             except Exception as e:
#                 st.error(f"Error processing files for section '{section}': {e}")
#                 traceback.print_exc()

#         if table_name in st.session_state.get("grag_instances", {}):
#             grag = st.session_state["grag_instances"][table_name]
#             if user_input.strip():
#                 try:
#                     response = retrieve_all_files_in_section(user_input, table_name)
#                     st.session_state.chat_history.append(("You", user_input))
#                     st.session_state.chat_history.append(("Bot", response))
#                 except Exception as e:
#                     st.error(f"Error during chatbot interaction: {e}")
#             else:
#                 st.info("Please enter a question to interact with the bot.")
#         else:
#             st.error("No GraphRAG instance found for this section. Please process files first.")

#     # Display chat history
#     if st.session_state.chat_history:
#         st.write("### Chat History")
#         for role, message in st.session_state.chat_history[-10:]:
#             st.write(f"**{role}:** {message}")
            
#     st.sidebar.write("### Uploaded Files")
#     try:
#         conn = sqlite3.connect("files.db", check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(f"SELECT file_name FROM {table_name};")
#         uploaded_files_list = [file[0] for file in cursor.fetchall()]

#         if uploaded_files_list:
#             for file_name in uploaded_files_list:
#                 delete_key = f"delete_{table_name}_{file_name}"
#                 col1, col2 = st.sidebar.columns([3, 1])
#                 with col1:
#                     st.sidebar.write(file_name)
#                 with col2:
#                     if st.sidebar.button("Delete", key=delete_key):
#                         try:
#                             delete_file(file_name, table_name)
#                             st.sidebar.success(f"File '{file_name}' deleted successfully!")
#                         except Exception as e:
#                             st.error(f"Failed to delete file '{file_name}': {e}")
#         else:
#             st.sidebar.info("No files uploaded for this section.")
#     except Exception as e:
#         st.sidebar.error(f"Failed to retrieve files: {e}")
        
#     # Track uploaded sections
#     # --- Sidebar: Breadcrumb Display ---
#     if "uploaded_sections" not in st.session_state:
#         st.session_state.uploaded_sections = set()

#     if uploaded_files:
#         st.session_state.uploaded_sections.add(section)

#     if st.session_state.uploaded_sections:
#         breadcrumb_text = " > ".join(sorted(st.session_state.uploaded_sections))
#         st.sidebar.info(f"📂 Sections with uploads: {breadcrumb_text}")