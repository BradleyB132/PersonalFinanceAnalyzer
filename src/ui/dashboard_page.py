"""Dashboard workspace for PersonalFinanceAnalyzer."""

from __future__ import annotations

from datetime import date
import logging

import altair as alt
import pandas as pd
import streamlit as st
from ui.dashboard_styles import build_dashboard_styles

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
    create_user_category,
)
from services.preferences_service import (
    get_user_preferences,
    save_user_preferences,
)

logger = logging.getLogger(__name__)

NAVIGATION_OPTIONS = [
    "Dashboard",
    "Upload Bank Statement",
    "Upload Credit Card Statement",
    "Transactions",
    "Search / Filter",
    "Reports",
    "Preferences",
    "Budgeting",
]

NAV_ICONS = {
    "Dashboard": "▦",
    "Upload Bank Statement": "⇪",
    "Upload Credit Card Statement": "⇪",
    "Transactions": "☰",
    "Search / Filter": "⌕",
    "Reports": "▤",
    "Preferences": "⚙",
    "Budgeting": "$",
}

NAV_DISPLAY = {
    "Dashboard": "Dashboard",
    "Upload Bank Statement": "Upload Bank",
    "Upload Credit Card Statement": "Upload Card",
    "Transactions": "Transactions",
    "Search / Filter": "Search",
    "Reports": "Reports",
    "Preferences": "Preferences",
    "Budgeting": "Budgeting",
}


def _resolve_theme_mode(engine) -> str:
    if "theme_mode" in st.session_state:
        return st.session_state.theme_mode

    if st.session_state.authenticated_user is not None:
        user_id = int(st.session_state.authenticated_user["id"])
        preferences = get_user_preferences(engine, user_id)
        theme_mode = preferences.get("theme_mode", "dark")
    else:
        theme_mode = "dark"

    st.session_state.theme_mode = theme_mode
    return theme_mode


def _theme_tokens(theme_mode: str) -> dict[str, str]:
    return {
        "bg": (
            "radial-gradient(circle at 8% 0%, rgba(68, 210, 255, 0.12), transparent 30%),"
            "radial-gradient(circle at 85% 7%, rgba(255, 90, 42, 0.14), transparent 42%),"
            "linear-gradient(160deg, #060910 0%, #0a1222 52%, #060910 100%)"
        ),
        "text": "#eaf0ff",
        "muted": "#94a6cc",
        "edge": "rgba(109, 125, 255, 0.25)",
        "sidebar": "linear-gradient(180deg, #0c1426 0%, #0a1020 100%)",
        "panel": "linear-gradient(145deg, rgba(15, 27, 48, 0.95), rgba(11, 18, 33, 0.95))",
        "hero": "linear-gradient(130deg, rgba(15, 27, 48, 0.96), rgba(11, 18, 33, 0.96))",
        "chip_bg": "rgba(30, 64, 175, 0.24)",
        "chip_border": "rgba(96, 165, 250, 0.35)",
        "txn_panel": "linear-gradient(145deg, rgba(15, 25, 44, 0.94), rgba(9, 16, 31, 0.94))",
        "shadow": "0 18px 45px rgba(5, 8, 15, 0.55)",
        "pos": "#34d399",
        "neg": "#fb7185",
    }


def _inject_dashboard_styles(theme_mode: str) -> None:
    t = _theme_tokens(theme_mode)
    st.markdown(build_dashboard_styles(t), unsafe_allow_html=True)


def initialize_dashboard_state() -> None:
    if "dashboard_section" not in st.session_state:
        st.session_state.dashboard_section = NAVIGATION_OPTIONS[0]


def _set_dashboard_section(section: str) -> None:
    st.session_state.dashboard_section = section


def _fmt_currency(value: float) -> str:
    return f"${value:,.2f}"


def _build_recent_activity_csv(transactions: pd.DataFrame, limit: int = 20) -> bytes:
    recent = transactions.head(limit).copy()
    recent["amount"] = pd.to_numeric(recent["amount"], errors="coerce").fillna(0.0)
    export_cols = [
        "transaction_date",
        "description",
        "category",
        "amount",
        "uploaded_file_id",
    ]
    existing_cols = [col for col in export_cols if col in recent.columns]
    if not existing_cols:
        return b""
    return recent[existing_cols].to_csv(index=False).encode("utf-8")


def _render_kpi_cards(metrics: dict[str, float]) -> None:
    cards = [
        ("Transactions", f"{int(metrics['transaction_count'])}", "Records uploaded"),
        ("Categories", f"{int(metrics['category_count'])}", "Mapped spending buckets"),
        (
            "Total Flow",
            _fmt_currency(float(metrics["total_amount"])),
            "Net captured in system",
        ),
        (
            "Average Txn",
            _fmt_currency(float(metrics["average_amount"])),
            "Typical entry size",
        ),
    ]
    for column, (title, value, note) in zip(st.columns(4), cards):
        column.markdown(
            f"""
            <div class="pf-card">
                <div class="pf-kpi-title">{title}</div>
                <div class="pf-kpi-value">{value}</div>
                <div class="pf-kpi-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _apply_chart_theme(chart: alt.Chart, theme_mode: str) -> alt.Chart:
    axis_color = "#c7d2fe"
    legend_color = "#e2e8f0"
    grid_color = "rgba(148, 163, 184, 0.18)"
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor=axis_color,
            titleColor=axis_color,
            gridColor=grid_color,
            domainColor=grid_color,
            tickColor=grid_color,
        )
        .configure_legend(labelColor=legend_color, titleColor=legend_color)
    )


def _render_spend_trend_chart(trend_summary: pd.DataFrame, theme_mode: str) -> None:
    if trend_summary.empty:
        st.info("No trend data is available yet.")
        return

    trend_frame = trend_summary.copy()
    trend_frame["amount"] = pd.to_numeric(
        trend_frame["amount"], errors="coerce"
    ).fillna(0.0)

    area_fill = "#2aa5ff"
    line_color = "#ff7b39"
    point_color = "#44d2ff"

    area = (
        alt.Chart(trend_frame)
        .mark_area(opacity=0.22, interpolate="monotone", color=area_fill)
        .encode(x=alt.X("period:N", title="Month"), y=alt.Y("amount:Q", title="Amount"))
    )
    line = (
        alt.Chart(trend_frame)
        .mark_line(strokeWidth=3, interpolate="monotone", color=line_color)
        .encode(x="period:N", y="amount:Q")
    )
    points = (
        alt.Chart(trend_frame)
        .mark_circle(size=64, color=point_color)
        .encode(
            x="period:N",
            y="amount:Q",
            tooltip=[
                alt.Tooltip("period:N", title="Month"),
                alt.Tooltip("amount:Q", title="Amount", format=",.2f"),
            ],
        )
    )
    composed = _apply_chart_theme(
        (area + line + points).properties(height=290), theme_mode
    )
    st.altair_chart(composed, use_container_width=True)


def _build_income_expense_series(transactions: pd.DataFrame) -> pd.DataFrame:
    tx = transactions.copy()
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0.0)
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"], errors="coerce")
    tx = tx.dropna(subset=["transaction_date"])
    if tx.empty:
        return pd.DataFrame(columns=["period", "series", "amount"])

    tx["period"] = tx["transaction_date"].dt.strftime("%Y-%m")
    tx["income"] = tx["amount"].clip(lower=0)
    tx["expense"] = tx["amount"].where(tx["amount"] < 0, 0).abs()

    grouped = tx.groupby("period", as_index=False)[["income", "expense"]].sum()
    melted = grouped.melt(
        id_vars=["period"],
        value_vars=["income", "expense"],
        var_name="series",
        value_name="amount",
    )
    melted["amount"] = pd.to_numeric(melted["amount"], errors="coerce").fillna(0.0)
    return melted


def _render_income_vs_expense_chart(
    transactions: pd.DataFrame, theme_mode: str
) -> None:
    frame = _build_income_expense_series(transactions)
    if frame.empty:
        st.info("Not enough data to render income vs expense trend yet.")
        return

    frame = frame.copy()
    frame["period_date"] = pd.to_datetime(frame["period"] + "-01", errors="coerce")
    frame = frame.dropna(subset=["period_date"]).sort_values("period_date")
    frame["period_label"] = frame["period_date"].dt.strftime("%B").str.upper()
    month_order = frame.drop_duplicates("period_date")["period_label"].tolist()

    income_color = "#ff8a3d"
    expense_color = "#9d4dff"

    hover = alt.selection_point(
        fields=["period_label"], on="pointerover", nearest=True, empty=False
    )

    base = alt.Chart(frame).encode(
        x=alt.X(
            "period_label:N",
            sort=month_order,
            title=None,
            axis=alt.Axis(labelAngle=0, labelPadding=12, tickSize=0, domain=False),
        ),
        y=alt.Y(
            "amount:Q",
            title=None,
            axis=alt.Axis(grid=False, domain=False, tickSize=0, format=",.0f"),
        ),
        color=alt.Color(
            "series:N",
            title=None,
            scale=alt.Scale(
                domain=["income", "expense"], range=[income_color, expense_color]
            ),
            legend=alt.Legend(orient="bottom-right", labelLimit=180),
        ),
        tooltip=[
            alt.Tooltip("period_label:N", title="Month"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("amount:Q", title="Amount", format=",.2f"),
        ],
    )

    line = base.mark_line(interpolate="monotone", strokeWidth=4)
    points = base.mark_circle(size=120, color="#ffffff", strokeWidth=2).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )

    rule = (
        alt.Chart(frame)
        .mark_rule(color="rgba(180, 188, 214, 0.45)", strokeWidth=1.25)
        .encode(x=alt.X("period_label:N", sort=month_order))
        .transform_filter(hover)
    )

    composed = (
        (line + rule + points)
        .add_params(hover)
        .properties(height=330)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#cdd6f4")
        .configure_legend(labelColor="#e2e8f0")
    )
    st.altair_chart(composed, use_container_width=True)


def _render_donut(
    frame: pd.DataFrame,
    category_col: str,
    amount_col: str,
    title: str,
    theme_mode: str,
    chart_height: int = 360,
) -> None:
    if frame.empty:
        st.info("No data is available for donut chart.")
        return

    donut_frame = frame.copy()
    donut_frame[amount_col] = pd.to_numeric(
        donut_frame[amount_col], errors="coerce"
    ).fillna(0.0)
    donut_frame = donut_frame[donut_frame[amount_col] > 0]
    donut_frame = donut_frame.sort_values(amount_col, ascending=False)
    if len(donut_frame.index) > 6:
        top = donut_frame.head(5).copy()
        other_amount = float(donut_frame.iloc[5:][amount_col].sum())
        other = pd.DataFrame([{category_col: "Other", amount_col: other_amount}])
        donut_frame = pd.concat([top, other], ignore_index=True)
    if donut_frame.empty:
        st.info("No spend values are available for donut chart.")
        return

    palette = [
        "#ff8b4a",
        "#ff5f7b",
        "#47d6ff",
        "#8a86ff",
        "#ba8cff",
        "#36dfc1",
        "#f8cf52",
    ]

    is_category_mix = title.lower() == "category"
    is_large = chart_height >= 420
    outer_radius = 138 if is_large else 116
    inner_radius = 68 if is_large else 56

    base_chart = alt.Chart(donut_frame)
    if is_category_mix:
        base_chart = base_chart.mark_arc(
            innerRadius=72,
            cornerRadius=8,
            padAngle=0.01,
            stroke="#ffffff",
            strokeWidth=1.1,
        )
    else:
        base_chart = base_chart.mark_arc(
            innerRadius=inner_radius,
            outerRadius=outer_radius,
            cornerRadius=8,
            padAngle=0.01,
            stroke="#ffffff",
            strokeWidth=1.1,
        )

    chart = base_chart.encode(
        theta=alt.Theta(f"{amount_col}:Q", stack=True),
        color=alt.Color(
            f"{category_col}:N",
            scale=alt.Scale(range=palette),
            legend=alt.Legend(
                title=title,
                orient="right",
                direction="vertical",
                symbolType="circle",
                symbolSize=130,
                labelFontSize=13,
                titleFontSize=14,
                labelLimit=180,
            ),
        ),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Category"),
            alt.Tooltip(f"{amount_col}:Q", title="Amount", format=",.2f"),
        ],
    ).properties(
        height=(340 if is_category_mix else chart_height),
        width="container",
        padding=(
            {"left": 18, "right": 0, "top": 0, "bottom": 0}
            if is_category_mix
            else {"left": 5, "right": 5, "top": 5, "bottom": 5}
        ),
    )
    st.altair_chart(_apply_chart_theme(chart, theme_mode), use_container_width=True)


def _render_recent_transaction_cards(
    engine, user_id: int, transactions: pd.DataFrame
) -> None:
    recent = transactions.head(8).copy()
    recent["amount"] = pd.to_numeric(recent["amount"], errors="coerce").fillna(0.0)
    categories = get_available_categories(engine, user_id)
    category_lookup = {
        str(row["name"]): int(row["id"])
        for _, row in categories.iterrows()
        if str(row["name"]).lower() != "uncategorized"
    }

    for _, row in recent.iterrows():
        amount = float(row["amount"])
        amount_class = "pf-amount-pos" if amount >= 0 else "pf-amount-neg"
        amount_value = _fmt_currency(abs(amount))
        if amount < 0:
            amount_value = f"-{amount_value}"

        source_type = str(row.get("source_type", "manual")).replace("_", " ").title()
        st.markdown(
            f"""
            <div class="pf-txn-card">
                <div class="pf-txn-row">
                    <div>
                        <div style="font-weight:700; color:var(--pf-text);">{str(row["description"])[:52]}</div>
                        <div style="font-size:0.80rem; color:var(--pf-muted); margin-top:0.1rem;">{row["transaction_date"]} | {source_type}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="{amount_class}">{amount_value}</div>
                        <div class="pf-chip">{row["category"]}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if str(row["category"]).lower() == "uncategorized" and category_lookup:
            with st.expander(
                f"Categorize transaction #{int(row['id'])}", expanded=False
            ):
                selected_category = st.selectbox(
                    "Select category",
                    list(category_lookup.keys()),
                    key=f"recent_uncategorized_select_{int(row['id'])}",
                )
                if st.button(
                    "Save category",
                    key=f"recent_uncategorized_save_{int(row['id'])}",
                    type="primary",
                ):
                    updated = update_transaction_category(
                        engine,
                        user_id=user_id,
                        transaction_id=int(row["id"]),
                        category_id=category_lookup[selected_category],
                    )
                    if updated:
                        st.success("Transaction category updated.")
                        st.rerun()
                    else:
                        st.error("Unable to update this transaction.")


def _render_sidebar(user, logout_callback) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:0.55rem 0.2rem 0.85rem 0.2rem;">
                <h3 style="margin:0; color:var(--pf-text);">Personal Finance</h3>
                <p style="margin:0.25rem 0 0 0; color:var(--pf-muted);">Pro dashboard workspace</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Signed in as: {user['email']}")
        if st.button(
            "Logout", key="sidebar_logout", use_container_width=True, type="primary"
        ):
            logout_callback()
        st.markdown(
            '<div class="pf-sidebar-sep"></div><div class="pf-nav-title">Navigation</div>',
            unsafe_allow_html=True,
        )
        for index, section in enumerate(NAVIGATION_OPTIONS):
            is_active = st.session_state.dashboard_section == section
            label = (
                f"{NAV_ICONS.get(section, '•')}  {NAV_DISPLAY.get(section, section)}"
            )
            button_type = "primary" if is_active else "secondary"
            if st.button(
                label,
                key=f"sidebar_nav_{index}",
                use_container_width=True,
                type=button_type,
            ):
                if st.session_state.dashboard_section != section:
                    st.session_state.dashboard_section = section
                    st.rerun()


def _render_empty_dashboard_prompt() -> None:
    st.info("No transactions are available yet. Use the upload section to add data.")
    st.button(
        "Upload data now",
        type="primary",
        on_click=_set_dashboard_section,
        args=("Upload Bank Statement",),
    )


def _render_dashboard_overview(engine, user_id: int) -> None:
    st.markdown(
        """
        <div class="pf-hero">
            <h1>Personal Finance Command Center</h1>
            <p>Track spending motion, category mix, and transaction quality from one place.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    theme_mode = _resolve_theme_mode(engine)
    metrics = get_dashboard_metrics(engine, user_id)
    _render_kpi_cards(metrics)

    transactions = get_transactions(engine, user_id)
    if transactions.empty:
        _render_empty_dashboard_prompt()
        return

    category_summary = get_category_summary(engine, user_id)
    trend_summary = get_trend_summary(engine, user_id)

    main_col, side_col = st.columns([2.2, 1], gap="large")
    with main_col:
        st.subheader("Income vs Expense")
        _render_income_vs_expense_chart(transactions, theme_mode)

        st.subheader("Monthly Spend Trend")
        _render_spend_trend_chart(trend_summary, theme_mode)

        row_left, row_right = st.columns([1.95, 0.35])
        with row_left:
            st.subheader("Recent Activity")
        with row_right:
            st.markdown('<div class="pf-compact-download">', unsafe_allow_html=True)
            st.download_button(
                "Download",
                data=_build_recent_activity_csv(transactions, limit=20),
                file_name="recent_activity.csv",
                mime="text/csv",
                type="primary",
                use_container_width=False,
            )
            st.markdown("</div>", unsafe_allow_html=True)
        _render_recent_transaction_cards(engine, user_id, transactions)

    with side_col:
        st.subheader("Category Mix")
        category_frame = (
            category_summary[["category", "amount"]].copy()
            if not category_summary.empty
            else pd.DataFrame()
        )
        if not category_frame.empty:
            category_frame["amount"] = (
                pd.to_numeric(category_frame["amount"], errors="coerce")
                .fillna(0.0)
                .abs()
            )
            category_frame = category_frame.sort_values("amount", ascending=False).head(
                7
            )
        _render_donut(
            category_frame,
            "category",
            "amount",
            "Category",
            theme_mode,
            chart_height=340,
        )


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

    if result.skipped_count > 0:
        st.success(
            f"Imported {result.inserted_count} transactions from {uploaded_file.name}. "
            f"Skipped {result.skipped_count} duplicate rows."
        )
    else:
        st.success(
            f"Imported {result.inserted_count} transactions from {uploaded_file.name}."
        )
    st.session_state.dashboard_section = "Dashboard"
    st.rerun()


def _render_upload_section(engine, user_id: int, file_type: str, title: str) -> None:
    st.title(title)
    st.markdown(
        '<div class="pf-upload-subtitle">Import your CSV and we will auto-categorize transactions using description rules.</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        f"Choose a {file_type.replace('_', ' ')} CSV",
        type=["csv"],
        key=file_type,
    )

    action_col, info_col = st.columns([1, 2.6])
    with action_col:
        st.button(
            "Process Upload",
            type="primary",
            disabled=uploaded_file is None,
            use_container_width=True,
            on_click=_process_upload,
            args=(engine, user_id, file_type, uploaded_file)
            if uploaded_file
            else (engine, user_id, file_type, None),
        )
    with info_col:
        if uploaded_file is not None:
            st.markdown(
                f'<div class="pf-upload-note">Selected file: {uploaded_file.name}</div>',
                unsafe_allow_html=True,
            )


def _render_transactions_section(engine, user_id: int) -> None:
    st.title("Transactions")
    st.write("Review transactions and update misclassified categories.")

    transactions = get_transactions(engine, user_id)
    categories = get_available_categories(engine, user_id)

    if transactions.empty:
        _render_empty_dashboard_prompt()
        return

    st.dataframe(transactions, use_container_width=True)

    # Replace the previous dropdown with a simple numeric input where the
    # user can type the transaction id directly. This is faster for power
    # users and simpler to integrate with the "create new category" flow.
    default_tx_id = int(transactions.iloc[0]["id"]) if not transactions.empty else 1
    selected_transaction_id = st.number_input(
        "Transaction ID",
        min_value=1,
        value=default_tx_id,
        step=1,
        key="selected_transaction_id",
    )

    try:
        selected_transaction_id = int(selected_transaction_id)
    except Exception:
        st.error("Transaction ID must be a whole number.")
        return

    selected_transaction = get_transaction_by_id(engine, user_id, selected_transaction_id)
    if selected_transaction is None:
        st.error("Could not load the selected transaction. Ensure the ID exists.")
        return

    # Allow the user to type a new category name. If the typed name already
    # exists for the user it will be reused; otherwise a new user-specific
    # category will be created.
    current_category_name = str(selected_transaction.get("category", ""))
    new_category_name = st.text_input(
        "Update category (type a new name to create)",
        value=current_category_name,
        key="transaction_category_new",
    )

    if st.button("Save category update", type="primary"):
        cname = str(new_category_name or "").strip()
        if not cname:
            st.error("Category name must not be empty.")
        else:
            try:
                # Create or find user category and then apply to transactions.
                category_id = create_user_category(engine, user_id, cname)
                updated = update_transaction_category(
                    engine,
                    user_id=user_id,
                    transaction_id=selected_transaction_id,
                    category_id=category_id,
                )
                if updated:
                    st.success("Transaction category updated successfully.")
                    st.rerun()
                else:
                    st.error("Unable to update the selected transaction.")
            except Exception as exc:
                st.error(f"Failed to create or update category: {exc}")


def _render_search_section(engine, user_id: int) -> None:
    st.title("Search and Filter")
    st.write("Find transactions by keyword, category, date range, or amount.")

    categories = get_available_categories(engine, user_id)
    category_lookup = {
        str(row["name"]): int(row["id"]) for _, row in categories.iterrows()
    }

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
            category_id=None
            if category_choice == "All"
            else category_lookup[category_choice],
            min_amount=min_amount if min_amount > 0 else None,
            max_amount=max_amount if max_amount > 0 else None,
        )
        if results.empty:
            st.info("No results match your search.")
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


def _render_preferences_section(engine, user_id: int) -> None:
    st.title("Preferences")
    st.write("Save your dashboard settings so the app matches your workflow.")

    preferences = get_user_preferences(engine, user_id)
    current_theme = preferences.get("theme_mode", "dark")
    selected_theme = st.radio(
        "Theme mode",
        ["dark", "light"],
        index=0 if current_theme == "dark" else 1,
        horizontal=True,
        key="preferences_theme_mode",
    )

    if st.button("Save preferences", type="primary"):
        saved = save_user_preferences(engine, user_id, selected_theme)
        st.session_state.theme_mode = saved["theme_mode"]
        st.success("Preferences saved successfully.")
        st.experimental_rerun()


def _render_budgeting_section(engine, user_id: int) -> None:
    st.markdown(
        """
        <div class="pf-hero">
            <h1>Budget Planner</h1>
            <p>Set monthly income, prioritize categories, and generate balanced budget targets.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    categories = get_available_categories(engine, user_id)
    category_names = [str(row["name"]) for _, row in categories.iterrows()]
    with st.form("budget_planner_form", clear_on_submit=True):
        monthly_income_raw = st.text_input(
            "Monthly income",
            value="",
            placeholder="Enter monthly income",
            key="monthly_income_input",
        )
        priority_categories = st.multiselect("Priority categories", category_names)
        submitted = st.form_submit_button("Calculate budget", type="primary")

    if not submitted:
        return

    cleaned_income = str(monthly_income_raw).strip().replace(",", "").replace("$", "")
    if not cleaned_income:
        st.error("Please enter your monthly income.")
        return

    try:
        monthly_income = float(cleaned_income)
    except ValueError:
        st.error("Monthly income must be a valid number.")
        return

    if monthly_income <= 0:
        st.error("Please enter a monthly income greater than zero.")
        return

    try:
        recommendations = calculate_budget_recommendations(
            engine=engine,
            user_id=user_id,
            monthly_income=monthly_income,
            priority_categories=priority_categories,
        )
    except ValueError as exc:
        st.error(f"Unable to calculate budget: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected budgeting error", exc_info=exc)
        st.error("An unexpected error occurred while calculating your budget.")
        return

    if recommendations.empty:
        st.info("No categories are available for budgeting yet.")
        return

    recommendations = recommendations.copy()
    recommendations["actual_spend"] = pd.to_numeric(
        recommendations["actual_spend"], errors="coerce"
    ).fillna(0.0)
    recommendations["recommended_budget"] = pd.to_numeric(
        recommendations["recommended_budget"], errors="coerce"
    ).fillna(0.0)
    recommendations["variance"] = pd.to_numeric(
        recommendations["variance"], errors="coerce"
    ).fillna(0.0)

    st.success("Budget recommendations generated successfully.")

    total_recommended = float(recommendations["recommended_budget"].sum())
    total_spend = float(recommendations["actual_spend"].sum())
    col1, col2, col3 = st.columns(3)
    col1.metric("Recommended total", _fmt_currency(total_recommended))
    col2.metric("Current spend", _fmt_currency(total_spend))
    col3.metric(
        "Unallocated", _fmt_currency(max(monthly_income - total_recommended, 0.0))
    )

    overspent = recommendations[recommendations["overspent"]]
    if not overspent.empty:
        st.warning(
            "Overspent categories: "
            + ", ".join(overspent["category"].astype(str).tolist())
        )

    theme_mode = _resolve_theme_mode(engine)
    left_col, right_col = st.columns([1.2, 1], gap="large")
    with left_col:
        viz_frame = recommendations[
            ["category", "actual_spend", "recommended_budget"]
        ].copy()
        viz_melted = viz_frame.melt(
            id_vars=["category"],
            value_vars=["actual_spend", "recommended_budget"],
            var_name="series",
            value_name="amount",
        )
        viz_melted["amount"] = pd.to_numeric(
            viz_melted["amount"], errors="coerce"
        ).fillna(0.0)
        bar_colors = ["#fb7185", "#44d2ff"]
        budget_chart = (
            alt.Chart(viz_melted)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("category:N", title="Category"),
                y=alt.Y("amount:Q", title="Amount"),
                color=alt.Color(
                    "series:N", scale=alt.Scale(range=bar_colors), title="Series"
                ),
                xOffset="series:N",
                tooltip=[
                    "category:N",
                    "series:N",
                    alt.Tooltip("amount:Q", format=",.2f"),
                ],
            )
            .properties(height=320)
        )
        st.subheader("Recommended vs Current by Category")
        st.altair_chart(budget_chart, use_container_width=True)

    with right_col:
        budget_split = pd.DataFrame(
            [
                {"category": "Budgeted", "amount": max(total_recommended, 0.0)},
                {
                    "category": "Remaining",
                    "amount": max(monthly_income - total_recommended, 0.0),
                },
            ]
        )
        st.subheader("Budget Usage")
        _render_donut(
            budget_split,
            "category",
            "amount",
            "Budget",
            theme_mode,
            chart_height=360,
        )

    st.dataframe(recommendations, use_container_width=True)


def render_dashboard_page(engine, logout_callback) -> None:
    user = st.session_state.authenticated_user
    if user is None:
        return

    initialize_dashboard_state()
    theme_mode = _resolve_theme_mode(engine)
    _inject_dashboard_styles(theme_mode)
    _render_sidebar(user, logout_callback)

    section = st.session_state.dashboard_section
    if section == "Dashboard":
        _render_dashboard_overview(engine, int(user["id"]))
    elif section == "Upload Bank Statement":
        _render_upload_section(
            engine, int(user["id"]), "bank_statement", "Upload Bank Statement"
        )
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
    elif section == "Preferences":
        _render_preferences_section(engine, int(user["id"]))
    elif section == "Budgeting":
        _render_budgeting_section(engine, int(user["id"]))
