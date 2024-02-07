from functools import lru_cache
from pydantic_settings import BaseSettings
import random


class Settings(BaseSettings):
    BASE_IMG_PATH: str = "images"
    DB_NAME: str = "tickets.sqlite"

    ENABLE_CREATE_TICKETS: bool = True
    ENABLE_CHECK_STATUSES: bool = True
    ENABLE_GENERATE_IMAGES: bool = True
    CREATE_TICKET_INTERVAL: int = 300
    CHECK_INTERVAL: int = 600
    GENERATE_IMAGE_INTERVAL: int = 10

    USE_GPU: bool
    PROMPT_MODEL_PATH: str
    PROMPT_CHAT_FORMAT: str
    IMAGE_MODEL_ID: str
    GRAMMAR_PATH: str

    LLAMA_SYSTEM_PROMPT: str
    LLAMA_USER_REQUEST: str
    SD_ITERATIONS: int = 50
    IMAGE_NEGATIVE_PROMPT: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()


def biased_random() -> int:
    return int(1 + (20-1) * (random.random() ** 2))


def get_random_genre() -> str:
    return random.choice(GENRE_LIST)


GENRE_LIST = [
    "Space Opera",
    "Fantasy World",
    "Magic Realm",
    "Dystopian Future",
    "Post-apocalyptic Landscape",
    "Alien Invasion",
    "Fairy Tale Kingdom",
    "Medieval Setting",
    "Steampunk Metropolis",
    "Science Fiction Cityscape",
    "Pirate Seascape",
    "Astrological Imagery",
    "Cryptid Forest",
    "Mystical Island",
    "Cosmic Landscape",
    "Dreamlike Environment",
    "Cybernetic Reality",
    "Supernatural Phenomena",
    "Epic Adventure",
    "Gothic Manor",
    "Abstract Art",
    "Still Life",
    "Portrait Photography",
    "Wildlife Photography",
    "Black and White",
    "Cityscape Images",
    "Fashion Photography",
    "Landscape Images",
    "Street Photography",
    "Documentary Photography",
    "Conceptual Art",
    "Fine Art",
    "Sports Photography",
    "Travel Photography",
    "Event Photography",
    "Food Photography",
    "Architectural Photography",
    "Underwater Photography",
    "Macro Photography",
    "Wedding Photography"
]
