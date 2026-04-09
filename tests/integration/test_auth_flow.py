from services.auth_service import authenticate_user, register_user


def test_register_and_login_flow(auth_engine) -> None:
    registration = register_user(auth_engine, "user@example.com", "Password123!")

    assert registration.success
    assert registration.user is not None
    assert registration.user["email"] == "user@example.com"
    assert registration.confirmation_message is not None

    login = authenticate_user(auth_engine, "user@example.com", "Password123!")

    assert login.success
    assert login.user is not None
    assert login.user["email"] == "user@example.com"


def test_duplicate_registration_is_rejected(auth_engine) -> None:
    first = register_user(auth_engine, "user@example.com", "Password123!")
    duplicate = register_user(auth_engine, "user@example.com", "Password123!")

    assert first.success
    assert not duplicate.success
    assert duplicate.message == "Email is already registered."


def test_invalid_login_returns_error(auth_engine) -> None:
    register_user(auth_engine, "user@example.com", "Password123!")

    login = authenticate_user(auth_engine, "user@example.com", "wrong-password")

    assert not login.success
    assert login.message == "Invalid username or password."
