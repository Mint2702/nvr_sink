from pydantic import BaseSettings, Field
from typing import Optional


class Settings(BaseSettings):
    nvr_api_key: str = Field(..., env="NVR_API_KEY")
    db_url: str = Field(..., env="DB_URL")
    url_redis: str = Field(..., env="URL_REDIS")
    period: int = Field(..., env="PERIOD")
    creds_path: str = Field(..., env="CREDS_PATH")
    token_path: str = Field(..., env="TOKEN_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings(_env_file="../.env")
