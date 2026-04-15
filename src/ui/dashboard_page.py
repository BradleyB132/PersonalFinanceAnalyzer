"""Dashboard workspace for PersonalFinanceAnalyzer."""

from __future__ import annotations

from datetime import date
import logging

import streamlit as st

from services.finance_service import (
    build_pdf_report,
    build_transactions_csv,
    calculate_budget_recommendations,
    get_available_categories,
    get_category_summary,
    get_dashboard_metrics,
    get_transaction_by_id,
    get_transactions,
    get_trend_summary,
    import_statement_file,
    search_transactions,
    update_transaction_category,
)

logger = logging.getLogger(__name__)

NAVIGATION_OPTIONS = [
    "Dashboard",
    "Upload Bank Statement",
    "Upload Credit Card Statement",
    "Transactions",
    "Search / Filter",
    "Reports",
    "Budgeting",
]


def _inject_dashboard_styles() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] .main .block-container {
                color: #0f172a !important;
            }

            [data-testid="stAppViewContainer"] .main h1,
            [data-testid="stAppViewContainer"] .main h2,
            [data-testid="stAppViewContainer"] .main h3,
            [data-testid="stAppViewContainer"] .main p,
            [data-testid="stAppViewContainer"] .main label,
            [data-testid="stAppViewContainer"] .main li,
            [data-testid="stAppViewContainer"] .main span {
                color: #0f172a !important;
            }

            [data-testid="stHeadingWithActionElements"] h1,
            [data-testid="stHeadingWithActionElements"] h2,
            [data-testid="stHeadingWithActionElements"] h3,
            [data-testid="stHeading"] h1,
            [data-testid="stHeading"] h2,
            [data-testid="stHeading"] h3 {
                color: #0f172a !important;
            }

            [data-testid="stMarkdownContainer"] p,
            [data-testid="stMarkdownContainer"] span,
            [data-testid="stMarkdownContainer"] div {
                color: #334155 !important;
            }

            [data-testid="stMetricLabel"],
            [data-testid="stMetricValue"] {
                color: #0f172a !important;
            }

            [data-testid="stAlertContainer"] p {
                color: #0f172a;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1b2130 0%, #161c2a 100%);
            }

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] div {
                color: #e5e7eb !important;
            }

            [data-testid="stSidebar"] a {
                color: #93c5fd !important;
                text-decoration: underline;
                text-underline-offset: 0.14em;
            }

            [data-testid="stSidebar"] [role="radiogroup"] > label {
                border-radius: 8px;
                padding: 0.2rem 0.35rem;
                margin-bottom: 0.12rem;
            }

            [data-testid="stSidebar"] [role="radiogroup"] > label > div,
            [data-testid="stSidebar"] [role="radiogroup"] > label p {
                color: #d1d5db !important;
                font-weight: 600;
            }

            [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
                background: rgba(59, 130, 246, 0.18);
                border: 1px solid rgba(147, 197, 253, 0.6);
            }

            [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p,
            [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) div {
                color: #eff6ff !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_dashboard_state() -> None:
    if "dashboard_section" not in st.session_state:
        st.session_state.dashboard_section = NAVIGATION_OPTIONS[0]


def _set_dashboard_section(section: str) -> None:
    st.session_state.dashboard_section = section


def _render_sidebar(user, logout_callback) -> None:
    with st.sidebar:
        st.subheader("Account")
        st.write(user["email"])
        if st.button("Logout", use_container_width=True, type="primary"):
            logout_callback()
        st.divider()
        st.radio("Navigate", NAVIGATION_OPTIONS, key="dashboard_section")


def _render_empty_dashboard_prompt() -> None:
    st.info("No transactions are available yet. Use the upload section to add data.")
    st.button(
        "Upload data now",
        type="primary",
        on_click=_set_dashboard_section,
        args=("Upload Bank Statement",),
    )


def _render_dashboard_overview(engine, user_id: int) -> None:
    st.title("Financial Dashboard")
    st.write("View your spending patterns, recent activity, and upload status.")

    metrics = get_dashboard_metrics(engine, user_id)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions", metrics["transaction_count"])
    col2.metric("Categories", metrics["category_count"])
    col3.metric("Total Amount", f"{metrics['total_amount']:.2f}")
    col4.metric("Average Amount", f"{metrics['average_amount']:.2f}")

    transactions = get_transactions(engine, user_id)
    if transactions.empty:
        _render_empty_dashboard_prompt()
        return

    category_summary = get_category_summary(engine, user_id)
    trend_summary = get_trend_summary(engine, user_id)

    st.subheader("Spending by Category")
    if not category_summary.empty:
        chart_frame = category_summary.set_index("category")["amount"]
        st.bar_chart(chart_frame)
    else:
        st.info("No category summary is available yet.")

    st.subheader("Spending Trends Over Time")
    if not trend_summary.empty:
        trend_frame = trend_summary.set_index("period")["amount"]
        st.line_chart(trend_frame)
    else:
        st.info("No trend data is available yet.")

    st.subheader("Recent Transactions")
    st.dataframe(transactions.head(20), use_container_width=True)


def _process_upload(engine, user_id: int, file_type: str, uploaded_file) -> None:
    try:
        result = import_statement_file(
            engine=engine,
            user_id=user_id,
            file_name=uploaded_file.name,
            file_type=file_type,
            file_bytes=uploaded_file.getvalue(),
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to process file: {exc}")
        return

    st.success(
        f"Imported {result.inserted_count} transactions from {uploaded_file.name}."
    )
    st.session_state.dashboard_section = "Dashboard"
    st.rerun()


def _render_upload_section(engine, user_id: int, file_type: str, title: str) -> None:
    st.title(title)
    st.write(
        "Upload a CSV file containing amount, description, and transaction_date columns."
    )
    uploaded_file = st.file_uploader(
        f"Choose a {file_type.replace('_', ' ')} CSV", type=["csv"], key=file_type
    )
    st.button(
        "Process Upload",
        type="primary",
        disabled=uploaded_file is None,
        on_click=_process_upload,
        args=(engine, user_id, file_type, uploaded_file) if uploaded_file else (engine, user_id, file_type, None),
    )
    if uploaded_file is not None:
        st.caption(f"Selected file: {uploaded_file.name}")
        st.write("The system will auto-categorize transactions using description rules.")


def _render_transactions_section(engine, user_id: int) -> None:
    st.title("Transactions")
    st.write("Review transactions and update misclassified categories.")

    transactions = get_transactions(engine, user_id)
    categories = get_available_categories(engine, user_id)

    if transactions.empty:
        _render_empty_dashboard_prompt()
        return

    st.dataframe(transactions, use_container_width=True)

    transaction_labels = {
        f"{row['id']} | {row['transaction_date']} | {str(row['description'])[:45]}": int(row["id"])
        for _, row in transactions.iterrows()
    }
    selected_label = st.selectbox(
        "Select a transaction",
        list(transaction_labels.keys()),
        key="selected_transaction",
    )
    selected_transaction_id = transaction_labels[selected_label]
    selected_transaction = get_transaction_by_id(engine, user_id, selected_transaction_id)
    if selected_transaction is None:
        st.error("Could not load the selected transaction.")
        return

    category_lookup = {
        str(row["name"]): int(row["id"]) for _, row in categories.iterrows()
    }
    category_names = list(category_lookup.keys())
    default_index = 0
    current_category_id = int(selected_transaction["category_id"])
    for index, name in enumerate(category_names):
        if category_lookup[name] == current_category_id:
            default_index = index
            break

    selected_category = st.selectbox(
        "Update category",
        category_names,
        index=default_index,
        key="transaction_category_update",
    )

    if st.button("Save category update", type="primary"):
        updated = update_transaction_category(
            engine,
            user_id=user_id,
            transaction_id=selected_transaction_id,
            category_id=category_lookup[selected_category],
        )
        if updated:
            st.success("Transaction category updated successfully.")
            st.rerun()
        else:
            st.error("Unable to update the selected transaction.")


def _render_search_section(engine, user_id: int) -> None:
    st.title("Search and Filter")
    st.write("Find transactions by keyword, category, date range, or amount.")

    categories = get_available_categories(engine, user_id)
    category_lookup = {str(row["name"]): int(row["id"]) for _, row in categories.iterrows()}

    with st.form("search_form"):
        keyword = st.text_input("Keyword", placeholder="Walmart, Uber, Netflix")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", value=None)
            min_amount = st.number_input("Minimum amount", value=0.0, step=1.0)
        with col2:
            end_date = st.date_input("End date", value=None)
            max_amount = st.number_input("Maximum amount", value=0.0, step=1.0)
        category_choice = st.selectbox(
            "Category", ["All"] + list(category_lookup.keys())
        )
        submitted = st.form_submit_button("Apply filters", type="primary")

    if submitted:
        results = search_transactions(
            engine=engine,
            user_id=user_id,
            keyword=keyword or None,
            start_date=start_date if isinstance(start_date, date) else None,
            end_date=end_date if isinstance(end_date, date) else None,
            category_id=None if category_choice == "All" else category_lookup[category_choice],
            min_amount=min_amount if min_amount > 0 else None,
            max_amount=max_amount if max_amount > 0 else None,
        )
        if results.empty:
            st.info('No results match your search.')
        else:
            st.dataframe(results, use_container_width=True)
    else:
        st.caption("Run a search to see matching transactions.")


def _render_reports_section(engine, user_id: int) -> None:
    st.title("Reports")
    st.write("Download CSV and PDF snapshots of your current financial data.")

    transactions = get_transactions(engine, user_id)
    if transactions.empty:
        st.info("No transaction data is available yet for export.")
        return

    csv_bytes = build_transactions_csv(engine, user_id)
    pdf_bytes = build_pdf_report(engine, user_id)

    st.download_button(
        "Download CSV report",
        data=csv_bytes,
        file_name="personal_finance_report.csv",
        mime="text/csv",
        type="primary",
    )
    st.download_button(
        "Download PDF snapshot",
        data=pdf_bytes,
        file_name="personal_finance_dashboard.pdf",
        mime="application/pdf",
    )

    st.subheader("Report Preview")
    st.dataframe(transactions.head(10), use_container_width=True)


def _render_budgeting_section(engine, user_id: int) -> None:
    st.title("Budgeting and Goal Setting")
    st.write("Enter your monthly income to calculate recommendations by category.")

    categories = get_available_categories(engine, user_id)
    category_names = [str(row["name"]) for _, row in categories.iterrows()]
    monthly_income = st.number_input("Monthly income", min_value=0.0, step=100.0)
    priority_categories = st.multiselect("Priority categories", category_names)

    if st.button("Calculate budget", type="primary"):
        if monthly_income <= 0:
            st.error("Please enter a monthly income greater than zero.")
            return

        recommendations = calculate_budget_recommendations(
            engine=engine,
            user_id=user_id,
            monthly_income=monthly_income,
            priority_categories=priority_categories,
        )
        if recommendations.empty:
            st.info("No categories are available for budgeting yet.")
            return

        st.success("Budget recommendations generated successfully.")
        st.dataframe(recommendations, use_container_width=True)

        overspent = recommendations[recommendations["overspent"]]
        if not overspent.empty:
            st.warning(
                "Overspent categories: "
                + ", ".join(overspent["category"].astype(str).tolist())
            )

        total_recommended = float(recommendations["recommended_budget"].sum())
        total_spend = float(recommendations["actual_spend"].sum())
        col1, col2 = st.columns(2)
        col1.metric("Recommended total budget", f"{total_recommended:.2f}")
        col2.metric("Current spending", f"{total_spend:.2f}")
    else:
        st.caption("Choose your priorities and click calculate to generate a budget.")


def render_dashboard_page(engine, logout_callback) -> None:
    user = st.session_state.authenticated_user
    if user is None:
        return

    _inject_dashboard_styles()
    initialize_dashboard_state()
    _render_sidebar(user, logout_callback)

    section = st.session_state.dashboard_section
    if section == "Dashboard":
        _render_dashboard_overview(engine, int(user["id"]))
    elif section == "Upload Bank Statement":
        _render_upload_section(engine, int(user["id"]), "bank_statement", "Upload Bank Statement")
    elif section == "Upload Credit Card Statement":
        _render_upload_section(
            engine,
            int(user["id"]),
            "credit_card_statement",
            "Upload Credit Card Statement",
        )
    elif section == "Transactions":
        _render_transactions_section(engine, int(user["id"]))
    elif section == "Search / Filter":
        _render_search_section(engine, int(user["id"]))
    elif section == "Reports":
        _render_reports_section(engine, int(user["id"]))
    elif section == "Budgeting":
        _render_budgeting_section(engine, int(user["id"]))
