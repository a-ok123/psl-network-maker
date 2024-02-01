import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CREATE_TICKET_INTERVAL: int = 3
    CHECK_INTERVAL: int = 300
    GENERATE_IMAGE_INTERVAL: int = 2
    BASE_IMG_PATH: str = "images"
    DB_NAME: str = "records.sqlite"

    USE_GPU: bool = False
    # PROMPT_MODEL_PATH: str = "D:\models\TheBloke\Llama-2-7B-Chat-GGUF\llama-2-7b-chat.Q5_K_M.gguf"
    PROMPT_MODEL_PATH: str = "D:\models\TheBloke\llama-2-13b.Q8_0.gguf"
    PROMPT_CHAT_FORMAT: str = "llama-2"
    IMAGE_MODEL_ID: str = "stabilityai/stable-diffusion-2-base"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()