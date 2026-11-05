from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_id: int = Field(default=0, alias="ADMIN_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
