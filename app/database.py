"""
Database configuration module.
Provides SQLAlchemy engine, session factory, and base declarative class.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://finance_user:finance_pass@localhost:5432/finance_db"
)


def _get_shared_engine():
    """Prefer the existing src/db.py engine so old and new app paths share one DB config."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    src_path = os.path.join(project_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    try:
        from db import get_engine as get_src_engine  # type: ignore
        return get_src_engine()
    except Exception:
        # Fallback keeps app runnable if src module path is unavailable.
        return create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)


engine = _get_shared_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    """Get a new database session. Caller must close it."""
    return SessionLocal()


def _ensure_schema_compatibility() -> None:
    """Add missing columns for legacy databases used by earlier app versions."""
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT FALSE",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'bank'",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS uploaded_file_id INTEGER",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
        "ALTER TABLE description_rules ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE description_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS file_type VARCHAR(20)",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS file_name VARCHAR(255)",
        "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP",
    ]

    with engine.begin() as conn:
        for statement in statements:
            try:
                conn.execute(text(statement))
            except Exception:
                # Ignore statements for tables/columns not present in a given legacy schema.
                continue


def init_db():
    """Create all tables. Called on app startup."""
    from app import models  # noqa: F401 - register models
    Base.metadata.create_all(bind=engine)
    _ensure_schema_compatibility()
