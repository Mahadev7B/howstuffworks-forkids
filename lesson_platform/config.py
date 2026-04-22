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


def _as_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
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
    image_parallelism: int
    max_generated_images: int
    image_size: str
    audio_enabled: bool
    local_media_only: bool
    local_tts_enabled: bool


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
        image_parallelism=max(1, _as_int(os.getenv("IMAGE_PARALLELISM"), 3)),
        max_generated_images=max(1, _as_int(os.getenv("MAX_GENERATED_IMAGES"), 4)),
        image_size=os.getenv("IMAGE_SIZE", "512x512").strip(),
        audio_enabled=_as_bool(os.getenv("AUDIO_ENABLED"), True),
        local_media_only=_as_bool(os.getenv("LOCAL_MEDIA_ONLY"), False),
        local_tts_enabled=_as_bool(os.getenv("LOCAL_TTS_ENABLED"), False),
    )
