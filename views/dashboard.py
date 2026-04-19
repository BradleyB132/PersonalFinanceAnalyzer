"""Dashboard view - financial overview with charts."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.database import get_session
from app import repositories as repo
from app.services import compute_dashboard_stats
from app.ui import render_header, CHART_COLORS
from app.utils import format_currency


def render():
    render_header(
        "Dashboard",
        "Your financial overview at a glance"
    )

    session = get_session()
    try:
        user_id = st.session_state["user_id"]
        stats = compute_dashboard_stats(session, user_id)
    finally:
        session.close()

    if stats["total_transactions"] == 0:
        _render_empty_state()
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions", stats["total_transactions"])
    col2.metric("Total Income", format_currency(stats["total_income"]))
    col3.metric("Total Expenses", format_currency(stats["total_expenses"]))
    col4.metric("Net Balance", format_currency(stats["net_balance"]))

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row 1
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Spending by Category")
        if stats["by_category"]:
            df = pd.DataFrame(stats["by_category"][:6])
            fig = px.pie(
                df, names="name", values="value",
                color_discrete_sequence=CHART_COLORS,
                hole=0.55,
            )
            fig.update_traces(
                textposition="outside",
                textinfo="label+percent",
                textfont_size=12,
                automargin=True,
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(l=24, r=24, t=20, b=56),
                height=360,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Manrope, sans-serif", color="#2C302B"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending data to display yet.")

    with col_b:
        st.markdown("#### Top Categories")
        if stats["by_category"]:
            df = pd.DataFrame(stats["by_category"][:6])
            df = df.sort_values("value")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["value"],
                y=df["name"],
                orientation="h",
                marker=dict(
                    color="#4A6741",
                    line=dict(color="#3D5535", width=0),
                ),
                text=[format_currency(v) for v in df["value"]],
                textposition="outside",
                textfont=dict(family="Manrope, sans-serif", color="#2C302B"),
            ))
            fig.update_layout(
                margin=dict(l=10, r=40, t=10, b=10),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=True, gridcolor="#F2F0EB",
                    tickprefix="$", zeroline=False,
                ),
                yaxis=dict(showgrid=False),
                font=dict(family="Manrope, sans-serif", color="#2C302B"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data to display yet.")

    # Chart row 2 - Trends
    st.markdown("#### Income vs Expenses Over Time")
    if stats["trends"]:
        df = pd.DataFrame(stats["trends"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["month"], y=df["income"],
            name="Income",
            mode="lines+markers",
            line=dict(color="#4A6741", width=3),
            fill="tozeroy",
            fillcolor="rgba(74, 103, 65, 0.15)",
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=df["month"], y=df["expenses"],
            name="Expenses",
            mode="lines+markers",
            line=dict(color="#C07C5F", width=3),
            fill="tozeroy",
            fillcolor="rgba(192, 124, 95, 0.15)",
            marker=dict(size=8),
        ))
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(
                showgrid=True, gridcolor="#F2F0EB",
                tickprefix="$", zeroline=False, title=""
            ),
            font=dict(family="Manrope, sans-serif", color="#2C302B"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload statements to see spending trends over time.")

    st.markdown("#### Recent Activity")
    _render_recent_activity(user_id)


def _render_recent_activity(user_id: int) -> None:
    session = get_session()
    try:
        categories = repo.list_categories(session, user_id)
        category_by_id = {c.id: c.name for c in categories}
        category_id_by_name = {c.name: c.id for c in categories}
        category_names = [c.name for c in categories if c.name.lower() != "uncategorized"]

        transactions = repo.list_transactions(session, user_id)
        if not transactions:
            st.info("No recent transactions yet.")
            return

        uncategorized_in_recent = 0

        for txn in transactions[:10]:
            category_name = category_by_id.get(txn.category_id, "Uncategorized")
            source_name = (txn.source or "manual").replace("_", " ").title()
            amount_text = format_currency(txn.amount)
            amount_color = "#4A6741" if txn.amount >= 0 else "#C07C5F"

            st.markdown(
                f"""
                <div style="background:#FFFFFF; border:1px solid #E8E6E1; border-radius:8px; padding:0.9rem 1rem; margin-bottom:0.55rem;">
                    <div style="display:flex; justify-content:space-between; gap:0.8rem; align-items:flex-start;">
                        <div>
                            <div style="font-weight:600; color:#2C302B;">{txn.description}</div>
                            <div style="font-size:0.82rem; color:#797D78; margin-top:0.15rem;">{txn.transaction_date} | {source_name}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:700; color:{amount_color};">{amount_text}</div>
                            <div style="font-size:0.8rem; color:#797D78; margin-top:0.15rem;">{category_name}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if category_name.lower() == "uncategorized" and category_names:
                uncategorized_in_recent += 1
                c1, c2 = st.columns([3, 1])
                with c1:
                    chosen_name = st.selectbox(
                        f"Categorize transaction #{txn.id}",
                        category_names,
                        key=f"dash_uncat_choice_{txn.id}",
                    )
                with c2:
                    st.write("")
                    if st.button(
                        "Save",
                        key=f"dash_uncat_save_{txn.id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        target_id = category_id_by_name.get(chosen_name)
                        if target_id is not None and repo.update_transaction_category(
                            session, user_id, txn.id, target_id
                        ):
                            st.success("Category updated.")
                            st.rerun()
                        else:
                            st.error("Unable to update this transaction.")

        if uncategorized_in_recent == 0:
            st.caption("No uncategorized items in the most recent activity.")
    finally:
        session.close()


def _render_empty_state():
    st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E8E6E1; border-radius: 8px;
            padding: 3rem; text-align: center; margin-top: 2rem;">
            <div style="display: inline-flex; align-items: center; justify-content: center;
                width: 72px; height: 72px; border-radius: 50%;
                background: rgba(74, 103, 65, 0.1); margin-bottom: 1rem;">
                <span class="mat" style="font-size: 2.5rem; color: #4A6741;
                    font-variation-settings: 'FILL' 1, 'wght' 400;">
                    insert_chart
                </span>
            </div>
            <h3 style="font-family: 'Outfit', sans-serif; color: #2C302B; margin: 0;">
                No transactions yet
            </h3>
            <p style="color: #797D78; margin-top: 0.5rem;">
                Upload your first bank or credit card statement to see beautiful visualizations.
            </p>
        </div>
    """, unsafe_allow_html=True)
    if st.button(
        ":material/cloud_upload: Go to Upload page",
        key="empty_upload_btn"
    ):
        st.session_state["current_page"] = "Upload"
        st.rerun()
