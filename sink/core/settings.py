from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    nvr_api_key: str = Field(..., env="NVR_API_KEY")
    period: int = Field(..., env="PERIOD")
    creds_path: str = Field(..., env="CREDS_PATH")
    token_path: str = Field(..., env="TOKEN_PATH")
    buildings: list = Field(..., env="BUILDINGS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings(_env_file="../.env")
