"""Budget view - monthly income setting and 50/30/20 recommendations."""
import streamlit as st
import plotly.graph_objects as go

from app.database import get_session
from app import repositories as repo
from app.services import compute_budget_recommendations
from app.ui import render_header
from app.utils import format_currency


def render():
    render_header(
        "Budget & Goals",
        "Set your budget and track spending recommendations"
    )

    session = get_session()
    user_id = st.session_state["user_id"]

    try:
        data = compute_budget_recommendations(session, user_id)
        monthly_income = data["monthly_income"]

        # --- Income Settings ---
        with st.container(border=True):
            st.markdown("""
                <div style="display: flex; align-items: center; gap: 8px;
                    font-family: 'Outfit', sans-serif; font-size: 1.15rem;
                    font-weight: 500; color: #2C302B; margin-bottom: 0.25rem;">
                    <span class="mat" style="color: #4A6741;
                        font-variation-settings: 'FILL' 1, 'wght' 400;">
                        payments
                    </span>
                    Monthly Income
                </div>
            """, unsafe_allow_html=True)
            st.caption("Set your income to receive personalized 50/30/20 recommendations")

            col1, col2 = st.columns([3, 1])
            with col1:
                new_income = st.number_input(
                    "Monthly income ($)",
                    min_value=0.0,
                    value=float(monthly_income),
                    step=100.0,
                    format="%.2f",
                    key="budget_income",
                    label_visibility="collapsed",
                )
            with col2:
                if st.button("Save Income", use_container_width=True, key="save_income_btn"):
                    repo.update_budget(session, user_id, new_income)
                    st.success("Budget updated")
                    st.rerun()

        if monthly_income <= 0:
            st.info(
                "Set your monthly income above to see personalized "
                "budget recommendations based on the 50/30/20 rule."
            )
            _render_50_30_20_explainer()
            return

        # --- Recommendations ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_header, col_badge = st.columns([3, 1])
        with col_header:
            st.markdown("### Budget Recommendations")
        with col_badge:
            st.markdown(f"""
                <div style="text-align: right; padding-top: 0.6rem;">
                    <span style="background: #F2F0EB; color: #4A6741;
                        padding: 4px 12px; border-radius: 999px;
                        font-size: 0.85rem; font-weight: 500;
                        display: inline-flex; align-items: center; gap: 4px;">
                        <span class="mat" style="font-size: 1em;">calendar_month</span>
                        Analyzing: {data["analysis_month"]}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        if not data["has_transactions"]:
            st.info(
                f"No transactions found for **{data['analysis_month']}**. "
                "Upload a statement or check the Transactions page."
            )

        cols = st.columns(3)
        for i, rec in enumerate(data["recommendations"]):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"**{rec['category']}**")
                    spent = rec["spent"]
                    budget = rec["budget"]
                    pct = (spent / budget * 100) if budget > 0 else 0
                    over = spent > budget

                    bar_color = "#C07C5F" if over else ("#D4A373" if pct > 80 else "#4A6741")

                    st.markdown(f"""
                        <div style="margin: 0.5rem 0;">
                            <div style="font-size: 1.5rem; font-weight: 600;
                                color: {'#C07C5F' if over else '#2C302B'};
                                font-family: 'Outfit', sans-serif;">
                                {format_currency(spent)}
                            </div>
                            <div style="color: #797D78; font-size: 0.85rem;">
                                of {format_currency(budget)} budget
                            </div>
                        </div>
                        <div style="background: #F2F0EB; border-radius: 999px; height: 8px;
                            overflow: hidden; margin: 0.5rem 0;">
                            <div style="background: {bar_color}; height: 100%;
                                width: {min(pct, 100)}%; border-radius: 999px;
                                transition: width 0.3s ease;"></div>
                        </div>
                        <div style="font-size: 0.85rem; color: {'#C07C5F' if over else '#797D78'};">
                            {format_currency(abs(rec['remaining']))}
                            {'over budget' if over else 'remaining'}
                        </div>
                    """, unsafe_allow_html=True)

        # --- Alerts ---
        if data["alerts"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
                <div style="display: flex; align-items: center; gap: 8px;
                    font-family: 'Outfit', sans-serif; font-size: 1.35rem;
                    font-weight: 500; color: #2C302B; margin-bottom: 0.5rem;">
                    <span class="mat" style="color: #C07C5F;">warning</span>
                    Spending Alerts
                </div>
            """, unsafe_allow_html=True)
            for alert in data["alerts"]:
                st.warning(
                    f"**{alert['category']}**: {alert['message']} "
                    f"({format_currency(alert['spent'])} this month)"
                )

        # --- Current month breakdown ---
        if data["current_spending"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### This Month's Spending Breakdown")
            import pandas as pd

            df = pd.DataFrame(data["current_spending"])
            df = df.sort_values("value", ascending=True)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["value"],
                y=df["name"],
                orientation="h",
                marker=dict(color="#C07C5F"),
                text=[format_currency(v) for v in df["value"]],
                textposition="outside",
            ))
            fig.update_layout(
                margin=dict(l=10, r=50, t=10, b=10),
                height=max(250, len(df) * 35),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#F2F0EB", tickprefix="$", zeroline=False),
                yaxis=dict(showgrid=False),
                font=dict(family="Manrope, sans-serif", color="#2C302B"),
            )
            st.plotly_chart(fig, use_container_width=True)

        _render_50_30_20_explainer()

    finally:
        session.close()


def _render_50_30_20_explainer():
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### Understanding the 50/30/20 Rule")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
                <div style="background: rgba(74, 103, 65, 0.08);
                    padding: 1rem; border-radius: 8px;">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.5rem;
                        font-weight: 600; color: #4A6741;">50%</div>
                    <strong>Needs</strong>
                    <p style="color: #797D78; font-size: 0.85rem; margin: 0.5rem 0 0;">
                        Groceries, utilities, transportation, healthcare
                    </p>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
                <div style="background: rgba(192, 124, 95, 0.08);
                    padding: 1rem; border-radius: 8px;">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.5rem;
                        font-weight: 600; color: #C07C5F;">30%</div>
                    <strong>Wants</strong>
                    <p style="color: #797D78; font-size: 0.85rem; margin: 0.5rem 0 0;">
                        Dining out, entertainment, shopping, subscriptions
                    </p>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
                <div style="background: rgba(212, 163, 115, 0.15);
                    padding: 1rem; border-radius: 8px;">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.5rem;
                        font-weight: 600; color: #D4A373;">20%</div>
                    <strong>Savings</strong>
                    <p style="color: #797D78; font-size: 0.85rem; margin: 0.5rem 0 0;">
                        Investments, emergency fund, debt repayment
                    </p>
                </div>
            """, unsafe_allow_html=True)
