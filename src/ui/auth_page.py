"""Auth page UI for PersonalFinanceAnalyzer."""

from __future__ import annotations

import logging

import streamlit as st

from services.auth_service import authenticate_user, register_user
from services.notifications import send_confirmation_email

logger = logging.getLogger(__name__)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #f7f8fc 0%, #eef2f8 100%);
            }

            .welcome-label {
                display: inline-flex;
                padding: 0.32rem 0.68rem;
                border-radius: 999px;
                background: rgba(15, 23, 42, 0.1);
                color: #1e293b;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .welcome-title {
                margin: 0.7rem 0 0.25rem;
                font-size: clamp(1.7rem, 3vw, 2.45rem);
                line-height: 1.05;
                font-weight: 800;
                color: #0f172a;
            }

            .welcome-copy {
                margin: 0;
                color: #475569;
                font-size: 0.98rem;
            }

            .auth-shell {
                max-width: 540px;
                margin: 2rem auto 0;
                padding: 1.2rem 1.2rem 1rem;
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid rgba(148, 163, 184, 0.18);
                box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
                backdrop-filter: blur(8px);
            }

            .auth-help {
                margin-top: 0.8rem;
                color: #111827;
                font-size: 0.95rem;
                text-align: left;
            }

            .auth-link-row {
                margin-top: 0.85rem;
                color: #111827;
                font-size: 0.95rem;
                text-align: left;
            }

            .stButton button {
                border-radius: 12px;
                font-weight: 700;
                padding: 0.55rem 1rem;
            }

            .stButton button[kind="primary"] {
                background: #111827 !important;
                color: #f9fafb !important;
                border: 1px solid #111827 !important;
                box-shadow: none !important;
            }

            .stButton button[kind="primary"]:hover {
                background: #000000 !important;
                color: #ffffff !important;
            }

            .stButton button[kind="secondary"] {
                background: transparent !important;
                border: 0 !important;
                color: #111827 !important;
                box-shadow: none !important;
                padding: 0 !important;
                min-height: auto !important;
                width: auto !important;
                text-decoration: underline;
                text-decoration-thickness: 1.5px;
                text-underline-offset: 0.18em;
                justify-content: flex-start !important;
                display: inline-flex !important;
            }

            .stButton button[kind="secondary"]:hover {
                background: transparent !important;
                color: #000000 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state() -> None:
    if "authenticated_user" not in st.session_state:
        st.session_state.authenticated_user = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "Login"


def set_auth_mode(mode: str) -> None:
    st.session_state.auth_mode = mode


def handle_logout() -> None:
    st.session_state.authenticated_user = None
    st.rerun()


def render_logged_in_view() -> None:
    user = st.session_state.authenticated_user
    if user is None:
        return

    with st.sidebar:
        st.subheader("Account")
        st.write(user["email"])
        if st.button("Logout", use_container_width=True, type="primary"):
            handle_logout()

    st.success("Logged in and redirected to your dashboard.")
    st.title("Personal Finance Dashboard")
    st.write("You are signed in and can now access personalized features.")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Account status", "Active")
    with col2:
        st.metric("Email", user["email"])
    st.info(
        "Next implementation slices will connect uploads, categorization, and dashboards to this session."
    )


def render_login_form(engine) -> None:
    with st.container(border=True):
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )
            submitted = st.form_submit_button(
                "Sign in", use_container_width=True, type="primary"
            )

        st.markdown(
            '<div class="auth-link-row">Don\'t have an account?</div>',
            unsafe_allow_html=True,
        )
        st.button(
            "Register here",
            key="register_here_button",
            on_click=set_auth_mode,
            args=("Register",),
            type="secondary",
            use_container_width=False,
        )

    if submitted:
        result = authenticate_user(engine, email, password)
        if result.success and result.user is not None:
            st.session_state.authenticated_user = result.user
            logger.info("user_logged_in", extra={"email": result.user["email"]})
            st.rerun()
        st.error(result.message)


def render_register_form(engine) -> None:
    with st.container(border=True):
        with st.form("register_form", clear_on_submit=False):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input(
                "Password", type="password", placeholder="Create a password"
            )
            confirm_password = st.text_input(
                "Confirm password", type="password", placeholder="Re-enter password"
            )
            submitted = st.form_submit_button(
                "Create account", use_container_width=True, type="primary"
            )

        st.markdown(
            '<div class="auth-link-row">Already have an account?</div>',
            unsafe_allow_html=True,
        )
        st.button(
            "Login here",
            key="login_here_button",
            on_click=set_auth_mode,
            args=("Login",),
            type="secondary",
            use_container_width=False,
        )

    if submitted:
        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        result = register_user(engine, email, password)
        if not result.success or result.user is None:
            st.error(result.message)
            return

        email_result = send_confirmation_email(
            recipient_email=result.user["email"],
            confirmation_message=result.confirmation_message
            or "Your account has been created.",
        )
        logger.info(
            "user_registered",
            extra={"email": result.user["email"], "email_sent": email_result.sent},
        )
        st.success("Account created successfully.")
        if email_result.sent:
            st.info("Confirmation email sent.")
        else:
            st.warning(
                "Confirmation email was not sent because SMTP is not configured. A preview was logged."
            )


def render_auth_page(engine) -> None:
    initialize_session_state()
    inject_styles()

    if st.session_state.authenticated_user is not None:
        render_logged_in_view()
        return

    left_spacer, auth_col, right_spacer = st.columns([1.15, 1.45, 1.15])
    with auth_col:
        with st.container(border=True):
            st.markdown(
                '<div class="welcome-label">PersonalFinanceAnalyzer</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="welcome-title">Welcome</div>', unsafe_allow_html=True
            )
            st.markdown(
                '<div class="welcome-copy">Login or register to continue.</div>',
                unsafe_allow_html=True,
            )

            if st.session_state.auth_mode == "Login":
                render_login_form(engine)
            else:
                render_register_form(engine)
