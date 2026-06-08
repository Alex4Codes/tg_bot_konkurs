import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    channel_id: str
    admin_id: int
    db_path: str = "contest.db"
    log_level: str = "INFO"

settings = Settings()
