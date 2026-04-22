from __future__ import annotations

from services.preferences_service import (
    get_user_preferences,
    save_user_preferences,
)


def test_get_user_preferences_defaults_to_dark(finance_engine) -> None:
    prefs = get_user_preferences(finance_engine, 1)

    assert prefs["theme_mode"] == "dark"


def test_save_user_preferences_updates_existing_record(finance_engine) -> None:
    save_user_preferences(finance_engine, 1, "light")
    prefs = get_user_preferences(finance_engine, 1)

    assert prefs["theme_mode"] == "light"


def test_save_user_preferences_normalizes_invalid_theme(finance_engine) -> None:
    prefs = save_user_preferences(finance_engine, 1, "alien")

    assert prefs["theme_mode"] == "dark"
