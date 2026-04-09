from services.auth_service import hash_password, verify_password


def test_password_hash_round_trip() -> None:
    stored_hash = hash_password("strong-password")

    assert verify_password("strong-password", stored_hash)
    assert not verify_password("wrong-password", stored_hash)
