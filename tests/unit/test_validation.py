from __future__ import annotations


from services.validation_service import (
    validate_email,
    validate_password,
    validate_search_filters,
    validate_uploaded_file,
)


class DummyUploadedFile:
    def __init__(self, name: str, size: int) -> None:
        self.name = name
        self.size = size


def test_validate_email_accepts_valid_addresses() -> None:
    assert validate_email("user@example.com")
    assert validate_email("test.user+alias@sub.domain.co")


def test_validate_email_rejects_invalid_addresses() -> None:
    assert not validate_email("")
    assert not validate_email("invalid-email")
    assert not validate_email("no-at-sign.com")


def test_validate_password_enforces_minimum_length() -> None:
    assert validate_password("strongpass")
    assert not validate_password("short")
    assert not validate_password("")


def test_validate_search_filters_detects_invalid_date_ranges() -> None:
    from datetime import date

    is_valid, message = validate_search_filters(
        date(2024, 2, 1),
        date(2024, 1, 1),
        None,
        None,
    )
    assert not is_valid
    assert "Start date must be before or equal to end date" in message


def test_validate_search_filters_detects_invalid_amount_ranges() -> None:
    is_valid, message = validate_search_filters(
        None,
        None,
        100.0,
        50.0,
    )
    assert not is_valid
    assert "Minimum amount cannot be greater than maximum amount" in message


def test_validate_search_filters_accepts_valid_filters() -> None:
    from datetime import date

    is_valid, message = validate_search_filters(
        date(2024, 1, 1),
        date(2024, 2, 1),
        10.0,
        100.0,
    )
    assert is_valid
    assert message == ""


def test_validate_uploaded_file_accepts_csv_file() -> None:
    fake_file = DummyUploadedFile(name="statement.csv", size=1024)
    is_valid, message = validate_uploaded_file(fake_file)
    assert is_valid
    assert message == ""


def test_validate_uploaded_file_rejects_missing_file() -> None:
    is_valid, message = validate_uploaded_file(None)
    assert not is_valid
    assert "No file selected" in message


def test_validate_uploaded_file_rejects_invalid_extension() -> None:
    fake_file = DummyUploadedFile(name="statement.txt", size=1024)
    is_valid, message = validate_uploaded_file(fake_file)
    assert not is_valid
    assert "Only CSV files are supported" in message


def test_validate_uploaded_file_rejects_large_file() -> None:
    fake_file = DummyUploadedFile(name="statement.csv", size=6 * 1024 * 1024)
    is_valid, message = validate_uploaded_file(fake_file)
    assert not is_valid
    assert "too large" in message
