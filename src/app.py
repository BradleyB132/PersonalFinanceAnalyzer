"""Streamlit entrypoint for PersonalFinanceAnalyzer."""

from __future__ import annotations

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from db import get_engine
from ui.auth_page import render_auth_page

st.set_page_config(
    page_title="PersonalFinanceAnalyzer", page_icon=":lock:", layout="wide"
)


def get_db_engine():
    try:
        return get_engine()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()


def main() -> None:
    try:
        engine = get_db_engine()
    except (RuntimeError, SQLAlchemyError) as exc:
        st.error(f"Database connection error: {exc}")
        st.stop()

    render_auth_page(engine)


if __name__ == "__main__":
    main()
