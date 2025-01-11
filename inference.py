import json
import re
import time
from appconfig import settings
import sqlite3
import gc
import streamlit as st
from document_processor import DocumentProcessor
from extractor import extract_pdf_from_db
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc
from lightrag import LightRAG, QueryParam
import numpy as np


async def async_task(task_function, *args):
    """
    Run an asynchronous task with arguments.
    """
    return await task_function(*args)


process_document = DocumentProcessor()

# async def llm_model_func(
#     prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
# ) -> str:
#     # Perform the API call
#     raw_result = await openai_complete_if_cache(
#         "solar-mini",
#         prompt,
#         system_prompt=system_prompt,
#         history_messages=history_messages,
#         api_key=settings.upstage_api_key,
#         base_url="https://api.upstage.ai/v1/solar",
#         **kwargs
#     )
    
#     # Check if keyword extraction is requested
#     if keyword_extraction:
#         # Generate keywords using LightRAG
#         kw_prompt_result = raw_result
#         print(f"Raw Keyword Output: {kw_prompt_result}")

#         # Clean and parse the keyword result
#         kw_prompt_json = clean_and_parse_json(kw_prompt_result)
#         print(f"Type of kw_prompt_json: {type(kw_prompt_json)}")
        
#         if not kw_prompt_json:
#             print("Skipping due to invalid JSON")
#             return ""
        
#         # Log the parsed keyword JSON
#         print(f"Parsed Keyword Prompt: {kw_prompt_json}")
        
#         # Convert the dictionary to a JSON-formatted string before returning
#         kw_prompt_json_str = json.dumps(kw_prompt_json)
#         return kw_prompt_json_str  # Return as a string
        
#     return raw_result  # Return the original result if not for keyword extraction


# async def embedding_func(texts: list[str]) -> np.ndarray:
#     return await openai_embedding(
#         texts,
#         model="solar-embedding-1-large-query",
#         api_key=settings.upstage_api_key,
#         base_url="https://api.upstage.ai/v1/solar"
#     )

# async def process_all_files_in_section(file_name, section, text_content: str):
#     """
#     Process all files in the given section by extracting text, creating embeddings,
#     and inserting the content into LightRAG for entity extraction and auto-query generation.
#     """
#     import logging
#     logging.basicConfig(level=logging.INFO)

#     logging.info(f"Processing file: {file_name}")
#     logging.info(f"Type of text_content: {type(text_content)}")

#     try:
#         if not isinstance(text_content, str):
#             raise ValueError("text_content must be a string")

#         rag = LightRAG(
#             working_dir="./analysis_workspace",
#             llm_model_func=llm_model_func,
#             embedding_func=EmbeddingFunc(
#                 embedding_dim=4096,
#                 max_token_size=8192,
#                 func=embedding_func
#             )
#         )

#         await rag.ainsert(text_content)
#         placeholder = st.empty()
#         placeholder.write(f"Processed and inserted file '{file_name}' successfully.")
#         time.sleep(5)
#         placeholder.empty()
#     except Exception as e:
#         logging.error(f"Error: {e}")
#         return f"Error processing file '{file_name}': {e}"
#     finally:
#         gc.collect()



        
        
# async def retrieve_all_files_in_section(query, section):
#     """
#     Process all files in the given section by extracting text, creating embeddings,
#     and inserting the content into GraphRAG for entity extraction and auto-query generation.
#     """
#     conn = sqlite3.connect("files.db", check_same_thread=False)
#     cursor = conn.cursor()

#     cursor.execute(f"SELECT file_name, file_content FROM {section}")
#     files = cursor.fetchall()

#     if not files:
#         return f"No files found in section {section}."

#     group_response = []
#     for file_name, file_content in files:
#         # Extract text from the PDF or file content
#         text_file_path, text_content = extract_pdf_from_db(file_name, section)
#         # print(f"Text Content for {file_name}: {text_content[:500]}")  # Log snippet

#         # Initialize GraphRAG with valid working directory
#         rag = LightRAG(
#             working_dir="./analysis_workspace",
#             llm_model_func=llm_model_func,
#             embedding_func=EmbeddingFunc(
#                 embedding_dim=4096,
#                 max_token_size=8192,
#                 func=embedding_func
#             )
#         )

#         # Await the asynchronous query
#         print(f"Query: {query}")
#         result = await rag.aquery(query)
#         print(f"Result for {file_name}: {result}")
#         response_content = result

#         if response_content == "Sorry, I'm not able to provide an answer to that question.":
#             print(f"Skipped response for {file_name}: {response_content}")
#         else:
#             group_response.append(response_content)

#     return "\n".join(group_response)


# def clean_and_parse_json(raw_json):
#     """
#     Fix and parse invalid JSON strings with double curly braces.
#     Args:
#         raw_json (str): The raw JSON string to be fixed.
#     Returns:
#         dict: Parsed JSON as a dictionary.
#     """
#     try:
#         # Replace double curly braces with single curly braces
#         fixed_json = raw_json.replace("{{", "{").replace("}}", "}")
#         return json.loads(fixed_json)
#     except json.JSONDecodeError as e:
#         print(f"JSON parsing error: {e}. Raw data: {raw_json}")
#         return None


import os
import logging
import shutil

logging.basicConfig(level=logging.INFO)

# Helper Function to Clean and Parse JSON
def clean_and_parse_json(raw_json):
    try:
        fixed_json = raw_json.replace("{{", "{").replace("}}", "}")
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {e}. Raw data: {raw_json}")
        return None

# Asynchronous LLM Model Function
async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    raw_result = await openai_complete_if_cache(
        "solar-mini",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=settings.upstage_api_key,
        base_url="https://api.upstage.ai/v1/solar",
        **kwargs
    )

    if keyword_extraction:
        kw_prompt_json = clean_and_parse_json(raw_result)
        if not kw_prompt_json:
            return "Error: Unable to extract keywords."
        return json.dumps(kw_prompt_json)

    return raw_result

# Asynchronous Embedding Function
async def embedding_func(texts: list[str]) -> np.ndarray:
    embeddings = await openai_embedding(
        texts,
        model="solar-embedding-1-large-query",
        api_key=settings.upstage_api_key,
        base_url="https://api.upstage.ai/v1/solar"
    )
    if embeddings is None:
        logging.error("Received empty embeddings from API.")
        return np.array([])
    return embeddings

# Process Files in a Section
async def process_all_files_in_section(file_name, section, text_content: str):
    try:
        if not isinstance(text_content, str):
            raise ValueError("text_content must be a string")

        # Create unique working directory for the file
        working_dir = f"./analysis_workspace/{section}/{file_name.split('.')[0]}"
        os.makedirs(working_dir, exist_ok=True)

        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=4096,
                max_token_size=8192,
                func=embedding_func
            )
        )

        await rag.ainsert(text_content)
        placeholder = st.empty()
        placeholder.success(f"Processed and inserted file '{file_name}' successfully.")
        time.sleep(5)
        placeholder.empty()
    except Exception as e:
        logging.error(f"Error processing file '{file_name}': {e}")
        return f"Error processing file '{file_name}': {e}"
    finally:
        gc.collect()

# Retrieve and Query Files in a Section
async def retrieve_all_files_in_section(query, section):
    if not isinstance(query, str) or not query.strip():
        return "Error: Query must be a non-empty string."

    conn = sqlite3.connect("files.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(f"SELECT file_name, file_content FROM {section}")
    files = cursor.fetchall()

    if not files:
        return f"No files found in section '{section}'."

    group_response = []

    for file_name, file_content in files:
        text_file_path, text_content = extract_pdf_from_db(file_name, section)

        # Create unique working directory for the file
        working_dir = f"./analysis_workspace/{section}/{file_name.split('.')[0]}"
        os.makedirs(working_dir, exist_ok=True)

        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=4096,
                max_token_size=8192,
                func=embedding_func
            )
        )

        # Query LightRAG for this file
        result = await rag.aquery(query, param=QueryParam("local"))
        if result != "Sorry, I'm not able to provide an answer to that question.":
            group_response.append(result)
        else:
            logging.warning(f"No relevant result for file: {file_name} in section: {section}")

    return "\n".join(group_response)

# Clear Old Data for a Section
def clear_section_data(section):
    section_dir = f"./analysis_workspace/{section}"
    if os.path.exists(section_dir):
        shutil.rmtree(section_dir)
        logging.info(f"Cleared data for section: {section}")
    os.makedirs(section_dir, exist_ok=True)


# async def llm_model_func(
#     prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
# ) -> str:
#     # Perform the API call
#     raw_result = await openai_complete_if_cache(
#         "solar-mini",
#         prompt,
#         system_prompt=system_prompt,
#         history_messages=history_messages,
#         api_key=settings.upstage_api_key,
#         base_url="https://api.upstage.ai/v1/solar",
#         **kwargs
#     )
    
#     # Check if keyword extraction is requested
#     if keyword_extraction:
#         # Generate keywords using LightRAG
#         kw_prompt_result = raw_result
#         print(f"Raw Keyword Output: {kw_prompt_result}")

#         # Clean and parse the keyword result
#         kw_prompt_json = clean_and_parse_json(kw_prompt_result)
#         print(f"Type of kw_prompt_json: {type(kw_prompt_json)}")
        
#         if not kw_prompt_json:
#             print(f"Error: Unable to parse keywords from raw result: {kw_prompt_result}")
#             return "Error: Unable to extract keywords."
        
#         # Log the parsed keyword JSON
#         print(f"Parsed Keyword Prompt: {kw_prompt_json}")
        
#         # Convert the dictionary to a JSON-formatted string before returning
#         kw_prompt_json_str = json.dumps(kw_prompt_json)
#         return kw_prompt_json_str  # Return as a string
        
#     return raw_result  # Return the original result if not for keyword extraction


# async def embedding_func(texts: list[str]) -> np.ndarray:
#     embeddings = await openai_embedding(
#         texts,
#         model="solar-embedding-1-large-query",
#         api_key=settings.upstage_api_key,
#         base_url="https://api.upstage.ai/v1/solar"
#     )
    
#     # Check embedding dimensions
#     if embeddings is not None:
#         print(f"Embedding Shape: {np.shape(embeddings)}")
#         return embeddings
#     else:
#         print("Error: Received empty embeddings from API.")
#         return np.array([])  # Return an empty array as fallback


# async def process_all_files_in_section(file_name, section, text_content: str):
#     """
#     Process all files in the given section by extracting text, creating embeddings,
#     and inserting the content into LightRAG for entity extraction and auto-query generation.
#     """
#     import logging
#     logging.basicConfig(level=logging.INFO)

#     logging.info(f"Processing file: {file_name}")
#     logging.info(f"Type of text_content: {type(text_content)}")

#     try:
#         if not isinstance(text_content, str):
#             raise ValueError("text_content must be a string")

#         # Log extracted text snippet
#         logging.info(f"Extracted Text (Snippet): {text_content[:500]}")

#         rag = LightRAG(
#             working_dir=f"./analysis_workspace/{section}/{file_name.split('.')[0]}",
#             llm_model_func=llm_model_func,
#             embedding_func=EmbeddingFunc(
#                 embedding_dim=4096,
#                 max_token_size=8192,
#                 func=embedding_func
#             )
#         )

#         await rag.ainsert(text_content)
#         placeholder = st.empty()
#         placeholder.write(f"Processed and inserted file '{file_name}' successfully.")
#         time.sleep(5)
#         placeholder.empty()
#     except Exception as e:
#         logging.error(f"Error processing file '{file_name}': {e}")
#         return f"Error processing file '{file_name}': {e}"
#     finally:
#         gc.collect()



# async def retrieve_all_files_in_section(query, section):
#     """
#     Process all files in the given section by extracting text, creating embeddings,
#     and inserting the content into GraphRAG for entity extraction and auto-query generation.
#     """
#     if not isinstance(query, str) or not query.strip():
#         return "Error: Query must be a non-empty string."

#     conn = sqlite3.connect("files.db", check_same_thread=False)
#     cursor = conn.cursor()

#     cursor.execute(f"SELECT file_name, file_content FROM {section}")
#     files = cursor.fetchall()

#     if not files:
#         return f"No files found in section {section}."

#     group_response = []
#     for file_name, file_content in files:
#         # Extract text from the PDF or file content
#         text_file_path, text_content = extract_pdf_from_db(file_name, section)
#         # print(f"Text Content for {file_name}: {text_content[:500]}")  # Log snippet

#         # Initialize GraphRAG with valid working directory
#     rag = LightRAG(
#         working_dir=f"./analysis_workspace/{section}/{file_name.split('.')[0]}",
#         llm_model_func=llm_model_func,
#         embedding_func=EmbeddingFunc(
#             embedding_dim=4096,
#             max_token_size=8192,
#             func=embedding_func
#         )
#     )

#     # Await the asynchronous query
#     print(f"Query: {query}")
#     result = await rag.aquery(query)
#     # print(f"Result for {file_name}: {result}")
#     response_content = result

#     if response_content == "Sorry, I'm not able to provide an answer to that question.":
#         print(f"Skipped response for {file_name}: {response_content}")
#     else:
#         group_response.append(response_content)

#     return "\n".join(group_response)



# def clean_and_parse_json(raw_json):
#     """
#     Fix and parse invalid JSON strings with double curly braces.
#     Args:
#         raw_json (str): The raw JSON string to be fixed.
#     Returns:
#         dict: Parsed JSON as a dictionary.
#     """
#     try:
#         # Replace double curly braces with single curly braces
#         fixed_json = re.sub(r"\{\{|\}\}", lambda m: "{" if m.group(0) == "{{" else "}", raw_json)
#         return json.loads(fixed_json)
#     except json.JSONDecodeError as e:
#         print(f"JSON parsing error: {e}. Raw data: {raw_json}")
#         return None  # Return None if parsing fails

