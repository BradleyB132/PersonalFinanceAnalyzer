"""Streamlit entrypoint for PersonalFinanceAnalyzer."""

from __future__ import annotations

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

import logging

# Import logging configuration to initialize handlers and formatters early in
# application startup. This ensures all modules using the standard logging
# library will emit records to the configured handlers (console + rotating file).
import logging_config  # noqa: F401 - module side-effects only

from db import get_engine
from ui.auth_page import render_auth_page

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="PersonalFinanceAnalyzer", page_icon=":lock:", layout="wide"
)


def get_db_engine():
    try:
        return get_engine()
    except RuntimeError as exc:
        # Log the configuration/runtime error and show friendly message in UI
        logger.exception("Database configuration missing or invalid")
        st.error(str(exc))
        st.stop()


def main() -> None:
    try:
        engine = get_db_engine()
    except (RuntimeError, SQLAlchemyError) as exc:
        logger.exception("Failed to obtain database engine")
        st.error(f"Database connection error: {exc}")
        st.stop()

    logger.info("Starting PersonalFinanceAnalyzer Streamlit app")
    render_auth_page(engine)


if __name__ == "__main__":
    main()
