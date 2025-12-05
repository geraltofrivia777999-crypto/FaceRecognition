from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _maybe_add_columns()


def _maybe_add_columns() -> None:
    """Ensure new columns exist for SQLite without full migrations."""
    if "sqlite" not in settings.database_url:
        return
    from sqlalchemy import text

    with engine.begin() as conn:
        info = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = {row[1] for row in info}
        if "expires_at" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN expires_at DATETIME"))
