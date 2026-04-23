from services.auth_service import build_confirmation_message, normalize_email

# Complexity overview:
# - Time: O(1) string normalization/message checks.
# - Space: O(1).


def test_email_normalization_is_lowercase_and_trimmed() -> None:
    assert normalize_email("  USER@Example.com  ") == "user@example.com"


def test_confirmation_message_mentions_account_creation() -> None:
    message = build_confirmation_message("user@example.com")

    assert "user@example.com" in message
    assert "account has been created" in message.lower()
