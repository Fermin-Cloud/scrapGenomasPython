# config.py
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".env").resolve())

class Settings(BaseSettings):
    DOCUMENT_URL_GOOGLE: str = Field(..., env="DOCUMENT_URL_GOOGLE")
    API_GOOGLE_URL: str = Field(..., env="API_GOOGLE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

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