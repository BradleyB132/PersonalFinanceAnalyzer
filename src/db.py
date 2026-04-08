"""
Database helper module.

Provides a simple SQLAlchemy engine factory and helper functions for
common DB operations used by the Streamlit app.

All functions ensure database connections are closed using context managers.

Complexities:
- Connection creation: O(1)
- execute_query: O(R) where R is rows returned

"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL missing in environment')

engine = create_engine(DATABASE_URL)


def execute_query(query, params=None):
    """Execute a raw SQL query and return fetched rows as list of dicts.

    Args:
        query (str): SQL query text
        params (dict): optional parameters

    Returns:
        list[dict]
    """
    with engine.connect() as conn:
        res = conn.execute(text(query), params or {})
        cols = res.keys()
        rows = [dict(zip(cols, r)) for r in res.fetchall()]
    return rows
