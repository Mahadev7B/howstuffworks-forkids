from pathlib import Path
from uuid import uuid4


def ensure_media_root(media_storage_path: str) -> Path:
    root = Path(media_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "audio").mkdir(parents=True, exist_ok=True)
    return root


def save_media_file(media_storage_path: str, media_type: str, ext: str, content: bytes) -> str:
    root = ensure_media_root(media_storage_path)
    folder = "images" if media_type == "image" else "audio"
    filename = f"{uuid4().hex}.{ext}"
    target = root / folder / filename
    target.write_bytes(content)
    return f"{folder}/{filename}"
