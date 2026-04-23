"""Authentication helpers for registration and login."""

# Complexity overview:
# - Time: O(1) for password hashing/verification and single-user lookups.
# - Space: O(1) per auth operation.

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import secrets
from typing import Any, Callable

from sqlalchemy.exc import IntegrityError

from db import execute_write, fetch_one

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 210_000
SALT_BYTES = 16


@dataclass(frozen=True)
class AuthResult:
    success: bool
    message: str
    user: dict[str, Any] | None = None
    confirmation_message: str | None = None
    email_sent: bool = False


def _ensure_user_profile_columns(engine=None) -> None:
    """Best-effort schema compatibility for profile fields used by the UI."""
    statements = [
        "ALTER TABLE users ADD COLUMN name VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'",
    ]
    for statement in statements:
        try:
            execute_write(statement, engine=engine)
        except Exception:  # noqa: BLE001
            continue


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt_bytes = salt or secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS,
    )
    return "$".join(
        [
            "pbkdf2_sha256",
            str(PBKDF2_ITERATIONS),
            base64.b64encode(salt_bytes).decode("ascii"),
            base64.b64encode(derived).decode("ascii"),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, encoded_salt, encoded_hash = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    salt = base64.b64decode(encoded_salt.encode("ascii"))
    expected_hash = base64.b64decode(encoded_hash.encode("ascii"))
    candidate_hash = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        int(iterations),
    )
    return hmac.compare_digest(candidate_hash, expected_hash)


def get_user_by_email(email: str, engine=None) -> dict[str, Any] | None:
    _ensure_user_profile_columns(engine=engine)
    return fetch_one(
        """
        SELECT
            id,
            email,
            password_hash,
            COALESCE(name, '') AS name,
            COALESCE(role, 'user') AS role,
            created_at
        FROM users
        WHERE email = :email
        """,
        {"email": normalize_email(email)},
        engine=engine,
    )


def build_confirmation_message(email: str) -> str:
    return (
        f"Welcome to PersonalFinanceAnalyzer, {email}! "
        "Your account has been created successfully. "
        "You can now log in and access your dashboard."
    )


ConfirmationSender = Callable[[str, str], None]


def register_user(
    engine,
    email: str,
    password: str,
    full_name: str | None = None,
    confirmation_sender: ConfirmationSender | None = None,
) -> AuthResult:
    _ensure_user_profile_columns(engine=engine)
    normalized_email = normalize_email(email)
    normalized_name = (full_name or "").strip()
    if not normalized_email:
        return AuthResult(False, "Email is required.")
    if not password:
        return AuthResult(False, "Password is required.")

    existing_user = get_user_by_email(normalized_email, engine=engine)
    if existing_user is not None:
        return AuthResult(False, "Email is already registered.")

    password_hash = hash_password(password)
    try:
        execute_write(
            """
            INSERT INTO users (email, password_hash, name, role)
            VALUES (:email, :password_hash, :name, :role)
            """,
            {
                "email": normalized_email,
                "password_hash": password_hash,
                "name": normalized_name,
                "role": "user",
            },
            engine=engine,
        )
    except IntegrityError:
        return AuthResult(False, "Email is already registered.")

    user = get_user_by_email(normalized_email, engine=engine)
    if user is None:
        return AuthResult(False, "Account creation failed. Please try again.")

    confirmation_message = build_confirmation_message(normalized_email)
    email_sent = False
    if confirmation_sender is not None:
        confirmation_sender(normalized_email, confirmation_message)
        email_sent = True

    return AuthResult(
        True,
        "Account created successfully.",
        user=user,
        confirmation_message=confirmation_message,
        email_sent=email_sent,
    )


def authenticate_user(engine, email: str, password: str) -> AuthResult:
    normalized_email = normalize_email(email)
    if not normalized_email or not password:
        return AuthResult(False, "Enter both email and password.")

    user = get_user_by_email(normalized_email, engine=engine)
    if user is None or not verify_password(password, user["password_hash"]):
        return AuthResult(False, "Invalid username or password.")

    return AuthResult(True, "Login successful.", user=user)
