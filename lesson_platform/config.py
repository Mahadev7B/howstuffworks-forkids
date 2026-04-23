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


def _clean_env(value: str, default: str = "") -> str:
    text = (value or "").strip()
    if not text:
        return default
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    return text or default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    embedding_model: str
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
    openai_api_key = _clean_env(os.getenv("OPENAI_API_KEY", ""))
    if not openai_api_key:
        openai_api_key = _clean_env(os.getenv("OPENAI_API", ""))
    return Settings(
        openai_api_key=openai_api_key,
        openai_model=_clean_env(os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "gpt-4.1-mini"),
        embedding_model=_clean_env(os.getenv("EMBEDDING_MODEL", "local-hash"), "local-hash"),
        database_url=_clean_env(os.getenv("DATABASE_URL", "")),
        similarity_threshold=_as_float(os.getenv("SIMILARITY_THRESHOLD"), 0.84),
        media_storage_path=_clean_env(os.getenv("MEDIA_STORAGE_PATH", "media_store"), "media_store"),
        lesson_timeout_seconds=_as_int(os.getenv("LESSON_TIMEOUT_SECONDS"), 180),
        image_parallelism=max(1, _as_int(os.getenv("IMAGE_PARALLELISM"), 3)),
        max_generated_images=max(1, _as_int(os.getenv("MAX_GENERATED_IMAGES"), 5)),
        image_size=os.getenv("IMAGE_SIZE", "auto").strip(),
        audio_enabled=_as_bool(os.getenv("AUDIO_ENABLED"), True),
        local_media_only=_as_bool(os.getenv("LOCAL_MEDIA_ONLY"), False),
        local_tts_enabled=_as_bool(os.getenv("LOCAL_TTS_ENABLED"), False),
    )
