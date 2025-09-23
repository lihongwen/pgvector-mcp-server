"""Database configuration and session management for pgvector MCP server."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings

# Settings and engine will be loaded when first needed
_settings = None
_engine = None
_SessionLocal = None

def get_db_settings():
    """Get settings with lazy initialization."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings

def get_engine():
    """Get database engine with lazy initialization."""
    global _engine
    if _engine is None:
        settings = get_db_settings()
        _engine = create_engine(
            settings.database_url,
            # Connection pool settings for better reliability
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Validates connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=settings.debug  # Log SQL queries in debug mode
        )
    return _engine

def get_session_local():
    """Get SessionLocal with lazy initialization."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

# Base class for models
Base = declarative_base()

def get_session() -> Session:
    """Get database session (legacy method - prefer get_db_session context manager)."""
    session_local = get_session_local()
    return session_local()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup."""
    session_local = get_session_local()
    session = session_local()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
