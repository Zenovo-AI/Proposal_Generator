# Load .env file using:
from dotenv import load_dotenv
load_dotenv()
import os

class AppSettings:
    environment= os.getenv("ENVIRONMENT")
    port = os.getenv("PORT")
    auth_user = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")
    domain = os.getenv("DOMAIN")
    db_conn_url = os.getenv("DB_CONN_URL")
    db_name = os.getenv("DB_NAME")
    google_api_key = os.getenv("GOOGLE_AI_API_KEY")
    upstage_api_key = os.getenv("UPSTAGE_API_KEY")
    
settings = AppSettings()