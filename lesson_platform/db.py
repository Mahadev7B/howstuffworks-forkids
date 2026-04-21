from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .config import Settings
from .models import Base


SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))
engine = None


def init_db(settings: Settings) -> None:
    global engine
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is required. Set it to your PostgreSQL connection string."
        )

    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
