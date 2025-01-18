import asyncio
import sqlite3
import time
from fastapi import requests
import streamlit as st
import httpx
from db_helper import delete_file, initialize_database, get_uploaded_sections
from constant import SECTION_KEYWORDS

# Document Processor Placeholder
process_document = None  # Replace with actual DocumentProcessor if used


def uploaded_files():
    """Allow users to upload PDF or TXT files."""
    return st.sidebar.file_uploader(
        "Upload PDF or TXT files", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )

def web_links():
    """Allow users to input web links."""
    return st.sidebar.text_area("Enter web links (one per line)").splitlines()

def select_section():
    """Allow users to select a document section."""
    sections = list(SECTION_KEYWORDS.values())
    section = st.sidebar.selectbox("Select a document section:", options=sections)
    table_name = next((key for key, value in SECTION_KEYWORDS.items() if value == section), None)
    return section, table_name

# Initialize session state for chat history
def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if 'initialized' not in st.session_state:
        initialize_database()
        
def process_files_and_links(files, web_links, section):
    with st.spinner("Processing..."):
        tasks = []
        for uploaded_file in files:
            tasks.append(process_file(uploaded_file, section, web_links))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(*tasks))
    st.session_state["files_processed"] = True

# This is the async function that processes the uploaded files
async def process_file(uploaded_file, section, web_links):
    try:
        # Prepare file for POST request
        file_data = {
            "file": (uploaded_file.name, uploaded_file.getvalue())
        }
        
        # Optional data
        data = {
            "section": section,
            "web_links": web_links.strip() if web_links else ""
        }
        
        # Use async HTTP client to send the request
        async with httpx.AsyncClient() as client:
            response = await client.post(" http://34.123.43.41/ingress-file", files=file_data, json=data, timeout=1800)
            
            if response.status_code == 200:
                placeholder = st.empty()
                placeholder.success(f"File {uploaded_file.name} processed successfully!")
                time.sleep(5)
                placeholder.empty()
                st.json(response.json())  # Display response from the backend
            else:
                st.error(f"Error processing file {uploaded_file.name}: {response.text}")
    
    except Exception as e:
        st.error(f"Connection error: {e}")

def main():
    # Initialize session state and set up the Streamlit UI
    initialize_session_state()
    st.title("Proposal and Chatbot System")

    # Select section and table name
    section, table_name = select_section()
    if not table_name:
        st.error("Please select a valid section to proceed.")

    # File uploader widget
    files = st.sidebar.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "txt"])

    # Optional input for web links
    web_links = st.sidebar.text_area("Enter web links (one per line)")
    
    # Check if files are already processed
    if "files_processed" not in st.session_state:
        st.session_state["files_processed"] = False

    # Process files and web links
    if (files or web_links.strip()) and not st.session_state["files_processed"]:
        process_files_and_links(files, web_links, section)
    
    if st.sidebar.button("Reset Processing"):
        st.session_state["files_processed"] = False

    # Chat Section
    st.header("Chat with the Bot")
    query = st.text_input("Ask your question:")

    if st.button("Send"):
        if query:
            with st.spinner("Retrieving your answer..."):
                try:
                    payload = {"query": query, "section": table_name}
                    with httpx.Client() as client:
                        response = client.post("http://34.123.43.41/retrieve", json=payload, timeout=1800)

                    if response.status_code == 200:
                        bot_response = response.json().get("response", "No response.")
                        st.session_state.chat_history.append(("You", query))
                        st.session_state.chat_history.append(("Bot", bot_response))
                    else:
                        st.error(f"Failed to retrieve response: {response.text}")
                except Exception as e:
                    st.error(f"Error retrieving response: {e}")

    if st.session_state.chat_history:
        st.write("### Chat History")
        for role, message in st.session_state.chat_history[-10:]:
            st.write(f"**{role}:** {message}")

    # Sidebar: Display uploaded files
    st.sidebar.write("### Uploaded Files")
    try:
        conn = sqlite3.connect("files.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(f'SELECT file_name FROM "{table_name}";')
        uploaded_files_list = [file[0] for file in cursor.fetchall()]

        if uploaded_files_list:
            for file_name in uploaded_files_list:
                delete_key = f"delete_{table_name}_{file_name}"
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    st.sidebar.write(file_name)
                with col2:
                    if st.sidebar.button("Delete", key=delete_key):
                        try:
                            delete_file(file_name, table_name)
                            st.sidebar.success(f"File '{file_name}' deleted successfully!")
                        except Exception as e:
                            st.error(f"Failed to delete file '{file_name}': {e}")
        else:
            st.sidebar.info("No files uploaded for this section.")
    except Exception as e:
        st.sidebar.error(f"Failed to retrieve files: {e}")
        
    # Sidebar: Breadcrumb Display
    uploaded_sections = get_uploaded_sections(SECTION_KEYWORDS)
    if "uploaded_sections" not in st.session_state:
        st.session_state.uploaded_sections = set()

    if files:
        st.session_state.uploaded_sections.add(section)

    if st.session_state.uploaded_sections:
        breadcrumb_text = " > ".join(sorted(st.session_state.uploaded_sections))
        st.sidebar.info(f"📂 Sections with uploads: {breadcrumb_text}")

if __name__ == "__main__":
    main()
