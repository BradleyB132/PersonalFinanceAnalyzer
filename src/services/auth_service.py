"""Authentication helpers for registration and login."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import secrets
from typing import Any, Callable

from sqlalchemy.exc import IntegrityError

from db import execute_write, fetch_one
from services.validation_service import (
    MIN_PASSWORD_LENGTH,
    validate_email,
    validate_password,
)
import logging

logger = logging.getLogger(__name__)

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
    return fetch_one(
        "SELECT id, email, password_hash, created_at FROM users WHERE email = :email",
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
    confirmation_sender: ConfirmationSender | None = None,
) -> AuthResult:
    normalized_email = normalize_email(email)
    if not validate_email(normalized_email):
        return AuthResult(False, "Enter a valid email address.")
    if not validate_password(password):
        return AuthResult(
            False,
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.",
        )

    existing_user = get_user_by_email(normalized_email, engine=engine)
    if existing_user is not None:
        logger.info("register_user: attempt with existing email", extra={"email": normalized_email})
        return AuthResult(False, "Email is already registered.")

    password_hash = hash_password(password)
    try:
        execute_write(
            "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)",
            {"email": normalized_email, "password_hash": password_hash},
            engine=engine,
        )
    except IntegrityError:
        logger.exception("register_user: IntegrityError while inserting user", extra={"email": normalized_email})
        return AuthResult(False, "Email is already registered.")
    except Exception:
        logger.exception("register_user: unexpected error while creating user", extra={"email": normalized_email})
        return AuthResult(False, "Account creation failed. Please try again.")

    user = get_user_by_email(normalized_email, engine=engine)
    if user is None:
        logger.error("register_user: user not found after insert", extra={"email": normalized_email})
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
    if not validate_email(normalized_email):
        logger.warning(
            "authenticate_user: invalid email format",
            extra={"email": normalized_email},
        )
        return AuthResult(False, "Enter a valid email address.")
    if not password:
        logger.warning(
            "authenticate_user: missing password",
            extra={"email": normalized_email},
        )
        return AuthResult(False, "Enter both email and password.")

    user = get_user_by_email(normalized_email, engine=engine)
    if user is None or not verify_password(password, user["password_hash"]):
        logger.warning("authenticate_user: failed login", extra={"email": normalized_email})
        return AuthResult(False, "Invalid username or password.")

    logger.info("authenticate_user: successful login", extra={"email": normalized_email})
    return AuthResult(True, "Login successful.", user=user)
