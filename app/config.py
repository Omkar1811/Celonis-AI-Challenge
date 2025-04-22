from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    HUGGINGFACE_ENDPOINT_URL: str
    HUGGINGFACE_TOKEN: str
    GCS_BUCKET_NAME: str
    GCS_CREDENTIALS_PATH: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings() 