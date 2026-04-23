from __future__ import annotations

# Complexity overview:
# - Time: O(1) fixture setup per test context, excluding SQL execution in tests.
# - Space: O(1) fixture metadata.

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture()
def auth_engine():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    return engine


@pytest.fixture()
def finance_engine():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user_id INTEGER NULL,
                    UNIQUE(name, user_id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    uploaded_file_id INTEGER NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE description_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    user_id INTEGER NULL
                )
                """
            )
        )
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash) VALUES (1, 'user@example.com', 'hash')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO categories (id, name, user_id) VALUES (1, 'Uncategorized', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO categories (id, name, user_id) VALUES (2, 'Groceries', 1)"
            )
        )
        connection.execute(
            text("INSERT INTO categories (id, name, user_id) VALUES (3, 'Travel', 1)")
        )
        connection.execute(
            text(
                "INSERT INTO description_rules (keyword, category_id, user_id) VALUES ('Whole Foods', 2, 1)"
            )
        )
    return engine
