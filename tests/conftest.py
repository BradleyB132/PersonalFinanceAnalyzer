from __future__ import annotations

import os
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
                """
                CREATE TABLE user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    theme_mode TEXT NOT NULL DEFAULT 'dark'
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


# E2E Test Fixtures


@pytest.fixture(scope="session")
def e2e_database_url():
    """Return database URL for E2E tests. Uses environment variable or defaults to local."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/personalfinanceanalyzer",
    )


@pytest.fixture(scope="function")
def e2e_test_user(e2e_database_url):
    """Create a unique test user for E2E tests and clean up after."""
    import uuid
    from sqlalchemy import create_engine, text

    test_email = f"e2e_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"

    engine = create_engine(e2e_database_url)

    # Create test user
    with engine.begin() as connection:
        # Hash password using the app's method
        from services.auth_service import hash_password

        password_hash = hash_password(test_password)

        connection.execute(
            text(
                "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)"
            ),
            {"email": test_email, "password_hash": password_hash},
        )

        # Get user ID
        result = connection.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": test_email}
        )
        user_id = result.fetchone()[0]

    yield {"email": test_email, "password": test_password, "user_id": user_id}

    # Cleanup: Delete test user and all associated data
    with engine.begin() as connection:
        # Delete in correct order due to foreign keys
        connection.execute(
            text("DELETE FROM transactions WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        connection.execute(
            text("DELETE FROM uploaded_files WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        connection.execute(
            text("DELETE FROM description_rules WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        connection.execute(
            text("DELETE FROM categories WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        connection.execute(
            text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id}
        )
