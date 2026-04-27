"""User preference helpers for PersonalFinanceAnalyzer."""

from __future__ import annotations

from db import execute_write, fetch_one

VALID_THEME_MODES = {"dark", "light"}


def _normalize_theme_mode(theme_mode: str) -> str:
    """Normalize a theme mode string to one of the valid modes.

    Unknown or invalid inputs default to 'dark'.
    """
    normalized = str(theme_mode).strip().lower()
    return normalized if normalized in VALID_THEME_MODES else "dark"


def get_user_preferences(engine, user_id: int) -> dict[str, str]:
    """Fetch or create default user preferences for a given user.

    Returns a dict containing preference keys (currently `theme_mode`). If a
    row does not exist it will be created with sensible defaults.
    """
    row = fetch_one(
        "SELECT theme_mode FROM user_preferences WHERE user_id = :user_id",
        {"user_id": user_id},
        engine=engine,
    )
    if row is not None:
        return {"theme_mode": row["theme_mode"] or "dark"}

    default_theme = "dark"
    execute_write(
        "INSERT INTO user_preferences (user_id, theme_mode) VALUES (:user_id, :theme_mode)",
        {"user_id": user_id, "theme_mode": default_theme},
        engine=engine,
    )
    return {"theme_mode": default_theme}


def save_user_preferences(engine, user_id: int, theme_mode: str) -> dict[str, str]:
    """Save or update user preferences and return the saved values."""
    theme_mode = _normalize_theme_mode(theme_mode)
    existing = fetch_one(
        "SELECT user_id FROM user_preferences WHERE user_id = :user_id",
        {"user_id": user_id},
        engine=engine,
    )
    if existing is None:
        execute_write(
            "INSERT INTO user_preferences (user_id, theme_mode) VALUES (:user_id, :theme_mode)",
            {"user_id": user_id, "theme_mode": theme_mode},
            engine=engine,
        )
    else:
        execute_write(
            "UPDATE user_preferences SET theme_mode = :theme_mode WHERE user_id = :user_id",
            {"user_id": user_id, "theme_mode": theme_mode},
            engine=engine,
        )
    return {"theme_mode": theme_mode}
