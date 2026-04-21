import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from .config import Settings
from .models import Base


SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))
engine = None
logger = logging.getLogger(__name__)


def _apply_postgres_compat_migrations() -> None:
    """Apply idempotent schema backfills for existing PostgreSQL databases.

    Base.metadata.create_all() only creates missing tables; it does not add
    newly introduced columns to already existing tables.
    """
    if engine is None or engine.dialect.name != "postgresql":
        return

    statements = [
        # lessons compatibility columns
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS steps_json JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS narration_json JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS scenes_json JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS lesson_json JSON NOT NULL DEFAULT '{}'::json",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS approved_flag BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS regeneration_needed_flag BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS helpful_score DOUBLE PRECISION NOT NULL DEFAULT 0.0",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS replay_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS reuse_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS generation_time_ms INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS estimated_api_cost DOUBLE PRECISION NOT NULL DEFAULT 0.0",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        # lesson_requests compatibility columns
        "ALTER TABLE lesson_requests ADD COLUMN IF NOT EXISTS generation_time_ms INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE lesson_requests ADD COLUMN IF NOT EXISTS estimated_api_cost DOUBLE PRECISION NOT NULL DEFAULT 0.0",
    ]

    try:
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
    except Exception:
        logger.exception("PostgreSQL compatibility migrations failed during init.")
        raise


def init_db(settings: Settings) -> None:
    global engine
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is required. Set it to your PostgreSQL connection string."
        )

    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
    _apply_postgres_compat_migrations()


def get_session():
    return SessionLocal()
