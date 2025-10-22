# ecommerce_backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_db_name: str = "ecommerce_db"
    data_path: str = os.path.join(os.path.dirname(__file__), "data")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
