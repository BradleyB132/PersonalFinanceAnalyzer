"""Auth page UI for PersonalFinanceAnalyzer."""

from __future__ import annotations

import logging

import streamlit as st

from services.auth_service import authenticate_user, register_user
from services.auth_service import get_user_by_email
from services.notifications import send_confirmation_email
from services.validation_service import (
    MIN_PASSWORD_LENGTH,
    validate_email,
    validate_password,
)
from ui.dashboard_page import render_dashboard_page

logger = logging.getLogger(__name__)
AUTH_QUERY_KEY = "auth_email"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #eff1f5 0%, #e8ebf1 100%);
            }

            [data-testid="stAppViewContainer"] .main .block-container {
                max-width: 1160px;
                padding-top: 1.6rem;
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 14px !important;
                background: rgba(255, 255, 255, 0.97) !important;
                border: 1px solid rgba(203, 209, 223, 0.9) !important;
                box-shadow: 0 14px 30px rgba(28, 36, 55, 0.1) !important;
            }

            [data-testid="stVerticalBlockBorderWrapper"] > div {
                padding: 1.15rem 1.1rem 1rem !important;
            }

            .auth-brand-row {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }

            .auth-brand-mark {
                width: 1.3rem;
                height: 1.3rem;
                border-radius: 6px;
                background: linear-gradient(135deg, #6a5cff, #5a55e8);
                color: #ffffff;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.82rem;
                font-weight: 800;
                box-shadow: 0 6px 14px rgba(89, 92, 232, 0.28);
            }

            .auth-brand-name {
                color: #2b3347;
                font-size: 0.95rem;
                font-weight: 700;
            }

            .auth-title {
                margin: 0.2rem 0 0.2rem;
                color: #1f2738;
                font-size: 2rem;
                line-height: 1;
                font-weight: 750;
            }

            .auth-copy {
                margin: 0;
                color: #7a859c;
                font-size: 0.9rem;
            }

            [data-testid="stForm"] {
                background: transparent;
                border: none;
                border-radius: 0;
                padding: 0.55rem 0 0;
            }

            [data-testid="stTextInput"] label {
                color: #4d5a74 !important;
                font-weight: 600;
            }

            /* Keep auth inputs simple and stable: plain white BaseWeb input controls. */
            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] {
                background: #ffffff !important;
                border: 1px solid rgba(186, 196, 216, 0.95) !important;
                border-radius: 10px !important;
                overflow: visible !important;
            }

            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] > div {
                background: #ffffff !important;
            }

            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] input {
                color: #222b3d !important;
                background: transparent !important;
                opacity: 1 !important;
            }

            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] input::placeholder {
                color: #7a869f !important;
                opacity: 1 !important;
            }

            [data-testid="stCheckbox"] label {
                color: #5b6780 !important;
                font-size: 0.87rem;
                font-weight: 600;
            }

            [data-testid="stCheckbox"] span {
                color: #5b6780 !important;
                opacity: 1 !important;
            }

            [data-testid="stCheckbox"] input + div {
                color: #5b6780 !important;
                opacity: 1 !important;
            }

            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] button {
                background: #ffffff !important;
                border: none !important;
                color: #4d5a74 !important;
                opacity: 1 !important;
            }

            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] button:hover {
                color: #33425f !important;
            }

            [data-testid="stTextInputRootElement"] div[data-baseweb="input"] svg {
                fill: #4d5a74 !important;
                stroke: #4d5a74 !important;
                opacity: 1 !important;
            }

            /* Keep "Press Enter to submit form" below the field, not near the eye icon. */
            [data-testid="stTextInput"] [data-testid="InputInstructions"],
            [data-testid="stTextInput"] [data-testid="stTextInputInstructions"] {
                position: static !important;
                display: block !important;
                margin-top: 0.32rem !important;
                padding-right: 0 !important;
                color: #6f7b93 !important;
                font-size: 0.78rem !important;
                line-height: 1.2 !important;
            }

            .auth-row {
                margin-top: 0.08rem;
                margin-bottom: 0.18rem;
                color: #6f7b93;
                font-size: 0.87rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .stButton button {
                border-radius: 10px;
                font-weight: 700;
                padding: 0.55rem 1rem;
            }

            .stButton button[kind="primary"] {
                background: linear-gradient(90deg, #6c5cff, #5e56e8) !important;
                color: #f9fafb !important;
                border: none !important;
                box-shadow: 0 8px 18px rgba(94, 86, 232, 0.28) !important;
            }

            .stButton button[kind="primary"]:hover {
                background: linear-gradient(90deg, #7363ff, #635cee) !important;
            }

            .stButton button[kind="secondary"] {
                background: transparent !important;
                border: 0 !important;
                color: #5c57e8 !important;
                box-shadow: none !important;
                padding: 0 !important;
                min-height: auto !important;
                width: auto !important;
                text-decoration: underline;
                text-decoration-thickness: 1.4px;
                text-underline-offset: 0.15em;
                justify-content: flex-start !important;
                display: inline-flex !important;
                font-size: 0.86rem !important;
            }

            .stButton button[kind="secondary"]:hover {
                background: transparent !important;
                color: #4c47d8 !important;
            }

            .auth-social-sep {
                margin: 0.45rem 0 0.45rem;
                color: #8b95ab;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-align: center;
                text-transform: uppercase;
            }

            .auth-social-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.55rem;
            }

            .auth-social-pill {
                border-radius: 8px;
                border: 1px solid rgba(207, 212, 224, 0.95);
                background: #fbfcff;
                color: #4b556a;
                font-size: 0.85rem;
                font-weight: 650;
                padding: 0.48rem 0.6rem;
                text-align: center;
            }

            .auth-footer-line {
                margin-top: 0.7rem;
                color: #616f8b;
                font-size: 0.88rem;
                text-align: center;
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
    if AUTH_QUERY_KEY in st.query_params:
        del st.query_params[AUTH_QUERY_KEY]
    st.rerun()


def _restore_auth_session(engine) -> None:
    if st.session_state.authenticated_user is not None:
        return

    persisted_email = st.query_params.get(AUTH_QUERY_KEY)
    if not persisted_email:
        return

    user = get_user_by_email(str(persisted_email), engine=engine)
    if user is not None:
        st.session_state.authenticated_user = user


def render_logged_in_view(engine) -> None:
    user = st.session_state.authenticated_user
    if user is None:
        return

    render_dashboard_page(engine, handle_logout)


def render_login_form(engine) -> None:
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )

        submitted = st.form_submit_button(
            "Sign in", use_container_width=True, type="primary"
        )

    st.markdown(
        '<div class="auth-footer-line">Don\'t have an account?</div>',
        unsafe_allow_html=True,
    )
    st.button(
        "Register now",
        key="register_here_button",
        on_click=set_auth_mode,
        args=("Register",),
        type="secondary",
        use_container_width=False,
    )

    if submitted:
        if not validate_email(email):
            st.error("Enter a valid email address.")
            return
        if not password:
            st.error("Password is required.")
            return

        result = authenticate_user(engine, email, password)
        if result.success and result.user is not None:
            st.session_state.authenticated_user = result.user
            st.query_params[AUTH_QUERY_KEY] = str(result.user["email"])
            logger.info("user_logged_in", extra={"email": result.user["email"]})
            st.rerun()
        st.error(result.message)


def render_register_form(engine) -> None:
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
        '<div class="auth-footer-line">Already have an account?</div>',
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
        if not validate_email(email):
            st.error("Enter a valid email address.")
            return
        if not validate_password(password):
            st.error(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
            )
            return
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
    _restore_auth_session(engine)
    inject_styles()

    if st.session_state.authenticated_user is not None:
        render_logged_in_view(engine)
        return

    left_spacer, auth_col, right_spacer = st.columns([1.35, 1.2, 1.35])
    with auth_col:
        with st.container(border=True):
            st.markdown(
                '<div class="auth-brand-row"><span class="auth-brand-mark">$</span><span class="auth-brand-name">PersonalFinanceAdvisor</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="auth-title">Sign in to Dashboard</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="auth-copy">Welcome back! Please sign in to continue.</div>',
                unsafe_allow_html=True,
            )

            if st.session_state.auth_mode == "Login":
                render_login_form(engine)
            else:
                render_register_form(engine)
