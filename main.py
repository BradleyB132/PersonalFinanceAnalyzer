"""
Personal Finance Analyzer - Main Streamlit Application
Entry point with authentication and navigation.
"""
# Complexity overview:
# - Time: O(1) routing/auth checks per request, excluding downstream DB/page operations.
# - Space: O(1) framework state here, excluding session/cache and page data.
import os
import sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Ensure imports resolve to the root `app` package, not `src/app.py`.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
if SRC_PATH in sys.path:
    sys.path.remove(SRC_PATH)
    sys.path.append(SRC_PATH)

existing_app_module = sys.modules.get("app")
if existing_app_module is not None and not hasattr(existing_app_module, "__path__"):
    del sys.modules["app"]

# Set page config FIRST (must be before any other streamlit command)
st.set_page_config(
    page_title="FinanceFlow - Personal Finance Analyzer",
    page_icon=":material/eco:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.database import init_db, get_session
from app.auth import (
    register_user, login_user, logout, login_session, is_logged_in,
)
from app.models import User
from app.utils import seed_default_categories
from app.ui import apply_custom_css, render_sidebar_user


# Initialize database on first run
@st.cache_resource
def _init():
    init_db()
    session = get_session()
    try:
        seed_default_categories(session)
        # Seed admin user
        from app.models import User
        from app.auth import hash_password
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@financeapp.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
        admin = session.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                name="Admin",
                role="admin",
            )
            session.add(admin)
            session.commit()
    finally:
        session.close()
    return True


_init()
apply_custom_css()


def _set_auth_query(email: str) -> None:
    st.query_params["auth_email"] = email


def _clear_auth_query() -> None:
    if "auth_email" in st.query_params:
        del st.query_params["auth_email"]


def _restore_session_from_query() -> None:
    if is_logged_in():
        return

    auth_email = st.query_params.get("auth_email")
    if isinstance(auth_email, list):
        auth_email = auth_email[0] if auth_email else None
    if not auth_email:
        return

    session = get_session()
    try:
        user = session.query(User).filter(User.email == str(auth_email).lower().strip()).first()
        if user is not None:
            login_session(user)
    finally:
        session.close()


def render_auth_page():
    """Render the login/register tabs for unauthenticated users."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-top: 2rem; margin-bottom: 1.5rem;">
                <div style="font-family: 'Outfit', sans-serif; font-size: 2rem;
                    font-weight: 600; color: #4A6741; display: flex;
                    align-items: center; justify-content: center; gap: 10px;">
                    <span class="mat" style="font-size: 2rem; color: #4A6741;
                        font-variation-settings: 'FILL' 1, 'wght' 400;">
                        eco
                    </span>
                    FinanceFlow
                </div>
                <p style="color: #797D78; margin-top: 0.25rem; margin-left: 0.4rem;">
                    Personal Finance Analyzer
                </p>
            </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        # --- LOGIN ---
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                st.markdown("### Welcome back")
                st.caption("Sign in to your account to continue")

                email = st.text_input(
                    "Email", placeholder="you@example.com", key="login_email"
                )
                password = st.text_input(
                    "Password", type="password", placeholder="Enter your password",
                    key="login_password"
                )
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        session = get_session()
                        try:
                            ok, msg, user = login_user(session, email, password)
                            if ok:
                                login_session(user)
                                _set_auth_query(user.email)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        finally:
                            session.close()

        # --- REGISTER ---
        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                st.markdown("### Create your account")
                st.caption("Start tracking your finances today")

                name = st.text_input("Name", placeholder="Jane Doe", key="reg_name")
                email = st.text_input(
                    "Email", placeholder="you@example.com", key="reg_email"
                )
                password = st.text_input(
                    "Password", type="password",
                    placeholder="At least 6 characters", key="reg_password"
                )
                confirm = st.text_input(
                    "Confirm Password", type="password",
                    placeholder="Re-enter password", key="reg_confirm"
                )
                submit = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

                if submit:
                    if password != confirm:
                        st.error("Passwords do not match")
                    elif not all([name, email, password]):
                        st.error("Please fill in all fields")
                    else:
                        session = get_session()
                        try:
                            ok, msg, user = register_user(
                                session, email, password, name
                            )
                            if ok:
                                login_session(user)
                                _set_auth_query(user.email)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        finally:
                            session.close()


def render_sidebar_nav():
    """Render the navigation sidebar for authenticated users."""
    with st.sidebar:
        st.markdown("""
            <div style="padding: 0.75rem 0.25rem 1.5rem 0.25rem;">
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.5rem;
                    font-weight: 600; color: #4A6741; display: flex;
                    align-items: center; gap: 8px;">
                    <span class="mat" style="font-size: 1.5rem; color: #4A6741;
                        font-variation-settings: 'FILL' 1, 'wght' 400;">
                        eco
                    </span>
                    FinanceFlow
                </div>
                <div style="color: #797D78; font-size: 0.8rem; margin-top: 0.1rem;">
                    Personal Finance Analyzer
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Navigation buttons
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Dashboard"

        # Streamlit's :material/...: shortcode renders Material Symbols inline
        pages = [
            ("Dashboard", ":material/space_dashboard:"),
            ("Transactions", ":material/receipt_long:"),
            ("Upload", ":material/cloud_upload:"),
            ("Budget", ":material/savings:"),
            ("Reports", ":material/description:"),
        ]
        for label, mat_icon in pages:
            is_current = st.session_state["current_page"] == label
            btn_label = f"{mat_icon}  {label}"
            if st.button(
                btn_label,
                key=f"nav_{label}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state["current_page"] = label
                st.rerun()

        render_sidebar_user(
            st.session_state.get("user_name", "User"),
            st.session_state.get("user_email", ""),
        )
        st.markdown("")
        if st.button(
            ":material/logout: Log Out",
            use_container_width=True,
            key="logout_btn",
        ):
            logout()
            _clear_auth_query()
            st.rerun()


def main():
    _restore_session_from_query()

    if not is_logged_in():
        render_auth_page()
        return

    render_sidebar_nav()

    # Route to the selected page
    page = st.session_state.get("current_page", "Dashboard")
    if page == "Dashboard":
        from views import dashboard
        dashboard.render()
    elif page == "Transactions":
        from views import transactions
        transactions.render()
    elif page == "Upload":
        from views import upload
        upload.render()
    elif page == "Budget":
        from views import budget
        budget.render()
    elif page == "Reports":
        from views import reports
        reports.render()


if __name__ == "__main__":
    main()
