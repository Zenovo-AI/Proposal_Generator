import json
import shutil
import tempfile
from src.config.appconfig import settings
import sqlite3
import gc
from src.document_processor import DocumentProcessor
from src.rag.extractor import extract_pdf_from_db
from lightrag.prompt import PROMPTS
from src.rag.helper import generate_example_queries_entities
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc
from lightrag import LightRAG
import numpy as np


process_document = DocumentProcessor()


def prepare_working_dir():
    """
    Prepare a clean temporary working directory for GraphRAG.
    """
    temp_dir = tempfile.mkdtemp()
    shutil.rmtree(temp_dir, ignore_errors=True)  # Clear any existing contents
    temp_dir = tempfile.mkdtemp()  # Recreate a fresh temporary directory
    return temp_dir

def filter_numeric_directories(working_dir):
    """
    Ensure only numeric directories are present in the working directory.
    """
    for subdir in tempfile.TemporaryDirectory()._get_next_temp_name_iterator():
        if not subdir.isdigit():
            shutil.rmtree(subdir)


def clean_working_dir(working_dir):
    """
    Ensure the working directory is clean by recreating it as an empty directory.
    """
    # Recreate the directory by removing and reinitializing it
    shutil.rmtree(working_dir, ignore_errors=True)  # Remove the directory and its contents
    tempfile.mkdtemp(dir=working_dir)  # Recreate the temporary directory        


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    # Perform the API call
    raw_result = await openai_complete_if_cache(
        "solar-mini",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=settings.upstage_api_key,
        base_url="https://api.upstage.ai/v1/solar",
        **kwargs
    )
    
    # Check if keyword extraction is requested
    if keyword_extraction:
        # Generate keywords using LightRAG
        kw_prompt_result = raw_result
        print(f"Raw Keyword Output: {kw_prompt_result}")

        # Clean and parse the keyword result
        kw_prompt_json = clean_and_parse_json(kw_prompt_result)
        print(f"Type of kw_prompt_json: {type(kw_prompt_json)}")
        
        if not kw_prompt_json:
            print("Skipping due to invalid JSON")
            return ""
        
        # Log the parsed keyword JSON
        print(f"Parsed Keyword Prompt: {kw_prompt_json}")
        
        # Convert the dictionary to a JSON-formatted string before returning
        kw_prompt_json_str = json.dumps(kw_prompt_json)
        return kw_prompt_json_str  # Return as a string
        
    return raw_result  # Return the original result if not for keyword extraction


async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embedding(
        texts,
        model="solar-embedding-1-large-query",
        api_key=settings.upstage_api_key,
        base_url="https://api.upstage.ai/v1/solar"
    )

async def process_all_files_in_section(file_name, section, text_content: str):
    """
    Process all files in the given section by extracting text, creating embeddings,
    and inserting the content into LightRAG for entity extraction and auto-query generation.
    """
    # print(f"Type of text_content: {type(text_content)}")
    # print(f"Text content preview: {text_content[:200]}")  # Displaying a snippet for verification
    
    try:
        # Ensure text_content is a string
        if not isinstance(text_content, str):
            print("Error: text_content is not a string")
            return f"Error processing files in section '{section}': text_content is not a string"

        # Initialize LightRAG with the LLM and embedding functions
        rag = LightRAG(
            working_dir="./analysis_workspace",
            llm_model_func=llm_model_func,  # Use the provided LLM model function
            embedding_func=EmbeddingFunc(
                embedding_dim=4096,  # Set the embedding dimension
                max_token_size=8192,  # Set the max token size
                func=embedding_func  # Use the provided embedding function
            )
        )

        # Insert text content into LightRAG
        await rag.ainsert(text_content)

        return f"Processed and inserted file '{file_name}' successfully."

    except Exception as e:
        print(f"Error: {e}")
        return f"Error processing files in section '{section}': {e}"

    finally:
        gc.collect()


        
        
async def retrieve_all_files_in_section(query, section):
    """
    Process all files in the given section by extracting text, creating embeddings,
    and inserting the content into GraphRAG for entity extraction and auto-query generation.
    """
    conn = sqlite3.connect("files.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(f"SELECT file_name, file_content FROM {section}")
    files = cursor.fetchall()

    if not files:
        return f"No files found in section {section}."

    group_response = []
    for file_name, file_content in files:
        # Extract text from the PDF or file content
        text_file_path, text_content = extract_pdf_from_db(file_name, section)
        # print(f"Text Content for {file_name}: {text_content[:500]}")  # Log snippet

        example_queries_entities = generate_example_queries_entities(text_content)

        # Initialize GraphRAG with valid working directory
        rag = LightRAG(
            working_dir="./analysis_workspace",
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=4096,
                max_token_size=8192,
                func=embedding_func
            )
        )

        # Await the asynchronous query
        print(f"Query: {query}")
        result = await rag.aquery(query)
        print(f"Result for {file_name}: {result}")
        response_content = result

        if response_content == "Sorry, I'm not able to provide an answer to that question.":
            print(f"Skipped response for {file_name}: {response_content}")
        else:
            group_response.append(response_content)

    return "\n".join(group_response)

def clean_and_parse_json(raw_json):
    """
    Fix and parse invalid JSON strings with double curly braces.
    Args:
        raw_json (str): The raw JSON string to be fixed.
    Returns:
        dict: Parsed JSON as a dictionary.
    """
    try:
        # Replace double curly braces with single curly braces
        fixed_json = raw_json.replace("{{", "{").replace("}}", "}")
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}. Raw data: {raw_json}")
        return None