"""Database helper module for the Streamlit application."""

from functools import lru_cache
import logging
import os

from dotenv import load_dotenv
import sentry_sdk
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

load_dotenv()

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    # Send INFO-level messages to Sentry as breadcrumbs, only send ERROR+ as events
    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[sentry_logging],
        send_default_pii=False,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        environment=os.getenv("SENTRY_ENV", "development"),
        release=os.getenv("SENTRY_RELEASE"),
        # enable_logs=True  # optionally enable if you want logging capture via SDK
    )

# If you still want to validate once, guard the crash behind an env var:
if os.getenv("SENTRY_VALIDATE") == "1":
    1 / 0


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL missing in environment")
    return database_url


@lru_cache(maxsize=1)
def get_engine():
    engine = create_engine(get_database_url(), future=True)
    logger.debug("Created SQLAlchemy engine for %s", get_database_url())
    return engine


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
