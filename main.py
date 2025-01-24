from datamodel import RequestModel
from inference import retrieve_all_files_in_section
from ingress import ingress_file_doc
import google.generativeai as genai
from db_helper import initialize_database
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, UploadFile, File
import os, uvicorn
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.security import HTTPBasic
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from settings import get_setting
from appconfig import settings as app_settings
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Get application settings from the settings module
settings = get_setting()
# Description for API documentation
description = f"""
{settings.API_STR} helps you do awesome stuff. 🚀
"""

# Define a context manager for the application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application lifespan.
    This function initializes and cleans up resources during the application's lifecycle.
    """
    # STARTUP Call Check routine
    print(running_mode)
    print()
    genai.configure(api_key=app_settings.google_api_key)
    initialize_database()
    print(" ⚡️🚀 RAG Server::Started")
    yield

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=description,
    openapi_url=f"{settings.API_STR}/openapi.json",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    contact={
        "name": "example",
        "url": "https://www.example.com/",
        "email": "hello@example.com",
    },
    lifespan=lifespan,
)
# Configure for development or production mode
if app_settings.environment in ["development", "staging"]:
    running_mode = f"  👩‍💻 🛠️  Running in::{app_settings.environment} mode"
else:
    app.add_middleware(HTTPSRedirectMiddleware)
    running_mode = "  🏭 ☁  Running in::production mode"

# Define allowed origins for CORS
origins = [
    "*",
]

# Instantiate basicAuth
security = HTTPBasic()

# Add middleware to allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# Define a health check endpoint
@app.get("/", status_code=status.HTTP_200_OK)
def index(response_class=JSONResponse):
    return {
        "ApplicationName": "Health Policy Chatbot",
        "ApplicationOwner": "Your Company",
        "ApplicationVersion": "0.1.0",
        "ApplicationEngineer": "Your name",
        "ApplicationStatus": "running...",
    }



@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return "healthy"

    
@app.post("/ingress-file")
async def ingress_file(file: UploadFile = File(...)):
    try:
        # Define the file path
        file_path = f"doc/{file.filename}"

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the file
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Call your subsequent processing function
        return await ingress_file_doc(file.filename, file_path)

    except Exception as e:
        # Catch any exception and return it
        return {"message": f"Error: {str(e)}"}

@app.post("/retrieve")
async def retrieve_query(requestModel:RequestModel):
    response = await retrieve_all_files_in_section(requestModel.query, requestModel.section)
    return JSONResponse(content={"response": response})
        
        
if __name__ == "__main__":
    # Retrieve environment variables for host, port, and timeout
    timeout_keep_alive = int(os.getenv("YOUR_TIMEOUT_IN_SECONDS", 6000))

    # Run the application with the specified host, port, and timeout
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(app_settings.port),
        timeout_keep_alive=timeout_keep_alive,
    )
