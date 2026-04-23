"""
Authentication module.
Handles password hashing, user creation, login, session management.
"""
# Complexity overview:
# - Time: O(1) per hash/verify, plus O(1) indexed user lookup per auth call.
# - Space: O(1) per request.
import bcrypt
import streamlit as st
from sqlalchemy.orm import Session
from app.models import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def register_user(session: Session, email: str, password: str, name: str) -> tuple[bool, str, User | None]:
    """
    Register a new user.
    Returns: (success, message, user)
    """
    email = email.lower().strip()

    # Validate
    if not email or "@" not in email:
        return False, "Please enter a valid email address", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters", None
    if not name.strip():
        return False, "Please enter your name", None

    # Check if exists
    existing = session.query(User).filter(User.email == email).first()
    if existing:
        return False, "Email already registered", None

    # Create
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name.strip(),
        role="user"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return True, "Account created successfully", user


def login_user(session: Session, email: str, password: str) -> tuple[bool, str, User | None]:
    """
    Authenticate a user.
    Returns: (success, message, user)
    """
    email = email.lower().strip()
    user = session.query(User).filter(User.email == email).first()
    if not user:
        return False, "Invalid email or password", None
    if not verify_password(password, user.password_hash):
        return False, "Invalid email or password", None
    return True, "Login successful", user


def get_current_user(session: Session) -> User | None:
    """Get the currently logged-in user from session state."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    return session.query(User).filter(User.id == user_id).first()


def logout():
    """Clear session state to log out."""
    for key in ["user_id", "user_email", "user_name", "user_role"]:
        if key in st.session_state:
            del st.session_state[key]


def login_session(user: User):
    """Set session state for a logged-in user."""
    st.session_state["user_id"] = user.id
    st.session_state["user_email"] = user.email
    st.session_state["user_name"] = user.name
    st.session_state["user_role"] = user.role


def is_logged_in() -> bool:
    """Check if a user is logged in."""
    return st.session_state.get("user_id") is not None


def require_login():
    """Redirect to login if not logged in. Call at top of protected pages."""
    if not is_logged_in():
        st.warning("Please log in to access this page")
        st.stop()
