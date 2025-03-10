# config.py

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".env").resolve())

class Settings(BaseSettings):
    """Setting environment variables."""

    SPREADSHEET_ID: str = Field(..., env="SPREADSHEET_ID")
    RANGE_NAME: str = Field(default="A1:Z100", env="RANGE_NAME")
    SCOPES: List[str] = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

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