from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    nvr_api_key: str = Field(..., env="NVR_API_KEY")
    db_url: str = Field(..., env="DB_URL")
    url_redis: str = Field(..., env="URL_REDIS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings(_env_file="../.env")
