"""Reports view - PDF report export."""
from datetime import datetime
import streamlit as st

from app.database import get_session
from app.services import compute_dashboard_stats
from app.reports import generate_report_pdf
from app.ui import render_header
from app.utils import format_currency


def render():
    render_header(
        "Reports",
        "Download a professional PDF snapshot of your finances"
    )

    session = get_session()
    user_id = st.session_state["user_id"]
    user_name = st.session_state.get("user_name", "User")

    try:
        stats = compute_dashboard_stats(session, user_id)
    finally:
        session.close()

    if stats["total_transactions"] == 0:
        st.info("Upload some transactions first to generate a report.")
        return

    # Preview the data that will be included
    with st.container(border=True):
        st.markdown("### Report Preview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Transactions", stats["total_transactions"])
        col2.metric("Total Income", format_currency(stats["total_income"]))
        col3.metric("Total Expenses", format_currency(stats["total_expenses"]))
        col4.metric("Net Balance", format_currency(stats["net_balance"]))

        st.markdown("**Top spending categories:**")
        for c in stats["by_category"][:5]:
            st.write(f"- {c['name']}: {format_currency(c['value'])}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Generate button
    pdf_bytes = generate_report_pdf(stats, user_name)
    filename = f"finance_report_{datetime.now().strftime('%Y%m%d')}.pdf"

    st.download_button(
        ":material/download: Download PDF Report",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=False,
        key="download_report_btn",
    )

    st.caption("The PDF includes summary metrics, spending by category, and monthly trends.")
