# config.py
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".env").resolve())

# scope of permissions
SCOPES: List[str] = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

class Settings(BaseSettings):
    """Setting environment variables."""
    DOCUMENT_URL_GOOGLE: str = Field(..., env="DOCUMENT_URL_GOOGLE")
    API_GOOGLE_URL: str = Field(..., env="API_GOOGLE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    # Variables related to Google Sheets
    SPREADSHEET_ID: str = Field(..., env="SPREADSHEET_ID")
    RANGE_NAME: str = Field(default="A1:Z100", env="RANGE_NAME")
    SCOPES: List[str] = SCOPES

    class Config:
        env_file = ".env"  

def get_settings():
    try:
        settings = Settings()  
        return settings
    except ValidationError as e:
        print("Error: Missing or invalid environment variables!")
        print(e.json())  
        raise  