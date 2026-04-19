"""Upload view - bank and credit card statement upload."""
import streamlit as st

from app.database import get_session
from app.services import process_uploaded_statement
from app.ui import render_header


def render():
    render_header(
        "Upload Statement",
        "Upload bank or credit card statements (CSV or PDF)"
    )

    tab_bank, tab_cc = st.tabs([
        ":material/account_balance:  Bank Statement",
        ":material/credit_card:  Credit Card Statement",
    ])

    with tab_bank:
        _render_upload_form("bank", "bank statement")

    with tab_cc:
        _render_upload_form("credit_card", "credit card statement")

    st.markdown("---")
    with st.expander(":material/info: Supported file formats"):
        st.markdown("""
        **CSV**: Standard bank CSV exports with columns like `Date`, `Description`, `Amount`.
        Flexible header naming supported (Transaction Date, Memo, Debit/Credit, etc.).

        **PDF**: Bank statement PDFs with date, description, and amount on each transaction line.

        **Auto-categorization**: Transactions are automatically categorized using rules matching
        common merchants (Walmart, Starbucks, Netflix, etc.). You can override categories anytime
        on the Transactions page.
        """)


def _render_upload_form(source: str, label: str):
    uploaded = st.file_uploader(
        f"Choose your {label}",
        type=["csv", "pdf"],
        key=f"uploader_{source}",
    )

    if uploaded is not None:
        st.markdown(f"**Selected:** `{uploaded.name}` ({uploaded.size / 1024:.1f} KB)")

        if st.button(
            f"Process {label}",
            key=f"btn_{source}",
            use_container_width=False,
        ):
            with st.spinner("Parsing and categorizing transactions..."):
                session = get_session()
                try:
                    count, msg = process_uploaded_statement(
                        session,
                        user_id=st.session_state["user_id"],
                        file_name=uploaded.name,
                        file_bytes=uploaded.getvalue(),
                        source=source,
                    )
                    if count > 0:
                        st.success(msg)
                    else:
                        st.error(msg)
                finally:
                    session.close()
