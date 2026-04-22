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
    gemini_api_key: str
    gemini_model: str
    gemini_embedding_model: str
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
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        gemini_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    return Settings(
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        gemini_embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip(),
        database_url=os.getenv("DATABASE_URL", "").strip(),
        similarity_threshold=_as_float(os.getenv("SIMILARITY_THRESHOLD"), 0.84),
        media_storage_path=os.getenv("MEDIA_STORAGE_PATH", "media_store").strip(),
        lesson_timeout_seconds=_as_int(os.getenv("LESSON_TIMEOUT_SECONDS"), 180),
        image_parallelism=max(1, _as_int(os.getenv("IMAGE_PARALLELISM"), 3)),
        max_generated_images=max(1, _as_int(os.getenv("MAX_GENERATED_IMAGES"), 5)),
        image_size=os.getenv("IMAGE_SIZE", "auto").strip(),
        audio_enabled=_as_bool(os.getenv("AUDIO_ENABLED"), True),
        local_media_only=_as_bool(os.getenv("LOCAL_MEDIA_ONLY"), False),
        local_tts_enabled=_as_bool(os.getenv("LOCAL_TTS_ENABLED"), False),
    )
