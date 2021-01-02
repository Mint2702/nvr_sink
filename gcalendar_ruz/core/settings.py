from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    host: str = Field(..., env="HOST_REDIS")
    port: str = Field(..., env="PORT_REDIS")
    nvr_api_key: str = Field(..., env="NVR_API_KEY")
    db_url: str = Field(..., env="DB_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings(_env_file="../.env")
