import os
from dataclasses import dataclass


def _as_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    openai_image_model: str
    openai_tts_model: str
    openai_tts_voice: str
    openai_embedding_model: str
    database_url: str
    similarity_threshold: float
    media_storage_path: str
    lesson_timeout_seconds: int


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1").strip(),
        openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip(),
        openai_tts_voice=os.getenv("OPENAI_TTS_VOICE", "coral").strip(),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip(),
        database_url=os.getenv("DATABASE_URL", "").strip(),
        similarity_threshold=_as_float(os.getenv("SIMILARITY_THRESHOLD"), 0.84),
        media_storage_path=os.getenv("MEDIA_STORAGE_PATH", "media_store").strip(),
        lesson_timeout_seconds=_as_int(os.getenv("LESSON_TIMEOUT_SECONDS"), 180),
    )
