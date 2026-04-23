# Complexity overview:
# - Time: O(n) for query result materialization, O(1) for engine retrieval.
# - Space: O(n) for returned row dictionaries.
from functools import lru_cache
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL missing in environment")
    return database_url


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(get_database_url(), future=True)


def execute_query(query, params=None, engine=None):
    """Execute a raw SQL query and return rows as dictionaries."""

    active_engine = engine or get_engine()
    with active_engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        rows = result.mappings().all()
    return [dict(row) for row in rows]


def fetch_one(query, params=None, engine=None):
    """Execute a query and return the first row as a dictionary or None."""

    active_engine = engine or get_engine()
    with active_engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        row = result.mappings().first()
    return dict(row) if row else None


def execute_write(query, params=None, engine=None):
    """Execute a data-changing query and commit it."""

    active_engine = engine or get_engine()
    with active_engine.begin() as conn:
        result = conn.execute(text(query), params or {})
    return result
