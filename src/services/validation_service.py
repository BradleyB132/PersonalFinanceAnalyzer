"""Validation utilities for PersonalFinanceAnalyzer."""

import re
from datetime import date
from typing import Any, Tuple

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


def validate_email(email: str) -> bool:
    """Return True when `email` looks like a valid email address.

    This is a lightweight syntactic check based on a simple regex and is
    intended for UI-level validation only (not authoritative verification).
    """
    if not isinstance(email, str):
        return False
    normalized = email.strip().lower()
    return bool(EMAIL_REGEX.match(normalized))


def validate_password(password: str) -> bool:
    """Validate password minimum length required for account creation."""
    if not isinstance(password, str):
        return False
    return len(password or "") >= MIN_PASSWORD_LENGTH


def validate_uploaded_file(uploaded_file: Any) -> Tuple[bool, str]:
    """Validate a Streamlit uploaded file object for CSV upload.

    Returns a tuple (is_valid, message). When `is_valid` is False the
    message contains a user-facing error description.
    """
    if uploaded_file is None:
        return False, "No file selected. Please choose a CSV file to upload."

    file_name = getattr(uploaded_file, "name", "")
    if not isinstance(file_name, str) or not file_name.lower().endswith(".csv"):
        return False, "Only CSV files are supported for upload."

    file_size = getattr(uploaded_file, "size", None)
    if isinstance(file_size, int) and file_size > MAX_UPLOAD_SIZE_BYTES:
        return (
            False,
            "Uploaded file is too large. Please upload a file smaller than 5 MB.",
        )

    return True, ""


def validate_search_filters(
    start_date: date | None,
    end_date: date | None,
    min_amount: float | None,
    max_amount: float | None,
) -> Tuple[bool, str]:
    """Validate search filter combinations for logical consistency.

    Ensures date ranges and amount ranges are ordered correctly.
    """
    if start_date and end_date and start_date > end_date:
        return False, "Start date must be before or equal to end date."
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        return False, "Minimum amount cannot be greater than maximum amount."
    return True, ""
