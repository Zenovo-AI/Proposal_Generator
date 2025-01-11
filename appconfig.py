import streamlit as st

class AppSettings:
    def __init__(self):
        secrets = st.secrets["general"]
        self.environment = secrets["ENVIRONMENT"]
        self.port = secrets["port"]
        self.auth_user = secrets["auth_username"]
        self.auth_password = secrets["auth_password"]
        self.domain = secrets["domain"]
        self.db_conn_url = secrets["db_conn_url"]
        self.db_name = secrets["db_name"]
        self.google_api_key = secrets["GOOGLE_API_KEY"]
        self.upstage_api_key = secrets["UPSTAGE_API_KEY"]
        
settings = AppSettings()