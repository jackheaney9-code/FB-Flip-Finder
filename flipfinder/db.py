from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use a relative SQLite path so it works both locally and on Render
DATABASE_URL = "sqlite:///./flipfinder.db"

# SQLAlchemy engine and session factory
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models; models.py does: from .db import Base
Base = declarative_base()


def init_db() -> None:
    """
    Ensure all tables are created.

    On a fresh Render deploy there is no flipfinder.db file yet,
    so we create the schema on startup. We import models here to
    avoid circular imports (db -> models -> db).
    """
    from . import models  # local import to avoid circular dependency

    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
